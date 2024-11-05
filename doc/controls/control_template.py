from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control
from ad_miner.sources.modules import logger
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.path_neo4j import Path

from ad_miner.sources.modules.utils import grid_data_stringify, days_format
from ad_miner.sources.modules.common_analysis import presence_of

from urllib.parse import quote


@register_control
class my_control_class_name(Control):  # TODO change the class name
    "Docstring of my control"  # TODO small documentation here

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        # TODO define this to "azure" or "on_premise" accordingly
        self.azure_or_onprem = ""

        # TODO define this to the category in which the control should appear
        # on the main page (passwords, kerberos, permissions, misc, az_permissions,
        # az_passwords, az_misc, ms_graph)
        self.category = ""

        # TODO add the control key. This string should be uniq and will be used
        # by the code and written to the data json.
        # Do NOT change existing control_key, as it will break evolution with older ad miner versions
        self.control_key = "control_key_to_change"

        # TODO define the control page title and texts
        self.title = ""
        self.description = ""
        self.risk = ""
        self.poa = ""

    def run(self):
        # TODO The code for the analysis goes here

        # TODO TODELETE TEMP TOREMOVE change page description to self.get_dico_description()

        # TODO define the metric of your control
        # it will be stored in the data json
        self.data = -1

        # TODO define the sentence that will be displayed in the 'smolcard' view and in the center of the mainpage
        self.name_description = f"... {12} ...."

    def get_rating(self) -> int:
        # TODO define the rating function.
        # You can use common rating functions define in ad_miner.sources.modules.common_analysis like presenceof, percentage_superior, etc.
        # -1 = grey, 1 = red, 2 = orange, 3 = yellow, 4 =green, 5 = green,
        return -1
