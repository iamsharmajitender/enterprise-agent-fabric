# agent-fabric-mocks

Local doubles for Enterprise Agent Fabric. Compose (and tests) use these instead of real domain APIs.

| Folder | What |
| --- | --- |
| [`tools/`](tools/) | Domain HTTP doubles on `:3010` (Compose service `tool-mock`). One file per capability under [`tools/catalog/`](tools/catalog/) |

```bash
./docs/run/scripts/start-app.sh   # rebuilds from this tree
```

Add a domain tool: add `tools/catalog/<id>.json` with unique `method`+`path`, point capability `invoke.url` at `http://tool-mock:3010{path}`, rebuild.
