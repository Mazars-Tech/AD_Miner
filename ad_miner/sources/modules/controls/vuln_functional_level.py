from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid


@register_control
class vuln_functional_level(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "misc"
        self.control_key = "vuln_functional_level"

        self.title = "Functional level of the domain"
        self.description = "The functional level of an Active Directory domain refers to the level of compatibility and functionality that the domain supports. It determines which features and capabilities are available for the domain controllers within that domain."
        self.risk = "Using a low functional level in Active Directory can present security risks, primarily because older functional levels may lack certain security features and improvements that have been introduced in newer versions of Windows Server."
        self.poa = "To mitigate these security risks, it's generally advisable to raise the functional level of your Active Directory domains to a level that corresponds to the version of Windows Server you are running, or at least to a reasonably recent level that provides essential security features."

        self.vuln_functional_level = requests_results["vuln_functional_level"]

    def run(self):
        if self.vuln_functional_level is None:
            return
        page = Page(
            self.arguments.cache_prefix,
            "vuln_functional_level",
            "Number of insufficient forest and domains functional levels",
            self.get_dico_description(),
        )
        grid = Grid("Number of insufficient forest and domains functional levels")
        final_data = []
        for dico in self.vuln_functional_level:
            d = dico.copy()
            if d["Level maturity"] is None:
                continue
            elif d["Level maturity"] <= 1:
                color = "red"
            elif d["Level maturity"] <= 3:
                color = "orange"
            else:
                color = "green"
            d[
                "Level maturity"
            ] = f'<i class="bi bi-star-fill" style="color: {color}"></i>' * d[
                "Level maturity"
            ] + f'<i class="bi bi-star" style="color: {color}"></i>' * (
                5 - d["Level maturity"]
            )
            final_data.append(d)
        grid.setheaders(["Level maturity", "Full name", "Functional level"])
        grid.setData(final_data)
        page.addComponent(grid)
        page.render()

        self.data = len(self.vuln_functional_level) if self.vuln_functional_level else 0

        self.name_description = (
            f"{self.data} insufficient forest and domains functional levels"
        )

    def get_rating(self) -> int:
        req = self.vuln_functional_level
        if req != None and req != []:
            return min([ret["Level maturity"] for ret in req])  # TODO
        else:
            return -1
