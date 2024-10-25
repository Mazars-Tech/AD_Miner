from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.common_analysis import presence_of, createGraphPage


@register_control
class unpriv_to_dnsadmins(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "permissions"
        self.control_key = "unpriv_to_dnsadmins"

        self.title = "Paths to DNS Admins"
        self.description = (
            "Users can take over DNS Admins group, leading to domain compromission."
        )

        self.unpriv_to_dnsadmins = requests_results["unpriv_to_dnsadmins"]

    def run(self):
        createGraphPage(
            self.arguments.cache_prefix,
            "unpriv_to_dnsadmins",
            "Unprivileged users with path to DNSAdmins",
            self.get_dico_description(),
            self.unpriv_to_dnsadmins,
            self.requests_results,
        )

        self.data = len(self.unpriv_to_dnsadmins) if self.unpriv_to_dnsadmins else 0
        self.name_description = f"{self.data} paths to DNSAdmins group"

    def get_rating(self) -> int:
        return presence_of(self.unpriv_to_dnsadmins, criticity=2)
