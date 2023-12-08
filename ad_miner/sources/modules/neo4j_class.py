import datetime
import multiprocessing as mp
import sys
import time
import json
from hashlib import md5
from pathlib import Path as pathlib

from ad_miner.sources.modules import istarmap  # import to apply patch # noqa
import numpy as np
import tqdm
import neo4j  # TO REPLACE BY 'from neo4j import GraphDatabase' after neo4j fix

from ad_miner.sources.modules import cache_class, logger
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.utils import timer_format

MODULES_DIRECTORY = pathlib(__file__).parent

# 🥒 This is a quick import of a fix from @Sopalinge
# 🥒 Following code should be removed when neo4j implements
# 🥒 serialization of neo4j datetime objects
GraphDatabase = neo4j.GraphDatabase


def temporary_fix(cls):
    return (
        cls.__class__,
        (
            cls.year,
            cls.month,
            cls.day,
            cls.hour,
            cls.minute,
            cls.second,
            cls.nanosecond,
            cls.tzinfo,
        ),
    )


neo4j.time.DateTime.__reduce__ = temporary_fix
# End of temporary dirty fix 🥒


def pre_request(arguments):
    driver = GraphDatabase.driver(
        arguments.bolt,
        auth=(arguments.username, arguments.password),
        encrypted=False,
    )
    try:
        with driver.session() as session:
            with session.begin_transaction() as tx:
                for record in tx.run(
                    "MATCH (a) WHERE a.lastlogon IS NOT NULL return toInteger(a.lastlogon) as last order by last desc LIMIT 1"
                ):
                    date_lastlogon = record.data()

        driver.close()
    except Exception as e:
        logger.print_error("Connection to neo4j database impossible.")
        logger.print_error(e)
        driver.close()
        sys.exit(-1)

    try:
        extract_date = datetime.datetime.fromtimestamp(date_lastlogon["last"]).strftime("%Y%m%d")
    except UnboundLocalError as e:
        logger.print_warning("No LastLogon, the date of the report will be today's date")
        extract_date_timestamp = datetime.date.today()
        extract_date = extract_date_timestamp.strftime("%Y%m%d")

    with driver.session() as session:
        with session.begin_transaction() as tx:
            total_objects = []
            boolean_azure = False
            for record in tx.run(
                "MATCH (x) return labels(x), count(labels(x)) AS number_type"
            ):
                total_objects.append(record.data())

            for record in tx.run(
                "MATCH ()-[r]->() RETURN count(r) AS total_relations"
            ):
                number_relations = record.data()["total_relations"]

            for record in tx.run(
                "MATCH (n) WHERE EXISTS(n.tenantid) return n LIMIT 1"
            ):
                boolean_azure = bool(record.data()["n"])

    driver.close()
    print("number relation : ", number_relations)

    return extract_date, total_objects, number_relations, boolean_azure


