### Introduction

This repo is to demonstrate a clustering failure that occurs when using Neomodel with Neo4J's causal cluster and its `bolt+routing` protocol.

The problem occurs after neomodel has connected to the cluster for the first time, then the cluster switches leader, and then neomodel tries to write again. The leader is not re-queried from the routing information.

### Prerequisites:

 - [Docker](https://www.docker.com/products/docker-desktop)
 - [Docker Compose](https://docs.docker.com/compose/install/)

### How to reproduce

 1. Clone this repo to a local folder
 2. Open 3 terminals in the local folder
 3. In terminal 1, run `docker-compose up` and wait for the cluster to establish
 4. In terminal 2:
   * run `docker ps`, noting the container ID of the `neo4j-cluster-failure_repro` image - e.g. 12345
   * run `docker exec -it 12345 bash`, replacing 12345 with your container ID from the previous step
   * run `python`
   * run `from commands import *`
   * run `do_first()`, noting the command it tells you to run. (e.g. `docker-compose restart neo4j-0`)
 5. In terminal 3, run the restart command from the previous step
 6. In terminal 2, run `do_second()` and note the output


Sample output from terminal 2:
```
DRA-W10-MAC027:neo4j-cluster-failure rgrant$ docker ps

CONTAINER ID        IMAGE                            COMMAND                  CREATED              STATUS              PORTS                     NAMES
ed16e171ac25        neo4j-cluster-failure_repro      "python3 miniserv.py"    54 seconds ago       Up 53 seconds                                 neo4j-cluster-failure_repro_1
ae27951fda8b        neo4j:3.5-enterprise             "/sbin/tini -g -- /d…"   33 minutes ago       Up About a minute   7473-7474/tcp, 7687/tcp   neo4j-cluster-failure_neo4j-1_1
64be8050f6a5        neo4j:3.5-enterprise             "/sbin/tini -g -- /d…"   33 minutes ago       Up About a minute   7473-7474/tcp, 7687/tcp   neo4j-cluster-failure_neo4j-0_1
1140941b0e59        neo4j:3.5-enterprise             "/sbin/tini -g -- /d…"   33 minutes ago       Up About a minute   7473-7474/tcp, 7687/tcp   neo4j-cluster-failure_neo4j-2_1

DRA-W10-MAC027:neo4j-cluster-failure bob$ docker exec -it ed16e171ac25 bash

root@ed16e171ac25:/# python
Python 3.7.0 (default, Oct 16 2018, 07:10:55) 
[GCC 6.3.0 20170516] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from commands import *
>>> do_first()
2019-01-04 21:54:45.706 | INFO     | commands:do_first:48 - Reading data: ([], ('n',))
2019-01-04 21:54:45.709 | INFO     | commands:do_first:49 - Writing data
2019-01-04 21:54:46.361 | INFO     | commands:do_first:51 - Successfully wrote data
2019-01-04 21:54:46.367 | INFO     | commands:do_first:52 - Reading data: ([[<Node id=0 labels={'Person'} properties={}>], [<Node id=1 labels={'Technology'} properties={}>]], ('n',))
2019-01-04 21:54:46.730 | INFO     | commands:do_first:53 - Please restart the leader using this command: docker-compose restart neo4j-0
>>> do_second()
2019-01-04 21:56:01.171 | INFO     | commands:do_second:63 - Hit SessionExpired...retrying
2019-01-04 21:56:02.592 | INFO     | commands:do_second:60 - Reading data: ([[<Node id=0 labels={'Person'} properties={}>], [<Node id=1 labels={'Technology'} properties={}>]], ('n',))
2019-01-04 21:56:02.592 | INFO     | commands:do_second:68 - Attempting to write data
2019-01-04 21:56:03.029 | ERROR    | commands:do_second:72 - Traceback (most recent call last):
  File "/commands.py", line 69, in do_second
    write_data()
  File "/usr/local/lib/python3.7/site-packages/neomodel/util.py", line 159, in wrapper
    return func(*args, **kwargs)
  File "/commands.py", line 44, in write_data
    return db.cypher_query(INSERT_QUERY)
  File "/usr/local/lib/python3.7/site-packages/neomodel/util.py", line 32, in wrapper
    return func(self, *args, **kwargs)
  File "/usr/local/lib/python3.7/site-packages/neomodel/util.py", line 119, in cypher_query
    raise exc_info[1].with_traceback(exc_info[2])
  File "/usr/local/lib/python3.7/site-packages/neomodel/util.py", line 108, in cypher_query
    results, meta = [list(r.values()) for r in response], response.keys()
  File "/usr/local/lib/python3.7/site-packages/neomodel/util.py", line 108, in <listcomp>
    results, meta = [list(r.values()) for r in response], response.keys()
  File "/usr/local/lib/python3.7/site-packages/neo4j/v1/api.py", line 736, in records
    self._session.fetch()
  File "/usr/local/lib/python3.7/site-packages/neo4j/v1/api.py", line 347, in fetch
    detail_count, _ = self._connection.fetch()
  File "/usr/local/lib/python3.7/site-packages/neo4j/bolt/connection.py", line 290, in fetch
    raise error
  File "/usr/local/lib/python3.7/site-packages/neo4j/bolt/connection.py", line 287, in fetch
    return self._fetch()
  File "/usr/local/lib/python3.7/site-packages/neo4j/bolt/connection.py", line 327, in _fetch
    response.on_failure(summary_metadata or {})
  File "/usr/local/lib/python3.7/site-packages/neo4j/v1/result.py", line 70, in on_failure
    raise CypherError.hydrate(**metadata)
neo4j.exceptions.NotALeaderError: No write operations are allowed directly on this database. Writes must pass through the leader. The role of this server is: FOLLOWER

>>>
```