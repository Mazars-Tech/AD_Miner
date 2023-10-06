import json
import os
from datetime import datetime
from operator import add
from urllib.parse import quote

from ad_miner.sources.modules import rating
from ad_miner.sources.modules.smolcard_class import SmolCard, dico_category
from ad_miner.sources.modules.utils import DESCRIPTION_MAP, TEMPLATES_DIRECTORY


def getData(arguments, neo4j, domains, computers, users, objects, extract_date):
    # Place in this dict all the {{key}} from main_header.html with their respecting value
    data = {}

    def americanStyle(n: int) -> str:
        """
        Returns the number n with spaces between thousands, e.g. 1234 => 1 234
        """
        return '{:,}'.format(n).replace(',', ' ')

    # Header
    data["render_name"] = arguments.cache_prefix
    data["date"] = f"{extract_date[-2:]}/{extract_date[-4:-2]}/{extract_date[:4]}"

    # Stats on the left
    data["nb_domains"] = len(domains.domains_list)
    data["nb_domain_collected"] = len(neo4j.all_requests["nb_domain_collected"]["result"])
    if data["nb_domains"] > 1:
        data["domain_or_domains"] = "Domains"
    else:
        data["domain_or_domains"] = "Domain"
    data["nb_dc"] = americanStyle(len(domains.computers_nb_domain_controllers))
    data["nb_da"] = americanStyle(len(domains.users_nb_domain_admins))

    data["nb_users"] = americanStyle(len(users.users))
    data["nb_groups"] = americanStyle(len(domains.groups))

    data["nb_computers"] = americanStyle(len(computers.list_total_computers))
    data["nb_adcs"] = americanStyle(len(computers.computers_adcs))

    data["domain_names"] = [k[0] for k in domains.getUserComputersCountPerDomain()]
    data["users_per_domain"] = [k[1] for k in domains.getUserComputersCountPerDomain()]
    data["computers_per_domain"] = [
        k[2] for k in domains.getUserComputersCountPerDomain()
    ]

    return data


def get_raw_other_data(arguments):
    try:
        raw_other_list_data = []
        for file_name in os.listdir(arguments.evolution):
            with open(arguments.evolution + "/" + file_name, "r") as f:
                raw_other_list_data.append(json.load(f))
        return raw_other_list_data
    except Exception as e:
        print("Bug Evolution over time 😨 : ", e)
        return None


def complete_data_evolution_time(data, raw_other_list_data):
    data["label_evolution_time"] = []

    list_immediate_risk = []
    list_potential_risk = []
    list_minor_risk = []
    list_handled_risk = []
    list_not_evaluated_risk = []

    if raw_other_list_data != None:

        data["boolean_evolution_over_time"] = "block;"

        dico_data_evolution_time = {
            "nb_domains": [],
            "nb_dc": [],
            "nb_da": [],
            "nb_users": [],
            "nb_groups": [],
            "nb_computers": [],
        }

        for k in dico_category["passwords"]:
            dico_data_evolution_time[k] = []
        for k in dico_category["kerberos"]:
            dico_data_evolution_time[k] = []
        for k in dico_category["permission"]:
            dico_data_evolution_time[k] = []

        for k in range(len(raw_other_list_data)):
            value_immediate_risk = 0
            value_potential_risk = 0
            value_minor_risk = 0
            value_handled_risk = 0
            value_not_evaluated_risk = 0

            date_k = raw_other_list_data[k]["datetime"]
            data["label_evolution_time"].append(
                f"{date_k[-4:]}-{date_k[3:5]}-{date_k[:2]}"
            )

            dico_color_category = raw_other_list_data[k]["color_category"]
            for name_label in dico_color_category:
                if dico_color_category[name_label] == "red":
                    value_immediate_risk += 1
                elif dico_color_category[name_label] == "orange":
                    value_potential_risk += 1
                elif dico_color_category[name_label] == "yellow":
                    value_minor_risk += 1
                elif dico_color_category[name_label] == "green":
                    value_handled_risk += 1
                elif dico_color_category[name_label] == "grey":
                    value_not_evaluated_risk += 1

            list_immediate_risk.append(value_immediate_risk)
            list_potential_risk.append(value_potential_risk)
            list_minor_risk.append(value_minor_risk)
            list_handled_risk.append(value_handled_risk)
            list_not_evaluated_risk.append(value_not_evaluated_risk)

            for key in dico_data_evolution_time:
                if key in [
                    "nb_domains",
                    "nb_dc",
                    "nb_da",
                    "nb_users",
                    "nb_groups",
                    "nb_computers",
                ]:
                    dico_data_evolution_time[key].append(
                        raw_other_list_data[k]["general_statistic"][key]
                    )
                else:
                    if raw_other_list_data[k]["value"].get(key) != None:
                        dico_data_evolution_time[key].append(
                            raw_other_list_data[k]["value"][key]
                        )

        data["dico_data_evolution_time"] = dico_data_evolution_time
    else:
        data["boolean_evolution_over_time"] = "none"
        data["dico_data_evolution_time"] = {}

    data["value_evolution_time_immediate_risk"] = list_immediate_risk
    data["value_evolution_time_potential_risk"] = list_potential_risk
    data["value_evolution_time_minor_risk"] = list_minor_risk
    data["value_evolution_time_handled_risk"] = list_handled_risk
    data["value_not_evaluated_time_handled_risk"] = list_not_evaluated_risk

    return data


