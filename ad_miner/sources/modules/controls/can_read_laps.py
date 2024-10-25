from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid


@register_control
class can_read_laps(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "passwords"
        self.control_key = "can_read_laps"

        self.title = "Access to LAPS passwords"
        self.description = "Accounts that can read LAPS local administrator passwords."
        self.risk = "These objects can read LAPS local administrator passwords. Objects with rights to read LAPS passwords are a potential threat as they can read the password of the local administrator account."
        self.poa = (
            "Review the accounts and make sure that their privileges are legitimate."
        )

        self.can_read_laps = requests_results["can_read_laps"]
        self.users_nb_domain_admins = requests_results["nb_domain_admins"]

    def run(self):
        if self.can_read_laps is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "can_read_laps",
            "Objects able to read LAPS password",
            self.get_dico_description(),
        )
        grid = Grid("Objects able to LAPS passwords")
        grid.setheaders(["domain", "name"])
        self.can_read_laps_parsed = [
            {
                "domain": '<i class="bi bi-globe2"></i> ' + user["domain"],
                "name": '<i class="bi bi-person-fill"></i> ' + user["name"],
            }
            for user in self.can_read_laps
            if user["domain"] is not None and user["name"] is not None
        ]
        grid.setData(self.can_read_laps_parsed)
        page.addComponent(grid)
        page.render()

        self.data = len(self.can_read_laps_parsed)

        self.name_description = (
            f"{len(self.can_read_laps_parsed)} accounts can read LAPS passwords"
        )

    def get_rating(self) -> int:
        return (
            2
            if len(self.can_read_laps_parsed) > len(self.users_nb_domain_admins)
            else 5
        )
