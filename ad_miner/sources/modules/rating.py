import datetime
import time
import json

from ad_miner.sources.modules.utils import CONFIG_MAP

d = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
    -1: [],
}  # -1 = not tested/disabled, 5 = tested and 0 matching


def rating(users, domains, computers, objects, arguments):
    d[presence_of(["1"]*domains.max_da_per_domain, criticity=2, threshold=10)].append("nb_domain_admins")
    d[presence_of(objects.can_dcsync_nodes)].append("can_dcsync")
    d[presence_of(users.users_shadow_credentials)].append("users_shadow_credentials")
    d[presence_of(users.users_shadow_credentials_to_non_admins, criticity=2)].append(
        "users_shadow_credentials_to_non_admins"
    )
    d[
        time_since(
            users.users_krb_pwd_last_set[0]["pass_last_change"],
            age=1 * 365,
            criticity=2,
        )
    ].append("krb_last_change")
    d[containsDAs(users.users_kerberoastable_users)].append("kerberoastables")
    d[containsDAs(users.users_kerberos_as_rep)].append("as_rep")
    d[
        presence_of(computers.list_computers_unconstrained_delegations, criticity=2)
    ].append("non-dc_with_unconstrained_delegations")
    d[constrainedDelegation(computers.users_constrained_delegations)].append(
        "users_constrained_delegations"
    )
    d[hasPathToDA(computers.list_computers_admin_computers)].append(
        "computers_admin_of_computers"
    )
    # ANSSI says 1y, need to adapt the requests etc.
    # d[percentage_superior(domains.users_pwd_not_changed_since_1y, users.users, percentage=0.25, presence=True)].append("users_pwd_not_changed_since") # TODO CHANGE DESCRIPTION = 3MONTHS NOT 1Y
    d[
        percentage_superior(
            domains.users_pwd_not_changed_since_3months,
            users.users,
            criticity=3,
            percentage=0.1,
            presence=True,
        )
    ].append(
        "users_pwd_not_changed_since"
    )  # TODO CHANGE DESCRIPTION = 3MONTHS NOT 1Y
    d[containsDAs(users.users_pwd_cleartext)].append("users_pwd_cleartext")
    d[
        min(
            hasPathToDA(users.users_admin_computer),
            percentage_superior(
                users.users_admin_computer, users.users, criticity=2, percentage=0.5
            ),
        )
    ].append("users_admin_of_computers")
    d[hasPathToDA(users.users_admin_on_servers_all_data)].append(
        "server_users_could_be_admin"
    )
    d[presence_of(computers.computers_members_high_privilege_uniq)].append(
        "computers_members_high_privilege"
    )
    d[presence_of(users.users_domain_admin_on_nondc)].append("dom_admin_on_non_dc")
    d[presence_of(users.users_dc_impersonation)].append("dc_impersonation")
    # Ghost computers
    d[
        percentage_superior(
            domains.computers_not_connected_since_60,
            computers.list_total_computers,
            criticity=2,
            percentage=0.5,
            presence=True,
        )
    ].append(
        "computers_last_connexion"
    )  # TODO: percentage TBD

    # RDP access | TODO: percentage TBD
    d[percentage_superior(users.users_rdp_access_1, users.users, criticity=3, percentage=0.5)].append("users_rdp_access")
    d[percentage_superior(users.users_rdp_access_2, users.users, criticity=3, percentage=0.5)].append("computers_list_of_rdp_users")
    # Users w/o pass expiration
    d[
        percentage_superior(
            users.users_password_never_expires,
            users.users,
            criticity=2,
            percentage=0.8,
            presence=True,
        )
    ].append("never_expires")
    # Dormant accounts
    d[
        percentage_superior(
            domains.users_dormant_accounts,
            users.users,
            criticity=2,
            percentage=0.5,
            presence=True,
        )
    ].append(
        "dormants_accounts"
    )  # TODO: percentage TBD

    d[presence_of(computers.list_computers_os_obsolete, criticity=2)].append(
        "computers_os_obsolete"
    )  # TODO : criticity TBD

    # Threshold of 1 to exclude the false positive of container USERS containing DOMAIN ADMIN group
    d[presence_of(domains.objects_to_domain_admin, criticity=1, threshold=1)].append(
        "graph_path_objects_to_da"
    )

    d[presence_of(users.unpriv_to_dnsadmins, criticity=2)].append("unpriv_to_dnsadmins")

    # https://www.cert.ssi.gouv.fr/uploads/guide-ad.html
    # print(domains.vuln_functional_level)

    if rate_vuln_functional_level(domains.vuln_functional_level) is not None:
        d[rate_vuln_functional_level(domains.vuln_functional_level)].append(
            "vuln_functional_level"
        )

    d[presence_of(users.vuln_permissions_adminsdholder, criticity=1)].append(
        "vuln_permissions_adminsdholder"
    )
    # d[presence_of(users.vuln_sidhistory_dangerous)].append("vuln_sidhistory_dangerous")
    d[presence_of(users.can_read_gmsapassword_of_adm)].append("can_read_gmsapassword_of_adm")
    d[presence_of(users.objects_to_operators_member)].append("objects_to_operators_member")

    # TODO : LAPS

    d[4 if computers.stat_laps < 20 else 3].append("computers_without_laps")

    d[presence_of(domains.objects_to_ou_handlers)].append(
        "graph_path_objects_to_ou_handlers"
    )
    d[
        min(
            presence_of(list(users.rbcd_graphs.keys()), criticity=2),
            presence_of(list(users.rbcd_to_da_graphs.keys()), criticity=1),
        )
    ].append("graph_list_objects_rbcd")
    d[presence_of(domains.da_to_da)].append("da_to_da")

    d[presence_of(computers.ADCS_path_sorted.keys())].append("objects_to_adcs")
    d[presence_of(domains.unpriv_users_to_GPO_parsed.items())].append("users_GPO_access")

    d[1 if domains.total_dangerous_paths > 0 else 5].append(
        "dangerous_paths"
    )
    d[presence_of(users.users_password_not_required,3)].append("users_password_not_required")

    d[2 if len(users.can_read_laps_parsed) > len(domains.users_nb_domain_admins) else 5].append("can_read_laps")

    d[2 if users.number_group_ACL_anomaly > 0 else 5].append("group_anomaly_acl")

    d[2 if len(domains.empty_groups)/len(domains.groups) > 0.40 else 3 if len(domains.empty_groups)/len(domains.groups) > 0.20 else 5].append("empty_groups")
    d[2 if len(domains.empty_ous)/len(domains.groups) > 0.40 else 3 if len(domains.empty_ous)/len(domains.groups) > 0.20 else 5].append("empty_ous")

    d[presence_of(users.has_sid_history, 2)].append("has_sid_history")
    d[rate_cross_domain_privileges(domains.cross_domain_local_admin_accounts,domains.cross_domain_domain_admin_accounts)].append("cross_domain_admin_privileges")
    d[1 if len([ude for ude in users.guest_accounts if ude[-1]]) > 0 else 5].append("guest_accounts")
    d[rate_admincount(users.unpriviledged_users_with_admincount, users.users_nb_domain_admins)].append("up_to_date_admincount"),
    d[1 if len([dic for dic in users.users_nb_domain_admins if "Protected Users" not in dic["admin type"]]) > 0 else 5].append("privileged_accounts_outside_Protected_Users")

    return d


