---
title: Memory
sidebar_label: Memory
description: "Memory profiles are route policy, not a store. What Agent Runtime honours today (working, loop) versus what the catalogue only records."
---

# Memory

`dataplane.memory_profiles` is **policy** on the route (`conversation`, `working`, `loop`, `long_term`, TTL, isolation). It is not a memory store. ADP serves the row; AR honors `working` and `loop` on the run pin (`agent-runtime/app/core/memory.py`).

| Field | Catalogue | This Runtime |
| --- | --- | --- |
| `working=session` | Scratch for this run | After each stage, writes `{ "notes": [...], "slots": { "<stage_id>": <json> } }` to `runtime.runs.working`. `/turns` reloads both |
| `loop=checkpoint` | Crash cursor | Writes `{step, stage_id, result, goal, resume_index}` to `runtime.runs.checkpoint`. Failed runs resume from `resume_index` via `/turns` with `{}` or `{ "resume": true }` |
| `conversation=session` | Next turn should see prior utterances | **Catalogue-only.** No transcript store. `/turns` reloads `notes`/`slots`, not user/assistant text |
| `long_term=retrieve_only` | Facts for a later journey | **Catalogue-only.** Not retrieve, not prefetch |

AFD freeze (`session_id` → pin) is route stickiness, not conversation memory.

## goal vs slots vs notes

| Channel | Role |
| --- | --- |
| `goal` | Immutable ingress (job `payload` / chat utterance). Never updated mid-run. |
| `slots` | Structured JSON per completed stage (`slots[stage_id]`). Used for HTTP schema merge, branch/gate, prefetch pack, child agent projection. |
| `notes` | Append-only strings for LLM stages (`_user_blob`). Optional `payload["notes"]` on HTTP. |

HTTP merge: `goal` ∪ prior-slot keys that appear on the **next** capability `input_schema` — see [data](/concepts/executing-a-request/run-data).

## Not a Shared Memory box

`conversation` and `long_term` need a fifth store (not AFD / ADP / AR / ACR). This repo does not have that box. Do not write transcripts or long-term facts onto the run pin.

Retrieval is a sibling table. Prefetch writes `working.slots.prefetch`; it is not `long_term`. See [retrieve](/concepts/authoring-a-product/retrieval).

Omit the profile on one-shot LLM/jobs (`email_summarize`, `llm_pipeline`). Author it when later stages or a later turn must keep working memory (`working=session`) or when an open loop should record a cursor (`loop=checkpoint`). `fee_explain` authors working + loop.

Box packs: [architecture](/architecture/). Scenario matrix: [dataflow scenarios](/running-locally/dataflow-scenarios). Verification: [dataflow-plan.md](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/dataflow-plan.md#verification-checklist-d13).
