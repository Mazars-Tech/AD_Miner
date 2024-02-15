class Path:
    def __init__(self, nodes):
        self.nodes = nodes

    def __eq__(self, other):
        if not isinstance(other, Path):
            return NotImplemented
        if len(self.nodes) != len(other.nodes):
            return False

        ret = True
        for i in range(len(self.nodes)):
            ret = ret and (self.nodes[i] == other.nodes[i])
        return ret

    def reverse(self):
        self.nodes.reverse()
        for i in range(len(self.nodes) - 1):
            self.nodes[i].relation_type = self.nodes[i + 1].relation_type
        self.nodes[-1].relation_type = ""
