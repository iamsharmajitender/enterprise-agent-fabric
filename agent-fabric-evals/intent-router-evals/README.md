# Intent router evals

CI answer key for the **decide board**: chat routing, jobs entitle, and catalogue pin lint.

Jane’s turn does **not** run these. A failed eval blocks a catalogue / PR change, not a live reply.

| This folder | Not this folder |
| --- | --- |
| Decide: utterance or named `route_id` + claims → `route` / `clarify` / `abstain` | After-start tool order → [`../route-quality/`](../route-quality/README.md) (`eval_suite_id`) |
| In-process ADP JUnit (`run.sh`) | Compose pin/hydrate smoke → `WAIT=1 ./agent-fabric-scripts/route-runs/run-job.sh --all` |

## Quick start

```bash
./agent-fabric-evals/intent-router-evals/run.sh
# same as:
./agent-fabric-plane/agent-data-plane/run-eval.sh
```

Runs `RoutingEvalTest`, `JobsEntitleEvalTest`, `CataloguePinLintTest` against `InMemoryRouteStore.seedEvalBoard()`.

## Layout

```text
intent-router-evals/
  active.json                 # suite → version folder
  routing/<version>/          # chat decide labels
  jobs-entitle/<version>/     # jobs entitle / fail-closed
  pin/<version>/              # catalogue-cut label for pin lint
  run.sh
```

Flip a golden `expected.route_id`, watch the gate fail, restore — do not delete the case.
