from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.utils import grid_data_stringify, days_format
from ad_miner.sources.modules.common_analysis import containsDAs

from urllib.parse import quote


@register_control
class kerberoastables(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "kerberos"
        self.control_key = "kerberoastables"

        self.title = "Kerberoastable accounts"
        self.description = "Some accounts are vulnerable to a Kerberoasting attack. If their password is weak, it could be recovered in plaintext."
        self.risk = "This list should be as short as possible and restricted to service accounts. This list contains accounts that have Service Principal Name (SPN) set. Accounts like this could be compromised in case their password is weak."
        self.poa = "If the accounts listed here are not service accounts (i.e. if they don't have a strong, automatically-generated password), you should investigate as to why the account has an SPN. You should change the password for these accounts to something very strong, or remove the SPN from these accounts if it is not necessary."

        self.child_page_dico_description: dict[str, str] = {
            "description": "The Service Principle Name associated to a given host. It identifies every service to its host. The presence of a SPN for a given account allows users to request a ticket that contains some cryptographical information about the account's password.",
            "risk": "Because users' passwords are often weak, the ability to retrieve a ticket creates a risk of easily cracking the password of the user who has a SPN.",
            "poa": "Review all account's SPNs to check if they are still relevant and if they are, ensure that the account's password is strong.",
        }

        self.users_kerberoastable_users = requests_results["nb_kerberoastable_accounts"]

    def run(self):
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
            sortClass = str(n).zfill(
                6
            )  # used to make the sorting feature work with icons
            user["SPN"] = grid_data_stringify(
                {
                    "link": "%s.html?parameter=%s"
                    % ("kerberoastables_SPN", quote(str(user["name"]))),
                    "value": f"{n} SPN{'s' if n > 1 else ''}</span>",
                    "before_link": f'<i class="bi bi-list-task {sortClass}"></i>',
                }
            )

        child_page = Page(
            self.arguments.cache_prefix,
            "kerberoastables_SPN",
            "List of SPN",
            self.child_page_dico_description,
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
            self.get_dico_description(),
        )
        grid = Grid("Kerberoastable users")
        grid.setheaders(
            ["domain", "name", "Last password change", "Account Creation Date", "SPN"]
        )

        for elem in range(len(self.users_kerberoastable_users)):
            if self.users_kerberoastable_users[elem]["is_Domain_Admin"] == True:
                self.users_kerberoastable_users[elem]["name"] = (
                    '<i class="bi bi-gem" title="This user is domain admin"></i> '
                    + self.users_kerberoastable_users[elem]["name"]
                )
            else:
                self.users_kerberoastable_users[elem]["name"] = (
                    '<i class="bi bi-person-fill"></i> '
                    + self.users_kerberoastable_users[elem]["name"]
                )

        data = []
        for dict in self.users_kerberoastable_users:
            tmp_data = {"domain": '<i class="bi bi-globe2"></i> ' + dict["domain"]}
            tmp_data["name"] = dict["name"]
            tmp_data["Last password change"] = days_format(dict["pass_last_change"])
            tmp_data["Account Creation Date"] = days_format(dict["accountCreationDate"])
            tmp_data["SPN"] = dict["SPN"]
            data.append(tmp_data)

        # print("users_kerberoastable_users : ", json.dumps(self.users_kerberoastable_users))
        grid.setData(data)
        page.addComponent(grid)
        page.render()

        # TODO define the metric of your control
        # it will be stored in the data json
        self.data = (
            len(self.users_kerberoastable_users)
            if self.users_kerberoastable_users
            else 0
        )

        self.name_description = f"{self.data} kerberoastable accounts"

    def get_rating(self) -> int:
        return containsDAs(self.users_kerberoastable_users)
