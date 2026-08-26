# Process gate (human pause)

A designer-owned workflow stage **stops the run** before a side-effect write. A person resumes with a structured decision packet. The LLM does not invent this edge.

Use this for KYC activate, refunds, card freeze, or any path where the business write must wait on a person. Pair with an [LLM review signal](human-review-llm-signal.md) when classify/OCR evidence should sit on the reviewer packet — the signal is not the stop.

**Not this page:** opening an async ops ticket and finishing the Pattern 1 turn (`escalate_to_human`) — see [escalate-to-human-handoff](escalate-to-human-handoff.md). That tool does not set `waiting`.

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

## Review SLA (optional)

The pause can carry a **designer-owned** time window (1 hour, 1 day, 7 days, …). Put it on the **`human_gate` / run**, not on the LLM signal [`human_review_required`](human-review-llm-signal.md). That boolean is evidence only; it does not start a clock.

Sketch (not wired yet):

```json
{
  "id": "manual_review",
  "type": "human_gate",
  "sla": { "after": "24h", "on_timeout": "reject" }
}
```

### Options when the reviewer misses the SLA

Finish the waiting run through the **same resume path** a human would use (`POST /v1/runs/{id}/turns`), or fail the pin — do not invent a separate “expire” API.

| `on_timeout` | Effect at deadline |
| --- | --- |
| `fail` | Fail the run (`reason_code` e.g. `review_sla_exceeded`). No side-effect write. |
| `reject` | Synthetic resume `{ "decision": "reject", "comment": "sla_exceeded" }` — same as human reject; gated write does not run. |
| `escalate` | Fail or reject **and** notify ops (ticket / audit). Still no silent approve. |
| `approve` | Synthetic approve resume — **only** when the product explicitly allows unattended approve (rare for refunds / KYC / freeze). |

**Default for `requires_approval` writes:** `fail` or `reject`. Never silent approve money or account activation.

### How to schedule the deadline

When the run hits `waiting` + `waiting_for=human_gate`, store `review_due_at` (or `sla` + pause time) on the checkpoint and schedule a wake:

| Approach | When |
| --- | --- |
| In-process delayed task | Local / Compose — same idea as subagent join (`_maybe_schedule_subagent_join`): `_schedule_run` + wait until `review_due_at` |
| Durable delayed queue | Prod — Redis / SQS / etc., keyed by `correlation_id` + gate stage |

On fire: reload the pin. If still waiting on that gate → apply `on_timeout`. If a human already resumed → no-op. On human resume before the deadline → cancel the job (or let the wake no-op after a status check).

**Do not:** put the timer on `human_review_required`; block the HTTP thread for hours; treat AFD freeze TTL as review SLA (that is pin storage, not ops due-by).

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
| Runtime pauses at `human_gate` | Yes. `status=waiting`; resume via `/turns`. See [status](../02-understand/status.md). |
| Resume merges human packet into slots | Yes (D9). |
| Gate `sla` / `review_due_at` / timeout wake | **Not built.** Options above are the intended menu; closest scheduler pattern is subagent join. |
| Dummy `purchase_refund` may still complete without a person in some smoke paths | Treat green carefully — pair with a real wait/resume check. |

Build toward: optional `sla` on the gate → checkpoint `review_due_at` → scheduled wake → fail/reject (or rare approve) if still waiting.
