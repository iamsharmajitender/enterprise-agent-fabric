# Stack

Start and stop the local fabric. Does **not** seed catalogue data.

| Script | Command |
| --- | --- |
| Start (build + up + health wait) | `./agent-fabric-scripts/stack/start-app.sh` |
| Stop (keep volumes) | `./agent-fabric-scripts/stack/stop-app.sh` |
| Java unit tests | `./agent-fabric-scripts/stack/test-java.sh` |

Compose file: [`../docker-compose/docker-compose.yml`](../docker-compose/docker-compose.yml).

After start, load routes with [`../catalogue-seed/add-seed-data.sh`](../catalogue-seed/add-seed-data.sh), then try chats at [http://localhost:3014/chat](http://localhost:3014/chat).
