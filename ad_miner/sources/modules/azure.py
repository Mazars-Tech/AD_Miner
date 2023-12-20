import time
from hashlib import md5
from datetime import datetime

from ad_miner.sources.modules.card_class import Card
from ad_miner.sources.modules.graph_class import Graph
from ad_miner.sources.modules.grid_class import Grid
from ad_miner.sources.modules.node_neo4j import Node
from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.path_neo4j import Path
from ad_miner.sources.modules.table_class import Table

from ad_miner.sources.modules.utils import days_format, grid_data_stringify, timer_format

from ad_miner.sources.modules import generic_computing
from ad_miner.sources.modules import generic_formating
from ad_miner.sources.modules import logger
from pathlib import Path as pathlib

import json
import time

MODULES_DIRECTORY = pathlib(__file__).parent


class Azure:
    def __init__(self, arguments, neo4j, domain):
        self.arguments = arguments
        self.start = time.time()
        logger.print_debug("Computing Azure objects")
        self.neo4j = neo4j

        self.tenant_id_name = {}

        self.azure_users = neo4j.all_requests["azure_user"]["result"]
        self.azure_admin = neo4j.all_requests["azure_admin"]["result"]
        self.azure_groups = neo4j.all_requests["azure_groups"]["result"]
        self.azure_vm = neo4j.all_requests["azure_vm"]["result"]
        self.azure_users_paths_high_target = neo4j.all_requests["azure_users_paths_high_target"]["result"]
        self.azure_ms_graph_controllers = neo4j.all_requests["azure_ms_graph_controllers"]["result"]
        self.azure_aadconnect_users = neo4j.all_requests["azure_aadconnect_users"]["result"]
        self.azure_admin_on_prem = neo4j.all_requests["azure_admin_on_prem"]["result"]
        self.azure_role_listing = neo4j.all_requests["azure_role_listing"]["result"]
        self.azure_role_paths = neo4j.all_requests["azure_role_paths"]["result"]
        self.azure_reset_passwd = neo4j.all_requests["azure_reset_passwd"]["result"]
        self.azure_last_passwd_change = neo4j.all_requests["azure_last_passwd_change"]["result"]
        self.azure_dormant_accounts = neo4j.all_requests["azure_dormant_accounts"]["result"]
        self.azure_accounts_disabled_on_prem = neo4j.all_requests["azure_accounts_disabled_on_prem"]["result"]
        self.azure_accounts_not_found_on_prem = neo4j.all_requests["azure_accounts_not_found_on_prem"]["result"]
        self.azure_tenants = neo4j.all_requests["azure_tenants"]["result"]
        self.azure_ga_to_ga = neo4j.all_requests["azure_ga_to_ga"]["result"]
        self.azure_cross_ga_da = neo4j.all_requests["azure_cross_ga_da"]["result"]

        # Generate all the azure-related pages
        self.genAzureUsers()
        self.genAzureAdmin()
        self.genAzureGroups()
        self.genAzureVM()

        # Utils
        self.setTenantIDName()

        self.genAzureUsersPathsHighTarget(domain)
        self.genAzureMSGraphController(domain)
        self.genAzureAADConnectUsers()
        self.genAzureAdminsAndOnPrem()
        self.genAzureRolePaths(domain)
        self.genAzurePasswdReset()
        self.genAzureLastPasswdSet()
        self.genAzureDormantAccounts()
        self.genAzureDisabledAccountsOnPrem()
        self.genAzureNotFoundAccountsOnPrem()
        #self.genAzureGAToGA()
        self.genAzureCrossGADA(domain)


    @staticmethod
    def createGraphPage(
        render_prefix, page_name, page_title, page_description, graph_data, domain
    ):
        page = Page(render_prefix, page_name, page_title, page_description)
        graph = Graph()
        graph.setPaths(graph_data)

        graph.addGhostComputers(domain.dico_ghost_computer)
        graph.addGhostUsers(domain.dico_ghost_user)
        graph.addDCComputers(domain.dico_dc_computer)
        graph.addUserDA(domain.dico_user_da)
        graph.addGroupDA(domain.dico_da_group)

        page.addComponent(graph)
        page.render()


    def setTenantIDName(self):
        for tenant in self.azure_tenants:
            self.tenant_id_name[tenant["ID"]] = tenant["Name"]


    def genAzureUsers(self):
        if self.azure_users is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_users", "List of all Azure users", "azure_users")
        grid = Grid("Azure Users")

        data = []
        for user in self.azure_users:
            data.append({
                "Tenant ID": '<i class="bi bi-file-earmark-person"></i> ' + user["Tenant ID"],
                "Name": '<i class="bi bi-person-fill"></i> ' + user["Name"],
                "Synced on premise": '<i class="bi bi-check-square"></i>' if user["onpremisesynced"] == True else '<i class="bi bi-square"></i>',
                "On premise SID": user["SID"] if user["onpremisesynced"] == True and user["SID"] != None else '-'
            })

        grid.setheaders(["Tenant ID", "Name", "Synced on premise", "On premise SID"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()
    
    def genAzureAdmin(self):
        if self.azure_admin is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_admin", "List of all Azure users", "azure_admin")
        grid = Grid("Azure Admin")

        data = []
        for admin in self.azure_admin:
            data.append({
                "Tenant ID": '<i class="bi bi-file-earmark-person"></i> ' + admin["Tenant ID"],
                "Name": '<i class="bi bi-gem"></i> ' + admin["Name"]
            })

        grid.setheaders(["Tenant ID", "Name"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()


    def genAzureGroups(self):
        if self.azure_groups is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_groups", "List of all Azure groups", "azure_groups")
        grid = Grid("Azure Groups")

        data = []
        for group in self.azure_groups:
            data.append({
                "Tenant ID": '<i class="bi bi-file-earmark-person"></i> ' + group["Tenant ID"],
                "Name": '<i class="bi bi-people-fill"></i> ' + group["Name"],
                "Description": group["Description"]
            })

        grid.setheaders(["Tenant ID", "Name", "Description"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()


    def genAzureVM(self):
        if self.azure_vm is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_vm", "List of all Azure vm", "azure_vm")
        grid = Grid("Azure VM")

        grid.setheaders(["Tenant ID", "Name", "Operating System"])

        data = []
        for dict in self.azure_vm:
            tmp_data = {"Tenant ID": dict["Tenant ID"]}

            tmp_data["Name"] = dict["Name"]

            #os
            if dict.get("os"):
                os = dict["os"]
                if "windows" in dict["os"].lower():
                    os = '<i class="bi bi-windows"></i> ' + os
                elif "mac" in dict["os"].lower():
                    os = '<i class="bi bi-apple"></i> ' + os
                else:
                    os = '<i class="bi bi-terminal-fill"></i> ' + os
            else:
                os = "Unknown"

            tmp_data["Operating System"] = os

            data.append(tmp_data)

        grid.setData(data)
        page.addComponent(grid)
        page.render()


    def genAzureUsersPathsHighTarget(self, domain):
        if self.azure_users_paths_high_target is None:
            self.azure_users_paths_high_target = []
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "azure_users_paths_high_target",
            "Azure Users with paths to high target",
            "azure_users_paths_high_target",
            self.azure_users_paths_high_target,
            domain,
        )
    

    def genAzureMSGraphController(self, domain):
        if self.azure_ms_graph_controllers is None:
            self.azure_ms_graph_controllers = []
            return
        self.createGraphPage(
            self.arguments.cache_prefix,
            "azure_ms_graph_controllers",
            "Controllers of MS Graph",
            "azure_ms_graph_controllers",
            self.azure_ms_graph_controllers,
            domain,
        )


    def genAzureAADConnectUsers(self):
        if self.azure_aadconnect_users is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_aadconnect_users", "Azure users with AADConnect session", "azure_aadconnect_users")
        grid = Grid("Azure users with AADConnect session")

        data = []
        for user in self.azure_aadconnect_users:
            data.append({
                "Tenant ID": '<i class="bi bi-file-earmark-person"></i> ' + user["Tenant ID"],
                "Name": '<i class="bi bi-people-fill"></i> ' + user["Name"],
                "Session": user["Session"] if user["Session"] != None else "-"
            })

        grid.setheaders(["Tenant ID", "Name", "Session"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()
    

    def genAzureAdminsAndOnPrem(self):
        if self.azure_admin_on_prem is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_admin_on_prem", "Azure & On premise Admins", "azure_admin_on_prem")
        grid = Grid("Azure & On premise Admins")

        data = []
        for user in self.azure_admin_on_prem:
            data.append({
                "Name": '<i class="bi bi-gem"></i> ' + user["Name"]
            })

        grid.setheaders(["Name"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()


    def genAzureRolePaths(self, domain):
        if self.azure_role_listing is None:
            return 

        # Add all paths tot the corresponding role
        paths = {}
        for path in self.azure_role_paths:
            try:
                paths[path.nodes[-1].name].append(path)
            except KeyError:
                paths[path.nodes[-1].name] = [path]

        page = Page(self.arguments.cache_prefix, "azure_roles", "Azure roles", "azure_roles")
        grid = Grid("Azure roles")
        
        data = []
        self.azure_roles_entry_nodes = []
        for role in self.azure_role_listing:
            if paths.get(role["Name"]):
                # Generate graph page for roles with paths
                hash = md5(role['Name'].encode()).hexdigest()
                self.createGraphPage(
                    self.arguments.cache_prefix,
                    f"azure_roles_paths_{hash}",
                    "Paths to Azure roles",
                    "azure_roles",
                    paths[role["Name"]],
                    domain,
                )
                # Count the number of nodes that have acces to the role
                unique_nodes = set([path.nodes[0].name for path in paths[role['Name']]])
                count = len(unique_nodes)
                self.azure_roles_entry_nodes += unique_nodes
                sortClass = str(count).zfill(6)
                data.append({
                    "Name": '<i class="bi bi-person-bounding-box"></i> ' + role["Name"],
                    "Description": role["Description"],
                    "Access to role": grid_data_stringify({
                        "link": f"azure_roles_paths_{hash}.html",
                        "value": f"{count} account{'s' if count > 1 else ''}",
                        "before_link": f"<i class='bi bi-shuffle {sortClass}' aria-hidden='true'></i>"
                    })
                })
        self.azure_roles_entry_nodes = set(self.azure_roles_entry_nodes)
        grid.setheaders(["Name", "Description", "Access to role"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()


    def genAzurePasswdReset(self):
        if self.azure_reset_passwd is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_reset_passwd", "Azure users with passwords reset privilege", "azure_reset_passwd")
        grid = Grid("Azure users with passwords reset privilege")

        self.reset_passwd = {}
        for path in self.azure_reset_passwd:
            try:
                self.reset_passwd[path.nodes[0].name].append(path.nodes[-1].name)
            except KeyError:
                self.reset_passwd[path.nodes[0].name] = [path.nodes[-1].name]

        data = []
        for user in self.reset_passwd.keys():
            count = len(self.reset_passwd[user])
            hash = md5(user.encode()).hexdigest()
            sortClass = str(count).zfill(6)

            subpage = Page(self.arguments.cache_prefix, f"passwords_reset_{hash}", f"Users which passwords can be reset by {user}", "azure_reset_passwd")
            subgrid = Grid(f"Users which passwords can be reset by {user}")
            subgrid.setheaders([user])
            subgrid.setData([{user: target} for target in self.reset_passwd[user]])
            subpage.addComponent(subgrid)
            subpage.render()

            data.append({
                "Privileged user": '<i class="bi bi-person-fill"></i> ' + user,
                "Passwords that can be reset": grid_data_stringify({
                        "link": f"passwords_reset_{hash}.html",
                        "value": f"{count} password{'s' if count > 1 else ''}",
                        "before_link": f"<i class='bi bi-key-fill {sortClass}' aria-hidden='true'></i>"
                    })
            })

        grid.setheaders(["Privileged user", "Passwords that can be reset"])
        grid.setData(data)
        page.addComponent(grid)
        page.render()


    def genAzureLastPasswdSet(self):
        if self.azure_last_passwd_change is None:
            self.azure_last_passwd_change_strange = []
            return 

        page = Page(self.arguments.cache_prefix, "azure_last_passwd_change", "Incoherent last password change both on Azure and on premise", "azure_last_passwd_change")
        grid = Grid("Incoherent last password change both on Azure and on premise")

        data = []
        self.azure_last_passwd_change_strange = []
        for user in self.azure_last_passwd_change:
            onprem = user["Last password set on premise"]
            onazure = user["Last password set on Azure"]
            diff = int(abs(onprem - onazure))
            if diff > 1:
                self.azure_last_passwd_change_strange.append(user)
                data.append({
                    "Name": '<i class="bi bi-person-fill"></i> ' + user["Name"],
                    "Last password set on premise": days_format(onprem),
                    "Last password set on Azure": days_format(onazure),
                    "Difference": days_format(diff)
                })

        grid.setheaders(["Name", "Last password set on premise", "Last password set on Azure", "Difference"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()
    

    def genAzureDormantAccounts(self):
        if self.azure_dormant_accounts is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_dormant_accounts", "Users that did not log in for 3 months", "azure_dormant_accounts")
        grid = Grid("Users that did not log in for 3 months")

        data = []
        self.azure_dormant_accounts_90_days = []
        for user in self.azure_dormant_accounts:
            if user["lastlogon"] > 90:
                self.azure_dormant_accounts_90_days.append(user)
                data.append({
                    "Name": '<i class="bi bi-person-fill"></i> ' + user["Name"],
                    "Last logon": days_format(user["lastlogon"]),
                    "Creation date": days_format(user["whencreated"])
                })

        grid.setheaders(["Name", "Last logon", "Creation date"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()
    

    def genAzureDisabledAccountsOnPrem(self):
        if self.azure_accounts_disabled_on_prem is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_accounts_disabled_on_prem", "Synced Azure accounts with different enabled status", "azure_accounts_disabled_on_prem")
        grid = Grid("Synced Azure accounts with different enabled status")

        data = []
        for user in self.azure_accounts_disabled_on_prem:
            data.append({
                "Azure name": '<i class="bi bi-person-fill"></i> ' + user["Azure name"],
                "Enabled on Azure": '<i class="bi bi-check-square"></i>' if user["Enabled on Azure"] is True else '<i class="bi bi-square"></i>',
                "On premise name": '<i class="bi bi-person"></i> ' + user["On premise name"],
                "Enabled on premise": '<i class="bi bi-check-square"></i>' if user["Enabled on premise"] is True else '<i class="bi bi-square"></i>'
            })

        grid.setheaders(["Azure name", "Enabled on Azure", "On premise name", "Enabled on premise"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()
    

    def genAzureNotFoundAccountsOnPrem(self):
        if self.azure_accounts_not_found_on_prem is None:
            return 

        page = Page(self.arguments.cache_prefix, "azure_accounts_not_found_on_prem", "Azure accounts that are synced to non-existing on premise account", "azure_accounts_not_found_on_prem")
        grid = Grid("Azure accounts that are synced to non-existing on premise account")

        data = []
        for user in self.azure_accounts_not_found_on_prem:
            data.append({
                "Name": '<i class="bi bi-person-fill"></i> ' + user["Name"],
                "Synced to on premise": '<i class="bi bi-check-square"></i>',
                "Synced account": '<i class="bi bi-question-lg"></i>'
            })

        grid.setheaders(["Name", "Synced to on premise", "Synced account"])

        grid.setData(data)
        page.addComponent(grid)
        page.render()

    """
    # TODO CANNOT BE TESTED NOW
    def genAzureGAToGA(self):
        
    """

    def genAzureCrossGADA(self, domains):
        self.azure_total_cross_ga_da_compromission = 0
        if self.azure_cross_ga_da is None:
            return 
        # Create the page
        page = Page(
            self.arguments.cache_prefix,
            "azure_cross_ga_da",
            "Paths between Azure admins and on premise admins",
            "azure_cross_ga_da",
        )
        # Create the grid
        grid = Grid("Paths between Azure admins and on premise admins")
        # Add the headers
        headers = ["Domain / Tenant"]
        for tenant_id in self.tenant_id_name.keys():
            headers.append(self.tenant_id_name[tenant_id])
        
        paths_sorted_per_domain = {}
        for domain in domains.collected_domains:
            domain = domain[0]
            paths_sorted_per_domain[domain] = {}
            # We re-do the loop for easier code reading
            for tenant_id in self.tenant_id_name.keys():
                paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]] = {"GA_to_DA": [],
                                                              "DA_to_GA": []}

        for path in self.azure_cross_ga_da:
            # Case where starting point is Azure
            if path.nodes[0].tenant_id != None:
                domain = path.nodes[-1].domain
                tenant_id = path.nodes[0].tenant_id
                paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]]["GA_to_DA"].append(path)
            # Case where starting point is on premise
            else:
                domain = path.nodes[0].domain
                tenant_id = path.nodes[-1].tenant_id
                paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]]["DA_to_GA"].append(path)
        
        data = []
        for domain in paths_sorted_per_domain.keys():
            row1 = {"Domain / Tenant": domain}
            row2 = {"Domain / Tenant": domain}
            for tenant_id in self.tenant_id_name.keys():
                count1 = len(paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]]["GA_to_DA"])
                count2 = len(paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]]["DA_to_GA"])
                sortClass1 = str(count1).zfill(6)
                sortClass2 = str(count2).zfill(6)
                hash1 = md5((tenant_id + domain).encode()).hexdigest()
                hash2 = md5((domain + tenant_id).encode()).hexdigest()
                if count1 > 0:
                    row1[self.tenant_id_name[tenant_id]] = grid_data_stringify({
                            "link": f"azure_cross_ga_da_{hash1}.html",
                            "value": f"{count1} Azure ⇨ On-prem path{'s' if count1 > 1 else ''}",
                            "before_link": f"<i class='bi bi-shuffle {sortClass1}' aria-hidden='true'></i>"
                        })
                    self.createGraphPage(
                        self.arguments.cache_prefix,
                        f"azure_cross_ga_da_{hash1}",
                        f"Paths from {self.tenant_id_name[tenant_id]} to {domain}",
                        "azure_cross_ga_da",
                        paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]]["GA_to_DA"],
                        domains,
                    )
                    self.azure_total_cross_ga_da_compromission += 1
                else:
                    row1[self.tenant_id_name[tenant_id]] = "-"
                if count2 > 0:
                    row2[self.tenant_id_name[tenant_id]] = grid_data_stringify({
                            "link": f"azure_cross_ga_da_{hash2}.html",
                            "value": f"{count2} On-prem ⇨ Azure path{'s' if count2 > 1 else ''}",
                            "before_link": f"<i class='bi bi-shuffle {sortClass2}' aria-hidden='true'></i>"
                        })
                    self.createGraphPage(
                        self.arguments.cache_prefix,
                        f"azure_cross_ga_da_{hash2}",
                        f"Paths from {domain} to {self.tenant_id_name[tenant_id]}",
                        "azure_cross_ga_da",
                        paths_sorted_per_domain[domain][self.tenant_id_name[tenant_id]]["DA_to_GA"],
                        domains,
                    )
                    self.azure_total_cross_ga_da_compromission += 1
                else:
                    row2[self.tenant_id_name[tenant_id]] = "-"
            data.append(row1)
            data.append(row2)
        
        grid.setheaders(headers)
        grid.setData(data)
        page.addComponent(grid)
        page.render()


