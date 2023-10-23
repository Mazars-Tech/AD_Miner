import json
import time
import re
from urllib.parse import quote

from ad_miner.sources.modules import generic_computing
from ad_miner.sources.modules import generic_formating
from ad_miner.sources.modules import logger
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.utils import timer_format, days_format, grid_data_stringify


class Computers:
    def __init__(self, arguments, neo4j, domain):
        self.arguments = arguments
        self.neo4j = neo4j
        self.domain = domain
        self.start = time.time()
        logger.print_debug("Computing Computers objects")

        self.list_total_computers = neo4j.all_requests["nb_computers"]["result"]
        self.list_computers_admin_computers = neo4j.all_requests[
            "computers_admin_on_computers"
        ]["result"]
        self.list_computers_os_obsolete = self.manageComputersOs(
            neo4j.all_requests["os"]["result"]
        )
        # print(neo4j.all_requests['os']['result'][0])
        # print(self.list_computers_os_obsolete[0])
        self.list_computers_unconstrained_delegations = neo4j.all_requests[
            "nb_computer_unconstrained_delegations"
        ]["result"]
        self.list_users_unconstrained_delegations = neo4j.all_requests[
            "nb_users_unconstrained_delegations"
        ]["result"]
        self.users_constrained_delegations = neo4j.all_requests[
            "users_constrained_delegations"
        ]["result"]
        self.computer_administrable_per_users = generic_computing.getCountValueFromKey(
            neo4j.all_requests["users_admin_on_computers"]["result"], "computer"
        )
        self.computer_administrable_per_users_list = generic_computing.getListAdminTo(
            neo4j.all_requests["users_admin_on_computers"]["result"], "computer", "user"
        )
        if (
            self.computer_administrable_per_users is not None
            and self.computer_administrable_per_users != {}
        ):
            self.computer_with_most_user_admin = self.computer_administrable_per_users[
                list(self.computer_administrable_per_users.keys())[0]
            ]
        else:
            self.computer_with_most_user_admin = []
        self.computers_members_high_privilege = neo4j.all_requests[
            "computers_members_high_privilege"
        ]["result"]
        self.computers_members_high_privilege_uniq = self.findUniqComputers(
            neo4j.all_requests["computers_members_high_privilege"]["result"]
        )
        self.computers_nb_has_laps = neo4j.all_requests["nb_computers_laps"]["result"]

        self.computers_non_dc_unconstrained_delegations = neo4j.all_requests[
            "nb_computer_unconstrained_delegations"
        ]["result"]
        self.users_non_dc_unconstrained_delegations = neo4j.all_requests[
            "nb_users_unconstrained_delegations"
        ]["result"]
        self.count_computers_admins = 0
        self.count_computers_admins_target = 0
        self.dropdown_computers_os_obsolete = []
        if self.users_constrained_delegations is not None:
            self.users_constrained_delegations = dict(
                sorted(
                    self.parseConstrainedData(
                        self.users_constrained_delegations
                    ).items(),
                    key=lambda x: len(x[1]),
                    reverse=True,
                )
            )

        self.users_nb_domain_admins = neo4j.all_requests["nb_domain_admins"]["result"]
        self.admin_list = []
        for admin in self.users_nb_domain_admins:
            self.admin_list.append(admin["name"])

        self.computers_adcs = neo4j.all_requests["set_is_adcs"]["result"]
        self.objects_to_adcs = neo4j.all_requests["objects_to_adcs"]["result"]

        # Generate all the computer-related pages
        self.generateComputersListPage()
        self.generateADCSListPage()
        self.genObsoleteOSPage()
        self.genNonDCWithUnconstrainedPage()
        self.genDCUsersWithUnconstrainedPage()
        self.genUsersConstrainedPage()
        self.genComputersAdminOfPages()
        self.genComputersWithMostAdminsPage()
        self.genComputersAdministrablePage()
        self.genHighPrivilegeGroupComputersPage()
        self.genComputersWithLAPSPage()
        self.genPathToADCS()

        self.generate_stat_laps()


        if self.list_computers_os_obsolete is not None:
            count_computers_os_obsolete_per_domain = (
                generic_computing.getCountValueFromKey(
                    self.list_computers_os_obsolete, "Operating system"
                )
            )
            self.dropdown_computers_os_obsolete = list(
                map(
                    lambda x: [x, count_computers_os_obsolete_per_domain[x]],
                    count_computers_os_obsolete_per_domain,
                )
            )

        logger.print_time(timer_format(time.time() - self.start))

    def generate_stat_laps(self):
        if len(self.list_total_computers) != 0:
            stat_LAPS = round(
                100
                * len(
                    [
                        computer_has_laps
                        for computer_has_laps in self.computers_nb_has_laps
                        if "Enabled" in computer_has_laps["LAPS"]
                    ]
                )
                / (len(self.computers_nb_has_laps) + 0.001)
            )

        else:
            stat_LAPS = 0
        self.stat_laps = 100 - stat_LAPS
        return self

    # Create computers list page
    def generateComputersListPage(self):
        if self.list_total_computers is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "computers",
            "List of all computers",
            "computers",
        )
        grid = Grid("Computers")
        data = []
        for computer in self.list_total_computers:
            # Check if computer is ghost computer
            if computer["ghost"]:
                name = '<svg height="15px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><path d="M40.1 467.1l-11.2 9c-3.2 2.5-7.1 3.9-11.1 3.9C8 480 0 472 0 462.2V192C0 86 86 0 192 0S384 86 384 192V462.2c0 9.8-8 17.8-17.8 17.8c-4 0-7.9-1.4-11.1-3.9l-11.2-9c-13.4-10.7-32.8-9-44.1 3.9L269.3 506c-3.3 3.8-8.2 6-13.3 6s-9.9-2.2-13.3-6l-26.6-30.5c-12.7-14.6-35.4-14.6-48.2 0L141.3 506c-3.3 3.8-8.2 6-13.3 6s-9.9-2.2-13.3-6L84.2 471c-11.3-12.9-30.7-14.6-44.1-3.9zM160 192a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zm96 32a32 32 0 1 0 0-64 32 32 0 1 0 0 64z"/></svg> ' + computer["name"]
            else:
                name = '<i class="bi bi-pc-display"></i> ' + computer["name"]
            # OS
            if computer["os"]:
                os = computer["os"]
                if "windows" in computer["os"].lower():
                    os = '<i class="bi bi-windows"></i> ' + os
                elif "mac" in computer["os"].lower():
                    os = '<i class="bi bi-apple"></i> ' + os
                else:
                    os = '<i class="bi bi-terminal-fill"></i> ' + os
            else:
                os = "Unknown"
            formated_computer = {"domain": '<i class="bi bi-globe2"></i> ' + computer["domain"], "name": name, "operating system": os}
            data.append(formated_computer)
        grid.setheaders(["domain", "name", "operating system"])
        grid.setData(data)
        page.addComponent(grid)
        page.render()

    # Create ADCS list page
    def generateADCSListPage(self):
        if self.computers_adcs is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "adcs",
            "List of all ADCS servers",
            "adcs",
        )
        grid = Grid("ADCS servers")
        grid.setheaders(["domain", "name"])
        for adcs in self.computers_adcs:
            adcs["domain"] = '<i class="bi bi-globe2"></i> ' + adcs["domain"]
            adcs["name"] = '<i class="bi bi-server"></i> ' + adcs["name"]
        grid.setData(self.computers_adcs)
        page.addComponent(grid)
        page.render()

    # Create obsolete os page and compute os obsolete dropdown
    def genObsoleteOSPage(self):
        if self.list_computers_os_obsolete is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "computers_os_obsolete",
            "Obsolete operating systems",
            "obsolete_os",
        )
        grid = Grid("Computers obsolete operating systems")
        cleaned_data = []
        for computer in self.list_computers_os_obsolete:
            if computer["Last logon in days"] < 90:  # remove ghost computers
                computer["Domain"] = '<i class="bi bi-globe2"></i> ' + computer["Domain"]
                computer["Last logon"] = days_format(computer["Last logon in days"])
                if (
                    "2008" in computer["Operating system"]
                    or "2003" in computer["Operating system"]
                    or "2012" in computer["Operating system"]
                ):  # Add icons whether it's a computer or a server
                    computer["Operating system"] = '<i class="bi bi-server"></i> ' + computer["Operating system"]
                    computer["name"] = '<i class="bi bi-server"></i> ' + computer["name"]
                if (
                    "2000" in computer["Operating system"]
                    or "XP" in computer["Operating system"]
                    or "Windows 7" in computer["Operating system"]
                ):
                    computer["Operating system"] = '<i class="bi bi-pc-display"></i> ' + computer["Operating system"]
                    computer["name"] = '<i class="bi bi-pc-display"></i> ' + computer["name"]

                cleaned_data.append(computer)
        grid.setheaders(["Domain", "name", "Operating system", "Last logon"])
        grid.setData(cleaned_data)
        page.addComponent(grid)
        page.render()
        self.list_computers_os_obsolete = cleaned_data

    # Non DC computers with unconstrained delegations
    def genNonDCWithUnconstrainedPage(self):
        if self.list_computers_unconstrained_delegations is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "non-dc_with_unconstrained_delegations",
            "Non-DC with unconstrained delegations",
            "non-dc_with_unconstrained_delegations",
        )
        grid = Grid("Non-DC with unconstrained delegations")
        grid.setheaders(["domain", "name"])
        for d in self.computers_non_dc_unconstrained_delegations:
            d["domain"] = '<i class="bi bi-globe2"></i> ' + d["domain"]
            d["name"] = '<i class="bi bi-pc-display"></i> ' + d["name"]
        grid.setData(self.computers_non_dc_unconstrained_delegations)
        page.addComponent(grid)
        page.render()

    # Non DC users with unconstrained delegations
    def genDCUsersWithUnconstrainedPage(self):
        if (
            self.list_users_unconstrained_delegations is None
            or self.users_non_dc_unconstrained_delegations is None
        ):
            return
        page = Page(
            self.arguments.cache_prefix,
            "non-dc_users_with_unconstrained_delegations",
            "Non-DC users with unconstrained delegations",
            "non-dc_users_with_unconstrained_delegations",
        )
        grid = Grid("Non-DC users with unconstrained delegations")
        grid.setheaders(["domain", "name"])
        for d in self.users_non_dc_unconstrained_delegations:
            d["domain"] = '<i class="bi bi-globe2"></i> ' + d["domain"]
            d["name"] = '<i class="bi bi-person-fill"></i> ' + d["name"]
        grid.setData(self.users_non_dc_unconstrained_delegations)
        page.addComponent(grid)
        page.render()

    # Users with constrained delegations
    def genUsersConstrainedPage(self):
        if self.users_constrained_delegations is None:
            return
        headers = ["Users", "Number of computers", "Computers"]
        formated_data = generic_formating.formatGridValues3Columns(
            generic_formating.formatFor3Col(
                self.users_constrained_delegations, headers
            ),
            headers,
            "users_constrained_delegations",
        )
        page = Page(
            self.arguments.cache_prefix,
            "users_constrained_delegations",
            "Users with constrained delegations",
            "users_constrained_delegations",
        )
        grid = Grid("Users with constrained delegations")
        grid.setheaders(headers)
        grid.setData(json.dumps(formated_data))
        page.addComponent(grid)
        page.render()

    # Compute path to da from administrable computers pages
    def genComputersAdminOfPages(self):
        if self.list_computers_admin_computers is None:
            return
        computers_admin_to_count = generic_computing.getCountValueFromKey(
            self.list_computers_admin_computers, "source_computer"
        )
        self.count_computers_admins = len(computers_admin_to_count)
        computers_admin_to_count_target = generic_computing.getCountValueFromKey(
            self.list_computers_admin_computers, "target_computer"
        )
        self.count_computers_admins_target = len(computers_admin_to_count_target)
        computers_admin_to_list = generic_computing.getListAdminTo(
            self.list_computers_admin_computers, "source_computer", "target_computer"
        )
        self.computers_admin_data_grid = []
        for admin_computer, computers_list in computers_admin_to_list.items():
            if admin_computer is not None and computers_list is not None:
                num_path, nb_domains = self.domain.findAndCreatePathToDaFromComputersList(admin_computer, computers_list)
                sortClass1 = str(computers_admin_to_count[admin_computer]).zfill(6)
                sortClass2 = str(num_path).zfill(6)

                tmp_line = {
                    "Computer Admin": '<i class="bi bi-pc-display"></i> ' + admin_computer,
                    "Computers count": grid_data_stringify({
                        "value": f"{computers_admin_to_count[admin_computer]} computers",
                        "link": f"computer_admin_{quote(str(admin_computer))}.html",
                        "before_link": f"<i class='bi bi-pc-display {sortClass1}'></i>"
                    })
                }
                if num_path > 0:
                    tmp_line["Paths to domain admin"] = grid_data_stringify({
                            "value": f"{num_path} paths to DA ({nb_domains} domain{'s' if nb_domains>1 else ''} impacted) <i class='bi bi-box-arrow-up-right'></i>",
                            "link": f"computers_path_to_da_from_{quote(str(admin_computer))}.html",
                            "before_link": f"<i class='bi bi-shuffle {sortClass2}' aria-hidden='true'></i>"
                        })
                else:
                    tmp_line["Paths to domain admin"] = "-"

                self.computers_admin_data_grid.append(tmp_line)
        self.computers_admin_data_grid.sort(
            key=lambda x: x["Computers count"], reverse=True
        )

        # Compute page computers : numbers of administrable computers
        page = Page(
            self.arguments.cache_prefix,
            "computers_admin_of_computers",
            "Computers with administration rights on other computers",
            "computers_admin_of_computers",
        )
        grid = Grid("Computers admins of other computers")
        grid.setheaders(["Computer Admin", "Computers count", "Paths to domain admin"])
        grid.setData(json.dumps(self.computers_admin_data_grid))
        page.addComponent(grid)
        page.render()

        # Compute page for each computer who have admin computer
        for computer, values in computers_admin_to_list.items():
            if computer is not None:
                page = Page(
                    self.arguments.cache_prefix,
                    "computer_admin_" + computer,
                    "Admin of computer " + computer,
                    "computer_admin",
                )
                grid = Grid("List of computers where %s is admin" % (computer))
                grid.addheader(computer)
                computers_admin_to_list = generic_formating.formatGridValues1Columns(
                    values, grid.getHeaders()
                )

                grid.setData(computers_admin_to_list)
                page.addComponent(grid)
                page.render()
            else:
                print("Hey Houston, it's toto, and WE HAVE A PROBLEM")
                # List of computers with most users admin page (and if to handle empty cases)

    def genComputersWithMostAdminsPage(self):
        if self.computer_administrable_per_users is None:
            return
        icon = '<i class="bi bi-people-fill"></i>'
        formated_data = generic_formating.formatGridValues2Columns(
            self.computer_administrable_per_users,
            ["Computers", "Number of admins"],
            "computer_administrable",
            icon=icon,
        )
        page = Page(
            self.arguments.cache_prefix,
            "computers_users_admin",
            "Administrators of computers",
            "computers_users_admin",
        )
        grid = Grid("Computers with most users admin")
        grid.setheaders(["Computers", "Number of admins"])
        grid.setData(json.dumps(formated_data))
        page.addComponent(grid)
        page.render()

    # List of Administrable computers
    def genComputersAdministrablePage(self):
        if self.computer_administrable_per_users_list is None:
            return
        allValues = []
        for computer, values in self.computer_administrable_per_users_list.items():
            for v in values:
                allValues.append(
                    "<span class='administrable-by-%s'> %s </span>" % (computer, v)
                )
        page = Page(
            self.arguments.cache_prefix,
            "computer_administrable",
            "Administrable computers",
            "computer_administrable",
        )
        grid = Grid("Computers administrable")
        grid.addheader("TO CHANGE")
        users_admin_to_list = generic_formating.formatGridValues1Columns(
            allValues, grid.getHeaders()
        )
        grid.setData(users_admin_to_list)
        page.addComponent(grid)
        page.render()

    # Create highprivilege group computers member page
    def genHighPrivilegeGroupComputersPage(self):
        if self.computers_members_high_privilege is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "computers_members_high_privilege",
            "Computers' members with high privilege",
            "computers_members_high_privilege",
        )
        grid = Grid("List of computer admins")
        for d in self.computers_members_high_privilege:
            d["domain"] = '<i class="bi bi-globe2"></i> ' + d["domain"]
            d["computer"] = '<i class="bi bi-pc-display"></i> ' + d["computer"]
            d["group"] = '<i class="bi bi-people-fill"></i> ' + d["group"]
        grid.setheaders(["domain", "computer", "group"])
        grid.setData(self.computers_members_high_privilege)
        page.addComponent(grid)
        page.render()

    # List computer with LAPS
    def genComputersWithLAPSPage(self):
        if self.computers_nb_has_laps is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "computers_without_laps",
            "Computers' LAPS status",
            "laps_computer_list",
        )
        grid = Grid("Computers with LAPS")
        grid.setheaders(["domain", "name", "LAPS", "Last logon"])

        cleaned_data = []
        for computer in self.computers_nb_has_laps:
            # If value is None
            if not computer.get("lastLogon"):
                continue
            # Exclude ghost computers (last logon > 90 days)
            if (computer["lastLogon"] < 90):
                computer["domain"] = '<i class="bi bi-globe2"></i> ' + computer["domain"]
                computer["Last logon"] = days_format(computer["lastLogon"])
                computer["name"] = '<i class="bi bi-pc-display"></i> ' + computer["name"]
                if computer["LAPS"] == "false":
                    computer["LAPS"] = '<i class="bi bi-unlock-fill text-danger"></i> Disabled'
                else:
                    computer["LAPS"] = '<i class="bi bi-lock-fill text-success"></i> Enabled'
                cleaned_data.append(computer)
        self.computers_nb_has_laps = cleaned_data
        if len(cleaned_data):
            grid.setData(cleaned_data)
        page.addComponent(grid)
        page.render()

    def genPathToADCS(self):
        if self.objects_to_adcs is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "objects_to_adcs",
            "Compromisable ADCS Servers",
            "objects_to_adcs",
        )
        grid = Grid("Objects to ADCS servers")
        grid.setheaders(["Domain", "Name", "Path to ADCS"])

        self.ADCS_path_sorted = {}
        self.ADCS_entry_point = []

        for path in self.objects_to_adcs:
            self.ADCS_entry_point.append(path.nodes[0].name)
            try:
                self.ADCS_path_sorted[path.nodes[-1].name].append(path)
            except KeyError:
                self.ADCS_path_sorted[path.nodes[-1].name] = [path]

        self.ADCS_entry_point = list(set(self.ADCS_entry_point))

        cleaned_data = []

        for key,paths in self.ADCS_path_sorted.items():
            tmp_data = {}
            tmp_data["Domain"] = '<i class="bi bi-globe2"></i> ' + paths[0].nodes[-1].domain
            tmp_data["Name"] = '<i class="bi bi-server"></i> ' + key
            nb_path_to_adcs = len(paths)
            sortClass = str(nb_path_to_adcs).zfill(6)
            tmp_data["Path to ADCS"] = grid_data_stringify({
                    "link": "path_to_adcs_%s.html" % quote(str(key)),
                    "value": f"{nb_path_to_adcs} paths to ADCS <i class='bi bi-box-arrow-up-right'></i>",
                    "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                })
            cleaned_data.append(tmp_data)

            graph_page = Page(
                self.arguments.cache_prefix,
                "path_to_adcs_%s" % key,
                "Path to ADCS through " + key,
                "path_to_adcs",
            )
            graph = Graph()
            graph.setPaths(paths)
            graph_page.addComponent(graph)
            graph_page.render()

        grid.setData(cleaned_data)
        page.addComponent(grid)
        page.render()

    # List of users with RDP access
    @staticmethod
    def parseConstrainedData(list_of_dict):
        final_dict = {}
        for dict in list_of_dict:
            if dict["name"] in final_dict.keys():
                final_dict[dict["name"]] += [dict["computer"]]
            else:
                final_dict[dict["name"]] = [dict["computer"]]
        return final_dict

    # Create os obsolete list
    @staticmethod
    def manageComputersOs(computer_list):
        if computer_list is None:
            return None
        computers_os_obsolete = []
        obsolete_os_list = [
            "Windows XP",
            "Windows 7",
            "Windows 2000",
            "Windows 2003",
            "Windows 2008",
            "Windows 2008R2",
            "Windows 2012",
            "Windows 2012R2"
        ]

        for line in computer_list:
            os = line["os"]
            if "Windows" in line["os"] or "windows" in line["os"]:
                os = os.replace("\xa0", " ")
                os = os.replace("®", "")
                os = os.replace(" Server", "")
                os = os.replace(" Storage", "")
                os = os.replace(" 2008 R2", " 2008R2")
                os = os.replace(" 2012 R2", " 2012R2")
                ver = re.match(r"^Windows ([.a-zA-Z0-9]+)\s", os, re.M | re.I)
                if ver:
                    os = "Windows " + ver.group(1)
            else:
                os = os[0:16] + "[..]"

            # Cleaner way to do a try/except for dictionaries is to use get() :
            lastLogon = line.get("lastLogon", "Not specified")
            final_line = {
                "Domain": line["domain"],
                "name": line["name"],
                "Operating system": os,
                "Last logon in days": lastLogon,
            }

            if os in obsolete_os_list:
                computers_os_obsolete.append(final_line)
        return computers_os_obsolete

    @staticmethod
    def findUniqComputers(computers_members_high_privilege):
        if computers_members_high_privilege is None:
            return None
        computers_list = []

        for line in computers_members_high_privilege:
            if line["computer"] not in computers_list:
                computers_list.append(line["computer"])
        return computers_list
