# duplicate_charge_review

Route id: `duplicate_charge_review` · version `2026.08.1` · Pattern 2 (deterministic).

Fixed pipeline: **2 LLM calls + 2 HTTP tool calls**. Slot merge passes `customer_id` from `lookup_order_by_order_id` into `investigate_duplicate_charge`.

| Stage | Tool | `llm_role` | Slot / data flow |
| --- | --- | --- | --- |
| `intake` | `duplicate_charge_intake` | `classify` | LLM → `slots.duplicate_charge_intake.order_id` |
| `order_lookup` | `lookup_order_by_order_id` | `none` | HTTP body gets `order_id` from classify slot |
| `dup_check` | `investigate_duplicate_charge` | `none` | HTTP body gets `order_id` + **`customer_id` from lookup slot** |
| `respond` | `duplicate_charge_respond` | `synthesis` | LLM reply from `notes` |

```bash
./agent-fabric-scripts/stack/route/duplicate_charge_review/add.sh
```

Then open [http://localhost:3014/chat](http://localhost:3014/chat) and pick **Deterministic → duplicate_charge_review**, or [http://localhost:3014/jobs](http://localhost:3014/jobs) for the job demo.

Example job goal:

```json
{
  "utterance": "I was charged twice on order ORD-77819"
}
```

Expected tool HTTP payloads (deterministic order):

1. `lookup_order`: `{"order_id": "ORD-77819"}`
2. `investigate_duplicate_charge`: `{"order_id": "ORD-77819", "customer_id": "CUS-1842"}` (customer id from lookup mock)
