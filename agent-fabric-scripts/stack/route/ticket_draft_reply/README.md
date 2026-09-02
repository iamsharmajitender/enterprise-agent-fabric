# ticket_draft_reply

Route id: `ticket_draft_reply` · version `2026.08.1` · Pattern 0 (child agent).

Jobs-only child started by parent [`ticket_triage`](../ticket_triage/) `draft_reply` capability (`kind=agent`, `join=true`). Control Plane: [http://localhost:3006/routes/ticket_draft_reply](http://localhost:3006/routes/ticket_draft_reply).

Parent projects this payload from goal + prior slots:

```json
{
  "utterance": "Customer charged twice on ORD-77819",
  "category": "billing",
  "order_ref": "ORD-77819",
  "intent": "duplicate_charge",
  "priority": "normal"
}
```

Load with parent:

```bash
./agent-fabric-scripts/stack/route/ticket_draft_reply/add.sh
./agent-fabric-scripts/stack/route/ticket_triage/add.sh
```
