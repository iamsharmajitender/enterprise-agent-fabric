# Task list: Layered intent router (local Fabric)

Plan: [intent-plan.md](./intent-plan.md) (includes **Present vs remaining**). Playbook: [Layered classifier](https://jitendersharma.dev/playbooks/agents/intent-router/layered-classifier). Docs map: [README.md](../README.md). Architecture: [agent-plane](../04-architecture/agent-plane.mdx).

**Execution order:**

1. **Pipeline** — I1–I3. Eligible → ① → ② → ③-noop. `router_layer`. Stickiness split documented.
2. **Layer ①** — I4–I6. Slash/command; jobs stay ①-only; topic map only if the contract has `topic`.
3. **Layer ②** — I7–I9. Risk bands, then retrieve, then budget.
4. **Layer ③** — I10–I12. Later, rare, default off.
5. **Packaging** — I13–I14.

Routing golden set ([eval-todo.md](./eval-todo.md) E1–E6) is the gate for I8+. I1–I7 may use existing `DecideServiceTest` if eval is not landed.

v1 fabric tasks remain in [todo.md](./todo.md); observability remains in [observability-todo.md](./observability-todo.md); evals remain in [eval-todo.md](./eval-todo.md); stage data sharing remains in [dataflow-todo.md](./dataflow-todo.md). This list does not replace them.

---

## 0. Pipeline

## Task I1: Split decide into eligible → ① → ② → ③-noop → abstain

**Description:** Refactor `DecideService` so the v1 behaviour is an explicit pipeline: eligible (or jobs entitle), then bind-if-named, then keyword retrieve, then a no-op Layer ③, then `abstain`. Jobs / named `route_id` must not enter ②. No behaviour change for existing tests.

**Acceptance criteria:**
- [x] Chat path: empty eligible → `abstain` before ②
- [x] Chat with `route_id` (hint / clarify pick) binds from eligible only; unknown id → `abstain`; does not keyword-match
- [x] Jobs with `route_id` entitle by claims only; never call keyword retrieve; never return `clarify`
- [x] Free-text chat still keyword-retrieves over eligible only

**Verification:**
- [x] Tests pass: `cd agent-data-plane && mvn test -Dtest=DecideServiceTest`
- [x] Manual: read `DecideService` — ② is unreachable when `hasRouteId()` on jobs

**Dependencies:** None

**Files likely touched:**
- `agent-data-plane/src/main/java/com/fabric/adp/application/DecideService.java`
- `agent-data-plane/src/test/java/com/fabric/adp/application/DecideServiceTest.java`

**Estimated scope:** Small

---

## Task I2: `router_layer` + `latency_ms` on decide result and events

**Description:** Operators need to see which cheap layer assigned the outcome. Add `router_layer` (`rules` | `retrieve` | `llm`) and `latency_ms` on `DecideResult`, the decide HTTP JSON (AFD-facing), and decide business events. Chat assistant JSON must still omit them (FR-5). No Layer ③ calls yet — `llm` unused.

**Acceptance criteria:**
- [x] Bind / jobs named `route_id` → `router_layer=rules`
- [x] Keyword unique winner / tie clarify / keyword miss abstain after a contest → `router_layer=retrieve` (abstain from empty eligible may omit layer or use a documented value; pick one and test it)
- [x] `latency_ms` is set on every decide
- [x] Existing AFD FR-5 tests still fail if assistant JSON contains `router_layer`

**Verification:**
- [x] Tests pass: DecideServiceTest asserts `router_layer` on route / clarify / jobs
- [x] Tests pass: `AssistantControllerTest` (or equivalent) still forbids `router_layer` on chat JSON

**Dependencies:** Task I1

**Files likely touched:**
- `agent-data-plane/src/main/java/com/fabric/adp/domain/DecideResult.java`
- `agent-data-plane/src/main/java/com/fabric/adp/adapters/in/http/DecideController.java`
- `agent-data-plane/src/main/java/com/fabric/adp/application/DecideService.java`
- `agent-front-door` FR-5 tests (read-only unless a leak appears)

**Estimated scope:** Small

---

## Task I3: Document AFD freeze vs decide ① (stickiness split)

**Description:** Playbook ① includes session stickiness (`"yes"` / `"$500"` stay on the pin, then safety). This fabric already skips decide on a live Front Door freeze. Record that split so I4–I12 do not re-read freeze inside ADP.

**Acceptance criteria:**
- [x] [intent-plan.md](./intent-plan.md) stickiness row stays the source; ADP README (or I13) states: live `session_id` with `correlation_id` does not call decide
- [x] No ADP code reads `frontdoor.freeze`
- [x] Decide-side continuation re-entitle is explicitly **out** until a seed case needs it

**Verification:**
- [x] Manual: AssistantService still resumes from freeze without decide (existing tests)
- [x] Manual: plan/todo do not schedule “copy freeze into DecideService”

**Dependencies:** None (can land with I1)

**Files likely touched:**
- `agent-data-plane/README.md` (short note; full handbook pass is I13)
- `agent-fabric-docs/tasks/intent-plan.md` (already states the split; tighten if needed)

**Estimated scope:** Small

---

## Checkpoint: Pipeline

- [x] I1–I3 acceptance criteria met
- [x] Existing route / clarify / abstain / jobs tests pass
- [ ] Human review before slash rules

---

## 1. Layer ① rules

## Task I4: Slash / command rules (catalogue, first match, eligible only)

**Description:** Deterministic ①: commands such as `/hr` or “talk to a human” assign a `route_id` already in the eligible set and skip ②/③. Rules are data (seed / table), not `if (message.equals("…"))` in `DecideService`. First match wins. Matched id not eligible → `abstain`.

**Acceptance criteria:**
- [x] At least one seeded command routes with `router_layer=rules` and does not require keywords
- [x] Command whose `route_id` is not in eligible → `abstain` (no keyword fall-through)
- [x] Free-text that is not a command still uses ②
- [x] Jobs path unchanged (does not parse chat slash from a jobs body)

**Verification:**
- [x] Tests pass: new DecideService cases for match / not-eligible / non-command
- [x] Manual: catalogue seed includes the command → route mapping

**Dependencies:** Task I1, Task I2

**Files likely touched:**
- `agent-data-plane` Flyway seed / `InMemoryRouteStore`
- `agent-data-plane/src/main/java/com/fabric/adp/application/DecideService.java`
- `agent-data-plane/src/test/java/com/fabric/adp/application/DecideServiceTest.java`

**Estimated scope:** Medium

---

## Task I5: Jobs / named `route_id` stay ①-only

**Description:** Lock the playbook rule: a payload that already named `route_id` must not run ② or ③ and must not return `clarify`. Missing claims / unknown route → `abstain` (AFD maps jobs to fail closed).

**Acceptance criteria:**
- [x] Jobs + entitled `route_id` → `route`, `router_layer=rules`, confidence 1.0 (or documented bind confidence)
- [x] Jobs + hidden route with claims still entitles (existing `claims_adjudicate` behaviour)
- [x] Jobs + missing claims → `abstain`; no `clarify`
- [x] Chat hint/clarify `route_id` also `router_layer=rules` when bind succeeds

**Verification:**
- [x] Tests pass: DecideServiceTest jobs cases; add `router_layer` assertions
- [x] Tests pass: Front Door jobs still 403 on decide abstain (existing JobsServiceTest)

**Dependencies:** Task I2

**Files likely touched:**
- `agent-data-plane/src/test/java/com/fabric/adp/application/DecideServiceTest.java`
- `agent-front-door` jobs tests only if behaviour drifts

**Estimated scope:** Small

---

## Task I6: Topic / event map (skip if no `topic` on the contract)

**Skipped.** Jobs decide body has no `topic` (`DecideRequest` / [decide-jobs-route.json](../05-reference/decide-jobs-route.json)). Do not invent Kafka. Reopen when the contract grows a `topic` field.

**Acceptance criteria:**
- [ ] Either: `topic` on decide request + rule row → bind eligible `route_id`, `router_layer=rules`, skip ②/③, never `clarify`
- [x] Or: task explicitly skipped; jobs contract unchanged
- [x] Missing claims still empty entitled set → `abstain`

**Verification:**
- [ ] If implemented: DecideServiceTest for topic match / missing claim
- [x] If skipped: this checkbox list marked skipped, no schema change

**Dependencies:** Task I4 (rule store). Skip allowed.

**Files likely touched:**
- `agent-fabric-docs/05-reference/` jobs decide fixture (only if implemented)
- `agent-data-plane` decide request + rules seed

**Estimated scope:** Medium (or skipped)

---

## Checkpoint: Layer ①

- [x] I4–I5 met; I6 met or skipped
- [x] Commands skip keywords; jobs never `clarify`
- [ ] Human review before ② retrieve

---

## 2. Layer ② retrieve

## Task I7: Per-route risk bands on the current scorer

**Description:** Stop using a single hardcoded `0.91` / `0.6`. High-risk routes (writes / freeze / pay in the catalogue seed) need a higher bar or forced `clarify`. Mid-risk may clarify on a close top-2. Still allowed to use keywords. This is calibration, not a new model.

**Acceptance criteria:**
- [x] Route rows (or a small risk map) expose a risk class or threshold
- [x] Unique keyword hit on a high-risk route below the bar → `clarify` or `abstain`, not silent `route`
- [x] Fee explain seed path still `route`s the `$42` utterance
- [x] `router_layer` remains `retrieve`

**Verification:**
- [x] Tests pass: at least one high-risk vs fee case
- [x] Manual: thresholds documented in ADP README or seed comments
12211
**Dependencies:** Task I2. Prefer eval E4 adversarial cases if they exist.

**Files likely touched:**
- `agent-data-plane` route seed / `RouteRow`
- `DecideService` scoring
- `DecideServiceTest`

**Estimated scope:** Medium

---

## Task I8: Replace keywords with retrieve-over-eligible

**Description:** Playbook ②: small model / kNN on the golden set, most chat traffic, &lt; 50 ms. Index utterances and/or route descriptions — **not** a copy of `keywords[]`. Classify only over eligible ids. Outcomes unchanged. Pick one in-process stack in this task (no new microservice).

**Acceptance criteria:**
- [x] `keywordRetrieve` is gone from the hot path (keywords may remain on the row unused, or dropped in a later cleanup — do not keep two scorers)
- [x] Unique retrieve winner → `route`, `router_layer=retrieve`
- [x] Close top-2 → `clarify` with candidates from eligible only
- [x] OOD / low score → `abstain` (or hand to ③ only after I12 flag; default abstain)
- [x] Eval routing golden set (E2–E4) passes, or a local adversarial file that includes fee ≠ `card_freeze`

**Verification:**
- [x] Tests pass: `mvn test -Dtest=DecideServiceTest,RoutingEval*` (skip RoutingEval* if eval not landed; then a dedicated retrieve test file)
- [x] Manual: `$42` still `fee_explain`

**Dependencies:** Task I7; eval E2–E4 strongly preferred

**Files likely touched:**
- `agent-data-plane` new retrieve collaborator + tests
- `DecideService`
- optional embedding/index assets under `agent-data-plane/src/main/resources/`

**Estimated scope:** Large — keep the first landing to in-memory kNN over labelled seed utterances; do not add training pipelines

---

## Task I9: Layer ② budget — over budget does not call ③

**Description:** Architecture: ② &lt; 50 ms; do not enqueue behind ③. Record `latency_ms`. If retrieve exceeds the budget, return `clarify` or `abstain` with `router_layer=retrieve`. Do not invoke Layer ③ to “finish” a slow ②.

**Acceptance criteria:**
- [x] Budget constant documented (default 50 ms)
- [x] Forced slow retrieve in a test sheds without calling ③
- [x] `latency_ms` still present

**Verification:**
- [x] Unit test with a fake slow retriever
- [x] I10’s ③ port is not required; a no-op ③ that counts calls is enough

**Dependencies:** Task I8

**Files likely touched:**
- retrieve collaborator + DecideService
- tests

**Estimated scope:** Small

---

## Checkpoint: Layer ②

- [x] I7–I9 met
- [x] Fee ≠ `card_freeze`; jobs still ①-only
- [ ] Human review before Layer ③

---

## 3. Layer ③ LLM fallback (later, rare)

## Task I10: Layer ③ port, default off, eligible-ids-only

**Description:** Add a Layer ③ port whose input is the user message plus the **eligible `route_id` list** (and optional top-k from ②). Output is structured: `route_id` in that list, or clarify/abstain. Default **off**: decide never calls it. No live LLM required — a stub that throws if called is enough.

**Acceptance criteria:**
- [x] Flag / config default false
- [x] When off, checkpoint ② behaviour is unchanged
- [x] Port contract forbids ids outside eligible
- [x] Jobs / bind never call the port

**Verification:**
- [x] Tests pass: flag off; spy ③ never invoked on fee utterance or jobs
- [x] Compile: no hard dependency on a cloud LLM SDK required yet

**Dependencies:** Task I9

**Files likely touched:**
- `agent-data-plane` application port + config
- `DecideService`

**Estimated scope:** Small

---

## Task I11: Bounded executor + timeout → shed

**Description:** Architecture: Layer ③ on a separate pool; saturate → `clarify` / `abstain`; do not queue behind ②. Locally: bounded executor + hard timeout. On timeout or rejection, return `clarify` or `abstain` with `router_layer=llm` (or a documented shed value) and do not retry.

**Acceptance criteria:**
- [x] Timeout is configured and tested
- [x] A hung ③ does not block the decide thread beyond the deadline
- [x] Jobs / flag-off paths never submit to the pool

**Verification:**
- [x] Test: fake ③ sleeps past timeout → clarify or abstain
- [x] Test: flag off → pool unused

**Dependencies:** Task I10

**Files likely touched:**
- `DecideService` / Layer ③ adapter
- tests

**Estimated scope:** Medium

---

## Task I12: Structured JSON fallback when ② is maybe / high-risk

**Deferred → future enhancement.** Flag stays off (`fabric.decide.llm.enabled=false`). I10 port + I11 pool/timeout stay in place; decide never calls a live model.

**Canonical write-up (what it will offer, when to revive):** [future-enhancement.md — I12 Layer ③ LLM fallback](./future-enhancement.md#i12-layer-3-llm-fallback).

**Description:** Turn ③ **on** only for ② maybe-band or high-risk top candidate. Prompt (or stub) must return JSON choosing among eligible ids only. Ambiguous → `clarify` with top-k. Invalid id → `abstain`. Local demo keeps the flag off.

**Acceptance criteria:**
- [ ] Flag on: ② confident fee utterance still does **not** call ③
- [ ] Flag on: seeded maybe/high-risk case calls ③; result id ∈ eligible
- [ ] Invalid model id → `abstain`
- [ ] Timeout path from I11 still holds

**Verification:**
- [ ] Tests with a stub model (no network)
- [ ] Manual: default Compose / local config still flag off

**Dependencies:** Task I11, Task I7 (risk bands)

**Files likely touched:**
- Layer ③ stub adapter
- DecideService gating
- tests
- [future-enhancement.md](./future-enhancement.md#i12-layer-3-llm-fallback) (keep in sync when reopening)

**Estimated scope:** Medium

---

## Checkpoint: Layer ③

- [x] Flag off ≡ Layer ② checkpoint
- [x] Flag on + timeout does not hang
- [x] Jobs / bind never call ③
- [ ] Human review; ④ safety is a **new** plan, not I15

---

## Packaging

## Task I13: ADP handbook + root README intent notes

**Description:** Point operators at the pipeline, present vs remaining, and that chat JSON still hides `router_layer`. Do not duplicate the playbook.

**Acceptance criteria:**
- [x] `agent-data-plane/README.md` describes eligible → ① → ② → ③-off, jobs ①-only
- [x] Root README Docs list links [intent-plan.md](./intent-plan.md) / [intent-todo.md](./intent-todo.md)
- [x] FR-5 reminder: assistant JSON still slim

**Verification:**
- [x] Manual: links resolve
- [x] Manual: README matches actual flag default (③ off)

**Dependencies:** Task I2; I8 if retrieve already landed (describe what is actually running)

**Files likely touched:**
- `agent-data-plane/README.md`
- `README.md`

**Estimated scope:** Small

---

## Task I14: Verification checklist

**Description:** A short operator checklist: command ①, fee retrieve ②, ③ off, jobs entitle/fail-closed, FR-5, golden set if present.

**Acceptance criteria:**
- [x] Checklist lives in [intent-plan.md](./intent-plan.md) demo path or `agent-fabric-scripts/docker-compose/ or agent-fabric-scripts/stack/` — one place
- [x] Includes: `/hr` (or seeded command) → rules; `$42` → `fee_explain` retrieve; jobs missing claims fail closed; assistant JSON has no `router_layer`

**Verification:**
- [x] Manual: walk the checklist against a running stack or unit tests as documented

**Dependencies:** Task I4, Task I8 (or keyword ② if I8 not yet done — checklist must say which)

**Files likely touched:**
- `agent-fabric-docs/tasks/intent-plan.md` demo path

**Estimated scope:** Small

---

## Checkpoint: Complete

- [x] I1–I9 and I13–I14 met
- [x] I6 skipped; I10–I11 met; I12 explicitly deferred (flag off)
- [x] Eval routing gate still the misroute CI (not decide hot path)
- [ ] Human review before a Layer ④ safety plan
