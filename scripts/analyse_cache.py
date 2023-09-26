import os
import pickle
import json

import sys

sys.path.append("../sources/python/")


def request_a():
    full_path_example = sys.argv[1]
    result_final = retrieveCacheEntry(full_path_example)
    return result_final


def retrieveCacheEntry(full_name):
    with open(full_name, "rb") as f:
        return pickle.load(f)


list_path = request_a()

dico_node_rel_node = {}

liste_totale = []

for path in list_path:

    for i in path.nodes:
        liste_totale += [(i.id, i.labels, i.name, i.relation_type, i.next_node)]

print(liste_totale, len(liste_totale))
