# Process gate (human pause)

A designer-owned workflow stage **stops the run** before a side-effect write. A person resumes with a structured decision packet. The LLM does not invent this edge.

Use this for KYC activate, refunds, card freeze, or any path where the business write must wait on a person. Pair with an [LLM review signal](human-review-llm-signal.md) when classify/OCR evidence should sit on the reviewer packet — the signal is not the stop.

## Who does what

```
Prior stages  (HTTP and/or classify)
    │  goal immutable; notes / later slots hold evidence
    ▼
Optional branch  (designer map on a slot)
    │  e.g. risk high → manual_review
    │       risk low  → activate_account
    ▼
human_gate stage  (type=human_gate, no tool URL)
    │  status → waiting
    │  no domain HTTP
    │  expose review packet from prior slots + goal
    ▼
Human / ops API
    │  POST resume JSON (approve | reject | overrides)
    ▼
Runtime
    │  write slot manual_review = packet
    │  continue graph
    ▼
requires_approval write  (post_refund / account_activate / freeze_card)
    │  runs only after resume approve
    ▼
Later synthesis / confirm
```

**Who must not open or close the gate:** the model, a classify boolean alone, or Front Door chat clarify. Gate and approval flags live on the **workflow** JSON in Data Plane.

## Workflow contract

```json
[
  { "id": "extract_fields", "tool": "extract_fields", "llm_role": "classify" },
  { "id": "eligibility", "tool": "refund_eligibility", "llm_role": "none" },
  { "id": "manual_review", "type": "human_gate" },
  {
    "id": "post_refund",
    "tool": "post_refund",
    "llm_role": "none",
    "side_effect": true,
    "requires_approval": true
  }
]
```

| Field | Role |
| --- | --- |
| `type=human_gate` | Pause stage. No `tool` / URL. |
| `branch` on a prior stage | Map a **slot** value to the next stage id (e.g. `high` → `manual_review`). |
| `side_effect` + `requires_approval` | Latch on the write: do not invoke until a human packet exists. |

`human_gate` without `requires_approval` on the next write is incomplete. `requires_approval` without a gate does not stop today’s linear Runtime.

Seed illustrations:

| Route | Gate shape |
| --- | --- |
| [`purchase_refund`](../03-catalogue/routes.md#purchase_refund) | Always gate before refund; LLM signal on `extract_fields` |
| [`kyc_onboarding`](../03-catalogue/routes.md#kyc_onboarding) | `branch` on risk → gate or activate |
| [`card_freeze`](../03-catalogue/routes.md#card_freeze) | `requires_approval` on freeze; no gate stage yet |

Patterns: [deterministic](../06-patterns/deterministic.md) overlay 11; [guided](../06-patterns/guided.md) may put a copilot stage in front of the same gate.

## Resume packet

Jobs poll until `status=waiting`, then resume the same `correlation_id`. Prefer Runtime `POST /v1/runs/{id}/turns` with JSON (dataflow D9). Not a free-text chat utterance.

```json
{
  "decision": "approve",
  "overrides": { "amount": 42.5, "merchant": "Acme" },
  "reviewer_id": "ops-17",
  "comment": "Corrected merchant from receipt photo"
}
```

| `decision` | Effect |
| --- | --- |
| `approve` | Write `slots.manual_review`; continue; gated HTTP may run |
| `reject` | Complete or fail closed; **do not** call the write |
| missing / empty | Stay `waiting` |

`overrides` merge into selected slots for the next HTTP body (`goal` stays the original ingress). Validate the assembled body against the write capability `input_schema` (D4a) when that path exists.

## What the human sees

| Consumer | Sees |
| --- | --- |
| Reviewer UI / ops | `goal` + prior slots (extraction, match, eligibility, risk) + LLM `human_review_reason` when present |
| Gated HTTP tool | `goal` ∪ selected slots (including human overrides), not a notes dump |
| Later synthesis | `notes` (and projected human comment if you add it) |

Do not dump the entire `notes` string list into the reviewer or into `post_refund`.

## Request

Ingress is a normal job. The caller does not send the gate decision on start.

```json
{
  "route_id": "purchase_refund",
  "idempotency_key": "job-refund:v1",
  "payload": {
    "doc_id": "dms:receipt-19",
    "account_id": "acc-42",
    "reason": "item damaged"
  }
}
```

Expected lifecycle when Runtime executes gates:

1. Start → stages before the gate run → `status=waiting`, checkpoint at `manual_review`
2. Resume with approve packet → `post_refund` → confirm → `completed`
3. Resume with reject → no refund HTTP → terminal rejected/failed

## Not this use case

| Shape | Where |
| --- | --- |
| Model emits “needs review” without pausing | [human-review-llm-signal](human-review-llm-signal.md) |
| Chat clarify / abstain before a route is pinned | Front Door decide — not an in-run gate |
| Crash continue from `loop=checkpoint` | Dataflow D11 — different resume |
| Human work-item as a third capability `kind` | Not required; gate is a workflow stage until a separate work-item API earns a kind ([capabilities](../02-understand/capabilities.md)) |

## Status

| Piece | Now |
| --- | --- |
| `human_gate` / `branch` / `requires_approval` on seed workflows | Yes. Shown in Control Plane. |
| Runtime pauses at `human_gate` | No. Linear graph; gate stage dropped when the route has a manifest. [status](../02-understand/status.md) |
| Resume merges human packet into slots | No. Dataflow D9 (after slots D3; branch D8 for KYC). |
| Dummy `purchase_refund` completes the refund without a person | Yes today — do not treat green as “gate works.” |

Build toward: hydrate keeps gate nodes → graph sets `waiting` → `/turns` accepts the packet → gated write runs only after approve.
