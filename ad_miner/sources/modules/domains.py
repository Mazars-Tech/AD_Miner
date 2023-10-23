import json
import time

from urllib.parse import quote
from os.path import sep

from ad_miner.sources.modules import generic_formating
from ad_miner.sources.modules import logger
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.histogram_class import Histogram
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.utils import (days_format, grid_data_stringify,
                                           timer_format)


class Domains:
    # we are manipulating Path and Node Objects
    # https://neo4j.com/docs/api/python-driver/current/api.html#path
    # https://neo4j.com/docs/api/python-driver/current/api.html#node

    def __init__(self, arguments, neo4j):
        start = time.time()
        logger.print_debug("Computing domains objects")
        self.arguments = arguments
        self.neo4j = neo4j
        self.domains = neo4j.all_requests["domains"]["result"]
        self.objects_to_domain_admin = neo4j.all_requests["objects_to_domain_admin"][
            "result"
        ]
        self.objects_to_unconstrained_delegation = neo4j.all_requests[
            "objects_to_unconstrained_delegation"
        ]["result"]
        self.objects_to_unconstrained_delegation_2 = neo4j.all_requests[
            "users_to_unconstrained_delegation"
        ]["result"]
        self.domain_map_trust = neo4j.all_requests["domain_map_trust"]["result"]
        self.domains_list = neo4j.all_requests["domains"]["result"]
        self.objects_to_dcsync = neo4j.all_requests["objects_to_dcsync"]["result"]
        self.unpriv_users_to_GPO = None

        self.computers_with_last_connection_date = neo4j.all_requests[
            "computers_not_connected_since"
        ]["result"]

        self.computers_not_connected_since_60 = list(
            filter(
                lambda computer: int(computer["days"]) > 60,
                self.computers_with_last_connection_date,
            )
        )

        self.computers_nb_domain_controllers = neo4j.all_requests[
            "nb_domain_controllers"
        ]["result"]
        self.users_nb_domain_admins = neo4j.all_requests["nb_domain_admins"]["result"]

        dico_ghost_computer = {}
        if self.computers_not_connected_since_60 != []:
            for dico in self.computers_not_connected_since_60:
                dico_ghost_computer[dico["name"]] = True
        self.dico_ghost_computer = dico_ghost_computer

        self.users_dormant_accounts = neo4j.all_requests["dormant_accounts"]["result"]
        self.users_pwd_not_changed_since = neo4j.all_requests["password_last_change"][
            "result"
        ]
        self.users_pwd_not_changed_since_3months = (
            [
                user
                for user in self.users_pwd_not_changed_since
                if user["days"] > neo4j.password_renewal
            ]
            if self.users_pwd_not_changed_since is not None
            else None
        )
        self.users_pwd_not_changed_since_1y = (
            [user for user in self.users_pwd_not_changed_since if user["days"] > 365]
            if self.users_pwd_not_changed_since is not None
            else None
        )
        self.groups = neo4j.all_requests["nb_groups"]["result"]

        dico_ghost_user = {}
        if self.users_pwd_not_changed_since_3months != None:
            for dico in self.users_pwd_not_changed_since_3months:
                dico_ghost_user[dico["user"]] = True
        self.dico_ghost_user = dico_ghost_user
        dico_dc_computer = {}
        if self.computers_nb_domain_controllers != None:
            for dico in self.computers_nb_domain_controllers:
                dico_dc_computer[dico["name"]] = True
        self.dico_dc_computer = dico_dc_computer

        dico_da_group = {}
        if self.groups != None:
            for dico in self.groups:
                if dico.get("da"):
                    dico_da_group[dico["name"]] = True
        self.dico_da_group = dico_da_group

        dico_user_da = {}
        if self.users_nb_domain_admins != []:
            for dico in self.users_nb_domain_admins:
                dico_user_da[dico["name"]] = True
        self.dico_user_da = dico_user_da

        self.admin_list = []
        for admin in self.users_nb_domain_admins:
            self.admin_list.append(admin["name"])

        if not arguments.gpo_low:
            self.unpriv_users_to_GPO_init = neo4j.all_requests[
                "unpriv_users_to_GPO_init"
            ]["result"]
            self.unpriv_users_to_GPO_user_enforced = neo4j.all_requests[
                "unpriv_users_to_GPO_user_enforced"
            ]["result"]
            self.unpriv_users_to_GPO_computer_enforced = neo4j.all_requests[
                "unpriv_users_to_GPO_computer_not_enforced"
            ]["result"]
            self.unpriv_users_to_GPO_user_not_enforced = neo4j.all_requests[
                "unpriv_users_to_GPO_user_not_enforced"
            ]["result"]
            self.unpriv_users_to_GPO_computer_not_enforced = neo4j.all_requests[
                "unpriv_users_to_GPO_computer_not_enforced"
            ]["result"]
        else:
            self.unpriv_users_to_GPO = neo4j.all_requests["unpriv_users_to_GPO"][
                "result"
            ]
        self.domain_OUs = neo4j.all_requests["domain_OUs"]["result"]
        self.objects_to_ou_handlers = neo4j.all_requests["objects_to_ou_handlers"][
            "result"
        ]
        self.nb_starting_nodes_to_ous = 0
        self.nb_ous_with_da = 0

        self.vuln_functional_level = neo4j.all_requests["vuln_functional_level"][
            "result"
        ]

        self.da_to_da = neo4j.all_requests["da_to_da"]["result"]
        self.collected_domains = neo4j.all_requests["nb_domain_collected"]["result"]
        self.crossDomain = 0

        self.number_of_gpo = 0
        self.number_of_OU = 0

        self.empty_groups = neo4j.all_requests["get_empty_groups"]["result"]
        self.empty_ous = neo4j.all_requests["get_empty_ous"]["result"]


        self.computers_to_domain_admin = {}
        self.users_to_domain_admin = {}
        self.groups_to_domain_admin = {}
        self.ou_to_domain_admin = {}
        self.gpo_to_domain_admin = {}
        self.domains_to_domain_admin = []

        self.computers_to_dcsync = {}
        self.users_to_dcsync = {}
        self.groups_to_dcsync = {}
        self.ou_to_dcsync = {}
        self.gpo_to_dcsync = {}

        self.computers_to_unconstrained_delegation = {}
        self.users_to_unconstrained_delegation = {}
        self.groups_to_unconstrained_delegation = {}
        self.ou_to_unconstrained_delegation = {}
        self.gpo_to_unconstrained_delegation = {}

        # For user accounts
        self.computers_to_unconstrained_delegation_2 = {}
        self.users_to_unconstrained_delegation_2 = {}
        self.groups_to_unconstrained_delegation_2 = {}
        self.ou_to_unconstrained_delegation_2 = {}
        self.gpo_to_unconstrained_delegation_2 = {}

        # main compromise path
        self.main_compromise_paths = {}
        self.number_paths_main_nodes = 0

        # 		for d in self.domain_map_trust:
        #                        print(d)

        # init variables : var[domain] = list

        self.paths_to_ou_handlers = {}

        for domain in self.domains:

            self.computers_to_domain_admin[domain[0]] = []
            self.users_to_domain_admin[domain[0]] = []
            self.groups_to_domain_admin[domain[0]] = []
            self.ou_to_domain_admin[domain[0]] = []
            self.gpo_to_domain_admin[domain[0]] = []

            self.computers_to_dcsync[domain[0]] = []
            self.users_to_dcsync[domain[0]] = []
            self.groups_to_dcsync[domain[0]] = []
            self.ou_to_dcsync[domain[0]] = []
            self.gpo_to_dcsync[domain[0]] = []

            self.computers_to_unconstrained_delegation[domain[0]] = []
            self.users_to_unconstrained_delegation[domain[0]] = []
            self.groups_to_unconstrained_delegation[domain[0]] = []
            self.ou_to_unconstrained_delegation[domain[0]] = []
            self.gpo_to_unconstrained_delegation[domain[0]] = []

            self.computers_to_unconstrained_delegation_2[domain[0]] = []
            self.users_to_unconstrained_delegation_2[domain[0]] = []
            self.groups_to_unconstrained_delegation_2[domain[0]] = []
            self.ou_to_unconstrained_delegation_2[domain[0]] = []
            self.gpo_to_unconstrained_delegation_2[domain[0]] = []

            self.paths_to_ou_handlers[domain[0]] = []

        self.genComputerNotConnectedSincePage()

        self.generatePathToOUHandlers(self)

        self.genDormantsUsersPage()
        self.genUsersPasswordNotChangedPage()

        self.genAllGroupsPage()

        self.genNumberOfDCPage()

        self.generatePathToDa()

        # self.generatePathToDcsync()

        self.generatePathToUnconstrainedDelegation()

        self.generatePathToUnconstrainedDelegation_2()

        self.generateDomainMapTrust()

        self.get_unpriv_users_to_GPO()
        self.get_domain_OUs()
        self.genDAPage()
        self.genInsufficientForestDomainsLevels()


        self.genDAToDAPaths()
        self.genDangerousPath()

        self.genEmptyGroups()
        self.genEmptyOUs()

        logger.print_time(timer_format(time.time() - start))

        # All groups



    def genDangerousPath(self):

        def analyse_cache(cache):
            if cache == None:
                return []
            dico_node_rel_node = {}
            for path in cache:
                for i in range(1, len(path.nodes)- 2):
                    node_rel_node_instance = f"{path.nodes[i].name} ⮕ {path.nodes[i].relation_type} ⮕ {path.nodes[i+1].name}"
                    if dico_node_rel_node.get(node_rel_node_instance):
                        dico_node_rel_node[node_rel_node_instance] +=1
                    else:
                        dico_node_rel_node[node_rel_node_instance] = 1

            return dict(sorted(dico_node_rel_node.items(), key=lambda item: item[1])[::-1][:100])

        dico_objects_to_da = analyse_cache(self.objects_to_domain_admin)
        dico_dcsync_to_da = analyse_cache(self.objects_to_dcsync)
        dico_da_to_da = analyse_cache(self.da_to_da)

        if self.objects_to_dcsync != None:
            len_dcsync = len(self.objects_to_dcsync)
        else:
            len_dcsync = 0

        if self.da_to_da != None:
            len_da_to_da = len(self.da_to_da)
        else:
            len_da_to_da = 0

        # Remove 1 to exclude the false positive of container USERS containing DOMAIN ADMIN group
        self.total_dangerous_paths = max(len_dcsync + len(self.objects_to_domain_admin) + len_da_to_da - 1, 0)

        page = Page(
            self.arguments.cache_prefix, "dangerous_paths_dcsync_to_da", "DCSync privileges to DA privileges", "dangerous_paths"
        )
        histo = Histogram()
        histo.setData(dico_dcsync_to_da, len_dcsync)
        page.addComponent(histo)
        page.render()

        page = Page(
            self.arguments.cache_prefix, "dangerous_paths_objects_to_da", "Objects to DA privileges", "dangerous_paths"
        )
        histo = Histogram()
        histo.setData(dico_objects_to_da, len(self.objects_to_domain_admin))
        page.addComponent(histo)
        page.render()

        page = Page(
            self.arguments.cache_prefix, "dangerous_paths_da_to_da", "DA privileges to DA privileges", "dangerous_paths"
        )
        histo = Histogram()
        histo.setData(dico_da_to_da, len_da_to_da)
        page.addComponent(histo)
        page.render()

        page = Page(
            self.arguments.cache_prefix, "dangerous_paths", "List of main dangerous paths", "dangerous_paths"
        )
        grid = Grid("dangerous paths")

        grid.addheader("Type of Graphs")
        dangerous_path_data = [
            {"Type of Graphs": grid_data_stringify({
                "value":"DCSync privileges to DA privileges",
                "link":"dangerous_paths_dcsync_to_da.html",
                "before_link": '<i class="bi bi-arrow-repeat"></i>'
                })
            },
            {"Type of Graphs": grid_data_stringify({
                "value":"Objects to DA privileges",
                "link":"dangerous_paths_objects_to_da.html",
                "before_link": '<i class="bi bi-chevron-double-up"></i>'
                })
            },
            {"Type of Graphs": grid_data_stringify({
                "value":"DA privileges to DA privileges",
                "link":"dangerous_paths_da_to_da.html",
                "before_link": '<i class="bi bi-arrow-left-right"></i>'
                })
            },
        ]

        grid.setData(dangerous_path_data)
        page.addComponent(grid)
        page.render()

        return self


    def genAllGroupsPage(self):
        if self.groups is None:
            return
        page = Page(
            self.arguments.cache_prefix, "groups", "List of all groups", "groups"
        )
        grid = Grid("Groups")
        grid.setheaders(["domain", "name"])
        group_extract = [
            {
                "domain": '<i class="bi bi-globe2"></i> ' + self.groups[k]["domain"],
                "name": '<i class="bi bi-gem" title="This group is domain admin"></i> '
                + self.groups[k]["name"]
                if self.groups[k].get("da")
                else '<i class="bi bi-people-fill"></i> ' + self.groups[k]["name"],
            }
            for k in range(len(self.groups))
        ]
        grid.setData(group_extract)
        page.addComponent(grid)
        page.render()

    # List of domain admins
    def genDAPage(self):
        if self.users_nb_domain_admins is None:
            self.max_da_per_domain = 0
            return
        page = Page(
            self.arguments.cache_prefix,
            "nb_domain_admins",
            "List of domain admins",
            "nb_domain_admins",
        )
        # Count the max number of domain admins per domain
        count_da = {}
        for da in self.users_nb_domain_admins:
            try:
                count_da[da["domain"]] += 1
            except KeyError:
                count_da[da["domain"]] = 1
        self.max_da_per_domain = max(count_da.values())

        for da in self.users_nb_domain_admins:
            da["domain"] = '<i class="bi bi-globe2"></i> ' + da["domain"]
            da["name"] = '<i class="bi bi-gem"></i> ' + da["name"]
            da["enterprise / schema admin"] = '<i class="bi bi-check-square-fill"></i><span style="display:none">True</span>' if "Enterprise Admin" in da["admin type"] else '<i class="bi bi-square"></i>'
            da["domain admin"] = '<i class="bi bi-check-square-fill"></i><span style="display:none">True</span>' if "Domain Admin" in da["admin type"] else '<i class="bi bi-square"></i>'
            da["(Enterprise) key admin"] = '<i class="bi bi-check-square-fill"></i><span style="display:none">True</span>' if "Key Admin" in da["admin type"] else '<i class="bi bi-square"></i>'
            da["builtin administrators"] = '<i class="bi bi-check-square-fill"></i><span style="display:none">True</span>' if "Builtin Administrator" in da["admin type"] else '<i class="bi bi-square"></i>'

        grid = Grid("Domain admins")
        grid.setheaders(["domain", "name", "enterprise / schema admin", "domain admin", "(Enterprise) key admin", "builtin administrators"])
        grid.setData(self.users_nb_domain_admins)
        page.addComponent(grid)
        page.render()

    # Create computer not connected since X page
    def genComputerNotConnectedSincePage(self):
        if self.computers_with_last_connection_date is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "computers_last_connexion",
            "Ghost computers",
            "computers_last_connexion",
        )

        data = []
        for c in self.computers_not_connected_since_60:
            data.append({"name": '<i class="bi bi-pc-display"></i> ' + c["name"], "Last logon": days_format(c["days"])})
        grid = Grid("Computers not connected since")
        grid.setheaders(["name", "Last logon"])
        grid.setData(data)
        page.addComponent(grid)
        page.render()

    # List of dormants accounts
    def genDormantsUsersPage(self):
        if self.users_dormant_accounts is None:
            return

        page = Page(
            self.arguments.cache_prefix,
            "dormants_accounts",
            "Number of dormants accounts",
            "dormants_accounts",
        )
        grid = Grid("Dormants accounts")
        grid.setheaders(["domain", "name", "last logon", "Account Creation Date"])

        data = []
        for dict in self.users_dormant_accounts:
            tmp_data = {"domain": '<i class="bi bi-globe2"></i> ' + dict["domain"]}

            tmp_data["name"] = (
                    '<i class="bi bi-gem" title="This user is domain admin"></i> '
                    + dict["name"]
                ) if dict["name"] in self.admin_list else '<i class="bi bi-person-fill"></i> ' + dict["name"]

            tmp_data["last logon"] = days_format(dict["days"])
            tmp_data["Account Creation Date"] = days_format(dict["accountCreationDate"])

            data.append(tmp_data)

        grid.setData(data)
        page.addComponent(grid)
        page.render()

    # Hey
    # List of users with password not changed > 3 months
    def genUsersPasswordNotChangedPage(self):
        if self.users_pwd_not_changed_since_3months is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "users_pwd_not_changed_since",
            f"Number of users with password not changed for at least {self.arguments.renewal_password} days",
            "users_pwd_not_changed_since",
        )
        grid = Grid("Users with password not changed > 3 months")
        # grid.setheaders(["user", "days"])
        # grid.setData(self.users_pwd_not_changed_since_3months)

        # Human readable display
        grid.setheaders(["user", "Last password change", "Account Creation Date"])
        data = []
        for dict in self.users_pwd_not_changed_since_3months:
            tmp_data = {"user": dict["user"]}
            if dict["user"] in self.admin_list:
                tmp_data["user"] = '<i class="bi bi-gem" title="This user is domain admin"></i> ' + tmp_data["user"]
            else:
                tmp_data["user"] = '<i class="bi bi-person-fill"></i> ' + tmp_data["user"]
            tmp_data["Last password change"] = days_format(dict["days"])
            tmp_data["Account Creation Date"] = days_format(dict["accountCreationDate"])

            data.append(tmp_data)
        grid.setData(data)
        page.addComponent(grid)
        page.render()

    def getUsersUnusedSince(self):
        result = []
        dict_since = {
            "3 months": 90,
            "1 year": 365,
            "5 years": 5 * 365,
            "10 years": 10 * 365,
            "never": 40 * 365,
        }
        result.append(
            [
                "> 3 months",
                len(
                    [
                        user
                        for user in self.users_dormant_accounts
                        if dict_since["1 year"] > user["days"] > dict_since["3 months"]
                    ]
                ),
            ]
        )
        result.append(
            [
                "> 1 year",
                len(
                    [
                        user
                        for user in self.users_dormant_accounts
                        if dict_since["5 years"] > user["days"] > dict_since["1 year"]
                    ]
                ),
            ]
        )
        result.append(
            [
                "> 5 years",
                len(
                    [
                        user
                        for user in self.users_dormant_accounts
                        if dict_since["10 years"] > user["days"] > dict_since["5 years"]
                    ]
                ),
            ]
        )
        result.append(
            [
                "> 10 years",
                len(
                    [
                        user
                        for user in self.users_dormant_accounts
                        if dict_since["never"] > user["days"] > dict_since["10 years"]
                    ]
                ),
            ]
        )
        result.append(
            [
                "Never",
                len(
                    [
                        user
                        for user in self.users_dormant_accounts
                        if user["days"] > dict_since["never"]
                    ]
                ),
            ]
        )
        return result
        """
		list_since = [90, 365, 5*365, 10*365, 40*365]
		for index_time in range(0, len(list_since)-1):
#			print(self.user_dormant_accounts)
			nb_users = len([user for user in self.users_dormant_accounts if list_since[index_time+1]>user['days']>list_since[index_time]])
			time_str = f"> {list_since[index_time]//365} year(s)" if list_since[index_time]>364 else "> %s days" % list_since[index_time]
			result.append([time_str, nb_users])
		nb_users_never = len([user for user in self.users_dormant_accounts if user['days']>list_since[-1]])
		result.append(["Never", nb_users_never])
		return result
		"""

    # Number of DC
    def genNumberOfDCPage(self):
        if self.computers_nb_domain_controllers is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "nb_domain_controllers",
            "List of domain controllers",
            "nb_domain_controllers",
        )
        grid = Grid("List of domain controllers")
        grid.setheaders(["domain", "name", "os"])
        for d in self.computers_nb_domain_controllers:
            d["domain"] = '<i class="bi bi-globe2"></i> ' + d["domain"]
            if d["ghost"]:
                d["name"] = '<svg height="15px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><path d="M40.1 467.1l-11.2 9c-3.2 2.5-7.1 3.9-11.1 3.9C8 480 0 472 0 462.2V192C0 86 86 0 192 0S384 86 384 192V462.2c0 9.8-8 17.8-17.8 17.8c-4 0-7.9-1.4-11.1-3.9l-11.2-9c-13.4-10.7-32.8-9-44.1 3.9L269.3 506c-3.3 3.8-8.2 6-13.3 6s-9.9-2.2-13.3-6l-26.6-30.5c-12.7-14.6-35.4-14.6-48.2 0L141.3 506c-3.3 3.8-8.2 6-13.3 6s-9.9-2.2-13.3-6L84.2 471c-11.3-12.9-30.7-14.6-44.1-3.9zM160 192a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm96 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"/></svg> ' + d['name']
            else:
                d["name"] = '<i class="bi bi-server"></i> ' + d['name']
            if 'Windows' in d['os']:
                d['os'] = '<i class="bi bi-windows"></i> ' + d['os']
            d.pop('ghost', None)
        grid.setData(self.computers_nb_domain_controllers)
        page.addComponent(grid)
        page.render()

    def createGraphPage(
        self, render_prefix, page_name, page_title, page_description, graph_data
    ):
        page = Page(render_prefix, page_name, page_title, page_description)
        graph = Graph()
        graph.setPaths(graph_data)

        graph.addUserDA(self.dico_user_da)
        graph.addGroupDA(self.dico_da_group)
        graph.addDCComputers(self.dico_dc_computer)
        graph.addGhostComputers(self.dico_ghost_computer)
        graph.addGhostUsers(self.dico_ghost_user)

        page.addComponent(graph)
        # print("rendering graphpage")
        page.render()
        # print("finshed rednering graphpage")

    def generatePathToDa(
        self, file_variable="da", file_variable2="admin"
    ):  # file_variable if we want to generate path to something other than domain admin groups
        if file_variable == "da":
            if self.objects_to_domain_admin is None:
                return

            # for p in self.objects_to_domain_admin:
            # 	for r in p.relationships:
            # 		print([a.name for a in  r.nodes])
            # exit(0)
            objects_to_domain = self.objects_to_domain_admin
            users_to_domain = self.users_to_domain_admin
            groups_to_domain = self.groups_to_domain_admin
            computers_to_domain = self.computers_to_domain_admin
            ou_to_domain = self.ou_to_domain_admin
            gpo_to_domain = self.gpo_to_domain_admin
            domains_to_domain = self.domains_to_domain_admin

        logger.print_debug("Split objects into types...")
        for path in self.objects_to_domain_admin:
            if "User" in path.nodes[0].labels:
                self.users_to_domain_admin[path.nodes[-1].domain].append(path)
            elif "Computer" in path.nodes[0].labels:
                self.computers_to_domain_admin[path.nodes[-1].domain].append(
                    path)
            elif "Group" in path.nodes[0].labels:
                self.groups_to_domain_admin[path.nodes[-1].domain].append(path)
            elif "OU" in path.nodes[0].labels:
                self.ou_to_domain_admin[path.nodes[-1].domain].append(path)
            elif "GPO" in path.nodes[0].labels:
                self.gpo_to_domain_admin[path.nodes[-1].domain].append(path)
            elif "Domain" in path.nodes[0].labels:
                self.domains_to_domain_admin.append(path)
        logger.print_debug("[Done]")
        for domain in self.domains:
            domain = domain[0]
            if len(users_to_domain[domain]):
                logger.print_debug("... from users")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + f"_users_to_{file_variable}",
                    f"Paths to domain {file_variable2}",
                    f"paths_to_domain_{file_variable2}",
                    users_to_domain[domain],
                )
            if len(computers_to_domain[domain]):
                logger.print_debug("... from computers")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + f"_computers_to_{file_variable}",
                    f"Paths to domain {file_variable2}",
                    f"paths_to_domain_{file_variable2}",
                    computers_to_domain[domain],
                )
            if len(groups_to_domain[domain]):
                logger.print_debug("... from groups")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + f"_groups_to_{file_variable}",
                    f"Paths to domain {file_variable2}",
                    f"paths_to_domain_{file_variable2}",
                    groups_to_domain[domain],
                )
            if len(ou_to_domain[domain]):
                logger.print_debug("... from OUs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + f"_OU_to_{file_variable}",
                    f"Paths to domain {file_variable2}",
                    f"paths_to_domain_{file_variable2}",
                    ou_to_domain[domain],
                )
            if len(gpo_to_domain[domain]):
                logger.print_debug("... from GPOs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + f"_GPO_to_{file_variable}",
                    f"Paths to domain {file_variable2}",
                    f"paths_to_domain_{file_variable2}",
                    gpo_to_domain[domain],
                )

        if len(domains_to_domain):
            self.createGraphPage(
                self.arguments.cache_prefix,
                f"domains_to_{file_variable}",
                f"Paths to domain {file_variable2}",
                f"paths_to_domain_{file_variable2}",
                self.domains_to_domain_admin,
            )

        def count_object_from_path(list_of_paths):
            """
            Count the numbers of object leading to DA instead of counting number of path.
            """
            entries = []
            for path in list_of_paths:
                start = path.nodes[0].name
                if start not in entries:
                    entries.append(start)
            return len(entries)

        # generating graph object to da grid
        page = Page(
            self.arguments.cache_prefix,
            f"graph_path_objects_to_{file_variable}",
            "All compromission paths to Domain Admin",
            f"graph_path_objects_to_{file_variable}",
        )
        grid = Grid("Numbers of path to domain admin per domain and objects")
        grid_data = []
        headers = [
            "Domain",
            "Users (Paths)",
            "Computers (Paths)",
            "Groups (Paths)",
            "OU (Paths)",
            "GPO (Paths)",
        ]
        self.total_object = 0

        for domain in self.collected_domains:
            domain = domain[0]
            tmp_data = {}

            tmp_data[headers[0]] = '<i class="bi bi-globe2"></i> ' + domain

            count = count_object_from_path(users_to_domain[domain])
            sortClass = str(count).zfill(6)  # used to make the sorting feature work with icons
            if count != 0:
                tmp_data[headers[1]] = grid_data_stringify({
                    "value": f"{count} (<i class='bi bi-shuffle' aria-hidden='true'></i> {len(self.users_to_domain_admin[domain])})",
                    "link": "%s_users_to_da.html" % quote(str(domain)),
                    "before_link": f"<i class='bi bi-person-fill {sortClass}' aria-hidden='true'></i> "
                })
            else:
                tmp_data[headers[1]] = (
                    "<i class='bi bi-person-fill %s' aria-hidden='true'></i> %s (<i class='bi bi-shuffle' aria-hidden='true'></i> %s)"
                    % (sortClass, count, len(self.users_to_domain_admin[domain]))
                )
            self.total_object += count

            count = count_object_from_path(computers_to_domain[domain])
            sortClass = str(count).zfill(6)  # used to make the sorting feature work with icons
            if count != 0:
                tmp_data[headers[2]] = grid_data_stringify({
                    "value": f"{count} (<i class='bi bi-shuffle' aria-hidden='true'></i> {len(self.computers_to_domain_admin[domain])})",
                    "link": "%s_computers_to_da.html" % quote(str(domain)),
                    "before_link": f"<i class='bi bi-pc-display-horizontal {sortClass}' aria-hidden='true'></i>"
                })
            else:
                tmp_data[headers[2]] = (
                    "<i class='bi bi-pc-display-horizontal %s' aria-hidden='true'></i> %s (<i class='bi bi-shuffle' aria-hidden='true'></i> %s)"
                    % (sortClass, count, len(self.computers_to_domain_admin[domain]))
                )
            self.total_object += count

            count = count_object_from_path(groups_to_domain[domain])
            sortClass = str(count).zfill(6)  # used to make the sorting feature work with icons
            if count != 0:
                tmp_data[headers[3]] = grid_data_stringify({
                    "value": f"{count} (<i class='bi bi-shuffle' aria-hidden='true'></i> {len(self.groups_to_domain_admin[domain])})",
                    "link": "%s_groups_to_da.html" % quote(str(domain)),
                    "before_link": f"<i class='bi bi-people-fill {sortClass}' aria-hidden='true'></i>"
                })
            else:
                tmp_data[headers[3]] = (
                    "<i class='bi bi-people-fill %s' aria-hidden='true'></i> %s (<i class='bi bi-shuffle' aria-hidden='true'></i> %s)"
                    % (sortClass, count, len(self.groups_to_domain_admin[domain]))
                )
            self.total_object += count

            count = count_object_from_path(ou_to_domain[domain])
            sortClass = str(count).zfill(6)  # used to make the sorting feature work with icons
            if count != 0:
                tmp_data[headers[4]] = grid_data_stringify({
                    "value": f"{count} (<i class='bi bi-shuffle' aria-hidden='true'></i> {len(self.ou_to_domain_admin[domain])})",
                    "link": "%s_OU_to_da.html" % quote(str(domain)),
                    "before_link": f"<i class='bi bi-building {sortClass}' aria-hidden='true'></i>"
                })
            else:
                tmp_data[headers[4]] = (
                    "<i class='bi bi-building %s' aria-hidden='true'></i> %s (<i class='bi bi-shuffle' aria-hidden='true'></i> %s)"
                    % (sortClass, count, len(self.ou_to_domain_admin[domain]))
                )
            self.total_object += count

            count = count_object_from_path(gpo_to_domain[domain])
            sortClass = str(count).zfill(6)  # used to make the sorting feature work with icons
            if count != 0:
                tmp_data[headers[5]] = grid_data_stringify({
                    "value": f"{count} (<i class='bi bi-shuffle' aria-hidden='true'></i> {len(self.gpo_to_domain_admin[domain])})",
                    "link": "%s_GPO_to_da.html" % quote(str(domain)),
                    "before_link": f"<i class='bi bi-journal-text {sortClass}' aria-hidden='true'></i>"
                })
            else:
                tmp_data[headers[5]] = (
                    "<i class='bi bi-journal-text %s' aria-hidden='true'></i> %s (<i class='bi bi-shuffle' aria-hidden='true'></i> %s)"
                    % (sortClass, count, len(self.gpo_to_domain_admin[domain]))
                )
            self.total_object += count

            grid_data.append(tmp_data)
        grid.setheaders(headers)
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    def generatePathToDcsync(self):
        if self.objects_to_dcsync is None:
            return
        logger.print_debug("Generate paths to DCSyncs")
        for path in self.objects_to_dcsync:
            if "User" in path.nodes[0].labels:
                self.users_to_dcsync[path.nodes[-1].domain].append(path)
            elif "Computer" in path.nodes[0].labels:
                self.computers_to_dcsync[path.nodes[-1].domain].append(path)
            elif "Group" in path.nodes[0].labels:
                self.groups_to_dcsync[path.nodes[-1].domain].append(path)
            elif "OU" in path.nodes[0].labels:
                self.ou_to_dcsync[path.nodes[-1].domain].append(path)
            elif "GPO" in path.nodes[0].labels:
                self.gpo_to_dcsync[path.nodes[-1].domain].append(path)

        for domain in self.domains:
            domain = domain[0]
            logger.print_debug("Generate paths to DCSync")
            if len(self.users_to_dcsync[domain]):
                logger.print_debug("... from users")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_users_to_dcsync",
                    "Paths to DC sync",
                    "paths_to_dcsync",
                    self.users_to_dcsync[domain],
                )
            if len(self.computers_to_dcsync[domain]):
                logger.print_debug("... from Computers")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_computers_to_dcsync",
                    "Paths to DC sync",
                    "paths_to_dcsync",
                    self.computers_to_dcsync[domain],
                )
            if len(self.groups_to_dcsync[domain]):
                logger.print_debug("... from Groups")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_groups_to_dcsync",
                    "Paths to DC sync",
                    "paths_to_dcsync",
                    self.groups_to_dcsync[domain],
                )
            if len(self.ou_to_dcsync[domain]):
                logger.print_debug("... from OUs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_OU_to_dcsync",
                    "Paths to DC sync",
                    "paths_to_dcsync",
                    self.ou_to_dcsync[domain],
                )
            if len(self.gpo_to_dcsync[domain]):
                logger.print_debug("... from GPOs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_GPO_to_dcsync",
                    "Paths to DC sync",
                    "paths_to_dcsync",
                    self.gpo_to_dcsync[domain],
                )

        # generating graph object to dcsync grid
        page = Page(
            self.arguments.cache_prefix,
            "graph_path_objects_to_dcsync",
            "Path to DCSync",
            "graph_path_objects_to_dcsync",
        )
        grid = Grid("Numbers of path to domain admin per domain and objects")
        grid_data = []
        for domain in self.domains:
            domain = domain[0]
            # print('domain')
            tmp_data = {}
            tmp_data["Domain"] = domain
            if len(self.users_to_dcsync[domain]) != 0:
                tmp_data["Users"] = {
                    "value": "<i class='bi bi-person-fill %s' aria-hidden='true'></i> %s"
                    % (
                        str(len(self.users_to_dcsync[domain])).zfill(6),
                        len(self.users_to_dcsync[domain]),
                    ),
                    "link": "%s_users_to_dcsync.html" % quote(str(domain)),
                }
            else:
                tmp_data[
                    "Users"
                ] = "<i class='bi bi-person-fill %s' aria-hidden='true'></i> %s" % (
                    str(len(self.users_to_dcsync[domain])).zfill(6),
                    len(self.users_to_dcsync[domain]),
                )
            if len(self.computers_to_dcsync[domain]) != 0:
                tmp_data["Computers"] = {
                    "value": "<i class='bi bi-pc-display-horizontal %s' aria-hidden='true'></i> %s"
                    % (
                        str(len(self.computers_to_dcsync[domain])).zfill(6),
                        len(self.computers_to_dcsync[domain]),
                    ),
                    "link": "%s_computers_to_dcsync.html" % quote(str(domain)),
                }
            else:
                tmp_data["Computers"] = (
                    "<i class='bi bi-pc-display-horizontal %s' aria-hidden='true'></i> %s"
                    % (
                        str(len(self.computers_to_dcsync[domain])).zfill(6),
                        len(self.computers_to_dcsync[domain]),
                    )
                )
            if len(self.groups_to_dcsync[domain]) != 0:
                tmp_data["Groups"] = {
                    "value": "<i class='bi bi-people-fill %s' aria-hidden='true'></i> %s"
                    % (
                        str(len(self.groups_to_dcsync[domain])).zfill(6),
                        len(self.groups_to_dcsync[domain]),
                    ),
                    "link": "%s_groups_to_dcsync.html" % quote(str(domain)),
                }
            else:
                tmp_data[
                    "Groups"
                ] = "<i class='bi bi-people-fill %s' aria-hidden='true'></i> %s" % (
                    str(len(self.groups_to_dcsync[domain])).zfill(6),
                    len(self.groups_to_dcsync[domain]),
                )
            if len(self.ou_to_dcsync[domain]) != 0:
                tmp_data["Ou"] = {
                    "value": "<i class='bi bi-building %s' aria-hidden='true'></i> %s"
                    % (
                        str(len(self.ou_to_dcsync[domain])).zfill(6),
                        len(self.ou_to_dcsync[domain]),
                    ),
                    "link": "%s_OU_to_dcsync.html" % quote(str(domain)),
                }
            else:
                tmp_data[
                    "Ou"
                ] = "<i class='bi bi-building %s' aria-hidden='true'></i> %s" % (
                    str(len(self.ou_to_dcsync[domain])).zfill(6),
                    len(self.ou_to_dcsync[domain]),
                )
            if len(self.gpo_to_dcsync[domain]) != 0:
                tmp_data["GPO"] = {
                    "value": "<i class='bi bi-journal-text %s' aria-hidden='true'></i> %s"
                    % (
                        str(len(self.gpo_to_dcsync[domain])).zfill(6),
                        len(self.gpo_to_dcsync[domain]),
                    ),
                    "link": "%s_GPO_to_dcsync.html" % quote(str(domain)),
                }
            else:
                tmp_data[
                    "GPO"
                ] = "<i class='bi bi-journal-text %s' aria-hidden='true'></i> %s" % (
                    str(len(self.gpo_to_dcsync[domain])).zfill(6),
                    len(self.gpo_to_dcsync[domain]),
                )
            grid_data.append(tmp_data)
        headers = ["Domain", "Users", "Computers", "Groups", "Ou", "GPO"]
        # print('headers')
        grid.setheaders(headers)
        # print('grid data')
        grid.setData(grid_data)
        # print('grid')
        page.addComponent(grid)
        # print('render')
        page.render()
        # print("finished render")

    def generateDomainMapTrust(self):
        if self.domain_map_trust is None:
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "domain_map_trust",
            "Map trust of domains ",
            "domain_map_trust",
            self.domain_map_trust,
        )

    def generatePathToUnconstrainedDelegation(self):
        if self.objects_to_unconstrained_delegation is None:
            return
        logger.print_debug("Generate paths to unconstrained delegations")
        for path in self.objects_to_unconstrained_delegation:

            if "User" in path.nodes[0].labels:
                self.users_to_unconstrained_delegation[path.nodes[-1].domain].append(
                    path
                )
            elif "Computer" in path.nodes[0].labels:
                self.computers_to_unconstrained_delegation[path.nodes[-1].domain].append(
                    path
                )
            elif "Group" in path.nodes[0].labels:
                self.groups_to_unconstrained_delegation[path.nodes[-1].domain].append(
                    path
                )
            elif "OU" in path.nodes[0].labels:
                self.ou_to_unconstrained_delegation[path.nodes[-1].domain].append(
                    path)
            elif "GPO" in path.nodes[0].labels:
                self.gpo_to_unconstrained_delegation[path.nodes[-1].domain].append(
                    path)

        for domain in self.domains:
            domain = domain[0]
            logger.print_debug("Doing domain " + domain)
            if len(self.users_to_unconstrained_delegation[domain]):
                logger.print_debug("... from users")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_users_to_unconstrained_delegation",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.users_to_unconstrained_delegation[domain],
                )
            if len(self.computers_to_unconstrained_delegation[domain]):
                logger.print_debug("... from Computers")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_computers_to_unconstrained_delegation",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.computers_to_unconstrained_delegation[domain],
                )
            if len(self.groups_to_unconstrained_delegation[domain]):
                logger.print_debug("... from Groups")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_groups_to_unconstrained_delegation",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.groups_to_unconstrained_delegation[domain],
                )
            if len(self.ou_to_unconstrained_delegation[domain]):
                logger.print_debug("... from OUs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_OU_to_unconstrained_delegation",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.ou_to_unconstrained_delegation[domain],
                )
            if len(self.gpo_to_unconstrained_delegation[domain]):
                logger.print_debug("... from GPOs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_GPO_to_unconstrained_delegation",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.gpo_to_unconstrained_delegation[domain],
                )

        # generating graph object to unconstrained delegation grid
        page = Page(
            self.arguments.cache_prefix,
            "graph_path_objects_to_unconstrained_delegation",
            "Path to unconstrained delegation",
            "graph_path_objects_to_unconstrained_delegation",
        )
        grid = Grid("Numbers of path to domain admin per domain and objects")
        grid_data = []
        for domain in self.domains:
            domain = domain[0]
            tmp_data = {}
            tmp_data["Domain"] = domain
            tmp_data["Users"] = {
                "value": len(self.users_to_unconstrained_delegation[domain]),
                "link": "%s_users_to_unconstrained_delegation.html" % quote(str(domain)),
            }
            tmp_data["Computers"] = {
                "value": len(self.computers_to_unconstrained_delegation[domain]),
                "link": "%s_computers_to_unconstrained_delegation.html" % quote(str(domain)),
            }
            tmp_data["Groups"] = {
                "value": len(self.groups_to_unconstrained_delegation[domain]),
                "link": "%s_groups_to_unconstrained_delegation.html" % quote(str(domain)),
            }
            tmp_data["Ou"] = {
                "value": len(self.ou_to_unconstrained_delegation[domain]),
                "link": "%s_OU_to_unconstrained_delegation.html" % quote(str(domain)),
            }
            tmp_data["GPO"] = {
                "value": len(self.gpo_to_unconstrained_delegation[domain]),
                "link": "%s_GPO_to_unconstrained_delegation.html" % quote(str(domain)),
            }
            grid_data.append(tmp_data)
        headers = ["Domain", "Users", "Computers", "Groups", "Ou", "GPO"]
        grid.setheaders(headers)
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    def generatePathToUnconstrainedDelegation_2(self):
        if self.objects_to_unconstrained_delegation_2 is None:
            return
        logger.print_debug("Generating path to unconstrained 2nd phase ????")
        for path in self.objects_to_unconstrained_delegation_2:

            if "User" in path.nodes[0].labels:
                self.users_to_unconstrained_delegation_2[path.nodes[-1].domain].append(
                    path
                )
            elif "Computer" in path.nodes[0].labels:
                self.computers_to_unconstrained_delegation_2[
                    path.nodes[-1].domain
                ].append(path)
            elif "Group" in path.nodes[0].labels:
                self.groups_to_unconstrained_delegation_2[path.nodes[-1].domain].append(
                    path
                )
            elif "OU" in path.nodes[0].labels:
                self.ou_to_unconstrained_delegation_2[path.nodes[-1].domain].append(
                    path)
            elif "GPO" in path.nodes[0].labels:
                self.gpo_to_unconstrained_delegation_2[path.nodes[-1].domain].append(
                    path
                )

        for domain in self.domains:
            domain = domain[0]
            if len(self.users_to_unconstrained_delegation_2[domain]):
                logger.print_debug("... from users")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_users_to_unconstrained_delegation_users",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.users_to_unconstrained_delegation_2[domain],
                )
            if len(self.computers_to_unconstrained_delegation_2[domain]):
                logger.print_debug("... from Computers")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_computers_to_unconstrained_delegation_users",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.computers_to_unconstrained_delegation_2[domain],
                )
            if len(self.groups_to_unconstrained_delegation_2[domain]):
                logger.print_debug("... from Groups")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_groups_to_unconstrained_delegation_users",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.groups_to_unconstrained_delegation_2[domain],
                )
            if len(self.ou_to_unconstrained_delegation_2[domain]):
                logger.print_debug("... from OUs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_OU_to_unconstrained_delegation_users",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.ou_to_unconstrained_delegation_2[domain],
                )
            if len(self.gpo_to_unconstrained_delegation_2[domain]):
                logger.print_debug("... from GPOs")
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    domain + "_GPO_to_unconstrained_delegation_users",
                    "Paths to unconstrained delegations",
                    "graph_path_objects_to_unconstrained_delegation_users",
                    self.gpo_to_unconstrained_delegation_2[domain],
                )

        # generating graph object to unconstrained delegation grid
        page = Page(
            self.arguments.cache_prefix,
            "graph_path_objects_to_unconstrained_delegation_users",
            "Path to unconstrained delegation",
            "graph_path_objects_to_unconstrained_delegation_users",
        )
        grid = Grid("Numbers of path to domain admin per domain and objects")
        grid_data = []
        for domain in self.domains:
            domain = domain[0]
            tmp_data = {}
            tmp_data["Domain"] = domain
            tmp_data["Users"] = {
                "value": len(self.users_to_unconstrained_delegation_2[domain]),
                "link": "%s_users_to_unconstrained_delegation_users.html" % quote(str(domain)),
            }
            tmp_data["Computers"] = {
                "value": len(self.computers_to_unconstrained_delegation_2[domain]),
                "link": "%s_computers_to_unconstrained_delegation_users.html" % quote(str(domain)),
            }
            tmp_data["Groups"] = {
                "value": len(self.groups_to_unconstrained_delegation_2[domain]),
                "link": "%s_groups_to_unconstrained_delegation_users.html" % quote(str(domain)),
            }
            tmp_data["Ou"] = {
                "value": len(self.ou_to_unconstrained_delegation_2[domain]),
                "link": "%s_OU_to_unconstrained_delegation_users.html" % quote(str(domain)),
            }
            tmp_data["GPO"] = {
                "value": len(self.gpo_to_unconstrained_delegation_2[domain]),
                "link": "%s_GPO_to_unconstrained_delegation_users.html" % quote(str(domain)),
            }
            grid_data.append(tmp_data)
        headers = ["Domain", "Users", "Computers", "Groups", "Ou", "GPO"]
        grid.setheaders(headers)
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    def getUserComputersCountPerDomain(self):
        if self.domains is None:
            logger.print_error(" self.domains is None")
            return ["Domain is None", 0, 0]
        result = []
        users = self.neo4j.all_requests["nb_enabled_accounts"]["result"]
        computers = self.neo4j.all_requests["nb_computers"]["result"]

        for domain in self.domains:
            domain = domain[0]
            nb_user = len(
                [element for element in users if element["domain"] == domain])
            nb_computer = len(
                [element for element in computers if element["domain"] == domain]
            )
            result.append([domain, nb_user, nb_computer])
        return result

    def findAndCreatePathToDaFromComputersList(self, admin_computer, computers) -> tuple([int, int]):
        """
        Returns the number of path to DA from admin_computer and the number of domains impacted
        """
        if self.computers_to_domain_admin is None:
            logger.print_error(" self.computers_to_domain_admin is None")
            return 0,0
        path_to_generate = []

        domains = []

        for paths in self.computers_to_domain_admin.values():
            for path in paths:

                domains.append(path.nodes[-1].domain)

                if path.nodes[0].name in computers:
                    # relation = Relation(
                    #     id=88888, nodes=[node_to_add, path.nodes[0]], type="Relay"
                    # )
                    node_to_add = Node(
                        id=42424243, labels="Computer", name=admin_computer, domain="start", relation_type="Relay"
                    )
                    path.nodes.insert(0, node_to_add)
                    path_to_generate.append(path)
        if len(path_to_generate):
            self.createGraphPage(
                self.arguments.cache_prefix,
                "computers_path_to_da_from_%s" % admin_computer,
                "Path to domain admins",
                "computers_path_to_da",
                path_to_generate,
            )
        return len(path_to_generate), len(list(set(domains)))

    def findAndCreatePathToDaFromUsersList(self, admin_user, computers):
        if self.users_to_domain_admin is None:
            return 0, 0
        path_to_generate = []
        # node_to_add = Node(id=42424243, labels="User",
        #                    name=admin_user, domain="start")
        list_domain = []
        for paths in self.computers_to_domain_admin.values():
            for path in paths:
                if path.nodes[0].name in computers:
                #if path.start_node.name in computers:
                    node_to_add = Node(
                        id=42424243, labels="User", name=admin_user, domain="start", relation_type="AdminTo"
                    )
                    # relation = Relation(
                    #     id=88888, nodes=[node_to_add, path.start_node], type="AdminTo"
                    # )
                    path.nodes.insert(0, node_to_add)
                    path_to_generate.append(path)
                    if path.nodes[-1].domain not in list_domain:
                        list_domain.append(path.nodes[-1].domain)
        if len(path_to_generate):
            self.createGraphPage(
                self.arguments.cache_prefix,
                "users_path_to_da_from_%s" % admin_user,
                "Path to domain admins",
                "computers_path_to_da",
                path_to_generate,
            )
        return (len(path_to_generate), len(list_domain))

    def get_unpriv_users_to_GPO(self):
        if self.arguments.gpo_low and self.unpriv_users_to_GPO is None:
            return
        if not self.arguments.gpo_low:
            fail = []
            if self.unpriv_users_to_GPO_init is None:
                fail.append("unpriv_users_to_GPO_init")
            elif self.unpriv_users_to_GPO_user_enforced is None:
                fail.append("unpriv_users_to_GPO_user_enforced")
            elif self.unpriv_users_to_GPO_user_not_enforced is None:
                fail.append("unpriv_users_to_GPO_user_not_enforced")
            elif self.unpriv_users_to_GPO_computer_enforced is None:
                fail.append("unpriv_users_to_GPO_computer_enforced")
            elif self.unpriv_users_to_GPO_computer_not_enforced is None:
                fail.append("unpriv_users_to_GPO_computer_not_enforced")

            if 0 < len(fail) < 5:  # if only some of them are disabled
                logger.print_error(
                    f" In order to use 'normal GPO mode', please activate the following in config.json : {', '.join(fail)}"
                )

            if len(fail) > 0:
                return

        def parseGPOData(listOfPaths, headers):
            """
            Initial parsing of data from neo4j requests for GPO
            """
            dictOfGPO = {}
            for path in listOfPaths:
                start = path.nodes[0]
                end = path.nodes[-1]
                if "GPO" in start.labels:
                    nameOfGPO = start.name
                    idOfGPO = start.id
                    sens = "right"
                elif "GPO" in end.labels:
                    nameOfGPO = end.name
                    idOfGPO = end.id
                    sens = "left"
                else:
                    continue
                try:
                    if sens == "right":
                        dictOfGPO[nameOfGPO][headers[4]] += 1
                        dictOfGPO[nameOfGPO]["right_path"].append(path)
                        dictOfGPO[nameOfGPO]["end_list"].append(end.name)
                    elif sens == "left":
                        dictOfGPO[nameOfGPO][headers[1]] += 1
                        dictOfGPO[nameOfGPO]["left_path"].append(path)
                        dictOfGPO[nameOfGPO]["entry_list"].append(start.name)
                    else:
                        continue
                except KeyError:
                    if sens == "right":
                        dictOfGPO[nameOfGPO] = {
                            headers[0]: nameOfGPO,
                            headers[1]: 0,
                            headers[4]: 1,
                            "left_path": [],
                            "right_path": [path],
                            "id": idOfGPO,
                            "entry_list": [],
                            "end_list": [end.name],
                        }
                    elif sens == "left":
                        dictOfGPO[nameOfGPO] = {
                            headers[0]: nameOfGPO,
                            headers[1]: 1,
                            headers[4]: 0,
                            "left_path": [path],
                            "right_path": [],
                            "id": idOfGPO,
                            "entry_list": [start.name],
                            "end_list": [],
                        }
                    else:
                        continue
            return dictOfGPO

        def formatGPOGrid(dictOfGPO, headers):
            output = []
            for _, dict in dictOfGPO.items():
                # Get number of domains
                domains = []
                for path in dict["right_path"]:
                    #for relation in path.relationships:
                    for i in range(len(path.nodes)):
                        if path.nodes[i].labels == "Domain":
                            domains.append(path.nodes[i].name)
                # 				if dict[headers[4]] > 0:
                self.number_of_gpo += 1

                nbDomains = len(list(set(domains)))
                sortClass = str(nbDomains).zfill(6)
                icon = (
                    '<svg class="%s" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1008 1024" style="width:25px";><path d="M477.177 855.5c-53.61-2.647-114.503-13.494-162.25-28.904l-12.093-3.903 11.589-2.755c39.97-9.503 85.839-16.49 131.01-19.956 24.873-1.909 90.361-1.613 115.893.523 27.799 2.326 57.168 5.986 82.23 10.247 23.064 3.921 58.937 11.383 60.137 12.509.427.4-5.922 2.855-14.109 5.455-66.413 21.092-139.925 30.362-212.407 26.784zm-208.104-75.808c0-20.764.152-22.771 1.764-23.266 19.345-5.942 55.283-14.613 79.414-19.16 80.071-15.088 168.65-17.737 252.896-7.563 36.86 4.451 82.447 13.218 120.176 23.111l16.376 4.294v22.537c0 13.633-.38 22.537-.962 22.537-.529 0-10.166-2.284-21.415-5.076-50.372-12.5-98.281-20.276-152.974-24.828-25.99-2.163-97.243-2.464-121.436-.513-55.427 4.47-101.73 11.938-148.142 23.893-11.64 2.998-22.183 5.745-23.431 6.105l-2.267.654zm0-81.045v-29.175l13.353-3.655c55.753-15.261 103.839-23.547 163.006-28.088 21.019-1.613 88.971-1.597 109.846.027 61.272 4.765 117.088 14.018 169.808 28.152l14.109 3.782.267 28.958c.147 15.927.078 28.958-.154 28.958s-9.596-2.294-20.808-5.097c-49.769-12.444-101.749-20.848-156.672-25.331-21.773-1.777-101.382-1.766-122.947.017-51.904 4.292-96.105 11.5-142.914 23.303-12.852 3.241-24.161 6.214-25.13 6.608-1.655.672-1.764-1.073-1.764-28.46zm464.076-59.894c-56.218-15.378-125.089-26.108-187.444-29.203-13.303-.66-24.282-1.257-24.399-1.327-.535-.318 8.091-36.072 11.798-48.899 13.277-45.954 33.728-88.885 57.246-120.175 25.869-34.418 58.363-60.432 89.428-71.593 10.915-3.922 28.85-7.582 43.059-8.788 35.38-3.002 72.831 6.529 100.423 25.558 25.515 17.596 31.39 50.279 16.837 93.67-7.738 23.074-22.629 53.628-41.103 84.34-8.764 14.571-39.872 62.986-49.261 76.667l-2.476 3.608zM247.35 625.59c-27.073-36.143-46.369-66.745-60.371-95.745-13.53-28.021-20.849-50.067-25.294-76.179-2.821-16.576-3.068-26.178-.909-35.34 6.174-26.19 35.844-49.829 70.191-55.921 13.228-2.346 37.419-3.987 47.907-3.25 34.167 2.402 67.912 16.521 98.533 41.228 11.349 9.157 29.856 28.537 39.171 41.017 29.069 38.95 55.724 101.939 69.551 164.358l.579 2.612-20.89.658c-44.784 1.41-98.475 7.955-141.822 17.288-12.384 2.666-50.707 12.405-59.092 15.017l-4.672 1.455zm245.774-115.325c-19.161-38.24-30.164-71.107-38.741-115.725-7.802-40.588-2.473-75.701 14.355-94.581 8.899-9.985 21.478-14.468 37.958-13.528 6.759.385 9.976 1.101 13.909 3.094 13.13 6.653 23.272 23.335 26.794 44.069 1.986 11.689 1.669 54.908-.517 70.52-3.877 27.69-10.832 54.591-20.382 78.831-5.682 14.423-19.608 43.444-22.056 45.963-1.076 1.107-3.066-2.17-11.32-18.644zm-21.49 464.563c-30.312-2.251-65.173-9.427-99.29-20.438-35.041-11.31-53.622-18.505-73.361-28.406C157.301 854.915 60.799 701.642 49.405 529.581c-5.867-88.606 15.612-180.612 58.7-251.437 10.422-17.13 38.329-58.173 46.597-68.528 34.91-43.724 76.788-78.503 127.253-105.681 78.12-42.072 171.469-60.997 263.751-53.47 90.355 7.37 175.104 40.137 241.864 93.513 14.51 11.601 38.686 34.958 51.18 49.448 11.63 13.486 34.003 43.345 44.601 59.524 39.171 59.798 65.304 131.971 73.527 203.065 3.887 33.607 4.369 85.162 1.064 113.877-13.304 115.605-74.695 222.976-172.388 301.5-72.61 58.362-159.043 94.146-247.82 102.599-14.38 1.369-52.445 1.852-66.099.838zm85.66-91.052c67.122-5.18 131.259-20.249 190.368-44.725 7.428-3.076 14.406-6.394 15.508-7.374 4.804-4.275 4.747-3.228 4.747-88.344v-80.077l18.999-29.046c41.342-63.205 59.138-94.391 72.73-127.456 11.023-26.817 15.059-43.376 15.807-64.853.612-17.566-.444-26.018-4.944-39.589-6.056-18.263-16.853-32.204-33.585-43.364-58.996-39.35-144.595-39.047-204.085.722-19.28 12.889-38.028 29.508-52.345 46.401l-6.355 7.499.646-4.475c2.731-18.93 3.384-47.839 1.562-69.159-2.452-28.688-11.216-49.319-27.37-64.431-7.583-7.093-13.599-10.692-23.428-14.014l-7.054-2.384-.54-47.476h61.51v-28.217h-61.474v-49.38h-28.217v49.38h-60.466v28.217h60.466v47.896l-8.975 2.144c-17.712 4.231-29.651 12.594-39.794 27.877-18.155 27.353-23.774 70.795-14.297 110.535 2.678 11.228 2.336 11.276-7.226 1.018-40.961-43.944-96.357-70.461-147.386-70.55-21.091-.037-49.396 3.723-64.243 8.533-47.021 15.235-76.818 51.595-76.831 93.752-.003 10.092 3.538 32.824 7.515 48.241 13.407 51.969 37.989 97.82 88.363 164.817l13.954 18.559v80.587c0 94.101-1.195 84.997 11.874 90.474 67.849 28.437 148.271 45.742 230.998 49.705 12.443.596 58.977-.316 73.567-1.442z"/></svg>'
                    % sortClass
                )

                output.append(
                    {
                        headers[0]: dict[headers[0]],
                        headers[1]: dict[headers[1]],
                        headers[2]: {
                            "link": "users_GPO_access-%s-left-graph.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-diagram-3-fill' aria-hidden='true'></i>",
                        },
                        headers[3]: {
                            "link": "users_GPO_access-%s-left-grid.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-list-columns-reverse' aria-hidden='true'></i>",
                        },
                        headers[4]: len(list(set(dict["end_list"]))),
                        headers[5]: "%s %d" % (icon, nbDomains),
                        headers[6]: {
                            "link": "users_GPO_access-%s-right-graph.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-diagram-3-fill' aria-hidden='true'></i>",
                        },
                        headers[7]: {
                            "link": "users_GPO_access-%s-right-grid.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-list-columns-reverse' aria-hidden='true'></i>",
                        },
                    }
                )
            return output

        def formatSmallGrid(list, gpo_name):
            output = []
            for n in list:
                output.append({gpo_name: n})
            return output

        headers = [
            "GPO name",
            "Paths to GPO",
            "Inbound graph",
            "Inbound list",
            "Objects impacted",
            "Domains impacted",
            "Outbound graph",
            "Outbound list",
        ]
        if not self.arguments.gpo_low:
            data = (
                self.unpriv_users_to_GPO_init
                + self.unpriv_users_to_GPO_user_enforced
                + self.unpriv_users_to_GPO_computer_enforced
                + self.unpriv_users_to_GPO_user_not_enforced
                + self.unpriv_users_to_GPO_computer_not_enforced
            )
            self.unpriv_users_to_GPO_parsed = parseGPOData(data, headers)
            grid = Grid("Users with GPO access")
        else:
            self.unpriv_users_to_GPO_parsed = parseGPOData(
                self.unpriv_users_to_GPO, headers
            )
            grid = Grid("Users with GPO access")

        formated_data = sorted(
            formatGPOGrid(self.unpriv_users_to_GPO_parsed, headers),
            key=lambda x: x[headers[1]],
            reverse=True,
        )
        page = Page(
            self.arguments.cache_prefix,
            "users_GPO_access",
            "Exploitation through GPO",
            "users_GPO_access",
        )

        grid.setheaders(headers)
        grid.setData(json.dumps(formated_data))
        page.addComponent(grid)
        page.render()

        for _, GPO in self.unpriv_users_to_GPO_parsed.items():
            url_left_graph = "users_GPO_access-%s-left-graph" % GPO[headers[0]]
            url_right_graph = "users_GPO_access-%s-right-graph" % GPO[headers[0]]
            page_left_graph = Page(
                self.arguments.cache_prefix,
                url_left_graph,
                "Users with write access on GPO",
                "graph_GPO_access",
            )
            page_right_graph = Page(
                self.arguments.cache_prefix,
                url_right_graph,
                "Objects impacted by GPO",
                "graph_GPO_access",
            )

            url_left_grid = "users_GPO_access-%s-left-grid" % GPO[headers[0]]
            url_right_grid = "users_GPO_access-%s-right-grid" % GPO[headers[0]]
            page_left_grid = Page(
                self.arguments.cache_prefix,
                url_left_grid,
                "List of users able to compromise %s" % GPO[headers[0]],
                "grid_GPO_access",
            )
            page_right_grid = Page(
                self.arguments.cache_prefix,
                url_right_grid,
                "List of users impacted by %s" % GPO[headers[0]],
                "grid_GPO_access",
            )

            # if GPO[headers[4]] > 0:
            graph_left = Graph()
            graph_left.setPaths(GPO["left_path"])
            page_left_graph.addComponent(graph_left)

            graph_right = Graph()
            graph_right.setPaths(GPO["right_path"])
            page_right_graph.addComponent(graph_right)

            if not self.arguments.gpo_low:
                entry_grid = Grid("List of users able to compromise %s" % GPO[headers[0]])
            else:
                entry_grid = Grid("List of users able to compromise %s" % GPO[headers[0]])
            entry_grid.setheaders([GPO[headers[0]]])
            entry_grid.setData(
                json.dumps(
                    formatSmallGrid(
                        list(set(GPO["entry_list"])), GPO[headers[0]])
                )
            )
            page_left_grid.addComponent(entry_grid)

            if not self.arguments.gpo_low:
                end_grid = Grid("List of users impacted by %s" % GPO[headers[0]])
            else:
                end_grid = Grid("List of users impacted by %s" % GPO[headers[0]])
            end_grid.setheaders([GPO[headers[0]]])
            end_grid.setData(
                json.dumps(formatSmallGrid(
                    list(set(GPO["end_list"])), GPO[headers[0]]))
            )
            page_right_grid.addComponent(end_grid)

            page_left_graph.render()
            page_right_graph.render()
            page_left_grid.render()
            page_right_grid.render()

    @staticmethod
    def generatePathToOUHandlers(self):
        if self.objects_to_ou_handlers is None:
            return
        logger.print_debug(
            "Generate paths to objects that can GPLink GPOs on OUs")

        starting_nodes_by_admin = {}
        ous_with_da_by_admin = {}

        for domain in self.domains:
            starting_nodes_by_admin[domain[0]] = []
            ous_with_da_by_admin[domain[0]] = []

        for path in self.objects_to_ou_handlers:
            try:
                self.paths_to_ou_handlers[path.nodes[-1].domain].append(path)
            except KeyError:
                self.paths_to_ou_handlers[path.nodes[-1].domain] = [path]
            if (
                path.nodes[0].labels != "OU"
                and path.nodes[0].name
                not in starting_nodes_by_admin[path.nodes[-1].domain]
            ):
                starting_nodes_by_admin[path.nodes[-1].domain].append(
                    path.nodes[0].name
                )
                self.nb_starting_nodes_to_ous += 1
            elif (
                path.nodes[0].labels == "OU"
                and path.nodes[0].name
                not in ous_with_da_by_admin[path.nodes[-1].domain]
            ):
                ous_with_da_by_admin[path.nodes[-1].domain].append(
                    path.nodes[0].name)
                self.nb_ous_with_da += 1

        for domain in self.domains:
            domain = domain[0]
            self.createGraphPage(
                self.arguments.cache_prefix,
                domain + "_paths_to_ou_handlers",
                "Paths to OU handlers",
                "_paths_to_ou_handlers",
                self.paths_to_ou_handlers[domain],
            )

        page = Page(
            self.arguments.cache_prefix,
            "graph_path_objects_to_ou_handlers",
            "Path to OU Handlers",
            "graph_path_objects_to_ou_handlers",
        )
        grid = Grid("Numbers of path to ou handlers per domain and objects")
        grid_data = []
        for domain in self.domains:
            domain = domain[0]
            if len(self.paths_to_ou_handlers[domain]) != 0:
                tmp_data = {}
                sortClass = str(len(ous_with_da_by_admin[domain])).zfill(6)
                tmp_data["Domain"] = '<i class="bi bi-globe2"></i> ' + domain
                tmp_data["Compromission paths"] = grid_data_stringify({
                    "value": f"{len(ous_with_da_by_admin[domain])} OU{'s' if len(ous_with_da_by_admin[domain]) > 1 else ''} exploitable by {len(starting_nodes_by_admin[domain])} object{'s' if len(starting_nodes_by_admin[domain]) > 1 else ''}",
                    "link": "%s_paths_to_ou_handlers.html" % quote(str(domain)),
                    "before_link": f'<i class="bi bi-shuffle {sortClass}"></i>'
                })
                # tmp_data["Paths to OU handlers"]= {"value" : '%d non DA may GPLink on %d OU' %(len(starting_nodes_by_admin[domain]),len(ous_with_da_by_admin[domain])), "link": "%s_paths_to_ou_handlers.html" % domain}
                grid_data.append(tmp_data)
        headers = ["Domain", "Compromission paths"]
        grid.setheaders(headers)
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    # OUs

    def get_domain_OUs(self):
        if self.domain_OUs is None:
            return

        def formatOU(listOfDict, headers):
            allValues = []
            dictData = {}
            nameList = []
            for dict in listOfDict:
                nameOfOU = dict["OU"]
                if nameOfOU not in nameList:
                    dictData[nameOfOU] = 1
                    nameList.append(nameOfOU)
                else:
                    dictData[nameOfOU] += 1
                allValues.append(
                    "<span class='corresponding-OU-%s'> %s </span>"
                    % (nameOfOU, dict["name"])
                )
            return dictData, allValues

        # Main grid
        headers = ["OU", "Number of objects"]
        page = Page(
            self.arguments.cache_prefix,
            "domain_OUs",
            "List of organisational units",
            "domain_OUs",
        )
        grid = Grid("Organisational Units")
        grid.setheaders(headers)

        dictOfOUs, allValues = formatOU(self.domain_OUs, headers)
        self.number_of_OU = len(dictOfOUs.keys())
        grid.setData(
            sorted(
                generic_formating.formatGridValues2Columns(
                    dictOfOUs, headers, "OU_member"
                ),
                key=lambda x: x[headers[1]],
                reverse=True,
            )
        )
        page.addComponent(grid)
        page.render()

        # Secondary grid
        page = Page(
            self.arguments.cache_prefix, "OU_member", "Member of OU", "OU_member"
        )
        grid = Grid("Member of OU")
        grid.addheader("TO CHANGE")
        OU_members = generic_formating.formatGridValues1Columns(
            allValues, grid.getHeaders()
        )
        grid.setData(OU_members)
        page.addComponent(grid)
        page.render()

    # Number of insufficient forest and domains functional levels
    def genInsufficientForestDomainsLevels(self):
        if self.vuln_functional_level is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "vuln_functional_level",
            "Number of insufficient forest and domains functional levels",
            "vuln_functional_level",
        )
        grid = Grid("Number of insufficient forest and domains functional levels")
        final_data = []
        for dico in self.vuln_functional_level:
            d = dico.copy()
            if d['Level maturity'] is None:
                continue
            elif d['Level maturity'] <= 1:
                color = "red"
            elif d['Level maturity'] <= 3:
                color = "orange"
            else:
                color = "green"
            d['Level maturity'] = f'<i class="bi bi-star-fill" style="color: {color}"></i>'*d['Level maturity'] + f'<i class="bi bi-star" style="color: {color}"></i>'*(5-d['Level maturity'])
            final_data.append(d)
        grid.setheaders(["Level maturity", "Full name", "Functional level"])
        grid.setData(final_data)
        page.addComponent(grid)
        page.render()

    def genDAToDAPaths(self):
        # get the result of the cypher request (a list of Path objects)
        paths = self.da_to_da
        # create the page
        page = Page(
            self.arguments.cache_prefix,
            "da_to_da",
            "Paths between different domains as domain admin",
            "da_to_da",
        )
        # create the grid
        grid = Grid("Paths between different domains as domain admin")
        # create the headers (domains)
        headers = []
        # future list of dicts
        pathLengthss = []
        graphDatas = {}
        if paths == None:
            grid.setheaders(["FROM / TO"])
            grid.setData([])
            return
        # for each path
        for domain in self.collected_domains:
            domain = domain[0]
            headers.append(domain)
            graphDatas[domain] = {}
            pathLengthss.append({"FROM / TO": '<i class="bi bi-globe2"></i> ' + domain, domain: "-"})
        for path in paths:
            # headers and pathLengths share the same index and it is cheaper to use headers here
            try:
                rowIndex = headers.index(path.nodes[0].name.split('@')[1])
            except ValueError:
                # Dirty fix in case there is a domain missing
                unknown_domain = path.nodes[0].name.split('@')[1]
                headers.append(unknown_domain)
                graphDatas[unknown_domain] = {}
                pathLengthss.append({"FROM / TO": '<i class="bi bi-globe2"></i> ' + unknown_domain, unknown_domain: "-"})
                rowIndex = headers.index(unknown_domain)

            # change value of the cell
            try:
                pathLengthss[rowIndex][path.nodes[-1].name.split('@')[1]] = {"value": pathLengthss[rowIndex][path.nodes[-1].name.split('@')[1]]["value"] + 1, "link": quote(path.nodes[0].name.split('@')[1]+"_to_"+path.nodes[-1].name.split('@')[1])+".html"}
            except KeyError:
                pathLengthss[rowIndex][path.nodes[-1].name.split('@')[1]] = {"value": 1, "link": quote(path.nodes[0].name.split('@')[1]+"_to_"+path.nodes[-1].name.split('@')[1])+".html"}

            # add a path to the list
            try:
                graphDatas[path.nodes[0].name.split('@')[1]][path.nodes[-1].name.split('@')[1]].append(path)
            except KeyError:
                graphDatas[path.nodes[0].name.split('@')[1]][path.nodes[-1].name.split('@')[1]] = [path]

        # fill the grid
        headers.insert(0, "FROM / TO")

        # Add some nice touch to the grid ;)
        for row in pathLengthss:
            # Add some text and icon to cells with links
            for key in row.keys():
                if key == "FROM / TO":
                    continue
                if row[key] == "-":
                    continue
                else:
                    sortClass = str(row[key]['value']).zfill(6)
                    row[key]['value'] = f"{row[key]['value']} path{'s' if row[key]['value'] > 1 else ''}"
                    row[key]['before_link'] = f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                    row[key] = grid_data_stringify(row[key])
            # Add some text to empty cells
            for header in headers:
                if header not in row.keys():
                    row[header] = "-"

        grid.setheaders(headers)
        grid.setData(pathLengthss)

        # create pages and graphs for each link
        for inputDomain, outputDomains in graphDatas.items():
            alreadySeenOutputDomains = []
            for outputDomain, paths in outputDomains.items():
                intGraph = Graph()
                # add each path to the graph
                for path in paths:
                    if (not(outputDomain in alreadySeenOutputDomains)):
                        # found a new domain reachable by the given input domain
                        self.crossDomain += 1
                        # each output domain is added once seen and the list is reset for each new input domain
                        alreadySeenOutputDomains.append(outputDomain)
                    intGraph.addPath(path)
                intPage = Page(
                    self.arguments.cache_prefix,
                    inputDomain+"_to_"+outputDomain,
                    "Paths through Domain Admins between "+inputDomain+" and "+outputDomain,
                    "da_to_da",
                )
                intPage.addComponent(intGraph)
                intPage.render()

        page.addComponent(grid)
        page.render()


    def genEmptyGroups(self):
        page = Page(
            self.arguments.cache_prefix,
            "empty_groups",
            "Groups with no object",
            "empty_groups",
        )
        grid = Grid("Groups without any object in it")
        headers = ["Empty group", "Full Reference"]

        for d in self.empty_groups:
            d["Empty group"] = '<i class="bi bi-people-fill"></i> ' + d["Empty group"]

        grid.setheaders(headers)
        grid.setData(self.empty_groups)

        page.addComponent(grid)
        page.render()

    def genEmptyOUs(self):
        page = Page(
            self.arguments.cache_prefix,
            "empty_ous",
            "OUs with no object",
            "empty_ous",
        )
        grid = Grid("OUs without any object in it")
        headers = ["Empty Organizational Unit", "Full Reference"]

        for d in self.empty_ous:
            d["Empty Organizational Unit"] = '<i class="bi bi-building"></i> ' + d["Empty Organizational Unit"]

        grid.setheaders(headers)
        grid.setData(self.empty_ous)

        page.addComponent(grid)
        page.render()

