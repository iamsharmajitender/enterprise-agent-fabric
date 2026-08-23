# Implementation Plan: Agent evals (local Fabric)

## Overview

Stand up a **CI-gated eval surface** for the catalogue seed so a misroute or a broken pin cannot ship unnoticed. Three slices, **in this order**:

1. **Routing** (the only eval the architecture requires). Chat is the contest: `(utterance, claims, channel) → route:<id> | clarify | abstain`. Not a memo. Jobs skip classify — thinner suite under this slice: named `route_id` + claims → entitled `route` or fail-closed. A misroute becomes a new case. Release does not ship if “Why was I charged $42?” starts `card_freeze`. `eval_suite_id` on a route is the wrong key; routing is a property of the board. Hold the golden set next to the catalogue (product + cut / labelled mix), not as `fee_explain_golden`.
2. **Pin and hydrate** (cheap, high signal). For each active route: pointers resolve, manifest refs are published, retrieval scope ids exist, Pattern 0 has no tools/workflow, high-risk routes still have a workflow. Catalogue lint plus dummy jobs `--all` as fail-closed smoke, pinned to route version.
3. **Route quality** (later, only where it pays). This is what `eval_suite_id` is for. Deterministic / jobs: same payload → expected tool sequence, not prose (`card_freeze` must be identity → limit → freeze). Grounded Q&A: citation from scoped corpus, or abstain. No LLM-as-judge. Free-form (`agent-chat`): skip — empty `eval_suite_id` is correct. Do not wait on `output_schema_id`; the reply can stay `{ "message": "…" }`.

Target: examiners can show adversarial routing cases pass at 100% before release, and that a routing incident was added to the golden set and blocked in CI ([enterprise-agent-fabric](../04-architecture/narrative/enterprise-agent-fabric.mdx)).

