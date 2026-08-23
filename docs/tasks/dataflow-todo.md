# Task list: Route-contract stage data sharing (local Fabric)

Plan: [dataflow-plan.md](./dataflow-plan.md) (includes **Present vs remaining** and proposed architecture). Docs map: [docs/README.md](../README.md). Architecture: [agent-runtime](../04-architecture/agent-runtime.md). Route contract: [route-contract-reference](https://jitendersharma.dev/playbooks/agents/intent-router/route-contract-reference).

**Execution order:**

1. **Explore** — D1–D2. Matrix + merge rule. No Runtime behaviour change. **Do this first when you pick the track up.**
2. **HTTP handoff** — D3–D5. Structured slots, then one seed chain that fails if the next tool does not see prior JSON.
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
- [ ] Table lives under `docs/tasks/` (this plan) or `docs/dataflow/scenarios.md` listing `route_id`, workflow/manifest, share kind: `goal_only` | `notes_to_llm` | `json_to_http` | `prefetch_pack` | `branch` | `human_gate` | `agent` | `none`
- [ ] At least `card_freeze`, `msa_risk_review`, `kyc_onboarding`, `policy_memo`, `pack_then_review`, `claims_adjudicate`, `fee_explain`, one `agent` parent, and `llm_pipeline` are labelled
- [ ] Each `json_to_http` row names the **field** stage N+1 needs that stage N produces (even if tool-mock does not return it today)
- [ ] `conversation` / `long_term` rows are marked **out of this plan** (Shared Memory)
- [ ] Pick a recommended D5 proof route (default: `card_freeze` if identity → limit → freeze needs a produced id; else `msa_risk_review`)

**Verification:**
- [ ] Manual: labels match `V1__dataplane.sql` / catalogue seed, not README wishful tense
- [ ] No code change required to merge D1

**Dependencies:** None

**Files likely touched:**
- `docs/tasks/dataflow-plan.md` (matrix section) or `docs/dataflow/scenarios.md`
- Read-only: `agent-data-plane/src/main/resources/db/migration/V1__dataplane.sql`, `docs/run/dummy-jobs/jobs.json`, `agent-runtime/app/graph/workflow.py`

**Estimated scope:** Small

---

## Task D2: Lock working-slot + HTTP merge rule

**Description:** Human decision before any Runtime merge. Close the open questions in [dataflow-plan.md](./dataflow-plan.md). Write the rule so D3–D4 do not invent a DSL on the fly.

**Acceptance criteria:**
- [ ] Written rule: `goal` immutable; `slots[stage_id] =` (full JSON | output_schema subset)
- [ ] Written rule: HTTP payload = `goal` ∪ **selected** slots (namespaced `prior.<id>` **or** workflow `input_from` **or** last JSON only). “All notes into every tool” is explicitly rejected or tightly scoped
- [ ] Cap or deny-list for slot size / keys stated (even if “none in first slice”)
- [ ] D5 proof `route_id` confirmed
- [ ] D11 (checkpoint resume) in or out of this track
- [ ] Plan “Architecture decisions” section updated from proposed → accepted (or a short ADR under `docs/decisions/` if you prefer)

**Verification:**
- [ ] Manual: D4 can be implemented from the rule without a new design debate
- [ ] Human review of the rule before D3

**Dependencies:** Task D1

**Files likely touched:**
- `docs/tasks/dataflow-plan.md`
- Optional: `docs/decisions/NNNN-working-slots.md`

**Estimated scope:** Small

---

## Checkpoint: Explore

- [ ] Share kinds labelled for the catalogue seed
- [ ] Merge rule accepted
- [ ] Human review before Runtime changes

---

## 1. HTTP handoff

## Task D3: Persist structured `working.slots`

**Description:** Extend the working blob so stage outputs can be JSON, not only strings. Keep `notes` as the LLM-facing projection so existing `/turns` and `_user_blob` behaviour stays. Honor `working=session` vs omit/`none` as today.

**Acceptance criteria:**
- [ ] `working` JSON shape `{ "notes": [str], "slots": { "<stage_id>": object } }` (empty `slots` ok)
- [ ] After each graph stage, if `working=session`, flush notes **and** that stage’s slot (HTTP JSON body or parsed object; LLM-only stages may slot `{ "text": ... }`)
- [ ] `/v1/runs/{id}/turns` still reloads `notes` for the LLM blob; slots reload for the next invoke
- [ ] `working` omitted/`none`: in-run slots still flow inside one `graph.invoke`; nothing written to `ar.runtime.runs.working`
- [ ] Old `{ "notes": [...] }` rows still load (missing `slots` → `{}`)

**Verification:**
- [ ] Tests pass: `cd agent-runtime && uv run pytest tests/test_memory.py tests/test_runs.py`
- [ ] Resume/turns test: two invokes with `working=session` see prior slot ids, not only note strings

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
- [ ] `llm_role=none` (and `query_formulation` after `query` is set) POST body matches D2 (`goal` ∪ selected slots)
- [ ] A stage listed with no `input_from` / no prior slots still POSTs `goal` only (plus `query` when formulated)
- [ ] `classify` / `synthesis` still skip HTTP; they still see `_user_blob(goal, notes)`
- [ ] Empty `invoke.url` remains a no-op (prefetch still D6)
- [ ] Unit test: second tool’s invoker payload contains a field that existed only in the first tool’s JSON response, not in `goal`

**Verification:**
- [ ] Tests pass: `cd agent-runtime && uv run pytest tests/test_graph.py tests/test_memory.py`
- [ ] Flip the test so the first tool returns no field → second payload must not magically contain it

**Dependencies:** Task D3

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/tests/test_graph.py`
- `agent-runtime/app/tools/invoker.py` (only if payload plumbing needs a seam)

**Estimated scope:** Medium

---

## Task D5: Seed-chain proof (tool-mock or contract test)

**Description:** Pick the D2 route. Make the **second** tool require a field produced by the **first**. Dummy `completed` without that field is a fail.

**Acceptance criteria:**
- [ ] Tool-mock (or a Runtime contract test with a fake invoker) asserts request JSON for stage N+1
- [ ] If the catalogue tool still returns only `{ "text": "..." }`, extend **that** mock with a typed field the next stage needs (keep canned `text` for LLM notes)
- [ ] README dummy-jobs blurb for that route says which field is handed off
- [ ] Seed/workflow order matches the proof (no hidden “all ids were in the job payload”)

**Verification:**
- [ ] `./docs/run/dummy-jobs/run-job.sh <proof-route>` completes **and** mock/tests saw the derived field
- [ ] Break the first tool’s extra field → job or test fails

**Dependencies:** Task D4

**Files likely touched:**
- `docs/run/tool-mock/` (or equivalent mock)
- `docs/run/dummy-jobs/jobs.json` / route README
- `agent-runtime/tests/` or mock tests
- Possibly capability `output_schema` in ACR seed if the field is now real

**Estimated scope:** Medium

---

## Checkpoint: HTTP handoff

- [ ] LLM paths unchanged (`notes` + `query_formulation`)
- [ ] `goal` still ingress-only on pin/checkpoint
- [ ] Proof route fails closed without the derived field

---

## 2. Prefetch pack

## Task D6: Prefetch writer (corpus POST → slot)

**Description:** `retrieval.mode=deterministic_prefetch` actually packs. Empty-`invoke` placeholder stages become writers of `working.slots` (e.g. `prefetch` / `packed_chunks`), not HTTP no-ops. This is **not** `long_term`.

**Acceptance criteria:**
- [ ] Runtime resolves catalogue corpus `url` + `collection` for the route’s `retrieval.scope` (published only)
- [ ] POST (or documented stub) returns chunks; writer stores them in a named slot; `notes` gets a short packed string for the LLM
- [ ] Gateway down / unpublished corpus → run fails closed (no fake pack)
- [ ] Routes without retrieval are unchanged
- [ ] Tests cover “empty invoke + prefetch mode ⇒ slot filled” vs “empty invoke + no retrieval ⇒ still no-op”

**Verification:**
- [ ] Tests pass: hydrate/graph/memory tests for prefetch
- [ ] Manual or stub: slot non-empty after prefetch stage

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
- [ ] LLM user blob or next HTTP payload contains packed text from D6
- [ ] Dummy job or graph test for at least one prefetch route asserts non-empty pack
- [ ] README Retrieve section tense matches: prefetch POSTs (or “stub gateway”) rather than “designed, not in this Runtime”

**Verification:**
- [ ] `./docs/run/dummy-jobs/run-job.sh policy_memo` (or the D1 prefetch id) plus test assertions
- [ ] Empty pack → fail or skip HTTP generate, per D2 (pick fail-closed)

**Dependencies:** Task D6

**Files likely touched:**
- `README.md` Retrieve / Memory
- dummy-jobs / graph tests
- prompt pack text only if the blob key name must be documented

**Estimated scope:** Small

---

## Checkpoint: Prefetch

- [ ] Prefetch ≠ `long_term`
- [ ] Seed prefetch route uses the slot
- [ ] No retrieval ⇒ empty invoke still no-op

---

## 3. Control-flow consumers

## Task D8: Execute workflow `branch` from a slot

**Description:** Catalogue `branch` is no longer documentation-only. Next node is chosen from a **slot** (e.g. risk `high` / `low`), not from a hardcoded linear list. Stay minimal: two outgoing edges, unknown value fails closed.

**Acceptance criteria:**
- [ ] Seeded `kyc_onboarding` (or D1 branch route) graph is not purely linear when `branch` is set
- [ ] Slot value maps through `branch` keys to the next stage id
- [ ] Missing slot / unknown key → fail closed (or documented `human_gate` / abstain — pick one in the task and test it)
- [ ] Linear workflows without `branch` unchanged
- [ ] README Workflows: `branch` is executed

**Verification:**
- [ ] Graph tests: high → manual path; low → activate path; garbage → fail
- [ ] `cd agent-runtime && uv run pytest tests/test_graph.py`

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
- [ ] Hitting a human_gate stage sets run status to a documented paused/waiting value; does not invoke a domain URL
- [ ] Resume endpoint (existing `/turns` or a dedicated resume) accepts a JSON packet, writes a slot, continues the graph
- [ ] Without a packet, the gated side-effect stage does not run
- [ ] README Workflows: `human_gate` is no longer “catalogue-only”

**Verification:**
- [ ] Tests: pause → resume with packet → later stage sees slot; resume without packet fails or stays paused
- [ ] `uv run pytest tests/test_runs.py tests/test_graph.py`

**Dependencies:** Task D8 (or D3 if you implement pause without branch; default D8)

**Files likely touched:**
- `agent-runtime/app/core/agent_core.py`
- `agent-runtime/app/api/routes/runs.py`
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/tests/test_runs.py`

**Estimated scope:** Medium

---

## Checkpoint: Control flow

- [ ] Linear routes unaffected
- [ ] Branch and gate consume slots, they do not add a second state store

---

## 4. Cross-run / resume

## Task D10: `agent` child goal projection

**Description:** Parent must not dump `notes` into the child. Project named slots (and/or a subset of parent `goal`) into the child jobs `payload` / Runtime `goal`. LLM never sees `{jobs_url}` or `activation_target`.

**Acceptance criteria:**
- [ ] Projection map documented (capability metadata or workflow stage field — pick the smaller catalogue change)
- [ ] Missing required child field → parent run fails closed; no child start
- [ ] Child `goal` JSON contains only projected keys
- [ ] Existing FR: `kind=agent` still POSTs API AFD jobs, not callee AR

**Verification:**
- [ ] Tests with fake AFD jobs client: child body == projection
- [ ] Manual: seed parent route in dummy-jobs (if one exists) or unit-only if seed has no parent yet

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
- [ ] On restart/resume, graph skips completed steps per checkpoint
- [ ] `goal` remains original ingress; slots reload from `working` if `working=session`
- [ ] Side-effect stages already done are not invoked again (test with a counting fake invoker)
- [ ] `loop=none` still fail-the-run on death

**Verification:**
- [ ] Tests: kill after stage 0 → resume starts at stage 1; invoker call count == remaining stages
- [ ] README Memory: resume-from-step is wired

**Dependencies:** Task D3; D2 must have kept D11 in scope

**Files likely touched:**
- `agent-runtime/app/core/execution.py`
- `agent-runtime/app/core/agent_core.py`
- `agent-runtime/app/core/memory.py`
- `README.md` Memory

**Estimated scope:** Medium

---

## 5. Packaging

## Task D12: README — goal vs slots vs notes

**Description:** Memory, Workflows, Retrieve, and dummy-jobs must describe the real assembly. No “designed, not in this Runtime” for items D3–D7 (and D8–D10 if done).

**Acceptance criteria:**
- [ ] Memory table: `working` blob includes `slots`; `notes` is the LLM projection
- [ ] Workflows: linear vs branch/gate matches what shipped
- [ ] Retrieve: prefetch pack vs retrieve tools vs `long_term` still distinct
- [ ] Dummy-jobs README: which proof route asserts a derived field
- [ ] [dataflow-plan.md](./dataflow-plan.md) present-vs-remaining table updated

**Verification:**
- [ ] Manual: a new session can answer “how does stage 2 get stage 1’s JSON?” from README + this plan

**Dependencies:** D5; D7/D8/D10 if those phases shipped in the same slice

**Files likely touched:**
- `README.md`
- `docs/run/dummy-jobs/README.md`
- `docs/tasks/dataflow-plan.md`

**Estimated scope:** Small

---

## Task D13: Verification checklist (break the mock)

**Description:** Examiner path: break the derived field, watch the proof fail; restore, watch it pass. Same spirit as eval E13.

**Acceptance criteria:**
- [ ] Short checklist at the end of [dataflow-plan.md](./dataflow-plan.md) or `docs/dataflow/README.md`: commands to run D5 (and D7 if shipped)
- [ ] Explicit “`completed` on dummy `--all` is not sufficient”
- [ ] Lists what is still catalogue-only (`conversation`, `long_term`, and any skipped D8–D11)

**Verification:**
- [ ] Manual: follow the checklist once on a clean compose

**Dependencies:** Task D12

**Files likely touched:**
- `docs/tasks/dataflow-plan.md` or `docs/dataflow/README.md`

**Estimated scope:** Small

---

## Checkpoint: Track complete (for the phases you chose)

- [ ] D1–D2 always
- [ ] D3–D5 if you wanted HTTP handoff
- [ ] D6–D7 if you wanted prefetch
- [ ] D8–D11 only as D2 scoped
- [ ] Human review before treating dummy jobs as dataflow-complete
