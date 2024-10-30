from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.common_analysis import containsDAs

import json


@register_control
class as_rep(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "kerberos"
        self.control_key = "as_rep"

        self.title = "AS-REP Roastable accounts"
        self.description = "These accounts do not need to authenticate to receive a response from the KDC containing the hash of the password of the account."
        self.risk = "Ideally, this list should be strictly empty. With the KRB_AS_REP, an attacker can find the password of the account offline and then take complete control of the account."
        self.poa = "Change the configuration of these accounts and make sure to not disable the need to authenticate."

        self.users_kerberos_as_rep = requests_results["nb_as-rep_roastable_accounts"]

    def run(self):
        if self.users_kerberos_as_rep is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "as_rep",
            "List of all users with AS-REP",
            self.get_dico_description(),
        )
        grid = Grid("Users with AS-REP")
        grid.setheaders(["domain", "name", "is_Domain_Admin"])
        grid.setData(json.dumps(self.users_kerberos_as_rep))
        page.addComponent(grid)
        page.render()

        self.data = len(self.users_kerberos_as_rep) if self.users_kerberos_as_rep else 0

        self.name_description = f"{self.data} accounts are AS-REP-roastable"

    def get_rating(self) -> int:
        return containsDAs(self.users_kerberos_as_rep)
