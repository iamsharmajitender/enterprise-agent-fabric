# Intent router evals

CI answer key for the **decide board**: chat routing, jobs entitle, and catalogue pin lint.

Jane’s turn does **not** run these. A failed eval blocks a catalogue / PR change, not a live reply.

| This folder | Not this folder |
| --- | --- |
| Decide: utterance or named `route_id` + claims → `route` / `clarify` / `abstain` | After-start tool order → [`../route-quality/`](../route-quality/README.md) (`eval_suite_id`) |
| In-process ADP JUnit (`run.sh`) | Compose pin/hydrate smoke → `WAIT=1 ./docs/run/dummy-request/run-job.sh --all` |

Task lists: [`docs/tasks/eval-plan.md`](../../docs/tasks/eval-plan.md), [`docs/tasks/eval-todo.md`](../../docs/tasks/eval-todo.md).

## Quick start

```bash
./agent-fabric-evals/intent-router-evals/run.sh
# same as:
./agent-data-plane/run-eval.sh
```

Runs `RoutingEvalTest`, `JobsEntitleEvalTest`, `CataloguePinLintTest`. Fixtures load from this tree via Maven `testResources`.

## What lives here

```text
intent-router-evals/
  active.json                 # which version each suite CI loads
  schemas/                    # authoring aids only (not enforced by the gate)
  routing/<version>/          # chat decide labels
  jobs-entitle/<version>/     # jobs entitle / fail-closed labels
  pin/<version>/              # catalogue-cut label for pin lint (+ smoke docs)
  run.sh
```

| Suite | Question the gate asks |
| --- | --- |
| `routing` | For this utterance + claims + channel, decide must pick X / clarify / abstain |
| `jobs-entitle` | For this named `route_id` + claims, entitle or fail closed |
| `pin` | This catalogue cut must be able to start (lint in ADP; optional Compose `--all`) |

### Per-suite files (routing / jobs-entitle)

Same shape; filename stem differs (`route-` vs `jobs-entitle-`):

```text
<suite>/<version>/
  {prefix}-suite.json           # suite metadata
  {prefix}-catalogue.json       # board pins (must match in-memory seed)
  {prefix}-case-manifest.json   # ordered list of files under cases/
  cases/*.json                  # labels split by purpose
```

| Suite | Prefix | Case buckets today |
| --- | --- | --- |
| `routing` | `route-` | `fee`, `clarify`, `adversarial`, `seed-intents`, `guards` |
| `jobs-entitle` | `jobs-entitle-` | `mode-0-inference` … `mode-3-guided`, `guards` |
| `pin` | `pin-` | `pin-suite.json` only — no cases |

## `active.json` — the live cut

```json
{
  "routing": "2026.08.1",
  "jobs-entitle": "2026.08.1",
  "pin": "2026.08.1"
}
```

Pointer map only: suite id → version **folder name**. Cases live under that folder; this file does not hold labels.

| Change | What to do |
| --- | --- |
| Add / fix a case on the current board | Edit `cases/` under the active version. Leave `active.json` alone. |
| New catalogue cut / board that must not mix with the old one | Copy `<suite>/<old>/` → `<suite>/<new>/`, edit the copy, flip that suite’s key in `active.json`. |
| Promote | Point the suite at the new folder. |
| Rollback | Point it back at the previous folder. Keep old folders for replay. |
| Suites drift | Normal. e.g. routing on `2026.09.1` while jobs-entitle stays on `2026.08.1`. |
| New suite kind later | Add a new key when the suite exists. Missing key → loader fails for that suite. |

## `schemas/` — authoring only

| File | Role |
| --- | --- |
| [`case.schema.json`](schemas/case.schema.json) | JSON Schema for one case (`id`, `ingress`, `claims`, `expected`, …) |
| [`example-chat-route.json`](schemas/example-chat-route.json) | Copy-paste starter for a routing case |

The gate does **not** load or validate against these. `EvalJson` checks ids, uniqueness, and `expected.outcome`. Use the schema in the IDE if you want shape hints while editing.

## Author a routing case

1. Copy [`schemas/example-chat-route.json`](schemas/example-chat-route.json) into the right file under active `routing/<version>/cases/` (`fee`, `clarify`, `adversarial`, `seed-intents`, or `guards`). New file → add its name to `route-case-manifest.json`.
2. Set `id`, utterance (`message`), claims, `expected`. No memo text.
3. Run `run.sh`. Do **not** delete a failing case to go green.

## Author a jobs-entitle case

1. Add under active `jobs-entitle/<version>/cases/` in the autonomy band that matches the job (`mode-0-inference` … `mode-3-guided`, or `guards`). New file → add its name to `jobs-entitle-case-manifest.json`.
2. Set `id`, named `route_id`, claims, `expected` (`route` or fail-closed `abstain`).
3. Run `run.sh`.

## New suite version

1. Copy `routing/2026.08.1/` → `routing/<new>/` (repeat for `jobs-entitle` / `pin` if those cuts move).
2. Edit `{prefix}-catalogue.json` and/or `cases/*`.
3. Point `active.json` at `<new>` for the suites that moved.
4. Keep the old folder for replay (“what sat the gate that day”).

## Incident → case

1. Capture ingress, channel, utterance **or** named `route_id`, claims, actual outcome.
2. Add a case under the active suite version. Tag `adversarial` for safety steals.
3. Fix catalogue or classifier; leave the case in place so CI keeps the regression.

## Break a label (prove the gate)

1. `./agent-fabric-evals/intent-router-evals/run.sh` exits 0.
2. In active `routing/<version>/cases/fee.json`, on `chat-fee-charged-42`, set `expected.route_id` to `card_freeze`.
3. Run again → non-zero.
4. Restore `fee_explain`.
5. Run again → 0.

## Related (not this gate)

```bash
# Pin/hydrate Compose smoke — needs a running stack; not the routing labels
WAIT=1 ./docs/run/dummy-request/run-job.sh --all
```

`eval_suite_id` on a catalogue row points at route-quality (slice 3 / E14), not at anything under this folder.
