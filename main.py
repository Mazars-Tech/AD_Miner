#!/usr/bin/env python3
import sys
sys.path.insert(0, 'sources/python/')
import os
import shutil

import traceback
import time
import json
import datetime

import utils
from ast import arguments
from neo4j_class import Neo4j, pre_request_date
from computers import Computers
from domains import Domains
from users import Users
from objects import Objects
import render_order
import main_page
import logger
import subprocess

from rating import rating


# Do all the requests (if cached, retrieve from cache, else store in cache)
def populateDataAndCache(neo4j):
    with open("sources/python/config.json", "r") as config:
        try:
            conf = json.load(config)["requests"]
        except:
            logger.print_error("Error while parsing config.json")
            exit(0)
        nb_requests = len(neo4j.all_requests.keys())
        requests_count = 0
        for key in neo4j.all_requests.keys():
            requests_count = requests_count + 1
            print("[" + str(requests_count) + "/" + str(nb_requests) + "] ", end="")
            req = neo4j.all_requests[key]
            if not conf.get(key) or conf[key] == "true":
                try:
                    req["result"] = None
                    req["method"](req)
                except Exception as e:
                    logger.print_error(e)
                    logger.print_error(traceback.format_exc())
                    pass
            else:
                req["result"] = None
                logger.print_time("Skipping request : %s    (config.json)" % key)
        logger.print_success("Requests finished !")


# - Create render folder
# - Copy JS, CSS and icons to render folder
def prepareRender(arguments):
    folder_name = "render_" + arguments.cache_prefix
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    os.mkdir(folder_name)
    os.mkdir("%s/csv" % folder_name)
    os.mkdir("%s/html" % folder_name)
    with open(f"{folder_name}/index.html", "w") as file:
        file.write("<script>window.location.href = './html/index.html'</script>")
    shutil.copytree(os.getcwd() + "/sources/html/bootstrap/css", folder_name + "/css")
    shutil.copytree(os.getcwd() + "/sources/html/bootstrap/js", folder_name + "/js")
    shutil.copytree(os.getcwd() + "/sources/html/bootstrap/icons", folder_name + "/icons")
    shutil.copytree(os.getcwd() + "/sources/html/assets", folder_name + "/assets")

    files = os.listdir(os.getcwd() + "/sources/js")

    for fname in files:
        shutil.copy2(
            os.path.join(os.getcwd() + "/sources/js", fname), folder_name + "/js"
        )


if __name__ == "__main__":

    start = time.time()
    arguments = utils.args()
    # If a cluster is specified:
    # check that the main neo4j server is in the cluster list
    if len(arguments.cluster) > 0:
        mainServer = arguments.bolt.replace("bolt://","")
        if not mainServer in arguments.cluster:
            errorMessage = "The main server (-b " + arguments.bolt + ") should be part of the cluster you specified (--cluster " + arguments.cluster + ")."
            logger.print_error(errorMessage)
            sys.exit(-1)

    # Create render folder
    prepareRender(arguments)

    # Do the requests
    try:
        extract_date_timestamp = pre_request_date(arguments)
        extract_date = datetime.datetime.fromtimestamp(extract_date_timestamp).strftime(
            "%Y%m%d"
        )
    except:  # TODO : cache for the datetime request
        extract_date_timestamp = datetime.date.today()
        extract_date = extract_date_timestamp.strftime("%Y%m%d")

    if arguments.extract_date != None:
        extract_date = arguments.extract_date

    neo4j = Neo4j(arguments, extract_date)

    # If a cluster is specified:
    # check that every node uses the same database
    if len(arguments.cluster) > 0:
        neo4j.verify_integrity(neo4j, neo4j.cluster)

    populateDataAndCache(neo4j)

    # Generate all secondary pages

    # Each of the objects (domains, computers, users, objects) pulls the data of the corresponding requests from the neo4j object
    # example : computers.list_total_computers contains the list of computers, pulled from neo4j
    # The data will be used when :
    # - Generating the main page (render_order.main_render(...))
    # - Generating the secondary pages (created when the objects are initialized)
    domains = Domains(arguments, neo4j)
    computers = Computers(arguments, neo4j, domains)
    users = Users(arguments, neo4j, domains)
    objects = Objects(arguments, neo4j)

    # Generate the main page
    logger.print_success("Temporary vulnerabilities rating :")
    rating_dic = rating(users, domains, computers, objects, arguments)
    for i in rating_dic.keys():
        print(f" {i} : {rating_dic[i]}")

    for i in rating_dic.keys():
        if len(rating_dic[i]) > 0:
            global_grade = i
            break
    logger.print_success(f"Global grade : {global_grade}")
    dico_name_description = main_page.render(
        arguments, neo4j, domains, computers, users, objects, rating_dic, extract_date
    )
    render_order.main_render(
        arguments,
        neo4j,
        domains,
        computers,
        users,
        objects,
        rating_dic,
        dico_name_description,
        extract_date,
    )

    neo4j.close()

    logger.print_success("Program finished !")
    logger.print_time(utils.timer_format(time.time() - start))
