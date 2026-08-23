# Task list: Agent evals (local Fabric)

Plan: [eval-plan.md](./eval-plan.md). Docs map: [docs/README.md](../README.md). Architecture: [agent-plane](../04-architecture/agent-plane.md), [Agent evals box](../04-architecture/narrative/enterprise-agent-fabric.mdx).

**Execution order (the architecture’s three slices):**

1. **Routing** (do this first) — E1–E6. Chat is the contest. Jobs are a thinner suite under this slice, not their own slice.
2. **Pin and hydrate** — E7–E8. Catalogue lint + dummy `--all` fail-closed.
3. **Route quality** (later) — E14 only. `eval_suite_id` lives here.

E9–E13 package how you run slices 1–2. They are not a fourth eval slice.

v1 fabric tasks remain in [todo.md](./todo.md); observability remains in [observability-todo.md](./observability-todo.md); intent router remains in [intent-todo.md](./intent-todo.md); stage data sharing remains in [dataflow-todo.md](./dataflow-todo.md). This list does not replace them. Routing cases (E1–E6) are the gate for intent I8+ (retrieve / LLM fallback).

---

## 0. Foundation

## Task E1: Eval fixture schema and `agent-data-plane/src/test/resources/eval/` layout

**Description:** Freeze the case file format. Document that evals are CI/platform, not decide/start/loop, and that the routing golden set is the **board** (not `eval_suite_id` / not `fee_explain_golden`).

**Acceptance criteria:**
- [x] `agent-data-plane/src/test/resources/eval/README.md` states: off hot path; routing suite sits next to the catalogue mix; `eval_suite_id` is slice 3 only; no utterance in metrics
- [x] JSON schema (or a checked example + field table) for a case: `id`, `ingress`, `channel`, `message` xor `route_id`, `claims`, `expected.outcome`, `expected.route_id` (when outcome is `route`)
- [x] Golden file header includes `catalogue` (list of `route_id` @ `route_version` the labels assume)
- [x] Pack decide fixtures remain the contract examples; eval cases live under `agent-data-plane/src/test/resources/eval/`, not `docs/`

**Verification:**
- [ ] Manual: a new session can author a case by copying one example
- [ ] Header field table matches [decide-chat-request.json](../05-reference/decide-chat-request.json) / [decide-jobs-route.json](../05-reference/decide-jobs-route.json)

**Dependencies:** None

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/README.md`
- `agent-data-plane/src/test/resources/eval/case.schema.json`
- `agent-data-plane/src/test/resources/eval/example-chat-route.json`

**Estimated scope:** Small

---

## 1. Routing (do this first)

This is the only eval the architecture requires. Cases are `(utterance, claims, channel) → expected outcome`. Expected is `route:fee_explain`, `clarify`, or `abstain` — not a memo.

Jobs skip classify, so they are a **thinner suite under this slice**: named `route_id` + claims → entitled `route` or fail-closed. Chat is the real contest.

A misroute in production becomes a new case. CI replays the whole active eligible set. Release does not ship if “Why was I charged $42?” starts `card_freeze`.

`eval_suite_id` on a route is the wrong key for this. Hold the routing golden set next to the catalogue version (or a product + cut), not as `fee_explain_golden`.

---

## Task E2: Chat routing golden set

**Description:** Encode labelled chat utterances for the catalogue seed, starting from today’s DecideService cases and adding enough contestants that a keyword steal is visible.

**Acceptance criteria:**
- [x] `agent-data-plane/src/test/resources/eval/routing-golden.json` includes at least: fee utterance → `route:fee_explain`; close match → `clarify`; empty eligible / wrong channel → `abstain`
- [ ] ≥15 additional chat cases across seed intents (policy, legal, fraud, chat hello) with claims that match seed `required_claims`
- [ ] File header lists the labelled active mix (the board), not an `eval_suite_id`
- [ ] No expected prose / output schema / memo text

**Verification:**
- [ ] Manual: every `expected.route_id` exists in the catalogue seed
- [ ] Cases are unique `id`s

**Dependencies:** Task E1

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/routing-golden.json`

**Estimated scope:** Medium

---

## Task E3: Parameterized Data Plane tests load the chat golden set

**Description:** One JUnit suite reads `routing-golden.json` and calls `DecideService` against the in-memory catalogue seed. Existing one-off decide tests may stay as smoke; they must not contradict the golden set.

