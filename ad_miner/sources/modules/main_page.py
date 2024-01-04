import json
import os
from datetime import datetime
from operator import add
from urllib.parse import quote
from numpy import pi, cos, sin, linspace
from random import randint

from ad_miner.sources.modules import rating
from ad_miner.sources.modules.smolcard_class import SmolCard, dico_category, dico_category_invert, category_repartition_dict
from ad_miner.sources.modules.utils import DESCRIPTION_MAP, TEMPLATES_DIRECTORY


def getData(arguments, neo4j, domains, computers, users, objects, azure, extract_date):
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
    OS_repartition = sorted(computers.all_os.items(), key=lambda x: x[1], reverse=True)
    data["os_labels"] = [os_rep[0] for os_rep in OS_repartition]
    data["os_repartition"] = [os_rep[1] for os_rep in OS_repartition]

    base_colors = ['rgb(255, 123, 0)', 'rgb(255, 149, 0)', 'rgb(255, 170, 0)', 'rgb(255, 195, 0)', 'rgb(255, 221, 0)']
    i = 0
    data["os_colors"] = []
    for os in data["os_labels"]:
        if os in computers.obsolete_os_list:
            data["os_colors"].append('rgb(139, 0, 0)')
        else:
            data["os_colors"].append(base_colors[i])
            i = (i + 1) % len(base_colors)

    data["azure_nb_users"]= len(azure.azure_users)
    data["azure_nb_admin"]= len(azure.azure_admin)
    data["azure_nb_groups"]= len(azure.azure_groups)
    data["azure_nb_vm"]= len(azure.azure_vm)


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

    list_immediate_risk = {"on_premise":[], "azure":[]}
    list_potential_risk = {"on_premise":[], "azure":[]}
    list_minor_risk = {"on_premise":[], "azure":[]}
    list_handled_risk = {"on_premise":[], "azure":[]}
    list_not_evaluated_risk = {"on_premise":[], "azure":[]}

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

        # Initialize evolution data for on premise and azure
        for category in dico_category.keys():
            for k in dico_category[category]:
                dico_data_evolution_time[k] = []

        for k in range(len(raw_other_list_data)):
            
            date_k = raw_other_list_data[k]["datetime"]
            data["label_evolution_time"].append(
                f"{date_k[-4:]}-{date_k[3:5]}-{date_k[:2]}"
            )

            dico_color_category_origin = raw_other_list_data[k]["color_category"]

            dico_color_category = {"on_premise":{}, "azure":{}}
            for key in dico_color_category_origin:
                category_repartition = category_repartition_dict[dico_category_invert[key]]
                dico_color_category[category_repartition][key] = dico_color_category_origin[key]


            value_immediate_risk = {"on_premise":0, "azure":0}
            value_potential_risk = {"on_premise":0, "azure":0}
            value_minor_risk = {"on_premise":0, "azure":0}
            value_handled_risk = {"on_premise":0, "azure":0}
            value_not_evaluated_risk = {"on_premise":0, "azure":0}

            for name_label in dico_color_category_origin:

                for key in [*dico_category]:
                    for value_instance in range(len(dico_category[key])):
                        if dico_category[key][value_instance] == name_label:
                            category_repartition  = category_repartition_dict[key]

                if dico_color_category[category_repartition][name_label] == "red":
                    value_immediate_risk[category_repartition] += 1
                elif dico_color_category[category_repartition][name_label] == "orange":
                    value_potential_risk[category_repartition] += 1
                elif dico_color_category[category_repartition][name_label] == "yellow":
                    value_minor_risk[category_repartition] += 1
                elif dico_color_category[category_repartition][name_label] == "green":
                    value_handled_risk[category_repartition] += 1
                elif dico_color_category[category_repartition][name_label] == "grey":
                    value_not_evaluated_risk[category_repartition] += 1

            for category_repartition in ["on_premise", "azure"]:
                list_immediate_risk[category_repartition].append(value_immediate_risk[category_repartition])
                list_potential_risk[category_repartition].append(value_potential_risk[category_repartition])
                list_minor_risk[category_repartition].append(value_minor_risk[category_repartition])
                list_handled_risk[category_repartition].append(value_handled_risk[category_repartition])
                list_not_evaluated_risk[category_repartition].append(value_not_evaluated_risk[category_repartition])

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

    data["value_evolution_time_immediate_risk"] = list_immediate_risk["on_premise"]+list_immediate_risk["azure"]
    data["value_evolution_time_potential_risk"] = list_potential_risk["on_premise"]+list_potential_risk["azure"]
    data["value_evolution_time_minor_risk"] = list_minor_risk["on_premise"]+list_potential_risk["azure"]
    data["value_evolution_time_handled_risk"] = list_handled_risk["on_premise"]+list_potential_risk["azure"]
    data["value_not_evaluated_time_handled_risk"] = list_not_evaluated_risk["on_premise"]+list_potential_risk["azure"]

    return data


