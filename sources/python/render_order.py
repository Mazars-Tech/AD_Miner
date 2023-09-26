from asyncore import read
import json
from pickletools import read_long1

from page_class import Page
from card_class import Card
from table_class import Table
from smolcard_class import SmolCard


def basicRedGreenColor(val):
    if int(val) > 0:
        return "danger"
    else:
        return "success"


def main_render(
    arguments,
    neo4j,
    domains,
    computers,
    users,
    objects,
    rating_dic,
    dico_name_description,
    extract_date,
):
    config = open("sources/python/config.json", "r")
    conf = json.load(config)["requests"]
    config.close()
    # This function creates the main page of the report
    # - Page object
    # 	- 4 Card objects (General, Password , Admin , Kerberos)
    # 		- lines on each card
    # Each line uses the results of a request, which is contained in the "domains", "computers", "users" and "objects" objects
    # Example : computers.list_total_computers contains the list of computers
    # It then calls Page.render()

    main_page = Page(
        arguments.cache_prefix,
        "index_old",
        f"{arguments.cache_prefix} - {extract_date[-2:]}/{extract_date[-4:-2]}/{extract_date[:4]}",
        "main page",
    )

    ### General card
    general_card = Card(
        title="General statistics", icon="bi-bar-chart", color="cardHeaderGreenBlue"
    )
    if (
        conf["vuln_functional_level"] == "true"
        and domains.vuln_functional_level is not None
    ):
        general_card.addLine(
            "%d insufficient forest and domains functional levels"
            % len(domains.vuln_functional_level),
            "bi-people-fill",
            "vuln_functional_level.html",
            basicRedGreenColor(len(domains.vuln_functional_level)),
        )
    if conf["domain_map_trust"] == "true":
        general_card.addLine(
            "%d domains with %d trusts"
            % ((len(domains.domains_list)), (len(domains.domain_map_trust))),
            "bi-gem",
            "domain_map_trust.html",
        )
    if conf["nb_domain_admins"] == "true":
        general_card.addLine(
            "%d domain admins" % (len(domains.users_nb_domain_admins)),
            "bi-gem",
            "nb_domain_admins.html",
        )
    if conf["nb_domain_controllers"] == "true":
        general_card.addLine(
            "%d domain controllers" % (len(domains.computers_nb_domain_controllers)),
            "bi-gem",
            "nb_domain_controllers.html",
        )
    if conf["nb_computers"] == "true":
        general_card.addLine(
            "%d member computers " % (len(computers.list_total_computers)),
            "bi-laptop",
            "computers.html",
        )
    # if conf["computers_not_connected_since"] == "true":
    general_card.addLine(
        "... including %d ghost computers"
        % (len(domains.computers_not_connected_since_60)),
        "bi-snapchat",
        "computers_last_connexion.html",
        basicRedGreenColor(len(domains.computers_not_connected_since_60)),
    )
    # Could use lightbulb-off as icon or snapchat or camera-video-off
    if conf["nb_enabled_accounts"] == "true":
        general_card.addLine(
            "%d domain users" % (len(users.users)), "bi-person-circle", "users.html"
        )
    if conf["nb_groups"] == "true":
        general_card.addLine(
            "%d groups" % (len(domains.groups)), "bi-diagram-3", "groups.html"
        )

    if conf["rdp_access"] == "true":
        general_card.addLine(
            "%d computers with RDP access" % (len(users.users_rdp_access_2)),
            "bi-laptop",
            "computers_list_of_rdp_users.html",
        )

    # general_card.addLine("%d computers with obsolete OS" % len(computers.list_computers_os_obsolete), "bi-laptop", "computers_os_obsolete.html")
    # general_card.setTable("Obsolete OS breakdown", ["OS", "Count"], computers.dropdown_computers_os_obsolete)

    if conf["unpriv_users_to_GPO"] == "true":
        general_card.addLine(
            "%d GPO can be exploited" % (domains.number_of_gpo),
            "bi-laptop",
            "users_GPO_access.html",
        )
    elif conf["unpriv_users_to_GPO_init"] == "true":
        general_card.addLine(
            "%d GPO can be exploited" % (domains.number_of_gpo),
            "bi-laptop",
            "users_GPO_access.html",
        )

    if conf["nb_enabled_accounts"] == "true" and conf["nb_computers"] == "true":
        general_card.setTable(
            "Users/Computers per domain",
            ["Domain", "Users", "Computers"],
            domains.getUserComputersCountPerDomain(),
        )

    main_page.addComponent(general_card)

    ### Password card
    password_card = Card(
        title="Password statistics",
        icon="bi-lock-fill",
        color="cardHeaderLightGreenBlue",
    )

    if conf["user_password_never_expires"] == "true":
        password_card.addLine(
            "%d users w/o password expiration"
            % (len(users.users_password_never_expires)),
            "bi-bell-slash",
            "never_expires.html",
            basicRedGreenColor(len(users.users_password_never_expires)),
        )
    if conf["password_last_change"] == "true":
        password_card.addLine(
            "%d unchanged passwords > %d months"
            % (
                len(domains.users_pwd_not_changed_since_3months),
                int((neo4j.password_renewal) / 30),
            ),
            "bi-laptop",
            "users_pwd_not_changed_since.html",
            basicRedGreenColor(len(domains.users_pwd_not_changed_since_3months)),
        )
    if conf["dormant_accounts"] == "true":
        password_card.addLine(
            "%d dormant accounts" % len(domains.users_dormant_accounts),
            "bi-clock-history",
            "dormants_accounts.html",
            basicRedGreenColor(len(domains.users_dormant_accounts)),
        )
        password_card.setTable(
            "Dormant accounts breakdown",
            ["Unused since ", "Number users"],
            domains.getUsersUnusedSince(),
        )
        # Question - we divide by list of computers with laps = None, True or False or only computers with laps = True or False
    if conf["nb_computers_laps"] == "true" and conf["nb_computers"] == "true":
        password_card.addLine(
            "%d%% computers don't have LAPS enabled" % computers.stat_laps,
            "bi-laptop",
            "computers_without_laps.html",
            basicRedGreenColor(100 - computers.stat_laps),
        )

    if conf["can_read_laps"] == "true":
        password_card.addLine(
            "%d objects can read LAPS" % len(users.can_read_laps),
            "bi-laptop",
            "can_read_laps.html",
            basicRedGreenColor(len(users.can_read_laps)),
        )

    if conf["nb_user_password_cleartext"] == "true":
        password_card.addLine(
            "%d users with clear text password" % len(users.users_pwd_cleartext),
            "bi-unlock-fill",
            "users_pwd_cleartext.html",
            basicRedGreenColor(len(users.users_pwd_cleartext)),
        )
    if (
        conf["users_shadow_credentials"] == "true"
        and users.users_shadow_credentials_uniq is not None
    ):
        password_card.addLine(
            "%d users can impersonate privileged accounts"
            % len(users.users_shadow_credentials_uniq),
            "bi-people-fill",
            "users_shadow_credentials.html",
            basicRedGreenColor(len(users.users_shadow_credentials_uniq)),
        )
    # general_card.addLine(f"{round(100*len(computers.computers_nb_has_laps)/len(computers.list_total_computers), 3)} % of computers with LAPS enabled", "bi-laptop", "computers_without_laps.html")

    if (
        conf["can_read_gmsapassword_of_adm"] == "true"
        and users.can_read_gmsapassword_of_adm is not None
    ):
        password_card.addLine(
            "%d users can read GMSA passwords of privileged accounts"
            % len(users.can_read_gmsapassword_of_adm),
            "bi-people-fill",
            "can_read_gmsapassword_of_adm.html",
            basicRedGreenColor(len(users.can_read_gmsapassword_of_adm)),
        )
    main_page.addComponent(password_card)
    # password_card.addLine("users can be impersonated by up %d users" %(users.max_number_users_shadow_credentials_to_non_admins), "bi-people-fill", "users_shadow_credentials_to_non_admins.html")
    #%max(users.users_shadow_credentials_to_non_admins["count"])

    ### Admin card
    admin_card = Card(
        title="Admin statistics", icon="bi-laptop", color="cardHeaderMazPurple"
    )
    if (
        conf["dom_admin_on_non_dc"] == "true"
        and len(users.users_domain_admin_on_nondc) > -1
    ):
        admin_card.addLine(
            "%d domain admin sessions on non-DC"
            % len(users.users_domain_admin_on_nondc),
            "bi-laptop",
            "dom_admin_on_non_dc.html",
            basicRedGreenColor(len(users.users_domain_admin_on_nondc)),
        )
    if conf["computers_admin_on_computers"] and computers.count_computers_admins > 0:
        admin_card.addLine(
            "%d computers admin of %d computers"
            % (
                computers.count_computers_admins,
                computers.count_computers_admins_target,
            ),
            "bi-laptop",
            "computers_admin_of_computers.html",
            "danger",
        )  # or bi-link
    elif conf["computers_admin_on_computers"]:
        admin_card.addLine(
            "No computer admin of other computers",
            "bi-laptop",
            "computers_admin_of_computers.html",
            "success",
        )  # or bi-link
    if conf["users_admin_on_computers"] == "true":
        admin_card.addLine(
            "%d users with admin privs." % len(users.users_admin_computer_count),
            "bi-laptop",
            "users_admin_of_computers.html",
        )
    if conf["objects_to_dcsync"] == "true":
        admin_card.addLine(
            "%d non DA/DC objects have DCSync privileges"
            % len(objects.can_dcsync_nodes),
            "bi-forward",
            "can_dcsync.html",
        )
        admin_card.addLine(
            "... and %d paths to get to them" % len(domains.objects_to_dcsync),
            "bi-forward",
            "graph_path_objects_to_dcsync.html",
            basicRedGreenColor(len(domains.objects_to_dcsync)),
        )

    if (
        conf["users_admin_on_computers"] == "true"
        and computers.computer_with_most_user_admin != []
    ):
        admin_card.addLine(
            "Up to %d admins on computers" % computers.computer_with_most_user_admin,
            "bi-laptop",
            "computers_users_admin.html",
        )

    if (
        conf["users_admin_on_servers_1"] == "true"
        and conf["users_admin_on_servers_2"] == "true"
        and users.servers_with_most_paths != []
    ):
        admin_card.addLine(
            "Up to %d users could compromise a server" % users.servers_with_most_paths,
            "bi-people-fill",
            "server_users_could_be_admin.html",
            "warning",
        )

    if conf["computers_members_high_privilege"] == "true":
        admin_card.addLine(
            "%d computers with high privs."
            % len(computers.computers_members_high_privilege_uniq),
            "bi-laptop",
            "computers_members_high_privilege.html",
            "warning",
        )
    if conf["objects_to_domain_admin"] == "true":
        admin_card.addLine(
            "%d objects with %d paths to Domain Admin"
            % (domains.total_object, len(domains.objects_to_domain_admin)),
            "bi-forward-fill",
            "graph_path_objects_to_da.html",
            "warning",
        )

    # 	if conf["objects_to_domain_admin"] == "true" or conf["objects_to_unconstrained_delegation"] == "true" or conf["objects_to_dcsync"] == "true":
    # 		admin_card.addLine("%d nodes are included in at least 3 paths of compromission" %(domains.number_paths_main_nodes), "bi-laptop", "main_compromise_paths.html")

    if conf["objects_admincount"] == "true":
        admin_card.addLine(
            "%d objects with AdminSDHolder" % len(users.objects_admincount_enabled),
            "bi-forward",
            "objects_adminsdholder.html",
        )

    if conf["dc_impersonation"] == "true":
        admin_card.addLine(
            "%d paths to impersonate DCs" % (users.users_dc_impersonation_count),
            "bi-server",
            "dc_impersonation.html",
            basicRedGreenColor(users.users_dc_impersonation_count),
        )
    if conf["rbcd"] == "true":
        admin_card.addLine(
            "%d users can RBCD attack on %d computers"
            % (users.nb_users_rbcd_attacks, users.nb_computers_rbcd_attacks),
            "bi-incognito",
            "rbcd.html",
        )

    if conf["graph_rbcd"] == "true":
        admin_card.addLine(
            "%d users can RBCD attack on %d computers"
            % (users.rbcd_nb_start_nodes, users.rbcd_nb_end_nodes),
            "bi-incognito",
            "graph_list_objects_rbcd.html",
        )

    if conf["unpriv_to_dnsadmins"] == "true":
        admin_card.addLine(
            "%d paths to DNSAdmins group" % len(users.unpriv_to_dnsadmins),
            "bi-laptop",
            "unpriv_to_dnsadmins.html",
            basicRedGreenColor(len(users.unpriv_to_dnsadmins)),
        )
    if conf["objects_to_ou_handlers"] == "true":
        admin_card.addLine(
            "%d dangerous control paths over %d OUs"
            % (domains.nb_starting_nodes_to_ous, domains.nb_ous_with_da),
            "bi-forward",
            "graph_path_objects_to_ou_handlers.html",
        )
    if (
        conf["vuln_sidhistory_dangerous"] == "true"
        and users.vuln_sidhistory_dangerous is not None
    ):
        admin_card.addLine(
            "%d accounts or groups with unexpected SID history"
            % len(users.vuln_sidhistory_dangerous),
            "bi-people-fill",
            "vuln_sidhistory_dangerous.html",
            basicRedGreenColor(len(users.vuln_sidhistory_dangerous)),
        )
    if (
        conf["objects_to_operators_member"] == "true"
        and users.objects_to_operators_member is not None
    ):
        admin_card.addLine(
            "%d objects with path to Operators Member"
            % len(users.objects_to_operators_member),
            "bi-forward-fill",
            "objects_to_operators_member.html",
            basicRedGreenColor(len(users.objects_to_operators_member)),
        )
    if (
        conf["vuln_permissions_adminsdholder"] == "true" 
        and users.vuln_permissions_adminsdholder is not None
    ):
        admin_card.addLine(
            "%d objects with path to AdminSDHolder container"
            % len(users.vuln_permissions_adminsdholder),
            "bi-forward-fill",
            "vuln_permissions_adminsdholder.html",
            basicRedGreenColor(len(users.vuln_permissions_adminsdholder)),
        )
    main_page.addComponent(admin_card)

    # ### Obsolete card (now in Kerberos card, doesn't make sense but lack of space in General card I guess...)
    # kerberos_card = Card(title="Obsolescence statistics", icon="bi-windows", color="cardHeaderMazFrame")
    # kerberos_card.addLine("%d computers with obsolete OS" % len(computers.list_computers_os_obsolete), "bi-laptop", "computers_os_obsolete.html")
    # kerberos_card.setTable("Obsolete OS breakdown", ["OS", "Count"], computers.dropdown_computers_os_obsolete)
    # main_page.addComponent(kerberos_card)

    ### Kerberos card
    kerberos_card = Card(
        title="Kerberos statistics", icon="bi-shield-lock", color="cardHeaderMazLower"
    )
    if conf["nb_computer_unconstrained_delegations"] == "true":
        kerberos_card.addLine(
            "%d non-DC with unconstrained delegations"
            % len(computers.computers_non_dc_unconstrained_delegations),
            "bi-laptop",
            "non-dc_with_unconstrained_delegations.html",
            basicRedGreenColor(
                len(computers.computers_non_dc_unconstrained_delegations)
            ),
        )

    if conf["objects_to_unconstrained_delegation"] == "true":
        kerberos_card.addLine(
            "... and %d paths to compromise these"
            % len(domains.objects_to_unconstrained_delegation),
            "bi-laptop",
            "graph_path_objects_to_unconstrained_delegation.html",
            basicRedGreenColor(len(domains.objects_to_unconstrained_delegation)),
        )

    if conf["nb_users_unconstrained_delegations"] == "true":
        kerberos_card.addLine(
            "%d users with unconstrained delegations"
            % len(computers.users_non_dc_unconstrained_delegations),
            "bi-laptop",
            "non-dc_users_with_unconstrained_delegations.html",
            basicRedGreenColor(len(computers.users_non_dc_unconstrained_delegations)),
        )

    if conf["users_to_unconstrained_delegation"] == "true":
        kerberos_card.addLine(
            "... and %d paths to compromise these"
            % len(domains.objects_to_unconstrained_delegation_2),
            "bi-laptop",
            "graph_path_objects_to_unconstrained_delegation_users.html",
            basicRedGreenColor(len(domains.objects_to_unconstrained_delegation_2)),
        )
    if conf["users_constrained_delegations"] == "true":
        kerberos_card.addLine(
            "%d users with constrained delegations"
            % len(computers.users_constrained_delegations),
            "bi-laptop",
            "users_constrained_delegations.html",
            "warning",
        )
    if (
        conf["nb_as-rep_roastable_accounts"] == "true"
        and len(users.users_kerberos_as_rep) > 0
    ):
        kerberos_card.addLine(
            "%d accounts are AS-REP-roastable" % len(users.users_kerberos_as_rep),
            "bi-laptop",
            "as_rep.html",
            basicRedGreenColor(len(users.users_kerberos_as_rep)),
        )
    if conf["nb_kerberoastable_accounts"] == "true":
        kerberos_card.addLine(
            "%d kerberoastable accounts" % len(users.users_kerberoastable_users),
            "bi-laptop",
            "kerberoastables.html",
            "warning",
        )
    # if conf["os"] == "true":
    kerberos_card.addLine(
        "%d computers with obsolete OS" % len(computers.list_computers_os_obsolete),
        "bi-laptop",
        "computers_os_obsolete.html",
        basicRedGreenColor(len(computers.list_computers_os_obsolete)),
    )
    # if conf["os"] == "true":
    kerberos_card.setTable(
        "Obsolete OS breakdown",
        ["OS", "Count"],
        computers.dropdown_computers_os_obsolete,
    )
    if conf["krb_pwd_last_change"] == "true" and len(users.users_krb_pwd_last_set):
        # On itère sur les KRBTGT des différents domaines, et on prend celui qui changé sont mot de passe il y a le plus longtemps
        # users_krb_pwd_last_set = [{'domain': 'BLABLA.LOCAL', 'name': 'KRBTGT@BLABLA.LOCAL', 'pass_last_change': 11},
        # 							{'domain': 'BLIBLI.LOCAL', 'name': 'KRBTGT@BLIBLI.LOCAL', 'pass_last_change': 2000}]
        # => 2000
        k = max([dict["pass_last_change"] for dict in users.users_krb_pwd_last_set])
        if k is not None:
            kerberos_card.addLine(
                "krbtgt not updated in > %d days " % k,
                "bi-laptop",
                "krb_last_change.html",
                basicRedGreenColor(k - 180),
            )
    main_page.addComponent(kerberos_card)
    main_page.render()

    secondary = Page(
        arguments.cache_prefix,
        "cards",
        f"{arguments.cache_prefix} - {extract_date[-2:]}/{extract_date[-4:-2]}/{extract_date[:4]}",
        "Following data provide indicators to measure the cybersecurity risk exposure of your Active Directory infrastructure",
        include_js=["hide_cards"],
    )

    descriptions = json.load(open("sources/python/description.json"))
    # print(rating_dic)
    for k in rating_dic.keys():
        for vuln in rating_dic[k]:
            if descriptions.get(vuln):
                description = descriptions[vuln]["description"]
            else:
                description = vuln
            secondary.addComponent(
                SmolCard(
                    id=vuln,
                    criticity=str(k),
                    href=f"{vuln}.html",
                    description=description,
                    details=dico_name_description.get(vuln),
                )
            )

    secondary.render()
