# Retrieve

Three ideas — do not conflate them:

| Mechanism | What it is | Store / transport |
| --- | --- | --- |
| **`deterministic_prefetch`** | App packs scoped corpora **before** generate | `working.slots.prefetch` on the run pin (not `long_term`) |
| **Retrieve tool** | Named capability on the manifest (`clause_search`, `account_fee_lookup`) | Ordinary HTTP to `invoke.url` (local: agent-fabric-mocks) |
| **`long_term=retrieve_only`** | Facts for a **later journey** | **Catalogue-only** — Shared Memory / RAG (not built) |

Do not add a retrieve `kind` — [capabilities](capabilities.md).

## Modes on the route

| `retrieval.mode` | Catalogue | This Runtime |
| --- | --- | --- |
| `tool` | Named retrieve capability over `scope` corpus ids | HTTP to that capability’s `invoke.url`. Payload = assembled `goal` ∪ schema-selected slots |
| `deterministic_prefetch` | App packs `scope` corpora before generate | GET each corpus row from ADP, POST `{collection, goal}` to corpus `url`, write `working.slots.prefetch`, inject pack text into downstream LLM user blobs (and HTTP when `input_schema` includes `packed_text`) |
| `none` / omit | — | No corpus access |

`policy_memo` and `pack_then_review` are prefetch routes (**D7 proof**). `fee_explain` is `tool` mode: HTTP to `account_fee_lookup`.

## Prefetch flow

1. Hydrate builds a prefetch stage node (`invoke` empty, `llm_role=none`).
2. When the route row has `retrieval.mode=deterministic_prefetch`, `agent-runtime/app/agents/prefetch.py` POSTs each scoped corpus gateway (Compose: agent-fabric-mocks `POST /v1/search/{gateway}`).
3. Chunks land in `working.slots.prefetch` and a formatted note for LLM stages.
4. Synthesis / query-formulation stages fail closed if the pack is empty.

Empty invoke **without** prefetch mode is still a no-op.

## Corpora table

ADP `dataplane.corpora` stores gateway url, collection, status. `retrieval.scope` is corpus ids only (`["policy-engine"]`). Runtime GETs corpora and POSTs published rows only.

Omit the retrieval row when the route must not touch an index (`email_summarize`, `llm_pipeline`).

Box packs: [04-architecture](../04-architecture/). Scenario matrix: [dataflow/scenarios.md](../dataflow/scenarios.md). Verification: [dataflow-plan.md](../tasks/dataflow-plan.md#verification-checklist-d13).
