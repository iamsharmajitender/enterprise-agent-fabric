# Memory

`dataplane.memory_profiles` is **policy** on the route (`conversation`, `working`, `loop`, `long_term`, TTL, isolation). It is not a memory store. ADP serves the row; AR honors two fields on the run pin (`agent-runtime/app/core/memory.py`).

| Field | Catalogue | This Runtime |
| --- | --- | --- |
| `working=session` | Scratch for this run | After each stage, writes `notes` to `runtime.runs.working`. `POST /v1/runs/{id}/turns` reloads those notes |
| `loop=checkpoint` | Crash cursor | Writes `{step, stage_id, result, goal}` to `runtime.runs.checkpoint`. Resume-from-step is **not** wired |
| `conversation=session` | Next turn should see prior utterances | **Catalogue-only.** No transcript store. `/turns` reloads `notes`, not user/assistant text |
| `long_term=retrieve_only` | Facts for a later journey | **Catalogue-only.** Not retrieve, not prefetch |

AFD freeze (`session_id` → pin) is route stickiness, not conversation memory.

## Not a Shared Memory box

`conversation` and `long_term` need a fifth store (not AFD / ADP / AR / ACR). This repo does not have that box. Do not write transcripts or long-term facts onto the run pin.

Retrieval is a sibling table. Prefetch is not `long_term`. See [retrieve](retrieve.md).

Omit the profile on one-shot LLM/jobs (`email_summarize`, `llm_pipeline`, `card_freeze`). Author it when later stages or a later turn must keep `notes` (`working=session`) or when an open loop should record a cursor (`loop=checkpoint`). `fee_explain` authors working + loop.

Box packs: [04-architecture](../04-architecture/). Later: [dataflow-plan.md](../tasks/dataflow-plan.md) (stage slots, not Shared Memory).
