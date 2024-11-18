from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.histogram_class import Histogram

from ad_miner.sources.modules.utils import grid_data_stringify


@register_control
class dangerous_paths(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "permissions"
        self.control_key = "dangerous_paths"

        self.title = "Attack paths choke points"
        self.description = "List of the main paths to become a domain administrator"
        self.risk = "This representation exposes the most common links to become domain administrator, which means the more likely to be used during an attack."
        self.poa = "Tackling the most common paths is a good approach to limit the risk of a compromission as it removes most of the paths to domain administrator."

        self.objects_to_domain_admin = requests_results["objects_to_domain_admin"]
        self.objects_to_dcsync = requests_results["objects_to_dcsync"]
        self.da_to_da = requests_results["da_to_da"]

    def run(self):

        def analyse_cache(cache):
            if cache == None:
                return []
            dico_node_rel_node = {}
            for path in cache:
                for i in range(1, len(path.nodes) - 2):
                    node_rel_node_instance = f"{path.nodes[i].name} ⮕ {path.nodes[i].relation_type} ⮕ {path.nodes[i+1].name}"
                    if dico_node_rel_node.get(node_rel_node_instance):
                        dico_node_rel_node[node_rel_node_instance] += 1
                    else:
                        dico_node_rel_node[node_rel_node_instance] = 1

            return dict(
                sorted(dico_node_rel_node.items(), key=lambda item: item[1])[::-1][:100]
            )

        dico_objects_to_da = analyse_cache(self.objects_to_domain_admin)
        dico_dcsync_to_da = analyse_cache(self.objects_to_dcsync)
        dico_da_to_da = analyse_cache(self.da_to_da)

        if self.objects_to_dcsync != None:
            len_dcsync = len(self.objects_to_dcsync)
        else:
            len_dcsync = 0

        if self.da_to_da != None:
            len_da_to_da = len(self.da_to_da)
        else:
            len_da_to_da = 0

        # Remove 1 to exclude the false positive of container USERS containing DOMAIN ADMIN group
        self.total_dangerous_paths = max(
            len_dcsync + len(self.objects_to_domain_admin) + len_da_to_da - 1, 0
        )

        page = Page(
            self.arguments.cache_prefix,
            "dangerous_paths_dcsync_to_da",
            "DCSync privileges to DA privileges",
            self.get_dico_description(),
        )
        histo = Histogram()
        histo.setData(dico_dcsync_to_da, len_dcsync)
        page.addComponent(histo)
        page.render()

        page = Page(
            self.arguments.cache_prefix,
            "dangerous_paths_objects_to_da",
            "Objects to DA privileges",
            self.get_dico_description(),
        )
        histo = Histogram()
        histo.setData(dico_objects_to_da, len(self.objects_to_domain_admin))
        page.addComponent(histo)
        page.render()

        page = Page(
            self.arguments.cache_prefix,
            "dangerous_paths_da_to_da",
            "DA privileges to DA privileges",
            self.get_dico_description(),
        )
        histo = Histogram()
        histo.setData(dico_da_to_da, len_da_to_da)
        page.addComponent(histo)
        page.render()

        page = Page(
            self.arguments.cache_prefix,
            "dangerous_paths",
            "Attack paths choke points",
            self.get_dico_description(),
        )
        grid = Grid("dangerous paths")

        grid.addheader("Type of Graphs")
        dangerous_path_data = [
            {
                "Type of Graphs": grid_data_stringify(
                    {
                        "value": "DCSync privileges to DA privileges",
                        "link": "dangerous_paths_dcsync_to_da.html",
                        "before_link": '<i class="bi bi-arrow-repeat"></i>',
                    }
                )
            },
            {
                "Type of Graphs": grid_data_stringify(
                    {
                        "value": "Objects to DA privileges",
                        "link": "dangerous_paths_objects_to_da.html",
                        "before_link": '<i class="bi bi-chevron-double-up"></i>',
                    }
                )
            },
            {
                "Type of Graphs": grid_data_stringify(
                    {
                        "value": "DA privileges to DA privileges",
                        "link": "dangerous_paths_da_to_da.html",
                        "before_link": '<i class="bi bi-arrow-left-right"></i>',
                    }
                )
            },
        ]

        grid.setData(dangerous_path_data)
        page.addComponent(grid)
        page.render()

        self.data = self.total_dangerous_paths
        self.name_description = (
            f"More than {self.total_dangerous_paths} dangerous paths to DA"
        )

    def get_rating(self) -> int:
        return 1 if self.total_dangerous_paths > 0 else 5