**Acceptance criteria:**
- [ ] Each golden case is a test invocation (parameterized)
- [ ] Assert `outcome` and, when `route`, `route_id` (and `route_version` if the fixture sets it)
- [ ] In-memory store used by the suite matches seed route ids (same names as Flyway seed)
- [ ] `mvn test` in Data Plane is the routing gate; no Compose required

**Verification:**
- [ ] `cd agent-data-plane && mvn test -Dtest=RoutingEval*` passes on current seed
- [ ] Flip one expected `route_id` in JSON → that test fails

**Dependencies:** Task E2

**Files likely touched:**
- `agent-data-plane/src/test/java/**/RoutingEval*`
- `agent-data-plane/src/test/resources/eval/`
- Possibly `InMemoryRouteStore` if the demo seed is thinner than the catalogue seed

**Estimated scope:** Medium

---

## Task E4: Adversarial / safety routing cases

**Description:** Cases that must never start a high-risk write from a read/explain utterance. A demo or production misroute is added here and stays until the classifier or catalogue is fixed.

**Acceptance criteria:**
- [ ] Fee / “charged $42” style utterances do not `route` to `card_freeze`, `account_notify`, or `kyc_onboarding`
- [ ] Same fee utterance without `accounts:read` → `abstain` (not a different route)
- [ ] At least one jobs-looking phrase in **chat** still classifies (does not bind `route_id` from the message text)
- [ ] Cases live in the same routing golden file (tag `adversarial` is fine)

**Verification:**
- [ ] E3 runner picks them up; `mvn test -Dtest=RoutingEval*` covers the new ids
- [ ] “Why was I charged $42?” starting `card_freeze` fails the suite

**Dependencies:** Task E3

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/routing-golden.json`

**Estimated scope:** Small

---

## Task E5: Jobs entitle golden set (thinner suite)

**Description:** Jobs skip classify. Label named `route_id` + claims only. Positive rows from [dummy-request/job/jobs.json](../run/dummy-request/job/jobs.json); negatives omit the required claim.

**Acceptance criteria:**
- [ ] `agent-data-plane/src/test/resources/eval/jobs-entitle-golden.json` covers every dummy-request `route_id` with its seed claims → `route`
- [ ] Each of those has a sibling case with empty/wrong claims → `abstain`
- [ ] Unknown `route_id` → `abstain` (or documented deny)
- [ ] `ingress` is `jobs`; `message` is null; no `clarify` expected

**Verification:**
- [ ] Dummy-jobs route ids ⊆ golden positives
- [ ] Claims match catalogue seed `required_claims`

**Dependencies:** Task E1

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/jobs-entitle-golden.json`

**Estimated scope:** Small

---

## Task E6: Parameterized tests for jobs entitle

**Description:** Load the jobs golden set into Data Plane tests. Layer ② / ③ must not run; bind is the named `route_id` plus entitle.

**Acceptance criteria:**
- [ ] Each jobs case is a test invocation
- [ ] Hidden routes (`chat_visible=false`) entitle when claimed
- [ ] `confidence` on successful bind stays 1.0 (today’s Layer ① behaviour) or the fixture documents otherwise
- [ ] Caller `X-Workload` remains `afd` (AR must still be forbidden — existing test)

**Verification:**
- [ ] `mvn test -Dtest=JobsEntitleEval*` passes
- [ ] Remove `claims:read` from `claims_adjudicate` positive → fail

**Dependencies:** Task E5

**Files likely touched:**
- `agent-data-plane/src/test/java/**/JobsEntitleEval*`
- `agent-data-plane/src/test/resources/eval/`

**Estimated scope:** Small

---

## Checkpoint: 1. Routing

- [ ] E1–E6 done
- [ ] Chat contest labelled; jobs entitle is the thinner suite
- [ ] Fee utterance cannot silently become a freeze
- [ ] Routing golden set is not stored as `eval_suite_id`
- [ ] Human review before pin lint

---

## 2. Pin and hydrate

For each active route: pointers resolve, manifest refs are published, retrieval scope ids exist, Pattern 0 has no tools/workflow, high-risk routes still have a workflow. Catalogue lint; dummy `--all` is the smoke seed — fail-closed and pinned to the route version.

---

## Task E7: Catalogue pin lint

**Description:** Static checks over the in-memory (and/or JDBC test) catalogue seed so a route that cannot hydrate cannot sit Active.

