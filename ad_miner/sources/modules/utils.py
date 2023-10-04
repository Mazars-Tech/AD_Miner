import argparse
from pathlib import Path
import multiprocessing as mp
import json
import re

from datetime import date

today = date.today()
current_date = today.strftime("%Y%m%d")

# Constants
MODULES_DIRECTORY = Path(__file__).parent


DESCRIPTION_MAP = json.loads((MODULES_DIRECTORY / "description.json").read_text(encoding='utf-8'))
CONFIG_MAP = json.loads((MODULES_DIRECTORY / "config.json").read_text(encoding='utf-8'))
HTML_DIRECTORY = Path(__file__).parent.parent / 'html'
JS_DIRECTORY = Path(__file__).parent.parent / 'js'

TEMPLATES_DIRECTORY = HTML_DIRECTORY / 'templates'


def args():
    parser = argparse.ArgumentParser(
        prog="AD-miner",
        description="Active Directory audit tool that leverages cypher queries to crunch data from the Bloodhound graph database to uncover security weaknesses."
    )
    parser.add_argument(
        "-b",
        "--bolt",
        type=str,
        default="bolt://127.0.0.1:7687",
        help="Neo4j bolt connection (default: bolt://127.0.0.1:7687)",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        default="neo4j",
        help="Neo4j username (default : neo4j)",
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        default="neo5j",
        help="Neo4j password (default : neo5j)",
    )
    parser.add_argument(
        "-e",
        "--extract_date",
        default=None,
        help="Extract date (e.g., 20220131). Default: last logon date",
    )
    parser.add_argument(
        "-r",
        "--renewal_password",
        default=90,
        help="Password renewal policy in days. Default: 90",
    )
    parser.add_argument(
        "-a", "--azure", default=False, help="Use Azure relations", action="store_true"
    )
    parser.add_argument(
        "-c",
        "--cache",
        default=False,
        help="Use local file for neo4j data",
        action="store_true",
    )
    parser.add_argument(
        "-l", "--level", type=str, default="14", help="Recursive level for path queries"
    )
    parser.add_argument(
        "-cf",
        "--cache_prefix",
        type=str,
        default="",
        help="Cache file to use (in case of multiple company cache files)",
        required=True,
    )
    parser.add_argument(
        "--gpo_low",
        default=False,
        help="Perform a faster but incomplete query for GPO (faster than the regular query)",
        action="store_true",
    )
    parser.add_argument(
        "-ch",
        "--nb_chunks",
        type=int,
        default=mp.cpu_count(),
        help="Number of chunks for parallel neo4j requests. Default : number of CPU",
    )
    parser.add_argument(
        "-co",
        "--nb_cores",
        type=int,
        default=mp.cpu_count(),
        help="Number of cores for parallel neo4j requests. Default : number of CPU",
    )
    parser.add_argument(
        "--rdp",
        default=False,
        help="Include the CanRDP edge in graphs",
        action="store_true",
    )

    parser.add_argument(
        "--evolution",
        type=str,
        default="",
        help="Evolution over time : location of json data files. ex : '../../tests/'",
    )
    parser.add_argument(
        "--cluster",
        type=str,
        default="",
        help="Nodes of the cluster to run parallel neo4j queries. ex : host1:port1:nCore1,host2:port2:nCore2,...",
    )
    return parser.parse_args()


def timer_format(delta_time):
    if delta_time < 60:
        suffix = "s"
        delta = delta_time
    elif delta_time >= 60 and delta_time < 3600:
        suffix = "m"
        delta = delta_time / 60
    else:
        suffix = "h"
        delta = (delta_time / 60) / 60
    return "Done in %.2f %s" % (delta, suffix)


def days_format(nb_days: int) -> str:
    """
    Returns the date in a nice format
    """
    sortClass = str(nb_days).zfill(6)
    if nb_days is None or nb_days > 19000:
        return f"<i class='{sortClass} bi bi-x-circle' style='color: rgb(255, 89, 94);'></i> Never"
    y = nb_days // 365
    m = (nb_days % 365) // 30
    d = (nb_days % 365) % 30
    if y > 0:
        return f"<i class='{sortClass} bi bi-calendar3'></i> {y} year{'s' if y > 1 else ''}, {m} month{'s' if m > 1 else ''} and {d} day{'s' if d > 1 else ''}"
    elif m > 0:
        return f"<i class='{sortClass} bi bi-calendar3'></i> {m} month{'s' if m > 1 else ''} and {d} day{'s' if d > 1 else ''}"
    else:
        return f"<i class='{sortClass} bi bi-calendar3'></i> {d} day{'s' if d > 1 else ''}"


def grid_data_stringify(raw_data: dict) -> str:
    """
    Transform a dict to a string for the grid formating. This is a dumb fix for the sorting with hyperlink.
    dict format :
    {
        "link",
        "value",
        "before_link"
    }
    """
    try:
        return f"{raw_data['before_link']} <a style='color: blue' target='_blank' href='{raw_data['link']}'>{raw_data['value']} </a>"
    except KeyError:
        return f"<a style='color: blue' target='_blank' href='{raw_data['link']}'>{raw_data['value']} </a>"


def clean_special_characters_link(value_string) -> str:
    return  re.sub(r'[?&#!%:/"\'\\|]', '_', str(value_string))