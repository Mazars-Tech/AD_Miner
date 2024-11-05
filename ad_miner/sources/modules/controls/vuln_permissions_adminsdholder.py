from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.common_analysis import presence_of, createGraphPage


@register_control
class vuln_permissions_adminsdholder(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "permissions"
        self.control_key = "vuln_permissions_adminsdholder"

        self.title = "Paths to the AdminSDHolder container"
        self.description = "Paths to the AdminSDHolder container"

        self.vuln_permissions_adminsdholder = requests_results[
            "vuln_permissions_adminsdholder"
        ]

    def run(self):
        createGraphPage(
            self.arguments.cache_prefix,
            "vuln_permissions_adminsdholder",
            "Objects with path to the adminSDHolder object",
            self.get_dico_description(),
            self.vuln_permissions_adminsdholder,
            self.requests_results,
        )
        self.data = (
            len(self.vuln_permissions_adminsdholder)
            if self.vuln_permissions_adminsdholder
            else 0
        )

        self.name_description = f"{self.data} paths to an AdminSDHolder container"

    def get_rating(self) -> int:
        return presence_of(self.vuln_permissions_adminsdholder, criticity=1)
