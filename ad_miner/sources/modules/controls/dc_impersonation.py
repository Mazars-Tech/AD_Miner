from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.common_analysis import createGraphPage, presence_of


@register_control
class dc_impersonation(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "misc"
        self.control_key = "dc_impersonation"

        self.title = "Shadow credentials on domain controllers"
        self.description = "Non-domain admins that can directly or indirectly impersonate a Domain Controller"
        self.risk = "The ability to impersonate the machine account of a domain controller allows to perform very powerful attacks such as DCSync. The accounts listed here are not member of domain admin groups but can still impersonate domain controllers, effectively giving them the privileges to dump all the data of Active Directory (including all users password hashes). If any of these accounts is compromised, then the domain it is attached to is can be considered compromised as well."
        self.poa = "Review the accounts to check if this privilege is legitimate. If not, remove it."

        self.users_dc_impersonation = requests_results["dc_impersonation"]
        if self.users_dc_impersonation != None:
            self.users_dc_impersonation_count = len(self.users_dc_impersonation)
        else:
            self.users_dc_impersonation_count = 0

    def run(self):

        createGraphPage(
            self.arguments.cache_prefix,
            "dc_impersonation",
            "Shadow credentials on domain controllers",
            self.get_dico_description(),
            self.users_dc_impersonation,
            requests_results=self.requests_results,
        )
        self.data = (
            self.users_dc_impersonation_count
            if self.users_dc_impersonation_count
            else 0
        )

        self.name_description = f"{self.data} paths to impersonate DCs"

    def get_rating(self) -> int:
        return presence_of(self.users_dc_impersonation)
