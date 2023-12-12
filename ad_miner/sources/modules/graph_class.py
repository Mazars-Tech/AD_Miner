
from ad_miner.sources.modules.utils import HTML_DIRECTORY

class Graph:
    def __init__(self, template="graph", path_limit=80000):
        self.template_base_path = HTML_DIRECTORY / "components/graph/"
        self.template = template
        self.paths = []
        self.nodes = {}
        self.relations = []
        self.relations_hashes = {}
        self.path_limit = path_limit
        self.ghost_computer = {}
        self.ghost_user = {}
        self.dc_computer = {}
        self.user_da = {}
        self.group_da = {}

    def addPath(self, path):
        self.paths.append(path)

    def setPaths(self, paths):
        self.paths = paths

    def addGhostComputers(self, ghost_computer):
        self.ghost_computer = ghost_computer

    def addGhostUsers(self, ghost_user):
        self.ghost_user = ghost_user

    def addDCComputers(self, dc_computer):
        self.dc_computer = dc_computer

    def addUserDA(self, user_da):
        self.user_da = user_da

    def addGroupDA(self, group_da):
        self.group_da = group_da

    def render(self, page_f):

        # Write header
        with open(
            self.template_base_path / (self.template + "_header.html"), "r"
        ) as header_f:
            html_header = header_f.read()
            page_f.write(html_header)

        for index, path in enumerate(self.paths):
            for i in range(len(path.nodes)):
                # Compute node style
                if i == 0:
                    node_position = "start"
                elif i == len(path.nodes) - 1:
                    node_position = "end"
                else:
                    node_position = "intermediate"

                if self.ghost_computer.get(path.nodes[i].name) or self.ghost_user.get(
                    path.nodes[i].name
                ):
                    attribute1 = "ghost"
                else:
                    attribute1 = "none"

                if (
                    self.dc_computer.get(path.nodes[i].name)
                    or self.user_da.get(path.nodes[i].name)
                    or self.group_da.get(path.nodes[i].name)
                ):
                    attribute2 = "da"
                else:
                    attribute2 = "none"


                list_labels = ["User", "Foreignsecurityprincipal", "GPO", "Computer", "OU", "Group", "Domain", "Container", "Unknown", "Group_cluster", "Device", "AZTenant", "AZRole"]


                if path.nodes[i].labels in list_labels:
                    label_instance = path.nodes[i].labels
                elif path.nodes[i].labels[2:] in list_labels:
                    label_instance = path.nodes[i].labels[2:]
                else:
                    label_instance = "Unknown"

                if not self.nodes.get(path.nodes[i].id):

                    final_graph_node = {
                        "id": path.nodes[i].id,
                        "label": path.nodes[i].name,
                        "shape": "image",
                        "group": f"{node_position}_{label_instance}_{attribute1}_{attribute2}",
                    }
                    self.nodes[path.nodes[i].id] = final_graph_node

                else:
                    if node_position != self.nodes[path.nodes[i].id]["group"].split("_")[0]:
                        self.nodes[path.nodes[i].id][
                            "group"
                        ] = f"intermediate_{label_instance}_{attribute1}_{attribute2}"

                if i!=0:
                    relation = {
                        "from": path.nodes[i-1].id,
                        "to": path.nodes[i].id,
                        "label": path.nodes[i-1].relation_type,
                    }

                    # Avoid relation duplicated to keep graph clean
                    # Use hashes list for better performance
                    hash_rel = hash(
                        str(relation["from"])
                        + str(relation["to"])
                        + str(relation["label"])
                    )
                    if not self.relations_hashes.get(hash_rel):
                        self.relations.append(relation)
                        self.relations_hashes[hash_rel] = True

            # Check if nodes number reaches soft limit
            # if (len(self.nodes_ids) > self.path_limit):
            # 	print("Info : A lot of nodes have to be processed, this could take awhile")
        nodes = list(self.nodes.values())
        for n in nodes:  # Sanitize None values (otherwise it creates a bug in JS)
            if n["label"] == None:
                n["label"] = "???"
        page_f.write(f'<script type="text/javascript">window.data_nodes = {nodes};\n')
        page_f.write(f"window.data_edges = {self.relations};</script>\n")
        # 	Write data of the graph in a different file
        # with open(self.template_base_path + self.template + "_footer.html", 'r') as footer_f:
        # 	page_f.write(footer_f.read() % (self.nodes, self.relations))
