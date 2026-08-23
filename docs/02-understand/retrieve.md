# Retrieve

Two modes on `dataplane.retrieval`. Prefetch is not `long_term` and not a tool list. A retrieve **tool** is an ordinary ACR capability.

| `retrieval.mode` | Catalogue | This Runtime |
| --- | --- | --- |
| `tool` | Named retrieve capability over `scope` corpus ids | HTTP to that capability’s `invoke.url` (local: tool-mock), same as any domain tool. Payload is still `dict(goal)` from `agent-runtime/app/graph/workflow.py` |
| `deterministic_prefetch` | App should pack `scope` corpora before generate | **No.** Mode and scope sit on the route. The prefetch stage has empty `invoke` and is a no-op |

`policy_memo` is a prefetch route. It does **not** POST the corpus gateway. `fee_explain` is `tool` mode: HTTP to `account_fee_lookup`.

## Prefetch is a no-op

Without a manifest, `agent-runtime/app/agents/hydrate.py` builds one node per workflow stage with `invoke: {}`. `llm_role=none` and no url skip HTTP. Packed chunks are never written to `notes` or anywhere else.

## Corpora table

ADP `dataplane.corpora` stores gateway url, collection, status. `retrieval.scope` is corpus ids only (`["policy-engine"]`). AR does not GET corpora and does not POST those urls yet.

Designed (not in this Runtime): look up each id, POST the gateway, pack chunks for generate. Until then, retrieve tools hit tool-mock (`fee_explain` → fee lookup HTTP) and prefetch stages skip HTTP.

Omit the retrieval row when the route must not touch an index (`email_summarize`, `llm_pipeline`).

Box packs: [04-architecture](../04-architecture/). Closing the pack gap: [dataflow-plan.md](../tasks/dataflow-plan.md).