def create_dico_data(
    data, arguments, domains, computers, users, objects, azure, dico_rating_color
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
        "azure":  {
            "azure_nb_users": len(azure.azure_users),
            "azure_nb_admin": len(azure.azure_admin),
            "azure_nb_groups": len(azure.azure_groups),
            "azure_nb_vm": len(azure.azure_vm),
        }
    }

    dico_data["value"] = {
        #On-premise
        "users_pwd_cleartext": len(users.users_pwd_cleartext) if users.users_pwd_cleartext else 0,
        "dc_impersonation": users.users_dc_impersonation_count if users.users_dc_impersonation_count else 0,
        "users_pwd_not_changed_since": len(domains.users_pwd_not_changed_since_3months) if domains.users_pwd_not_changed_since_3months else 0,
        "kerberoastables": len(users.users_kerberoastable_users) if users.users_kerberoastable_users else 0,
        "as_rep": len(users.users_kerberos_as_rep) if users.users_kerberos_as_rep else 0,
        "non-dc_with_unconstrained_delegations": len(
            domains.kud_list
        ) if domains.kud_list else 0,
        "users_constrained_delegations": len(computers.users_constrained_delegations) if computers.users_constrained_delegations else 0,
        "krb_last_change": max([dict["pass_last_change"] for dict in users.users_krb_pwd_last_set], default=0),
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
        "anomaly_acl": users.number_group_ACL_anomaly,
        "empty_groups": len(domains.empty_groups),
        "empty_ous": len(domains.empty_ous),
        "has_sid_history": len(users.has_sid_history),
        "cross_domain_admin_privileges":domains.cross_domain_total_admin_accounts,
        "guest_accounts": len([ude for ude in users.guest_accounts if ude[-1]]),
        "unpriviledged_users_with_admincount": len(users.unpriviledged_users_with_admincount),
        "priviledge_users_without_admincount": len([dic for dic in users.users_nb_domain_admins if not dic["admincount"]]),
        "privileged_accounts_outside_Protected_Users": len([dic for dic in users.users_nb_domain_admins if "Protected Users" not in dic["admin type"]]),
        "rid_singularities": users.rid_singularities,
        "pre_windows_2000_compatible_access_group": len(users.pre_windows_2000_compatible_access_group),
        "up_to_date_admincount": len(users.unpriviledged_users_with_admincount) + len([dic for dic in users.users_nb_domain_admins if not dic["admincount"]]),
        "fgpp": len(users.fgpps),

        # Azure
        "azure_users_paths_high_target": len(azure.azure_users_paths_high_target),
        "azure_ms_graph_controllers": len(azure.azure_ms_graph_controllers),
        "azure_aadconnect_users": len(azure.azure_aadconnect_users),
        "azure_admin_on_prem": len(azure.azure_admin_on_prem),
        "azure_roles": len(azure.azure_roles_entry_nodes),
        "azure_reset_passwd": len(azure.reset_passwd.keys()),
        "azure_last_passwd_change": len(azure.azure_last_passwd_change_strange),
        "azure_dormant_accounts": len(azure.azure_dormant_accounts_90_days),
        "azure_accounts_disabled_on_prem": len(azure.azure_accounts_disabled_on_prem),
        "azure_accounts_not_found_on_prem": len(azure.azure_accounts_not_found_on_prem),
        "azure_cross_ga_da": azure.azure_total_cross_ga_da_compromission
    }
    dico_data["color_category"] = {**dico_rating_color["on_premise"],**dico_rating_color["azure"]}

    return dico_data

