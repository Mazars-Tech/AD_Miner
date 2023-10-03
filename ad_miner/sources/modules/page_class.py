import json
from ad_miner.sources.modules.utils import DESCRIPTION_MAP, TEMPLATES_DIRECTORY, JS_DIRECTORY

class Page:
    def __init__(
        self,
        render_prefix,
        name,
        title,
        description,
        template_file="base",
        include_js=[],
    ):
        self.render_prefix = render_prefix
        self.name = name + ".html"
        self.template = template_file
        self.title = title
        self.include_js = include_js

        try:
            self.description = DESCRIPTION_MAP[description]
        except:  # A supprimer quand toutes les descriptions auront été changées
            self.description = DESCRIPTION_MAP["template"]
            print(
                "[!] Warning : Add a description in description.json for the key '%s'."
                % (description)
            )
        self.components = []

    def addComponent(self, component):
        self.components.append(component)

    # TODO remove magic string foldername
    def render(self):

        # shutil.copyfile(self.template + "_header", "./render/" +  os.path.basename(self.template + ))

        with open(
            "./render_%s/html/%s" % (self.render_prefix, self.name), "w", encoding='utf-8'
        ) as page_f:
            with open(
                TEMPLATES_DIRECTORY / (self.template + "_header.html"), "r", encoding='utf-8'
            ) as header_f:
                page_f.write(
                    header_f.read()
                    % (
                        self.title,
                        self.description["description"],
                        self.description["risk"],
                        self.description["poa"],
                    )
                )

            for component in self.components:
                component.render(page_f)

            for jsFile in self.include_js:
                # open jsFile and write content to page_f in a <script> block
                with open(JS_DIRECTORY / (jsFile + ".js"), "r") as js_f:
                    page_f.write("<script>%s</script>" % js_f.read())

            with open(
                TEMPLATES_DIRECTORY / (self.template + "_footer.html"), "r"
            ) as footer_f:
                page_f.write(footer_f.read())
