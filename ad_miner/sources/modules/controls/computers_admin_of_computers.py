from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.utils import grid_data_stringify
from ad_miner.sources.modules import generic_formating, generic_computing
from ad_miner.sources.modules.common_analysis import (
    findAndCreatePathToDaFromComputersList,
    hasPathToDA,
)
import json
from urllib.parse import quote


@register_control
class computers_admin_of_computers(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "permissions"
        self.control_key = "computers_admin_of_computers"

        self.title = "Computers admin of other computers"
        self.description = "Some machine accounts have administration privileges over other computers accounts."
        self.risk = "This controls reveals computers (i.e., the computer machine account) that have local administration privileges over other computers. This weakness can be leveraged by any domain user to relay coerced connections and eventually obtain local administration privileges over target computer. Coerced authentication can be triggered using numerous techniques such as EFSRPC (e.g., using PetitPotam). This attack requires network access over target machine and that SMB signing be not required (which is default)."
        self.poa = "Microsoft's primary goal is not to mitigate coerced-authentication based attacks. Indeed, the general recommendation is to require SMB signing and also to ensure that unnecessarry relayable services (e.g., SMB, RPC, etc.) be filtered to users."

        self.dico_description_computer_admin = {
            "description": "List of computers admin of other machines.",
            "risk": "This controls reveals computers (i.e., the computer machine account) that have local administration privileges over other computers. This weakness can be leveraged by any domain user to relay coerced connections and eventually obtain local administration privileges over target computer. Coerced authentication can be triggered using numerous techniques such as EFSRPC (e.g., using PetitPotam). This attack requires network access over target machine and that SMB signing be not required (which is default).",
            "poa": "Microsoft's primary goal is not to mitigate coerced-authentication based attacks. Indeed, the general recommendation is to require SMB signing and also to ensure that unnecessarry relayable services (e.g., SMB, RPC, etc.) be filtered to users.",
        }

        self.list_computers_admin_computers = requests_results[
            "computers_admin_on_computers"
        ]

    def run(self):
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
                num_path, nb_domains = findAndCreatePathToDaFromComputersList(
                    self.requests_results,
                    self.arguments,
                    admin_computer,
                    computers_list,
                )
                sortClass1 = str(computers_admin_to_count[admin_computer]).zfill(6)
                sortClass2 = str(num_path).zfill(6)

                tmp_line = {
                    "Computer Admin": '<i class="bi bi-pc-display"></i> '
                    + admin_computer,
                    "Computers count": grid_data_stringify(
                        {
                            "value": f"{computers_admin_to_count[admin_computer]} computers",
                            "link": f"computer_admin_{quote(str(admin_computer))}.html",
                            "before_link": f"<i class='bi bi-pc-display {sortClass1}'></i>",
                        }
                    ),
                }
                if num_path > 0:
                    tmp_line["Paths to domain admin"] = grid_data_stringify(
                        {
                            "value": f"{num_path} paths to DA ({nb_domains} domain{'s' if nb_domains>1 else ''} impacted)",
                            "link": f"computers_path_to_da_from_{quote(str(admin_computer))}.html",
                            "before_link": f"<i class='bi bi-shuffle {sortClass2}' aria-hidden='true'></i>",
                        }
                    )
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
            self.get_dico_description(),
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
                    self.dico_description_computer_admin,
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
                print("Bug")
                # List of computers with most users admin page (and if to handle empty cases)

        self.data = self.count_computers_admins if self.count_computers_admins else 0

        # TODO define the sentence that will be displayed in the 'smolcard' view and in the center of the mainpage
        self.name_description = f"{self.count_computers_admins} computers admin of {self.count_computers_admins_target} computers"

    def get_rating(self) -> int:
        return hasPathToDA(self.list_computers_admin_computers)
