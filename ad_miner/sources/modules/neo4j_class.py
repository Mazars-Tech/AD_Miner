import datetime
import gc
import multiprocessing as mp
import sys
import time
from hashlib import md5

from ad_miner.sources.modules import istarmap  # import to apply patch
import numpy as np
import tqdm
from neo4j import GraphDatabase

from ad_miner.sources.modules import cache_class, logger
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.utils import timer_format


def pre_request_date(arguments):
    driver = GraphDatabase.driver(
        arguments.bolt,
        auth=(arguments.username, arguments.password),
        encrypted=False,
    )

    with driver.session() as session:
        with session.begin_transaction() as tx:
            for record in tx.run(
                "MATCH (a) WHERE a.lastlogon IS NOT NULL return toInteger(a.lastlogon) as last order by last desc LIMIT 1"
            ):
                date_lastlogon = record.data()
    driver.close()
    return date_lastlogon["last"]


class Neo4j:
    def __init__(self, arguments, extract_date_int):

        # remote computers that run requests with their number of core
        if len(arguments.cluster) > 0:
            self.cluster = {}
            list_nodes = arguments.cluster.split(",")
            for node in list_nodes:
                try:
                    ip, port, nCore = node.split(":")
                except ValueError as e:
                    print(e)
                    logger.print_error(
                        "An error occured while parsing the cluster argument. The correct syntax is --cluster ip1:port1:nCores1,ip2:port2:nCores2,etc"
                    )
                    sys.exit(-1)
                self.cluster[ip + ":" + port] = int(nCore)

        extract_date = self.set_extract_date(str(extract_date_int))

        recursive_level = arguments.level
        self.password_renewal = int(arguments.renewal_password)
        # We only use the Azure relationships when requested to do so
        if arguments.azure:
            properties = "MemberOf|HasSession|AdminTo|AllExtendedRights|AddMember|ForceChangePassword|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|CanRDP|ExecuteDCOM|AllowedToDelegate|ReadLAPSPassword|Contains|GpLink|AddAllowedToAct|AllowedToAct|SQLAdmin|ReadGMSAPassword|HasSIDHistory|CanPSRemote|AddSelf|WriteSPN|AddKeyCredentialLink|SyncLAPSPassword|CanExtractDCSecrets|AZAddMembers|AZContains|AZContributor|AZGetCertificates|AZGetKeys|AZGetSecrets|AZGlobalAdmin|AZOwns|AZPrivilegedRoleAdmin|AZResetPassword|AZUserAccessAdministrator|AZAppAdmin|AZCloudAppAdmin|AZRunsAs|AZKeyVaultContributor|AddSelf|WriteSPN|AddKeyCredentialLink|AZAddSecret|AZAvereContributor|AZExecuteCommand|AZGrant|AZGrantSelf|AZHasRole|AZMemberOf|AZOwner|AZVMAdminLogin"
        else:
            properties = "MemberOf|HasSession|AdminTo|AllExtendedRights|AddMember|ForceChangePassword|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|ExecuteDCOM|AllowedToDelegate|ReadLAPSPassword|Contains|GpLink|AddAllowedToAct|AllowedToAct|SQLAdmin|ReadGMSAPassword|HasSIDHistory|CanPSRemote|AddSelf|WriteSPN|AddKeyCredentialLink|SyncLAPSPassword|CanExtractDCSecrets"
            if arguments.rdp:
                properties += "|CanRDP"

            inbound_control_edges = "MemberOf|AddSelf|WriteSPN|AddKeyCredentialLink|AddMember|AllExtendedRights|ForceChangePassword|GenericAll|GenericWrite|WriteDacl|WriteOwner|Owns"

            self.all_requests = {
                "delete_orphans": {
                    "name": "Delete orphan objects that have no labels",
                    "request": "MATCH (n) WHERE size(labels(n))=1 DETACH DELETE n",
                    "filename": "delete_orphans",
                    "method": self.requestList,
                },
                "preparation_request_nodes": {
                    "name": "Clean AD Miner custom attributes",
                    "request": "MATCH (n) "
                    "REMOVE n.is_server,n.is_dc,n.is_da,n.is_dag,n.can_dcsync,n.path_candidate,n.ou_candidate,n.contains_da_dc,n.is_da_dc,n.ghost_computer,n.has_path_to_da,n.is_admin,n.is_group_operator,n.nbr_adm_machines,n.members_count,n.has_members,n.user_members_count,n.is_operator_member,n.is_group_account_operator,n.is_group_backup_operator,n.is_group_server_operator,n.is_group_print_operator,n.is_account_operator,n.is_backup_operator,n.is_server_operator,n.is_print_operator,n.gpolinks_count,n.has_links,n.dangerous_inbound, n.is_adminsdholder,n.is_dnsadmin,n.da_types",

                    "filename": "preparation_request_nodes",
                    "method": self.requestList,
                },
                "delete_unresolved": {
                    "name": "Delete objects for which SID could not resolved",
                    "request": "MATCH (n) WHERE NOT EXISTS(n.domain) OR NOT EXISTS(n.name) DETACH DELETE n",
                    "filename": "delete_unresolved",
                    "method": self.requestList,
                },
                "set_upper_domain_name": {
                    "name": "Set domain names to upper case when not the case",
                    "request": "MATCH (g) where g.domain <> toUpper(g.domain) SET g.domain=toUpper(g.domain) ",
                    "filename": "set_upper_domain_name",
                    "method": self.requestList,
                },
                "preparation_request_relations": {
                    "name": "Clean AD Miner custom relations",
                    "request": "MATCH (g:Group)-[r:CanExtractDCSecrets|CanLoadCode|CanLogOnLocallyOnDC]->(c:Computer) "
                    "DELETE r ",
                    "filename": "preparation_request_relations",
                    "method": self.requestList,
                },
                "set_server": {
                    "name": "Set is_server=TRUE to computers for which operatingsystem contains Server)",
                    "request": "MATCH (c:Computer) "
                    ' WHERE c.operatingsystem CONTAINS "erver" '
                    "SET c.is_server=TRUE",
                    "filename": "set_server",
                    "method": self.requestList,
                },
                "set_non_server": {
                    "name": "Set is_server=FALSE to other computers )",
                    "request": "MATCH (c:Computer) "
                    "WHERE c.is_server IS NULL  "
                    "SET c.is_server=FALSE",
                    "filename": "set_non_server",
                    "method": self.requestList,
                },
                "set_dc": {
                    "name": "Set dc=TRUE to computers that are domain controllers)",
                    "request": "MATCH (c:Computer)-[:MemberOf*1..3]->(g:Group) "
                    'WHERE g.objectid ENDS WITH "-516" OR g.objectid ENDS WITH "-521"'
                    "SET c.is_dc=TRUE",
                    "filename": "set_dc",
                    "method": self.requestList,
                },
                "set_nondc": {
                    "name": "Set dc=FALSE to computers that are not domain controllers)",
                    "request": "MATCH (c:Computer) "
                    "WHERE c.is_dc IS NULL "
                    "SET c.is_dc=FALSE",
                    "filename": "set_nondc",
                    "method": self.requestList,
                },
                "set_can_extract_dc_secrets": {
                    "name": "ADD CanExtractDCSecrets relation from BACKUP OPERATORS OR SERVER OPERATORS groups to DCs of same domain",
                    "request": 'MATCH (g:Group) WHERE g.objectid ENDS WITH "-551" OR g.objectid ENDS WITH "-549" '
                    "MATCH (c:Computer{is_dc:true}) "
                    "WHERE g.domain = c.domain "
                    "MERGE (g)-[:CanExtractDCSecrets]->(c) ",
                    "filename": "set_can_extract_dc_secrets",
                    "method": self.requestList,
                },
                "set_unconstrained_delegations": {
                    "name": "ADD UnconstrainedDelegations relation from objects with KUD to the corresponding domain",
                    "request": "MATCH (m{unconstraineddelegation:true,is_dc:false}) "
                    "MATCH (d:Domain) "
                    "WHERE m.domain = d.domain "
                    "MERGE (m)-[:UnconstrainedDelegations]->(d) ",
                    "filename": "set_unconstrained_delegations",
                    "method": self.requestList,
                },
                "set_is_adminsdholder": { 'name': 'Set is_adminsdholder to Container with AdminSDHOLDER in name',
                    "request": "MATCH (c:Container) "
                    'WHERE c.name STARTS WITH "ADMINSDHOLDER@" '
                    "SET c.is_adminsdholder=true ",
                    "filename": "set_is_adminsdholder",
                    "method": self.requestList,
                },
                "set_is_dnsadmin": { 'name': 'Set is_dnsadmin to Group with DNSAdmins in name',
                    "request": "MATCH (g:Group) "
                    'WHERE g.name STARTS WITH "DNSADMINS@" '
                    "SET g.is_dnsadmin=true ",
                    "filename": "set_is_dnsadmin",
                    "method": self.requestList,
                },
                "set_can_load_code": {
                    "name": "ADD CanLoadCode relation from PRINT OPERATORS groups to DCs of same domain",
                    "request": 'MATCH (g:Group) WHERE g.objectid ENDS WITH "-550" '
                    "MATCH (c:Computer{is_dc:true}) "
                    "WHERE g.domain = c.domain "
                    "MERGE (g)-[:CanLoadCode]->(c) ",
                    "filename": "set_can_load_code",
                    "method": self.requestList,
                },
                "set_can_logon_dc": {
                    "name": "ADD CanLogOnLocallyOnDC relation from ACCOUNT OPERATORS groups to DCs of same domain",
                    "request": 'MATCH (g:Group) WHERE g.objectid ENDS WITH "-548" '
                    "MATCH (c:Computer{is_dc:true}) "
                    "WHERE g.domain = c.domain "
                    "MERGE (g)-[:CanLogOnLocallyOnDC]->(c) ",
                    "filename": "set_can_logon_dc",
                    "method": self.requestList,
                },
                "set_da": {
                    "name": "Set da=TRUE to users that are domain admins or administrators or enterprise admin",
                    "request": "MATCH (c:User)-[:MemberOf*1..3]->(g:Group) "
                    'WHERE g.objectid ENDS WITH "-512" ' # Domain admin
                    'OR g.objectid ENDS WITH "-518" '    # Schema admin
                    'OR g.objectid ENDS WITH "-519" '    # Enterprise admin
                    'OR g.objectid ENDS WITH "-526" '    # Key admin
                    'OR g.objectid ENDS WITH "-527" '    # Enterprise key admin
                    'OR g.objectid ENDS WITH "-544" '    # Builtin admin
                    "SET c.is_da=TRUE, c.da_types=[]",
                    "filename": "set_da",
                    "method": self.requestList,
                },
                "set_da_types": {
                    "name": "Set the da type (domain, enterprise, key or builtin)",
                    "request": "MATCH (c:User)-[:MemberOf*1..3]->(g:Group) " # Don't know why but I have to recheck the whole condition or it doesn't work...
                    'WHERE g.objectid ENDS WITH "-512" ' # Domain admin
                    'OR g.objectid ENDS WITH "-518" '    # Schema admin
                    'OR g.objectid ENDS WITH "-519" '    # Enterprise admin
                    'OR g.objectid ENDS WITH "-526" '    # Key admin
                    'OR g.objectid ENDS WITH "-527" '    # Enterprise key admin
                    'OR g.objectid ENDS WITH "-544" '    # Builtin admin
                    'WITH c,g, '
                    'CASE '
                    'WHEN g.objectid ENDS WITH "-512" THEN "Domain Admin" '
                    'WHEN g.objectid ENDS WITH "-518" THEN "Enterprise Admin" '
                    'WHEN g.objectid ENDS WITH "-519" THEN "Enterprise Admin" '
                    'WHEN g.objectid ENDS WITH "-526" THEN "Key Admin" '
                    'WHEN g.objectid ENDS WITH "-527" THEN "Key Admin" '
                    'WHEN g.objectid ENDS WITH "-544" THEN "Builtin Administrator" '
                    'ELSE null '
                    "END AS da_type "
                    "SET c.da_types = c.da_types + da_type",
                    "filename": "set_da_types",
                    "method": self.requestList,
                },
                "set_dag": {
                    "name": "Set da=TRUE to groups that are domain admins or administrators or enterprise admin",
                    "request": "MATCH (c:Group)-[:MemberOf*1..3]->(g:Group) "
                    'WHERE g.objectid ENDS WITH "-512" ' # Domain admin
                    'OR g.objectid ENDS WITH "-518" '    # Schema admin
                    'OR g.objectid ENDS WITH "-519" '    # Enterprise admin
                    'OR g.objectid ENDS WITH "-526" '    # Key admin
                    'OR g.objectid ENDS WITH "-527" '    # Enterprise key admin
                    'OR g.objectid ENDS WITH "-544" '    # Builtin admin
                    "SET c.is_da=TRUE",
                    "filename": "set_dag",
                    "method": self.requestList,
                },
                "set_dag_types": {
                    "name": "Set the da type (domain, enterprise, key or builtin)",
                    "request": "MATCH (c:Group)-[:MemberOf*1..3]->(g:Group) " # Don't know why but I have to recheck the whole condition or it doesn't work...
                    'WHERE g.objectid ENDS WITH "-512" ' # Domain admin
                    'OR g.objectid ENDS WITH "-518" '    # Schema admin
                    'OR g.objectid ENDS WITH "-519" '    # Enterprise admin
                    'OR g.objectid ENDS WITH "-526" '    # Key admin
                    'OR g.objectid ENDS WITH "-527" '    # Enterprise key admin
                    'OR g.objectid ENDS WITH "-544" '    # Builtin admin
                    'WITH c,g, '
                    'CASE '
                    'WHEN g.objectid ENDS WITH "-512" THEN "Domain Admin" '
                    'WHEN g.objectid ENDS WITH "-518" THEN "Enterprise Admin" '
                    'WHEN g.objectid ENDS WITH "-519" THEN "Enterprise Admin" '
                    'WHEN g.objectid ENDS WITH "-526" THEN "Key Admin" '
                    'WHEN g.objectid ENDS WITH "-527" THEN "Key Admin" '
                    'WHEN g.objectid ENDS WITH "-544" THEN "Builtin Administrator" '
                    'ELSE null '
                    "END AS da_type "
                    "SET c.da_types = c.da_types + da_type",
                    "filename": "set_da_types",
                    "method": self.requestList,
                },
                "set_dagg": {
                    "name": "Set da=TRUE to groups that are domain admins or administrators or enterprise admin",
                    "request": "MATCH (g:Group) "
                    'WHERE g.objectid ENDS WITH "-512" ' # Domain admin
                    'OR g.objectid ENDS WITH "-518" '    # Schema admin
                    'OR g.objectid ENDS WITH "-519" '    # Enterprise admin
                    'OR g.objectid ENDS WITH "-526" '    # Key admin
                    'OR g.objectid ENDS WITH "-527" '    # Enterprise key admin
                    'OR g.objectid ENDS WITH "-544" '    # Builtin admin
                    "SET g.is_da=TRUE",
                    "filename": "set_dagg",
                    "method": self.requestList,
                },
                "set_dagg_types": {
                    "name": "Set the da type (domain, enterprise, key or builtin)",
                    "request": "MATCH (g:Group) " # Don't know why but I have to recheck the whole condition or it doesn't work...
                    'WHERE g.objectid ENDS WITH "-512" ' # Domain admin
                    'OR g.objectid ENDS WITH "-518" '    # Schema admin
                    'OR g.objectid ENDS WITH "-519" '    # Enterprise admin
                    'OR g.objectid ENDS WITH "-526" '    # Key admin
                    'OR g.objectid ENDS WITH "-527" '    # Enterprise key admin
                    'OR g.objectid ENDS WITH "-544" '    # Builtin admin
                    'WITH g, '
                    'CASE '
                    'WHEN g.objectid ENDS WITH "-512" THEN "Domain Admin" '
                    'WHEN g.objectid ENDS WITH "-518" THEN "Enterprise Admin" '
                    'WHEN g.objectid ENDS WITH "-519" THEN "Enterprise Admin" '
                    'WHEN g.objectid ENDS WITH "-526" THEN "Key Admin" '
                    'WHEN g.objectid ENDS WITH "-527" THEN "Key Admin" '
                    'WHEN g.objectid ENDS WITH "-544" THEN "Builtin Administrator" '
                    'ELSE null '
                    "END AS da_type "
                    "SET g.da_types = g.da_types + da_type",
                    "filename": "set_da_types",
                    "method": self.requestList,
                },
                "set_daggg": {
                    "name": "Set dag=TRUE to the exact domain admin group (end with 512)",
                    "request": "MATCH (g:Group) "
                    'WHERE g.objectid ENDS WITH "-512"  '
                    "SET g.is_dag=TRUE",
                    "filename": "set_daggg",
                    "method": self.requestList,
                },
                "set_nonda": {
                    "name": "Set is_da=FALSE to all objects that do not have is_da=TRUE",
                    "request": "MATCH (c) "
                    "WHERE c.is_da IS NULL "
                    "SET c.is_da=FALSE",
                    "filename": "set_nonda",
                    "method": self.requestList,
                },
                "set_nondag": {
                    "name": "Set is_dag=FALSE to all objects that do not have is_da=TRUE",
                    "request": "MATCH (g) "
                    "WHERE g.is_dag IS NULL "
                    "SET g.is_dag=FALSE",
                    "filename": "set_nondag",
                    "method": self.requestList,
                },
                "del_fake_dc_admins": {
                    "name": "Delete AdminTo edges from non-DA to DC",
                    "request": "MATCH (g{is_da:false})-[rr:AdminTo]->(c:Computer{is_dc:true}) "
                    "DETACH DELETE rr ",
                    "filename": "del_fake_dc_admins",
                    "method": self.requestList,
                },
                # BACKUP OPERATORS ENDS WITH = S-1-5-32-551 | ACCOUNT OPERATORS ENDS WITH =  S-1-5-32-548
                # SERVER OPERATORS ENDS WITH = S-1-5-32-549 | PRINT OPERATORS ENDS WITH   = S-1-5-32-550
                "set_is_group_operator": { 'name': 'Set is_group_operator to Operator Groups (cf: ACCOUNT OPERATORS, SERVER OPERATORS, BACKUP OPERATORS, PRINT OPERATORS)',
                          "request":
                          'MATCH (g:Group) '
                          'WHERE g.objectid ENDS WITH "-551" OR g.objectid ENDS WITH "-549" OR g.objectid ENDS WITH "-548" OR g.objectid ENDS WITH "-550" '
                          'SET g.is_group_operator=True '
                          'SET '
                          'g.is_group_account_operator = CASE WHEN g.objectid ENDS WITH "-548" THEN true END, '
                          'g.is_group_backup_operator = CASE WHEN g.objectid ENDS WITH "-551" THEN true END, '
                          'g.is_group_server_operator = CASE WHEN g.objectid ENDS WITH "-549" THEN true END, '
                          'g.is_group_print_operator = CASE WHEN g.objectid ENDS WITH "-550" THEN true END ',
                           "filename": "set_is_group_operator",
                           "method": self.requestList
                },
                "set_is_operator_member": { 'name': 'Set is_operator_member to objects member of Operator Groups (cf: ACCOUNT OPERATORS, SERVER OPERATORS, BACKUP OPERATORS, PRINT OPERATORS)',
                          "request":
                          'MATCH (o:User)-[r:MemberOf*1..5]->(g:Group{is_group_operator:True}) '
                          'WHERE o.is_da=false OR o.domain <> g.domain '
                          'SET o.is_operator_member=true '
                          'SET '
                          'o.is_account_operator = CASE WHEN g.objectid ENDS WITH "-548" THEN true ELSE o.is_account_operator END, '
                          'o.is_type_operator = CASE WHEN g.objectid ENDS WITH "-548" THEN "ACCOUNT OPERATOR" ELSE o.is_type_operator END, '
                          'o.is_backup_operator = CASE WHEN g.objectid ENDS WITH "-551" THEN true ELSE o.is_backup_operator END, '
                          'o.is_type_operator = CASE WHEN g.objectid ENDS WITH "-548" THEN "BACKUP OPERATOR" ELSE o.is_type_operator END, '
                          'o.is_server_operator = CASE WHEN g.objectid ENDS WITH "-549" THEN true ELSE o.is_server_operator END, '
                          'o.is_type_operator = CASE WHEN g.objectid ENDS WITH "-548" THEN "SERVER OPERATOR" ELSE o.is_type_operator END, '
                          'o.is_print_operator = CASE WHEN g.objectid ENDS WITH "-550" THEN true ELSE o.is_print_operator END, '
                          'o.is_type_operator = CASE WHEN g.objectid ENDS WITH "-548" THEN "PRINT OPERATOR" ELSE o.is_type_operator END ',
                           "filename": "set_is_operator_member",
                           "method": self.requestList,
                },
                "set_dcsync1": {
                    "name": "Set dcsync=TRUE to nodes that can DCSync (GetChanges/GetChangesAll)",
                    "request": "MATCH p=allShortestPaths((n1)-[:MemberOf|GetChanges*1..5]->(u:Domain)) WHERE n1 <> u WITH n1 "
                    "MATCH p2=(n1)-[:MemberOf|GetChangesAll*1..5]->(u:Domain) "
                    "WHERE n1 <> u "
                    "AND NOT n1.name IS NULL "
                    "AND (((n1.is_da IS NULL OR n1.is_da=FALSE) AND (n1.is_dc IS NULL OR n1.is_dc=FALSE)) "
                    "OR (NOT u.domain CONTAINS '.' + n1.domain AND n1.domain <> u.domain)) "
                    "SET n1.can_dcsync=TRUE "
                    "RETURN DISTINCT p2 as p",
                    "filename": "set_dcsync1",
                    "method": self.requestGraph,
                },
                "set_dcsync2": {
                    "name": "Set dcsync=TRUE to nodes that can DCSync (GenericAll/AllExtendedRights)",
                    "request": "MATCH p3=allShortestPaths((n2)-[:MemberOf|GenericAll|AllExtendedRights*1..5]->(u:Domain)) "
                    "WHERE n2 <> u "
                    "AND NOT n2.name IS NULL "
                    "AND (((n2.is_da IS NULL OR n2.is_da=FALSE) AND (n2.is_dc IS NULL OR n2.is_dc=FALSE)) "
                    "OR (NOT u.domain CONTAINS '.' + n2.domain AND n2.domain <> u.domain)) "
                    "SET n2.can_dcsync=TRUE "
                    "RETURN DISTINCT p3 as p",
                    "filename": "set_dcsync2",
                    "method": self.requestGraph,
                },
                "dcsync_list": {
                    "name": "Get list of objects that can DCsync (and should probably not be to)",
                    "request": "MATCH (n{can_dcsync:true}) "
                    "RETURN n.domain as domain, n.name as name",
                    "filename": "dcsync_list",
                    "method": self.requestDict,
                },
                "set_path_candidate": {
                    "name": "Set path_candidate=TRUE to candidates eligible to shortestPath to DA",
                    "request": "MATCH (o) "
                    "WHERE NOT o.name IS NULL AND (o.is_da=false OR o.is_da IS NULL) AND NOT o:Domain "
                    "AND ((o.enabled=True AND o:User) "
                    "OR NOT o:User) "
                    "SET o.path_candidate=TRUE",
                    "filename": "set_path_candidate",
                    "method": self.requestList,
                },
                "set_ou_candidate": {
                    "name": "Set ou_candidate=TRUE to candidates eligible to shortestou to DA",
                    "request": "MATCH (m) "
                    "WHERE NOT m.name IS NULL AND ((m:Computer AND (m.is_dc=false OR NOT EXISTS(m.is_dc))) OR (m:User AND (m.is_da=false OR NOT EXISTS(m.is_da)))) "
                    "SET m.ou_candidate=TRUE",
                    "filename": "set_ou_candidate",
                    "method": self.requestList,
                },
                "set_containsda": {
                    "name": "Set contains_da_dc=TRUE to all objects that contains a domain administrator",
                    "request": "MATCH (o:OU)-[r:Contains*1..]->(x{is_da:true}) "
                    "SET o.contains_da_dc=true",
                    "filename": "set_containsda",
                    "method": self.requestList,
                },
                "set_containsdc": {
                    "name": "Set contains_da_dc=TRUE to all objects that contains a domain controller",
                    "request": "MATCH (o:OU)-[r:Contains*1..]->(x{is_dc:true}) "
                    "SET o.contains_da_dc=true",
                    "filename": "set_containsdc",
                    "method": self.requestList,
                },
                "set_is_da_dc": {
                    "name": "Set is_da_dc=TRUE to all objects that are domain controller or domain admins",
                    "request": "MATCH (u) WHERE (u.is_da=true OR u.is_dc=true) "
                    "SET u.is_da_dc=true",
                    "filename": "set_is_da_dc",
                    "method": self.requestList,
                },
                # Recursivity = 5 seems the good match for ratio results/time when searching MemberOf*1..X when using with Carbon/or Helium (else 3)
                "set_groups_members_count": {
                    "name": "Set members_count to groups (recursivity = 5)",
                    "request": "MATCH  (g:Group) WITH g ORDER BY g.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH (u:User)-[:MemberOf*1..5]->(g) "
                    "WHERE NOT u.name IS NULL AND NOT g.name IS NULL "
                    "WITH g AS g1, count(u) AS memberscount "
                    "SET g1.members_count=memberscount",
                    "filename": "set_groups_members_count",
                    "method": self.requestList,
                    "scope_query":"MATCH (g:Group) RETURN count(g)"
                },
                "set_groups_has_members": {
                    "name": "Set has_member=True to groups with member, else false ",
                    "request": "MATCH (g:Group) "
                    "SET g.has_members=(CASE WHEN g.members_count>0 THEN TRUE ELSE FALSE END) ",
                    "filename": "set_groups_has_members",
                    "method": self.requestList,
                },
                # Not used anymore and possibly buggy
                # "set_x_nbr_adm_machines": {
                #     "name": "Set the number of machines where Computers, Users, or Groups are admin (if too long, set recursivity to 3 into the query)",
                #     "request": "OPTIONAL MATCH (u:User) "
                #     "WITH COLLECT (DISTINCT u) AS u1 "
                #     "OPTIONAL MATCH (c:Computer) "
                #     "WITH COLLECT(DISTINCT c) + u1 AS o1 "
                #     "OPTIONAL MATCH (g:Group) "
                #     "WITH COLLECT(DISTINCT g) + o1 AS o2 "
                #     "UNWIND o2 AS o "
                #     "MATCH (o) WITH o ORDER BY o.name "
                #     "MATCH p=(o)-[:AdminTo*1..3]->(c:Computer) "
                #     "WITH count(p) as nbr_admin, o.name as username "
                #     "MATCH (o) "
                #     "WHERE o.name=username "
                #     "SET o.nbr_adm_machines=nbr_admin ",
                #     "filename": "set_x_nbr_adm_machines",
                #     "method": self.requestList,
                # },
                "set_gpo_links_count": {
                    "name": "Set the count of links/object where the GPO is applied",
                    "request": "MATCH p=(g:GPO)-[:GPLink]->(o) "
                    "WITH g.name as gponame, count(p) AS gpolinkscount "
                    "MATCH (g1:GPO) "
                    "WHERE g1.name=gponame AND gpolinkscount IS NOT NULL "
                    "SET g1.gpolinks_count=gpolinkscount ",
                    "filename": "set_gpo_links_count",
                    "method": self.requestList,
                },
                "set_gpos_has_links": {
                    "name": "Set has_links=True to GPOs with links, else false ",
                    "request": "MATCH (g:GPO) "
                    "SET g.has_links=(CASE WHEN g.gpolinks_count>0 THEN TRUE ELSE FALSE END) ",
                    "filename": "set_gpos_has_links",
                    "method": self.requestList,
                },
                "set_is_adcs": {
                    "name": "Set is_adcs to ADCS servers",
                    "request": "MATCH (g:Group) WHERE g.name STARTS WITH 'CERT PUBLISHERS@' "
                    "MATCH (c:Computer)-[r:MemberOf*1..4]->(g) "
                    "SET c.is_adcs=TRUE "
                    "RETURN c.domain AS domain, c.name AS name",
                    "filename": "set_is_adcs",
                    "method": self.requestDict,
                },
                # This block of requests aims at optimizing the path requests by tagging interesting nodes
                "set_groups_direct_admin": {
                    "name": "Set groups which are direct admins of computers",
                    "request": "MATCH (g:Group)-[r:AdminTo]->(c:Computer) "
                    "SET g.is_admin=true RETURN DISTINCT g",
                    "filename": "set_groups_direct_admin",
                    "method": self.requestList,
                },
                # TODO : write a clean recursion, not 4 times the same request
                "set_groups_indirect_admin_1": {
                    "name": "1 - Set groups which are indirect admins of computers, ie. admins of admin groups (see precedent request)",
                    "request": "MATCH (g:Group)-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "SET g.is_admin=true RETURN DISTINCT g",
                    "filename": "set_groups_indirect_admin_1",
                    "method": self.requestList,
                },
                "set_groups_indirect_admin_2": {
                    "name": "2 - Set groups which are indirect admins of computers, ie. admins of admin groups (see precedent request)",
                    "request": "MATCH (g:Group{is_admin:false})-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "SET g.is_admin=true RETURN DISTINCT g",
                    "filename": "set_groups_indirect_admin_2",
                    "method": self.requestList,
                },
                "set_groups_indirect_admin_3": {
                    "name": "3 - Set groups which are indirect admins of computers, ie. admins of admin groups (see precedent request)",
                    "request": "MATCH (g:Group{is_admin:false})-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "SET g.is_admin=true RETURN DISTINCT g",
                    "filename": "set_groups_indirect_admin_3",
                    "method": self.requestList,
                },
                "set_groups_indirect_admin_4": {
                    "name": "4 - Set groups which are indirect admins of computers, ie. admins of admin groups (see precedent request)",
                    "request": "MATCH (g:Group{is_admin:false})-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "SET g.is_admin=true RETURN DISTINCT g",
                    "filename": "set_groups_indirect_admin_4",
                    "method": self.requestList,
                },
                "nb_domain_collected": {
                    "name": "Count number of domains collected",
                    "request": "MATCH (m:Domain)-[r]->() "
                    "RETURN distinct(m.domain)",
                    "filename": "nb_domain_collected",
                    "method": self.requestList,
                },
                "get_count_of_member_admin_group": {
                    "name": "Count number of users in group",
                    "request": "MATCH (u:User{enabled:true})-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "WHERE NOT u.name IS NULL and NOT gg.name IS NULL "
                    "WITH count(u) as count, gg as g MATCH (g) SET g.user_members_count=count",
                    "filename": "get_count_of_member_admin_group",
                    "method": self.requestList,
                },
                "get_users_linked_admin_group": {
                    "name": "Returns all users member of an admin group",
                    "request": "MATCH (u:User{enabled:true})-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "WHERE NOT u.name IS NULL and NOT gg.name IS NULL "
                    "SET u.is_admin=true "
                    "RETURN u, gg, ID(u) as idu, ID(gg) as idg",
                    "filename": "get_users_linked_admin_group",
                    "method": self.requestDict,
                },
                "get_groups_linked_admin_group": {
                    "name": "Returns all groups member of an admin group",
                    "request": "MATCH (g:Group)-[r:MemberOf]->(gg:Group{is_admin:true}) "
                    "WHERE NOT g.name IS NULL and NOT gg.name IS NULL "
                    "RETURN g, gg, ID(g) as idg, ID(gg) as idgg",
                    "filename": "get_groups_linked_admin_group",
                    "method": self.requestDict,
                },
                "get_computers_linked_admin_group": {
                    "name": "Returns all computers administrated by an admin group",
                    "request": "MATCH (g:Group{is_admin:true})-[r:AdminTo]->(c:Computer) "
                    "WHERE NOT c.name IS NULL and NOT g.name IS NULL "
                    "RETURN g, c, ID(g) as idg, ID(c) as idc",
                    "filename": "get_computers_linked_admin_group",
                    "method": self.requestDict,
                },
                "get_users_direct_admin": {
                    "name": "Return direct admin users",
                    "request": "MATCH (g:User{enabled:true})-[r:AdminTo]->(c:Computer) "
                    "WHERE NOT g.name IS NULL and NOT c.name IS NULL "
                    "SET g.is_admin=True "
                    "RETURN g, c, ID(g) as idg, ID(c) as idc",
                    "filename": "get_users_direct_admin",
                    "method": self.requestDict,
                },
                "set_ghost_computer": {
                    "name": "Set ghost_computer=TRUE to computers that did not login for more than 90 days",
                    "request": "MATCH (n:Computer) WHERE toInteger((%d - n.lastlogontimestamp)/86400)>%s "
                    "SET   n.ghost_computer=TRUE"
                    % (extract_date, self.password_renewal),
                    "filename": "set_ghost_computer",
                    "method": self.requestList,
                },
                "domains": {
                    "name": "List of domains",
                    "request": "MATCH (m:Domain) RETURN DISTINCT(m.name) AS domain ORDER BY m.name",
                    "filename": "domains",
                    "method": self.requestList,
                },
                "nb_domain_controllers": {
                    "name": "Number of domain controllers",
                    "request": "MATCH (c1:Computer{is_dc:TRUE}) "
                    "RETURN DISTINCT(c1.domain) AS domain, c1.name AS name, COALESCE(c1.operatingsystem, 'Unknown') AS os, COALESCE(c1.ghost_computer, False) AS ghost",
                    "filename": "nb_domain_controllers",
                    "method": self.requestDict,
                },
                "domain_OUs": {
                    "name": "Domain Organisational Units",
                    "request": "MATCH (o:OU)-[:Contains]->(c) RETURN o.name AS OU, c.name AS name",
                    "filename": "domain_OUs",
                    "method": self.requestDict,
                },
                "users_shadow_credentials": {
                    "name": "Non privileged users that can impersonate privileged users",
                    "request": #"CALL { "
                    "MATCH (u:User{enabled:true,is_da:false}) WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=allShortestPaths((u)-[r:MemberOf|AddKeyCredentialLink|WriteProperty|GenericAll|GenericWrite|Owns|WriteDacl*1..3]->(m:User{is_da:true,enabled:true})) "
                    "RETURN p ",
                    #"UNION ALL "
                    #"MATCH (u:User{enabled:true,is_da:false}) WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    #"MATCH p=(u:User{enabled:true,is_da:false})-[r2:MemberOf*1..5]->(g:Group)-[r3:AddKeyCredentialLink|WriteProperty|GenericAll|GenericWrite|Owns|WriteDacl*1..3]->(m:User{is_da:true,enabled:true}) "
                    #"RETURN p"
                    #"} "
                    #"RETURN DISTINCT p",
                    "filename": "users_shadow_credentials",
                    "scope_query": "MATCH (u:User{is_da:false, enabled:true}) return count(u)",
                    "method": self.requestGraph,
                },
                "users_shadow_credentials_to_non_admins": {
                    "name": "Non privileged users that can be impersonated by non privileged users",
                    "request":"CALL {"
                    "MATCH (u:User{enabled:true,is_da:false}) WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=shortestPath((u)-[r:AddKeyCredentialLink|WriteProperty|GenericAll|GenericWrite|Owns|WriteDacl*1..3]->(m:User{enabled:true})) "
                    "WHERE u<>m "
                    "RETURN p "
                    "UNION ALL "
                    "MATCH (g:Group{is_dag:false,is_da:false})  WITH g ORDER BY g.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=shortestPath((g:Group{is_dag:false,is_da:false})-[r3:AddKeyCredentialLink|WriteProperty|GenericAll|GenericWrite|Owns|WriteDacl*1..3]->(m:User{enabled:true})) "
                    "RETURN p"
                    "} "
                    "RETURN distinct p",
                    "scope_query": "MATCH (u:User {enabled:true, is_da:false}) "
                    "WITH count(u) AS user_count "
                    "MATCH (g:Group {is_dag:false, is_da:false}) "
                    "WITH user_count, count(g) AS group_count "
                    "RETURN CASE WHEN user_count > group_count THEN user_count ELSE group_count END AS max_count",
                    "filename": "users_shadow_credentials_to_non_admins",
                    "method": self.requestGraph,
                },
                "nb_total_accounts": {
                    "name": "Number of domain accounts",
                    "request": "MATCH p=(u:User) RETURN DISTINCT(u.name) AS user",
                    "filename": "nb_total_accounts",
                    "method": self.requestDict,
                },
                "nb_enabled_accounts": {
                    "name": "Number of domain accounts enabled",
                    "request": "MATCH p=(u:User{enabled:true} ) "
                    "RETURN DISTINCT(u.domain) AS domain, u.name AS name, toInteger((%d - u.lastlogontimestamp)/86400) AS logon "
                    "ORDER BY u.domain" % extract_date,
                    "filename": "nb_enabled_accounts",
                    "method": self.requestDict,
                },
                "nb_disabled_accounts": {
                    "name": "Number of domain accounts disabled",
                    "request": "MATCH p=(u:User{enabled:false} ) RETURN DISTINCT(u.name) AS user",
                    "filename": "nb_disabled_accounts",
                    "method": self.requestDict,
                },
                "nb_groups": {
                    "name": "Number of groups",
                    "request": "MATCH p=(g:Group) WHERE NOT g.name IS NULL AND NOT g.domain IS NULL RETURN DISTINCT(g.domain) AS domain, g.name AS name, g.is_da AS da ORDER BY g.domain",
                    "filename": "nb_groups",
                    "method": self.requestDict,
                },
                "nb_computers": {
                    "name": "Number of computers",
                    "request": "MATCH (c:Computer) WHERE NOT c.name IS NULL "
                    "RETURN DISTINCT(c.domain) AS domain, c.name AS name, c.operatingsystem AS os, c.ghost_computer AS ghost ORDER BY c.domain",
                    "filename": "nb_computers",
                    "method": self.requestDict,
                },
                "computers_not_connected_since": {
                    "name": "Computers not connected since",
                    "request": "MATCH (c:Computer) WHERE NOT c.lastlogontimestamp IS NULL AND c.name IS NOT NULL RETURN c.name AS name, toInteger((%d - c.lastlogontimestamp)/86400) AS days ORDER BY days DESC "
                    % extract_date,
                    "filename": "computers_not_connected_since",
                    "method": self.requestDict,
                },
                "nb_domain_admins": {
                    "name": "Number of domain admin accounts",
                    "request": 'MATCH (n{enabled:true}) '
                    'WHERE n.is_da = TRUE '
                    'RETURN n.domain AS domain, n.name AS name, n.da_types AS `admin type`',
                    "filename": "nb_domain_admins",
                    "method": self.requestDict,
                },
                "os": {
                    "name": "Number of OS",
                    "request": "MATCH (c:Computer{enabled:true}) WHERE  NOT c.enabled IS NULL AND NOT c.operatingsystem IS NULL RETURN DISTINCT(c.operatingsystem) AS os, toInteger((%d - c.lastlogontimestamp)/86400) as lastLogon, c.name AS name, c.domain AS domain ORDER BY c.operatingsystem"
                    % extract_date,
                    "filename": "os",
                    "method": self.requestDict,
                },
                "krb_pwd_last_change": {
                    "name": "Kerberos password last change in days",
                    "request": 'MATCH(u:User) WHERE u.name STARTS WITH "KRBTGT@" RETURN u.domain as domain, u.name as name, toInteger((%d - u.pwdlastset)/86400) as pass_last_change, toInteger((%d - u.whencreated)/86400) AS accountCreationDate'
                    % (extract_date, extract_date),
                    "filename": "krb_pwd_last_change",
                    "method": self.requestDict,
                },
                "nb_kerberoastable_accounts": {
                    "name": "Number of Kerberoastable accounts",
                    "request": "MATCH (u:User{hasspn:true,enabled:true}) "
                    "WHERE u.name IS NOT NULL "
                    "RETURN u.domain AS domain, u.name AS name, toInteger((%d - u.pwdlastset)/86400) AS pass_last_change, u.is_da AS is_Domain_Admin, u.serviceprincipalnames AS SPN, toInteger((%d - u.whencreated)/86400) AS accountCreationDate ORDER BY pass_last_change DESC"
                    % (extract_date, extract_date),
                    "filename": "nb_kerberoastable_accounts",
                    "method": self.requestDict,
                },
                "nb_as-rep_roastable_accounts": {
                    "name": "Number of AS-REP Roastable accounts",
                    "request": "MATCH (u:User{enabled:true,dontreqpreauth: true}) RETURN u.domain AS domain,u.name AS name, u.is_da AS is_Domain_Admin",
                    "filename": "nb_as-rep_roastable_accounts",
                    "method": self.requestDict,
                },
                "nb_computer_unconstrained_delegations": {
                    "name": "Number of machines with unconstrained delegations",
                    "request": "MATCH (c2:Computer{unconstraineddelegation:true,is_dc:FALSE}) "
                    "RETURN DISTINCT(c2.domain) AS domain,c2.name AS name",
                    "filename": "nb_computer_unconstrained_delegations",
                    "method": self.requestDict,
                },
                "nb_users_unconstrained_delegations": {
                    "name": "Number of users with unconstrained delegations",
                    "request": "MATCH (c2:User{enabled:true,unconstraineddelegation:true,is_da:FALSE}) "
                    "RETURN DISTINCT(c2.domain) AS domain,c2.name AS name",
                    "filename": "nb_users_unconstrained_delegations",
                    "method": self.requestDict,
                },
                "users_constrained_delegations": {
                    "name": "Number of users with constrained delegations",
                    "request": "MATCH (u:User)-[:AllowedToDelegate]->(c:Computer) "
                    "WHERE u.name IS NOT NULL AND c.name IS NOT NULL "
                    "RETURN u.name AS name, c.name AS computer,c.is_dc as to_DC ORDER BY name",
                    "filename": "users_constrained_delegations",
                    "method": self.requestDict,
                },
                "nb_never_used_accounts": {
                    "name": "Number of enabled and never used " "accounts",
                    "request": "MATCH (n:User) WHERE n.lastlogontimestamp=-1.0 AND n.enabled=TRUE "
                    "RETURN DISTINCT(n.name) ORDER BY n.name",
                    "filename": "nb_never_used_accounts",
                    "method": self.requestDict,
                },
                "dormant_accounts": {
                    "name": "Dormant accounts",
                    "request": "MATCH (n:User{enabled:true}) WHERE toInteger((%d - n.lastlogontimestamp)/86400)>%s "
                    "RETURN n.domain as domain, n.name as name,toInteger((%d - n.lastlogontimestamp)/86400) AS days, toInteger((%d - n.whencreated)/86400) AS accountCreationDate "
                    "ORDER BY days DESC"
                    % (extract_date, self.password_renewal, extract_date, extract_date),
                    "filename": "dormant_accounts",
                    "method": self.requestDict,
                },
                "password_last_change": {
                    "name": "Password last change in days",
                    "request": "MATCH (c:User {enabled:TRUE}) "
                    "RETURN DISTINCT(c.name) AS user,toInteger((%d - c.pwdlastset )/ 86400) AS days, toInteger((%d - c.whencreated)/86400) AS accountCreationDate "
                    "ORDER BY days DESC" % (extract_date, extract_date),
                    "filename": "password_last_change",
                    "method": self.requestDict,
                },
                "nb_user_password_cleartext": {
                    "name": "Number of accounts where password cleartext password is populated",
                    "request": "MATCH (u:User) WHERE NOT u.userpassword IS null "
                    'RETURN u.name AS user,"[redacted for security purposes]" AS password, u.is_da as `is Domain Admin`',
                    "filename": "nb_user_password_cleartext",
                    "method": self.requestDict,
                },
                "get_users_password_not_required": {
                    "name": "Number of accounts where password is not required",
                    "request": "MATCH (u:User{enabled:true,passwordnotreqd:true}) "
                    "RETURN DISTINCT (u.domain) as domain, (u.name) AS user,toInteger((%d - u.pwdlastset )/ 86400) AS pwdlastset,toInteger((%d - u.lastlogontimestamp)/86400) AS lastlogon" % (extract_date, extract_date),
                    "filename": "get_users_password_not_required",
                    "method": self.requestDict,
                },
                "nb_dormant_accounts_by_domain": {
                    "name": "Number of sleeping accounts per domain",
                    "request": "MATCH (n:User) WHERE n.lastlogontimestamp=-1.0 "
                    "RETURN DISTINCT(n.domain), count(n.domain) ORDER BY count(n.domain) DESC",
                    "filename": "nb_dormant_accounts_by_domain",
                    "method": self.requestDict,
                },
                "objects_admincount": {
                    "name": "N objects have AdminSDHolder",
                    "request": "MATCH (n{enabled:True, admincount:True}) RETURN n.domain as domain, labels(n)[1] as type, n.name as name ",
                    # FIXME the UNION is messing up the AS and breaks the grid
                    #                      'UNION MATCH (n{admincount:true}) RETURN n.domain as domain, labels(n)[1] as type, n.name as name',
                    "filename": "objects_admincount",
                    "method": self.requestDict,
                },
                "user_last_logon_in_days": {
                    "name": "Last logon in days",
                    "request": "MATCH (n:User) WHERE n.enabled=TRUE "
                    "RETURN DISTINCT(n.name),toInteger((%d - n.lastlogontimestamp)/86400) AS days, n.name AS user,n.domain AS domain"
                    % extract_date,
                    "filename": "user_last_logon_in_days",
                    "method": self.requestDict,
                },
                "user_password_never_expires": {
                    "name": "Password never expired",
                    "request": "MATCH (u:User{enabled:true})"
                    "WHERE u.pwdneverexpires = true "
                    "RETURN DISTINCT(u.domain) AS domain, u.name AS name, toInteger((%d - u.lastlogontimestamp)/86400) AS LastLogin, toInteger((%d - u.pwdlastset )/ 86400) AS LastPasswChange,toInteger((%d - u.whencreated)/86400) AS accountCreationDate" % (extract_date, extract_date, extract_date),
                    "filename": "user_password_never_expires",
                    "method": self.requestDict,
                },
                "users_domain_breakdown": {
                    "name": "Domain accounts breakdown",
                    "request": "MATCH p=(u:User{enabled:true}) "
                    "RETURN DISTINCT(u.domain) AS domain,COUNT(u.name) AS user ORDER BY u.domain",
                    "filename": "users_domain_breakdown",
                    "method": self.requestDict,
                },
                "computers_domain_breakdown": {
                    "name": "Domain computers breakdown",
                    "request": "MATCH p=(u:Computer{enabled:true}) RETURN DISTINCT(u.domain) AS domain,COUNT(u.name) AS computer ORDER BY u.domain ",
                    "filename": "computers_domain_breakdown",
                    "method": self.requestDict,
                },
                "computers_members_high_privilege": {
                    "name": "High privilege group computer member",
                    "request": "MATCH(c:Computer{is_dc:false})-[r:MemberOf*1..4]->(g:Group{highvalue:true}) "
                    "WHERE NOT c.name IS NULL RETURN distinct(c.name) AS computer, g.name AS group, g.domain AS domain",
                    "filename": "computers_members_high_privilege",
                    "method": self.requestDict,
                },
                "objects_to_domain_admin": {
                    "name": "Objects with path to DA",
                    "request": "MATCH (m{path_candidate:true}) WHERE NOT m.name IS NULL "
                    "WITH m ORDER BY m.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p = shortestPath((m)-[r:%s*1..%s]->(g:Group{is_dag:true})) "
                    "WHERE m<>g "
                    "SET m.has_path_to_da=true "
                    "RETURN DISTINCT(p) as p" % (properties, recursive_level),
                    "filename": "objects_to_domain_admin",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (m{path_candidate:true}) WHERE NOT m.name IS NULL "
                    "RETURN count(m)",
                },
                "objects_to_adcs": {
                    "name": "Objects with path to ADCS servers",
                    "request": "MATCH (o{path_candidate:true}) WHERE NOT o.name IS NULL "
                    "WITH o ORDER BY o.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=(o)-[rrr:MemberOf*1..4]->(gg:Group)-[rr:AdminTo]->(c) "
                    "WHERE c.is_adcs = TRUE "
                    "RETURN DISTINCT(p) as p",
                    "filename": "objects_to_adcs",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (m{path_candidate:true}) WHERE NOT m.name IS NULL "
                    "RETURN count(m)",
                },
                "users_admin_on_computers": {
                    "name": "Users admin on machines",
                    "request": "MATCH p=(n:User{enabled:true})-[r:MemberOf|AdminTo*1..4]->(m:Computer) "
                    "WHERE n:User AND n.enabled=true "
                    "RETURN distinct(n.name) AS user,m.name AS computer,m.has_path_to_da AS has_path_to_da",
                    "filename": "users_admin_on_computers",
                    "method": self.requestDict,
                },
                "users_admin_on_servers_1": {
                    "name": "Users admin on servers n°1",
                    "request": "MATCH p=(n:User{enabled:true,is_da:false}) "
                    "WHERE NOT n.name IS NULL MATCH (n)-[r:MemberOf*1..4]->(g:Group)-[r1:%s]->(u:Computer) WITH LENGTH(p) as pathLength, p, n, u SKIP PARAM1 LIMIT PARAM2 "
                    "WHERE NONE (x in NODES(p)[1..(pathLength-1)] "
                    "WHERE x.objectid = u.objectid) AND NOT n.objectid = u.objectid "
                    "RETURN n.name AS user, u.name AS computer, u.has_path_to_da as has_path_to_da"
                    % (properties),
                    "filename": "users_admin_on_servers_1",
                    "scope_query": "MATCH (n:User{enabled:true,is_da:false}) WHERE NOT n.name IS NULL "
                    "RETURN count(n)",
                    "method": self.requestDict,
                },
                "users_admin_on_servers_2": {
                    "name": "Users admin on servers n°2",
                    "request": "MATCH p=(n:User{enabled:true,is_da:false}) "
                    "WHERE NOT n.name IS NULL MATCH (n)-[r1:%s]->(u:Computer) WITH LENGTH(p) as pathLength, p, n, u SKIP PARAM1 LIMIT PARAM2 "
                    "WHERE NONE (x in NODES(p)[1..(pathLength-1)] "
                    "WHERE x.objectid = u.objectid) AND NOT n.objectid = u.objectid "
                    "RETURN n.name AS user, u.name AS computer, u.has_path_to_da as has_path_to_da"
                    % (properties),
                    "filename": "users_admin_on_servers_2",
                    "scope_query": "MATCH (n:User{enabled:true,is_da:false}) WHERE NOT n.name IS NULL "
                    "RETURN count(n)",
                    "method": self.requestDict,
                },
                "computers_admin_on_computers": {
                    "name": "Number of computers admin of computers",
                    "request": "CALL{"
                    "MATCH (c1:Computer)-[r1:AdminTo]->(c2:Computer) WHERE c1.name IS NOT NULL AND c2.name IS NOT NULL AND c1 <> c2 RETURN c1.name AS source_computer, c2.name AS target_computer, c2.has_path_to_da AS has_path_to_da "
                    "UNION ALL "
                    "MATCH (c1:Computer)-[r2:MemberOf*1..4]->(g:Group)-[r3:AdminTo]->(c2:Computer) WHERE c1.name IS NOT NULL AND c2.name IS NOT NULL AND c1 <> c2 RETURN c1.name AS source_computer, c2.name AS target_computer, c2.has_path_to_da AS has_path_to_da}  "
                    "RETURN distinct(source_computer), target_computer, has_path_to_da",
                    "filename": "computers_admin_on_computers",
                    "method": self.requestDict,
                },
                "domain_map_trust": {
                    "name": "Domain map trust",
                    "request": "MATCH p=shortestpath((d:Domain)-[:TrustedBy]->(m:Domain)) "
                    "WHERE d<>m RETURN DISTINCT(p)",
                    "request2": "MATCH p=(c1:Computer)-[r2:MemberOf*1..4]->(g:Group)-[r3:AdminTo]->(c2:Computer) RETURN p",
                    "filename": "domain_map_trust",
                    "method": self.requestGraph,
                },
                "objects_to_unconstrained_delegation": {
                    "name": "Object with path to non-DC computers with unconstrained delegations ",
                    "request": "MATCH (n{path_candidate:true}) WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 MATCH p=shortestPath((n)-[:%s*1..%s]->(m:Computer{unconstraineddelegation:true,is_dc:false})) "
                    "WHERE NOT n=m "
                    "AND NOT m.name IS NULL RETURN DISTINCT(p)"
                    % (properties, recursive_level),
                    "filename": "objects_to_unconstrained_delegation",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (n{path_candidate:true}) " "RETURN count(n)",
                },
                "users_to_unconstrained_delegation": {
                    "name": "Objects with paths to users that have unconstrained delegations ",
                    "request": "MATCH (n{path_candidate:true}) WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 MATCH p=shortestPath((n:User{is_da:false,enabled:true})-[:%s*1..%s]->(m:User{unconstraineddelegation:true,enabled:true,sensitive:false})) "
                    "WHERE NOT n=m AND "
                    "NOT m.name IS NULL RETURN DISTINCT(p)"
                    % (inbound_control_edges, recursive_level),
                    "filename": "users_to_unconstrained_delegation",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (n{path_candidate:true}) " "RETURN count(n)",
                },
                "nb_computers_laps": {
                    "name": "Number of computers with laps",
                    "request": "MATCH (c:Computer) WHERE NOT c.name is NULL and NOT c.haslaps IS NULL AND c.operatingsystem CONTAINS 'indows' "
                    "RETURN DISTINCT(c.domain) AS domain, toInteger((%d - c.lastlogontimestamp)/86400) as lastLogon, c.name AS name, toString(c.haslaps) AS LAPS"
                    % extract_date,
                    "filename": "nb_computers_laps",
                    "method": self.requestDict,
                },
                "can_read_laps": {
                    "name": "Objects allowed to read LAPS",
                    "request": "MATCH p = (n)-[r1:MemberOf*1..]->(g:Group)-[r2:GenericAll]->(t:Computer {haslaps:true}) "
                    "RETURN distinct(n.domain) AS domain, n.name AS name",
                    "filename": "can_read_laps",
                    "method": self.requestDict,
                },
                "objects_to_dcsync": {
                    "name": "Objects to dcsync",
                    "request": "MATCH (n{path_candidate:true}) WHERE n.can_dcsync IS NULL AND NOT n.name IS NULL WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p = shortestPath((n)-[r:%s*1..%s]->(target{can_dcsync:TRUE})) "
                    "WHERE n<>target "
                    "RETURN distinct(p) AS p" % (properties, recursive_level),
                    "filename": "objects_to_dcsync",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (n{path_candidate:true}) WHERE n.can_dcsync IS NULL AND NOT n.name IS NULL "
                    "RETURN count(n)",
                },
                "dom_admin_on_non_dc": {
                    "name": "Domain admin with session on non DC computers",
                    "request": "MATCH p=(c:Computer)-[r:HasSession]->(u:User{enabled:true, is_da:true}) "
                    "WHERE NOT c.name IS NULL and NOT u.name IS NULL and NOT c.is_dc=True "
                    "RETURN distinct(p) AS p",
                    "filename": "dom_admin_on_non_dc",
                    "method": self.requestGraph,
                },
                "unpriv_to_dnsadmins": {
                    "name": "Unprivileged users with path to DNSAdmins",
                    "request": "MATCH (u:User{path_candidate:true}) "
                    "WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=(u)-[r:MemberOf*1..%s]->(g:Group{is_dnsadmin:true}) "
                    "RETURN distinct(p) AS p" % recursive_level,
                    "filename": "unpriv_to_dnsadmins",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (u:User{path_candidate:true}) "
                    "RETURN count(u)",
                },
                "rdp_access": {
                    "name": "Users with RDP-access to Computers ",
                    "request": "CALL{"
                    "MATCH p=(n:User{enabled:true,is_da:false})-[r1:MemberOf*1..5]->(m:Group)-[r2:CanRDP]->(c:Computer) "
                    "RETURN n,c "
                    "UNION ALL "
                    "MATCH p=(n:User{enabled:true,is_da:false})-[r2:CanRDP]->(c:Computer) "
                    "RETURN n,c "
                    "}"
                    "RETURN DISTINCT n.name AS user, c.name as computer",
                    "filename": "rdp_access",
                    "method": self.requestDict,
                },
                "dc_impersonation": {
                    "name": "Non-domain admins that can directly or indirectly impersonate a Domain Controller ",
                    "request": "CALL{"
                    "MATCH p=(u{ou_candidate:true})-[r:MemberOf*1..5]->(g:Group)-[r3:AddKeyCredentialLink|WriteProperty|GenericAll|GenericWrite|Owns|WriteDacl]->(m:Computer{is_dc:true}) "
                    "RETURN p "
                    "UNION ALL "
                    "MATCH p=(u{ou_candidate:true})-[r3:AddKeyCredentialLink|WriteProperty|GenericAll|GenericWrite|Owns|WriteDacl]->(m:Computer{is_dc:true}) "
                    "RETURN p "
                    "}"
                    "RETURN DISTINCT p",
                    "filename": "dc_impersonation",
                    "method": self.requestGraph,
                },
                "rbcd": {
                    "name": "RBCD attacks",
                    "request": "CALL{"
                    "MATCH (u:User{enabled:true,is_da:false}) "
                    "WHERE u.name IS NOT NULL "
                    "WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH (u:User{enabled:true,is_da:false})-[rr:MemberOf*1..5]->(g:Group)-[r:GenericAll|GenericWrite|WriteDACL|AllExtendedRights|Owns|AdminTo]->(m:Computer{is_server:true}) "
                    "RETURN u as user, g.name as groupname, r, m "
                    "UNION ALL "
                    "MATCH (u:User{enabled:true,is_da:false}) "
                    "WHERE u.name IS NOT NULL "
                    "WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH (u:User{enabled:true,is_da:false})-[r:GenericAll|GenericWrite|WriteDACL|AllExtendedRights|Owns|AdminTo]->(m:Computer{is_server:true}) "
                    'RETURN u as user, "Direct (nogroup)" as groupname, r, m '
                    "}"
                    "RETURN distinct user.name as username, groupname, type(r) as acl, m.name as computername ORDER BY username, computername, acl",
                    "filename": "rbcd",
                    "method": self.requestDict,
                    "scope_query": "MATCH (u:User{enabled:true,is_da:false}) "
                    "RETURN count(u)",
                },
                "graph_rbcd": {
                    "name": "Builds RBCD attack path graph and sets is_rbcd_target attribute ",
                    "request": "CALL{ "
                    "MATCH p1=(u:User{enabled:true,is_da:false})-[rr:MemberOf|AddMember*1..5]->(g:Group)-[r:GenericAll|GenericWrite|WriteDACL|AllExtendedRights|Owns|AdminTo]->(m:Computer{is_server:true}) "
                    "SET m.is_rbcd_target=TRUE "
                    "RETURN p1 as p "
                    "UNION ALL "
                    "MATCH p2=(u:User{enabled:true,is_da:false})-[r:GenericAll|GenericWrite|WriteDACL|AllExtendedRights|Owns|AdminTo]->(m:Computer{is_server:true}) "
                    "SET m.is_rbcd_target=TRUE "
                    "RETURN p2 as p "
                    "} "
                    "RETURN p",
                    "filename": "graph_rbcd",
                    "method": self.requestGraph,
                },
                "graph_rbcd_to_da": {
                    "name": "Builds RBCD targets to DA paths",
                    "request": "MATCH (m:Computer{is_rbcd_target:true}) WHERE NOT m.name IS NULL "
                    "WITH m ORDER BY m.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p = shortestPath((m)-[r:%s*1..%s]->(g:Group{is_dag:true})) "
                    "WHERE m<>g "
                    "RETURN DISTINCT(p) as p" % (properties, recursive_level),
                    "filename": "graph_rbcd_to_da",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (m:Computer{is_rbcd_target:true}) WHERE NOT m.name IS NULL "
                    "RETURN count(m)",
                },
                "objects_to_ou_handlers": {
                    "name": "paths to objects that can link a gpo on an OU",
                    "request": "MATCH (u{ou_candidate:true}) WITH u ORDER BY u.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p1=shortestPath((u)-[:MemberOf|GenericAll|GenericWrite|Owns|WriteOwner|WriteDacl*1..8]->(o:OU{contains_da_dc:true})) WHERE NOT u=o "
                    "CALL{"
                    "WITH p1,o "
                    "RETURN DISTINCT(p1) as p "
                    "UNION ALL "
                    "WITH o "
                    "MATCH p=shortestPath((o:OU{contains_da_dc:true})-[:Contains*1..]->(v{is_da_dc:true})) "
                    "RETURN DISTINCT(p) as p "
                    "}"
                    "RETURN p",
                    "filename": "objects_to_ou_handlers",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (u:Computer{ou_candidate:true}) "
                    "RETURN count(u)",
                },
                "vuln_functional_level": {
                    "name": "Insufficient forest and domains functional levels. According to ANSSI (on a scale from 1 to 5, 5 being the better): the security level is at 1 if functional level (FL) <= Windows 2008 R2, at 3 if FL <= Windows 2012R2, at 4 if FL <= Windows 2016 / 2019 / 2022.",
                    "request": "MATCH (o:Domain) "
                    "WHERE o.functionallevel IS NOT NULL "
                    "RETURN CASE "
                    'WHEN toUpper(o.functionallevel) CONTAINS "2000" OR toUpper(o.functionallevel) CONTAINS "2003" OR toUpper(o.functionallevel) CONTAINS "2008" OR toUpper(o.functionallevel) CONTAINS "2008 R2" THEN 1 '
                    'WHEN toUpper(o.functionallevel) CONTAINS "2012 R2" THEN 2 '
                    'WHEN toUpper(o.functionallevel) CONTAINS "2016" OR toUpper(o.functionallevel) CONTAINS "2018" OR toUpper(o.functionallevel) CONTAINS "2020" OR toUpper(o.functionallevel) CONTAINS "2022" THEN 5 '
                    "END as `Level maturity`, o.distinguishedname as `Full name`, o.functionallevel as `Functional level`",
                    "filename": "vuln_functional_level",
                    "method": self.requestDict,
                },
                "vuln_sidhistory_dangerous": {
                    "name": "Accounts or groups with unexpected SID history",
                    "request": "MATCH(o1)-[r:HasSIDHistory]->(o2{is_da:true}) "
                    "RETURN o1.domain as parent_domain, o1.name as name, o1.sidhistory as sidhistory",
                    "filename": "vuln_sidhistory_dangerous",
                    "method": self.requestDict,
                },
                "can_read_gmsapassword_of_adm": {
                    "name": "Objects allowed to read the GMSA of objects with admincount=True",
                    "request" : "CALL {"
                    "MATCH (o{path_candidate:true}) "
                    "WITH o ORDER BY o.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=((o)-[:MemberOf*1..7]->(g:Group)-[:ReadGMSAPassword]->(u:User{is_admin:true})) "
                    "WHERE o.name<>u.name "
                    "RETURN DISTINCT(p) "
                    "UNION ALL "
                    "MATCH (o{path_candidate:true}) "
                    "WITH o ORDER BY o.name SKIP PARAM1 LIMIT PARAM2 "
                    "MATCH p=((o)-[:ReadGMSAPassword]->(u:User{is_admin:true})) "
                    "WHERE o.name<>u.name "
                    "RETURN DISTINCT(p) "
                    "} "
                    "RETURN p",
                    "filename": "can_read_gmsapassword_of_adm",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (o{path_candidate:true}) "
                    'RETURN count(o)',
                },
                # to do : table with type, account name, is_da (l'étoile) et le nbr de chemin qui mène à lui avec lien vers les chemins
                "objects_to_operators_member": {
                    "name": "Unprivileged users with path to an Operator Member",
                    'request': 'MATCH (m:User{path_candidate:true}) WHERE NOT m.name CONTAINS "MSOL_" '
                    'WITH m ORDER BY m.name SKIP PARAM1 LIMIT PARAM2 '
                    'MATCH p = shortestPath((m)-[r:%s*1..%s]->(o:User{is_operator_member:true})) '
                    'WHERE m<>o AND NOT m.name CONTAINS "MSOL_" '
                    'AND ((o.is_da=true AND o.domain<>m.domain) OR (o.is_da=false AND o.domain=m.domain)) '
                    'RETURN DISTINCT(p) as p' % (properties, recursive_level),
                    "filename": "objects_to_operators_member",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (m:User{path_candidate:true}) WHERE NOT m.name CONTAINS 'MSOL_' "
                    "RETURN count(m)",
                },

                # TO DO : table with les adminsdholder + path with => X objects to SDHolder
                "vuln_permissions_adminsdholder": {
                    "name": "Dangerous permissions on the adminSDHolder object",
                    "request": "MATCH (n:User{path_candidate:true}) "
                    'WHERE NOT n.name CONTAINS "MSOL_" '
                    'WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 '
                    "MATCH p = shortestPath((n)-[r:%s*1..4]->(target1{is_adminsdholder:true})) "
                    'WHERE n<>target1 AND NOT ANY(no in nodes(p) WHERE (no.is_da=true AND (no.domain=target1.domain OR target1.domain CONTAINS "." + no.domain))) '
                    "RETURN distinct(p) AS p" % properties,
                    "filename": "vuln_permissions_adminsdholder",
                    "method": self.requestGraph,
                    "scope_query": "MATCH (n:User{path_candidate:true}) WHERE NOT n.name CONTAINS 'MSOL_' "
                    "RETURN count(n)",
                },
                "da_to_da": {
                    "name": "Paths between two domain admins belonging to different domains",
                    "request": "MATCH p=allShortestPaths((g:Group{is_dag:true})-[r:%s*1..%s]->(gg:Group{is_dag:true})) WHERE g<>gg AND g.domain <> gg.domain RETURN p"
                    % (properties, recursive_level),
                    "filename": "da_to_da",
                    "method": self.requestGraph,
                },
                "group_anomaly_acl": {
                    "name": "group_anomaly_acl",
                    "request": "MATCH (gg:Group) WHERE EXISTS(gg.members_count) with gg as g order by gg.members_count DESC LIMIT 10000 "
                    "MATCH (g)-[r2{isacl:true}]->(n) "
                    "RETURN g.members_count,n.name,g.name, type(r2) order by g.members_count DESC",
                    "filename": "group_anomaly_acl",
                    "method": self.requestDict,
                },
                "get_empty_groups": {
                    "name": "Returns empty groups",
                    "request": "MATCH (g:Group) "
                    "WHERE NOT EXISTS(()-[:MemberOf]->(g)) AND NOT g.distinguishedname CONTAINS 'CN=BUILTIN' "
                    "RETURN g.name AS `Empty group`, COALESCE(g.distinguishedname, '-') AS `Full Reference`",
                    "filename": "get_empty_groups",
                    "method": self.requestDict,
                },
                "get_empty_ous": {
                    "name": "Returns empty ous",
                    "request": "MATCH (o:OU) "
                    "WHERE NOT ()<-[:Contains]-(o) "
                    "RETURN o.name AS `Empty Organizational Unit`, COALESCE(o.distinguishedname, '-') AS `Full Reference`",
                    "filename": "get_empty_ous",
                    "method": self.requestDict,
                },
                "has_sid_history": {
                    "name": "Objects that have a SID History",
                    "request": "MATCH (a)-[r:HasSIDHistory]->(b) "
                    "RETURN a.name AS `Has SID History`, LABELS(a)[0] AS `Type_a`, b.name AS `Target`, LABELS(b)[0] AS `Type_b`",
                    "filename": "has_sid_history",
                    "method": self.requestDict,
                }
            }

        if not arguments.gpo_low:
            # Deep version of GPO requests
            self.all_requests["unpriv_users_to_GPO_init"] = {
                "name": "Initialization request for GPOs [WARNING: If this query is too slow, you can use --gpo_low]",
                "request": 'MATCH (n:User{path_candidate:true}) WHERE NOT n.name IS NULL AND NOT n.name CONTAINS "MSOL_" WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 '
                "MATCH p = shortestPath((n)-[r:MemberOf|AddSelf|WriteSPN|AddKeyCredentialLink|AddMember|AllExtendedRights|ForceChangePassword|GenericAll|GenericWrite|WriteDacl|WriteOwner|Owns*1..]->(g:GPO)) "
                "WHERE NOT n=g AND NOT g.name IS NULL "
                "RETURN p ",
                "filename": "unpriv_users_to_GPO_init",
                "method": self.requestGraph,
                "scope_query": 'MATCH (n:User{path_candidate:true}) WHERE NOT n.name IS NULL AND NOT n.name CONTAINS "MSOL_" '
                "RETURN count(n)",
                "postProcessing": self.setDangerousInboundOnGPOs,
            }

            self.all_requests["unpriv_users_to_GPO_user_enforced"] = {
                "name": "Compromisable GPOs to users (enforced)",
                "request": "MATCH (n:User{enabled:true}) WHERE n.name IS NOT NULL WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 "
                "MATCH p = (g:GPO{dangerous_inbound:true})-[r1:GPLink {enforced:true}]->(container2)-[r2:Contains*1..]->(n) "
                "RETURN p",
                "filename": "unpriv_users_to_GPO_user_enforced",
                "method": self.requestGraph,
                "scope_query": "MATCH (n:User{enabled:true}) WHERE n.name IS NOT NULL "
                "RETURN count(n)",
            }

            self.all_requests["unpriv_users_to_GPO_user_not_enforced"] = {
                "name": "Compromisable GPOs to users (not enforced)",
                "request": "MATCH (n:User{enabled:true}) WHERE n.name IS NOT NULL WITH n ORDER BY n.name SKIP PARAM1 LIMIT PARAM2 "
                "MATCH p = (g:GPO{dangerous_inbound:true})-[r1:GPLink{enforced:false}]->(container1)-[r2:Contains*1..]->(n) "
                'WHERE NONE(x in NODES(p) WHERE x.blocksinheritance = true AND LABELS(x) = "OU") '
                "RETURN p",
                "filename": "unpriv_users_to_GPO_user_not_enforced",
                "method": self.requestGraph,
                "scope_query": "MATCH (n:User{enabled:true}) WHERE n.name IS NOT NULL "
                "RETURN count(n)",
            }

            self.all_requests["unpriv_users_to_GPO_computer_enforced"] = {
                "name": "Compromisable GPOs to computers (enforced)",
                "request": "MATCH (n:Computer) WITH n ORDER BY n.name WITH n SKIP PARAM1 LIMIT PARAM2 "
                "MATCH p = (g:GPO{dangerous_inbound:true})-[r1:GPLink {enforced:true}]->(container2)-[r2:Contains*1..]->(n) "
                "RETURN p",
                "filename": "unpriv_users_to_GPO_computer_enforced",
                "method": self.requestGraph,
                "scope_query": "MATCH (n:Computer) " "RETURN count(n)",
            }

            self.all_requests["unpriv_users_to_GPO_computer_not_enforced"] = {
                "name": "Compromisable GPOs to computers (not enforced)",
                "request": "MATCH (n:Computer) WITH n ORDER BY n.name WITH n SKIP PARAM1 LIMIT PARAM2 "
                "MATCH p = (g:GPO{dangerous_inbound:true})-[r1:GPLink{enforced:false}]->(container1)-[r2:Contains*1..]->(n) "
                'WHERE NONE(x in NODES(p) WHERE x.blocksinheritance = true AND LABELS(x) = "OU") '
                "RETURN p",
                "filename": "unpriv_users_to_GPO_computer_not_enforced",
                "method": self.requestGraph,
                "scope_query": "MATCH (n:Computer) " "RETURN count(n)",
            }

        else:
            # Normal version of GPO request
            self.all_requests["unpriv_users_to_GPO"] = {
                "name": "Non privileged users to GPO",
                "request": "MATCH (g:GPO) "
                "WITH g ORDER BY g.name SKIP PARAM1 LIMIT PARAM2 "
                "OPTIONAL MATCH (g)-[r1:GPLink {enforced:false}]->(container1) "
                "WITH g,container1 "
                "OPTIONAL MATCH (g)-[r2:GPLink {enforced:true}]->(container2) "
                "WITH g,container1,container2 "
                "OPTIONAL MATCH p = (g)-[r1:GPLink]->(container1)-[r2:Contains*1..8]->(n1:Computer) "
                'WHERE NONE(x in NODES(p) WHERE x.blocksinheritance = true AND LABELS(x) = "OU") '
                "WITH g,p,container2,n1 "
                "OPTIONAL MATCH p2 = (g)-[r1:GPLink]->(container2)-[r2:Contains*1..8]->(n2:Computer) "
                "RETURN p",
                "filename": "unpriv_users_to_GPO",
                "method": self.requestGraph,
                "scope_query": "MATCH (g:GPO) RETURN COUNT(g)"
            }

        try:
            # Setup driver
            self.driver = GraphDatabase.driver(
                arguments.bolt,
                auth=(arguments.username, arguments.password),
                encrypted=False,
            )

            # Test connection. Takes ~ 25ms
            with self.driver.session() as session:
                session.begin_transaction().close()

            self.arguments = arguments
            self.cache_enabled = arguments.cache
            self.cache = cache_class.Cache(arguments)
            logger.print_success("Connected to database")

        except Exception as e:
            logger.print_error("Connection to neo4j database impossible.")
            logger.print_error(e)
            sys.exit(-1)

    def close(self):
        self.driver.close()

    def requestDict(self, request):
        if len(self.arguments.cluster) > 0:
            result = self.distributeRequestsOnRemote(self, request, dict)
        else:
            result = self.request(self, request, dict)
        request["result"] = result

    def requestList(self, request):
        if len(self.arguments.cluster) > 0:
            result = self.distributeRequestsOnRemote(self, request, list)
        else:
            result = self.request(self, request, list)
        request["result"] = result

    def requestGraph(self, request):
        if len(self.arguments.cluster) > 0:
            result = self.distributeRequestsOnRemote(self, request, Graph)
        else:
            result = self.request(self, request, Graph)
        request["result"] = result

    @staticmethod
    def run(value, identifier, query, arguments, output_type):
        start_time = time.time()
        q = query.replace("PARAM1", str(value)).replace("PARAM2", str(identifier))
        result = []
        driver = GraphDatabase.driver(
            arguments.bolt,
            auth=(arguments.username, arguments.password),
            encrypted=False,
        )
        with driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(q):
                        result.append(record["p"])

                else:
                    result = tx.run(q)
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()

        if output_type is not dict:
            try:
                result = Neo4j.computePathObject(result)
            except Exception as e:
                logger.print_error(
                    "An error occured during the transformation of a request result."
                )
                errorMessage = "The exact query was:\n" + q
                logger.print_error(errorMessage)
                logger.print_error(e)

        gc.collect()
        return result

    @staticmethod
    def request(self, request, output_type):
        start = time.time()
        if self.cache_enabled:
            result = self.cache.retrieveCacheEntry(request["filename"])
            if result != False:
                if len(result):
                    logger.print_debug(
                        "From cache : %s - %d objects" % (request["name"], len(result))
                    )
                    # self.cache.createCsvFileFromRequest(
                    #    request["filename"], result, output_type
                    # )
                return result
        logger.print_debug("Requesting : %s" % request["name"])

        start_time = time.time()

        # if output_type is Graph:
        result = []
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                if "PARAM" in request["request"]:
                    scopeQuery = request["scope_query"]
                    scopeSize = tx.run(scopeQuery).value()[0]
                    part_number = int(self.arguments.nb_chunks)
                    nb_cores = int(self.arguments.nb_cores)
                    print(
                        f"scope size : {str(scopeSize)} | nb chunks : {part_number} | nb cores : {nb_cores}"
                    )

                    part_number = min(
                        scopeSize, part_number
                    )  # no more requests than scope size
                    items = []
                    space = np.linspace(0, scopeSize, part_number + 1, dtype=int)
                    for i in range(len(space) - 1):
                        items.append(
                            [
                                space[i],
                                space[i + 1] - space[i],
                                request["request"],
                                self.arguments,
                                output_type,
                            ]
                        )

                    with mp.Pool(nb_cores) as pool:
                        # results = pool.starmap(self.run, tqdm.tqdm(items, total=len(items)))
                        # with open("temporary.txt", "a") as f:
                        #     f.write("\n")
                        #     f.write("-------------------------\n")
                        #     f.write(f"{self.arguments.cache_prefix} : {request['name']} \n")
                        result = []
                        for _ in tqdm.tqdm(
                            pool.istarmap(self.run, items), total=len(items)
                        ):
                            result += _

                    # result = self.computePathObject(result)

                else:
                    if output_type is Graph:
                        for record in tx.run(request["request"]):
                            result.append(record["p"])
                            # print("other RESULT : ", result)
                            # Quick and dirty way of handling multiple records (e.g., RETURN p, p2
                            # TODO : possibly improve that ugly code
                            try:
                                result.append(record["p2"])
                            except:
                                pass
                        result = self.computePathObject(result)
                    else:
                        result = tx.run(request["request"])
                        if output_type is list:
                            result = result.values()
                        else:
                            result = result.data()

        self.cache.createCacheEntry(request["filename"], result)
        # self.cache.createCsvFileFromRequest(request["filename"], result, output_type)
        logger.print_time(
            timer_format(time.time() - start) + " - %d objects" % len(result)
        )

        if "postProcessing" in request:
            request["postProcessing"](self, result)

        gc.collect()
        return result

    @staticmethod
    def setDangerousInboundOnGPOs(self, data):
        print("Entering Post processing")
        ids = []
        for d in data:
            ids.append(d.nodes[-1].id)
        q = "MATCH (g) WHERE ID(g) in " + str(ids) + " SET g.dangerous_inbound=TRUE"
        # print(q)
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(q)

    @staticmethod
    def set_extract_date(date):
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])
        date_time = datetime.datetime(year, month, day)
        return time.mktime(date_time.timetuple())

    @staticmethod
    def requestNamesAndHash(server, username, password):
        q = "MATCH (a) RETURN ID(a),a.name"
        bolt = "bolt://" + server

        driver = GraphDatabase.driver(
            bolt,
            auth=(username, password),
            encrypted=False,
        )

        names = ""

        with driver.session() as session:
            with session.begin_transaction() as tx:
                for record in tx.run(q):
                    names += str(record["a.name"])

        driver.close()
        hash = md5(names.encode()).hexdigest()
        logger.print_debug("Hash for " + server + " is " + hash)
        return hash

    @staticmethod
    def verify_integrity(self, cluster):
        """
        Hash the names of all nodes to verify that the same database is on every node.
        """
        startig_time = time.time()
        logger.print_debug("Starting integrity check")
        hashes = []
        temp_results = []
        username = self.arguments.username
        password = self.arguments.password

        with mp.Pool(processes=self.arguments.nb_cores) as pool:
            for server in cluster.keys():
                task = pool.apply_async(
                    Neo4j.requestNamesAndHash,
                    (
                        server,
                        username,
                        password,
                    ),
                )
                temp_results.append(task)

            for task in temp_results:
                try:
                    hashes.append(task.get())
                except Exception as e:
                    errorMessage = "Connection to neo4j database refused."
                    logger.print_error(errorMessage)
                    logger.print_error(e)
                    sys.exit(-1)

        if all(hash == hashes[0] for hash in hashes):
            logger.print_success("All databases seems to be the same.")
        else:
            logger.print_error("Be careful, the database on the nodes seems different.")

        stopping_time = time.time()

        logger.print_time(
            "Integrity check took " + str(round(stopping_time - startig_time, 2)) + "s"
        )

    @staticmethod
    def requestOnRemote(value, identifier, query, arguments, output_type, server):
        start_time = time.time()
        q = query.replace("PARAM1", str(value)).replace("PARAM2", str(identifier))
        result = []
        bolt = "bolt://" + server
        driver = GraphDatabase.driver(
            bolt,
            auth=(arguments.username, arguments.password),
            encrypted=False,
        )

        with driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(q):
                        result.append(record["p"])

                else:
                    result = tx.run(q)
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()

        if output_type is not dict:
            try:
                result = Neo4j.computePathObject(result)
            except Exception as e:
                logger.print_error(
                    "An error occured during the transformation of a request result."
                )
                errorMessage = (
                    "The database used is " + server + " and the exact query was:\n" + q
                )
                logger.print_error(errorMessage)
                logger.print_error(e)

        driver.close()  # TODO pas de base ?
        gc.collect
        return result

    @staticmethod
    def writeRequestOnRemote(query, output_type, server, username, password):
        start_time = time.time()
        result = []
        bolt = "bolt://" + server
        driver = GraphDatabase.driver(
            bolt,
            auth=(username, password),
            encrypted=False,
        )

        with driver.session() as session:
            with session.begin_transaction() as tx:
                if output_type is Graph:
                    for record in tx.run(query):
                        result.append(record["p"])
                        # print("other RESULT : ", result)
                        # Quick and dirty way of handling multiple records (e.g., RETURN p, p2
                        # TODO : possibly improve that ugly code
                        try:
                            result.append(record["p2"])
                        except:
                            pass
                    result = Neo4j.computePathObject(result)
                else:
                    result = tx.run(query)
                    if output_type is list:
                        result = result.values()
                    else:
                        result = result.data()

        driver.close()  # TODO pas de base ?
        duration = round(time.time() - start_time, 2)
        logger.print_debug(
            "Write query executed to " + server + " in " + str(duration) + "s"
        )
        return result

    @staticmethod
    def distributeRequestsOnRemote(self, request, output_type):
        cluster = self.cluster
        # Total CPU units of all node of the cluster
        max_parallel_requests = sum(cluster.values())

        start = time.time()
        if self.cache_enabled:
            result = self.cache.retrieveCacheEntry(request["filename"])
            if result != False:
                if len(result):
                    logger.print_debug(
                        "From cache : %s - %d objects" % (request["name"], len(result))
                    )
                    # self.cache.createCsvFileFromRequest(
                    #    request["filename"], result, output_type
                    # )
                return result
        logger.print_debug("Requesting : %s" % request["name"])

        result = []
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                if "PARAM" in request["request"]:
                    scopeQuery = request["scope_query"]
                    scopeSize = tx.run(scopeQuery).value()[0]
                    part_number = self.arguments.nb_chunks
                    # It is assumed here that no one will set number of chunks to the default.
                    # If left to default but cluster is used it is better to choosesomething
                    # like chunk = 20 x total number of cores in the cluster.
                    if part_number == mp.cpu_count():
                        part_number = 20 * max_parallel_requests
                    nb_cores = int(max_parallel_requests)
                    print(
                        f"scope size : {str(scopeSize)} | nb chunks : {part_number} | nb cores : {nb_cores}"
                    )

                    part_number = min(scopeSize, part_number)
                    items = []
                    space = np.linspace(0, scopeSize, part_number + 1, dtype=int)
                    # Divide the requests with SKIP & LIMIT
                    for i in range(len(space) - 1):
                        items.append(
                            [
                                space[i],
                                space[i + 1] - space[i],
                                request["request"],
                                self.arguments,
                                output_type,
                            ]
                        )

                    requestList = items.copy()

                    pbar = tqdm.tqdm(
                        total=len(requestList), desc="Cluster participation:\n"
                    )

                    temp_results = []

                    with mp.Pool(processes=max_parallel_requests) as pool:

                        # Dict that keep track of which server is executing which requests
                        active_jobs = dict((server, []) for server in cluster)

                        # Dict that keep track of how many queries each server did
                        jobs_done = dict((server, 0) for server in cluster)

                        # Counter to keep track of how many objects have been retrieved
                        number_of_retrieved_objects = 0

                        while len(requestList) > 0:
                            time.sleep(0.01)

                            for server, max_jobs in cluster.items():
                                if len(requestList) == 0:
                                    break
                                for task in active_jobs[server]:
                                    if (
                                        task.ready()
                                    ):  # Meaning that a task have been finished on a remote server

                                        temporary_result = task.get()

                                        if output_type == list:
                                            if len(temporary_result) > 0:
                                                for sublist in temporary_result:
                                                    number_of_retrieved_objects += len(
                                                        sublist
                                                    )
                                        elif (
                                            output_type == dict or output_type == Graph
                                        ):
                                            number_of_retrieved_objects += len(
                                                temporary_result
                                            )

                                        temporary_result = None

                                        active_jobs[server].remove(task)
                                        task = None
                                        jobs_done[server] += 1
                                        total_jobs_done = sum(jobs_done.values())
                                        cluster_participation = ""
                                        for server_running in jobs_done:
                                            server_name = server_running.split(":")[0]
                                            cluster_participation += (
                                                server_name
                                                + ": "
                                                + str(
                                                    int(
                                                        round(
                                                            100
                                                            * jobs_done[server_running]
                                                            / total_jobs_done,
                                                            0,
                                                        )
                                                    )
                                                )
                                                + "% "
                                            )
                                        pbar.set_description(
                                            cluster_participation
                                            + "| "
                                            + str(number_of_retrieved_objects)
                                            + " objects"
                                        )
                                        pbar.refresh()
                                        pbar.update(1)

                                if len(active_jobs[server]) < max_jobs:

                                    item = requestList.pop()
                                    (
                                        value,
                                        identifier,
                                        query,
                                        arguments,
                                        output_type,
                                    ) = item

                                    task = pool.apply_async(
                                        Neo4j.requestOnRemote,
                                        (
                                            value,
                                            identifier,
                                            query,
                                            arguments,
                                            output_type,
                                            server,
                                        ),
                                    )
                                    temp_results.append(task)
                                    active_jobs[server].append(task)

                        # Waiting for every task to finish
                        # Not in the main loop for better efficiency

                        while not all(
                            len(tasks) == 0 for tasks in active_jobs.values()
                        ):
                            time.sleep(0.01)
                            for server, max_jobs in cluster.items():
                                for task in active_jobs[server]:
                                    if (
                                        task.ready()
                                    ):  # Meaning that a task have been finished on a remote server

                                        temporary_result = task.get()

                                        if output_type == list:
                                            if len(temporary_result) > 0:
                                                for sublist in temporary_result:
                                                    number_of_retrieved_objects += len(
                                                        sublist
                                                    )
                                        elif (
                                            output_type == dict or output_type == Graph
                                        ):
                                            number_of_retrieved_objects += len(
                                                temporary_result
                                            )

                                        temporary_result = None

                                        active_jobs[server].remove(task)
                                        task = None
                                        jobs_done[server] += 1
                                        total_jobs_done = sum(jobs_done.values())
                                        cluster_participation = ""
                                        for server_running in jobs_done:
                                            server_name = server_running.split(":")[0]
                                            cluster_participation += (
                                                server_name
                                                + ": "
                                                + str(
                                                    int(
                                                        round(
                                                            100
                                                            * jobs_done[server_running]
                                                            / total_jobs_done,
                                                            0,
                                                        )
                                                    )
                                                )
                                                + "% "
                                            )
                                        pbar.set_description(
                                            cluster_participation
                                            + "| "
                                            + str(number_of_retrieved_objects)
                                            + " objects"
                                        )
                                        pbar.refresh()
                                        pbar.update(1)

                        for r in temp_results:
                            result += r.get()

                    pbar.close()

                elif (
                    "SET" in request["request"]
                    or "MERGE" in request["request"]
                    or "DELETE" in request["request"]
                ):
                    # Si c'est une requête d'écriture il faut la faire sur tous les noeuds du cluster
                    query = request["request"]
                    username = self.arguments.username
                    password = self.arguments.password
                    results = []
                    temp_results = []

                    with mp.Pool(processes=self.arguments.nb_cores) as pool:
                        for server in cluster.keys():
                            task = pool.apply_async(
                                Neo4j.writeRequestOnRemote,
                                (
                                    query,
                                    output_type,
                                    server,
                                    username,
                                    password,
                                ),
                            )
                            temp_results.append(task)

                        for task in temp_results:
                            results.append(task.get())

                    result = results[0]

                else:
                    if output_type is Graph:
                        for record in tx.run(request["request"]):
                            result.append(record["p"])
                            # print("other RESULT : ", result)
                            # Quick and dirty way of handling multiple records (e.g., RETURN p, p2
                            # TODO : possibly improve that ugly code
                            try:
                                result.append(record["p2"])
                            except:
                                pass
                        result = self.computePathObject(result)
                    else:
                        result = tx.run(request["request"])
                        if output_type is list:
                            result = result.values()
                        else:
                            result = result.data()

        self.cache.createCacheEntry(request["filename"], result)
        # self.cache.createCsvFileFromRequest(request["filename"], result, output_type)
        logger.print_time(
            timer_format(time.time() - start) + " - %d objects" % len(result)
        )

        if "postProcessing" in request:
            request["postProcessing"](self, result)

        gc.collect()
        return result


    @classmethod
    def computePathObject(cls, Paths):
        final_paths = []
        for path in Paths:
            if not path is None:

                nodes = []
                for relation in path.relationships:

                    for node in relation.nodes:
                        label = next(
                            iter(node.labels.difference({"Base"}))
                        )  # e.g. : {"User","Base"} -> "User"

                        nodes.append(Node(node.id, label, node["name"], node["domain"], relation.type))
                        break


                nodes.append(Node(path.end_node.id, next(iter(path.end_node.labels.difference({"Base"}))), path.end_node["name"], path.end_node["domain"], ""))

                final_paths.append(Path(nodes))

        return final_paths
