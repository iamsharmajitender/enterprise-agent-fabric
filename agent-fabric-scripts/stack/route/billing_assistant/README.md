# billing_assistant

Route id: `billing_assistant` · version `2026.08.1` · Pattern 1 (autonomous) with **LLM-owned branching**.

No workflow. The model picks the next tool each turn via `CALL` / `ASK` / `DONE`:

| Customer asks about… | Typical `CALL` |
| --- | --- |
| Account fees / charges | `account_fee_lookup` with `acct-*` |
| Order status / delivery | `lookup_order_by_order_id` with `ORD-*` |

```bash
./agent-fabric-scripts/stack/route/billing_assistant/add.sh
```

Chat demos: [http://localhost:3014/chat](http://localhost:3014/chat)

Example messages:

- `Why was I charged $42 on account acct-4412?` → fee lookup tool
- `Where is my order ORD-77819?` → order lookup tool

Required claims: `accounts:read`, `support:case` (stub user needs both in `X-Stub-Claims`).

Remove: `./remove.sh`
