# LLM review signal

A classify (or score) stage asks the model to say **whether a person should look** and **why**. That is evidence for a reviewer, not a pause. The model writes structured fields onto the stage output; Runtime keeps them on the run. A designer-owned [process gate](human-review-process-gate.md) is what actually stops the write.

Use this when OCR / intake is incomplete, confidence is low, or the notes are ambiguous — and a later human (or a `branch`) needs an explicit flag.

## Who does what

```
Prior stages (e.g. ocr_extract)
    │  notes: OCR text
    ▼
LLM classify  (extract_fields)
    │  output_schema requires:
    │    human_review_required  (boolean)
    │    human_review_reason    (string|null)
    │    + extraction fields, confidence, missing_information
    ▼
Runtime
    │  validate structured completion
    │  append to notes (LLM view)
    │  later: write slot extract_fields = JSON   (dataflow D3)
    ▼
Next stages / reviewer UI
    │  read the flag + reason as evidence
    │  do NOT pause here
```

**Who must not pause the run:** the LLM, `output_schema`, or a boolean alone. Pause belongs on `type=human_gate` ([process gate](human-review-process-gate.md)).

## Capability contract

Put the signal on **`output_schema`** of the classify capability — not on `input_schema`, and not only in prompt text.

```json
{
  "human_review_required": { "type": "boolean" },
  "human_review_reason": {
    "type": ["string", "null"],
    "description": "Why review is required, or null when human_review_required is false."
  }
}
```

List both keys in `required`. Schema description should tell the model when to set the flag (null fields, low confidence, ambiguous notes). Full pattern: [schemas](../02-understand/schemas.md). Seed: [`extract_fields`](../05-reference/capability-extract-fields.json).

| Intent | Schema |
| --- | --- |
| Always emit the key; true when review needed | `boolean` in `required` |
| Reason only when true | `["string","null"]` in `required`; null when false |
| Steer the graph | Do not. Use a workflow `branch` on the slot later (D8). |

## Request / goal

Ingress is unchanged. The caller does not send the review flag.

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

`goal` for the run stays that payload. The signal appears only after the classify stage.

Example classify completion (into `notes` today; into `slots.extract_fields` when slots exist):

```json
{
  "merchant": null,
  "amount": 42.5,
  "currency": "USD",
  "date": "2026-08-01",
  "tax": null,
  "missing_information": ["merchant", "tax"],
  "confidence": 0.41,
  "human_review_required": true,
  "human_review_reason": "merchant missing; low confidence"
}
```

## How it pairs with a gate

| Layer | Role on `purchase_refund` |
| --- | --- |
| LLM signal | `extract_fields` emits the flag + reason |
| Process gate | Workflow stage `manual_review` (`type=human_gate`) always stops before `post_refund` |
| Approval latch | `post_refund` has `requires_approval` |

The flag does **not** open the gate. On an always-gated route it is the **reviewer packet**. On a branched route (KYC-style), a later `branch` may map `true` → `manual_review` and `false` → the write — still by reading a **slot**, not by trusting free prose.

Seed: [`purchase_refund`](../03-catalogue/routes.md#purchase_refund). Patterns: [deterministic](../06-patterns/deterministic.md) (overlay `branch` / `human_gate`).

## Not this use case

| Shape | Where |
| --- | --- |
| Pause / resume / approve a write | [human-review-process-gate](human-review-process-gate.md) |
| Synthesis “summarize for a human; do not recommend” | Prompt-only assist; not a structured signal |
| HTTP tool inventing `human_review_required` | Domain JSON may have its own risk field; put `branch` on that slot instead |
| Chat clarify / abstain | Front Door decide outcomes — not a run gate |

## Status

| Piece | Now |
| --- | --- |
| `output_schema` fields on `extract_fields` | Yes. Bound on classify in Runtime. |
| Validated JSON in `notes` | Yes (string form of the completion). |
| Slot `extract_fields` for branch / reviewer UI | No. Dataflow D3. |
| Branch on `human_review_required` | No. Catalogue may name `branch`; Runtime is linear. See [status](../02-understand/status.md). |
| Auto-pause when flag is true | Never planned. Gate stages only. |
| Review SLA / due-by clock | Not on this signal. Optional on [`human_gate`](human-review-process-gate.md#review-sla-optional) (`fail` / `reject` / `escalate` / rare `approve`). |
