# This script is meant to "pseudo-anonymize" (using bleeding-edge technique
# referred to as "match & replace") a neo4j database and focuses only on
# the node attributes that show in AD Miner reports (name, domain, SPNs,
# and descriptions)
#
# For this script to work, you need to provide 2 files :
#   - the list of words to replace (beware of upper/lower case), 1 per line
#   - the list of replacement words
#
# Both lists must be of the same size (especially if you wish to revert)


from neo4j import GraphDatabase

def replace_names(tx, word_to_replace, replacement):
    query = (
        f"MATCH (n) WHERE EXISTS(n.name) AND n.name CONTAINS '{word_to_replace}' "
        f"SET n.name = REPLACE(n.name, '{word_to_replace}', '{replacement}') RETURN count(n)"
    )
    result = tx.run(query)
    return result.single()[0]

def replace_domains(tx, word_to_replace, replacement):
    query = (
        f"MATCH (n) WHERE EXISTS(n.domain) AND n.domain CONTAINS '{word_to_replace}' "
        f"SET n.domain = REPLACE(n.domain, '{word_to_replace}', '{replacement}') RETURN count(n)"
    )
    result = tx.run(query)
    return result.single()[0]

def replace_descriptions(tx, word_to_replace, replacement):
    query = (
        f"MATCH (n) WHERE EXISTS(n.description) AND n.descriptions CONTAINS '{word_to_replace}' "
        f"SET n.description = REPLACE(n.description, '{word_to_replace}', '{replacement}') RETURN count(n)"
    )
    result = tx.run(query)
    return result.single()[0]

def replace_spn(tx, word_to_replace, replacement):
    query = (
        f"MATCH (n) WHERE EXISTS(n.serviceprincipalnames) "
        f"SET n.serviceprincipalnames =  REDUCE(acc = [], i IN RANGE(0, SIZE(COALESCE(n.serviceprincipalnames, []))-1) |    acc + [CASE WHEN n.serviceprincipalnames[i] CONTAINS '{word_to_replace}' THEN REPLACE(n.serviceprincipalnames[i],'{word_to_replace}','{replacement}') ELSE n.serviceprincipalnames[i] END]  ) RETURN count(n)"
    )
    print(query)
    result = tx.run(query)
    return result.single()[0]

def main(host, port, username, password, words_to_replace_file, replacements_file):
    with open(words_to_replace_file, 'r') as file:
        words_to_replace = file.read().splitlines()

    with open(replacements_file, 'r') as file:
        replacements = file.read().splitlines()[:len(words_to_replace)]

    # Connect to the Neo4j database
    uri = f"bolt://{host}:{port}"
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            for word, replacement in zip(words_to_replace, replacements):
                count = session.execute_write(replace_names, word, replacement)
                print(f"Replaced {count} occurrences (names) of '{word}' with '{replacement}'.")
                count = session.execute_write(replace_domains, word, replacement)
                print(f"Replaced {count} occurrences (domains) of '{word}' with '{replacement}'.")
                count = session.execute_write(replace_spn, word, replacement)
                print(f"Replaced {count} occurrences (spn) of '{word}' with '{replacement}'.")
                count = session.execute_write(replace_descriptions, word, replacement)
                print(f"Replaced {count} occurrences (spn) of '{word}' with '{replacement}'.\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 7:
        print("Usage: python script.py <host> <port> <username> <password> <words_to_replace_file> <replacements_file>")
        sys.exit(1)

    host, port, username, password, words_to_replace_file, replacements_file = sys.argv[1:7]
    main(host, int(port), username, password, words_to_replace_file, replacements_file)
