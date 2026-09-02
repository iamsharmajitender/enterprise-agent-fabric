# Task list: Agent evals (local Fabric)

Plan: [eval-plan.md](./eval-plan.md). Docs map: [README.md](../README.md). Architecture: [agent-plane](../04-architecture/agent-fabric-plane.mdx), [Agent evals box](../04-architecture/enterprise-agent-fabric-architecture.mdx).

**Execution order (the architecture’s three slices):**

1. **Routing** (do this first) — E1–E6. Chat is the contest. Jobs are a thinner suite under this slice, not their own slice.
2. **Pin and hydrate** — E7–E8. Catalogue lint + dummy `--all` fail-closed.
3. **Route quality** — E14. `eval_suite_id` lives here (`*_tools` suites).

E9–E13 package how you run slices 1–2. They are not a fourth eval slice.

v1 fabric tasks remain in [todo.md](./todo.md); observability remains in [observability-todo.md](./observability-todo.md); intent router remains in [intent-todo.md](./intent-todo.md); stage data sharing remains in [dataflow-todo.md](./dataflow-todo.md). This list does not replace them. Routing cases (E1–E6) are the gate for intent I8+ (retrieve / LLM fallback).

---

## 0. Foundation

## Task E1: Eval fixture schema and `agent-fabric-evals/intent-router-evals/` layout

**Description:** Freeze the case file format. Document that evals are CI/platform, not decide/start/loop, and that the routing golden set is the **board** (not `eval_suite_id` / not `fee_explain_golden`).

**Acceptance criteria:**
- [x] `agent-fabric-evals/intent-router-evals/README.md` states: off hot path; routing suite sits next to the catalogue mix; `eval_suite_id` is slice 3 only; no utterance in metrics
- [x] JSON schema (or a checked example + field table) for a case: `id`, `ingress`, `channel`, `message` xor `route_id`, `claims`, `expected.outcome`, `expected.route_id` (when outcome is `route`)
- [x] Golden file header includes `catalogue` (list of `route_id` @ `route_version` the labels assume)
- [x] Pack decide fixtures remain the contract examples; eval cases live under `agent-fabric-evals/`, not `docs/`

**Verification:**
- [x] Manual: a new session can author a case by copying one example
- [x] Header field table matches [decide-chat-request.json](../05-reference/decide-chat-request.json) / [decide-jobs-route.json](../05-reference/decide-jobs-route.json)

**Dependencies:** None

**Files likely touched:**
- `agent-fabric-evals/intent-router-evals/README.md`
- `agent-fabric-evals/intent-router-evals/schemas/case.schema.json`
- `agent-fabric-evals/intent-router-evals/schemas/example-chat-route.json`

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
- [x] `agent-fabric-evals/intent-router-evals/routing/<version>/cases/*.json` includes at least: fee utterance → `route:fee_explain`; close match → `clarify`; empty eligible / wrong channel → `abstain`
- [x] ≥15 additional chat cases across seed intents (policy, legal, fraud, chat hello) with claims that match seed `required_claims`
- [x] File header lists the labelled active mix (the board), not an `eval_suite_id`
- [x] No expected prose / output schema / memo text

**Verification:**
- [x] Manual: every `expected.route_id` exists in the catalogue seed
- [x] Cases are unique `id`s

**Dependencies:** Task E1

**Files likely touched:**
- `agent-fabric-evals/intent-router-evals/routing/<version>/cases/*.json`

**Estimated scope:** Medium

---

## Task E3: Parameterized Data Plane tests load the chat golden set

**Description:** One JUnit suite reads `routing-golden.json` and calls `DecideService` against the in-memory catalogue seed. Existing one-off decide tests may stay as smoke; they must not contradict the golden set.

**Acceptance criteria:**
- [x] Each golden case is a test invocation (parameterized)
- [x] Assert `outcome` and, when `route`, `route_id` (and `route_version` if the fixture sets it)
- [x] In-memory store used by the suite matches seed route ids (same names as Flyway seed)
- [x] `mvn test` in Data Plane is the routing gate; no Compose required

