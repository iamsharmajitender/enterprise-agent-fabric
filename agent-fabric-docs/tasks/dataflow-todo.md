# Task list: Route-contract stage data sharing (local Fabric)

Plan: [dataflow-plan.md](./dataflow-plan.md) (includes **Present vs remaining** and proposed architecture). Docs map: [README.md](../README.md). Architecture: [agent-runtime](../04-architecture/agent-runtime.mdx). Route contract: [route-contract-reference](https://jitendersharma.dev/playbooks/agents/intent-router/route-contract-reference).

**Execution order:**

1. **Explore** — D1–D2. Matrix + merge rule. No Runtime behaviour change. **Do this first when you pick the track up.**
2. **HTTP handoff** — D3–D5. Structured slots, schema-validate the hop (D4a), then one seed chain that fails if the next tool does not see prior JSON.
3. **Prefetch pack** — D6–D7. Corpus POST writes a slot; generate/LLM actually uses it.
4. **Control-flow consumers** — D8–D9. `branch` / `human_gate` read slots.
5. **Cross-run / resume** — D10–D11. Child projection; checkpoint resume optional.
6. **Packaging** — D12–D13.

v1 fabric tasks remain in [todo.md](./todo.md); observability remains in [observability-todo.md](./observability-todo.md); evals remain in [eval-todo.md](./eval-todo.md); intent remains in [intent-todo.md](./intent-todo.md). Shared Memory (`conversation` / `long_term`) stays in [future-enhancement.md](./future-enhancement.md#shared-memory-conversation-and-long_term). This list does not replace them.

Dummy jobs returning `completed` is **not** acceptance. Tool-mock today ignores bodies.

---

## 0. Explore

## Task D1: Scenario matrix for the catalogue seed

**Description:** Label every Pattern 2/3 (and relevant Pattern 1) seed route by **how data must move**, using the live seed — not a new abstraction. This is the explore artifact. Runtime stays unchanged.

**Acceptance criteria:**
- [x] Table lives under `agent-fabric-docs/tasks/` (this plan) or `agent-fabric-docs/dataflow/scenarios.md` listing `route_id`, workflow/manifest, share kind: `goal_only` | `notes_to_llm` | `json_to_http` | `prefetch_pack` | `branch` | `human_gate` | `agent` | `none`
- [x] At least `card_freeze`, `msa_risk_review`, `kyc_onboarding`, `policy_memo`, `pack_then_review`, `claims_adjudicate`, `fee_explain`, one `agent` parent, and `llm_pipeline` are labelled
- [x] Each `json_to_http` row names the **field** stage N+1 needs that stage N produces (even if agent-fabric-mocks does not return it today)
- [x] `conversation` / `long_term` rows are marked **out of this plan** (Shared Memory)
- [x] Pick a recommended D5 proof route (default: `card_freeze` if identity → limit → freeze needs a produced id; else `msa_risk_review`)

**Verification:**
- [x] Manual: labels match `V1__dataplane.sql` / catalogue seed, not README wishful tense
- [x] No code change required to merge D1

**Dependencies:** None

**Files likely touched:**
- `agent-fabric-docs/tasks/dataflow-plan.md` (matrix section) or `agent-fabric-docs/dataflow/scenarios.md`
- Read-only: `agent-data-plane/src/main/resources/db/migration/V1__dataplane.sql`, `agent-fabric-scripts/route-runs/job/jobs.json`, `agent-runtime/app/graph/workflow.py`

**Estimated scope:** Small

---

## Task D2: Lock working-slot + HTTP merge rule

**Description:** Human decision before any Runtime merge. Close the open questions in [dataflow-plan.md](./dataflow-plan.md). Write the rule so D3–D4 do not invent a DSL on the fly.

**Acceptance criteria:**
- [x] Written rule: `goal` immutable; `slots[stage_id] =` (full JSON | output_schema subset)
- [x] Written rule: HTTP payload = `goal` ∪ **selected** slots (namespaced `prior.<id>` **or** workflow `input_from` **or** last JSON only). “All notes into every tool” is explicitly rejected or tightly scoped
- [x] Written rule: a pinned route is **not** a trust boundary between tools. Before invoke, the assembled payload must match the next capability `input_schema` (fail closed). Slot store is `output_schema` subset or full JSON (pick one). LLM-written fields (`query_formulation`), OCR/prefetch text, and human-gate packets are untrusted. Domain HTTP is projected/validated JSON — not HTML-sanitised strings. PEP is authorisation, not a payload contract
- [x] Cap or deny-list for slot size / keys stated (even if “none in first slice”)
- [x] D5 proof `route_id` confirmed
- [x] D11 (checkpoint resume) in or out of this track
- [x] Plan “Architecture decisions” section updated from proposed → accepted (or a short ADR under `agent-fabric-docs/decisions/` if you prefer)

**Verification:**
- [x] Manual: D4 can be implemented from the rule without a new design debate
- [x] Human review of the rule before D3

**Dependencies:** Task D1

**Files likely touched:**
- `agent-fabric-docs/tasks/dataflow-plan.md`
- Optional: `agent-fabric-docs/decisions/NNNN-working-slots.md`

**Estimated scope:** Small

---

## Checkpoint: Explore

- [x] Share kinds labelled for the catalogue seed
- [x] Merge rule accepted
- [x] Human review before Runtime changes

---

## 1. HTTP handoff

## Task D3: Persist structured `working.slots`

**Description:** Extend the working blob so stage outputs can be JSON, not only strings. Keep `notes` as the LLM-facing projection so existing `/turns` and `_user_blob` behaviour stays. Honor `working=session` vs omit/`none` as today.

**Acceptance criteria:**
- [x] `working` JSON shape `{ "notes": [str], "slots": { "<stage_id>": object } }` (empty `slots` ok)
- [x] After each graph stage, if `working=session`, flush notes **and** that stage’s slot (HTTP JSON body or parsed object; LLM-only stages may slot `{ "text": ... }`)
- [x] `/v1/runs/{id}/turns` still reloads `notes` for the LLM blob; slots reload for the next invoke
- [x] `working` omitted/`none`: in-run slots still flow inside one `graph.invoke`; nothing written to `ar.runtime.runs.working`
- [x] Old `{ "notes": [...] }` rows still load (missing `slots` → `{}`)

**Verification:**
- [x] Tests pass: `cd agent-runtime && uv run pytest tests/test_memory.py tests/test_runs.py`
- [x] Resume/turns test: two invokes with `working=session` see prior slot ids, not only note strings

**Dependencies:** Task D2

**Files likely touched:**
- `agent-runtime/app/core/memory.py`
- `agent-runtime/app/core/agent_core.py`
- `agent-runtime/app/graph/workflow.py` (slot write; keep payload merge for D4)
- `agent-runtime/tests/test_memory.py`
- `agent-runtime/tests/test_runs.py`

**Estimated scope:** Medium

---

## Task D4: HTTP invoke payload includes selected slots

**Description:** Domain HTTP (and only as D2 specified) receives derived data, not just ingress `goal`. LLM blob still uses `notes` strings. Do not mutate `goal`.

**Acceptance criteria:**
- [x] `llm_role=none` (and `query_formulation` after `query` is set) POST body matches D2 (`goal` ∪ selected slots)
- [x] A stage listed with no `input_from` / no prior slots still POSTs `goal` only (plus `query` when formulated)
- [x] `classify` / `synthesis` still skip HTTP; they still see `_user_blob(goal, notes)`
- [x] Empty `invoke.url` remains a no-op (prefetch still D6)
- [x] Unit test: second tool’s invoker payload contains a field that existed only in the first tool’s JSON response, not in `goal`

**Verification:**
- [x] Tests pass: `cd agent-runtime && uv run pytest tests/test_graph.py tests/test_memory.py`
- [x] Flip the test so the first tool returns no field → second payload must not magically contain it

**Dependencies:** Task D3

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/tests/test_graph.py`
- `agent-runtime/app/tools/invoker.py` (only if payload plumbing needs a seam)

**Estimated scope:** Medium

---

## Task D4a: Validate and constrain tool-to-tool payloads

**Description:** Pinning freezes which tools and versions run. It does not make tool A’s JSON trusted input for tool B. After D4 merge, Runtime must fail closed on a hop that does not match the next capability contract, and must not dump unbounded prior JSON (PII, secrets such as `doc_url`, OCR/LLM text) into the next HTTP body.

**Acceptance criteria:**
- [x] Before each domain (and `kind=agent`) invoke, the assembled payload is validated against that capability’s `input_schema`; mismatch fails the stage (no invoke)
- [x] Slot write stores only the D2-chosen projection (`output_schema` subset **or** full JSON). Extra keys are stripped or rejected per that rule
- [x] Size cap and/or deny-list from D2 applied on slot write (and on merge if D2 says so)
- [x] `notes` strings are never used as the next HTTP JSON; `query_formulation` / OCR / prefetch fields are treated as untrusted (type + length only; no HTML-sanitise-as-security)
- [x] Unit tests: extra field from stage N does not reach stage N+1 unless selected; missing required `input_schema` field fails closed; `notes` prose is absent from the next POST body

**Verification:**
- [x] Tests pass: `cd agent-runtime && uv run pytest tests/test_graph.py tests/test_memory.py`
- [x] Flip: valid merge that fails `input_schema` → no HTTP call

**Dependencies:** Task D2 (rule), Task D4 (merge exists to validate)

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/app/tools/invoker.py` (only if a validate seam belongs there)
- `agent-runtime/tests/test_graph.py`
- capability `input_schema` / `output_schema` on the hydrated pin (read-only unless seed schemas are too empty to test)

**Estimated scope:** Medium

---

## Task D5: Seed-chain proof (agent-fabric-mocks or contract test)

**Description:** Pick the D2 route. Make the **second** tool require a field produced by the **first**. Dummy `completed` without that field is a fail.

**Acceptance criteria:**
- [x] Tool-mock (or a Runtime contract test with a fake invoker) asserts request JSON for stage N+1
- [x] If the catalogue tool still returns only `{ "text": "..." }`, extend **that** mock with a typed field the next stage needs (keep canned `text` for LLM notes)
- [x] README dummy-request blurb for that route says which field is handed off
- [x] Seed/workflow order matches the proof (no hidden “all ids were in the job payload”)

**Verification:**
- [x] `./agent-fabric-scripts/route-runs/run-job.sh <proof-route>` completes **and** mock/tests saw the derived field
- [x] Break the first tool’s extra field → job or test fails

**Dependencies:** Task D4, Task D4a

**Files likely touched:**
- `agent-fabric-mocks/tools/` (or equivalent mock)
- `agent-fabric-scripts/route-runs/job/jobs.json` / route README
- `agent-runtime/tests/` or mock tests
- Possibly capability `output_schema` in ACR seed if the field is now real

**Estimated scope:** Medium

---

## Checkpoint: HTTP handoff

- [x] LLM paths unchanged (`notes` + `query_formulation`)
- [x] `goal` still ingress-only on pin/checkpoint
- [x] Hop validated against next `input_schema`; unbounded slot dump rejected
- [x] Proof route fails closed without the derived field

---

## 2. Prefetch pack

## Task D6: Prefetch writer (corpus POST → slot)

**Description:** `retrieval.mode=deterministic_prefetch` actually packs. Empty-`invoke` placeholder stages become writers of `working.slots` (e.g. `prefetch` / `packed_chunks`), not HTTP no-ops. This is **not** `long_term`.

**Acceptance criteria:**
- [x] Runtime resolves catalogue corpus `url` + `collection` for the route’s `retrieval.scope` (published only)
- [x] POST (or documented stub) returns chunks; writer stores them in a named slot; `notes` gets a short packed string for the LLM
- [x] Gateway down / unpublished corpus → run fails closed (no fake pack)
- [x] Routes without retrieval are unchanged
- [x] Tests cover “empty invoke + prefetch mode ⇒ slot filled” vs “empty invoke + no retrieval ⇒ still no-op”

**Verification:**
- [x] Tests pass: hydrate/graph/memory tests for prefetch
- [x] Manual or stub: slot non-empty after prefetch stage

**Dependencies:** Task D5 (or D3 if you explicitly skip the HTTP proof; default is D5)

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/app/agents/hydrate.py` (corpus pointers if needed)
- `agent-runtime/tests/test_graph.py`
- `agent-runtime/tests/test_hydrate.py`

**Estimated scope:** Medium

---

## Task D7: Prefetch seed routes consume the pack

**Description:** `policy_memo` / `pack_then_review` (names as seeded) must generate or call tools using packed chunks. A synthesis prompt that says “use packed chunks” is not enough if the slot is empty.

**Acceptance criteria:**
- [x] LLM user blob or next HTTP payload contains packed text from D6
- [x] Dummy job or graph test for at least one prefetch route asserts non-empty pack
- [x] README Retrieve section tense matches: prefetch POSTs (or “stub gateway”) rather than “designed, not in this Runtime”

**Verification:**
- [x] `./agent-fabric-scripts/route-runs/run-job.sh policy_memo` (or the D1 prefetch id) plus test assertions
- [x] Empty pack → fail or skip HTTP generate, per D2 (pick fail-closed)

**Dependencies:** Task D6

**Files likely touched:**
- `README.md` Retrieve / Memory
- dummy-request / graph tests
- prompt pack text only if the blob key name must be documented

**Estimated scope:** Small

---

## Checkpoint: Prefetch

- [x] Prefetch ≠ `long_term`
- [x] Seed prefetch route uses the slot
- [x] No retrieval ⇒ empty invoke still no-op

---

## 3. Control-flow consumers

## Task D8: Execute workflow `branch` from a slot

**Description:** Catalogue `branch` is no longer documentation-only. Next node is chosen from a **slot** (e.g. risk `high` / `low`), not from a hardcoded linear list. Stay minimal: two outgoing edges, unknown value fails closed.

**Acceptance criteria:**
- [x] Seeded `kyc_onboarding` (or D1 branch route) graph is not purely linear when `branch` is set
- [x] Slot value maps through `branch` keys to the next stage id
- [x] Missing slot / unknown key → fail closed (or documented `human_gate` / abstain — pick fail-closed)
- [x] Linear workflows without `branch` unchanged
- [x] README Workflows: `branch` is executed

**Verification:**
- [x] Graph tests: high → manual path; low → activate path; garbage → fail
- [x] `cd agent-runtime && uv run pytest tests/test_graph.py`

**Dependencies:** Task D3 (slots). Prefer after D5 so HTTP stages still write slots.

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/app/agents/hydrate.py`
- `agent-runtime/tests/test_graph.py`
- `README.md` Workflows

**Estimated scope:** Medium

---

## Task D9: `human_gate` pause and merge

**Description:** `type=human_gate` pauses the run. Resume merges the human payload into slots (D2 shape), then continues. No AFD chat UX required — Runtime API + tests are enough.

**Acceptance criteria:**
- [x] Hitting a human_gate stage sets run status to a documented paused/waiting value; does not invoke a domain URL
- [x] Resume endpoint (existing `/turns` or a dedicated resume) accepts a JSON packet, writes a slot, continues the graph
- [x] Without a packet, the gated side-effect stage does not run
- [x] README Workflows: `human_gate` is no longer “catalogue-only”

**Verification:**
- [x] Tests: pause → resume with packet → later stage sees slot; resume without packet fails or stays paused
- [x] `uv run pytest tests/test_runs.py tests/test_graph.py`

**Dependencies:** Task D8 (or D3 if you implement pause without branch; default D8)

**Files likely touched:**
- `agent-runtime/app/core/agent_core.py`
- `agent-runtime/app/api/routes/runs.py`
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/tests/test_runs.py`

**Estimated scope:** Medium

---

## Checkpoint: Control flow

- [x] Linear routes unaffected
- [x] Branch consumes slots
- [x] Gate pause + resume merges human packet

---

## 4. Cross-run / resume

## Task D10: `agent` child goal projection

**Description:** Parent must not dump `notes` into the child. Project named slots (and/or a subset of parent `goal`) into the child jobs `payload` / Runtime `goal`. LLM never sees `{jobs_url}` or `activation_target`.

**Acceptance criteria:**
- [x] Projection map documented (capability metadata or workflow stage field — pick the smaller catalogue change)
- [x] Missing required child field → parent run fails closed; no child start
- [x] Child `goal` JSON contains only projected keys
- [x] Existing FR: `kind=agent` still POSTs API AFD jobs, not callee AR

**Verification:**
- [x] Tests with fake AFD jobs client: child body == projection
- [x] Manual: seed parent route in dummy-request (if one exists) or unit-only if seed has no parent yet

**Dependencies:** Task D3

**Files likely touched:**
- `agent-runtime` invoke path for `agent`
- ACR capability JSON if the map lives there
- tests for hydrate/invoke

**Estimated scope:** Medium

---

## Task D11: Resume graph from `loop=checkpoint` (optional)

**Description:** Only if D2 kept this in-track. Writes already happen (`step`, `stage_id`, `result`, `goal`). Continue from the next stage after a crash **without** re-running completed HTTP side effects.

**Acceptance criteria:**
- [x] On restart/resume, graph skips completed steps per checkpoint
- [x] `goal` remains original ingress; slots reload from `working` if `working=session`
- [x] Side-effect stages already done are not invoked again (test with a counting fake invoker)
- [x] `loop=none` still fail-the-run on death

**Verification:**
- [x] Tests: kill after stage 0 → resume starts at stage 1; invoker call count == remaining stages
- [x] README Memory: resume-from-step is wired

**Dependencies:** Task D3; D2 must have kept D11 in scope

**Files likely touched:**
- `agent-runtime/app/core/execution.py`
- `agent-runtime/app/core/agent_core.py`
- `agent-runtime/app/core/memory.py`
- `README.md` Memory

**Estimated scope:** Medium

---

## Checkpoint: Crash resume

- [x] `resume_index` persisted after each completed stage
- [x] Failed `loop=checkpoint` run resumes via `/turns`; completed stages not re-invoked
- [x] `loop=none` failures are not recoverable

---

## 5. Packaging

## Task D12: README — goal vs slots vs notes

**Description:** Memory, Workflows, Retrieve, and dummy-request must describe the real assembly. No “designed, not in this Runtime” for items D3–D7 (and D8–D10 if done).

**Acceptance criteria:**
- [x] Memory table: `working` blob includes `slots`; `notes` is the LLM projection
- [x] Workflows: linear vs branch/gate matches what shipped
- [x] Retrieve: prefetch pack vs retrieve tools vs `long_term` still distinct
- [x] Dummy-jobs README: which proof route asserts a derived field
- [x] [dataflow-plan.md](./dataflow-plan.md) present-vs-remaining table updated

**Verification:**
- [x] Manual: a new session can answer “how does stage 2 get stage 1’s JSON?” from README + this plan

**Dependencies:** D5; D7/D8/D10 if those phases shipped in the same slice

**Files likely touched:**
- `README.md`
- `agent-fabric-scripts/route-runs/README.md`
- `agent-fabric-docs/tasks/dataflow-plan.md`

**Estimated scope:** Small

---

## Task D13: Verification checklist (break the mock)

**Description:** Examiner path: break the derived field, watch the proof fail; restore, watch it pass. Same spirit as eval E13.

**Acceptance criteria:**
- [x] Short checklist at the end of [dataflow-plan.md](./dataflow-plan.md) or `agent-fabric-docs/dataflow/README.md`: commands to run D5 (and D7 if shipped)
- [x] Explicit “`completed` on dummy `--all` is not sufficient”
- [x] Lists what is still catalogue-only (`conversation`, `long_term`, and any skipped D8–D11)

**Verification:**
- [x] Manual: follow the checklist once on a clean compose

**Dependencies:** Task D12

**Files likely touched:**
- `agent-fabric-docs/tasks/dataflow-plan.md` or `agent-fabric-docs/dataflow/README.md`

**Estimated scope:** Small

---

## Checkpoint: Track complete (for the phases you chose)

- [x] D1–D2 always
- [x] D3–D5 (including D4a hop validation) if you wanted HTTP handoff
- [x] D6–D7 if you wanted prefetch
- [x] D8–D11 only as D2 scoped
- [x] D12–D13 packaging
- [x] Human review before treating dummy jobs as dataflow-complete ([sign-off](./dataflow-plan.md#human-review-track-sign-off))
