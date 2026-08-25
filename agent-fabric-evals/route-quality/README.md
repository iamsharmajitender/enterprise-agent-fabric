# Route quality

Per-route suites for **after start**: did **this** route do the right work in order?

Not the decide board. Intent-router gates stay under [`../intent-router-evals/`](../intent-router-evals/README.md).

| This folder | Not this folder |
| --- | --- |
| Same `route_id` + goal → expected **stage / tool order** | Utterance contest → `intent-router-evals/routing` |
| Keyed by catalogue `eval_suite_id` | Jobs entitle / pin lint → `jobs-entitle` / `pin` |
| No LLM-as-judge; no reply-prose scoring | Compose `--all` smoke |

**Status:** Pattern 2 tool-sequence suites + harness (**E14**). Run:

```bash
./agent-fabric-evals/route-quality/run.sh
# or:
./agent-data-plane/run-eval.sh --quality
```

Default `./agent-data-plane/run-eval.sh` stays intent-router-only. Free-form routes keep `eval_suite_id` empty.

## When a route gets a suite

| Applicable | Skip |
| --- | --- |
| Pattern **2** deterministic workflows (fixed stage/tool order) | Pattern **0** free-form / single inference |
| | Pattern **1** autonomous CALL/DONE (model picks tools) |
| | Pattern **3** guided inner allowlists (outer order only — later if needed) |
| | Chat with no mandated tool path (`agent-chat`, …) |

Empty `eval_suite_id` on a route means “no quality suite.” That is correct for free-form.

Suite id convention: `{route_id}_tools` (e.g. `card_freeze` → `card_freeze_tools`). Catalogue may point at that id only when the folder exists.

## Layout

```text
route-quality/
  active.json                 # suite_id → live version
  run.sh                      # RouteQualityEvalTest
  schemas/
    case.schema.json          # authoring aid (not enforced by loader shape checks)
    example-tool-sequence.json
  routes/
    <suite_id>/<version>/
      suite.json              # metadata + route_id
      cases.json              # happy-path goal + expected.stages
```

## Active suites (2026.08.1)

| `eval_suite_id` | Route | Expected order (short) |
| --- | --- | --- |
| `llm_pipeline_tools` | `llm_pipeline` | extract → rewrite → format |
| `policy_memo_tools` | `policy_memo` | prefetch → generate |
| `account_notify_tools` | `account_notify` | notify_customer → respond |
| `card_freeze_tools` | `card_freeze` | identity_check → limit_check → freeze_card → respond |
| `dispute_intake_tools` | `dispute_intake` | doc_intake → case_open → packet_summarize |
| `pack_then_notify_tools` | `pack_then_notify` | prefetch → notify → respond |
| `pack_then_freeze_tools` | `pack_then_freeze` | prefetch → identity → limit → freeze → respond |
| `pack_then_review_tools` | `pack_then_review` | prefetch → ocr → risk_engine → draft_memo |
| `clause_lookup_tools` | `clause_lookup` | clause_search → respond |
| `template_retrieve_tools` | `template_retrieve` | clause_search → policy_search → risk_engine → respond |
| `msa_risk_review_tools` | `msa_risk_review` | ocr → clause → policy → risk → memo |
| `kyc_onboarding_tools` | `kyc_onboarding` | docs → id → sanctions → risk → human_gate → activate → summarize |
| `claims_adjudicate_tools` | `claims_adjudicate` | policy_search → clause_search → risk → memo |

Stage lists match the seeded workflow JSON in Data Plane (`InMemoryWorkflowStore` / `V1__dataplane.sql`). `kyc_onboarding` includes catalogue-only `branch` / `human_gate` nodes in designer order.

## What a case asserts

1. **Input** — fixed jobs `goal` (+ claims). Not an open utterance contest.
2. **Expected** — ordered `stages[]` with `id`, and `tool` / `llm_role` / `type` when present.
3. **Not asserted** — assistant memo text, `output_schema_id`, “sounds right.”

Example: [`schemas/example-tool-sequence.json`](schemas/example-tool-sequence.json) (`card_freeze_tools`).

## `active.json`

Pointer map: suite id → version folder. Same promote / rollback idea as intent-router:

- Edit cases under the live version → leave `active.json` alone.
- New cut → copy `routes/<suite>/<old>/` → `routes/<suite>/<new>/`, flip that key.
- Suites advance independently.

## How CI uses this (E14)

1. Resolve route’s `eval_suite_id` → load `route-quality/routes/<id>/<active version>/`.
2. Hydrate workflow from in-memory seed / test doubles (**no live model**).
3. Compare observed stage/tool order to `expected.stages` (`RouteQualityEvalTest`).
4. Reorder a seeded stage → match fails (`reorderedWorkflowFailsMatch`).
5. Intent-router gate stays separate: `./agent-data-plane/run-eval.sh` (no `--quality`). Combined: `--all`.

```bash
./agent-fabric-evals/route-quality/run.sh
./agent-data-plane/run-eval.sh --quality
./agent-data-plane/run-eval.sh --all
```


## Author a case

1. Confirm the route is Pattern 2 with a fixed workflow.
2. Copy [`schemas/example-tool-sequence.json`](schemas/example-tool-sequence.json) into that suite’s `cases.json` (or add a sibling case).
3. Set `id`, `goal`, `claims`, `expected.stages` from the seeded workflow — do not invent tools.
4. If you introduce a **new** suite id, add it to `active.json`, create `routes/<suite_id>/<version>/`, and only then set catalogue `eval_suite_id` to that id.

## New suite version

1. Copy `routes/<suite_id>/2026.08.1/` → `routes/<suite_id>/<new>/`.
2. Align `expected.stages` with the new workflow cut.
3. Point `active.json` at `<new>`.
4. Keep the old folder for replay.

## Related

```bash
# Intent-router gate (decide / entitle / pin) — not route-quality
./agent-fabric-evals/intent-router-evals/run.sh
```

Task lists: [`docs/tasks/eval-plan.md`](../../docs/tasks/eval-plan.md) (slice 3), [`docs/tasks/eval-todo.md`](../../docs/tasks/eval-todo.md) (E14).
