# Eval fixtures (Data Plane tests)

Golden sets for the teaching catalogue. **CI/platform only** — not decide, pin, start, or loop.

Routing is the **board** (this mix of `route_id` @ `route_version`), not `eval_suite_id` on a row. `eval_suite_id` is slice 3 (route quality), later.

Do not put utterances in metrics.

## Layout

| File | Role |
| --- | --- |
| `case.schema.json` | Case shape |
| `example-chat-route.json` | Copy this to add a chat case |
| `routing-golden.json` | Chat contest + adversarial rows |
| `jobs-entitle-golden.json` | Named `route_id` + claims (no classify) |

Pack decide fixtures stay in [`docs/05-reference/`](../../../../../docs/05-reference/README.md). They are contract examples, not the golden set. Docs map: [`docs/README.md`](../../../../../docs/README.md).

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

## Author a case

1. Copy `example-chat-route.json`.
2. Set `id`, utterance, claims, `expected`.
3. No memo text. No `eval_suite_id`.
4. A misroute stays in the file until the catalogue or classifier is fixed — do not delete it to go green.
