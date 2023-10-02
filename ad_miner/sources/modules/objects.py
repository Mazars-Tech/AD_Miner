import random
import time

from ad_miner.sources.modules import logger
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.page_class import Page
#from relation_neo4j import Relation
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.utils import grid_data_stringify, timer_format


class Objects:
    def __init__(self, arguments, neo4j):
        self.arguments = arguments
        self.neo4j = neo4j
        self.start = time.time()
        logger.print_debug("Computing other objects")

        self.objects_to_dcsync = neo4j.all_requests["objects_to_dcsync"]["result"]
        self.dcsync_list = neo4j.all_requests["dcsync_list"]["result"]

        self.users_nb_domain_admins = neo4j.all_requests["nb_domain_admins"]["result"]

        end_nodes = []
        # Check if dcsync path is activated or not
        if self.objects_to_dcsync == None:
            # Placeholder to fill the list for the rating
            self.can_dcsync_nodes = ["1"]*len(self.dcsync_list)
            self.genNodesDCsyncLightPage(neo4j)
        else:
            for p in self.objects_to_dcsync:
                end_nodes.append(p.nodes[-1])  # Get last node of the path
            end_nodes = list(set(end_nodes))

            self.can_dcsync_nodes = end_nodes
            # Generate all the objects-related pages

            self.genNodesDCsyncPage()
        logger.print_time(timer_format(time.time() - self.start))

        # Nodes that can dcsync

    def genNodesDCsyncPage(self):
        if not self.objects_to_dcsync:
            return

        data = []
        for n in self.can_dcsync_nodes:
            page = Page(
                self.arguments.cache_prefix,
                f"path_to_{n.name}_with_dcsync",
                f"DCsync path for {n.name}",
                "can_dcsync_graph",
            )
            graph = Graph()

            paths = []
            for path in self.objects_to_dcsync:
                if path.nodes[-1].name == n.name:
                    paths.append(path)

            # TODO : vérifier que le droit DCSync correspond TOUJOURS à un DCSync sur le domaine d'appartenance du noeud
            # 		-> Si ce n'est pas la cas alors il faut adapter la ligne suivante (n.domain)
            n.relation_type = "DCSync"
            end = Node(f"{random.randint(1,10000):06}", "Domain", n.domain, n.domain, "")
            #rel = Relation(int(str(n.id) + "00" + str(n.id)), [n, end], "DCSync")
            path = Path([n, end])
            paths.append(path)

            graph.setPaths(paths)
            page.addComponent(graph)
            page.render()

            if n.labels.lower() == "user":
                type_icon = '<i class="bi bi-person-fill"></i>'
            elif n.labels.lower() == "group":
                type_icon = '<i class="bi bi-people-fill"></i>'
            else:
                type_icon = '<i class="bi bi-question-circle-fill"></i>'

            if n.name in self.users_nb_domain_admins:
                name_icon = '<i class="bi bi-gem stats-icon"></i>'
            else:
                name_icon = type_icon

            sortClass = str(len(paths)).zfill(6)
            data.append(
                {
                    "domain": '<i class="bi bi-globe2"></i> ' + n.domain,
                    "type": type_icon + ' ' + n.labels,
                    "name": name_icon + ' ' + n.name,
                    "path to account": grid_data_stringify({
                        "link": "path_to_%s_with_dcsync.html" % n.name,
                        "value": f"{len(paths)} paths <i class='bi bi-box-arrow-up-right'></i>",
                        "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                    }),
                }
            )

        page = Page(
            self.arguments.cache_prefix,
            "can_dcsync",
            "List of all objects with dcsync privileges",
            "can_dcsync",
        )
        grid = Grid("DCsync objects")
        headers = ["domain", "type", "name", "path to account"]
        grid.setheaders(headers)
        grid.setData(data)
        page.addComponent(grid)
        page.render()

    def genNodesDCsyncLightPage(self, neo4j):
        page = Page(
            self.arguments.cache_prefix,
            "can_dcsync",
            "List of all objects with dcsync privileges",
            "can_dcsync",
        )
        paths = neo4j.all_requests["set_dcsync1"]["result"] + neo4j.all_requests["set_dcsync2"]["result"]
        raw_data = {}
        for e in self.dcsync_list:
            raw_data[e["name"]] = {
                "domain": e["domain"],
                "name": e["name"],
                "target graph": {},
                "paths": []
            }
        for path in paths:
            try:
                raw_data[path.nodes[0].name]["paths"].append(path)
            except KeyError:
                continue
        data = []
        #print(raw_data)
        for k in raw_data.keys():
            graph_page = Page(
            self.arguments.cache_prefix,
            f"can_dcsync_from_{raw_data[k]['name']}",
            f"DCSync from {raw_data[k]['name']}",
            "can_dcsync",
            )
            graph = Graph()
            graph.setPaths(raw_data[k]["paths"])
            graph_page.addComponent(graph)
            graph_page.render()
            sortClass = str(len(raw_data[k]["paths"])).zfill(6)
            raw_data[k]["target graph"]["link"] = f"can_dcsync_from_{raw_data[k]['name']}.html"
            raw_data[k]["target graph"]["value"] = f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i> View paths ({len(raw_data[k]['paths'])}) <i class='bi bi-box-arrow-up-right'></i>"
            data.append({
                "domain": raw_data[k]["domain"],
                "name": raw_data[k]["name"],
                "target graph": raw_data[k]["target graph"],
                         })
        grid = Grid("DCsync objects")
        headers = ["domain", "name", "target graph"]
        grid.setheaders(headers)
        grid.setData(data)
        page.addComponent(grid)
        page.render()