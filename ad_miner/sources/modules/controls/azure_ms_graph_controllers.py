from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.common_analysis import presence_of, createGraphPage


@register_control
class azure_ms_graph_controllers(Control):  # TODO change the class name
    "Legacy control"  # TODO small documentation here

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "azure"
        self.category = "ms_graph"
        self.control_key = "azure_ms_graph_controllers"

        self.title = "Direct Controllers of MS Graph"
        self.description = "Accounts with privileged access to Microsoft Graph"
        self.risk = "Malicious actors can create privileged rights on Microsoft Graph to obtain persistence"
        self.poa = "The CISA recommends checking Graph API permissions for threat actors as part of detecting post compromise residual access"

        self.azure_ms_graph_controllers = requests_results["azure_ms_graph_controllers"]

    def run(self):
        if self.azure_ms_graph_controllers is None:
            self.azure_ms_graph_controllers = []

        createGraphPage(
            self.arguments.cache_prefix,
            "azure_ms_graph_controllers",
            "Controllers of MS Graph",
            self.get_dico_description(),
            self.azure_ms_graph_controllers,
            self.requests_results,
        )

        self.data = len(self.azure_ms_graph_controllers)
        self.name_description = (
            f"{len(self.azure_ms_graph_controllers)} paths to MS Graph controllers"
        )

    def get_rating(self) -> int:
        return presence_of(self.azure_ms_graph_controllers, 1)
