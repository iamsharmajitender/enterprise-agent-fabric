# chat-shopassist_case

Route id: `shopassist_case` · version `2026.08.1` · Pattern 1 (autonomous chat).

| File | Contract | Database |
| --- | --- | --- |
| [`capability.sql`](capability.sql) | Domain tools | `acr.registry.capabilities` |
| [`manifest.sql`](manifest.sql) | Tool manifest | `acr.registry.manifests`, `adp.dataplane.manifests` |
| [`prompt.sql`](prompt.sql) | Host prompt | `adp.dataplane.prompt_packs` |
| [`route.sql`](route.sql) | Route pin | `adp.dataplane.routes` |
| [`memory.sql`](memory.sql) | Memory profile | `adp.dataplane.memory_profiles` |
| [`intent.sql`](intent.sql) | `/shopassist` command | `adp.dataplane.intent_rules` |

No `workflow.sql` — this route uses manifest tools + prompt, not a fixed workflow.

```bash
./agent-fabric-scripts/stack/route/shopassist_case/add.sh
```

Then open [http://localhost:3014/chat](http://localhost:3014/chat) and run `shopassist_case_ask`.

Remove this route from Postgres only: `./remove.sh` (same directory).
