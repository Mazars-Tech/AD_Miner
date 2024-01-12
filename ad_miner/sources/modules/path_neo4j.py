class Path:
    def __init__(self, nodes):
        self.nodes = nodes

    def reverse(self):
        self.nodes.reverse()
        for i in range(len(self.nodes) - 1):
            self.nodes[i].relation_type = self.nodes[i + 1].relation_type
        self.nodes[-1].relation_type = None
