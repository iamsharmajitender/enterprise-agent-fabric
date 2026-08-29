# agent-fabric-scripts

Local operator tooling, split by purpose.

## Folders

| Folder | Purpose |
| --- | --- |
| [`stack/`](stack/) | Start and stop the fabric (Docker Compose) |
| [`catalogue-seed/`](catalogue-seed/) | Seed routes into Postgres and run chat demos |
| [`docker-compose/`](docker-compose/) | Compose file, Postgres, Grafana |

## Quick start

From **repo root**:

```bash
./agent-fabric-scripts/stack/start-app.sh
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh
./agent-fabric-scripts/catalogue-seed/run-chat.sh shopassist_case_ask
```

## Cheat sheet

| Goal | Command |
| --- | --- |
| Start | `./agent-fabric-scripts/stack/start-app.sh` |
| Stop | `./agent-fabric-scripts/stack/stop-app.sh` |
| Wipe all DBs | `./agent-fabric-scripts/catalogue-seed/delete-seed-data.sh` |
| Reload all routes | `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh` |
| Wipe + one route | `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh --clean shopassist_case` |
| Seed one route (no wipe) | `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh shopassist_case` |
| List chat demos | `./agent-fabric-scripts/catalogue-seed/run-chat.sh --list` |
| Run a demo | `./agent-fabric-scripts/catalogue-seed/run-chat.sh <id>` |

Full runbook: [README.md](../README.md).
