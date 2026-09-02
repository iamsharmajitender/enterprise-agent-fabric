# Stack

Start, stop, and seed the local fabric.

| Script | Command |
| --- | --- |
| Start (build + up + health wait) | `./agent-fabric-scripts/stack/start-app.sh` |
| Stop (keep volumes) | `./agent-fabric-scripts/stack/stop-app.sh` |
| Java unit tests | `./agent-fabric-scripts/stack/test-java.sh` |
| Wipe all DBs | `./agent-fabric-scripts/stack/delete-seed-data.sh` |
| Reload all routes | `./agent-fabric-scripts/stack/add-seed-data.sh` |
| Wipe + one route | `./agent-fabric-scripts/stack/add-seed-data.sh --clean shopassist_case` |
| Seed one route (no wipe) | `./agent-fabric-scripts/stack/add-seed-data.sh shopassist_case` |

Compose file: [`../docker-compose/docker-compose.yml`](../docker-compose/docker-compose.yml).

Flyway migrations create schema only; route data loads from `route/` via `add-seed-data.sh` or per-route `add.sh`.

```bash
./agent-fabric-scripts/stack/start-app.sh
./agent-fabric-scripts/stack/add-seed-data.sh
```

Open [http://localhost:3014/chat](http://localhost:3014/chat) to run chat demos from [`agent-fabric-scratchpad/catalog/chats.json`](../../agent-fabric-scratchpad/catalog/chats.json).

Wipe and seed a single route while iterating:

```bash
./agent-fabric-scripts/stack/add-seed-data.sh --clean shopassist_case
# or from inside the route pack:
./agent-fabric-scripts/stack/route/shopassist_case/add.sh
./agent-fabric-scripts/stack/route/shopassist_case/remove.sh
```

## SQL layout

```
sql/
└── delete-seed-data.sql

route/
├── fee_explain/
│   ├── add.sh / remove.sh   # load or drop this route only
│   └── *.sql
└── shopassist_case/
    ├── add.sh / remove.sh
    └── *.sql
```

Apply order: `capability` → `manifest` → `prompt` → `route` → `retrieval` → `memory` → `workflow`.

## Add a route

1. Copy `route/shopassist_case/` → `route/<route_id>/`, edit the SQL files.
2. Run `./agent-fabric-scripts/stack/add-seed-data.sh <route_id>` (or `./add.sh` / `--clean` to wipe first).
3. Add a chat row to [`agent-fabric-scratchpad/catalog/chats.json`](../../agent-fabric-scratchpad/catalog/chats.json), then try it at [http://localhost:3014/chat](http://localhost:3014/chat).