**Verification:**
- [x] `cd agent-data-plane && mvn test -Dtest=RoutingEval*` passes on current seed
- [x] Flip one expected `route_id` in JSON → that test fails

**Dependencies:** Task E2

**Files likely touched:**
- `agent-data-plane/src/test/java/**/RoutingEval*`
- `agent-fabric-evals/`
- Possibly `InMemoryRouteStore` if the demo seed is thinner than the catalogue seed

**Estimated scope:** Medium

---

## Task E4: Adversarial / safety routing cases

**Description:** Cases that must never start a high-risk write from a read/explain utterance. A demo or production misroute is added here and stays until the classifier or catalogue is fixed.

**Acceptance criteria:**
- [x] Fee / “charged $42” style utterances do not `route` to `card_freeze`, `account_notify`, or `kyc_onboarding`
- [x] Same fee utterance without `accounts:read` → `abstain` (not a different route)
- [x] At least one jobs-looking phrase in **chat** still classifies (does not bind `route_id` from the message text)
- [x] Cases live in the same routing golden file (tag `adversarial` is fine)

**Verification:**
- [x] E3 runner picks them up; `mvn test -Dtest=RoutingEval*` covers the new ids
- [x] “Why was I charged $42?” starting `card_freeze` fails the suite

**Dependencies:** Task E3

**Files likely touched:**
- `agent-fabric-evals/intent-router-evals/routing/<version>/cases/*.json`

**Estimated scope:** Small

---

## Task E5: Jobs entitle golden set (thinner suite)

**Description:** Jobs skip classify. Label named `route_id` + claims only. Positive rows from [chats.json](../../agent-fabric-scratchpad/catalog/chats.json); negatives omit the required claim.

**Acceptance criteria:**
- [x] `agent-fabric-evals/intent-router-evals/jobs-entitle/<version>/cases/*.json` covers every dummy-request `route_id` with its seed claims → `route`
- [x] Each of those has a sibling case with empty/wrong claims → `abstain`
- [x] Unknown `route_id` → `abstain` (or documented deny)
- [x] `ingress` is `jobs`; `message` is null; no `clarify` expected

**Verification:**
- [x] Dummy-jobs route ids ⊆ golden positives
- [x] Claims match catalogue seed `required_claims`

**Dependencies:** Task E1

**Files likely touched:**
- `agent-fabric-evals/intent-router-evals/jobs-entitle/<version>/cases/*.json`

**Estimated scope:** Small

---

## Task E6: Parameterized tests for jobs entitle

**Description:** Load the jobs golden set into Data Plane tests. Layer ② / ③ must not run; bind is the named `route_id` plus entitle.

**Acceptance criteria:**
- [x] Each jobs case is a test invocation
- [x] Hidden routes (`chat_visible=false`) entitle when claimed
- [x] `confidence` on successful bind stays 1.0 (today’s Layer ① behaviour) or the fixture documents otherwise
- [x] Caller `X-Workload` remains `afd` (AR must still be forbidden — existing test)

**Verification:**
- [x] `mvn test -Dtest=JobsEntitleEval*` passes
- [x] Remove `claims:read` from `claims_adjudicate` positive → fail

**Dependencies:** Task E5

**Files likely touched:**
- `agent-data-plane/src/test/java/**/JobsEntitleEval*`
- `agent-fabric-evals/`

**Estimated scope:** Small

---

## Checkpoint: 1. Routing

- [x] E1–E6 done
- [x] Chat contest labelled; jobs entitle is the thinner suite
- [x] Fee utterance cannot silently become a freeze
- [x] Routing golden set is not stored as `eval_suite_id`
- [x] Human review before pin lint

---

## 2. Pin and hydrate

For each active route: pointers resolve, manifest refs are published, retrieval scope ids exist, Pattern 0 has no tools/workflow, high-risk routes still have a workflow. Catalogue lint; dummy `--all` is the smoke seed — fail-closed and pinned to the route version.

---

## Task E7: Catalogue pin lint

**Description:** Static checks over the in-memory (and/or JDBC test) catalogue seed so a route that cannot hydrate cannot sit Active.