**Acceptance criteria:**
- [ ] For every active route: `prompt_id` / `workflow_id` / `tool_manifest` either empty in the allowed way for that `autonomy_mode`, or resolvable to a seeded artefact
- [ ] Pattern 0: no tools, no workflow, no retrieve tool, no retrieval prefetch required (match glossary)
- [ ] Pattern 2: workflow present; high-risk write routes (`card_freeze`, `account_notify`, `kyc_onboarding`) still have a workflow
- [ ] Manifest refs (when present) are published capability ids known to the test seed
- [ ] `retrieval.scope` ids are known corpora when retrieval is set
- [ ] Lint does not call Runtime or an LLM

**Verification:**
- [ ] `mvn test -Dtest=CataloguePinLint*` passes on current seed
- [ ] Temporarily set Pattern 0 `tool_manifest` in the in-memory store → lint fails

**Dependencies:** None (can start after E1; needs catalogue seed in tests). Do not start before slice 1 is the agreed first gate.

**Files likely touched:**
- `agent-data-plane/src/test/java/**/CataloguePinLint*`
- Optionally a small `application` helper if lint is reused later

**Estimated scope:** Medium

---

## Task E8: Dummy `--all` fail-closed smoke

**Description:** Turn [run-job.sh --all](../run/dummy-request/run-job.sh) into the Compose half of slice 2: every dummy job must complete (or fail controlled) at the pinned route version. Not the routing golden set.

**Acceptance criteria:**
- [ ] Documented command: `./docs/run/dummy-request/run-job.sh --all` with `WAIT=1` (or equivalent) exits non-zero on hydrate/start/loop failure
- [ ] Smoke is pinned to the route versions in the catalogue seed (header or script comment lists them)
- [ ] Default `run-eval.sh` (E9) still runs the **lint** without Compose; `--all` is the Compose confirmation
- [ ] README/eval README: `--all` is pin/hydrate smoke, not routing labels

**Verification:**
- [ ] Manual on a running stack: `--all` passes on current seed
- [ ] Break a manifest pointer on one jobs route → `--all` fails

**Dependencies:** Task E7

**Files likely touched:**
- `docs/run/dummy-request/run-job.sh` (fail-closed / WAIT default for eval)
- `agent-data-plane/run-eval.sh`
- `agent-data-plane/src/test/resources/eval/README.md`

**Estimated scope:** Small

---

## Checkpoint: 2. Pin and hydrate

- [ ] E7 done; E8 fail-closed `--all` documented and proven once on Compose
- [ ] Catalogue seed is lint-clean
- [ ] Human review before treating slices 1–2 as the ship gate

---

## Gate packaging (how you run 1 + 2)

Not a fourth eval slice.

---

## Task E9: Local eval gate script

**Description:** One command that runs the in-process eval tests so operators do not have to remember Maven class names.

**Acceptance criteria:**
- [ ] `agent-data-plane/run-eval.sh` runs Routing (chat + jobs entitle) and Pin lint test classes
- [ ] Non-zero exit on any failure
- [ ] Help text points at `agent-data-plane/src/test/resources/eval/README.md` and this task list; mentions `--all` as slice 2 Compose smoke
- [ ] Does not require Grafana or an LLM

**Verification:**
- [ ] `./agent-data-plane/run-eval.sh` exits 0 on current main
- [ ] Break a golden expected `route_id` → non-zero

**Dependencies:** Task E3, Task E6, Task E7

**Files likely touched:**
- `agent-data-plane/run-eval.sh`

**Estimated scope:** Small

---

## Task E10: Incident-to-case playbook

**Description:** A misroute becomes a golden row. The gate stays red until the catalogue or classifier is fixed.

**Acceptance criteria:**
- [ ] A section in `agent-data-plane/src/test/resources/eval/README.md` lists: capture utterance + claims + actual outcome; add case; run `run-eval.sh`; do not “fix” by deleting the case
- [ ] States jobs vs chat (jobs are entitle, not classify)
- [ ] Links examiner questions from the plan

**Verification:**
- [ ] Manual: steps are followable without this chat
- [ ] Does not tell the operator to call decide from a browser as the gate

