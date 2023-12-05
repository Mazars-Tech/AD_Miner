from xml.dom import UserDataHandler
from urllib.parse import quote

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

        self.azure_users = neo4j.all_requests["azure_user"]["result"]
        self.azure_admin = neo4j.all_requests["azure_admin"]["result"]
        self.azure_groups = neo4j.all_requests["azure_groups"]["result"]
        self.azure_vm = neo4j.all_requests["azure_vm"]["result"]
        self.azure_users_paths_high_target = neo4j.all_requests["azure_users_paths_high_target"]["result"]
        self.azure_ms_graph_controllers = neo4j.all_requests["azure_ms_graph_controllers"]["result"]
        self.azure_aadconnect_users = neo4j.all_requests["azure_aadconnect_users"]["result"]

        # Generate all the azure-related pages
        self.genAzureUsers()
        self.genAzureAdmin()
        self.genAzureGroups()
        self.genAzureVM()

        self.genAzureUsersPathsHighTarget(domain)
        self.genAzureMSGraphController(domain)
        self.genAzureAADConnectUsers()


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