**Acceptance criteria:**
- [x] For every active route: `prompt_id` / `workflow_id` / `tool_manifest` either empty in the allowed way for that `autonomy_mode`, or resolvable to a seeded artefact
- [x] Pattern 0: no tools, no workflow, no retrieve tool, no retrieval prefetch required (match glossary)
- [x] Pattern 2: workflow present; high-risk write routes (`card_freeze`, `account_notify`, `kyc_onboarding`) still have a workflow
- [x] Manifest refs (when present) are published capability ids known to the test seed
- [x] `retrieval.scope` ids are known corpora when retrieval is set
- [x] Lint does not call Runtime or an LLM

**Verification:**
- [x] `mvn test -Dtest=CataloguePinLint*` passes on current seed
- [x] Temporarily set Pattern 0 `tool_manifest` in the in-memory store → lint fails

**Dependencies:** None (can start after E1; needs catalogue seed in tests). Do not start before slice 1 is the agreed first gate.

**Files likely touched:**
- `agent-data-plane/src/test/java/**/CataloguePinLint*`
- Optionally a small `application` helper if lint is reused later

**Estimated scope:** Medium

---

## Task E8: Dummy `--all` fail-closed smoke

**Description:** Turn the chat scratchpad catalog into the Compose half of slice 2: every dummy chat must complete (or fail controlled) at the pinned route version. Not the routing golden set.

**Acceptance criteria:**
- [x] Documented command: `./agent-fabric-scripts/route-runs/run-job.sh --all` with `WAIT=1` (or equivalent) exits non-zero on hydrate/start/loop failure
- [x] Smoke is pinned to the route versions in the catalogue seed (header or script comment lists them)
- [x] Default `run-eval.sh` (E9) still runs the **lint** without Compose; `--all` is the Compose confirmation
- [x] README/eval README: `--all` is pin/hydrate smoke, not routing labels

**Verification:**
- [x] Manual on a running stack: `--all` passes on current seed
- [x] Break a manifest pointer on one jobs route → `--all` fails (retire ACR `fee_explain@2026.08.1` → POST jobs 422 `HYDRATE_FAILED`; FK blocks inventing a missing manifest id)

**Dependencies:** Task E7

**Files likely touched:**
- `agent-fabric-scripts/route-runs/run-job.sh` (fail-closed / WAIT default for eval)
- `agent-data-plane/run-eval.sh`
- `agent-fabric-evals/intent-router-evals/README.md`

**Estimated scope:** Small

---

## Checkpoint: 2. Pin and hydrate

- [x] E7 done; E8 fail-closed `--all` documented
- [x] Proven once on Compose: `WAIT=1 ./agent-fabric-scripts/route-runs/run-job.sh --all` passes; break a manifest → fails
- [x] Catalogue seed is lint-clean
- [x] Human review before treating slices 1–2 as the ship gate

---

## Gate packaging (how you run 1 + 2)

Not a fourth eval slice.

---

## Task E9: Local eval gate script

**Description:** One command that runs the in-process eval tests so operators do not have to remember Maven class names.

**Acceptance criteria:**
- [x] `agent-data-plane/run-eval.sh` runs Routing (chat + jobs entitle) and Pin lint test classes
- [x] Non-zero exit on any failure
- [x] Help text points at `agent-fabric-evals/intent-router-evals/README.md` and this task list; mentions `--all` as slice 2 Compose smoke
- [x] Does not require Grafana or an LLM

**Verification:**
- [x] `./agent-data-plane/run-eval.sh` exits 0 on current main
- [x] Break a golden expected `route_id` → non-zero

**Dependencies:** Task E3, Task E6, Task E7

**Files likely touched:**
- `agent-data-plane/run-eval.sh`

**Estimated scope:** Small

---

## Task E10: Incident-to-case playbook

**Description:** A misroute becomes a golden row. The gate stays red until the catalogue or classifier is fixed.

