#!/usr/bin/env python3

# Built-in imports
import datetime
import json
import shutil
from pathlib import Path
import time
import traceback
import os

# Local library imports
from ad_miner.sources.modules import logger, main_page, render_order, utils
from ad_miner.sources.modules.computers import Computers
from ad_miner.sources.modules.domains import Domains
from ad_miner.sources.modules.neo4j_class import Neo4j, pre_request_date
from ad_miner.sources.modules.objects import Objects
from ad_miner.sources.modules.rating import rating
from ad_miner.sources.modules.users import Users

# Third party library imports


# Constants
SOURCES_DIRECTORY = Path(__file__).parent / 'sources'


# Do all the requests (if cached, retrieve from cache, else store in cache)
def populate_data_and_cache(neo4j: Neo4j) -> None:
    """Populate data and cache it based on configuration settings.

    This function reads a configuration file (config.json) and determines
    whether to execute specific requests or skip them based on the configuration.

    Args:
        neo4j (Neo4j): An instance of the Neo4j class.

    Returns:
        None: This function does not return any values.

    Raises:
        FileNotFoundError: If the config.json file is not found.
        json.JSONDecodeError: If there is an issue parsing the JSON in config.json.
    """


    config_file_path = SOURCES_DIRECTORY / 'modules' / 'config.json'

    try:
        with config_file_path.open('r', encoding='utf-8') as config_file:
            config_data = json.load(config_file)['requests']
    except (FileNotFoundError, json.JSONDecodeError) as error:
        logger.print_error(f"Error while parsing {config_file_path}: {error}")
        return

    nb_requests = len(neo4j.all_requests.keys())
    requests_count = 0

    for key in neo4j.all_requests.keys():
        requests_count = requests_count + 1
        print(f"[{requests_count}/{nb_requests}] ", end="")
        req = neo4j.all_requests[key]
        if not config_data.get(key) or config_data[key] == "true":
            try:
                req["result"] = None
                req["method"](req)
            except Exception as error:
                logger.print_error(error)
                logger.print_error(traceback.format_exc())
                pass
        else:
            req["result"] = None
            logger.print_time("Skipping request : %s    (config.json)" % key)

    logger.print_success("Requests finished !")


def prepare_render(arguments) -> None:
    """Prepares the render folder by copying necessary assets.

    Args:
        arguments: Parsed command line arguments.
    """

    folder_name = Path(f"render_{arguments.cache_prefix}")

    if folder_name.exists():
        shutil.rmtree(folder_name)

    folder_name.mkdir(parents=True, exist_ok=True)
    (folder_name / "csv").mkdir()
    (folder_name / "html").mkdir()

    # Create redirect index.html
    (folder_name / "index.html").write_text("<script>window.location.href = './html/index.html'</script>")

    # Copy assets
    subpaths = {
        "css": SOURCES_DIRECTORY / "html" / "bootstrap" / "css",
        "js": SOURCES_DIRECTORY / "html" / "bootstrap" / "js",
        "icons": SOURCES_DIRECTORY / "html" / "bootstrap" / "icons",
        "assets": SOURCES_DIRECTORY / "html" / "assets"
    }

    for sub, src_path in subpaths.items():
        shutil.copytree(src_path, folder_name / sub)


    for js_file in (SOURCES_DIRECTORY / "js").iterdir():
        shutil.copy2(js_file, folder_name / "js")




def main() -> None:
    """Main execution function for the script."""
    start = time.time()
    arguments = utils.args()

    if arguments.cluster:
        main_server = arguments.bolt.replace("bolt://", "")
        if main_server not in arguments.cluster:
            error_message = (f"The main server (-b {arguments.bolt}) should be "
                             f"part of the cluster you specified (--cluster {arguments.cluster}).")
            logger.print_error(error_message)
            return

    prepare_render(arguments)

    try:
        extract_date_timestamp = pre_request_date(arguments)
        extract_date = datetime.datetime.fromtimestamp(extract_date_timestamp).strftime("%Y%m%d")
    except Exception as e:  # Ideally, replace `Exception` with the specific exception you're catching.
        logger.print_error(f"Error with pre_request_date: {e}")
        extract_date_timestamp = datetime.date.today()
        extract_date = extract_date_timestamp.strftime("%Y%m%d")

    if arguments.extract_date:
        extract_date = arguments.extract_date

    neo4j = Neo4j(arguments, extract_date)

    if arguments.cluster:
        neo4j.verify_integrity(neo4j, neo4j.cluster)

    populate_data_and_cache(neo4j)

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

    if os.path.exists(Path().cwd() / 'temporary.txt'):
        (Path().cwd() / 'temporary.txt').unlink()

    logger.print_success(f"Program finished in {utils.timer_format(time.time() - start)}!")

if __name__ == "__main__":
    main()