import re


class Line:
    def __init__(
        self, template="card", text=None, icon=None, href=None, color="secondary"
    ):
        self.template_base_path = "sources/html/components/card/"
        self.template = template
        self.text = text
        self.icon = icon
        self.href = href
        self.color = color
        if href:
            self.href = '<a class="cardLink text-secondary" href="%s"> %s </a>' % (
                href,
                "%s",
            )

    # 			self.href = '<a class="cardLink text-%s" href="%s" target="_blank"> %s </a>' % (color,href, '%s')

    @staticmethod
    def decorateTextNumbers(text):
        # 		print(text)
        # 		num_to_decorate = re.findall('(\d+[%]?)', text)
        num_to_decorate = re.findall("(\d+)", text)
        num_to_decorate += re.findall("([%])", text)
        # 		num_to_decorate += re.findall('%', text)
        # 		print(num_to_decorate)
        working_text = text
        for num in num_to_decorate:
            working_text = working_text.replace(
                num, '<span class="number">%s</span>' % (num)
            )
        return working_text

    def render(self, page_f):

        with open(
            self.template_base_path + self.template + "_line.html", "r"
        ) as line_f:
            html_line = line_f.read()
        if self.href:
            self.href = self.href % self.decorateTextNumbers(self.text)
            html_line = html_line % (self.icon, self.color, self.href)
        else:
            html_line = html_line % (
                self.icon,
                self.color,
                self.decorateTextNumbers(self.text),
            )
        page_f.write(html_line)