class Neo4j:
    def __init__(self, arguments, extract_date_int, boolean_azure):
        # remote computers that run requests with their number of core
        if len(arguments.cluster) > 0:
            arguments.nb_chunks = 0
            self.parallelRequest = self.parallelRequestCluster
            self.parallelWriteRequest = self.parallelWriteRequestCluster
            self.writeRequest = self.ClusterWriteRequest

            self.cluster = {}
            list_nodes = arguments.cluster.split(",")
            for node in list_nodes:
                try:
                    ip, port, nCore = node.split(":")
                    self.cluster[ip + ":" + port] = int(nCore)
                    arguments.nb_chunks += 20 * int(nCore)
                except ValueError as e:
                    logger.print_error(
                        "An error occured while parsing the cluster argument. The correct syntax is --cluster ip1:port1:nCores1,ip2:port2:nCores2,etc"
                    )
                    logger.print_error(e)
                    sys.exit(-1)
            if len(self.cluster) == 1:
                # No need to use distributed write requests
                # if there is only one computer
                self.writeRequest = self.simpleRequest
                self.parallelWriteRequest = self.parallelRequestCluster

        else:
            self.parallelRequest = self.parallelRequestLegacy
            self.parallelWriteRequest = self.parallelRequestLegacy
            self.writeRequest = self.simpleRequest

        self.boolean_azure = boolean_azure

        self.extract_date = self.set_extract_date(str(extract_date_int))

        recursive_level = arguments.level
        self.password_renewal = int(arguments.renewal_password)

        properties = "MemberOf|HasSession|AdminTo|AllExtendedRights|AddMember|ForceChangePassword|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|ExecuteDCOM|AllowedToDelegate|ReadLAPSPassword|Contains|GpLink|AddAllowedToAct|AllowedToAct|SQLAdmin|ReadGMSAPassword|HasSIDHistory|CanPSRemote|AddSelf|WriteSPN|AddKeyCredentialLink|SyncLAPSPassword|CanExtractDCSecrets|CanLoadCode|CanLogOnLocallyOnDC|UnconstrainedDelegations|WriteAccountRestrictions|DumpSMSAPassword|Synced"

        if boolean_azure:
            properties += "|AZAKSContributor|AZAddMembers|AZAddOwner|AZAddSecret|AZAutomationContributor|AZAvereContributor|AZCloudAppAdmin|AZContains|AZContributor|AZExecuteCommand|AZGetCertificates|AZGetKeys|AZGetSecrets|AZGlobalAdmin|AZHasRole|AZKeyVaultContributor|AZLogicAppContributor|AZMGAddMember|AZMGAddOwner|AZMGAddSecret|AZMGAppRoleAssignment_ReadWrite_All|AZMGApplication_ReadWrite_All|AZMGDirectory_ReadWrite_All|AZMGGrantAppRoles|AZMGGrantRole|AZMGGroupMember_ReadWrite_All|AZMGGroup_ReadWrite_All|AZMGRoleManagement_ReadWrite_Directory|AZMGServicePrincipalEndpoint_ReadWrite_All|AZManagedIdentity|AZMemberOf|AZNodeResourceGroup|AZOwner|AZOwns|AZPrivilegedAuthAdmin|AZPrivilegedRoleAdmin|AZResetPassword|AZRunAs|AZScopedTo|AZUserAccessAdministrator|AZVMAdminLogin|AZVMContributor|AZWebsiteContributor"

        if arguments.rdp:
            properties += "|CanRDP"

        inbound_control_edges = "MemberOf|AddSelf|WriteSPN|AddKeyCredentialLink|AddMember|AllExtendedRights|ForceChangePassword|GenericAll|GenericWrite|WriteDacl|WriteOwner|Owns"

        try:
            self.all_requests = json.loads(
                (MODULES_DIRECTORY / "requests.json").read_text(
                    encoding="utf-8"
                )
            )
            for request_key in self.all_requests.keys():
                # Replace methods with python methods
                self.all_requests[request_key]["output_type"] = {
                    "Graph": Graph,
                    "list": list,
                    "dict": dict,
                }.get(
                    self.all_requests[request_key]["output_type"],
                )
                # Replace variables with their values in requests
                variables_to_replace = {
                    "$extract_date": int(self.extract_date),
                    "$password_renewal": int(self.password_renewal),
                    "$properties": properties,
                    "$recursive_level": int(recursive_level),
                    "$inbound_control_edges": inbound_control_edges,
                }
                for variable in variables_to_replace.keys():
                    self.all_requests[request_key][
                        "request"
                    ] = self.all_requests[request_key]["request"].replace(
                        variable, str(variables_to_replace[variable])
                    )

                # Replace postprocessing with python method
                if "postProcessing" in self.all_requests[request_key]:
                    self.all_requests[request_key]["postProcessing"] = {
                        "Neo4j.setDangerousInboundOnGPOs": self.setDangerousInboundOnGPOs,
                    }.get(self.all_requests[request_key]["postProcessing"])
        except json.JSONDecodeError as error:
            logger.print_error(
                f"Error while parsing neo4j requests from requests.json : \n{error}"
            )
            sys.exit(-1)
        except FileNotFoundError:
            logger.print_error(
                f"Neo4j request file not found : {MODULES_DIRECTORY / 'requests.json'} no such file."
            )
            sys.exit(-1)
        if arguments.gpo_low:
            del self.all_requests["unpriv_users_to_GPO_init"]
            del self.all_requests["unpriv_users_to_GPO_user_enforced"]
            del self.all_requests["unpriv_users_to_GPO_user_not_enforced"]
            del self.all_requests["unpriv_users_to_GPO_computer_enforced"]
            del self.all_requests["unpriv_users_to_GPO_computer_not_enforced"]

        else:  # Deep version of GPO requests
            del self.all_requests["unpriv_users_to_GPO"]

        try:
            # Setup driver
            self.driver = GraphDatabase.driver(
                arguments.bolt,
                auth=(arguments.username, arguments.password),
                encrypted=False,
            )

            self.arguments = arguments
            self.cache_enabled = arguments.cache
            self.cache = cache_class.Cache(arguments)

        except Exception as e:
            logger.print_error("Connection to neo4j database impossible.")
            logger.print_error(e)
            sys.exit(-1)

    def close(self):
        self.driver.close()

    @staticmethod
    def executeParallelRequest(
        value, identifier, query, arguments, output_type, server
    ):
        """This function is used in multiprocessing pools
        to execute multiple query parts in parallel"""
        q = query.replace("PARAM1", str(value)).replace(
            "PARAM2", str(identifier)
        )
        result = []
        bolt = server if server.startswith("bolt://") else "bolt://" + server
        driver = GraphDatabase.driver(
            bolt,
            auth=(arguments.username, arguments.password),
            encrypted=False,
        )
        with driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(q):
                        result.append(record["p"])
                        # Quick way to handle multiple records
                        # (e.g., RETURN p, p2)
                        if "p2" in record:
                            result.append(record["p2"])
                    try:
                        result = Neo4j.computePathObject(result)
                    except Exception as e:
                        logger.print_error(
                            "An error while computing path object of this query:\n"
                            + q
                        )
                        logger.print_error(e)

                else:
                    result = tx.run(q)
                    if output_type is list:
                        result = result.values()
                    else:  # then it should be dict ?
                        result = result.data()

        return result

    @staticmethod
    def process_request(self, request_key):
        if self.cache_enabled:  # If cache enable, try to retrieve from cache
            result = self.cache.retrieveCacheEntry(request_key)
            if result is None:
                result = []
            if result is not False:  # Sometimes result = []
                logger.print_debug(
                    "From cache : %s - %d objects"
                    % (self.all_requests[request_key]["name"], len(result))
                )
                self.all_requests[request_key]["result"] = result
                return result

        request = self.all_requests[request_key]
        logger.print_debug("Requesting : %s" % request["name"])
        start = time.time()
        result = []

        if "scope_query" in request:
            with self.driver.session() as session:
                with session.begin_transaction() as tx:
                    scopeQuery = request["scope_query"]
                    if tx.run(scopeQuery).value() != []:
                        scopeSize = tx.run(scopeQuery).value()[0]
                    else:
                        scopeSize = 0

            part_number = int(self.arguments.nb_chunks)
            part_number = min(scopeSize, part_number)

            print(f"scope size : {str(scopeSize)} | nb chunks : {part_number}")
            items = []
            space = np.linspace(0, scopeSize, part_number + 1, dtype=int)
            output_type = self.all_requests[request_key]["output_type"]

            # Divide the request with SKIP & LIMIT
            for i in range(len(space) - 1):
                items.append(
                    [
                        space[i],
                        space[i + 1] - space[i],
                        request["request"],
                        self.arguments,
                        output_type,
                    ]
                )

            if "is_a_write_request" in request:
                result = self.parallelWriteRequest(self, items)
            else:
                result = self.parallelRequest(self, items)

        elif "is_a_write_request" in request:  # Not parallelized write request
            result = self.writeRequest(self, request_key)
        else:  # Simple not parallelized read request
            result = self.simpleRequest(self, request_key)

        if result is None:
            result = []

        self.cache.createCacheEntry(request_key, result)
        logger.print_warning(
            timer_format(time.time() - start) + " - %d objects" % len(result)
        )

        if "postProcessing" in request:
            request["postProcessing"](self, result)

        request["result"] = result
        return result

    @staticmethod
    def simpleRequest(self, request_key):
        request = self.all_requests[request_key]
        output_type = request["output_type"]
        result = []
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(request["request"]):
                        result.append(record["p"])
                        # Quick way to handle multiple records
                        # (e.g., RETURN p, p2)
                        if "p2" in record:
                            result.append(record["p2"])
                    result = self.computePathObject(result)
                else:
                    result = tx.run(request["request"])
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()
        return result

    @staticmethod
    def ClusterWriteRequest(self, request_key):
        """This function ensure that simple write
        queries are executed to all nodes of a cluster"""
        starting_time = time.time()
        cluster_state = {server: False for server in self.cluster.keys()}
        query = self.all_requests[request_key]["request"]
        items = [  # Create all requests to do
            (
                -1,
                -1,
                query,
                self.arguments,
                self.all_requests[request_key]["output_type"],
                server,
            )
            for server in self.cluster.keys()
        ]

        with mp.Pool(len(self.cluster)) as pool:
            result = []
            tasks = {}
            for item in items:
                tasks[item[5]] = pool.apply_async(
                    self.executeParallelRequest, item
                )
            while not all(task.ready() for task in tasks.values()):
                time.sleep(0.01)
                for server in tasks.keys():
                    if tasks[server].ready() and not cluster_state[server]:
                        cluster_state[server] = True
                        logger.print_success(
                            "Write query executed by "
                            + server
                            + " in "
                            + str(round(time.time() - starting_time, 2))
                            + "s."
                        )
            temp_results = [task.get() for task in tasks.values()]
            result = temp_results[0]
            # Same request executed on every node, we only need the result once
        return result

    @staticmethod
    def parallelRequestCluster(self, items):
        """parallelRequestCluster is able to distribute parts of a
        complex request to multiple computers"""
        if len(items) == 0:
            return []
        output_type = items[0][4]
        # Total CPU units of all node of the cluster
        max_parallel_requests = sum(self.cluster.values())

        result = []
        requestList = items.copy()

        pbar = tqdm.tqdm(
            total=len(requestList), desc="Cluster participation:\n"
        )

        temp_results = []

        def process_completed_task(
            number_of_retrieved_objects, task, active_jobs, jobs_done, pbar
        ):
            temporary_result = task.get()
            # Update displayed number of retrieved objects
            if output_type == list:
                if len(temporary_result) > 0:
                    for sublist in temporary_result:
                        number_of_retrieved_objects += len(sublist)
            elif output_type == dict or output_type == Graph:
                number_of_retrieved_objects += len(temporary_result)

            temporary_result = None

            active_jobs[server].remove(task)
            jobs_done[server] += 1
            total_jobs_done = sum(jobs_done.values())
            cluster_participation = ""
            for server_running in jobs_done:
                server_name = server_running.split(":")[0]
                cluster_participation += (
                    server_name
                    + ": "
                    + str(
                        int(
                            round(
                                100
                                * jobs_done[server_running]
                                / total_jobs_done,
                                0,
                            )
                        )
                    )
                    + "% "
                )
            pbar.set_description(
                cluster_participation
                + "| "
                + str(number_of_retrieved_objects)
                + " objects"
            )
            pbar.refresh()
            pbar.update(1)
            return number_of_retrieved_objects

        with mp.Pool(processes=max_parallel_requests) as pool:
            # Dict that keep track of which server is executing which requests
            active_jobs = dict((server, []) for server in self.cluster)

            # Dict that keep track of how many queries each server did
            jobs_done = dict((server, 0) for server in self.cluster)

            # Counter to keep track of how many objects have been retrieved
            number_of_retrieved_objects = 0

            while len(requestList) > 0:
                time.sleep(0.01)

                for server, max_jobs in self.cluster.items():
                    if len(requestList) == 0:
                        break
                    for task in active_jobs[server]:
                        if task.ready():
                            number_of_retrieved_objects = (
                                process_completed_task(
                                    number_of_retrieved_objects,
                                    task,
                                    active_jobs,
                                    jobs_done,
                                    pbar,
                                )
                            )

                    if len(active_jobs[server]) < max_jobs:
                        item = requestList.pop()
                        (
                            value,
                            identifier,
                            query,
                            arguments,
                            output_type,
                        ) = item

                        task = pool.apply_async(
                            self.executeParallelRequest,
                            (
                                value,
                                identifier,
                                query,
                                arguments,
                                output_type,
                                server,
                            ),
                        )
                        temp_results.append(task)
                        active_jobs[server].append(task)

            # Waiting for every task to finish
            # Not in the main loop for better efficiency

            while not all(len(tasks) == 0 for tasks in active_jobs.values()):
                time.sleep(0.01)
                for server, max_jobs in self.cluster.items():
                    for task in active_jobs[server]:
                        if task.ready():
                            number_of_retrieved_objects = (
                                process_completed_task(
                                    number_of_retrieved_objects,
                                    task,
                                    active_jobs,
                                    jobs_done,
                                    pbar,
                                )
                            )
            for r in temp_results:
                result += r.get()
        pbar.close()
        return result

    @staticmethod
    def parallelRequestLegacy(self, items):
        """parallelRequestLegacy is the default way of slicing requests
        in smaller requests to parallelize it"""
        items = [  # Add bolt to items
            (
                value,
                identifier,
                query,
                arguments,
                output_type,
                self.arguments.bolt,
            )
            for value, identifier, query, arguments, output_type in items
        ]

        with mp.Pool(mp.cpu_count()) as pool:
            result = []
            for _ in tqdm.tqdm(
                pool.istarmap(self.executeParallelRequest, items),
                total=len(items),
            ):
                result += _
        return result

    @staticmethod
    def setDangerousInboundOnGPOs(self, data):
        print("Entering Post processing")
        ids = []
        for d in data:
            ids.append(d.nodes[-1].id)
        q = (
            "MATCH (g) WHERE ID(g) in "
            + str(ids)
            + " SET g.dangerous_inbound=TRUE"
        )
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(q)

    @staticmethod
    def set_extract_date(date):
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])
        date_time = datetime.datetime(year, month, day)
        return time.mktime(date_time.timetuple())

    @staticmethod
    def requestNamesAndHash(server, username, password):
        """requestNamesAndHash returns the md5 hash of the
        concatenation of all nodes names and is used by verify_integrity()"""
        q = "MATCH (a) RETURN ID(a),a.name"
        bolt = "bolt://" + server

        driver = GraphDatabase.driver(
            bolt,
            auth=(username, password),
            encrypted=False,
        )

        names = ""

        with driver.session() as session:
            with session.begin_transaction() as tx:
                for record in tx.run(q):
                    names += str(record["a.name"])

        driver.close()
        hash = md5(names.encode(), usedforsecurity=False).hexdigest()
        logger.print_debug("Hash for " + server + " is " + hash)
        return hash

    @staticmethod
    def verify_integrity(self):
        """
        Hash the names of all nodes to avoid obvious errors
        (like trying to use two completely different neo4j databases)
        """
        if len(self.cluster) == 1:
            return
        startig_time = time.time()
        logger.print_debug("Starting integrity check")
        hashes = []
        temp_results = []
        username = self.arguments.username
        password = self.arguments.password

        with mp.Pool(processes=self.arguments.nb_cores) as pool:
            for server in self.cluster.keys():
                task = pool.apply_async(
                    Neo4j.requestNamesAndHash,
                    (
                        server,
                        username,
                        password,
                    ),
                )
                temp_results.append(task)

            for task in temp_results:
                try:
                    hashes.append(task.get())
                except Exception as e:
                    errorMessage = "Connection to neo4j database refused."
                    logger.print_error(errorMessage)
                    logger.print_error(e)
                    sys.exit(-1)

        if all(hash == hashes[0] for hash in hashes):
            logger.print_success("All databases seems to be the same.")
        else:
            logger.print_error(
                "Be careful, the database on the nodes seems different."
            )

        stopping_time = time.time()

        logger.print_warning(
            "Integrity check took "
            + str(round(stopping_time - startig_time, 2))
            + "s"
        )

    @staticmethod
    def parallelWriteRequestCluster(self, items):
        """parallelWriteRequestCluster ensures that a parallelised write
        request is done to each neo4j database"""
        starting_time = time.time()
        result = []
        if len(items) == 0:
            return result

        output_type = items[0][4]

        small_requests_to_do = {
            server: [
                (value, identifier, query, arguments, output_type, server)
                for value, identifier, query, arguments, output_type in items
            ]
            for server in self.cluster.keys()
        }
        cluster_state = {server: False for server in self.cluster.keys()}

        pbar = tqdm.tqdm(
            total=sum(len(lst) for lst in small_requests_to_do.values()),
            desc="Executing write query to all cluster nodes",
        )

        # Total CPU units of all node of the cluster
        max_parallel_requests = sum(self.cluster.values())

        temp_results = []

        with mp.Pool(processes=max_parallel_requests) as pool:
            # Dict that keep track of which server is executing which requests
            active_jobs = dict((server, []) for server in self.cluster)

            while sum(len(lst) for lst in small_requests_to_do.values()) > 0:
                time.sleep(0.01)

                for server, max_jobs in self.cluster.items():
                    if (
                        sum(len(lst) for lst in small_requests_to_do.values())
                        == 0
                    ):
                        break
                    for task in active_jobs[server]:
                        if task.ready():
                            active_jobs[server].remove(task)
                            pbar.update(1)
                    if (
                        len(small_requests_to_do[server]) == 0
                        and len(active_jobs[server]) == 0
                        and not cluster_state[server]
                    ):
                        cluster_state[server] = True
                        logger.print_success(
                            "Write request executed by "
                            + server
                            + " in "
                            + str(round(time.time() - starting_time, 2))
                            + "s."
                        )
                    if (
                        len(active_jobs[server]) < max_jobs
                        and len(small_requests_to_do[server]) > 0
                    ):
                        item = small_requests_to_do[server].pop()
                        (
                            value,
                            identifier,
                            query,
                            arguments,
                            output_type,
                            server,
                        ) = item

                        task = pool.apply_async(
                            self.executeParallelRequest,
                            (
                                value,
                                identifier,
                                query,
                                arguments,
                                output_type,
                                server,
                            ),
                        )
                        if server == next(iter(self.cluster)):
                            temp_results.append(task)
                        active_jobs[server].append(task)

            # Waiting for every task to finish
            # Not in the main loop for better efficiency

            while not all(len(tasks) == 0 for tasks in active_jobs.values()):
                time.sleep(0.01)
                for server, max_jobs in self.cluster.items():
                    for task in active_jobs[server]:
                        if task.ready():
                            active_jobs[server].remove(task)
                            pbar.update(1)
                    if (
                        len(small_requests_to_do[server]) == 0
                        and len(active_jobs[server]) == 0
                        and not cluster_state[server]
                    ):
                        cluster_state[server] = True
                        logger.print_success(
                            "Write request executed to "
                            + server
                            + " in "
                            + str(round(time.time() - starting_time, 2))
                            + "s."
                        )
            for r in temp_results:
                result += r.get()
        pbar.close()
        return result

    @classmethod
    def computePathObject(cls, Paths):
        """computePathObject allows object to be serialized and should
        be used when output_type == Graph"""
        final_paths = []
        for path in Paths:
            if path is not None:
                nodes = []
                for relation in path.relationships:
                    for node in relation.nodes:
                        label = [i for i in node.labels if 'Base' not in i][0] # e.g. : {"User","Base"} -> "User" or {"User","AZBase"} -> "User"
                        nodes.append(
                            Node(
                                node.id,
                                label,
                                node["name"],
                                node["domain"],
                                relation.type,
                            )
                        )
                        break

                nodes.append(
                    Node(
                        path.end_node.id,
                        [i for i in path.end_node.labels if 'Base' not in i][0],
                        path.end_node["name"],
                        path.end_node["domain"],
                        "",
                    )
                )

                final_paths.append(Path(nodes))

        return final_paths
