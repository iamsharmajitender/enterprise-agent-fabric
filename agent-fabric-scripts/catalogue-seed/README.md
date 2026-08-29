# Catalogue seed

Load route catalogue rows into Postgres and run chat demos. Stack must be running (`../stack/start-app.sh`).

## Commands

| Script | What it does |
| --- | --- |
| [`delete-seed-data.sh`](delete-seed-data.sh) | Wipe all application data (afd, adp, ar, acr, audit) |
| [`add-seed-data.sh`](add-seed-data.sh) | Wipe + reload **all** route packs under `route/` |
| [`add-seed-data.sh <route_id>`](add-seed-data.sh) | Load one route pack only (no wipe) |
| [`add-seed-data.sh --clean <route_id>`](add-seed-data.sh) | Wipe all DBs, then load one route pack |
| [`run-chat.sh`](run-chat.sh) | Post a chat demo from [`chats.json`](chats.json) |

```bash
./agent-fabric-scripts/stack/start-app.sh
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh
./agent-fabric-scripts/catalogue-seed/run-chat.sh shopassist_case_ask
```

Wipe and seed a single route while iterating:

```bash
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh --clean shopassist_case
./agent-fabric-scripts/catalogue-seed/run-chat.sh shopassist_case_ask
```

## SQL layout

```
sql/
└── delete-seed-data.sql

route/
├── fee_explain/
└── shopassist_case/
    ├── capability.sql   # ACR tools
    ├── manifest.sql     # ACR + ADP manifest
    ├── prompt.sql       # ADP prompt_pack
    ├── route.sql        # ADP route row
    ├── retrieval.sql    # optional
    ├── memory.sql       # optional
    └── workflow.sql     # only when workflow_id is set
```

Apply order: `capability` → `manifest` → `prompt` → `route` → `retrieval` → `memory` → `workflow`.

## Add a route

1. Copy `route/shopassist_case/` → `route/<route_id>/`, edit the SQL files.
2. Mirror in Flyway for clean `start-app.sh`.
3. Run `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh <route_id>` (or `--clean` to wipe first).
4. Add a chat row to [`chats.json`](chats.json), then `./run-chat.sh <id>`.

## Chat demos

| File | Role |
| --- | --- |
| [`chats.json`](chats.json) | Demo definitions (message, claims, expectations) |
| [`run-chat.sh`](run-chat.sh) | Shell entrypoint |
| [`run_chat.py`](run_chat.py) | Posts to Front Door, polls events |

Environment: `AFD_URL` (default `http://localhost:3005`), `WAIT=1` with `--all`, `FABRIC_LLM_STUB=1` for stub LLM.
