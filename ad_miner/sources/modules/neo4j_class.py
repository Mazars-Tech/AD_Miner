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
from neo4j import GraphDatabase

from ad_miner.sources.modules import cache_class, logger
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.utils import timer_format

MODULES_DIRECTORY = pathlib(__file__).parent


def pre_request_date(arguments):
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
    return date_lastlogon["last"]


class Neo4j:
    def __init__(self, arguments, extract_date_int):
        # remote computers that run requests with their number of core
        if len(arguments.cluster) > 0:
            self.parallelRequest = self.parallelRequestOnCluster

            self.cluster = {}
            list_nodes = arguments.cluster.split(",")
            for node in list_nodes:
                try:
                    ip, port, nCore = node.split(":")
                    self.cluster[ip + ":" + port] = int(nCore)
                except ValueError as e:
                    logger.print_error(
                        "An error occured while parsing the cluster argument. The correct syntax is --cluster ip1:port1:nCores1,ip2:port2:nCores2,etc"
                    )
                    logger.print_error(e)
                    sys.exit(-1)
        else:
            self.parallelRequest = self.parallelRequestLegacy

        extract_date = self.set_extract_date(str(extract_date_int))

        recursive_level = arguments.level
        self.password_renewal = int(arguments.renewal_password)
        # We only use the Azure relationships when requested to do so

        properties = "MemberOf|HasSession|AdminTo|AllExtendedRights|AddMember|ForceChangePassword|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|ExecuteDCOM|AllowedToDelegate|ReadLAPSPassword|Contains|GpLink|AddAllowedToAct|AllowedToAct|SQLAdmin|ReadGMSAPassword|HasSIDHistory|CanPSRemote|AddSelf|WriteSPN|AddKeyCredentialLink|SyncLAPSPassword|CanExtractDCSecrets"

        if arguments.azure:
            properties += "|AZAddMembers|AZContains|AZContributor|AZGetCertificates|AZGetKeys|AZGetSecrets|AZGlobalAdmin|AZOwns|AZPrivilegedRoleAdmin|AZResetPassword|AZUserAccessAdministrator|AZAppAdmin|AZCloudAppAdmin|AZRunsAs|AZKeyVaultContributor|AddSelf|WriteSPN|AddKeyCredentialLink|AZAddSecret|AZAvereContributor|AZExecuteCommand|AZGrant|AZGrantSelf|AZHasRole|AZMemberOf|AZOwner|AZVMAdminLogin"

        if arguments.rdp:
            properties += "|CanRDP"

        inbound_control_edges = "MemberOf|AddSelf|WriteSPN|AddKeyCredentialLink|AddMember|AllExtendedRights|ForceChangePassword|GenericAll|GenericWrite|WriteDacl|WriteOwner|Owns"

        try:
            # TODO add comments in json
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
                )  # TODO maybe add a check for the request type ?
                # Replace variables with their values in requests
                variables_to_replace = {
                    "$extract_date": int(extract_date),
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
                if "postprocessing" in self.all_requests[request_key]:
                    self.all_requests[request_key]["postprocessing"] = {
                        "Neo4j.setDangerousInboundOnGPOs": self.setDangerousInboundOnGPOs,
                    }.get(self.all_requests[request_key]["postprocessing"])
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
    def run(value, identifier, query, arguments, output_type):
        q = query.replace("PARAM1", str(value)).replace(
            "PARAM2", str(identifier)
        )
        result = []
        driver = GraphDatabase.driver(
            arguments.bolt,
            auth=(arguments.username, arguments.password),
            encrypted=False,
        )
        with driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(q):
                        result.append(record["p"])

                else:
                    result = tx.run(q)
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()

        if output_type is not dict:
            try:
                result = Neo4j.computePathObject(result)
            except Exception as e:
                logger.print_error(
                    "An error occured during the transformation of a request result."
                )
                errorMessage = "The exact query was:\n" + q
                logger.print_error(errorMessage)
                logger.print_error(e)

        return result

    @staticmethod
    def process_request(self, request, output_type):
        start = time.time()
        result = []

        if "scope_query" in request:
            result = self.parallelRequest(self, request, output_type)
        else:
            result = self.simpleRequest(self, request, output_type)
        request["result"] = result
        logger.print_time(
            timer_format(time.time() - start) + " - %d objects" % len(result)
        )

    @staticmethod
    def simpleRequest(self, request, output_type):
        result = None  # TODO fix
        return result

    @staticmethod
    def parallelRequestOnCluster(self, request, output_type):
        result = None  # TODO fix
        return result

    @staticmethod
    def parallelRequestLegacy(self, request, output_type):
        result = None  # TODO fix
        return result

    @staticmethod
    def request(self, request, output_type):
        start = time.time()
        if self.cache_enabled:
            result = self.cache.retrieveCacheEntry(request["filename"])
            if result != False:
                if len(result):
                    logger.print_debug(
                        "From cache : %s - %d objects"
                        % (request["name"], len(result))
                    )
                    # self.cache.createCsvFileFromRequest(
                    #    request["filename"], result, output_type
                    # )
                return result
        logger.print_debug("Requesting : %s" % request["name"])

        # if output_type is Graph:
        result = []
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                if "PARAM" in request["request"]:
                    scopeQuery = request["scope_query"]
                    scopeSize = tx.run(scopeQuery).value()[0]
                    part_number = int(self.arguments.nb_chunks)
                    nb_cores = int(self.arguments.nb_cores)
                    print(
                        f"scope size : {str(scopeSize)} | nb chunks : {part_number} | nb cores : {nb_cores}"
                    )

                    part_number = min(
                        scopeSize, part_number
                    )  # no more requests than scope size
                    items = []
                    space = np.linspace(
                        0, scopeSize, part_number + 1, dtype=int
                    )
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

                    with mp.Pool(nb_cores) as pool:
                        # results = pool.starmap(self.run, tqdm.tqdm(items, total=len(items)))
                        # with open("temporary.txt", "a") as f:
                        #     f.write("\n")
                        #     f.write("-------------------------\n")
                        #     f.write(f"{self.arguments.cache_prefix} : {request['name']} \n")
                        result = []
                        for _ in tqdm.tqdm(
                            pool.istarmap(self.run, items), total=len(items)
                        ):
                            result += _

                    # result = self.computePathObject(result)

                else:
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

        self.cache.createCacheEntry(request["filename"], result)
        # self.cache.createCsvFileFromRequest(request["filename"], result, output_type)
        logger.print_time(
            timer_format(time.time() - start) + " - %d objects" % len(result)
        )

        if "postProcessing" in request:
            request["postProcessing"](self, result)

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
        # print(q)
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
    def verify_integrity(self, cluster):
        """
        Hash the names of all nodes to verify that the same database is on every node.
        """
        startig_time = time.time()
        logger.print_debug("Starting integrity check")
        hashes = []
        temp_results = []
        username = self.arguments.username
        password = self.arguments.password

        with mp.Pool(processes=self.arguments.nb_cores) as pool:
            for server in cluster.keys():
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

        logger.print_time(
            "Integrity check took "
            + str(round(stopping_time - startig_time, 2))
            + "s"
        )

    @staticmethod
    def requestOnRemote(
        value, identifier, query, arguments, output_type, server
    ):
        start_time = time.time()
        q = query.replace("PARAM1", str(value)).replace(
            "PARAM2", str(identifier)
        )
        result = []
        bolt = "bolt://" + server
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

                else:
                    result = tx.run(q)
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()

        if output_type is not dict:
            try:
                result = Neo4j.computePathObject(result)
            except Exception as e:
                logger.print_error(
                    "An error occured during the transformation of a request result."
                )
                errorMessage = (
                    "The database used is "
                    + server
                    + " and the exact query was:\n"
                    + q
                )
                logger.print_error(errorMessage)
                logger.print_error(e)

        driver.close()  # TODO pas de base ?
        return result

    @staticmethod
    def writeRequestOnRemote(query, output_type, server, username, password):
        start_time = time.time()
        result = []
        bolt = "bolt://" + server
        driver = GraphDatabase.driver(
            bolt,
            auth=(username, password),
            encrypted=False,
        )

        with driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(query):
                        result.append(record["p"])
                        # Quick way to handle multiple records
                        # (e.g., RETURN p, p2)
                        if "p2" in record:
                            result.append(record["p2"])
                    result = Neo4j.computePathObject(result)
                else:
                    result = tx.run(query)
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()

        driver.close()  # TODO pas de base ?
        duration = round(time.time() - start_time, 2)
        logger.print_debug(
            "Write query executed to " + server + " in " + str(duration) + "s"
        )
        return result

    @staticmethod
    def distributeRequestsOnRemote(self, request, output_type):
        cluster = self.cluster
        # Total CPU units of all node of the cluster
        max_parallel_requests = sum(cluster.values())

        start = time.time()
        if self.cache_enabled:
            result = self.cache.retrieveCacheEntry(request["filename"])
            if result != False:
                if len(result):
                    logger.print_debug(
                        "From cache : %s - %d objects"
                        % (request["name"], len(result))
                    )
                    # self.cache.createCsvFileFromRequest(
                    #    request["filename"], result, output_type
                    # )
                return result
        logger.print_debug("Requesting : %s" % request["name"])

        result = []
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                if "PARAM" in request["request"]:
                    scopeQuery = request["scope_query"]
                    scopeSize = tx.run(scopeQuery).value()[0]
                    part_number = self.arguments.nb_chunks
                    # It is assumed here that no one will set number of chunks to the default.
                    # If left to default but cluster is used it is better to choose something
                    # like chunk = 20 x total number of cores in the cluster.
                    if part_number == mp.cpu_count():
                        part_number = 20 * max_parallel_requests
                    nb_cores = int(max_parallel_requests)
                    print(
                        f"scope size : {str(scopeSize)} | nb chunks : {part_number} | nb cores : {nb_cores}"
                    )

                    part_number = min(scopeSize, part_number)
                    items = []
                    space = np.linspace(
                        0, scopeSize, part_number + 1, dtype=int
                    )
                    # Divide the requests with SKIP & LIMIT
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

                    requestList = items.copy()

                    pbar = tqdm.tqdm(
                        total=len(requestList), desc="Cluster participation:\n"
                    )

                    temp_results = []

                    with mp.Pool(processes=max_parallel_requests) as pool:
                        # Dict that keep track of which server is executing which requests
                        active_jobs = dict((server, []) for server in cluster)

                        # Dict that keep track of how many queries each server did
                        jobs_done = dict((server, 0) for server in cluster)

                        # Counter to keep track of how many objects have been retrieved
                        number_of_retrieved_objects = 0

                        while len(requestList) > 0:
                            time.sleep(0.01)

                            for server, max_jobs in cluster.items():
                                if len(requestList) == 0:
                                    break
                                for task in active_jobs[server]:
                                    if (
                                        task.ready()
                                    ):  # Meaning that a task have been finished on a remote server
                                        temporary_result = task.get()

                                        if output_type == list:
                                            if len(temporary_result) > 0:
                                                for (
                                                    sublist
                                                ) in temporary_result:
                                                    number_of_retrieved_objects += len(
                                                        sublist
                                                    )
                                        elif (
                                            output_type == dict
                                            or output_type == Graph
                                        ):
                                            number_of_retrieved_objects += len(
                                                temporary_result
                                            )

                                        temporary_result = None

                                        active_jobs[server].remove(task)
                                        task = None
                                        jobs_done[server] += 1
                                        total_jobs_done = sum(
                                            jobs_done.values()
                                        )
                                        cluster_participation = ""
                                        for server_running in jobs_done:
                                            server_name = server_running.split(
                                                ":"
                                            )[0]
                                            cluster_participation += (
                                                server_name
                                                + ": "
                                                + str(
                                                    int(
                                                        round(
                                                            100
                                                            * jobs_done[
                                                                server_running
                                                            ]
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
                                        Neo4j.requestOnRemote,
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

                        while not all(
                            len(tasks) == 0 for tasks in active_jobs.values()
                        ):
                            time.sleep(0.01)
                            for server, max_jobs in cluster.items():
                                for task in active_jobs[server]:
                                    if (
                                        task.ready()
                                    ):  # Meaning that a task have been finished on a remote server
                                        temporary_result = task.get()

                                        if output_type == list:
                                            if len(temporary_result) > 0:
                                                for (
                                                    sublist
                                                ) in temporary_result:
                                                    number_of_retrieved_objects += len(
                                                        sublist
                                                    )
                                        elif (
                                            output_type == dict
                                            or output_type == Graph
                                        ):
                                            number_of_retrieved_objects += len(
                                                temporary_result
                                            )

                                        temporary_result = None

                                        active_jobs[server].remove(task)
                                        task = None
                                        jobs_done[server] += 1
                                        total_jobs_done = sum(
                                            jobs_done.values()
                                        )
                                        cluster_participation = ""
                                        for server_running in jobs_done:
                                            server_name = server_running.split(
                                                ":"
                                            )[0]
                                            cluster_participation += (
                                                server_name
                                                + ": "
                                                + str(
                                                    int(
                                                        round(
                                                            100
                                                            * jobs_done[
                                                                server_running
                                                            ]
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

                        for r in temp_results:
                            result += r.get()

                    pbar.close()

                elif (
                    "SET" in request["request"]
                    or "MERGE" in request["request"]
                    or "DELETE" in request["request"]
                ):
                    # Si c'est une requête d'écriture il faut la faire
                    # sur tous les noeuds du cluster
                    query = request["request"]
                    username = self.arguments.username
                    password = self.arguments.password
                    results = []
                    temp_results = []

                    with mp.Pool(processes=self.arguments.nb_cores) as pool:
                        for server in cluster.keys():
                            task = pool.apply_async(
                                Neo4j.writeRequestOnRemote,
                                (
                                    query,
                                    output_type,
                                    server,
                                    username,
                                    password,
                                ),
                            )
                            temp_results.append(task)

                        for task in temp_results:
                            results.append(task.get())

                    result = results[0]

                else:
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

        self.cache.createCacheEntry(request["filename"], result)
        logger.print_time(
            timer_format(time.time() - start) + " - %d objects" % len(result)
        )

        if "postProcessing" in request:
            request["postProcessing"](self, result)
        return result

    @classmethod
    def computePathObject(cls, Paths):
        final_paths = []
        for path in Paths:
            if not path is None:
                nodes = []
                for relation in path.relationships:
                    for node in relation.nodes:
                        label = next(
                            iter(node.labels.difference({"Base"}))
                        )  # e.g. : {"User","Base"} -> "User"

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
                        next(iter(path.end_node.labels.difference({"Base"}))),
                        path.end_node["name"],
                        path.end_node["domain"],
                        "",
                    )
                )

                final_paths.append(Path(nodes))

        return final_paths
