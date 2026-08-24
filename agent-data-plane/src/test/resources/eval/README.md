# Eval fixtures (Data Plane tests)

Golden sets for the catalogue seed. **CI/platform only** — not decide, pin, start, or loop.

Routing is the **board** (this mix of `route_id` @ `route_version`), not `eval_suite_id` on a row. `eval_suite_id` is slice 3 (route quality), later.

Do not put utterances in metrics.

## Layout

| File | Role |
| --- | --- |
| `case.schema.json` | Case shape |
| `example-chat-route.json` | Copy this to add a chat case |
| `routing-golden.json` | Chat contest + adversarial rows |
| `jobs-entitle-golden.json` | Named `route_id` + claims (no classify) |

Pack decide fixtures stay in [`docs/05-reference/`](../../../../../docs/05-reference/README.md). They are contract examples, not the golden set. Field names on a case follow [decide-chat-request.json](../../../../../docs/05-reference/decide-chat-request.json) / [decide-jobs-route.json](../../../../../docs/05-reference/decide-jobs-route.json) (`ingress`, `channel`, `message` xor `route_id`, `claims`). Docs map: [`docs/README.md`](../../../../../docs/README.md). Plan: [`docs/tasks/eval-plan.md`](../../../../../docs/tasks/eval-plan.md).

## Case fields

| Field | Chat | Jobs |
| --- | --- | --- |
| `id` | unique | unique |
| `ingress` | `chat` | `jobs` |
| `channel` | e.g. `web` | e.g. `web` |
| `message` | required | `null` |
| `route_id` | `null` (classify) | named route |
| `claims` | decide `sub` + `emts` | same |
| `expected.outcome` | `route` / `clarify` / `abstain` | `route` / `abstain` (never `clarify`) |
| `expected.route_id` | when outcome is `route` | when outcome is `route` |
| `tags` | optional (`adversarial`) | optional |

File header `catalogue` lists the labelled mix. Drift against `InMemoryRouteStore` fails the suite.

## Chat vs jobs

| | Chat | Jobs |
| --- | --- | --- |
| Question | Did classify pick the right route? | Did named `route_id` + claims entitle? |
| File | `routing-golden.json` | `jobs-entitle-golden.json` |
| `clarify` | yes | never |
| Phrase that looks like a job, in chat | still **classifies** (does not bind `route_id` from the text) | not a jobs case |

## Author a case

1. Copy `example-chat-route.json` (chat) or a jobs row in `jobs-entitle-golden.json`.
2. Set `id`, utterance or named `route_id`, claims, `expected`.
3. No memo text. No `eval_suite_id`.
4. A misroute stays in the file until the catalogue or classifier is fixed — do not delete it to go green.

## Incident → case (do not “fix” by deleting)

A production or demo misroute becomes a golden row. The gate stays red until the catalogue or classifier is fixed.

1. Capture `ingress`, `channel`, utterance **or** named `route_id`, `claims`, and the **actual** outcome (`route:<id>` / `clarify` / `abstain`).
2. Add a case with a new unique `id`. Tag `adversarial` when it is a safety steal (fee ≠ freeze). Chat incidents go in `routing-golden.json`. Jobs entitle misses go in `jobs-entitle-golden.json`.
3. Run `./agent-data-plane/run-eval.sh` from the repo root (or this module).
4. Change keywords, claims, or the catalogue so the **expected** label is true. Do **not** delete the case to go green. Do **not** call decide from a browser as the gate.

Examiner questions ([eval-plan.md](../../../../../docs/tasks/eval-plan.md)):

1. Which routes were eligible for this identity (and channel)?
2. Why this turn **routed**, **clarified**, or **abstained**?
3. Do adversarial routing cases pass at 100% before release?
4. Was the last routing incident added to the golden set so CI would block a regression?

## Run the gate

```bash
./agent-data-plane/run-eval.sh
```

No Compose. No LLM. If `mvn` is not on PATH, the Data Plane image build runs the same tests:

```bash
docker compose -f docs/run/compose/docker-compose.yml build agent-data-plane
```

Dummy `--all` is pin/hydrate smoke on a running stack, **not** these labels:

```bash
WAIT=1 ./docs/run/dummy-request/run-job.sh --all
```

## Verification checklist (break a label)

Proves the routing gate is a gate. Fixtures contain no secrets (seed claims only). Eval adds **no** decide / start / loop path — only Data Plane tests.

1. Confirm green: `./agent-data-plane/run-eval.sh` exits 0.
2. In `routing-golden.json`, on case `chat-fee-charged-42`, set `expected.route_id` to `card_freeze`.
3. `./agent-data-plane/run-eval.sh` exits non-zero.
4. Restore `fee_explain`.
5. `./agent-data-plane/run-eval.sh` exits 0.

Do not leave the flipped label in the file.
