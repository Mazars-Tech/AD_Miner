# row format : {key1 : {"value": value, "link":link}, key2 : value2}
from ad_miner.sources.modules.utils import HTML_DIRECTORY


class Grid:
    def __init__(self, title, template="grid", classes="thead-light"):
        self.template_base_path = HTML_DIRECTORY / "components/grid/"
        self.title = title
        self.template = template
        self.headers = []
        self.data = ""
        self.class_css = classes

    def addheader(self, header):
        self.headers.append(header)

    def setheaders(self, header):
        self.headers = header

    def getHeaders(self):
        return self.headers

    def setData(self, data):
        self.data = data

    def render(self, page_f):
        with open(self.template_base_path / (self.template + "_template.html"), "r") as grid_template:
            # Grid data that will be inserted in the template
            textToInsert = "var columnDefs = ["
            for header in self.headers:
                textToInsert += """{
                    field:\"%s\",
                    cellRenderer: function(params) {
                        if (typeof params.data[params.column.colId] === 'object') {
                            if (params.data[params.column.colId].value == \"0\") {
                                return params.data[params.column.colId].value;
                            }
                            if (params.data[params.column.colId].link == 'FALSE_LINK') {
                                params.data[params.column.colId] = '<p>' + params.data[params.column.colId].value + '</p>';
                                return params.data[params.column.colId];
                            }
                            if (params.data[params.column.colId].link != null) {
                                if (params.data[params.column.colId].before_link != null) {
                                    var prepend = params.data[params.column.colId].before_link;
                                }
                                else {
                                    var prepend = "";
                                }
                                params.data[params.column.colId] = prepend + '<a style="color: blue" target="_blank" href="' + params.data[params.column.colId].link + '">'+ params.data[params.column.colId].value + '</a>';
                                return params.data[params.column.colId];
                            }
                            return params.data[params.column.colId];
                        }
                        else {
                            return params.value;
                        }
                    },
                },""" % (header)

            textToInsert = textToInsert + "];\nvar rowData=%s;\n" % (self.data)

            template_contents = grid_template.read()

            new_contents = template_contents.replace("// DATA PLACEHOLDER", textToInsert)

            page_f.write(new_contents)
