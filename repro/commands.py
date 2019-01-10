import traceback
import time
import neomodel
import neo4j
import requests as r
from loguru import logger

db = neomodel.db
neomodel.config.DATABASE_URL = "bolt+routing://test:test@neo4j-0:7687"

READ_QUERY = "MATCH (n) RETURN n"
INSERT_QUERY = "CREATE (p:Person)-[:LIKES]->(t:Technology)"
CLUSTER_QUERY_URL = f"http://neo4j-0:7474/db/data/transaction/commit"
CLUSTER_QUERY_STATEMENT = r"CALL dbms.cluster.overview()"

def parse_neo4j_status(resp):
    out = []
    for row in (datum["row"] for datum in resp["results"][0]["data"]):
        out.append((row[1][0][7:14], row[2]))
    return out

def retrieve_cluster_info():
    try:
        resp = r.post(CLUSTER_QUERY_URL, json={"statements": [{"statement": CLUSTER_QUERY_STATEMENT}]})
        return parse_neo4j_status(resp.json())
    except r.exceptions.ConnectionError:
        logger.info("The neo4j-0 instance is not available. Perhaps the cluster is still starting up or reforming after a leader election")

def print_cluster_info():
    logger.info(f"{retrieve_cluster_info()}")

def retrieve_cluster_leader():
    cluster_info = retrieve_cluster_info()
    if cluster_info:
        for server, role in cluster_info:
            if role == "LEADER":
                return server

def do_request(request):
    while True:
        try:
            return db.cypher_query(request)
        except neo4j.v1.exceptions.SessionExpired:
            logger.info("Session has expired. Trying again in 1 second")
            time.sleep(1)
            continue
        except neo4j.exceptions.ServiceUnavailable:
            logger.info("Neo4j is unavailable. Trying again in 5 seconds")
            time.sleep(5)
            continue
        except neo4j.exceptions.NotALeaderError:
            logger.info("Routing table is incorrect. Attempting to locate and connect to new leader")
            reconnect()
            continue
        except:
            raise

def reconnect():
    while True:
        cluster_leader = retrieve_cluster_leader()
        if cluster_leader:
            logger.info(f"Got new leader {cluster_leader}")
            return reconnect_to_leader(cluster_leader)
        logger.info("Could not locate leader. Trying again in 5 seconds")
        time.sleep(5)

def reconnect_to_leader(cluster_leader):

      url = "bolt+routing://test:test@" + cluster_leader + ":7687"

      while True:
          try:
              db.set_connection(url)
              logger.info(f"Connected to new leader {url}")
              break
          except neo4j.exceptions.ServiceUnavailable:
              logger.info("Waiting for routing information to become available...")
              time.sleep(5)
              continue

def write():
    logger.info("Attempting to write data")
    do_request(INSERT_QUERY)
    logger.info("Successfully wrote data")

def read():
    logger.info("Attempting to read data")
    data = do_request(READ_QUERY)
    logger.info(f"Successfully read data {data}")