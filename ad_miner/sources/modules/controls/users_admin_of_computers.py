from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control
from ad_miner.sources.modules import logger
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules import generic_computing

from ad_miner.sources.modules.utils import grid_data_stringify
from ad_miner.sources.modules.common_analysis import (
    findAndCreatePathToDaFromUsersList,
    hasPathToDA,
    percentage_superior,
    days_format,
)

import json
from urllib.parse import quote
from tqdm import tqdm


@register_control
class users_admin_of_computers(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "permissions"
        self.control_key = "users_admin_of_computers"

        self.title = "Users with local admin privileges"
        self.description = "Users have administration rights over machines, creating potential compromission paths."
        self.risk = "You should watch out for accounts who are admin of too many computers or users who should not be admin at all. Wrongfully configured administration privileges are a big vector of vertical and lateral movement."
        self.poa = "Review this list to ensure admin privilege are effectively provided on a need to know basis."

        self.description_users_to_computer = {
            "description": "Path of users who have direct or indirect administration privilege on computers",
            "interpretation": "",
            "risk": "Inadequate administration rights on computers can lead to easy privilege escalation for an attacker. With a privileged account, it is possible to perform local memory looting to find credentials for example.",
            "poa": "Only a handful of accounts should have administrator privilege on computers to perform some maintenance actions. No normal user should be admin of any computer, not even its own.",
        }

        self.users_admin_computer = requests_results["users_admin_on_computers"]
        self.users_kerberoastable_users = requests_results["nb_kerberoastable_accounts"]
        self.users_pwd_not_changed_since = requests_results["password_last_change"]
        self.get_users_linked_admin_group = requests_results[
            "get_users_linked_admin_group"
        ]
        self.get_groups_linked_admin_group = requests_results[
            "get_groups_linked_admin_group"
        ]
        self.get_computers_linked_admin_group = requests_results[
            "get_computers_linked_admin_group"
        ]
        self.get_users_direct_admin = requests_results["get_users_direct_admin"]
        self.admin_list = requests_results["admin_list"]
        self.users = requests_results["nb_enabled_accounts"]
        self.users_to_computer_admin = {}

        self.users_admin_computer_count = generic_computing.getCountValueFromKey(
            self.users_admin_computer, "user"
        )
        self.users_admin_computer_list = generic_computing.getListAdminTo(
            self.users_admin_computer, "user", "computer"
        )

    def run(self):

        # Several requests are needed for this function, therefore we fail if there is one missing, and we print the issue
        fail = []
        if self.users_admin_computer_list is None:
            fail.append("users_admin_computer_list")

        if self.users_kerberoastable_users is None:
            fail.append("users_kerberoastable_users")

        if self.users_pwd_not_changed_since is None:
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

        def generateGraphPathToAdmin(self):
            data = []
            for couple in self.get_users_linked_admin_group:
                u = couple["u"]
                g = couple["gg"]

                start = Node(
                    couple["idu"], "User", u["name"], u["domain"], None, "MemberOf"
                )
                end = Node(couple["idg"], "Group", g["name"], g["domain"], None, "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "MemberOf"
                # )

                path = Path([start, end])
                data.append(path)
                self.users_to_computer_admin[u["name"]] = couple["idu"]

            for couple in self.get_groups_linked_admin_group:
                g = couple["g"]
                gg = couple["gg"]

                start = Node(
                    couple["idg"], "Group", g["name"], g["domain"], None, "MemberOf"
                )
                end = Node(couple["idgg"], "Group", gg["name"], gg["domain"], None, "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "MemberOf"
                # )

                path = Path([start, end])
                data.append(path)

            for couple in self.get_computers_linked_admin_group:
                g = couple["g"]
                c = couple["c"]

                start = Node(
                    couple["idg"], "Group", g["name"], g["domain"], None, "AdminTo"
                )
                end = Node(couple["idc"], "Computer", c["name"], c["domain"], None, "")

                # rel = Relation(
                #     int(str(start.id) + "00" + str(end.id)), [start, end], "AdminTo"
                # )

                path = Path([start, end])
                data.append(path)

            for couple in self.get_users_direct_admin:
                g = couple["g"]
                c = couple["c"]

                start = Node(
                    couple["idg"], "User", g["name"], g["domain"], None, "AdminTo"
                )
                end = Node(couple["idc"], "Computer", c["name"], c["domain"], None, "")

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
                self.description_users_to_computer,
            )
            graph = Graph()
            graph.setPaths(data)

            graph.addGhostComputers(self.requests_results["dico_ghost_computer"])
            graph.addGhostUsers(self.requests_results["dico_ghost_user"])
            graph.addDCComputers(self.requests_results["dico_dc_computer"])
            graph.addUserDA(self.requests_results["dico_user_da"])
            graph.addGroupDA(self.requests_results["dico_da_group"])

            page.addComponent(graph)
            page.render()

        def check_kerberoastable(account):
            for elem in self.users_kerberoastable_users:
                if elem["name"] == account:
                    return "<i class='bi bi-ticket-perforated-fill' style='color: #b00404;' title='This account is vulnerable to Kerberoasting'></i> YES"
            return "-"

        def get_last_pass_change(account):
            for elem in self.users_pwd_not_changed_since:
                if elem["user"] == account:
                    return days_format(elem["days"])
            return "<i class='bi bi-calendar3'></i> Unknown"

        generateGraphPathToAdmin(self)

        tmp_rslt = []
        for key in tqdm(self.users_admin_computer_list.keys()):
            partDict = {}
            partDict[headers[0]] = key

            partDict[headers[1]] = check_kerberoastable(key)
            partDict[headers[2]] = get_last_pass_change(key)

            partDict[headers[3]] = self.users_admin_computer_list[key]
            try:  # Case when node is not present in graph
                partDict[headers[4]] = grid_data_stringify(
                    {
                        "link": f"users_to_computers.html?node={quote(str(self.users_to_computer_admin[key]))}",
                        "value": "Path to computers",
                        "before_link": f"<i class='bi bi-sign-turn-right' aria-hidden='true'></i>",
                    }
                )
            except KeyError:
                partDict[headers[4]] = "No path to show"

            nb_path_to_da, nb_domain = findAndCreatePathToDaFromUsersList(
                self.requests_results, self.arguments, key, partDict[headers[3]]
            )

            if nb_path_to_da > 0:
                sortClass = str(nb_path_to_da).zfill(6)
                partDict[headers[5]] = grid_data_stringify(
                    {
                        "link": "users_path_to_da_from_%s.html" % quote(str(key)),
                        "value": f" {nb_path_to_da} path{'s' if nb_path_to_da > 1 else ''} to DA ({nb_domain} domain{'s' if nb_domain > 1 else ''})",
                        "before_link": f"<i class='bi bi-sign-turn-right-fill {sortClass}' style='color:#b00404;' aria-hidden='true'></i>",
                    }
                )
            else:
                partDict[headers[5]] = "-"
            tmp_rslt.append(partDict)

        # This loop should return nothing, just in case
        for key in self.users_to_computer_admin.keys():
            if key not in self.users_admin_computer_list.keys():
                partDict = {}
                partDict[headers[0]] = key

                partDict[headers[1]] = check_kerberoastable(key)
                partDict[headers[2]] = get_last_pass_change(key)

                partDict[headers[3]] = "No data to show"
                try:  # Case when node is not present in graph
                    partDict[headers[4]] = grid_data_stringify(
                        {
                            "link": f"users_to_computers.html?node={quote(str(self.users_to_computer_admin[key]))}",
                            "value": "Path to computers",
                            "before_link": f"<i class='bi bi-sign-turn-right' aria-hidden='true'></i>",
                        }
                    )
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
                    partDict[headers[5]] = grid_data_stringify(
                        {
                            "link": "users_path_to_da_from_%s.html" % quote(str(key)),
                            "value": f" {nb_path_to_da} path{'s' if nb_path_to_da > 1 else ''} to DA ({nb_domain} domain{'s' if nb_domain > 1 else ''})",
                            "before_link": f"<i class='bi bi-sign-turn-right-fill {sortClass}' style='color:#b00404;' aria-hidden='true'></i>",
                        }
                    )
                else:
                    partDict[headers[5]] = "-"
                tmp_rslt.append(partDict)

        formated_data = []
        formated_data_details = []
        for dict in tmp_rslt:
            if dict[headers[3]] != "No data to show":
                sortClass = str(len(dict[headers[3]])).zfill(
                    6
                )  # used to make the sorting feature work with icons
                data_header_computer = grid_data_stringify(
                    {
                        "link": "%s.html?parameter=%s"
                        % (
                            "users_admin_of_computers_details",
                            quote(str(dict[headers[0]])),
                        ),
                        "value": f" {len(dict[headers[3]])} Computer{'s' if len(dict[headers[3]]) > 1 else ''}",
                        "before_link": f"<i class='bi bi-hdd-network {sortClass}'></i>",
                    }
                )
                formated_data_details.append(
                    {
                        headers_details[0]: dict[headers[0]],
                        headers_details[1]: dict[headers[3]],
                    }
                )
            if dict[headers[0]] in self.admin_list:
                formated_data.append(
                    {
                        headers[
                            0
                        ]: '<i class="bi bi-gem" title="This user is domain admin"></i> '
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
                        headers[0]: '<i class="bi bi-person-fill"></i> '
                        + dict[headers[0]],
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
            self.get_dico_description(),
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
            self.get_dico_description(),
        )
        grid = Grid("Users admins of")
        if len(self.users_admin_computer_count) > 0:
            if formated_data_details != [] and formated_data_details is not None:
                grid.setheaders(headers)
                grid.setData(json.dumps(formated_data_details))
        page.addComponent(grid)
        page.render()

        self.data = (
            len(self.users_admin_computer_count)
            if self.users_admin_computer_count
            else 0
        )

        self.name_description = f"{self.data} users with local admin privileges"

    def get_rating(self) -> int:
        return min(
            hasPathToDA(self.users_admin_computer),
            percentage_superior(
                self.users_admin_computer, self.users, criticity=2, percentage=0.5
            ),
        )
