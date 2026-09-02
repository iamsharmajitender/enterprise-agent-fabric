# Implementation Plan: Route-contract stage data sharing (local Fabric)

## Overview

Explore, then close, the gap between **what a route contract can name** (multi-stage workflow, prefetch, branch, human gate, child `agent`) and **what Runtime actually passes between stages**.

Today the run graph has two channels only:

| Channel | Lives on | Who consumes it |
| --- | --- | --- |
| `goal` | Start body (`payload` / utterance). Copied into every HTTP tool. **Never updated.** | Every HTTP stage |
| `notes` | Append-only **strings** (`text` / `message` / LLM completion) | LLM stages (`query_formulation`, `classify`, `synthesis`); `/turns` when `working=session` |

That is enough when every tool already has its ids in the job payload, and later stages are **LLM** readers of prose. It is **not** a general dataflow. Dummy jobs still complete because agent-fabric-mocks ignores request bodies.

**Do this list later**, after v1 seed jobs are green. Do not fold it into [todo.md](./todo.md). Do not reopen locked fabric rules (AFD-only start, pin-then-hydrate, chat FR-5, Shared Memory as a fifth store).

**Not in this plan:** `conversation` / `long_term` Shared Memory ([future-enhancement](./future-enhancement.md#shared-memory-conversation-and-long_term)); LLM-as-judge evals ([eval-plan](./eval-plan.md) slice 3); Layer ②/③ classify ([intent-plan](./intent-plan.md)); executing `branch` / `human_gate` as a product UX (this plan only uses them as **consumers** of stage data).

**Docs map:** [README.md](../README.md). **Behaviour / architecture source:** [agent-runtime](../04-architecture/agent-runtime.mdx), [route contract](https://jitendersharma.dev/playbooks/agents/intent-router/route-contract-reference), README [Memory](../../README.md#memory) / [Workflows](../../README.md#workflows) / [Retrieve](../../README.md#retrieve). Graph: `agent-runtime/app/graph/workflow.py`. Policy: `dataplane.memory_profiles.working`.

## Present vs remaining

| Share scenario | Route contract / seed | Runtime today | This plan |
| --- | --- | --- | --- |
| Ingress ids on every tool | Jobs `payload` → AFD `goal` | Yes. `payload = dict(goal)` | Keep. `goal` stays immutable. |
| LLM reads prior stage prose | `llm_role` classify / synthesis / query_formulation | Yes. `_user_blob(goal, notes)` | Keep `notes` as the LLM view. |
| LLM writes `query` then HTTP | `query_formulation` | Yes. `payload["query"]` | Keep. |
| Tool JSON → next **HTTP** tool | Workflow stage order (`ocr` → `risk_engine`, identity → freeze) | Yes. Slot merge + `input_schema` hop validation | **Done** (D3–D5). |
| Prefetch pack → generate | `retrieval.mode=deterministic_prefetch`; empty-`invoke` stages | Yes. `working.slots.prefetch` + downstream consume | **Done** (D6–D7). |
| Score → next node | Workflow `branch` (`kyc_onboarding`) | Yes. Branch reads prior slot | **Done** (D8). |
| Human packet → resume | `type=human_gate` | Yes. `status=waiting`; resume via `/turns` | **Done** (D9). |
| Parent extract → child job | Capability `kind=agent` | Yes. Projected child `payload` only | **Done** (D10). |
| Crash continue | `loop=checkpoint` | Yes. `resume_index`; failed run resumes via `/turns` | **Done** (D11). |
| Next chat turn transcript | `conversation=session` | Catalogue-only. `/turns` reloads **notes/slots**, not utterances. | **Out.** Shared Memory. |
| Facts for a later journey | `long_term=retrieve_only` | Catalogue-only. | **Out.** Shared Memory / RAG. |

## Architecture decisions (accepted — D2)

Do **not** add a dataflow DSL on the route row in the first slice. The route already points at a workflow; Runtime owns assembly.

1. **`goal` is ingress only.** Job/chat payload. Immutable for the run. Tools that need a caller-supplied id (`card_id`, `doc_id`) keep reading it from `goal`.
2. **`working` becomes structured.** Persist `{ "notes": [...], "slots": { "<stage_id>": <json> } }` on `ar.runtime.runs.working` when `working=session`. `notes` stays the string list the LLM sees (projection of slots + prose).
3. **HTTP payload = `goal` ∪ schema-selected slot keys.** For each domain HTTP invoke, merge keys from **all prior stage slots** whose names appear in the next capability `input_schema.properties` and are not already in `goal`. **Do not** put `notes` strings on the HTTP body. Unbounded “dump every prior JSON key” is forbidden — only keys declared on the next `input_schema` are merged.
3a. **Validate at the hop (D4a).** Before invoke, every `input_schema.required` key must be present on the assembled body (fail closed). Slot write stores an **`output_schema` subset** when the capability defines `properties`; otherwise the full HTTP JSON body. LLM classify JSON is parsed when possible; OCR/prefetch/human-gate fields are untrusted. Domain HTTP is projected/validated JSON — not HTML-sanitised strings. PEP is authorisation, not a payload contract.
4. **Prefetch is a writer of slots**, not `long_term`. Same working blob. Corpus POST is still unpublished until D6; empty `invoke` stays a no-op until then.
5. **Branch / gate read slots**, they do not invent a second state object.
6. **Child `agent` does not inherit notes.** Parent projects only keys declared on the agent capability `input_schema.properties` from `goal` ∪ prior slots (same merge rule as domain HTTP). Fail closed if required child fields are missing. Runtime POSTs API AFD `/v1/jobs` with `{ route_id, idempotency_key, payload }`; not callee AR.
7. **Do not store conversation or long-term facts on the run pin.** Unchanged.
8. **Slot size cap / deny-list:** none in the first slice (D3–D5).
9. **D5 proof route:** `purchase_refund` (`extract_fields` → `match_purchase` needs `merchant`, `amount`, `date`).
10. **D11 checkpoint resume:** **Done.** Generic resume from `resume_index` on failed checkpointed runs; `loop=none` still fail-closed.

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
D1 scenario matrix (which seed routes actually need a share)
    → D2 lock payload-merge rule (human)
        → D3 structured working slots (persist + reload)
            → D4 HTTP merge → D4a validate hop against `input_schema` + D5 one seed proof (card_freeze or msa_risk_review)
                → D6–D7 prefetch pack (policy_memo / pack_then_review)
                    → D8 branch, D9 human_gate
                        → D10 parent→child projection
                            → D11 checkpoint resume (optional)
                                → D12–D13 README + prove
```

One vertical slice at a time. After D5, `card_freeze` (or the chosen chain) must fail if agent-fabric-mocks does **not** receive the prior stage’s fields. After D7, a prefetch route must fail if generate/LLM sees empty pack.

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
# seed job whose second tool requires a field the first tool returns
./agent-fabric-scripts/route-runs/run-job.sh card_freeze   # or the route D1 picks
# agent-fabric-mocks / test asserts body, not only 200
```

## Task list

### Phase 0: Explore (do this first — no Runtime behaviour change)

- [x] Task D1: Scenario matrix for the catalogue seed
- [x] Task D2: Lock working-slot + HTTP merge rule (human review)

### Checkpoint: Explore

- [x] Every Pattern 2/3 seed route is labelled: `goal_only` / `notes_to_llm` / `json_to_http` / `prefetch_pack` / `branch` / `human_gate` / `agent`
- [x] Merge rule written; “dump all notes into every tool” is rejected or explicitly scoped
- [x] Human review before D3

### Phase 1: Structured working → next HTTP tool

- [x] Task D3: Persist `working.slots` (keep `notes` as LLM projection)
- [x] Task D4: HTTP invoke payload includes selected slots
- [x] Task D4a: Validate assembled payload against next `input_schema`; constrain slot store
- [x] Task D5: One seed chain proves agent-fabric-mocks / test sees prior JSON

### Checkpoint: HTTP handoff

- [x] LLM stages still see `notes` strings
- [x] `goal` in the run pin / checkpoint is still the ingress payload
- [x] Hop validated against next `input_schema`; unbounded slot dump rejected
- [x] A test fails if the second tool is called with `goal` only

### Phase 2: Prefetch pack

- [x] Task D6: Prefetch writer (corpus POST → slot)
- [x] Task D7: `policy_memo` / `pack_then_review` consume the pack

### Phase 3: Control-flow consumers

- [x] Task D8: Execute `branch` from a slot
- [x] Task D9: `human_gate` pause + merge human payload

### Phase 4: Cross-run / resume

- [x] Task D10: `agent` child goal projection
- [x] Task D11: Resume graph from `loop=checkpoint` (optional)

### Packaging

- [x] Task D12: README Memory / Workflows / Retrieve — goal vs slots vs notes
- [x] Task D13: Verification checklist (break a mock, watch the job fail)

## Verification checklist (D13)

**`completed` on `./agent-fabric-scripts/route-runs/run-job.sh --all` is pin/hydrate smoke only.** It does not prove that stage *N*’s JSON reached stage *N+1*, that prefetch packed chunks, or that branch/gate read a slot.

### D5 — HTTP slot handoff

**Proof route:** `purchase_refund` — job payload has `doc_id` and `account_id` only. Classify `extract_fields` must supply `merchant`, `amount`, `date` to HTTP `match_purchase`.

```bash
# Unit (no compose): happy merge + fail closed when classify omits fields
cd agent-runtime && uv run pytest \
  tests/test_graph.py::test_http_after_classify_merges_slot_fields_not_notes \
  tests/test_graph.py::test_http_after_classify_fails_when_slot_missing_required_fields -q

# Compose (optional): end-to-end
./agent-fabric-scripts/stack/start-app.sh
WAIT=1 ./agent-fabric-scripts/route-runs/run-job.sh purchase_refund
```

**Break it:** the second pytest fails with `missing required field` before `match_purchase` runs. **Restore:** classify returns all required keys — first pytest passes.

### D7 — Prefetch pack

**Proof routes:** `policy_memo`, `pack_then_review` — prefetch POSTs corpus gateway; pack in `working.slots.prefetch`; synthesis fails if empty.

```bash
cd agent-runtime && uv run pytest tests/test_prefetch.py tests/test_graph.py -k prefetch -q

./agent-fabric-scripts/stack/start-app.sh   # if not already up
WAIT=1 ./agent-fabric-scripts/route-runs/run-job.sh policy_memo
```

**Break it:** stop or stale-build agent-mocks so `POST /v1/search/*` is missing — prefetch route fails (503 / empty pack). **Restore:** `docker compose build agent-mocks && docker compose up -d agent-mocks` (from `agent-fabric-scripts/docker-compose/`), rerun.

### Quick regression (all dataflow unit tests)

```bash
cd agent-runtime && uv run pytest \
  tests/test_graph.py tests/test_memory.py tests/test_runs.py \
  tests/test_prefetch.py tests/test_checkpoint.py tests/test_human_gate.py \
  tests/test_payload.py tests/test_jobs_client.py -q
```

### Still catalogue-only (not this track)

| Item | Status |
| --- | --- |
| `conversation=session` | No transcript store — Shared Memory ([future-enhancement](./future-enhancement.md#shared-memory-conversation-and-long_term)) |
| `long_term=retrieve_only` | No cross-journey fact store / RAG recall |
| Pattern 3 stage `allowlist` | Metadata on ADP; AR does not enforce inner tool picks yet |

**Shipped in this track (D8–D11):** workflow `branch`, `human_gate` pause/resume, `kind=agent` child projection, `loop=checkpoint` crash resume.

## Human review (track sign-off)

**Date:** 2026-08-26

### Examiner questions ([definition of useful](#examiner-questions-definition-of-useful))

| # | Question | Result |
| --- | --- | --- |
| 1 | Ingress (`goal`) vs derived (`slots`)? | Documented in README Memory + [data.md](../02-understand/data.md). `purchase_refund` proof. |
| 2 | Stage N HTTP body includes stage N−1 output? | Unit tests pass (`test_http_after_classify_merges_slot_fields_not_notes`). D5 checklist. |
| 3 | Prefetch pack used by generate? | `test_prefetch.py` + graph prefetch tests pass. D7 checklist. |
| 4 | Branch reads slot, not hardcoded edge? | `test_branch.py`, `kyc_onboarding` workflow tests. |
| 5 | Child job gets projected goal, not parent notes? | `test_payload.py`, `test_jobs_client.py`. |

### Verification executed

- 84 dataflow unit tests passed (D13 regression bundle)
- D5 + D7 pytest checklist commands run green
- Catalogue matrix updated: [routes.md](../03-catalogue/routes.md), [use-cases.md](../03-catalogue/use-cases.md), [status.md](../02-understand/status.md)

### Residual gaps (honest)

| Gap | Notes |
| --- | --- |
| Dummy `--all` | Pin/hydrate smoke only — does not assert HTTP bodies |
| Pattern 0/1 + prefetch mode | No pack without a workflow prefetch stage |
| `card_freeze`, `msa_risk_review` | Still goal-only HTTP (not D5 proof routes) |
| `conversation` / `long_term` | Catalogue-only — Shared Memory not built |
| Pattern 3 allowlist | Metadata only; inner CALL/DONE not enforced |
| agent-fabric-mocks | Returns canned JSON; does not validate request bodies |

### Sign-off

**Dataflow track D1–D13 accepted** for local Fabric. Treat dummy job `completed` as smoke unless [D13 verification](#verification-checklist-d13) proof routes/checklist pass.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Treat dummy `--all` green as “dataflow works” | High | D5/D7 require body assertions; agent-fabric-mocks must validate or tests stub the body |
| Merge entire history into every HTTP call | High (PII, schema) | D2 names selected slots; default is not “all notes”; D4a schema-validates the hop |
| Treat pin as making tool JSON trusted | High | D4a: next `input_schema` fail-closed; OCR/LLM/prefetch untrusted |
| Slots become a mini Shared Memory | Med | TTL = run; `conversation` / `long_term` stay out |
| Branch/gate scope explodes into a workflow engine | Med | D8–D9 only consume slots already written; no new catalogue DSL |
| Prefetch implemented as `long_term` | Med | Pack writes `working.slots` only |
| Child inherits parent notes | High | D10 fail-closed projection |

## Open questions (answer in D2)

- Merge key: namespaced `prior.<stage_id>` vs workflow `input_from: ["ocr"]` vs “last JSON body only”?
- Slot value: full tool JSON, or only `output_schema` fields?
- Cap / redaction on slots (size, deny-list keys)? Extra keys: strip vs reject?
- Validate next `input_schema` on every hop (yes — D4a); any exception for LLM-only stages?
- Which seed route is the D5 proof (`card_freeze` vs `msa_risk_review` vs `claims_adjudicate`)?
- Is D11 in this plan or a Runtime reliability follow-on?

## Out of scope (do not sneak in)

- Shared Memory box; writing transcripts onto `ar.runtime.runs`
- Replacing Pattern 1’s CALL/DONE loop with a richer planner
- Output-schema validation of the **assistant** reply (eval slice 3)
- Moving `working` off the run pin
- A generic visual dataflow mapper in Control Plane
