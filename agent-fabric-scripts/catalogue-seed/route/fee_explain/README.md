# fee_explain

Route id: `fee_explain` · version `2026.08.1` · Pattern 1 (autonomous chat/jobs).

Answers “Why was I charged?” via the `account_fee_lookup` domain API (`POST /fees/explain`).

| File | Contract | Database |
| --- | --- | --- |
| [`capability.sql`](capability.sql) | `account_fee_lookup@1.0.0` | `acr.registry.capabilities` |
| [`manifest.sql`](manifest.sql) | Tool manifest | `acr.registry.manifests`, `adp.dataplane.manifests` |
| [`prompt.sql`](prompt.sql) | Host prompt | `adp.dataplane.prompt_packs` |
| [`route.sql`](route.sql) | Route pin | `adp.dataplane.routes` |
| [`retrieval.sql`](retrieval.sql) | Retrieval policy | `adp.dataplane.retrieval` |
| [`memory.sql`](memory.sql) | Memory profile | `adp.dataplane.memory_profiles` |

Required claim: `accounts:read` (stub user `jane`).

```bash
./agent-fabric-scripts/catalogue-seed/add-seed-data.sh fee_explain
./agent-fabric-scripts/catalogue-seed/run-chat.sh fee_explain
```
