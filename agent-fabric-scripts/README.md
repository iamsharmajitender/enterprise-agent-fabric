# agent-fabric-scripts

Local operator tooling, split by purpose.

## Folders

| Folder | Purpose |
| --- | --- |
| [`stack/`](stack/) | Start and stop the fabric (Docker Compose) |
| [`catalogue-seed/`](catalogue-seed/) | Seed routes into Postgres |
| [`docker-compose/`](docker-compose/) | Compose file, Postgres, Grafana |

## Quick start

From **repo root**:

```bash
./agent-fabric-scripts/stack/start-app.sh
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh
```

Open [http://localhost:3014/chat](http://localhost:3014/chat) to try chat demos.

## Cheat sheet

| Goal | Command |
| --- | --- |
| Start | `./agent-fabric-scripts/stack/start-app.sh` |
| Stop | `./agent-fabric-scripts/stack/stop-app.sh` |
| Wipe all DBs | `./agent-fabric-scripts/catalogue-seed/delete-seed-data.sh` |
| Reload all routes | `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh` |
| Wipe + one route | `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh --clean shopassist_case` |
| Seed one route (no wipe) | `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh shopassist_case` |
| Chat demos | [http://localhost:3014/chat](http://localhost:3014/chat) |

Full runbook: [README.md](../README.md).
