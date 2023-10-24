import time
import json

from os.path import sep

from ad_miner.sources.modules import logger
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.page_class import Page
#from relation_neo4j import Relation
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.utils import grid_data_stringify, timer_format
from urllib.parse import quote


class Objects:
    def __init__(self, arguments, neo4j, domain, computers, users):
        self.arguments = arguments
        self.neo4j = neo4j
        self.domain = domain
        self.computers = computers
        self.users = users
        self.start = time.time()
        logger.print_debug("Computing other objects")

        self.objects_to_dcsync = neo4j.all_requests["objects_to_dcsync"]["result"]
        self.dcsync_list = neo4j.all_requests["dcsync_list"]["result"]

        self.dcsync_paths = neo4j.all_requests["set_dcsync1"]["result"] + neo4j.all_requests["set_dcsync2"]["result"]

        self.users_nb_domain_admins = neo4j.all_requests["nb_domain_admins"]["result"]

        self.get_unpriv_users_to_GPO()

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
            # Graph path to DCSync
            page = Page(
                self.arguments.cache_prefix,
                f"path_to_{n.name}_with_dcsync",
                f"DCsync path for {n.name}",
                "can_dcsync_graph",
            )
            graph = Graph()

            paths_left = []
            for path in self.objects_to_dcsync:
                if path.nodes[-1].name == n.name:
                    paths_left.append(path)

            graph.setPaths(paths_left)
            page.addComponent(graph)
            page.render()

            # Graph DCSync detail
            page = Page(
                self.arguments.cache_prefix,
                f"dcsync_from_{n.name}",
                f"DCSync detail for {n.name}",
                "can_dcsync_graph",
            )
            graph = Graph()

            paths_right = []
            for path in self.dcsync_paths:
                if path.nodes[0].name == n.name:
                    paths_right.append(path)

            graph.setPaths(paths_right)
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

            sortClass = str(len(paths_left)).zfill(6)
            data.append(
                {
                    "domain": '<i class="bi bi-globe2"></i> ' + n.domain,
                    "type": type_icon + ' ' + n.labels,
                    "name": name_icon + ' ' + n.name,
                    "path to account": grid_data_stringify({
                        "link": "path_to_%s_with_dcsync.html" % quote(str(n.name)),
                        "value": f"{len(paths_left)} paths <i class='bi bi-box-arrow-up-right'></i>",
                        "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                    }),
                    "path to dcsync": grid_data_stringify({
                        "link": "dcsync_from_%s.html" % quote(str(n.name)),
                        "value": f"DCSync path <i class='bi bi-box-arrow-up-right'></i>",
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
        headers = ["domain", "type", "name", "path to account", "path to dcsync"]
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
            raw_data[k]["target graph"]["link"] = f"can_dcsync_from_{quote(str(raw_data[k]['name']))}.html"
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

    
    def get_unpriv_users_to_GPO(self):
        if self.arguments.gpo_low and self.domain.unpriv_users_to_GPO is None:
            return
        if not self.arguments.gpo_low:
            fail = []
            if self.domain.unpriv_users_to_GPO_init is None:
                fail.append("unpriv_users_to_GPO_init")
            elif self.domain.unpriv_users_to_GPO_user_enforced is None:
                fail.append("unpriv_users_to_GPO_user_enforced")
            elif self.domain.unpriv_users_to_GPO_user_not_enforced is None:
                fail.append("unpriv_users_to_GPO_user_not_enforced")
            elif self.domain.unpriv_users_to_GPO_computer_enforced is None:
                fail.append("unpriv_users_to_GPO_computer_enforced")
            elif self.domain.unpriv_users_to_GPO_computer_not_enforced is None:
                fail.append("unpriv_users_to_GPO_computer_not_enforced")

            if 0 < len(fail) < 5:  # if only some of them are disabled
                logger.print_error(
                    f" In order to use 'normal GPO mode', please activate the following in config.json : {', '.join(fail)}"
                )

            if len(fail) > 0:
                return

        def parseGPOData(listOfPaths, headers):
            """
            Initial parsing of data from neo4j requests for GPO
            """
            dictOfGPO = {}
            for path in listOfPaths:
                start = path.nodes[0]
                end = path.nodes[-1]
                if "GPO" in start.labels:
                    nameOfGPO = start.name
                    idOfGPO = start.id
                    sens = "right"
                elif "GPO" in end.labels:
                    nameOfGPO = end.name
                    idOfGPO = end.id
                    sens = "left"
                else:
                    continue
                try:
                    if sens == "right":
                        dictOfGPO[nameOfGPO][headers[4]] += 1
                        dictOfGPO[nameOfGPO]["right_path"].append(path)
                        dictOfGPO[nameOfGPO]["end_list"].append((end.name, end.labels))
                    elif sens == "left":
                        dictOfGPO[nameOfGPO][headers[1]] += 1
                        dictOfGPO[nameOfGPO]["left_path"].append(path)
                        dictOfGPO[nameOfGPO]["entry_list"].append((start.name, start.labels))
                    else:
                        continue
                except KeyError:
                    if sens == "right":
                        dictOfGPO[nameOfGPO] = {
                            headers[0]: nameOfGPO,
                            headers[1]: 0,
                            headers[4]: 1,
                            "left_path": [],
                            "right_path": [path],
                            "id": idOfGPO,
                            "entry_list": [],
                            "end_list": [(end.name, end.labels)],
                        }
                    elif sens == "left":
                        dictOfGPO[nameOfGPO] = {
                            headers[0]: nameOfGPO,
                            headers[1]: 1,
                            headers[4]: 0,
                            "left_path": [path],
                            "right_path": [],
                            "id": idOfGPO,
                            "entry_list": [(start.name, start.labels)],
                            "end_list": [],
                        }
                    else:
                        continue
            return dictOfGPO

        def formatGPOGrid(dictOfGPO, headers):
            output = []

            # Extract all computers admin of computers
            self.computers_with_admin_rights = [d["Computer Admin"].split('</i> ')[-1] for d in self.computers.computers_admin_data_grid]
            # Extract all users admin of computers
            self.users_with_admin_rights = [d["User"].split('</i> ')[-1] for d in self.users.users_admin_of_computers]

            for _, dict in dictOfGPO.items():
                self.domain.number_of_gpo += 1
                # Rate the interest of the GPO
                # 0 star  : no object impacted
                # 1 star  : at least one object impacted
                # 2 stars : at least one admin account impacted
                # 3 stars : full domain or at least one domain admin impacted
                paths = dict["right_path"]

                if len(paths) == 0:
                    interest = 0
                else:
                    interest = 1
                
                for path in paths:
                    for i in range(len(path.nodes)):
                        if path.nodes[i].labels == "Domain":
                            interest = 3
                            break
                        if path.nodes[i].name in self.domain.admin_list:
                            interest = 3
                            break
                        if path.nodes[i].name in self.users_with_admin_rights or path.nodes[i].name in self.computers_with_admin_rights:
                            interest = max(2, interest)
                
                
                icon = f"<span class='{interest}'></span><i class='bi bi-star-fill'></i>"*interest + "<i class='bi bi-star'></i>"*(3-interest)

                output.append(
                    {
                        headers[0]: dict[headers[0]],
                        headers[1]: f'<i class="bi bi-shuffle {str(dict[headers[1]]).zfill(6)}"></i> ' + str(dict[headers[1]]),
                        headers[2]: {
                            "link": "users_GPO_access-%s-left-graph.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-diagram-3-fill' aria-hidden='true'></i>",
                        },
                        headers[3]: {
                            "link": "users_GPO_access-%s-left-grid.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-list-columns-reverse' aria-hidden='true'></i>",
                        },
                        headers[4]: f'<i class="bi bi-bullseye {str(len(list(set(dict["end_list"])))).zfill(6)}"></i> ' + str(len(list(set(dict["end_list"])))),
                        headers[5]: icon,
                        headers[6]: {
                            "link": "users_GPO_access-%s-right-graph.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-diagram-3-fill' aria-hidden='true'></i>",
                        },
                        headers[7]: {
                            "link": "users_GPO_access-%s-right-grid.html"
                            % (quote(str(dict[headers[0]]).replace(sep, '_'))),
                            "value": "<i class='bi bi-list-columns-reverse' aria-hidden='true'></i>",
                        },
                    }
                )
            return output

        def formatSmallGrid(list, gpo_name):
            output = []
            for n in list:
                if n[1] == "Computer":
                    icon = '<i class="bi bi-pc-display"></i> '
                elif n[1] == "User":
                    icon = '<i class="bi bi-person-fill"></i> '
                elif n[1] == "Domain":
                    icon = '<i class="bi bi-house-fill"></i> '
                else:
                    icon = '<i class="bi bi-question-circle-fill"></i> '
                
                if n[0] in self.computers_with_admin_rights or n[0] in self.users_with_admin_rights:
                    icon = icon + '<i class="bi bi-gem" title="This object has administration rights" style="color:grey;"></i> '
                if n[0] in self.domain.admin_list:
                    icon = '<i class="bi bi-gem" title="This user is domain admin" style="color:deepskyblue;"></i> '

                output.append({gpo_name: icon + n[0]})
            return output

        headers = [
            "GPO name",
            "Paths to GPO",
            "Inbound graph",
            "Inbound list",
            "Objects impacted",
            "Targets interest",
            "Outbound graph",
            "Outbound list",
        ]
        if not self.arguments.gpo_low:
            data = (
                self.domain.unpriv_users_to_GPO_init
                + self.domain.unpriv_users_to_GPO_user_enforced
                + self.domain.unpriv_users_to_GPO_computer_enforced
                + self.domain.unpriv_users_to_GPO_user_not_enforced
                + self.domain.unpriv_users_to_GPO_computer_not_enforced
            )
            self.domain.unpriv_users_to_GPO_parsed = parseGPOData(data, headers)
            grid = Grid("Users with GPO access")
        else:
            self.domain.unpriv_users_to_GPO_parsed = parseGPOData(
                self.domain.unpriv_users_to_GPO, headers
            )
            grid = Grid("Users with GPO access")

        formated_data = sorted(
            formatGPOGrid(self.domain.unpriv_users_to_GPO_parsed, headers),
            key=lambda x: x[headers[1]],
            reverse=True,
        )
        page = Page(
            self.domain.arguments.cache_prefix,
            "users_GPO_access",
            "Exploitation through GPO",
            "users_GPO_access",
        )

        grid.setheaders(headers)
        grid.setData(json.dumps(formated_data))
        page.addComponent(grid)
        page.render()

        for _, GPO in self.domain.unpriv_users_to_GPO_parsed.items():
            url_left_graph = "users_GPO_access-%s-left-graph" % GPO[headers[0]]
            url_right_graph = "users_GPO_access-%s-right-graph" % GPO[headers[0]]
            page_left_graph = Page(
                self.arguments.cache_prefix,
                url_left_graph,
                "Users with write access on GPO",
                "graph_GPO_access",
            )
            page_right_graph = Page(
                self.arguments.cache_prefix,
                url_right_graph,
                "Objects impacted by GPO",
                "graph_GPO_access",
            )

            url_left_grid = "users_GPO_access-%s-left-grid" % GPO[headers[0]]
            url_right_grid = "users_GPO_access-%s-right-grid" % GPO[headers[0]]
            page_left_grid = Page(
                self.arguments.cache_prefix,
                url_left_grid,
                "List of users able to compromise %s" % GPO[headers[0]],
                "grid_GPO_access",
            )
            page_right_grid = Page(
                self.arguments.cache_prefix,
                url_right_grid,
                "List of users impacted by %s" % GPO[headers[0]],
                "grid_GPO_access",
            )

            # if GPO[headers[4]] > 0:
            graph_left = Graph()
            graph_left.setPaths(GPO["left_path"])
            page_left_graph.addComponent(graph_left)

            graph_right = Graph()
            graph_right.setPaths(GPO["right_path"])
            page_right_graph.addComponent(graph_right)

            if not self.arguments.gpo_low:
                entry_grid = Grid("List of users able to compromise %s" % GPO[headers[0]])
            else:
                entry_grid = Grid("List of users able to compromise %s" % GPO[headers[0]])
            entry_grid.setheaders([GPO[headers[0]]])
            entry_grid.setData(
                json.dumps(
                    formatSmallGrid(
                        list(set(GPO["entry_list"])), GPO[headers[0]])
                )
            )
            page_left_grid.addComponent(entry_grid)

            
            end_grid = Grid("List of users impacted by %s" % GPO[headers[0]])
            end_grid.setheaders([GPO[headers[0]]])
            end_grid.setData(
                json.dumps(formatSmallGrid(
                    list(set(GPO["end_list"])), GPO[headers[0]]))
            )
            page_right_grid.addComponent(end_grid)

            page_left_graph.render()
            page_right_graph.render()
            page_left_grid.render()
            page_right_grid.render()