**Dependencies:** Task E9

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/README.md`

**Estimated scope:** Small

---

## Task E11: Glossary / Control Plane honesty for `eval_suite_id`

**Description:** `eval_suite_id` is slice 3 (per-route quality). It is not the routing golden set.

**Acceptance criteria:**
- [ ] Glossary Eval suite text still says not used on the hot path; add that the CI routing golden set is the board, not this pointer
- [ ] Empty `eval_suite_id` on a route is not an error in the UI (correct for `agent-chat`)
- [ ] Do not add a fake “eval passed” badge

**Verification:**
- [ ] Control Plane glossary copy reviewed against [index.html](../../agent-control-plane/public/index.html) glossary Eval suite row
- [ ] No new Control Plane API

**Dependencies:** None (docs/UI copy only)

**Files likely touched:**
- `agent-control-plane/public/index.html`
- Possibly `agent-control-plane/public/app.js` if empty-state copy needs a word

**Estimated scope:** Small

---

## Task E12: README eval notes

**Description:** Root README points at the eval plan/todo and how to run the local gate.

**Acceptance criteria:**
- [ ] README links [eval-plan.md](./eval-plan.md) and [eval-todo.md](./eval-todo.md)
- [ ] Routing command: `./agent-data-plane/run-eval.sh`
- [ ] Pin/hydrate smoke: dummy-request `--all` (fail-closed)
- [ ] Explicit: not on the hot path; `--all` is not the routing golden set

**Verification:**
- [ ] Manual: a new session can find and run slice 1 from README
- [ ] Docs table / See also does not claim evals are implemented until E9 exists

**Dependencies:** Task E9

**Files likely touched:**
- `README.md`
- `agent-data-plane/src/test/resources/eval/README.md`

**Estimated scope:** Small

---

## Task E13: Verification checklist (break a label)

**Description:** Prove the routing gate is a gate: change one expected outcome, watch failure, restore.

**Acceptance criteria:**
- [ ] Checklist: (1) flip `fee_explain` expected route (2) `run-eval.sh` fails (3) restore (4) passes
- [ ] Confirms no decide/start/loop code path was added for eval
- [ ] Confirms fixtures contain no secrets

**Verification:**
- [ ] Run the checklist once; all boxes pass
- [ ] Human sign-off

**Dependencies:** Task E9, Task E10

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/README.md`

**Estimated scope:** Small

---

## Checkpoint: slices 1–2 complete

- [ ] E1–E13 done
- [ ] Local command gates routing; `--all` is pin/hydrate smoke
- [ ] Out of scope still out (LLM-as-judge, output schemas, hot-path eval, route_tables)
- [ ] Human review before slice 3

---

## 3. Route quality (later, and only where it pays)

This is what `eval_suite_id` is for: fixtures for **that** route after start. Keep them boring.

- Deterministic / jobs: same payload → expected tool sequence, not expected prose. `card_freeze` must call identity → limit → freeze, not a chatty “I froze it.”
- Grounded Q&A: citation from the scoped corpus, or abstain. No LLM-as-judge yet.
- Free-form routes (`agent-chat`): skip. Empty `eval_suite_id` means “no quality suite,” which is correct.

Do not wait on `output_schema_id`. Structured output is a later contract for jobs that must return JSON. Eval can assert tools, citations, and decide outcomes while the reply is still `{ "message": "…" }`.

---

## Task E14: Deterministic tool-sequence suite

**Description:** First real `eval_suite_id`. Pattern 2 jobs route `card_freeze`: expected stage/tool order identity_check → limit_check → freeze_card. No LLM-as-judge. No `output_schema_id`. Grounded Q&A suites are out of this task (next increment after E14 if needed).

**Acceptance criteria:**
- [ ] Fixture lists expected stage/tool order from the seeded workflow
- [ ] Test hydrates from test doubles or asserts workflow JSON — does not require a live model
- [ ] Free-form routes remain without a suite (`eval_suite_id` empty)
- [ ] Routing gate (E1–E13) must not depend on E14
- [ ] Seed `eval_suite_id` only if this suite id is real

**Verification:**
- [ ] Reorder a workflow stage in the test double → suite fails
- [ ] `run-eval.sh` either skips E14 by default or has `--quality`

**Dependencies:** Checkpoint slices 1–2 complete

**Files likely touched:**
- `agent-data-plane/src/test/resources/eval/route-quality/card_freeze.json`
- `agent-runtime` or `agent-data-plane` tests (workflow order)
- Catalogue seed `eval_suite_id` on `card_freeze` only if the id resolves

**Estimated scope:** Medium
