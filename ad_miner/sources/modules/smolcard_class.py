import string
import json
from hashlib import md5


from ad_miner.sources.modules.utils import DESCRIPTION_MAP, HTML_DIRECTORY

dico_category = {
    "passwords": [
        "users_pwd_cleartext",
        "users_pwd_not_changed_since",
        "never_expires",
        "computers_without_laps",
        "can_read_gmsapassword_of_adm",
        "users_password_not_required",
        "can_read_laps",
    ],
    "kerberos": [
        "kerberoastables",
        "as_rep",
        "non-dc_with_unconstrained_delegations",
        "users_constrained_delegations",
        "krb_last_change",
        "graph_list_objects_rbcd",
        "users_shadow_credentials",
        "users_shadow_credentials_to_non_admins",
    ],
    "permission": [
        "users_admin_of_computers",
        "server_users_could_be_admin",
        "dom_admin_on_non_dc",
        "nb_domain_admins",
        "can_dcsync",
        "computers_members_high_privilege",
        "computers_admin_of_computers",
        "graph_path_objects_to_da",
        "users_rdp_access",
        "computers_list_of_rdp_users",
        "unpriv_to_dnsadmins",
        "objects_to_operators_member",
        "graph_path_objects_to_ou_handlers",
        "vuln_permissions_adminsdholder",
        "objects_to_adcs",
        "users_GPO_access",
        "da_to_da",
        "dangerous_paths",
        "group_anomaly_acl",
        "has_sid_history",
        "cross_domain_admin_privileges",
        "guest_accounts",
        "up_to_date_admincount",
        "privileged_accounts_outside_Protected_Users",
        "pre_windows_2000_compatible_access_group"
    ],
    "misc": [
        "computers_os_obsolete",
        "dormants_accounts",
        "dc_impersonation",
        "computers_last_connexion",
        "vuln_functional_level",
        "empty_groups",
        "empty_ous",
        "primaryGroupID_lower_than_1000"

    ]
}


class SmolCard:
    def __init__(
        self,
        template="smolcard",
        id=None,
        criticity=None,
        href=None,
        description=None,
        details=None,
        evolution_data={},
        evolution_labels=[]
    ):
        self.template_base_path = HTML_DIRECTORY / "components/smolcard/"
        self.template = template
        self.id = id
        self.title = ""
        self.criticity = criticity
        self.href = href
        self.description = description
        self.details = details
        self.evolution_data = evolution_data
        self.evolution_labels = evolution_labels

        self.category = "all"
        for category in dico_category:
            if self.id in dico_category[category]:
                self.category = category

        desc = DESCRIPTION_MAP
        self.title = desc[self.id].get("title")

    def fillTemplate(self, template_raw: str, dict_of_value: dict) -> str:
        """
        Fill the smolcard template with the data in dict_of_value.
        It extracts the {{something}} variables in the html template and replaces them with their value in the dict_of_value dictionnary.
        Every \` char will be skipped.
        """
        original = template_raw
        content = ""
        i = 0
        while i < len(original):
            if original[i] == "{" and original[i + 1] == "{":
                j = 2
                key = ""
                while original[i + j] != "}" and original[i + j + 1] != "}":
                    key += original[i + j]
                    j += 1
                key += original[i + j]
                try:
                    content += str(dict_of_value[key])
                except KeyError:
                    content += "N/A"
                i += len(key) + 4
            elif original[i] == "`":
                i += 1
            else:
                content += original[i]
                i += 1
        return content

    def render(self, page_f, return_html=False):
        color = ""

        if self.criticity == "-1":
            color = "secondary"
            hexa_color = "grey"
            rgb_color = "50, 50, 50"
            # self.criticity = "N/A"
            self.description = "IoE was not controlled."
        elif self.criticity == "1":
            hexa_color = "red"
            color = "danger"
            rgb_color = "245, 75, 75"
        elif self.criticity == "2":
            hexa_color = "orange"
            color = "warning"
            rgb_color = "245, 177, 75"
        elif self.criticity == "3":
            hexa_color = "yellow"
            color = "alert"
            rgb_color = "255, 221, 0"
        elif self.criticity == "4":
            hexa_color = "green"
            color = "success"
            rgb_color = "91, 180, 32"
        elif self.criticity == "5":
            hexa_color = "green"
            color = "success"
            rgb_color = "91, 180, 32"
        else:
            hexa_color = "grey"
            color = "secondary"
            rgb_color = "50, 50, 50"

        with open(
            self.template_base_path / (self.template + "_header.html"), "r"
        ) as line_f:
            html_raw = line_f.read()

        startedDollars = False
        startedDigits = False
        tmp_details = ""
        for char in self.details:
            if char == "$":
                # Toggle the in_dollars flag but don't add the dollar to the output
                startedDollars = not startedDollars
                # If we end a digit sequence because of a dollar, we close the tag
                if startedDigits:
                    tmp_details += "</b>"
                    startedDigits = False
                continue
            
            if not startedDollars and not startedDigits and char in string.digits:
              tmp_details += "<b class='number-in-details'>"
              startedDigits = True

            if startedDigits and char not in string.digits:
                tmp_details += "</b>"
                startedDigits = False

            tmp_details += char

        # Add closing tag if the string ends with a number
        if startedDigits:
            tmp_details += "</b>"

        if len(self.description) > 150:
            self.description_reduced = self.description[:150] + "..."
        else:
            self.description_reduced = self.description
            self.description = ""

        try:
            evolution_chart_data = self.evolution_data[self.id]
        except KeyError:
            evolution_chart_data = []

        template_data = {
            "category": self.category,
            "hexa_color": hexa_color,
            "color": color,
            "href": self.href,
            "title": self.title,
            "description": self.description,
            "description_reduced": self.description_reduced,
            "details": self.details,
            "id": md5(self.description_reduced.encode('utf-8')).hexdigest()[:8],
            "rgb_color": rgb_color,
            "evolution_chart_data": evolution_chart_data,
            "evolution_labels": self.evolution_labels
        }

        html_line = self.fillTemplate(html_raw, template_data)

        if not return_html:
            page_f.write(html_line)
        else:
            return html_line