def rating_color(total_rating):
    # total_rating = rating(users, domains, computers, objects, arguments)
    dico_rating_color = {}

    conf = CONFIG_MAP['requests']

    for notation in total_rating:
        for indicator in total_rating[notation]:
            if notation == 1:
                color = "red"
            elif notation == 2:
                color = "orange"
            elif notation == 3:
                color = "yellow"
            elif notation == 4 or notation == 5:
                color = "green"
            else:
                color = "grey"

            # Check if control is disabled in config.json. If so, color = grey
            try:
                disabled = conf.get(indicator) == "false"
            except KeyError:
                disabled = False
            if disabled:
                color = "grey"

            dico_rating_color[indicator] = color

    return dico_rating_color


## PERCENTAGE SUP FUNCTION
# If no presence argument : return criticity if > percentage
# If presence argument : return criticity if > percentage, criticity+1 if there at least one
def percentage_superior(req, base, criticity=1, percentage=0, presence=False):
    if req is None:
        return -1
    if base is None:
        return -1
    if len(base) == 0:
        return -1

    if len(base) and len(req) / len(base) > percentage:
        return criticity

    if presence:
        if len(req) > 0:
            return criticity + 1
    return 5


## PERCENTAGE INF FUNCTION
# return criticity if < percentage, criticity - 1 if < percentage/2
def percentage_inferior(req, base, criticity=1, percentage=0):
    if req is None:
        return -1
    if base is None:
        return -1
    if len(base) == 0:
        return -1

    if len(base) and len(req) / len(base) < percentage:
        return criticity

    if len(base) and len(req) / len(base) < percentage / 2:
        return criticity - 1

    return 5


