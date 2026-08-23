# Patterns

The catalogue seed is autonomy **0–3**. `autonomy_mode` on the route is that integer. Pattern answers who picks the next step inside Runtime. It does not change pin-then-hydrate.

| Pattern | Mode | What the route points at | What Runtime runs |
| --- | --- | --- | --- |
| 0 Single inference | `0` | Prompt pack. No tools, no workflow | One `synthesis` node from `host` |
| 1 Autonomous | `1` | Manifest + `max_loop_steps`. No workflow | Hydrated tools in manifest order (open loop is catalogue intent; this graph is still linear) |
| 2 Deterministic | `2` | Workflow required. Manifest when there are tools | Fixed stage list |
| 3 Guided | `3` | Workflow required; stages may carry an allowlist | Same linear graph. Allowlist is catalogue-only |

Examples: Pattern 0 `email_summarize`; Pattern 1 `fee_explain`; Pattern 2 `card_freeze`, `llm_pipeline`, `policy_memo`. Catalogue matrix: [03-catalogue](../03-catalogue/).

## Workflow is a stage list

ADP owns `dataplane.workflows`. The route stores `workflow_id`. AR GETs the published workflow at hydrate.

A stage is a named step: `id`, optional `tool`, `llm_role`. Catalogue also stores `branch`, `type=human_gate`. Runtime does not execute those last two. `kyc_onboarding` names both; AR still walks the tool list in order.

With a manifest, ACR hydrates every capability; the workflow only stamps `llm_role` (and prompt text) onto matching tools. Graph order is **manifest order**. Without a manifest, `agent-runtime/app/agents/hydrate.py` builds one node per stage and `invoke` is empty.

## The graph is linear

`agent-runtime/app/graph/workflow.py` adds one LangGraph node per hydrated tool and wires them `START → n0 → n1 → … → END`. There is no conditional edge.

Stage data that actually moves: [data](data.md). Catalogue vs Runtime: [status](status.md).
