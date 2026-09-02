# ticket_triage

Route id: `ticket_triage` · version `2026.08.1` · Pattern 3 (guided).

Composition **#2** from [guided.md](../../../../agent-fabric-docs/06-patterns/guided.md): fixed outer stages, session memory, per-stage **allowlists** (catalogue metadata — inner CALL/DONE loop not wired in Runtime yet).

Control Plane: [http://localhost:3006/routes/ticket_triage](http://localhost:3006/routes/ticket_triage)

## Outer pipeline (3 stages)

| Stage | Tool | `llm_role` | Kind | Data flow |
| --- | --- | --- | --- | --- |
| `extract` | `parse_ticket` | `none` | domain | HTTP parses ticket → `slots.parse_ticket` |
| `analyse` | `tag_intent` | `none` | domain | HTTP gets **`category` + `order_ref` from parse slot** |
| `reply` | `draft_reply` | `none` | **agent** | POST child job → [`ticket_draft_reply`](../ticket_draft_reply/) (`join=true`) |

Child payload is projected from goal ∪ slots (`utterance`, `category`, `order_ref`, `intent`, `priority`).

```bash
./agent-fabric-scripts/stack/route/ticket_draft_reply/add.sh
./agent-fabric-scripts/stack/route/ticket_triage/add.sh
```

Scratchpad: [http://localhost:3014/chat](http://localhost:3014/chat) → **Guided → ticket_triage**

Example job payload:

```json
{
  "utterance": "Customer says they were charged twice on order ORD-77819"
}
```