def create_dico_data(
    data, arguments, domains, computers, users, objects, dico_rating_color
):
    """
    This function creates the data dictionary which is saved in json in the client's report
    """
    dico_data = {
        "datetime": data["date"],
        "render_name": arguments.cache_prefix,
        "general_statistic": {
            "nb_domains": len(domains.domains_list),
            "nb_dc": len(domains.computers_nb_domain_controllers),
            "nb_da": len(domains.users_nb_domain_admins),
            "nb_users": len(users.users),
            "nb_groups": len(domains.groups),
            "nb_computers": len(computers.list_total_computers),
            "nb_adcs": len(computers.computers_adcs),
        },
    }

    dico_data["value"] = {
        "users_pwd_cleartext": len(users.users_pwd_cleartext) if users.users_pwd_cleartext else 0,
        "dc_impersonation": users.users_dc_impersonation_count if users.users_dc_impersonation_count else 0,
        "users_pwd_not_changed_since": len(domains.users_pwd_not_changed_since_3months) if domains.users_pwd_not_changed_since_3months else 0,
        "kerberoastables": len(users.users_kerberoastable_users) if users.users_kerberoastable_users else 0,
        "as_rep": len(users.users_kerberos_as_rep) if users.users_kerberos_as_rep else 0,
        "non-dc_with_unconstrained_delegations": len(
            computers.computers_non_dc_unconstrained_delegations
        ) if computers.computers_non_dc_unconstrained_delegations else 0,
        "non-dc_users_with_unconstrained_delegations": len(
            computers.users_non_dc_unconstrained_delegations
        ) if computers.users_non_dc_unconstrained_delegations else 0,
        "users_constrained_delegations": len(computers.users_constrained_delegations) if computers.users_constrained_delegations else 0,
        "krb_last_change": max(
            [dict["pass_last_change"] for dict in users.users_krb_pwd_last_set]
        ) if users.users_krb_pwd_last_set else 0,
        "users_admin_of_computers": len(users.users_admin_computer_count) if users.users_admin_computer_count else 0,
        "server_users_could_be_admin": users.servers_with_most_paths if users.servers_with_most_paths else 0,
        "dom_admin_on_non_dc": len(users.users_domain_admin_on_nondc) if users.users_domain_admin_on_nondc else 0,
        "nb_domain_admins": len(domains.users_nb_domain_admins) if domains.users_nb_domain_admins else 0,
        "users_shadow_credentials_to_non_admins": users.max_number_users_shadow_credentials_to_non_admins if users.max_number_users_shadow_credentials_to_non_admins else 0,
        "users_shadow_credentials": len(users.users_shadow_credentials_uniq) if users.users_shadow_credentials_uniq else 0,
        "can_dcsync": len(objects.can_dcsync_nodes) if objects.can_dcsync_nodes else 0,
        "computers_members_high_privilege": len(
            computers.computers_members_high_privilege_uniq
        ) if computers.computers_members_high_privilege_uniq else 0,
        "computers_admin_of_computers": computers.count_computers_admins if computers.count_computers_admins else 0,
        "graph_path_objects_to_da": len(list(set([item for sublist in domains.users_to_domain_admin.values() for item in sublist]))) if domains.users_to_domain_admin else 0,
        "computers_last_connexion": len(domains.computers_not_connected_since_60) if domains.computers_not_connected_since_60 else 0,
        "users_rdp_access": len(users.users_rdp_access_1) if users.users_rdp_access_1 else 0,
        "computers_list_of_rdp_users": len(users.users_rdp_access_2) if users.users_rdp_access_2 else 0,
        "never_expires": len(users.users_password_never_expires) if users.users_password_never_expires else 0,
        "dormants_accounts": len(domains.users_dormant_accounts) if domains.users_dormant_accounts else 0,
        "unpriv_to_dnsadmins": len(users.unpriv_to_dnsadmins) if users.unpriv_to_dnsadmins else 0,
        "objects_to_operators_member": len(users.objects_to_operators_member) if len(users.objects_to_operators_member) else 0,
        "computers_os_obsolete": len(computers.list_computers_os_obsolete) if computers.list_computers_os_obsolete else 0,
        "users_pwd_cleartext": len(users.users_pwd_cleartext) if users.users_pwd_cleartext else 0,
        "computers_without_laps": computers.stat_laps if computers.stat_laps else 0,
        "graph_path_objects_to_ou_handlers": domains.nb_starting_nodes_to_ous if domains.nb_starting_nodes_to_ous else 0,
        "vuln_functional_level": len(domains.vuln_functional_level) if domains.vuln_functional_level else 0,
        "graph_list_objects_rbcd": len(list(users.rbcd_graphs.keys())) if users.rbcd_graphs else 0,
        "vuln_permissions_adminsdholder": len(users.vuln_permissions_adminsdholder) if users.vuln_permissions_adminsdholder else 0,
        "objects_to_adcs": len(computers.ADCS_path_sorted.keys()) if computers.ADCS_path_sorted else 0,
        "users_GPO_access": domains.number_of_gpo if domains.number_of_gpo else 0,
        "da_to_da": domains.crossDomain,
        "can_read_gmsapassword_of_adm": len(users.can_read_gmsapassword_of_adm) if users.can_read_gmsapassword_of_adm else 0,
        "dangerous_path": domains.total_dangerous_paths,
        "users_password_not_required":len(users.users_password_not_required),
        "can_read_laps":len(users.can_read_laps_parsed),
        "group_anomaly_acl": users.number_group_ACL_anomaly,
        "empty_groups": len(domains.empty_groups),
        "empty_ous": len(domains.empty_ous),
        "has_sid_history": len(users.has_sid_history)
    }

    dico_data["color_category"] = dico_rating_color

    return dico_data