#Elem 1 singular, Elem2 plural
def manage_plural(elem, text):
    if elem > 1:
        return text[1]
    return text[0]


def get_hexagons_pos(n_hexagons: int, angle_start: float, angle_end: float) -> list[list[float]]:
    angle_and_pos = []
    hex_offset_v = -3.5  # Offset to compensate hexagon height
    hex_offset_h = -2.5  # Offset to compensate hexagon width


    # harcoded values of concentric arcs for hexagon placement
    arc_distances = [27.5, 35.3, 43.5]

    n_arcs = len(arc_distances)
    angle = angle_end - angle_start
    arcs_lengths = [angle * arc_distance for arc_distance in arc_distances]
    total_length = sum(arcs_lengths)

    hex_per_arc = [int(n_hexagons * le / total_length) for le in arcs_lengths]
    if sum(hex_per_arc) < n_hexagons:
        hex_per_arc[-2] += 1
    while sum(hex_per_arc) < n_hexagons:
        hex_per_arc[-1] += 1

    for i in range(n_arcs):
        to_place = hex_per_arc[i]
        if to_place == 0:
            continue

        rad = arc_distances[i]
        d_theta = angle / to_place
        angles = [angle_start + (i + 0.5) * d_theta for i in range(to_place)]
        for j in range(to_place):

            left = round(50 + rad * cos(angles[j]) + hex_offset_h, 2)
            top = round(50 - rad * sin(angles[j]) + hex_offset_v, 2)

            current_angle = angles[j] - angle_start
            angle_and_pos.append((current_angle, top, left))

    angle_and_pos.sort(key=lambda x: x[0])

    hex_pos = [(top, left) for angle, top, left in angle_and_pos]

    return hex_pos