**Acceptance criteria:**
- [x] A section in `agent-fabric-evals/intent-router-evals/README.md` lists: capture utterance + claims + actual outcome; add case; run `run-eval.sh`; do not “fix” by deleting the case
- [x] States jobs vs chat (jobs are entitle, not classify)
- [x] Links examiner questions from the plan

**Verification:**
- [x] Manual: steps are followable without this chat
- [x] Does not tell the operator to call decide from a browser as the gate

**Dependencies:** Task E9

**Files likely touched:**
- `agent-fabric-evals/intent-router-evals/README.md`

**Estimated scope:** Small

---

## Task E11: Glossary / Control Plane honesty for `eval_suite_id`

**Description:** `eval_suite_id` is slice 3 (per-route quality). It is not the routing golden set.

**Acceptance criteria:**
- [x] Glossary Eval suite text still says not used on the hot path; add that the CI routing golden set is the board, not this pointer
- [x] Empty `eval_suite_id` on a route is not an error in the UI (correct for `agent-chat`)
- [x] Do not add a fake “eval passed” badge

**Verification:**
- [x] Control Plane glossary copy reviewed against [index.html](../../agent-fabric-plane/agent-control-plane/public/index.html) glossary Eval suite row
- [x] No new Control Plane API

**Dependencies:** None (docs/UI copy only)

**Files likely touched:**
- `agent-fabric-plane/agent-control-plane/public/index.html`
- Possibly `agent-fabric-plane/agent-control-plane/public/app.js` if empty-state copy needs a word

**Estimated scope:** Small

---

## Task E12: README eval notes

**Description:** Root README points at the eval plan/todo and how to run the local gate.

**Acceptance criteria:**
- [x] README links [eval-plan.md](./eval-plan.md) and [eval-todo.md](./eval-todo.md)
- [x] Routing command: `./agent-data-plane/run-eval.sh`
- [x] Pin/hydrate smoke: dummy-request `--all` (fail-closed)
- [x] Explicit: not on the hot path; `--all` is not the routing golden set

**Verification:**
- [x] Manual: a new session can find and run slice 1 from README
- [x] Docs table / See also does not claim evals are implemented until E9 exists

**Dependencies:** Task E9

**Files likely touched:**
- `README.md`
- `agent-fabric-evals/intent-router-evals/README.md`

**Estimated scope:** Small

---

## Task E13: Verification checklist (break a label)

**Description:** Prove the routing gate is a gate: change one expected outcome, watch failure, restore.

**Acceptance criteria:**
- [x] Checklist: (1) flip `fee_explain` expected route (2) `run-eval.sh` fails (3) restore (4) passes
- [x] Confirms no decide/start/loop code path was added for eval
- [x] Confirms fixtures contain no secrets

**Verification:**
- [x] Run the checklist once; all boxes pass
- [x] Human sign-off

**Dependencies:** Task E9, Task E10

**Files likely touched:**
- `agent-fabric-evals/intent-router-evals/README.md`

**Estimated scope:** Small

---

## Checkpoint: slices 1–2 complete

- [x] E1–E13 done
- [x] Local command gates routing; `--all` is pin/hydrate smoke
- [x] Out of scope still out (LLM-as-judge, output schemas, hot-path eval, route_tables)
- [x] Human review before slice 3

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
- [x] Fixture lists expected stage/tool order from the seeded workflow
- [x] Test hydrates from test doubles or asserts workflow JSON — does not require a live model
- [x] Free-form routes remain without a suite (`eval_suite_id` empty)
- [x] Routing gate (E1–E13) must not depend on E14
- [x] Seed `eval_suite_id` only if this suite id is real

**Verification:**
- [x] Reorder a workflow stage in the test double → suite fails
- [x] `run-eval.sh` either skips E14 by default or has `--quality`

**Dependencies:** Checkpoint slices 1–2 complete

**Files likely touched:**
- `agent-fabric-evals/route-quality/routes/<suite_id>/<version>/cases.json`
- `agent-runtime` or `agent-data-plane` tests (workflow order)
- Catalogue seed `eval_suite_id` on `card_freeze` only if the id resolves

**Estimated scope:** Medium
