from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid

from ad_miner.sources.modules.common_analysis import containsDAs

import json


@register_control
class users_pwd_cleartext(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "passwords"

        self.control_key = "users_pwd_cleartext"

        self.title = "Users with cleartext passwords"
        self.description = (
            "These users have their passwords stored somewhere in plaintext."
        )
        self.risk = "This list should be strictly zero. Any attacker finding a password in cleartext would be able to use it instantly to enter in the AD. This represents a major security issue."
        self.poa = "Review this list and change password for all of these accounts. Make sure their new passwords are not stored in cleartext anymore."

        self.users_pwd_cleartext = requests_results["nb_user_password_cleartext"]

    def run(self):
        if self.users_pwd_cleartext is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "users_pwd_cleartext",
            "Number of users with password in cleartext",
            self.get_dico_description(),
        )
        grid = Grid("Users with password in cleartext")
        grid.setheaders(["user", "password", "is Domain Admin"])
        grid.setData(json.dumps(self.users_pwd_cleartext))
        page.addComponent(grid)
        page.render()

        self.data = len(self.users_pwd_cleartext) if self.users_pwd_cleartext else 0

        self.name_description = f"{self.data} users with clear text password"

    def get_rating(self) -> int:
        return containsDAs(self.users_pwd_cleartext)