def render(
    arguments, neo4j, domains, computers, users, objects, data_rating, extract_date
):

    if arguments.evolution != "":
        raw_other_list_data = get_raw_other_data(arguments)
    else:
        raw_other_list_data = None

    data = getData(arguments, neo4j, domains, computers, users, objects, extract_date)

    dico_rating_color = rating.rating_color(data_rating)
    dico_data = create_dico_data(
        data, arguments, domains, computers, users, objects, dico_rating_color
    )

    if raw_other_list_data != None:
        raw_other_list_data.append(dico_data)

        raw_other_list_data_2 = []
        list_date_raw_other_list_data = [k["datetime"] for k in raw_other_list_data]
        dates_raw_other_list_data = [datetime.strptime(date, "%d/%m/%Y") for date in list_date_raw_other_list_data]
        dates_raw_other_list_data.sort()
        dates_raw_other_list_data = [datetime.strftime(date, "%d/%m/%Y") for date in dates_raw_other_list_data]
        for date_instance in dates_raw_other_list_data:
            for dico in raw_other_list_data:
                if dico["datetime"] == date_instance:
                    raw_other_list_data_2.append(dico)
                    break
        raw_other_list_data = raw_other_list_data_2

    data = complete_data_evolution_time(
        data, raw_other_list_data
    )  # for the chart evolution over time

    # TODO : corriger incohérence entre password not change > 1year and 3 months
    # dico_name_description = {
    #     "dc_impersonation": f"{users.users_dc_impersonation_count} paths to impersonate DCs",
    #     "users_pwd_not_changed_since": f"{len(domains.users_pwd_not_changed_since_3months)} unchanged passwords > {int((neo4j.password_renewal)/30)} months",
    #     "kerberoastables": f"{len(users.users_kerberoastable_users)} kerberoastable accounts",
    #     "as_rep": f"{len(users.users_kerberos_as_rep)} accounts are AS-REP-roastable",
    #     "non-dc_with_unconstrained_delegations": f"{len(computers.computers_non_dc_unconstrained_delegations)} non-DC with unconstrained delegations",
    #     "non-dc_users_with_unconstrained_delegations": f"{len(computers.users_non_dc_unconstrained_delegations)} users with unconstrained delegations",
    #     "users_constrained_delegations": f"{len(computers.users_constrained_delegations)} users with constrained delegations",
    #     "krb_last_change": f"krbtgt not updated in > {max([dict['pass_last_change'] for dict in users.users_krb_pwd_last_set])} days",
    #     "users_admin_of_computers": f"{len(users.users_admin_computer_count)} users with admin privs.",
    #     "server_users_could_be_admin": f"Up to {users.servers_with_most_paths} users could compromise a server",
    #     "dom_admin_on_non_dc": f"{len(users.users_domain_admin_on_nondc)} domain admin sessions on non-DC",
    #     "nb_domain_admins": f"{len(domains.users_nb_domain_admins)} domain admins",
    #     "users_shadow_credentials_to_non_admins": f"Users can be impersonated by up {users.max_number_users_shadow_credentials_to_non_admins} users",
    #     "users_shadow_credentials": f"{len(users.users_shadow_credentials_uniq)} users can impersonate privileged accounts",
    #     "can_dcsync": f"{len(objects.can_dcsync_nodes)} non DA/DC objects have DCSync privileges",
    #     "computers_members_high_privilege": f"{len(computers.computers_members_high_privilege_uniq)} computers with high privs.",
    #     "computers_admin_of_computers": f"{computers.count_computers_admins} computers admin of {computers.count_computers_admins_target} computers",
    #     "graph_path_objects_to_da": f"{len(domains.objects_to_domain_admin)} paths to DA",
    #     "computers_last_connexion": f"{len(domains.computers_not_connected_since_60)} ghost computers",
    #     "computers_list_of_rdp_users": f"{len(users.users_rdp_access_2)} computers with RDP access",
    #     "never_expires": f"{len(users.users_password_never_expires)} users w/o password expiration",
    #     "dormants_accounts": f"{len(domains.users_dormant_accounts)} dormant accounts",
    #     "unpriv_to_dnsadmins": f"{len(users.unpriv_to_dnsadmins)} paths to DNSAdmins group",
    #     "unpriv_to_backupoperators": f"{len(users.unpriv_to_backupoperators)} paths to Backup Operators group",
    #     "computers_os_obsolete": f"{len(computers.list_computers_os_obsolete)} computers with obsolete OS",
    #     "users_pwd_cleartext": f"{len(users.users_pwd_cleartext)} users with clear text password",
    #     "computers_without_laps": f"{computers.stat_laps} % computers without LAPS",
    #     "graph_path_objects_to_ou_handlers": f"{domains.nb_starting_nodes_to_ous} dangerous control paths over {domains.nb_ous_with_da} OUs",
    #     "vuln_functional_level": f"{len(domains.vuln_functional_level)} insufficient forest and domains functional levels",
    #     "vuln_permissions_adminsdholder": f"{len(users.vuln_permissions_adminsdholder)} paths to an AdminSDHolder container",
    #     "graph_list_objects_rbcd": f"{users.rbcd_nb_start_nodes} users can perform an RBCD attack on {users.rbcd_nb_end_nodes} computers",
    #     "objects_to_adcs": f"{len(computers.ADCS_path_sorted.keys())} ADCS servers can be compromised",
    #     "users_GPO_access": f"{domains.number_of_gpo} GPO can be exploited"
    # }

    dico_name_description = {
        "dc_impersonation": f"{dico_data['value']['dc_impersonation']} paths to impersonate DCs",
        "users_pwd_not_changed_since": f"{dico_data['value']['users_pwd_not_changed_since']} unchanged passwords > {int((neo4j.password_renewal)/30)} months",
        "kerberoastables": f"{dico_data['value']['kerberoastables']} kerberoastable accounts",
        "as_rep": f"{dico_data['value']['as_rep']} accounts are AS-REP-roastable",
        "non-dc_with_unconstrained_delegations": f"{dico_data['value']['non-dc_with_unconstrained_delegations']} non-DC with unconstrained delegations",
        "non-dc_users_with_unconstrained_delegations": f"{dico_data['value']['non-dc_users_with_unconstrained_delegations']} users with unconstrained delegations",
        "users_constrained_delegations": f"{dico_data['value']['users_constrained_delegations']} users with constrained delegations",
        "krb_last_change": f"krbtgt not updated in > {dico_data['value']['krb_last_change']} days",
        "users_admin_of_computers": f"{dico_data['value']['users_admin_of_computers']} users with admin privs.",
        "server_users_could_be_admin": f"Up to {dico_data['value']['server_users_could_be_admin']} users could compromise a server",
        "dom_admin_on_non_dc": f"{dico_data['value']['dom_admin_on_non_dc']} domain admin sessions on non-DC",
        "nb_domain_admins": f"{dico_data['value']['nb_domain_admins']} domain admins",
        "users_shadow_credentials_to_non_admins": f"Users can be impersonated by up {dico_data['value']['users_shadow_credentials_to_non_admins']} users",
        "users_shadow_credentials": f"{dico_data['value']['users_shadow_credentials']} users can impersonate privileged accounts",
        "can_dcsync": f"{dico_data['value']['can_dcsync']} non DA/DC objects have DCSync privileges",
        "computers_members_high_privilege": f"{dico_data['value']['computers_members_high_privilege']} computers with high privs.",
        "computers_admin_of_computers": f"{computers.count_computers_admins} computers admin of {computers.count_computers_admins_target} computers",
        "graph_path_objects_to_da": f"{len(list(set([item for sublist in domains.users_to_domain_admin.values() for item in sublist]))) if domains.users_to_domain_admin else 0} users have a path to DA",
        "computers_last_connexion": f"{dico_data['value']['computers_last_connexion']} ghost computers",
        "users_rdp_access": f"{dico_data['value']['users_rdp_access']} users with RDP access",
        "computers_list_of_rdp_users": f"{dico_data['value']['computers_list_of_rdp_users']} computers with RDP access",
        "never_expires": f"{dico_data['value']['never_expires']} users w/o password expiration",
        "dormants_accounts": f"{dico_data['value']['dormants_accounts']} dormant accounts",
        "unpriv_to_dnsadmins": f"{dico_data['value']['unpriv_to_dnsadmins']} paths to DNSAdmins group",
        "objects_to_operators_member": f"{dico_data['value']['objects_to_operators_member']} paths to Operator (Print, Server, Backup or Accounts) members",
        "computers_os_obsolete": f"{dico_data['value']['computers_os_obsolete']} computers with obsolete OS",
        "users_pwd_cleartext": f"{dico_data['value']['users_pwd_cleartext']} users with clear text password",
        "computers_without_laps": f"{dico_data['value']['computers_without_laps']} % computers without LAPS",
        "graph_path_objects_to_ou_handlers": f"{domains.nb_starting_nodes_to_ous} dangerous control paths over {domains.nb_ous_with_da} OUs",
        "vuln_functional_level": f"{dico_data['value']['vuln_functional_level']} insufficient forest and domains functional levels",
        "vuln_permissions_adminsdholder": f"{dico_data['value']['vuln_permissions_adminsdholder']} paths to an AdminSDHolder container",
        "graph_list_objects_rbcd": f"{users.rbcd_nb_start_nodes} users can perform an RBCD attack on {users.rbcd_nb_end_nodes} computers",
        "objects_to_adcs": f"{dico_data['value']['objects_to_adcs']} ADCS servers can be compromised",
        "users_GPO_access": f"{dico_data['value']['users_GPO_access']} GPO can be exploited",
        "da_to_da": f"{domains.crossDomain} paths between different DA",
        "can_read_gmsapassword_of_adm": f"{len(users.can_read_gmsapassword_of_adm)} can read GMSA passwords of Administrators",
        "dangerous_paths": f"More than {domains.total_dangerous_paths} dangerous paths to DA",
        "users_password_not_required":f"{dico_data['value']['users_password_not_required']} users can bypass your password policy",
        "can_read_laps":f"{len(users.can_read_laps_parsed)} accounts can read LAPS passwords",
        "group_anomaly_acl": f"{users.number_group_ACL_anomaly} groups with potential ACL anomalies",
        "empty_groups": f"{len(domains.empty_groups)} groups without any member",
        "empty_ous": f"{len(domains.empty_ous)} OUs without any member",
        "has_sid_history": f"{len(users.has_sid_history)} objects can exploit SID History"
    }

    descriptions = DESCRIPTION_MAP
    dico_name_title = {k: descriptions[k].get("title") for k in descriptions.keys()}


    # I didn't look at why the rating was returning duplicates, but it should be corrected rather than deleting the duplicates stupidly
    data["immediate_risk"] = len(data_rating[1])
    data["potential_risk"] = len(data_rating[2])
    data["minor_risk"] = len(data_rating[3])
    data["handled_risk"] = len(data_rating[4] + data_rating[5])

    data["immediate_risk_list"] = data_rating[1]
    data["potential_risk_list"] = data_rating[2]
    data["minor_risk_list"] = data_rating[3]
    data["handled_risk_list"] = data_rating[4] + data_rating[5]

    # This part has to be the worst code I've ever produced : need factorisation
    c_permissions = 0
    c_passwords = 0
    c_kerberos = 0
    data["permissions_data"] = []
    data["passwords_data"] = []
    data["kerberos_data"] = []
    for control in data["handled_risk_list"]:
        if control in dico_category["permission"]:
            c_permissions += 1
        elif control in dico_category["passwords"]:
            c_passwords += 1
        elif control in dico_category["kerberos"]:
            c_kerberos += 1
    if c_permissions > 1:
        data["permissions_graph_text"] = "vulnerabilities"
    else:
        data["permissions_graph_text"] = "vulnerability"
    if c_permissions > 0:
        data["permissions_letter_grade"] = "A"
        data["permissions_letter_color"] = "91, 180, 32"
        data[
            "permissions_graph_summary"
        ] = f"""
            <p><i class="bi bi-check-circle-fill" style="color: rgb(91, 180, 32); margin-right: 3px;"></i>
                <span>{c_permissions}</span> {data["permissions_graph_text"]}
            </p>"""
    data["permissions_data"] = [c_permissions] + data["permissions_data"]

    if c_passwords > 1:
        data["passwords_graph_text"] = "vulnerabilities"
    else:
        data["passwords_graph_text"] = "vulnerability"
    if c_passwords > 0:
        data["passwords_letter_grade"] = "A"
        data["passwords_letter_color"] = "91, 180, 32"
        data[
            "passwords_graph_summary"
        ] = f"""
            <p><i class="bi bi-check-circle-fill" style="color: rgb(91, 180, 32); margin-right: 3px;"></i>
                <span>{c_passwords}</span> {data["passwords_graph_text"]}
            </p>"""
    data["passwords_data"] = [c_passwords] + data["passwords_data"]

    if c_kerberos > 1:
        data["kerberos_graph_text"] = "vulnerabilities"
    else:
        data["kerberos_graph_text"] = "vulnerability"
    if c_kerberos > 0:
        data["kerberos_letter_grade"] = "A"
        data["kerberos_letter_color"] = "91, 180, 32"
        data[
            "kerberos_graph_summary"
        ] = f"""
            <p><i class="bi bi-check-circle-fill" style="color: rgb(91, 180, 32); margin-right: 3px;"></i>
                <span>{c_kerberos}</span> {data["kerberos_graph_text"]}
            </p>"""
    data["kerberos_data"] = [c_kerberos] + data["kerberos_data"]

    c_permissions = 0
    c_passwords = 0
    c_kerberos = 0
    for control in data["minor_risk_list"]:
        if control in dico_category["permission"]:
            c_permissions += 1
        elif control in dico_category["passwords"]:
            c_passwords += 1
        elif control in dico_category["kerberos"]:
            c_kerberos += 1
    if c_permissions > 1:
        data["permissions_graph_text"] = "vulnerabilities"
    else:
        data["permissions_graph_text"] = "vulnerability"
    if c_permissions > 0:
        data["permissions_letter_grade"] = "B"
        data["permissions_letter_color"] = "255, 221, 0"
        data[
            "permissions_graph_summary"
        ] = f"""
            <p><i class="bi bi-dash-circle-fill" style="color: rgb(255, 221, 0); margin-right: 3px;"></i>
                <span>{c_permissions}</span> minor {data["permissions_graph_text"]}
            </p>"""
    data["permissions_data"] = [c_permissions] + data["permissions_data"]

    if c_passwords > 1:
        data["passwords_graph_text"] = "vulnerabilities"
    else:
        data["passwords_graph_text"] = "vulnerability"
    if c_passwords > 0:
        data["passwords_letter_grade"] = "B"
        data["passwords_letter_color"] = "255, 221, 0"
        data[
            "passwords_graph_summary"
        ] = f"""
            <p><i class="bi bi-dash-circle-fill" style="color: rgb(255, 221, 0); margin-right: 3px;"></i>
                <span>{c_passwords}</span> minor {data["passwords_graph_text"]}
            </p>"""
    data["passwords_data"] = [c_passwords] + data["passwords_data"]

    if c_kerberos > 1:
        data["kerberos_graph_text"] = "vulnerabilities"
    else:
        data["kerberos_graph_text"] = "vulnerability"
    if c_kerberos > 0:
        data["kerberos_letter_grade"] = "B"
        data["kerberos_letter_color"] = "255, 221, 0"
        data[
            "kerberos_graph_summary"
        ] = f"""
            <p><i class="bi bi-dash-circle-fill" style="color: rgb(255, 221, 0); margin-right: 3px;"></i>
                <span>{c_kerberos}</span> minor {data["kerberos_graph_text"]}
            </p>"""
    data["kerberos_data"] = [c_kerberos] + data["kerberos_data"]

    c_permissions = 0
    c_passwords = 0
    c_kerberos = 0
    for control in data["potential_risk_list"]:
        if control in dico_category["permission"]:
            c_permissions += 1
        elif control in dico_category["passwords"]:
            c_passwords += 1
        elif control in dico_category["kerberos"]:
            c_kerberos += 1
    if c_permissions > 1:
        data["permissions_graph_text"] = "vulnerabilities"
    else:
        data["permissions_graph_text"] = "vulnerability"
    if c_permissions > 0:
        data["permissions_letter_grade"] = "C"
        data["permissions_letter_color"] = "245, 177, 75"
        data[
            "permissions_graph_summary"
        ] = f"""
            <p><i class="bi bi-exclamation-triangle-fill" style="color: rgb(245, 177, 75); margin-right: 3px;"></i>
                <span>{c_permissions}</span> major {data["permissions_graph_text"]}
            </p>"""
    data["permissions_data"] = [c_permissions] + data["permissions_data"]

    if c_passwords > 1:
        data["passwords_graph_text"] = "vulnerabilities"
    else:
        data["passwords_graph_text"] = "vulnerability"
    if c_passwords > 0:
        data["passwords_letter_grade"] = "C"
        data["passwords_letter_color"] = "245, 177, 75"
        data[
            "passwords_graph_summary"
        ] = f"""
            <p><i class="bi bi-exclamation-triangle-fill" style="color: rgb(245, 177, 75); margin-right: 3px;"></i>
                <span>{c_passwords}</span> major {data["passwords_graph_text"]}
            </p>"""
    data["passwords_data"] = [c_passwords] + data["passwords_data"]

    if c_kerberos > 1:
        data["kerberos_graph_text"] = "vulnerabilities"
    else:
        data["kerberos_graph_text"] = "vulnerability"
    if c_kerberos > 0:
        data["kerberos_letter_grade"] = "C"
        data["kerberos_letter_color"] = "245, 177, 75"
        data[
            "kerberos_graph_summary"
        ] = f"""
            <p><i class="bi bi-exclamation-triangle-fill" style="color: rgb(245, 177, 75); margin-right: 3px;"></i>
                <span>{c_kerberos}</span> major {data["kerberos_graph_text"]}
            </p>"""
    data["kerberos_data"] = [c_kerberos] + data["kerberos_data"]

    c_permissions = 0
    c_passwords = 0
    c_kerberos = 0
    for control in data["immediate_risk_list"]:
        if control in dico_category["permission"]:
            c_permissions += 1
        elif control in dico_category["passwords"]:
            c_passwords += 1
        elif control in dico_category["kerberos"]:
            c_kerberos += 1
    if c_permissions > 1:
        data["permissions_graph_text"] = "vulnerabilities"
    else:
        data["permissions_graph_text"] = "vulnerability"
    if c_permissions > 0:
        data["permissions_letter_grade"] = "D"
        data["permissions_letter_color"] = "245, 75, 75"
        data[
            "permissions_graph_summary"
        ] = f"""
            <p><i class="bi bi-exclamation-diamond-fill" style="color: rgb(245, 75, 75); margin-right: 3px;"></i>
                <span>{c_permissions}</span> critical {data["permissions_graph_text"]}
            </p>"""
    data["permissions_data"] = [c_permissions] + data["permissions_data"]

    if c_passwords > 1:
        data["passwords_graph_text"] = "vulnerabilities"
    else:
        data["passwords_graph_text"] = "vulnerability"
    if c_passwords > 0:
        data["passwords_letter_grade"] = "D"
        data["passwords_letter_color"] = "245, 75, 75"
        data[
            "passwords_graph_summary"
        ] = f"""
            <p><i class="bi bi-exclamation-diamond-fill" style="color: rgb(245, 75, 75); margin-right: 3px;"></i>
                <span>{c_passwords}</span> critical {data["passwords_graph_text"]}
            </p>"""
    data["passwords_data"] = [c_passwords] + data["passwords_data"]

    if c_kerberos > 1:
        data["kerberos_graph_text"] = "vulnerabilities"
    else:
        data["kerberos_graph_text"] = "vulnerability"
    if c_kerberos > 0:
        data["kerberos_letter_grade"] = "D"
        data["kerberos_letter_color"] = "245, 75, 75"
        data[
            "kerberos_graph_summary"
        ] = f"""
            <p><i class="bi bi-exclamation-diamond-fill" style="color: rgb(245, 75, 75); margin-right: 3px;"></i>
                <span>{c_kerberos}</span> critical {data["kerberos_graph_text"]}
            </p>"""
    data["kerberos_data"] = [c_kerberos] + data["kerberos_data"]

    if data["immediate_risk"] > 0:
        data[
            "global_rating"
        ] = """
            <div class="alert alert-danger d-flex align-items-center global-rating" role="alert">
                    <i class="bi bi-exclamation-diamond-fill rating-icon"></i>
                    <div class="rating-text">
                    CRITICAL
                    </div>
                </div>
        """
        data["main_letter_grade"] = "D"
        data["main_letter_color"] = "245, 75, 75"

    elif data["potential_risk"] > 0:
        data[
            "global_rating"
        ] = """
            <div class="alert alert-orange d-flex align-items-center global-rating" role="alert">
                    <i class="bi bi-exclamation-triangle-fill rating-icon"></i>
                    <div class="rating-text">
                    HIGH
                    </div>
                </div>
        """
        data["main_letter_grade"] = "C"
        data["main_letter_color"] = "245, 177, 75"

    elif data["minor_risk"] > 0:
        data[
            "global_rating"
        ] = """
            <div class="alert alert-yellow d-flex align-items-center global-rating" role="alert">
                    <i class="bi bi-dash-circle-fill rating-icon"></i>
                    <div class="rating-text">
                    LIMITED
                    </div>
                </div>
        """
        data["main_letter_grade"] = "B"
        data["main_letter_color"] = "255, 221, 0"

    else:
        data[
            "global_rating"
        ] = """
            <div class="alert alert-success d-flex align-items-center global-rating" role="alert">
                    <i class="bi bi-check-circle-fill rating-icon"></i>
                    <div class="rating-text">
                    SECURED
                    </div>
                </div>
        """
        data["main_letter_grade"] = "A"
        data["main_letter_color"] = "91, 180, 32"

    data["main_graph_data"] = list(
        map(
            add,
            data["permissions_data"],
            list(map(add, data["passwords_data"], data["kerberos_data"])),
        )
    )

    # cards of the right panel
    data["list_cards_dangerous_issues"] = ""
    red_status = "<i class='bi bi-exclamation-diamond-fill' style='color: rgb(245, 75, 75); margin-right: 3px;'></i> Immediate risk"
    for issue in data["immediate_risk_list"]:
        data[
            "list_cards_dangerous_issues"
        ] += f"""
            <a href="{issue}.html">
                <div class="card threat-card" custom-title="{dico_name_description[issue]}" custom-status="{red_status}">
                    <div class="card-body">
                        <h6 class="card-title">{dico_name_title[issue]}</h6>
                    </div>
                    <span class="position-absolute top-0 start-100 translate-middle p-2 border border-light rounded-circle"
                    style="background-color: rgb(245, 75, 75);">
                    </span>
                    </div>
            </a>
        """

    data["list_cards_alert_issues"] = ""
    orange_status = "<i class='bi bi-exclamation-triangle-fill' style='color: rgb(245, 177, 75); margin-right: 3px;'></i> Potential risk"
    for issue in data["potential_risk_list"]:
        data[
            "list_cards_alert_issues"
        ] += f"""
            <a href="{issue}.html">
                <div class="card threat-card" custom-title="{dico_name_description[issue]}" custom-status="{orange_status}">
                    <div class="card-body">
                        <h6 class="card-title">{dico_name_title[issue]}</h6>
                    </div>
                    <span class="position-absolute top-0 start-100 translate-middle p-2 border border-light rounded-circle"
                    style="background-color: rgb(245, 177, 75);">
                    </span>
                    </div>
            </a>
        """

    data["list_cards_minor_alert_issues"] = ""
    yellow_status = "<i class='bi bi-dash-circle-fill' style='color: rgb(255, 221, 0); margin-right: 3px;'></i> Minor risk"
    for issue in data["minor_risk_list"]:
        data[
            "list_cards_minor_alert_issues"
        ] += f"""
            <a href="{issue}.html">
                <div class="card threat-card" custom-title="{dico_name_description[issue]}" custom-status="{yellow_status}">
                    <div class="card-body">
                        <h6 class="card-title">{dico_name_title[issue]}</h6>
                    </div>
                    <span class="position-absolute top-0 start-100 translate-middle p-2 border border-light rounded-circle"
                    style="background-color: rgb(255, 221, 0);">
                    </span>
                    </div>
            </a>
        """

    # Vulnerability or vulnerabilities ? :D
    if data["immediate_risk"] > 1:
        data["vuln_text_immediate_risk"] = "vulnerabilities"
        data["issue_or_issues"] = "issues"
    else:
        data["vuln_text_immediate_risk"] = "vulnerability"
        data["issue_or_issues"] = "issue"

    if data["potential_risk"] > 1:
        data["vuln_text_major_risk"] = "vulnerabilities"
        data["alert_or_alerts"] = "Alerts"
    else:
        data["vuln_text_major_risk"] = "vulnerability"
        data["alert_or_alerts"] = "Alert"

    if data["minor_risk"] > 1:
        data["minor_alert_or_alerts"] = "Minor issues"
    else:
        data["minor_alert_or_alerts"] = "Minor issue"

    with open("./render_%s/html/index.html" % arguments.cache_prefix, "w") as page_f:
        with (TEMPLATES_DIRECTORY / "main_header.html").open(mode='r') as header_f:
            # This part extracts the {{something}} variables in the html template and replaces them with their value in the getData function
            # Every ` char will be skipped
            original = header_f.read()
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
                        content += str(data[key])
                    except KeyError:
                        content += "N/A"
                    i += len(key) + 4
                elif original[i] == "`":
                    i += 1
                else:
                    content += original[i]
                    i += 1

            page_f.write(content)

            # secondary = Page(arguments.cache_prefix, "cards", f"{arguments.cache_prefix} - {arguments.extract_date[-2:]}/{arguments.extract_date[-4:-2]}/{arguments.extract_date[:4]}", "Following data provide indicators to measure the cybersecurity risk exposure of your Active Directory infrastructure",include_js=["hide_cards"])
            # descriptions = json.load(open('description.json'))
            # print(rating_dic)
            cardsHtml = ""
            for k in data_rating.keys():
                for vuln in data_rating[k]:
                    if descriptions.get(vuln):
                        description = descriptions[vuln]["description"]
                    else:
                        description = vuln
                    cardsHtml += SmolCard(
                        id=vuln,
                        criticity=str(k),
                        href=f"{vuln}.html",
                        description=description,
                        details=dico_name_description.get(vuln),
                        evolution_data=data["dico_data_evolution_time"],
                        evolution_labels=data["label_evolution_time"]
                    ).render(page_f, return_html=True)
            modal_header = open(TEMPLATES_DIRECTORY / "cards_modal_header.html", "r").read()
            modal_footer = """
                  </div>
        </div>
      <div class="modal-footer">
      </div>
    </div>
  </div>
</div>
            """
            if arguments.evolution == "":
                modal_footer += "<script>document.querySelector('#flexSwitchCheckDefault').setAttribute('disabled', '');</script>"

            page_f.write(modal_header + cardsHtml + modal_footer)
            # html = secondary.returnHtml()

    with open(
        f"./render_{arguments.cache_prefix}/data_{arguments.cache_prefix}_{extract_date}.json",
        "w",
    ) as f:
        f.write(json.dumps(dico_data, indent=4))

    with open(f"./render_{arguments.cache_prefix}/js/main_circle.js", "a") as f_page:

        dico_js = {}

        # permission : top, passwords : left, kerberos : right
        dico_position = {
            "passwords": [
                [52, 25],
                [70, 17],
                [80, 40],
                [36, 12],
                [50, 10],
                [70, 30],
                [78, 24],
                [62, 8],
                [44, 17],
                [42, 25],
                [70, 41],
                [42, 5],
                [89, 38],
                [84, 30]
            ],
            "kerberos": [
                [60, 85],
                [90, 55],
                [48, 75],
                [81, 71],
                [70, 80],
                [70, 70],
                [40, 85],
                [72, 55],
                [80, 60],
            ],
            "permission": [
                [19, 65],
                [10, 30],
                [25, 20],
                [28, 60],
                [5, 50],
                [13, 42],
                [18, 80],
                [10, 66],
                [16, 20],
                [22, 14],
                [26, 75],
                [5, 38],
                [7, 58],
                [27, 36],
                [20, 30],
                [13, 53],
                [26, 48],
                [30, 25],
                [30, 68],
                [16, 72]
            ],
        }

        dico_position_instance = {"passwords": 0, "kerberos": 0, "permission": 0}

        for category in dico_category:
            for indicator in dico_category[category]:

                if dico_rating_color.get(indicator):
                    color = dico_rating_color[indicator]
                else:
                    color = "grey"

                dico_js[indicator] = {
                    "color": color,
                    "name": dico_name_title[indicator],
                    "link": quote(str(indicator)) + ".html",
                    "category": category,
                    "position": dico_position[category][
                        dico_position_instance[category]
                    ],
                    "title": dico_name_description[indicator]
                    if dico_name_description.get(indicator)
                    else indicator,
                }
                dico_position_instance[category] += 1

        string_dico = f"""\n var dico_entry = {json.dumps(dico_js)} \n
    display_all_hexagons(dico_entry);"""
        f_page.write(string_dico)

    return dico_name_description
