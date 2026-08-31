# Catalogue seed

Load route catalogue rows into Postgres. Stack must be running (`../stack/start-app.sh`). Flyway migrations create schema only; route data loads from `route/` via `add-seed-data.sh` or per-route `add.sh`.

## Commands

| Script | What it does |
| --- | --- |
| [`delete-seed-data.sh`](delete-seed-data.sh) | Wipe all application data (afd, adp, ar, acr, audit) |
| [`add-seed-data.sh`](add-seed-data.sh) | Wipe + reload **all** route packs under `route/` |
| [`add-seed-data.sh <route_id>`](add-seed-data.sh) | Load one route pack only (no wipe) |
| [`add-seed-data.sh --clean <route_id>`](add-seed-data.sh) | Wipe all DBs, then load one route pack |

```bash
./agent-fabric-scripts/stack/start-app.sh
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh
```

Open [http://localhost:3014/chat](http://localhost:3014/chat) to run chat demos from [`agent-fabric-scratchpad/catalog/chats.json`](../../agent-fabric-scratchpad/catalog/chats.json).

Wipe and seed a single route while iterating:

```bash
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh --clean shopassist_case
# or from inside the route pack:
./agent-fabric-scripts/catalogue-seed/route/shopassist_case/add.sh
./agent-fabric-scripts/catalogue-seed/route/shopassist_case/remove.sh
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
2. Run `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh <route_id>` (or `./add.sh` / `--clean` to wipe first).
3. Add a chat row to [`agent-fabric-scratchpad/catalog/chats.json`](../../agent-fabric-scratchpad/catalog/chats.json), then try it at [http://localhost:3014/chat](http://localhost:3014/chat).

## Chat demos

Chat demo definitions live in [`agent-fabric-scratchpad/catalog/chats.json`](../../agent-fabric-scratchpad/catalog/chats.json). Run them from the [chat scratchpad](http://localhost:3014/chat) (included in Compose via `start-app.sh`).
