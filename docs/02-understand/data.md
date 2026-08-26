# Data

The run graph has three channels for stage handoff inside one correlation id:

| Channel | Lives on | Who consumes it |
| --- | --- | --- |
| `goal` | Start body (job `payload` / chat utterance). **Never updated.** | Every LLM stage; base of every HTTP body |
| `slots` | `working.slots[stage_id]` — structured JSON after each stage | Next HTTP merge (schema keys only); branch/gate; prefetch pack; child `kind=agent` projection |
| `notes` | Append-only **strings** on `working` | LLM stages (`_user_blob(goal, notes)`); optional `payload["notes"]` on HTTP |

`GraphState` in `agent-runtime/app/graph/workflow.py` is `result`, `goal`, `notes`, `slots`. HTTP assembly is in `agent-runtime/app/graph/payload.py`:

```python
payload = dict(goal)
# merge keys from prior slots when declared on next input_schema.properties
```

Fail closed if `input_schema.required` keys are missing. Do not dump all slots or all notes onto every HTTP call.

`query_formulation` sets `payload["query"]` from the LLM. `classify` / `synthesis` append prose to `notes` and, when JSON parses, write `slots[stage_id]`. LLM roles with `output_schema` validate through `with_structured_output`. How to write that schema: [schemas](schemas.md).

## Example: stage 2 gets stage 1’s JSON

Route `purchase_refund` (**D5 proof**): job payload has `doc_id`, `account_id` only.

1. `extract_fields` (classify) returns `{ merchant, amount, date }` → stored in `slots["extract_fields"]` and appended to `notes`.
2. `match_purchase` HTTP body = `goal` ∪ `{ merchant, amount, date }` because those keys are `required` on `match_purchase`’s `input_schema`.
3. If classify omits a required field, the run fails **before** `match_purchase` invokes.

Route `card_freeze` today: identity/limit tools return prose; structured slot merge is not the proof path unless the workflow adds schema-bound hops.

## Prefetch

On `deterministic_prefetch`, empty-invoke prefetch stages POST corpus gateways and write `working.slots.prefetch`. Downstream LLM/HTTP stages consume packed text. See [retrieve](retrieve.md).

## Still catalogue-only

- **`conversation` / `long_term`** — Shared Memory (not the run pin). See [memory](memory.md).
- **Stage allowlists** on Pattern 3 — metadata only; AR does not enforce inner tool picks yet.

Catalogue vs Runtime matrix: [status](status.md). Verification checklist: [dataflow-plan.md](../tasks/dataflow-plan.md#verification-checklist-d13).
