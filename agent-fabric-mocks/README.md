# agent-fabric-mocks

Local doubles for Enterprise Agent Fabric. Compose (and tests) use these instead of real domain APIs.

| Folder | What |
| --- | --- |
| [`tools/`](tools/) | Domain HTTP doubles on `:3010` (Compose service `agent-mocks`). One file per capability under [`tools/catalog/`](tools/catalog/) |
| [`tools/data/corpora/`](tools/data/corpora/) | Corpus search fixtures served at `POST /corpora/{corpus_id}/search` |

```bash
./agent-fabric-scripts/stack/start-app.sh   # rebuilds from this tree
```

Add a domain tool: add `tools/catalog/<id>.json` with unique `method`+`path`, point capability `invoke.url` at `http://agent-mocks:3010{path}`, rebuild.

Add a corpus: add `tools/data/corpora/<name>.json` with `corpus_id` and `chunks`, register the row in ADP `dataplane.corpora` with `url` `http://agent-mocks:3010/corpora/<corpus_id>/search`, rebuild.
