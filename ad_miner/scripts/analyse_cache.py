import pickle
import sys
from pathlib import Path

# Constants
MODULES_DIRECTORY = Path(__file__).parent / 'sources/modules'


def request_a():
    module_name = sys.argv[1]
    return retrieveCacheEntry(full_module_path=MODULES_DIRECTORY / module_name)


def retrieveCacheEntry(full_module_path: Path):
    with open(full_module_path, "rb") as f:
        return pickle.load(f)


list_path = request_a()

dico_node_rel_node = {}

liste_totale = []

for path in list_path:

    for i in path.nodes:
        liste_totale += [(i.id, i.labels, i.name, i.relation_type, i.next_node)]

print(liste_totale, len(liste_totale))
