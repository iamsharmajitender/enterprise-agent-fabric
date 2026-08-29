# Tool doubles (catalog)

One JSON file per capability id. Unique `method` + `path` across files.

Point the capability `invoke.url` at `http://agent-mocks:3010{path}`. Rebuild (`./agent-fabric-scripts/stack/start-app.sh`).

Do not use path `/health`. Skip `kind=agent` capabilities (those POST Front Door `/v1/jobs`).
