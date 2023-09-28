# ADMiner #

ADMiner is a an Active Directory a tool that leverages cypher queries to crunch data from the [BloodHound](https://github.com/BloodHoundAD/BloodHound) graph database (neo4j) and gives you a global overview of existing weaknesses through a web-based static report, including detailed listing, dynamic graphs, key indicators history, along with risk ratings.

![Main page](doc/img/main.gif)

You can also observe indicators over time to help measuring mitigation efficiency.
![Main page](doc/img/evolution.png)

ADMiner was created and is maintained by the Mazars Cybersecurity Audit & Advisory team.

## Installation and setup ##

Prerequisites: Python3

    pip install -r requirements.txt

## Usage ##

Run the tool:

    ./main.py [-h] [-b BOLT] [-u USERNAME] [-p PASSWORD] [-e EXTRACT_DATE] [-r RENEWAL_PASSWORD] [-a] [-c] [-l LEVEL] -cf CACHE_PREFIX [-ch NB_CHUNKS] [-co NB_CORES] [--rdp] [--evolution EVOLUTION] [--cluster CLUSTER]

Example:

    ./main.py -c -cf My_Report -u neo4j -p mypassword

To better handle large data sets, it is possible to enable multi-threading and also to use a cluster of neo4j databases, as shown in the following example (where server1 handles 32 threads and server2 handles 16) :

    ./main.py -c -cf My_Report -b bolt://server1:7687 -u neo4j -p mypassword  --cluster server1:7687:32,server2:7687:16

Options:

    -h, --help              Show this help message and exit
    -b, --bolt              Neo4j bolt connection (default: bolt://127.0.0.1:7687)
    -u, --username          Neo4j username (default : neo4j)
    -p, --password          Neo4j password (default : neo5j)
    -e, --extract_date      Extract date (e.g., 20220131). Default: last logon date
    -r, --renewal_password  Password renewal policy in days. Default: 90
    -a, --azure             Use Azure relations
    -c, --cache             Use local file for neo4j data
    -l, --level             Recursive level for path queries
    -cf, --cache_prefix     Cache file to use (in case of multiple company cache files)
    --gpo_deep              Perform a deep query for GPO (may take some time)
    -ch, --nb_chunks        Number of chunks for parallel neo4j requests. Default : number of CPU
    -co, --nb_cores         Number of cores for parallel neo4j requests. Default : number of CPU
    --rdp                   Include the CanRDP edge in graphs
    --evolution             Evolution over time : location of json data files. ex : '../../tests/'
    --cluster               Nodes of the cluster to run parallel neo4j queries. ex : host1:port1:nCore1,host2:port2:nCore2,...

## Contributing ##

Check out how to contribute [here](CONTRIBUTING.md).