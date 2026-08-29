# Escalate to human (async handoff)

A Pattern 1 domain tool **opens a ticket for a human queue**, then the **parent run completes**. The human works the case later outside this correlation. The run does **not** pause for `/turns`.

Seed proof: [`shopassist_case`](../03-catalogue/routes.md#shopassist_case). Runtime: `build_agent_loop` in `agent-runtime/app/graph/workflow.py`.

This is **not** a [process gate](human-review-process-gate.md). Use `human_gate` when the **same** run must continue after an in-flow approve/reject.

## Who does what

```
Lookups → billing/policy domain APIs (optional)
    │
    ▼
CALL escalate_to_human
    │  POST domain handoff API (mock: /handoff/escalate)
    │  slot escalate_to_human = { handoff_id, text }
    ▼
Runtime policy (not another LLM turn required)
    │  if handoff ok AND no pending specialist joins → complete parent
    │  if handoff ok AND joins still pending → keep looping (no second ticket)
    ▼
Customer-facing result (auto or DONE)
    │  e.g. "I've escalated… Reference hof-1. Someone will follow up."
    ▼
run.terminal status=completed
    │
    ▼
Human queue (outside Fabric)
    │  works hof-1 later; does not resume this Pattern 1 loop
```

## Two Runtime guarantees

### 1. Auto-complete after success (when nothing else is pending)

After a **successful** escalate (`handoff_id` present in `slots.escalate_to_human`):

| Pending `kind=agent` joins? | Behavior |
| --- | --- |
| No | Parent **auto-completes** with a customer message that includes the handoff id. Audit shows **completed**. |
| Yes (child started, not yet terminal join) | Do **not** complete yet; loop continues until joins finish or the model `DONE`s. |

“Pending join” means a specialist slot has `correlation_id` / `route_id` but is not yet `{ status: completed|failed, result: … }`.

### 2. Idempotent re-CALL

If the model `CALL escalate_to_human` **again** after a handoff already exists:

| Prior handoff? | Pending joins? | Behavior |
| --- | --- | --- |
| Yes | No | **No second POST**. Complete with the **same** `handoff_id`. |
| Yes | Yes | **No second POST**. Note that the handoff is already open; keep looping. |
| No | — | First POST creates the ticket. |

Never open a second ticket for the same parent turn after success.

## Scenario (ShopAssist)

Customer: damaged jacket ORD-77819, possible double charge, wants full refund.

1. ASK for locator → lookup order → `investigate_duplicate_charge` / `check_return_policy` as needed.  
2. Policy: eligible but above auto limit → needs human.  
3. `escalate_to_human` → `hof-1`.  
4. Parent **completes** (auto) with the handoff reference.  
5. Ops works `hof-1` later; this chat run is already done.

[`run-chat.sh shopassist_case_ask`](../../agent-fabric-scripts/catalogue-seed/run-chat.sh).

## Contrast

| | `escalate_to_human` | `human_gate` |
| --- | --- | --- |
| Shape | Domain HTTP tool | Workflow stage `type=human_gate` |
| After success | Parent usually **completed** | Parent **waiting** |
| Human continues | Separate queue / ticket | Same correlation via `/turns` |
| Idempotency | Re-CALL does not create a second handoff | N/A (pause, not a ticket tool) |

## Code map

- Loop + auto-complete + idempotency: `agent-runtime/app/graph/workflow.py` (`_complete_after_escalate`, `_idempotent_escalate_replay`)
- Capability / mock: seed `escalate_to_human`; `agent-fabric-mocks/tools/catalog/escalate_to_human.json`
- Tests: `agent-runtime/tests/test_graph.py` (`test_agent_loop_escalate_*`)
