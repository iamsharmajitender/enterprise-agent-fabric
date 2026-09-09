---
title: Coverage status
sidebar_label: Coverage status
description: "What the catalogue can name versus what this Runtime executes today."
---

# Coverage status

What the catalogue can name versus what this Runtime does. Present tense on the right column is pin-hydrate-graph behaviour in `agent-runtime`. Catalogue-only means ADP stores it and Control Plane shows it; AR does not execute it.

| Capability | Catalogue | This Runtime |
| --- | --- | --- |
| goal on every HTTP tool | yes | yes |
| notes → LLM stages | yes | yes |
| notes → HTTP body | yes | yes (`payload["notes"]`) |
| query_formulation adds query | yes | yes |
| tool JSON → next HTTP (slots / fill-by-name) | implied by input schema | yes — schema-selected slot merge + hop validation |
| deterministic_prefetch pack | mode+scope on route | yes — `working.slots.prefetch` |
| workflow `branch` | stored | executed (slot → next stage) |
| `human_gate` | stored | executed (`status=waiting`; resume via `/turns`) |
| Pattern 1 `ASK` | loop verb | executed (`waiting_for=customer_ask`; chat `/turns` with `{message}` keeps the original goal) |
| `escalate_to_human` (domain tool) | stored | Pattern 1: successful handoff auto-completes parent when no pending joins; re-CALL is idempotent (no second ticket). See [escalate-to-human-handoff](/use-cases/escalate-to-human-handoff) |
| kind=agent child projection | capability `input_schema` | POST API AFD `/v1/jobs` with projected child `payload` only |
| kind=agent join (`join: true`) | capability / invoke flag | Parent pauses (`waiting_for=subagent`); poller resumes with `{ "subagents": [...] }` packet |
| conversation=session | flag | NO transcript store |
| long_term=retrieve_only | flag | NO |
| loop=checkpoint resume | writes blob + `resume_index` | resume from `resume_index` on failed run via `/turns` |

## How to read the gaps

- **goal / notes / query_formulation** — implemented in `agent-runtime/app/graph/workflow.py`. `GraphState` is `result`, `goal`, `notes`. HTTP body is schema keys from goal ∪ slots ∪ CALL args. `query_formulation` sets `payload["query"]`. LLM stages read goal and prior `notes` in `_user_blob`. Hydrate stamps `llm_role` / `llm_prompt` in `agent-runtime/app/agents/hydrate.py`.
- **Slots / fill-by-name** — prior stage JSON merges into the next HTTP body when keys appear on `input_schema`. See [data](/concepts/executing-a-request/run-data).
- **deterministic_prefetch** — corpus POST writes `working.slots.prefetch`. See [retrieve](/concepts/authoring-a-product/retrieval).
- **human_gate** — branch routes pick the next stage from a prior slot; `human_gate` sets `status=waiting` until `POST /v1/runs/{id}/turns` merges a human packet. See [patterns](/concepts/executing-a-request/autonomy-modes) and [human-review-process-gate](/use-cases/human-review-process-gate).
- **Pattern 1 ASK** — the model replies `ASK <question>` when a locator is missing. Runtime pauses (`waiting_for=customer_ask`) with that question as `result.message`. The next chat turn posts `{message}`; AR appends `customer: …` to notes and continues the same loop. Not a `human_gate`.
- **escalate_to_human** — Pattern 1 domain tool that opens an async handoff; parent completes when the handoff succeeds and no `kind=agent` joins are pending; repeat CALL does not create another ticket. See [escalate-to-human-handoff](/use-cases/escalate-to-human-handoff). Not a `human_gate`.
- **kind=agent** — child start POSTs API AFD `/v1/jobs` with a projected `payload` (`input_schema` keys from parent `goal` ∪ slots; notes excluded). Parent routes: `fraud_investigate`, `ops_start_kyc`. With `join: true` on the capability or invoke, the parent pauses (`waiting_for=subagent`) until a `{ "subagents": [...] }` resume packet arrives (AR backgrounds a jobs status poll). See [capabilities](/concepts/authoring-a-product/capability).
- **conversation / long_term** — flags on `dataplane.memory_profiles`. Not a Shared Memory box. See [memory](/concepts/authoring-a-product/memory).
- **loop=checkpoint** — cursor JSON and `resume_index` are written after each stage. Failed runs with `loop=checkpoint` resume from the next stage via `POST /v1/runs/{id}/turns` with `{}` or `{ "resume": true }`; `goal` reloads from checkpoint, `slots`/`notes` from `working`. `loop=none` still fails closed.

Later work: [dataflow-plan.md](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/dataflow-plan.md). Do not treat dummy `--all` green as dataflow. Catalogue matrix: [catalogue](/catalogue/). Contracts: [reference](/reference/). Box packs: [architecture](/architecture/).