**Not in this plan:** LLM-as-judge, output-schema validation, eval on the decide/start/loop hot path, a decision-audit store, `route_tables` snapshots ([future-enhancement](./future-enhancement.md#versioned-route-table)), production eval SaaS, scoring free-form chat prose, implementing `policy_profile` / PDP. Replacing keyword Layer ② / adding ① rules and ③ fallback is [intent-plan.md](./intent-plan.md) — this eval plan only freezes the labels those layers must still hit.

**Docs map:** [docs/README.md](../README.md). **Behaviour / architecture source:** [agent-plane](../04-architecture/agent-plane.md), [enterprise-agent-fabric](../04-architecture/narrative/enterprise-agent-fabric.mdx) (Agent evals box). Do not reopen locked fabric rules.

## Architecture Decisions

- **Evals are platform/CI, not a runtime step.** Decide stays a classify call. A failed eval blocks a catalogue change (or a PR), not Jane’s turn.
- **Slice 1 is the board.** Do not key chat cases on `eval_suite_id`. `eval_suite_id` exists only for slice 3.
- **Jobs live under slice 1.** They do not get their own numbered slice. Chat is the real contest.
- **Slice 2 is lint + `--all`.** Dummy `--all` is smoke for hydrate/start, fail-closed at the pinned version. It is not the routing golden set.
- **Empty `output_schema_id` is fine.** Slice 3 asserts tools and citations while the reply is free-form text.
- **JSON fixtures are the source of truth.** Same shape as pack decide contracts. Unit tests load the files from `agent-data-plane/src/test/resources/eval/` (not `docs/`).
- **Fast path: in-memory catalogue seed.** Parameterized Data Plane tests against `InMemoryRouteStore` (must stay aligned with Flyway/SQL seed).
- **Incidents become cases.** CI stays red until the catalogue or classifier is fixed — do not delete the case.
- **Record the mix.** Each golden file headers `route_id` @ `route_version` it was labelled against. Cheaper than `route_tables` now.

## Eval surfaces (this order)

| # | Slice | Question | Expected |
| --- | --- | --- | --- |
| 1 | Routing | Chat: utterance + claims + channel → decide? Jobs (thinner): named `route_id` + claims entitled? | `route:<id>`, `clarify`, or `abstain`. Not a memo. |
| 2 | Pin and hydrate | Can each active row start at this version? | Pointers resolve; Pattern 0 has no tools/workflow; high-risk still has a workflow; `--all` fail-closed |
| 3 | Route quality (later) | After start, did **this** route do the right work? | Tool sequence / citation. Empty `eval_suite_id` = no suite |

## Examiner questions (definition of useful)

1. Which routes were eligible for this identity (and channel)?
2. Why this turn **routed**, **clarified**, or **abstained**?
3. Do adversarial routing cases pass at 100% before release?
4. Was the last routing incident added to the golden set so CI would block a regression?

## Demo path (definition of done for slices 1–2)

```text
# routing gate — no Compose
cd agent-data-plane && mvn test -Dtest=RoutingEval*,JobsEntitleEval*,CataloguePinLint*
./agent-data-plane/run-eval.sh
# inject a bad label → gate fails; restore → passes

# pin/hydrate smoke — Compose
WAIT=1 ./docs/run/dummy-jobs/run-job.sh --all   # fail-closed, pinned route versions
```

## Task List

### Phase 0: Foundation (fixtures)

- [x] Task E1: Eval fixture schema and `agent-data-plane/src/test/resources/eval/` layout

### 1. Routing (do this first)

- [x] Task E2: Chat routing golden set (`utterance, claims, channel → outcome`)
- [x] Task E3: Parameterized tests load the chat golden set
- [x] Task E4: Adversarial cases (fee ≠ `card_freeze`; incident becomes a case)
- [x] Task E5: Jobs entitle golden set (thinner suite under routing)
- [x] Task E6: Parameterized tests for jobs ingress

### Checkpoint: 1. Routing

- [ ] “Why was I charged $42?” → `route:fee_explain`, never `card_freeze`
- [ ] Clarify and abstain covered
- [ ] Jobs entitle with claims, fail closed without
- [ ] Golden set sits next to the catalogue mix, not on `eval_suite_id`
- [ ] Human review before pin lint

### 2. Pin and hydrate

- [x] Task E7: Catalogue pin lint (pointers, Pattern 0–3, published refs, retrieval scope)
- [x] Task E8: Dummy `--all` fail-closed smoke at route version

### Checkpoint: 2. Pin and hydrate

- [ ] Broken `tool_manifest` / Pattern 0-with-tools fails lint
- [ ] High-risk routes still have a workflow
- [ ] Catalogue seed passes lint; `--all` fail-closed on a running stack

### Gate packaging (how you run 1 + 2)

- [x] Task E9: `agent-data-plane/run-eval.sh`
- [ ] Task E10: Incident-to-case playbook
- [ ] Task E11: Glossary / Control Plane: `eval_suite_id` is slice 3, not routing
- [ ] Task E12: README eval notes
- [ ] Task E13: Verification checklist (break a label, watch the gate fail)

### Checkpoint: slices 1–2 complete

- [ ] All E1–E13 acceptance criteria in [eval-todo.md](./eval-todo.md) met
- [ ] Human review before slice 3

### 3. Route quality (later, only where it pays)

- [ ] Task E14: Deterministic tool sequence (`card_freeze` identity → limit → freeze); first real `eval_suite_id`; no output schema; no LLM-as-judge; skip `agent-chat`; grounded Q&A only after this

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| InMemory store drifts from Flyway seed | High | Pin lint + `--all` at the pinned versions |
| Golden set encodes yesterday’s keywords, not intent | Med | Cases are utterances + expected outcome; Layer ② may change as long as labels hold |
| Scope expands to scoring memos | High | Slice 3 is later; free-form routes keep `eval_suite_id` empty |
| Contest mix changes silently | Med | Fixture header lists the labelled mix; drift fails the suite |
| Eval calls live decide over HTTP in CI | Med | Routing gate is in-process JUnit; `--all` is slice 2 smoke |
| `eval_suite_id` mistaken for the routing suite | Med | E11 glossary/UI copy |

## Open Questions

- Keep the runner as Data Plane JUnit only, or also POST `/v1/intent/decide` against Compose? (Default: JUnit is the routing gate; E9 wraps `mvn test`. `--all` is slice 2.)
- How many chat cases in E2 before E3 lands? (Default: existing DecideService cases plus ~15 labelled seed utterances, including fee ≠ freeze.)
- Should Control Plane show routing-suite status? (Default: no. README + eval script are the operator surface.)
