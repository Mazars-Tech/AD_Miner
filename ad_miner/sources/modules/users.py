import json
import time
from xml.dom import UserDataHandler

from ad_miner.sources.modules import generic_computing
from ad_miner.sources.modules import generic_formating
from ad_miner.sources.modules import logger
#from relation_neo4j import Relation
from ad_miner.sources.modules.utils import days_format, grid_data_stringify, timer_format

from ad_miner.sources.modules.card_class import Card
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.table_class import Table


class Users:
    def __init__(self, arguments, neo4j, domain):
        self.arguments = arguments
        self.domain = domain
        self.start = time.time()
        logger.print_debug("Computing Users objects")
        self.neo4j = neo4j
        self.users = neo4j.all_requests["nb_enabled_accounts"]["result"]

        self.users_admin_computer = neo4j.all_requests["users_admin_on_computers"][
            "result"
        ]
        self.users_admin_computer_count = generic_computing.getCountValueFromKey(
            self.users_admin_computer, "user"
        )

        self.users_admin_computer_list = generic_computing.getListAdminTo(
            self.users_admin_computer, "user", "computer"
        )

        self.users_kerberos_as_rep = neo4j.all_requests["nb_as-rep_roastable_accounts"][
            "result"
        ]

        self.users_password_never_expires = neo4j.all_requests[
            "user_password_never_expires"
        ]["result"]
        self.users_kerberoastable_users = neo4j.all_requests[
            "nb_kerberoastable_accounts"
        ]["result"]
        self.users_krb_pwd_last_set = neo4j.all_requests["krb_pwd_last_change"][
            "result"
        ]
        self.users_domain_admin_on_nondc = neo4j.all_requests["dom_admin_on_non_dc"][
            "result"
        ]

        self.users_pwd_cleartext = neo4j.all_requests["nb_user_password_cleartext"][
            "result"
        ]

        self.objects_admincount_enabled = neo4j.all_requests["objects_admincount"][
            "result"
        ]

        self.users_shadow_credentials = neo4j.all_requests["users_shadow_credentials"][
            "result"
        ]
        self.users_shadow_credentials_uniq = []

        self.users_shadow_credentials_to_non_admins = neo4j.all_requests[
            "users_shadow_credentials_to_non_admins"
        ]["result"]

        self.users_rdp_access = neo4j.all_requests["rdp_access"]["result"]

        self.users_dc_impersonation = neo4j.all_requests["dc_impersonation"]["result"]
        if self.users_dc_impersonation != None:
            self.users_dc_impersonation_count = len(self.users_dc_impersonation)
        else:
            self.users_dc_impersonation_count=0

        self.group_anomaly_acl = neo4j.all_requests["group_anomaly_acl"]["result"]

        # users_can_impersonate_to_count = generic_computing.getCountValueFromKey(self.users_dc_impersonation, 'name')
        # self.users_can_impersonate_count = len(users_can_impersonate_to_count) if self.users_dc_impersonation is not None else None
        # dcs_can_be_impersonated_to_count = generic_computing.getCountValueFromKey(self.users_dc_impersonation, 'target')
        # self.dcs_can_be_impersonated_count = len(dcs_can_be_impersonated_to_count) if self.users_dc_impersonation is not None else None

        self.users_rbcd_attacks = self.removeAlreadyAdmins(
            neo4j.all_requests["rbcd"]["result"]
        )

        self.users_rdp_access_1 = (
            dict(
                sorted(
                    self.parseRDPData(self.users_rdp_access).items(),
                    key=lambda x: len(x[1]),
                    reverse=True,
                )
            )
            if self.users_rdp_access is not None
            else None
        )
        self.users_rdp_access_2 = (
            dict(
                sorted(
                    self.parseRDPdataByHosts(self.users_rdp_access).items(),
                    key=lambda x: len(x[1]),
                    reverse=True,
                )
            )
            if self.users_rdp_access is not None
            else None
        )

        rbcd_attacks_infos = (
            self.formatRBCD(self.users_rbcd_attacks)
            if self.users_rbcd_attacks is not None
            else None
        )
        self.users_rbcd_attacks_data = (
            rbcd_attacks_infos[0] if self.users_rbcd_attacks is not None else None
        )
        self.nb_users_rbcd_attacks = (
            rbcd_attacks_infos[1] if self.users_rbcd_attacks is not None else None
        )
        self.nb_computers_rbcd_attacks = (
            rbcd_attacks_infos[2] if self.users_rbcd_attacks is not None else None
        )
        if self.users_rbcd_attacks_data is not None:
            self.users_rbcd_attacks_data.sort(
                key=lambda x: x["Number of users"], reverse=True
            )
        self.can_read_laps = neo4j.all_requests["can_read_laps"]["result"]

        self.get_users_linked_admin_group = neo4j.all_requests[
            "get_users_linked_admin_group"
        ]["result"]
        self.get_groups_linked_admin_group = neo4j.all_requests[
            "get_groups_linked_admin_group"
        ]["result"]
        self.get_computers_linked_admin_group = neo4j.all_requests[
            "get_computers_linked_admin_group"
        ]["result"]
        self.get_users_direct_admin = neo4j.all_requests["get_users_direct_admin"][
            "result"
        ]
        self.users_to_computer_admin = {}

        if not neo4j.all_requests["users_admin_on_servers_1"]["result"]:
            neo4j.all_requests["users_admin_on_servers_1"]["result"] = []
        if not neo4j.all_requests["users_admin_on_servers_2"]["result"]:
            neo4j.all_requests["users_admin_on_servers_2"]["result"] = []
        self.users_admin_on_servers_all_data = (
            neo4j.all_requests["users_admin_on_servers_1"]["result"]
            + neo4j.all_requests["users_admin_on_servers_2"]["result"]
        )
        self.users_admin_on_servers = generic_computing.getCountValueFromKey(
            self.users_admin_on_servers_all_data, "computer"
        )
        self.users_admin_on_servers_list = generic_computing.getListAdminTo(
            neo4j.all_requests["users_admin_on_servers_1"]["result"]
            + neo4j.all_requests["users_admin_on_servers_2"]["result"],
            "computer",
            "user",
        )

        if (
            self.users_admin_on_servers is not None
            and self.users_admin_on_servers != {}
        ):
            self.servers_with_most_paths = self.users_admin_on_servers[
                list(self.users_admin_on_servers.keys())[0]
            ]
        else:
            self.servers_with_most_paths = []

        self.unpriv_to_dnsadmins = neo4j.all_requests["unpriv_to_dnsadmins"]["result"]
        self.vuln_sidhistory_dangerous = neo4j.all_requests[
            "vuln_sidhistory_dangerous"
        ]["result"]
        self.can_read_gmsapassword_of_adm = neo4j.all_requests[
            "can_read_gmsapassword_of_adm"
        ]["result"]
        self.objects_to_operators_member = neo4j.all_requests[
            "objects_to_operators_member"
        ]["result"]

        self.rbcd_paths = neo4j.all_requests["graph_rbcd"]["result"]
        self.rbcd_paths_to_da = neo4j.all_requests["graph_rbcd_to_da"]["result"]
        self.rbcd_to_da_graphs = {}
        self.rbcd_graphs = {}

        self.rbcd_nb_start_nodes = 0
        self.rbcd_nb_end_nodes = 0


        self.vuln_permissions_adminsdholder = neo4j.all_requests[
            "vuln_permissions_adminsdholder"
        ]["result"]

        self.can_read_laps_parsed = []

        self.users_password_not_required = neo4j.all_requests["get_users_password_not_required"]["result"]

        self.has_sid_history = neo4j.all_requests["has_sid_history"]["result"]

        # Generate all the users-related pages
        self.genComputersWithMostAdminsPage()
        self.genServersCompromisablePage()
        self.genUsersListPage(domain)
        self.genPrivilegedShadowCredsUsersPage()
        self.genUnprivilegedShadowCredsUsersPage()
        self.genUsersAdminOfComputersPage(domain)
        self.genASREPUsersPage()
        self.genUsersWithoutPasswordExpirationPage(domain)
        self.genKerberoastablesUsersPage()
        self.genKerberosUsersPage()
        self.genCleartextPasswordUsersPage()
        self.genSDHolderUsersPage()
        self.genRDPUsersPage()
        self.genRDPUsersComputerPage()
        self.genImpersonateDCUsersPage()
        self.genRBCDPage()
        self.genReadLAPSPage()
        self.genUsersDAonNonDCPage(domain)
        self.genDNSAdminsPage(domain)
        self.genAccountsDangerousSIDHistory()
        self.genObjectsReadGMSAPassword()
        self.generatePathToOperatorsMember(domain)
        self.genRBCDGraph(domain)
        self.generatePathToSDHolder(domain)
        self.generatePasswordNotRequiredPage()
        self.genHasSIDHistory()
        self.number_group_ACL_anomaly = self.genGroupAnomalyAcl(domain)

        logger.print_time(timer_format(time.time() - self.start))

    # List of Servers with the most user compromise paths (and if to handle empty cases)
    def genComputersWithMostAdminsPage(self):
        if self.users_admin_on_servers is None:
            return
        icon = '<i class="bi bi-people-fill"></i>'
        formated_data = generic_formating.formatGridValues2Columns(
            self.users_admin_on_servers,
            ["Computers", "Users who have a server compromise path"],
            "server_compromisable",
            icon=icon, icon2='<i class="bi bi-pc-display"></i> '
        )

        page = Page(
            self.arguments.cache_prefix,
            "server_users_could_be_admin",
            "Computers that are compromisable by users",
            "server_users_could_be_admin",
        )
        grid = Grid("Servers with the most user compromise paths")
        grid.setheaders(["Computers", "Users who have a server compromise path"])
        grid.setData(json.dumps(formated_data))
        page.addComponent(grid)
        page.render()

    # List of Compromisable servers
    def genServersCompromisablePage(self):
        if self.users_admin_on_servers_list is None:
            return
        allValues = []
        for computer, values in self.users_admin_on_servers_list.items():
            for v in values:
                allValues.append(
                    "<span class='compromisable-by-%s'> %s </span>" % (computer, v)
                )
        page = Page(
            self.arguments.cache_prefix,
            "server_compromisable",
            "Compromisable computers",
            "server_compromisable",
        )
        grid = Grid("Server compromisable")
        grid.addheader("TO CHANGE")
        users_admin_of_servers = generic_formating.formatGridValues1Columns(
            allValues, grid.getHeaders()
        )
        grid.setData(users_admin_of_servers)
        page.addComponent(grid)
        page.render()

        # List of users page

    def genUsersListPage(self, domain):
        if self.users is None:
            return
        page = Page(self.arguments.cache_prefix, "users", "List of all users", "users")
        grid = Grid("Users")
        grid.setheaders(["domain", "name", "last logon"])
        for user in self.users:
            user["domain"] = '<i class="bi bi-globe2"></i> ' + user["domain"]
            # Add admin icon
            if user["name"] in domain.admin_list:
                user["name"] = '<i class="bi bi-gem" title="This user is domain admin"></i> ' + user["name"]
            else:
                user["name"] = '<i class="bi bi-person-fill"></i> ' + user["name"]
            # Add calendar icon
            logon = -1
            if user.get("logon"):
                logon = user["logon"]
            user["last logon"] = days_format(logon)
        grid.setData(self.users)
        page.addComponent(grid)
        page.render()

        # Unpriv users that can perform shadow credentials on privileged users

    def genPrivilegedShadowCredsUsersPage(self):
        if self.users_shadow_credentials is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "users_shadow_credentials",
            "List of non-privileged users that can perform shadow credentials on privileged accounts",
            "users_shadow_credentials",
        )
        # Build raw data from requests
        data = {}
        for path in self.users_shadow_credentials:
            try:
                data[path.nodes[0]]["paths"].append(path)
                if path.nodes[-1].name not in data[path.nodes[0]]["target"]:
                    data[path.nodes[0]]["target"].append(path.nodes[-1].name)
            except KeyError:
                data[path.nodes[0]] = {
                    "domain": path.nodes[0].domain,
                    "name": path.nodes[0].name,
                    "target": [path.nodes[-1].name],
                    "paths": [path]
                }

        # Build grid data
        grid_data = []
        for d in data.values():
            sortClass = str(len(d['paths'])).zfill(6)
            tmp_grid_data = {
                "domain": '<i class="bi bi-globe2"></i> ' + d["domain"],
                "name": '<i class="bi bi-person-fill"></i> ' + d["name"],
                "target": grid_data_stringify({
                    "value": f"{len(d['paths'])} paths to {len(d['target'])} target{'s' if len(d['target'])>1 else ''} <i class='bi bi-box-arrow-up-right'></i>",
                    "link": f"users_shadow_credentials_from_{d['name']}.html",
                    "before_link": f"<i class='{sortClass} bi bi-shuffle' aria-hidden='true'></i>"
                })
            }
            grid_data.append(tmp_grid_data)
            # Build graph data
            page_graph = Page(self.arguments.cache_prefix, f"users_shadow_credentials_from_{d['name']}", f"{d['name']} shadow credentials attack paths on privileged accounts", "users_shadow_credentials")
            graph = Graph()
            graph.setPaths(d['paths'])
            page_graph.addComponent(graph)
            page_graph.render()

        self.users_shadow_credentials_uniq = data.keys()
        grid = Grid("Shadow credentials")
        grid.setheaders(["domain", "name", "target"])
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    # Unpriv users that can perform shadow credentials on unprivileged users
    def genUnprivilegedShadowCredsUsersPage(self):
        if self.users_shadow_credentials_to_non_admins is None:
            return

        data = {}
        for path in self.users_shadow_credentials_to_non_admins:
            try:
                data[path.nodes[-1]]["paths"].append(path)
            except KeyError:
                data[path.nodes[-1]] = {
                    "domain": path.nodes[-1].domain,
                    "target": path.nodes[-1].name,
                    "paths": [path]
                }
        grid_data = []
        max_paths = 0
        for target in data.keys():
            nb_paths = len(data[target]["paths"])
            max_paths = max(max_paths, nb_paths)
            sortClass = str(nb_paths).zfill(6)
            grid_data.append(
                {
                    "domain": '<i class="bi bi-globe2"></i> ' + data[target]["domain"],
                    "target": '<i class="bi bi-bullseye"></i> ' + data[target]["target"],
                    "paths": grid_data_stringify({
                        "value": f"{nb_paths} paths to target <i class='bi bi-box-arrow-up-right'></i>",
                        "link": f"users_shadow_credentials_to_non_admins_to_{data[target]['target']}.html",
                        "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                    })
                }
            )
            graph_page = Page(self.arguments.cache_prefix,
            f"users_shadow_credentials_to_non_admins_to_{data[target]['target']}",
            "List of targets that can be compromised through shadow credentials",
            "users_shadow_credentials")
            graph = Graph()
            graph.setPaths(data[target]['paths'])
            graph_page.addComponent(graph)
            graph_page.render()

        if self.users_shadow_credentials_to_non_admins != None:
            self.max_number_users_shadow_credentials_to_non_admins = max_paths
        else:
            self.max_number_users_shadow_credentials_to_non_admins = 0

        page = Page(
            self.arguments.cache_prefix,
            "users_shadow_credentials_to_non_admins",
            "List of targets that can be compromised through shadow credentials",
            "users_shadow_credentials"
        )
        grid = Grid("Users")
        grid.setheaders(["domain", "target", "paths"])
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    # List of users admin of computers page
    def genUsersAdminOfComputersPage(self, domain):

        # Several requests are needed for this function, therefore we fail if there is one missing, and we print the issue
        fail = []
        if self.users_admin_computer_list is None:
            fail.append("users_admin_computer_list")

        if self.users_kerberoastable_users is None:
            fail.append("users_kerberoastable_users")

        if domain.users_pwd_not_changed_since is None:
            fail.append("users_pwd_not_changed_since")

        if 0 < len(fail) < 3:  # if only some of them are activated
            logger.print_error(
                f" In order to render 'List of users admin of computers' page, you need to activate the following in config.json : {', '.join(fail)}"
            )
            return

        if len(fail) > 0:
            return

        headers = [
            "User",
            "Kerberoastable",
            "Last password change",
            "List of computers",
            "Path to computers",
            "Path to DA",
        ]
        headers_details = ["User", "Computers"]

        def generateGraphPathToAdmin(self, domain):
            data = []
            for couple in self.get_users_linked_admin_group:
                u = couple["u"]
                g = couple["gg"]

                start = Node(couple["idu"], "User", u["name"], u["domain"], "MemberOf")
                end = Node(couple["idg"], "Group", g["name"], g["domain"], "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "MemberOf"
                # )

                path = Path([start, end])
                data.append(path)
                self.users_to_computer_admin[u["name"]] = couple["idu"]

            for couple in self.get_groups_linked_admin_group:
                g = couple["g"]
                gg = couple["gg"]

                start = Node(couple["idg"], "Group", g["name"], g["domain"], "MemberOf")
                end = Node(couple["idgg"], "Group", gg["name"], gg["domain"], "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "MemberOf"
                # )

                path = Path([start, end])
                data.append(path)

            for couple in self.get_computers_linked_admin_group:
                g = couple["g"]
                c = couple["c"]

                start = Node(couple["idg"], "Group", g["name"], g["domain"], "AdminTo")
                end = Node(couple["idc"], "Computer", c["name"], c["domain"], "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "AdminTo"
                # )

                path = Path([start, end])
                data.append(path)

            for couple in self.get_users_direct_admin:
                g = couple["g"]
                c = couple["c"]

                start = Node(couple["idg"], "User", g["name"], g["domain"], "AdminTo")
                end = Node(couple["idc"], "Computer", c["name"], c["domain"], "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "AdminTo"
                # )

                path = Path([start, end])
                data.append(path)
                self.users_to_computer_admin[g["name"]] = couple["idg"]

            page = Page(
                self.arguments.cache_prefix,
                "users_to_computers",
                "Paths from users to computers",
                "users_to_computers",
            )
            graph = Graph()
            graph.setPaths(data)

            graph.addGhostComputers(domain.dico_ghost_computer)
            graph.addGhostUsers(domain.dico_ghost_user)
            graph.addDCComputers(domain.dico_dc_computer)
            graph.addUserDA(domain.dico_user_da)
            graph.addGroupDA(domain.dico_da_group)

            page.addComponent(graph)
            page.render()

        def check_kerberoastable(account):
            for elem in self.users_kerberoastable_users:
                if elem["name"] == account:
                    return "<i class='bi bi-ticket-perforated-fill' title='This account is vulnerable to Kerberoasting'></i> YES"
            return "-"

        def get_last_pass_change(account, domain):
            for elem in domain.users_pwd_not_changed_since:
                if elem["user"] == account:
                    sortClass = str(elem["days"]).zfill(
                        6
                    )  # used to make the sorting feature work with icons
                    return "<i class='bi bi-calendar3 %s'></i> %d days ago" % (
                        sortClass,
                        elem["days"],
                    )
            return "<i class='bi bi-calendar3'></i> Very recently"

        generateGraphPathToAdmin(self, domain)

        tmp_rslt = []
        for key in self.users_admin_computer_list.keys():
            partDict = {}
            partDict[headers[0]] = key

            partDict[headers[1]] = check_kerberoastable(key)
            partDict[headers[2]] = get_last_pass_change(key, domain)

            partDict[headers[3]] = self.users_admin_computer_list[key]
            try:  # Case when node is not present in graph
                partDict[headers[4]] = grid_data_stringify({
                    "link": f"users_to_computers.html?node={self.users_to_computer_admin[key]}",
                    "value": "Path to computers <i class='bi bi-box-arrow-up-right'></i>",
                    "before_link": f"<i class='bi bi-shuffle' aria-hidden='true'></i>"
                })
            except KeyError:
                partDict[headers[4]] = "No path to show"

            nb_path_to_da, nb_domain = self.domain.findAndCreatePathToDaFromUsersList(
                key, partDict[headers[3]]
            )
            if nb_path_to_da > 0:
                sortClass = str(nb_path_to_da).zfill(6)
                partDict[headers[5]] = grid_data_stringify({
                    "link": "users_path_to_da_from_%s.html" % key,
                    "value": f" {nb_path_to_da} path{'s' if nb_path_to_da > 1 else ''} to DA ({nb_domain} domain{'s' if nb_domain > 1 else ''}) <i class='bi bi-box-arrow-up-right'></i>",
                    "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                })
            else:
                partDict[headers[5]] = "-"
            tmp_rslt.append(partDict)

        # This loop should return nothing, just in case
        for key in self.users_to_computer_admin.keys():
            if key not in self.users_admin_computer_list.keys():
                partDict = {}
                partDict[headers[0]] = key

                partDict[headers[1]] = check_kerberoastable(key)
                partDict[headers[2]] = get_last_pass_change(key, domain)

                partDict[headers[3]] = "No data to show"
                try:  # Case when node is not present in graph
                    partDict[headers[4]] = grid_data_stringify({
                        "link": f"users_to_computers.html?node={self.users_to_computer_admin[key]}",
                        "value": "Path to computers <i class='bi bi-box-arrow-up-right'></i>",
                        "before_link": f"<i class='bi bi-shuffle' aria-hidden='true'></i>"
                    })
                except KeyError:
                    partDict[headers[4]] = "No path to show"
                (
                    nb_path_to_da,
                    nb_domain,
                ) = self.domain.findAndCreatePathToDaFromUsersList(
                    key, partDict[headers[3]]
                )
                if nb_path_to_da > 0:
                    sortClass = str(nb_path_to_da).zfill(6)
                    partDict[headers[5]] = grid_data_stringify({
                    "link": "users_path_to_da_from_%s.html" % key,
                    "value": f" {nb_path_to_da} path{'s' if nb_path_to_da > 1 else ''} to DA ({nb_domain} domain{'s' if nb_domain > 1 else ''}) <i class='bi bi-box-arrow-up-right'></i>",
                    "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                })
                else:
                    partDict[headers[5]] = "-"
                tmp_rslt.append(partDict)

        formated_data = []
        formated_data_details = []
        for dict in tmp_rslt:
            if dict[headers[3]] != "No data to show":
                sortClass = str(len(dict[headers[3]])).zfill(6)  # used to make the sorting feature work with icons
                data_header_computer = grid_data_stringify({
                    "link": "%s.html?parameter=%s"
                    % ("users_admin_of_computers_details", dict[headers[0]]),
                    "value": f" {len(dict[headers[3]])} Computer{'s' if len(dict[headers[3]]) > 1 else ''} <i class='bi bi-box-arrow-up-right'></i>",
                    "before_link": f"<i class='bi bi-pc-display-horizontal {sortClass}'></i>"
                })
                formated_data_details.append(
                    {
                        headers_details[0]: dict[headers[0]],
                        headers_details[1]: dict[headers[3]],
                    }
                )
            if dict[headers[0]] in domain.admin_list:
                formated_data.append(
                    {
                        headers[0]: '<i class="bi bi-gem" title="This user is domain admin"></i> '
                        + dict[headers[0]],
                        headers[1]: dict[headers[1]],
                        headers[2]: dict[headers[2]],
                        headers[3]: data_header_computer,
                        headers[4]: dict[headers[4]],
                        headers[5]: dict[headers[5]],
                    }
                )
            else:
                formated_data.append(
                    {
                        headers[0]: '<i class="bi bi-person-fill"></i> ' + dict[headers[0]],
                        headers[1]: dict[headers[1]],
                        headers[2]: dict[headers[2]],
                        headers[3]: data_header_computer,
                        headers[4]: dict[headers[4]],
                        headers[5]: dict[headers[5]],
                    }
                )
        page = Page(
            self.arguments.cache_prefix,
            "users_admin_of_computers",
            "Users that are administrator of computers",
            "users_admin_of_computers",
        )
        grid = Grid("Users admins of")
        if len(self.users_admin_computer_count) > 0:
            if formated_data != [] and formated_data is not None:
                grid.setheaders(headers)
                grid.setData(json.dumps(formated_data))
        page.addComponent(grid)
        page.render()
        self.users_admin_of_computers = formated_data

        page = Page(
            self.arguments.cache_prefix,
            "users_admin_of_computers_details",
            "Users that are administrator of computers",
            "users_admin_of_computers",
        )
        grid = Grid("Users admins of")
        if len(self.users_admin_computer_count) > 0:
            if formated_data_details != [] and formated_data_details is not None:
                grid.setheaders(headers)
                grid.setData(json.dumps(formated_data_details))
        page.addComponent(grid)
        page.render()

    # List of user account with AS-REP
    def genASREPUsersPage(self):
        if self.users_kerberos_as_rep is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "as_rep",
            "List of all users with AS-REP",
            "as_rep",
        )
        grid = Grid("Users with AS-REP")
        grid.setheaders(["domain", "name", "is_Domain_Admin"])
        grid.setData(json.dumps(self.users_kerberos_as_rep))
        page.addComponent(grid)
        page.render()

        # List of user without password expiration

    def genUsersWithoutPasswordExpirationPage(self, domain):
        if self.users_password_never_expires is None:
            return
        for user in self.users_password_never_expires:
            # Add admin icon
            if user["name"] in domain.admin_list:
                user["name"] = '<i class="bi bi-gem" title="This user is domain admin"></i> ' + user["name"]
            else:
                user["name"] = '<i class="bi bi-person-fill"></i> ' + user["name"]
        page = Page(
            self.arguments.cache_prefix,
            "never_expires",
            "List of all users without password expiration",
            "never_expires",
        )
        grid = Grid("Users without password expiration")
        grid.setheaders(["domain", "name", "Last login", "Last password change", "Account Creation Date"])


        data = []
        for dict in self.users_password_never_expires:
            tmp_data = {"domain": '<i class="bi bi-globe2"></i> ' + dict["domain"], "name": dict["name"]}
            tmp_data["Last login"] = days_format(dict["LastLogin"])
            tmp_data["Last password change"] = days_format(dict["LastPasswChange"])
            tmp_data["Account Creation Date"] = days_format(dict["accountCreationDate"])

            data.append(tmp_data)
        grid.setData(data)
        page.addComponent(grid)
        page.render()

    # List of kerberoastables users
    def genKerberoastablesUsersPage(self):
        if self.users_kerberoastable_users is None:
            return

        SPNs = []
        child_headers = ["Account", "SPN"]
        for user in self.users_kerberoastable_users:
            n = 0
            if not user.get("SPN"):
                continue
            for s in user["SPN"]:
                child_dict = {}
                child_dict[child_headers[0]] = user["name"]
                child_dict[child_headers[1]] = s
                SPNs.append(child_dict)
                n += 1
            sortClass = str(n).zfill(6)  # used to make the sorting feature work with icons
            user["SPN"] = grid_data_stringify({
                "link": "%s.html?parameter=%s" % ("kerberoastables_SPN", user["name"]),
                "value": f"{n} SPN{'s' if n > 1 else ''} <i class='bi bi-box-arrow-up-right'></i></span>",
                "before_link": f'<i class="bi bi-list-task {sortClass}"></i>'
            })

        child_page = Page(
            self.arguments.cache_prefix,
            "kerberoastables_SPN",
            "List of SPN",
            "kerberoastables_SPN",
        )
        child_grid = Grid("SPN")
        child_grid.setheaders(child_headers)
        child_grid.setData(SPNs)
        child_page.addComponent(child_grid)
        child_page.render()

        page = Page(
            self.arguments.cache_prefix,
            "kerberoastables",
            "List of kerberoastable account",
            "kerberoastables",
        )
        grid = Grid("Kerberoastable users")
        grid.setheaders(
            ["domain", "name", "Last password change", "Account Creation Date", "SPN"]
        )

        for elem in range(len(self.users_kerberoastable_users)):
            if self.users_kerberoastable_users[elem]["is_Domain_Admin"] == True:
                self.users_kerberoastable_users[elem]["name"] = '<i class="bi bi-gem" title="This user is domain admin"></i> ' + self.users_kerberoastable_users[elem]["name"]
            else:
                self.users_kerberoastable_users[elem]["name"] = '<i class="bi bi-person-fill"></i> ' + self.users_kerberoastable_users[elem]["name"]

        data = []
        for dict in self.users_kerberoastable_users:
            tmp_data = {"domain": '<i class="bi bi-globe2"></i> ' + dict["domain"]}
            tmp_data["name"] = dict["name"]
            tmp_data["Last password change"] = days_format(dict["pass_last_change"])
            tmp_data["Account Creation Date"] = days_format(dict["accountCreationDate"])
            tmp_data["SPN"] = dict["SPN"]
            data.append(tmp_data)

        #print("users_kerberoastable_users : ", json.dumps(self.users_kerberoastable_users))
        grid.setData(data)
        page.addComponent(grid)
        page.render()

        # List of Kerberos accounts

    def genKerberosUsersPage(self):
        if self.users_krb_pwd_last_set is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "krb_last_change",
            "KRBTGT account",
            "krb_last_change",
        )
        grid = Grid("KRBTGT account")
        grid.setheaders(["domain", "name", "Last password change", "Account Creation Date"])

        data = []
        for dict in self.users_krb_pwd_last_set:
            tmp_data = {"domain": '<i class="bi bi-globe2"></i> ' + dict["domain"]}
            tmp_data["name"] = '<i class="bi bi-ticket-perforated-fill"></i> ' + dict["name"]
            tmp_data["Last password change"] = days_format(dict["pass_last_change"])
            tmp_data["Account Creation Date"] = days_format(dict["accountCreationDate"])
            data.append(tmp_data)


        grid.setData(data)
        page.addComponent(grid)
        page.render()

    # Users with password in cleartext
    def genCleartextPasswordUsersPage(self):
        if self.users_pwd_cleartext is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "users_pwd_cleartext",
            "Number of users with password in cleartext",
            "users_pwd_cleartext",
        )
        grid = Grid("Users with password in cleartext")
        grid.setheaders(["user", "password", "is Domain Admin"])
        grid.setData(json.dumps(self.users_pwd_cleartext))
        page.addComponent(grid)
        page.render()

    # List of objects with SDHolder
    def genSDHolderUsersPage(self):
        if self.objects_admincount_enabled is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "objects_adminsdholder",
            "Number of objects with AdminSDHolder ",
            "objects_with_adminSDHolder",
        )
        grid = Grid("Objects having AdminSDHolder")
        grid.setheaders(["domain", "type", "name"])
        grid.setData(self.objects_admincount_enabled)
        page.addComponent(grid)
        page.render()

    # Users with RDP access
    def genRDPUsersPage(self):
        if self.users_rdp_access_1 is None:
            return
        headers = ["Users", "Computers"]
        formated_data = []
        for key in self.users_rdp_access_1:
            sortClass = str(len(self.users_rdp_access_1[key])).zfill(6)
            d = {
                "Users": '<i class="bi bi-person-fill"></i> ' + key,
                "Computers": grid_data_stringify({
                    "value": f"{len(self.users_rdp_access_1[key])} Computers <i class='bi bi-box-arrow-up-right'></i><p style='visibility:hidden;'>{self.users_rdp_access_1[key]}</p>",
                    "link": f"users_rdp_access.html?parameter={key}",
                    "before_link": f'<i class="bi bi-pc-display {sortClass}"></i>'
                })
            }
            formated_data.append(d)
        page = Page(
            self.arguments.cache_prefix,
            "users_rdp_access",
            "Users with RDP access",
            "users_rdp_access",
        )
        grid = Grid("Users with RDP access")
        grid.setheaders(headers)
        grid.setData(formated_data)
        page.addComponent(grid)
        page.render()

    # Computer's list of RDP Users (whatever that means ?)
    def genRDPUsersComputerPage(self):
        if self.users_rdp_access_2 is None:
            return
        #headers = ["Computers", "Number of users", "Users"]
        #formated_data = generic_formating.formatGridValues3Columns(
        #    generic_formating.formatFor3Col(self.users_rdp_access_2, headers),
        #    headers,
        #    "computers_list_of_rdp_users",
        #)
        headers = ["Computers", "Users"]
        formated_data = []
        for key in self.users_rdp_access_2:
            sortClass = str(len(self.users_rdp_access_2[key])).zfill(6)
            d = {
                "Computers": '<i class="bi bi-pc-display"></i> ' + key,
                "Users": grid_data_stringify({
                    "value": f"{len(self.users_rdp_access_2[key])} Users <i class='bi bi-box-arrow-up-right'></i><p style='visibility:hidden;'>{self.users_rdp_access_2[key]}</p>",
                    "link": f"computers_list_of_rdp_users.html?parameter={key}",
                    "before_link": f'<i class="bi bi-person-fill {sortClass}"></i>'
                })
            }
            formated_data.append(d)
        page = Page(
            self.arguments.cache_prefix,
            "computers_list_of_rdp_users",
            "Computers that can be accessed through RDP",
            "computers_list_of_rdp_users",
        )
        grid = Grid("Computers' lists of RDP users")
        grid.setheaders(headers)
        grid.setData(formated_data)
        page.addComponent(grid)
        page.render()

    # List of users that can impersonate a DC
    def genImpersonateDCUsersPage(self):
        if not self.users_dc_impersonation:
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "dc_impersonation",
            "DC Impersonation",
            "dc_impersonation",
            self.users_dc_impersonation,
            self.domain,
        )

    # Users that can perform RBCD
    def genRBCDPage(self):
        if self.users_rbcd_attacks_data is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "rbcd",
            "Users able to RBCD attack",
            "rbcd_attack",
        )
        grid = Grid("Users that can perform RBCD attacks")
        grid.setheaders(["Computer name", "ACL", "Group name", "Number of users"])
        grid.setData(self.users_rbcd_attacks_data)
        page.addComponent(grid)
        page.render()

    def genReadLAPSPage(self):
        if self.can_read_laps is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "can_read_laps",
            "Objects able to read LAPS password",
            "can_read_laps",
        )
        grid = Grid("Objects able to LAPS passwords")
        grid.setheaders(["domain", "name"])
        self.can_read_laps_parsed = [
            {
                "domain": '<i class="bi bi-globe2"></i> ' + user["domain"],
                "name": '<i class="bi bi-person-fill"></i> ' + user["name"]
            }
            for user in self.can_read_laps if user["domain"] is not None and user["name"] is not None
        ]
        grid.setData(self.can_read_laps_parsed)
        page.addComponent(grid)
        page.render()

    def genUsersDAonNonDCPage(self, domain):
        if self.users_domain_admin_on_nondc is None:
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "dom_admin_on_non_dc",
            "Domain admin with sessions on non DC computers ",
            "dom_admin_on_non_dc",
            self.users_domain_admin_on_nondc,
            domain,
        )

    def genDNSAdminsPage(self, domain):
        if self.unpriv_to_dnsadmins is None:
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "unpriv_to_dnsadmins",
            "Unprivileged users with path to DNSAdmins",
            "unpriv_to_dnsadmins",
            self.unpriv_to_dnsadmins,
            domain,
        )

    # List of users with RDP access
    def parseRDPData(self, list_of_dict):
        final_dict = {}
        for dict in list_of_dict:
            if dict["user"] in final_dict.keys():
                final_dict[dict["user"]] += [dict["computer"]]
            else:
                final_dict[dict["user"]] = [dict["computer"]]
        return final_dict

    # List of users that can access a given computer with rdp
    def parseRDPdataByHosts(self, list_of_dict):
        final_dict = {}
        for dict in list_of_dict:
            if dict["computer"] in final_dict.keys():
                final_dict[dict["computer"]] += [dict["user"]]
            else:
                final_dict[dict["computer"]] = [dict["user"]]
        return final_dict

    # List of users that can indirectly act as an admin on a computer without being one
    def removeAlreadyAdmins(self, data):
        if data is None:
            return None
        todelete = []
        # todeleteuser = []
        # todeletecomputer = []
        prevUser = ""
        # prevGroup=""
        prevAcl = ""
        prevComputer = ""
        lastAction = ""
        # i=0
        for k in range(len(data)):
            if data[k]["acl"] == "AdminTo":
                todelete.append(k)
                lastAction = "del"
            else:
                if (
                    (lastAction == "del" or prevAcl == "AdminTo")
                    and prevUser == data[k]["username"]
                    and prevComputer == data[k]["computername"]
                ):
                    todelete.append(k)
                else:
                    lastAction = ""
            prevUser = data[k]["username"]
            # prevGroup=data[k]['groupname']
            prevAcl = data[k]["acl"]
            prevComputer = data[k]["computername"]
        for x in range(len(todelete) - 1, -1, -1):
            data.pop(todelete[x])
        return data

    def formatRBCD(self, data):
        data.sort(key=lambda x: x["username"])
        if data != [] and data is not None:
            users = [data[0]["username"]]
            for d in data:
                if d["username"] != users[-1]:
                    users.append(d["username"])

            data.sort(key=lambda x: x["groupname"])
            data.sort(key=lambda x: x["acl"])
            data.sort(key=lambda x: x["computername"])
            computername_temp = data[0]["computername"]
            groupname_temp = data[0]["groupname"]
            acl_temp = data[0]["acl"]
            final_tab = []
            init = {
                "Computer name": computername_temp,
                "ACL": acl_temp,
                "Group name": groupname_temp,
                "Number of users": 1,
            }
            final_tab.append(init)

            pos = 0
            computers = [computername_temp]
            for i in range(1, len(data)):
                cd = data[i]
                if cd["computername"] != computers[-1]:
                    computers.append(cd["computername"])
                if (
                    cd["computername"] == computername_temp
                    and cd["groupname"] == groupname_temp
                    and cd["acl"] == acl_temp
                ):
                    final_tab[pos]["Number of users"] += 1
                else:
                    computername_temp = data[i]["computername"]
                    groupname_temp = data[i]["groupname"]
                    acl_temp = data[i]["acl"]
                    nd = {
                        "Computer name": computername_temp,
                        "ACL": acl_temp,
                        "Group name": groupname_temp,
                        "Number of users": 1,
                    }
                    final_tab.append(nd)
                    pos += 1

            nb_users = len(users)
            nb_computers = len(computers)
            return final_tab, nb_users, nb_computers
        else:
            return [], 0, 0

    @staticmethod
    def createGraphPage(
        render_prefix, page_name, page_title, page_description, graph_data, domain
    ):
        page = Page(render_prefix, page_name, page_title, page_description)
        graph = Graph()
        graph.setPaths(graph_data)

        graph.addGhostComputers(domain.dico_ghost_computer)
        graph.addGhostUsers(domain.dico_ghost_user)
        graph.addDCComputers(domain.dico_dc_computer)
        graph.addUserDA(domain.dico_user_da)
        graph.addGroupDA(domain.dico_da_group)

        page.addComponent(graph)
        page.render()

    # Number of accounts or groups with unexpected SID history
    def genAccountsDangerousSIDHistory(self):
        if self.vuln_sidhistory_dangerous is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "vuln_sidhistory_dangerous",
            "Number of accounts or groups with unexpected SID history",
            "vuln_sidhistory_dangerous",
        )
        grid = Grid("Number of accounts or groups with unexpected SID history")
        grid.setheaders(["parent_domain", "name", "sidhistory"])
        grid.setData(self.vuln_sidhistory_dangerous)
        page.addComponent(grid)
        page.render()

    # Objects allowed to read the GMSA of objects with admincount=True
    def genObjectsReadGMSAPassword(self):
        if self.can_read_gmsapassword_of_adm is None:
            return
        # page = Page(
        #     self.arguments.cache_prefix,
        #     "can_read_gmsapassword_of_adm",
        #     "Objects allowed to read the GMSA of objects with admincount=True",
        #     "can_read_gmsapassword_of_adm",
        # )
        # grid = Grid("Number of accounts or groups with unexpected SID history")
        # grid.setheaders(["domain", "object_allowed", "object_targeted"])
        # grid.setData(self.can_read_gmsapassword_of_adm)
        # page.addComponent(grid)
        # page.render()
        page = Page(
            self.arguments.cache_prefix,
            "can_read_gmsapassword_of_adm",
            "List of non-privileged users that can read GMSAPassword on privileged accounts",
            "can_read_gmsapassword_of_adm",
        )
        # Build raw data from requests
        data = {}
        for path in self.can_read_gmsapassword_of_adm:
            try:
                data[path.nodes[0]]["paths"].append(path)
                if path.nodes[-1].name not in data[path.nodes[0]]["target"]:
                    data[path.nodes[0]]["target"].append(path.nodes[-1].name)
            except KeyError:
                data[path.nodes[0]] = {
                    "domain": path.nodes[0].domain,
                    "name": path.nodes[0].name,
                    "target": [path.nodes[-1].name],
                    "paths": [path]
                }

        # Build grid data
        grid_data = []
        for d in data.values():
            sortClass = str(len(d['paths'])).zfill(6)
            tmp_grid_data = {
                "domain": '<i class="bi bi-globe2"></i> ' + d["domain"],
                "name": '<i class="bi bi-person-fill"></i> ' + d["name"],
                "target": grid_data_stringify({
                    "value": f"{len(d['paths'])} paths to {len(d['target'])} target{'s' if len(d['target'])>1 else ''} <i class='bi bi-box-arrow-up-right'></i>",
                    "link": f"can_read_gmsapassword_of_adm_from_{d['name']}.html",
                    "before_link": f"<i class='{sortClass} bi bi-shuffle' aria-hidden='true'></i>"
                })
            }
            grid_data.append(tmp_grid_data)
            # Build graph data
            page_graph = Page(self.arguments.cache_prefix, f"can_read_gmsapassword_of_adm_from_{d['name']}", f"{d['name']} can read GMSA Password attack paths on privileged accounts", "can_read_gmsapassword_of_adm")
            graph = Graph()
            graph.setPaths(d['paths'])
            page_graph.addComponent(graph)
            page_graph.render()

        self.can_read_gmsapassword_of_adm = data.keys()
        grid = Grid("Users that can read GMSA Password")
        grid.setheaders(["domain", "name", "target"])
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()


    def generatePathToOperatorsMember(self, domain):
        if self.objects_to_operators_member is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "objects_to_operators_member",
            "Unprivileged path to an operator member",
            "objects_to_operators_member",
        )
        # Build raw data from requests
        data = {}
        for path in self.objects_to_operators_member:
            try:
                data[path.nodes[0]]["paths"].append(path)
                if path.nodes[-1].name not in data[path.nodes[0]]["target"]:
                    data[path.nodes[0]]["target"].append(path.nodes[-1].name)
            except KeyError:
                data[path.nodes[0]] = {
                    "domain": '<i class="bi bi-globe2"></i> ' + path.nodes[0].domain,
                    "name": '<i class="bi bi-person-fill"></i> ' + path.nodes[0].name,
                    "link": path.nodes[0].name,
                    "target": [path.nodes[-1].name],
                    "paths": [path]
                }

        # Build grid data
        grid_data = []
        for d in data.values():
            sortClass = str(len(d['paths'])).zfill(6)
            tmp_grid_data = {
                "domain": d["domain"],
                "name": d["name"],
                "target": grid_data_stringify({
                    "value": f"{len(d['paths'])} paths to {len(d['target'])} target{'s' if len(d['target'])>1 else ''} <i class='bi bi-box-arrow-up-right'></i>",
                    "link": f"objects_to_operators_member_from_{d['link']}.html",
                    "before_link": f"<i class='{sortClass} bi bi-shuffle' aria-hidden='true'></i>"
                })
            }
            grid_data.append(tmp_grid_data)
            # Build graph data
            page_graph = Page(self.arguments.cache_prefix, f"objects_to_operators_member_from_{d['link']}", f"{d['link']} can have a path to an Operator member", "objects_to_operators_member")
            graph = Graph()
            graph.setPaths(d['paths'])
            page_graph.addComponent(graph)
            page_graph.render()

        self.objects_to_operators_member = data.keys()
        grid = Grid("Users that can have a path to Operator member")
        grid.setheaders(["domain", "name", "target"])
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

    def genRBCDGraph(self, domain):
        if self.rbcd_paths is None:
            return
        logger.print_debug("Generate paths of objects that can RCBD on a computer")


        for path in self.rbcd_paths_to_da:
            starting_node = path.nodes[0]
            starting_node_name = starting_node.name
            if starting_node_name not in list(self.rbcd_to_da_graphs.keys()):
                self.rbcd_to_da_graphs[starting_node_name] = {}
                self.rbcd_to_da_graphs[starting_node_name]["paths"] = []
            if path not in self.rbcd_to_da_graphs[starting_node_name]["paths"]:
                self.rbcd_to_da_graphs[starting_node_name]["paths"].append(path)

        for object_name in list(self.rbcd_to_da_graphs.keys()):
            self.createGraphPage(
                self.arguments.cache_prefix,
                "rbcd_target_" + object_name + "_paths_to_da",
                "Path to DA from " + object_name + " RBCD target",
                "graph_path_objects_to_da",
                self.rbcd_to_da_graphs[object_name]["paths"],
                domain,
            )


        ending_nodes_names_distinct = []

        for path in self.rbcd_paths:
            starting_node = path.nodes[0]
            starting_node_name = starting_node.name
            ending_node = path.nodes[-1]
            ending_node_name = ending_node.name

            if starting_node_name not in list(self.rbcd_graphs.keys()):
                self.rbcd_nb_start_nodes += 1
                self.rbcd_graphs[starting_node_name] = {}
                self.rbcd_graphs[starting_node_name]["paths"] = []
                self.rbcd_graphs[starting_node_name]["nb_paths_to_da"] = 0
                self.rbcd_graphs[starting_node_name]["destinations"] = []
                self.rbcd_graphs[starting_node_name]["domain"] = starting_node.domain
            if path not in self.rbcd_graphs[starting_node_name]["paths"]:
                self.rbcd_graphs[starting_node_name]["paths"].append(path)
            if ending_node_name not in self.rbcd_graphs[starting_node_name]["destinations"]:
                self.rbcd_graphs[starting_node_name]["destinations"].append(
                    ending_node_name
                )
            if ending_node_name not in ending_nodes_names_distinct:
                self.rbcd_nb_end_nodes += 1
                ending_nodes_names_distinct.append(ending_node_name)




        for object_name in list(self.rbcd_graphs.keys()):

            self.createGraphPage(
                self.arguments.cache_prefix,
                object_name + "_rbcd_graph",
                "Attack paths of accounts that can RBCD",
                "graph_list_objects_rbcd",
                self.rbcd_graphs[object_name]["paths"],
                domain,
            )

            sub_page = Page(
                self.arguments.cache_prefix,
                "graph_list_objects_rbcd_to_da_from_" + object_name,
                "Paths to DA from rbcd targets",
                "graph_path_objects_to_da",
            )
            sub_grid = Grid("RBCD targets that have a path to DA from " + object_name)
            sub_grid_data = []

            for destination in self.rbcd_graphs[object_name]["destinations"]:

                sub_tmp_data = {}
                sub_tmp_data["Name"] = destination
                if destination in list(self.rbcd_to_da_graphs.keys()):
                    self.rbcd_graphs[object_name]["nb_paths_to_da"] += len(
                        self.rbcd_to_da_graphs[destination]["paths"]
                    )
                    sortClass = str(len(self.rbcd_to_da_graphs[destination]["paths"])).zfill(6)
                    sub_tmp_data["Paths to DA"] = grid_data_stringify({
                        "value": f'{len(self.rbcd_to_da_graphs[destination]["paths"])} path{"s" if len(self.rbcd_to_da_graphs[destination]["paths"]) > 1 else ""} to <i class="bi bi-gem"></i> DA',
                        "link": "rbcd_target_%s_paths_to_da.html" % destination,
                        "before_link": f'<i class="bi bi-shuffle {sortClass}"></i>'
                    })
                else:
                    sub_tmp_data["Paths to DA"] = "-"
                sub_grid_data.append(sub_tmp_data)
            sub_headers = ["Name", "Paths to DA"]
            sub_grid.setheaders(sub_headers)
            sub_grid.setData(sub_grid_data)
            sub_page.addComponent(sub_grid)
            sub_page.render()

        page = Page(
            self.arguments.cache_prefix,
            "graph_list_objects_rbcd",
            "Users able to RBCD attack",
            "graph_list_objects_rbcd",
        )
        grid = Grid("Objects that can perform an RBCD attack on computers")
        grid_data = []

        if len(list(self.rbcd_graphs.keys())) != 0:
            for object_name in list(self.rbcd_graphs.keys()):
                tmp_data = {}
                tmp_data["Domain"] = '<i class="bi bi-globe2"></i> ' + self.rbcd_graphs[object_name]["domain"]
                tmp_data["Name"] = '<i class="bi bi-person-fill"></i> ' + object_name
                sortClass1 = str(len(self.rbcd_graphs[object_name]["paths"])).zfill(6)
                tmp_data["Paths to targets"] = grid_data_stringify({
                    "value": f'{len(self.rbcd_graphs[object_name]["paths"])} path{"s" if len(self.rbcd_graphs[object_name]["paths"]) > 1 else ""} to <i class="bi bi-bullseye"></i> targets',
                    "link": "%s_rbcd_graph.html" % object_name,
                    "before_link": f'<i class="bi bi-shuffle {sortClass1}"></i>'
                })
                if self.rbcd_graphs[object_name]["nb_paths_to_da"] > 0:
                    sortClass2 = str(self.rbcd_graphs[object_name]["nb_paths_to_da"]).zfill(6)
                    tmp_data["Paths to DA"] = grid_data_stringify({
                        "value": f'{self.rbcd_graphs[object_name]["nb_paths_to_da"]} path{"s" if self.rbcd_graphs[object_name]["nb_paths_to_da"] > 1 else ""} to <i class="bi bi-gem"></i> DA',
                        "link": "graph_list_objects_rbcd_to_da_from_%s.html" % object_name,
                        "before_link": f'<i class="bi bi-shuffle {sortClass2}"></i>'
                    })
                else:
                    tmp_data["Paths to DA"] = "-"
                grid_data.append(tmp_data)
            headers = ["Domain", "Name", "Paths to targets", "Paths to DA"]
            grid.setheaders(headers)
            grid.setData(grid_data)
            page.addComponent(grid)
            page.render()

    def generatePathToSDHolder(self, domain):
        if self.vuln_permissions_adminsdholder is None:
            self.vuln_permissions_adminsdholder = []
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "vuln_permissions_adminsdholder",
            "Objects with path to the adminSDHolder object",
            "vuln_permissions_adminsdholder",
            self.vuln_permissions_adminsdholder,
            domain,
        )

    def generatePasswordNotRequiredPage(self):
        if self.users_password_not_required is None:
            self.users_password_not_required = []
            return
        page = Page(
            self.arguments.cache_prefix,
            "users_password_not_required",
            "Users that can bypass your password policy",
            "users_password_not_required",
        )
        grid_data=[]
        for dic in self.users_password_not_required:
            tmp_data = {}
            tmp_data["Domain"] = '<i class="bi bi-globe2"></i> ' + dic["domain"]
            tmp_data["User"] = '<i class="bi bi-person-fill"></i> ' + dic["user"]
            tmp_data["Password last change"] = days_format(dic["pwdlastset"])
            tmp_data["Last logon"] = days_format(dic["lastlogon"])
            grid_data.append(tmp_data)
        grid = Grid("Users that can bypass your password policy")
        grid.setheaders(["Domain", "User", "Password last change","Last logon"])
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()


    def genGroupAnomalyAcl(self, domain):

        if self.group_anomaly_acl is None:
            return

        formated_data_details = []
        formated_data = {}
        group_anomaly_acl_extract = []

        for k in range(len(self.group_anomaly_acl)):
            if formated_data.get(self.group_anomaly_acl[k]["g.name"]) and formated_data[self.group_anomaly_acl[k]["g.name"]]["type"] == self.group_anomaly_acl[k]["type(r2)"]:
                formated_data[self.group_anomaly_acl[k]["g.name"]]["targets"].append(self.group_anomaly_acl[k]["n.name"])
            else:
                formated_data[self.group_anomaly_acl[k]["g.name"]] = {
                    "name": self.group_anomaly_acl[k]["g.name"],
                    "type": self.group_anomaly_acl[k]["type(r2)"],
                    "members_count": self.group_anomaly_acl[k]["g.members_count"],
                    "targets": [self.group_anomaly_acl[k]["n.name"]]
                }

        for name_instance in formated_data:

            formated_data_details = []
            interest = 0
            for k in formated_data[name_instance]["targets"]:
                tmp_dict = {}
                if k in domain.admin_list:
                    tmp_dict["targets"] = '<i class="bi bi-gem" title="This user is domain admin"></i> ' + k
                    interest = max(3, interest)
                else:
                    tmp_dict["targets"] = k

                tmp_dict["Computers admin"] = "-"
                tmp_dict["Path to DA"] = "-"
                for u in self.users_admin_of_computers:
                    if k in u["User"]:
                        if "No data to show" not in u['List of computers']:
                            count = int(u['List of computers'][u['List of computers'].find("'>", 55)+2:u['List of computers'].find('Computer')].strip())
                            tmp_dict["Computers admin"] = grid_data_stringify({
                                "link": u['Path to computers'].split("href='", 1)[-1].split("'", 1)[0],
                                "value": f"Admin of {count} computer{'s' if count > 1 else ''}",
                                "before_link": f"<i class='bi bi-pc-display-horizontal {str(count).zfill(6)}'></i>"
                            })
                            interest = max(1, interest)
                        tmp_dict["Path to DA"] = u['Path to DA']
                        if tmp_dict["Path to DA"] != "-":
                            interest = max(2, interest)
                        break

                formated_data_details.append(tmp_dict)

            page = Page(
            self.arguments.cache_prefix, f"group_anomaly_acl_details_{name_instance}", "Group Anomaly ACL Details", "group_anomaly_acl"
        )


            grid = Grid("Target Details")

            grid.setheaders(["targets", "Computers admin", "Path to DA"])
            grid.setData(formated_data_details)
            page.addComponent(grid)
            page.render()

            group_anomaly_acl_extract.append(
                {
                    "name": '<i class="bi bi-people-fill"></i> ' + name_instance,
                    "type": formated_data[name_instance]["type"],
                    "members count": f'<i class="{str(formated_data[name_instance]["members_count"]).zfill(6)} bi bi-people-fill"></i> ' + str(formated_data[name_instance]["members_count"]),
                    "targets count": grid_data_stringify({
                        "link": f"group_anomaly_acl_details_{name_instance}.html",
                        "value": f"{len(formated_data[name_instance]['targets'])} target{'s' if len(formated_data[name_instance]['targets']) > 1 else ''} <i class='bi bi-box-arrow-up-right' aria-hidden='true'></i>",
                        "before_link": f"<i class='<i bi bi-bullseye {str(len(formated_data[name_instance]['targets'])).zfill(6)}'></i> "
                    }),
                    "interest": f"<span class='{interest}'></span><i class='bi bi-star-fill'></i>"*interest + "<i class='bi bi-star'></i>"*(3-interest)
                }
            )

        page = Page(
            self.arguments.cache_prefix, "group_anomaly_acl", "Group Anomaly ACL", "group_anomaly_acl"
        )
        grid = Grid("group_anomaly_acl")
        grid.setheaders(["name", "type", "members count", "targets count", "interest"])

        grid.setData(group_anomaly_acl_extract)
        page.addComponent(grid)
        page.render()

        return len([*formated_data])

    def genHasSIDHistory(self):
        page = Page(
            self.arguments.cache_prefix,
            "has_sid_history",
            "Objects who can abuse SID History",
            "has_sid_history",
        )
        grid = Grid("Objects who can abuse SID History")
        headers = ["Has SID History", "Admin of", "Target", "admin of"]

        # add icons for type of object
        star_icon = "<i class='bi bi-star-fill' style='color:gold; text-shadow: 0px 0px 1px black, 0px 0px 1px black, 0px 0px 1px black, 0px 0px 1px black;' title='This SID history allows for access to more computers'></i>"
        for row in self.has_sid_history:
            # add admin of columns
            row['Admin of'] = "-"
            row['admin of'] = "-"
            target_count = 0
            origin_count = 0
            for u in self.users_admin_of_computers:
                if row['Has SID History'] in u['User']:
                    row['Admin of'] = u['List of computers']
                    origin_count = int(u['List of computers'][u['List of computers'].find("'>", 55)+2:u['List of computers'].find('Computer')].strip())
                if row['Target'] in u['User']:
                    row['admin of'] = u['List of computers']
                    target_count = int(u['List of computers'][u['List of computers'].find("'>", 55)+2:u['List of computers'].find('Computer')].strip())

            # add user icons
            if row['Type_a'] == "User":
                row['Has SID History'] = "<i class='bi bi-person-fill' title='User'></i> " + row['Has SID History']
            elif row['Type_a'] == "Group":
                row['Has SID History'] = "<i class='bi bi-people-fill' title='Group'></i> " + row['Has SID History']
            else:
                row['Has SID History'] = "<i class='bi bi-question-circle-fill' title='Unknown'></i> " + row['Has SID History']
            if row['Type_b'] == "User":
                row['Target'] = "<i class='bi bi-person-fill' title='User'></i> " + row['Target']
            elif row['Type_b'] == "Group":
                row['Target'] = "<i class='bi bi-people-fill' title='Group'></i> " + row['Target']
            else:
                row['Target'] = "<i class='bi bi-question-circle-fill' title='Unknown'></i> " + row['Target']

            # add star icon
            if target_count > origin_count:
                row['Has SID History'] = star_icon + " " + row['Has SID History']
                row['Target'] = star_icon + " " + row['Target']



        grid.setheaders(headers)
        grid.setData(self.has_sid_history)

        page.addComponent(grid)
        page.render()