def render(
    arguments, neo4j, domains, computers, users, objects, azure, data_rating, extract_date
):

    if arguments.evolution != "":
        raw_other_list_data = get_raw_other_data(arguments)
    else:
        raw_other_list_data = None

    data = getData(arguments, neo4j, domains, computers, users, objects, azure, extract_date)

    dico_rating_color = rating.rating_color(data_rating)

    dico_data = create_dico_data(
        data, arguments, domains, computers, users, objects, azure, dico_rating_color
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

    dico_name_description = {
        "dc_impersonation": f"{dico_data['value']['dc_impersonation']} paths to impersonate DCs",
        "users_pwd_not_changed_since": f"{dico_data['value']['users_pwd_not_changed_since']} unchanged passwords > {int((neo4j.password_renewal)/30)} months",
        "kerberoastables": f"{dico_data['value']['kerberoastables']} kerberoastable accounts",
        "as_rep": f"{dico_data['value']['as_rep']} accounts are AS-REP-roastable",
        "non-dc_with_unconstrained_delegations": f"{dico_data['value']['non-dc_with_unconstrained_delegations']} objects with unconstrained delegations",
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
        "can_read_laps": f"{len(users.can_read_laps_parsed)} accounts can read LAPS passwords",
        "anomaly_acl": f"{users.number_group_ACL_anomaly} groups with potential ACL anomalies",
        "empty_groups": f"{len(domains.empty_groups)} groups without any member",
        "empty_ous": f"{len(domains.empty_ous)} OUs without any member",
        "has_sid_history": f"{len(users.has_sid_history)} objects can exploit SID History",
        "cross_domain_admin_privileges": f"{dico_data['value']['cross_domain_admin_privileges']} accounts have cross-domain admin privileges",
        "guest_accounts": f"{dico_data['value']['guest_accounts']} guests accounts are enabled",
        "up_to_date_admincount": f"{dico_data['value']['priviledge_users_without_admincount']} priviledged accounts without admincount and {dico_data['value']['unpriviledged_users_with_admincount']} unpriviledged accounts with admincount",
        "privileged_accounts_outside_Protected_Users": f"{dico_data['value']['privileged_accounts_outside_Protected_Users']} priviledged accounts not in Protected Users group",
        "primaryGroupID_lower_than_1000": f"{dico_data['value']['rid_singularities']} accounts with unknown RIDs or unexpected names",
        "pre_windows_2000_compatible_access_group": f"{len(users.pre_windows_2000_compatible_access_group)} inadequate membership users in Pre-Win $2000$ Compatible Access group",
        "fgpp": f"{len(users.fgpps)} FGPP defined",

        #azure
        "azure_users_paths_high_target": f"{len(azure.azure_users_paths_high_target)} Users with a Path to High Value Targets",
        "azure_ms_graph_controllers": f"{len(azure.azure_ms_graph_controllers)} paths to MS Graph controllers",
        "azure_aadconnect_users": f"{len(azure.azure_aadconnect_users)} users with AADConnect session",
        "azure_admin_on_prem": f"{len(azure.azure_admin_on_prem)} admins on Azure and on premise",
        "azure_roles": f"{len(azure.azure_roles_entry_nodes)} users have access to Azure roles",
        "azure_reset_passwd": f"{len(azure.reset_passwd.keys())} users can reset passwords",
        "azure_last_passwd_change": f"{len(azure.azure_last_passwd_change_strange)} users have unusual last password change",
        "azure_dormant_accounts": f"{len(azure.azure_dormant_accounts_90_days)} dormant accounts",
        "azure_accounts_disabled_on_prem": f"{len(azure.azure_accounts_disabled_on_prem)} Azure accounts are disabled on prem.",
        "azure_accounts_not_found_on_prem": f"{len(azure.azure_accounts_not_found_on_prem)} Azure accounts are non-existant on prem.",
        "azure_cross_ga_da": f"{azure.azure_total_cross_ga_da_compromission} domain{'s' if azure.azure_total_cross_ga_da_compromission > 1 else ''} & tenant{'s' if azure.azure_total_cross_ga_da_compromission > 1 else ''} are cross compromisable"
    }

    descriptions = DESCRIPTION_MAP
    dico_name_title = {k: descriptions[k].get("title") for k in descriptions.keys()}

    data["boolean_azure"] = "inline" if neo4j.boolean_azure else "none"

    # On premise
    data["on_premise"] = {}

    data["on_premise"]["immediate_risk"] = len(data_rating["on_premise"][1])
    data["on_premise"]["potential_risk"] = len(data_rating["on_premise"][2])
    data["on_premise"]["minor_risk"] = len(data_rating["on_premise"][3])
    data["on_premise"]["handled_risk"] = len(data_rating["on_premise"][4] + data_rating["on_premise"][5])

    data["on_premise"]["immediate_risk_list"] = data_rating["on_premise"][1]
    data["on_premise"]["potential_risk_list"] = data_rating["on_premise"][2]
    data["on_premise"]["minor_risk_list"] = data_rating["on_premise"][3]
    data["on_premise"]["handled_risk_list"] = data_rating["on_premise"][4] + data_rating["on_premise"][5]

    # Azure
    data["azure"] = {}

    data["azure"]["immediate_risk"] = len(data_rating["azure"][1])
    data["azure"]["potential_risk"] = len(data_rating["azure"][2])
    data["azure"]["minor_risk"] = len(data_rating["azure"][3])
    data["azure"]["handled_risk"] = len(data_rating["azure"][4] + data_rating["azure"][5])

    data["azure"]["immediate_risk_list"] = data_rating["azure"][1]
    data["azure"]["potential_risk_list"] = data_rating["azure"][2]
    data["azure"]["minor_risk_list"] = data_rating["azure"][3]
    data["azure"]["handled_risk_list"] = data_rating["azure"][4] + data_rating["azure"][5]

    global_risk_controls = {
        "immediate_risk":  {"code" :"D", "colors": "245, 75, 75", "i_class": 'bi bi-exclamation-diamond-fill', "div_class": "danger", "panel_key": "list_cards_dangerous_issues", "risk_name": "Critical"},
        "potential_risk":  {"code" :"C", "colors": "245, 177, 75", "i_class": 'bi bi-exclamation-triangle-fill', "div_class": "orange", "panel_key": "list_cards_alert_issues", "risk_name": "Major"},
        "minor_risk":      {"code" :"B", "colors": "255, 221, 0", "i_class": 'bi bi-dash-circle-fill', "div_class": "yellow", "panel_key": "list_cards_minor_alert_issues", "risk_name": "Minor"},
        "handled_risk":    {"code" :"A", "colors": "91, 180, 32", "i_class": 'bi bi-check-circle-fill', "div_class": "success", "panel_key": "", "risk_name": ""}
    }
    data["on_premise"]["permissions_data"] = []
    data["on_premise"]["passwords_data"] = []
    data["on_premise"]["kerberos_data"] = []
    data["on_premise"]["misc_data"] = []

    #azure
    data["azure"]["az_permissions_data"] = []
    data["azure"]["az_passwords_data"] = []
    data["azure"]["az_misc_data"] = []
    data["azure"]["ms_graph_data"] = []

    data["on_premise"]["global_rating"] = ""
    data["azure"]["global_rating"] = ""

    for category_repartition in ["on_premise", "azure"]:
        for risk_control in global_risk_controls:

            if category_repartition == "on_premise":  # on premise
                categories = {"permissions": 0, "passwords": 0, "kerberos": 0, "misc": 0}

                for control in data["on_premise"][f"{risk_control}_list"]:

                    for category in categories.keys():
                        if control in dico_category[category]:
                            categories[category] += 1

            else:   # azure
                categories = {"az_permissions": 0, "az_passwords": 0, "az_misc": 0, "ms_graph": 0}

                for control in data["azure"][f"{risk_control}_list"]:

                    for category in categories.keys():
                        if control in dico_category[category]:
                            categories[category] += 1

            for category in categories:
                if categories[category] > 0 and f"{category}_letter_grade" not in data[category_repartition]:
                    data[category_repartition][f"{category}_letter_grade"] = global_risk_controls[risk_control]["code"]
                    data[category_repartition][f"{category}_letter_color"] = global_risk_controls[risk_control]["colors"]
                    data[category_repartition][
                        f"{category}_graph_summary"
                    ] = f"""
                        <p><i class="{global_risk_controls[risk_control]["i_class"]}" style="color: rgb({global_risk_controls[risk_control]["colors"]}); margin-right: 3px;"></i>
                            <span>{categories[category]}</span> {global_risk_controls[risk_control]["risk_name"]} {manage_plural(categories[category], ("Vulnerability", "Vulnerabilities"))}
                        </p>"""
                data[category_repartition][f"{category}_data"].append(categories[category])

            # Setting global risk info
            if not data[category_repartition]["global_rating"] and data[category_repartition][risk_control] > 0:
                data[category_repartition]["global_rating"] = f"""
                    <div class="alert alert-{global_risk_controls[risk_control]["div_class"]} d-flex align-items-center global-rating" role="alert">
                            <i class="{global_risk_controls[risk_control]["i_class"]} rating-icon"></i>
                            <div class="rating-text">
                            {global_risk_controls[risk_control]["risk_name"].upper()}
                            </div>
                        </div>
                """
                data[category_repartition]["main_letter_grade"] = global_risk_controls[risk_control]["code"]
                data[category_repartition]["main_letter_color"] = global_risk_controls[risk_control]["colors"]

            # Creating cards of the right panel
            if (global_risk_controls[risk_control]["panel_key"]):
                data[category_repartition][global_risk_controls[risk_control]["panel_key"]] = ""
                red_status = f"""<i class='{global_risk_controls[risk_control]["i_class"]}' style='color: rgb({global_risk_controls[risk_control]["colors"]}); margin-right: 3px;'></i> {risk_control.replace("_", " ").capitalize()}"""
                for issue in data[category_repartition][f"{risk_control}_list"]:
                    custom_title = dico_name_description[issue].replace("$", "")
                    data[category_repartition][
                        global_risk_controls[risk_control]["panel_key"]
                    ] += f"""
                        <a href="{issue}.html">
                            <div class="card threat-card" custom-title="{custom_title}" custom-status="{red_status}">
                                <div class="card-body">
                                    <h6 class="card-title">{dico_name_title[issue]}</h6>
                                </div>
                                <span class="position-absolute top-0 start-100 translate-middle p-2 border border-light rounded-circle"
                                style="background-color: rgb({global_risk_controls[risk_control]["colors"]});">
                                </span>
                                </div>
                        </a>
                    """

        data[category_repartition]["issue_or_issues"] = manage_plural(data[category_repartition]["immediate_risk"], ("issue", "issues"))
        data[category_repartition]["vuln_text_major_risk"] = manage_plural(data[category_repartition]["potential_risk"], ("vulnerability", "vulnerabilities"))
        data[category_repartition]["alert_or_alerts"] = manage_plural(data[category_repartition]["potential_risk"], ("Alert", "Alerts"))
        data[category_repartition]["minor_alert_or_alerts"] = manage_plural(data[category_repartition]["minor_risk"], ("Minor issue", "Minor issues"))

    data["on_premise"]["main_graph_data"] = [l1 + l2 + l3 + l4 for l1, l2, l3, l4 in zip(data["on_premise"]["permissions_data"], data["on_premise"]["kerberos_data"], data["on_premise"]["passwords_data"], data["on_premise"]["misc_data"])]
    data["azure"]["main_graph_data"] = [l1 + l2 + l3 + l4 for l1, l2, l3, l4 in zip(data["azure"]["ms_graph_data"], data["azure"]["az_permissions_data"], data["azure"]["az_passwords_data"], data["azure"]["az_misc_data"])]


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
                        if "on_premise|" in key:
                            content += str(data["on_premise"][key.split("on_premise|")[1]])

                        elif "azure|" in key:
                            content += str(data["azure"][key.split("azure|")[1]])
                        else:
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
            for category_repartition in ["on_premise", "azure"]:
                for k in data_rating[category_repartition].keys():
                    for vuln in data_rating[category_repartition][k]:

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
                modal_footer += """<script>
                document.querySelector('#flexSwitchCheckDefault').setAttribute('disabled', '');
                document.querySelector('#switchLogScaleDiv').style.display = 'none';
                </script>
                """

            page_f.write(modal_header + cardsHtml + modal_footer)
            # html = secondary.returnHtml()

    with open(
        f"./render_{arguments.cache_prefix}/data_{arguments.cache_prefix}_{extract_date}.json",
        "w",
    ) as f:
        f.write(json.dumps(dico_data, indent=4))

    with open(f"./render_{arguments.cache_prefix}/js/main_circle.js", "a") as f_page:

        dico_js = {}

        angles = {"passwords": (-2*pi/3, -pi),
                  "kerberos": (0, -pi/3),
                  "permissions": (0, pi),
                  "misc": (-pi/3, -2*pi/3),
                  "az_permissions": (0, pi),
                  "az_misc": (-pi/3, -2*pi/3),
                  "az_passwords": (-2*pi/3, -pi),
                  "ms_graph": (0, -pi/3)}

        dico_position = {}

        for category in dico_category:
            number_of_controls = len(dico_category[category])
            dico_position[category] = get_hexagons_pos(number_of_controls,
                                                       angles[category][0],
                                                       angles[category][1])

        dico_position_instance = {"passwords": 0, "kerberos": 0, "permissions": 0, "misc": 0, "az_misc": 0, "az_permissions": 0, "az_passwords": 0, "ms_graph": 0}

        controls_by_color = {"grey": [],
                             "green": [],
                             "yellow": [],
                             "orange": [],
                             "red": []}

        for category in dico_category:
            for indicator in dico_category[category]:

                if dico_rating_color[category_repartition_dict[category]].get(indicator):
                    color = dico_rating_color[category_repartition_dict[category]][indicator]

                else:
                    color = "grey"

                controls_by_color[color].append((category, indicator))

        for color in controls_by_color.keys():
            for category, indicator in controls_by_color[color]:

                dico_js[indicator] = {
                    "color": color,
                    "name": dico_name_title[indicator],
                    "category_repartition": category_repartition_dict[category],
                    "link": quote(str(indicator)) + ".html",
                    "category": category,
                    "position": dico_position[category][
                        dico_position_instance[category]
                    ],
                    "title": dico_name_description[indicator].replace("$", "")
                    if dico_name_description.get(indicator)
                    else indicator,
                }
                dico_position_instance[category] += 1

        string_dico = f"""\n var dico_entry = {json.dumps(dico_js)} \n
    display_all_hexagons(dico_entry);"""
        f_page.write(string_dico)

    return dico_name_description
