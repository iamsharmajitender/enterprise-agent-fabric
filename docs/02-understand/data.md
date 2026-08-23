# Data

The run graph has two channels. Slots do not exist.

| Channel | Lives on | Who consumes it |
| --- | --- | --- |
| `goal` | Start body (job `payload` / chat utterance). Copied onto every HTTP tool. **Never updated.** | Every HTTP stage |
| `notes` | Append-only **strings** (`text` / `message` / LLM completion) | LLM stages (`query_formulation`, `classify`, `synthesis`); `/v1/runs/{id}/turns` when `working=session` |

`GraphState` in `agent-runtime/app/graph/workflow.py` is `result`, `goal`, `notes`. HTTP payload is `dict(goal)` only:

```python
payload = dict(goal)
```

`query_formulation` then sets `payload["query"]` from the LLM. `classify` and `synthesis` append the completion to `notes` and skip HTTP.

## Freeze example

Route `card_freeze` is identity → limits → freeze. Dummy job payload is `card_id` and `account_id`. That object is `goal` for the whole run.

1. `identity_check` POSTs `dict(goal)`. It does not receive a derived `customer_id` from anywhere else.
2. The tool JSON (whatever identity returned) is **not** merged into `goal`. Only `text` / `message` is appended to `notes`.
3. `freeze_card` POSTs the same `dict(goal)` again. It never sees `identity_check` JSON. `customer_id` is missing unless the caller put it on the job payload.

Dummy jobs still complete because tool-mock ignores request bodies. That is not proof of dataflow.

## What is not built

- **Slots.** No structured per-stage JSON on the run pin. A capability `input_schema` does not fill the next HTTP body.
- **Tool JSON → next HTTP.** `notes` are strings for the LLM. HTTP never reads `notes`.
- **Prefetch pack.** Empty `invoke.url` is a no-op; chunks are not written anywhere. See [retrieve](retrieve.md).

Later work: [dataflow-plan.md](../tasks/dataflow-plan.md). Catalogue vs Runtime: [status](status.md).
