import random
import string

from ad_miner.sources.modules.utils import HTML_DIRECTORY

class Table:
    def __init__(
        self,
        title,
        template="table",
        classes="thead-light",
    ):
        self.id = self.generateRandID()
        self.template_base_path = HTML_DIRECTORY / "components/table/"
        self.template = template
        self.title = title
        self.headers = []
        self.rows = []
        self.class_css = classes

    @staticmethod
    def generateRandID():
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for i in range(7))

    def addheader(self, header):
        self.headers.append(header)

    def setheaders(self, headers):
        self.headers = headers

    def addRow(self, row):
        self.rows.append(row)

    def setRows(self, rows):
        self.rows = rows

    def render(self, page_f):

        # write header
        with open(
            self.template_base_path / (self.template + "_header.html"), "r"
        ) as header_f:
            page_f.write(header_f.read() % (self.id, self.id, self.title, self.id))

        page_f.write('<thead class=" ' + self.class_css + ' ">\n<tr>\n')

        with open(
            self.template_base_path / (self.template + "_col.html"), "r"
        ) as row_header_f:
            line = row_header_f.read()

        for header in self.headers:
            page_f.write(line % ("th", 'scope="col"', header, "th"))

        page_f.write("</tr>\n</thead>\n<tbody>\n")

        for row in self.rows:

            page_f.write("<tr>\n")

            for index, col in enumerate(row):
                if index == 0:
                    page_f.write(line % ("th", 'scope="row"', col, "th"))
                else:
                    page_f.write(line % ("td", "", col, "td"))
            page_f.write("</tr>\n")

        page_f.write("</tbody>\n")
        with open(
            self.template_base_path / (self.template + "_footer.html"), "r"
        ) as footer_f:
            page_f.write(footer_f.read())
