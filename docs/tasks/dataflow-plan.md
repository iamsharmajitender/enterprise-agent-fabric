# Implementation Plan: Route-contract stage data sharing (local Fabric)

## Overview

Explore, then close, the gap between **what a route contract can name** (multi-stage workflow, prefetch, branch, human gate, child `agent_start`) and **what Runtime actually passes between stages**.

Today the run graph has two channels only:

| Channel | Lives on | Who consumes it |
| --- | --- | --- |
| `goal` | Start body (`payload` / utterance). Copied into every HTTP tool. **Never updated.** | Every HTTP stage |
| `notes` | Append-only **strings** (`text` / `message` / LLM completion) | LLM stages (`query_formulation`, `classify`, `synthesis`); `/turns` when `working=session` |

That is enough when every tool already has its ids in the job payload, and later stages are **LLM** readers of prose. It is **not** a general dataflow. Dummy jobs still complete because tool-mock ignores request bodies.

**Do this list later**, after v1 teaching jobs are green. Do not fold it into [todo.md](./todo.md). Do not reopen locked fabric rules (AFD-only start, pin-then-hydrate, chat FR-5, Shared Memory as a fifth store).

**Not in this plan:** Pattern 1 ReAct tool choice; `conversation` / `long_term` Shared Memory ([future-enhancement](./future-enhancement.md#shared-memory-conversation-and-long_term)); LLM-as-judge evals ([eval-plan](./eval-plan.md) slice 3); Layer ②/③ classify ([intent-plan](./intent-plan.md)); executing `branch` / `human_gate` as a product UX (this plan only uses them as **consumers** of stage data).

**Docs map:** [docs/README.md](../README.md). **Behaviour / architecture source:** [agent-runtime](../04-architecture/agent-runtime.md), [route contract](https://jitendersharma.dev/playbooks/agents/intent-router/route-contract-reference), README [Memory](../../README.md#memory) / [Workflows](../../README.md#workflows) / [Retrieve](../../README.md#retrieve). Graph: `agent-runtime/app/graph/workflow.py`. Policy: `dataplane.memory_profiles.working`.

## Present vs remaining

| Share scenario | Route contract / seed | Runtime today | This plan |
| --- | --- | --- | --- |
| Ingress ids on every tool | Jobs `payload` → AFD `goal` | Yes. `payload = dict(goal)` | Keep. `goal` stays immutable. |
| LLM reads prior stage prose | `llm_role` classify / synthesis / query_formulation | Yes. `_user_blob(goal, notes)` | Keep `notes` as the LLM view. |
| LLM writes `query` then HTTP | `query_formulation` | Yes. `payload["query"]` | Keep. |
| Tool JSON → next **HTTP** tool | Workflow stage order (`ocr` → `risk_engine`, identity → freeze) | **No.** HTTP never sees `notes`. | D3–D5. Structured slots + payload merge. |
| Prefetch pack → generate | `retrieval.mode=deterministic_prefetch`; empty-`invoke` stages | **No-op.** Chunks never packed. | D6–D7. Pack into slots / notes. |
| Score → next node | Workflow `branch` (`kyc_onboarding`) | Catalogue-only. Graph is linear. | D8. Execute branch from a slot. |
| Human packet → resume | `type=human_gate` | Catalogue-only. | D9. Pause, merge human payload into slots, resume. |
| Parent extract → child job | Capability `kind=agent_start` | Child `goal` is a new jobs body; no parent notes. | D10. Explicit projection. |
| Crash continue | `loop=checkpoint` | Writes `{step, stage_id, result, goal}`. Resume-from-step **not** wired. | D11. Optional last. |
| Next chat turn transcript | `conversation=session` | Catalogue-only. `/turns` reloads **notes**, not utterances. | **Out.** Shared Memory. |
| Facts for a later journey | `long_term=retrieve_only` | Catalogue-only. | **Out.** Shared Memory / RAG. |

## Architecture decisions (proposed — lock in D2)

Do **not** add a dataflow DSL on the route row in the first slice. The route already points at a workflow; Runtime owns assembly.

1. **`goal` is ingress only.** Job/chat payload. Immutable for the run. Tools that need a caller-supplied id (`card_id`, `doc_id`) keep reading it from `goal`.
2. **`working` becomes structured.** Persist `{ "notes": [...], "slots": { "<stage_id>": <json> } }` on `ar.runtime.runs.working` when `working=session`. `notes` stays the string list the LLM sees (projection of slots + prose).
3. **HTTP payload = `goal` ∪ selected slots.** Default for the first teaching proof: merge **prior slots** (not raw `notes` strings) under a namespaced key (e.g. `prior`) **or** a stage-declared `input_from`. D2 must pick one. Unbounded “dump every previous body into every tool” is forbidden (PII / over-wide schema).
4. **Prefetch is a writer of slots**, not `long_term`. Same working blob. Corpus POST is still unpublished until D6; empty `invoke` stays a no-op until then.
5. **Branch / gate read slots**, they do not invent a second state object.
6. **Child `agent_start` does not inherit notes.** Parent must name which slots become the child `goal`. Fail closed if required child fields are missing.
7. **Do not store conversation or long-term facts on the run pin.** Unchanged.

### Rejected (for now)

| Alternative | Why not first |
| --- | --- |
| Mutate `goal` in place after each stage | Mixes ingress audit with derived data; hard to replay “what the caller sent.” |
| Pass `notes` strings as the next HTTP JSON | Tools have `input_schema`; a prose list is not a `doc_id`. |
| Full JSON-pointer maps on every workflow stage on day one | Over-design before the scenario matrix (D1) says which maps exist. |
| Shared Memory for stage handoff | Wrong lifetime. Stage scratch dies with `correlation_id`. |

## Build order

Explore **before** Runtime changes. Dummy jobs completing is not evidence.

```text
D1 scenario matrix (which teaching routes actually need a share)
    → D2 lock payload-merge rule (human)
        → D3 structured working slots (persist + reload)
            → D4 HTTP merge + D5 one teaching proof (card_freeze or msa_risk_review)
                → D6–D7 prefetch pack (policy_memo / pack_then_review)
                    → D8 branch, D9 human_gate
                        → D10 parent→child projection
                            → D11 checkpoint resume (optional)
                                → D12–D13 README + prove
```

One vertical slice at a time. After D5, `card_freeze` (or the chosen chain) must fail if tool-mock does **not** receive the prior stage’s fields. After D7, a prefetch route must fail if generate/LLM sees empty pack.

## Examiner questions (definition of useful)

1. For this route, which fields are ingress (`goal`) vs derived (`slots`)?
2. Did stage N’s HTTP body include what stage N−1 produced — not only the original payload?
3. Did a prefetch stage leave chunks in working memory that generate actually used?
4. On a branch, did the recorded slot (not a hardcoded edge) pick the next node?
5. Did a child job start with a **projected** goal, not the parent’s whole notes list?

## Demo path (definition of done for D1–D5)

```text
# no Compose for D1–D2 (docs)
# D3–D5
cd agent-runtime && uv run pytest tests/test_graph.py tests/test_memory.py tests/test_runs.py
# teaching job whose second tool requires a field the first tool returns
./docs/run/dummy-jobs/run-job.sh card_freeze   # or the route D1 picks
# tool-mock / test asserts body, not only 200
```

## Task list

### Phase 0: Explore (do this first — no Runtime behaviour change)

- [ ] Task D1: Scenario matrix for the teaching catalogue
- [ ] Task D2: Lock working-slot + HTTP merge rule (human review)

### Checkpoint: Explore

- [ ] Every Pattern 2/3 teaching route is labelled: `goal_only` / `notes_to_llm` / `json_to_http` / `prefetch_pack` / `branch` / `human_gate` / `agent_start`
- [ ] Merge rule written; “dump all notes into every tool” is rejected or explicitly scoped
- [ ] Human review before D3

### Phase 1: Structured working → next HTTP tool

- [ ] Task D3: Persist `working.slots` (keep `notes` as LLM projection)
- [ ] Task D4: HTTP invoke payload includes selected slots
- [ ] Task D5: One teaching chain proves tool-mock / test sees prior JSON

### Checkpoint: HTTP handoff

- [ ] LLM stages still see `notes` strings
- [ ] `goal` in the run pin / checkpoint is still the ingress payload
- [ ] A test fails if the second tool is called with `goal` only

### Phase 2: Prefetch pack

- [ ] Task D6: Prefetch writer (corpus POST → slot)
- [ ] Task D7: `policy_memo` / `pack_then_review` consume the pack

### Phase 3: Control-flow consumers

- [ ] Task D8: Execute `branch` from a slot
- [ ] Task D9: `human_gate` pause + merge human payload

### Phase 4: Cross-run / resume

- [ ] Task D10: `agent_start` child goal projection
- [ ] Task D11: Resume graph from `loop=checkpoint` (optional)

### Packaging

- [ ] Task D12: README Memory / Workflows / Retrieve — goal vs slots vs notes
- [ ] Task D13: Verification checklist (break a mock, watch the job fail)

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Treat dummy `--all` green as “dataflow works” | High | D5/D7 require body assertions; tool-mock must validate or tests stub the body |
| Merge entire history into every HTTP call | High (PII, schema) | D2 names selected slots; default is not “all notes” |
| Slots become a mini Shared Memory | Med | TTL = run; `conversation` / `long_term` stay out |
| Branch/gate scope explodes into a workflow engine | Med | D8–D9 only consume slots already written; no new catalogue DSL |
| Prefetch implemented as `long_term` | Med | Pack writes `working.slots` only |
| Child inherits parent notes | High | D10 fail-closed projection |

## Open questions (answer in D2)

- Merge key: namespaced `prior.<stage_id>` vs workflow `input_from: ["ocr"]` vs “last JSON body only”?
- Slot value: full tool JSON, or only `output_schema` fields?
- Cap / redaction on slots (size, deny-list keys)?
- Which teaching route is the D5 proof (`card_freeze` vs `msa_risk_review` vs `claims_adjudicate`)?
- Is D11 in this plan or a Runtime reliability follow-on?

## Out of scope (do not sneak in)

- Shared Memory box; writing transcripts onto `ar.runtime.runs`
- Replacing Pattern 1 with a real ReAct chooser
- Output-schema validation of the **assistant** reply (eval slice 3)
- Moving `working` off the run pin
- A generic visual dataflow mapper in Control Plane
