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
    resp = r.post(CLUSTER_QUERY_URL, json={"statements": [{"statement": CLUSTER_QUERY_STATEMENT}]})
    return parse_neo4j_status(resp.json())


def print_cluster_info():
    logger.info(f"{retrieve_cluster_info()}")


def retrieve_cluster_leader():
    for server, role in retrieve_cluster_info():
        if role == "LEADER":
            return server


def read_data():
    return db.cypher_query(READ_QUERY)


@db.write_transaction
def write_data():
    return db.cypher_query(INSERT_QUERY)


def do_first():
    logger.info(f"Reading data: {read_data()}")
    logger.info(f"Writing data")
    write_data()
    logger.info("Successfully wrote data")
    logger.info(f"Reading data: {read_data()}")
    logger.info(f"Please restart the leader using this command: docker-compose restart {retrieve_cluster_leader()}")


def do_second():
    while True:
        try:
            data = read_data()
            logger.info(f"Reading data: {data}")
            break
        except neo4j.v1.exceptions.SessionExpired:
            logger.info(f"Hit SessionExpired...retrying")
            time.sleep(1)
            continue

    try:
        logger.info(f"Attempting to write data")
        write_data()
        logger.info("Successfully wrote data")
    except neo4j.exceptions.NotALeaderError as e:
        logger.error(traceback.format_exc())


