from ad_miner.sources.modules.line_class import Line
from ad_miner.sources.modules.table_class import Table
from ad_miner.sources.modules.utils import HTML_DIRECTORY


class Card:
    def __init__(
        self,
        template="card",
        title=None,
        icon=None,
        table=None,
        color="cardHeaderMazGrey",
    ):
        self.template_base_path = HTML_DIRECTORY / "components/card/"
        self.template = template
        self.title = title
        self.icon = icon
        self.lines = []
        self.table = table
        self.color = color

    def addLine(self, text, icon, href=None, color="secondary"):
        line = Line(text=text, icon=icon, href=href, color=color)
        self.lines.append(line)

    def setTable(self, title, headers, rows):
        self.table = Table(title)
        self.table.setheaders(headers)
        self.table.setRows(rows)

    def render(self, page_f):

        # write header
        with open(
            self.template_base_path / (self.template + "_header.html"), "r"
        ) as header_f:
            html_header = header_f.read()
            page_f.write(html_header % (self.color, self.title, self.icon))

        for line in self.lines:
            line.render(page_f)

        if self.table:
            page_f.write("\n</div>\n")
            self.table.render(page_f)

        with open(
            self.template_base_path / (self.template + "_footer.html"), "r"
        ) as footer_f:
            page_f.write(footer_f.read())
