class Histogram:
    def __init__(
        self, title=None, template="histogram", icon=None, color="cardHeaderMazGrey"
    ):
        self.template_base_path = "sources/html/components/histogram/"
        self.title = title
        self.icon = icon
        self.template = template
        self.color = color
        self.data1 = {}
        self.data2 = ""
        self.number_paths_main_nodes = 0

    def setData(self, data1, data2):
        self.data1 = data1
        self.data2 = data2

    def render(self, page_f):

        # write header
        with open(
            self.template_base_path + self.template + "_header.html", "r"
        ) as header_f:
            html_header = header_f.read()
            page_f.write(html_header)

        with open(
            self.template_base_path + self.template + "_footer.html", "r"
        ) as footer_f:
            page_f.write(footer_f.read() % (self.data1, self.data2))
