# Use cases

Intended **caller and process shapes** this fabric will support. Not a dump of seed routes (those live in [03-catalogue](../03-catalogue/)). Not autonomy patterns (those live in [06-patterns](../06-patterns/)).

Add a file here when a new caller or control-flow shape is real. One concern per file. Each page should say: who acts, what the request or stage contract contains, what Runtime sees, and what is out of scope.

Autonomy mode does not change these pages. Jobs vs chat is ingress, not a new use case.

## Files

| File | Concern | Fabric sees |
| --- | --- | --- |
| [files-via-dms](files-via-dms.md) | Objects already in the enterprise DMS | JSON ids, or a short-lived presigned GET |
| [files-bytes-upload](files-bytes-upload.md) | Raw bytes on the channel request | Multipart on Front Door; DMS id on `goal` after mint |
| [human-review-llm-signal](human-review-llm-signal.md) | Classify says a person should look | Structured `human_review_*` on stage output (evidence, not a pause) |
| [human-review-process-gate](human-review-process-gate.md) | Designer stops before a write | `human_gate` → `waiting` → resume packet → `requires_approval` write |

Default for documents is DMS-first ([files-via-dms](files-via-dms.md)). Byte upload is opt-in per route.

Default for risky writes is a process gate ([human-review-process-gate](human-review-process-gate.md)). The LLM signal ([human-review-llm-signal](human-review-llm-signal.md)) feeds the reviewer (or a later `branch`); it does not pause by itself.

## Honest now vs later

Today jobs/chat are JSON. Seed document routes already pass `doc_id` (see [`msa_risk_review`](../03-catalogue/routes.md#msa_risk_review)). Tool-mock does **not** GET the DMS; it returns canned `text`. Presigned URLs, `ingress_files`, and Front Door PUT to DMS are **not** built.

Seed refund/KYC workflows **execute** `human_gate` (pause/resume via `/turns`) and `branch` (slot → next stage). See [human-review-process-gate](human-review-process-gate.md) and [status](../02-understand/status.md).

Stage handoff after ingress: [data](../02-understand/data.md) — `goal`, `slots`, `notes`. Proof checklist: [dataflow-plan D13](../tasks/dataflow-plan.md#verification-checklist-d13).