## PRESENCE FUNCTION
# Return criticity if at least one, 5 if not
def presence_of(req, criticity=1, threshold=0):
    if req is None:
        return -1
    if len(req) > threshold:
        return criticity
    return 5


## TIME SINCE EXTRACT FUNCTION
# return criticity if time since > age, 5 if not
def time_since_extraction_date(req, extimestamp=0, age=90, criticity=1):
    if req is None:
        return -1

    year = int(extimestamp[0:4])
    month = int(extimestamp[4:6])
    day = int(extimestamp[6:8])
    date_time = datetime.datetime(year, month, day)
    extraction_date = time.mktime(date_time.timetuple())
    days_since = (extraction_date - req) / 86400

    if days_since > age:
        return criticity

    return 5


## TIME SINCE FUNCTION
# return criticity if time since > age, 5 if not
def time_since(req, age=90, criticity=1):  # req as days
    if req is None:
        return -1
    if req > age:
        return criticity

    return 5


## CONTAINS DA FUNCTION
# return criticity if at least one DA, 5 if not
def containsDAs(req, criticity=1):
    if req is None:
        return -1

    for object in req:
        if object.get("is_Domain_Admin"):
            if object["is_Domain_Admin"] == True:
                return criticity
        # if object.get("is_da"):
        #     if object["is_da"] == True:
        #         return criticity

    if len(req) > 0:
        return criticity + 1

    return 5


def constrainedDelegation(req):
    if req is None:
        return -1
    for object in req:
        if type(object) == str:
            return -1
        if object["to_DC"] == True:
            return 2

    if len(req) > 0:
        return 3

    return 5


def hasPathToDA(
    req, criticity=1
):  # ne marche que partiellement : besoin de rajouter l'attribut has_path_to_DA dans toutes les requêtes pertinentes + dans domains.py/findAndCreatePathToDaFromComputersList
    if req is None:
        return -1

    for object in req:
        # print(object)
        if not object.get("has_path_to_da"):
            continue
        if object["has_path_to_da"] == True:
            # print(object)
            return criticity

    if len(req) > 0:
        return criticity + 1

    return 5

### Rating vuln functional level

#  d[min([ret["level_maturity"] for ret in domains.vuln_functional_level])].append(
#         "vuln_functional_level"
#     )


def rate_vuln_functional_level(req):
    if req != None:
        return min([ret["Level maturity"] for ret in req])
    else:
        return -1


def rate_cross_domain_privileges(nb_local_priv,nb_da_priv):
    if nb_da_priv > 0:
        return 1
    elif nb_local_priv>0:
        return 2
    else:
        return 5


def rate_admincount(unpriviledged_users_with_admincount, users_nb_domain_admins):
    for da_dic in users_nb_domain_admins:
        if not da_dic["admincount"]:
            return 1
    if len(unpriviledged_users_with_admincount) > 0:
        return 3
    return 5
