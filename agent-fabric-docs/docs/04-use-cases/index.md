---
title: Use cases
sidebar_label: Overview
---

# Use cases

Intended **caller and process shapes** this fabric will support. Not a dump of seed routes (those live in [catalogue](/catalogue/)). Not autonomy patterns (those live in [autonomy](/autonomy/)).

Add a file here when a new caller or control-flow shape is real. One concern per file. Each page should say: who acts, what the request or stage contract contains, what Runtime sees, and what is out of scope.

Autonomy mode does not change these pages. Jobs vs chat is ingress, not a new use case.

**Index of domain-agnostic shapes** (control-flow + autonomy + attachments + seed map): [generic-shapes](/use-cases/generic-shapes).

## Files

| File | Concern | Fabric sees |
| --- | --- | --- |
| [generic-shapes](/use-cases/generic-shapes) | Domain-agnostic index of what EAF supports | Cross-links to these pages, autonomy, catalogue, tasks |
| [files-via-dms](/use-cases/files-via-dms) | Objects already in the enterprise DMS | JSON ids, or a short-lived presigned GET |
| [files-bytes-upload](/use-cases/files-bytes-upload) | Raw bytes on the channel request | Multipart on Front Door; DMS id on `goal` after mint |
| [human-review-llm-signal](/use-cases/human-review-llm-signal) | Classify says a person should look | Structured `human_review_*` on stage output (evidence, not a pause) |
| [human-review-process-gate](/use-cases/human-review-process-gate) | Designer stops before a write | `human_gate` → `waiting` → resume packet → `requires_approval` write |
| [escalate-to-human-handoff](/use-cases/escalate-to-human-handoff) | Bot opens an async ops ticket then finishes | `escalate_to_human` → handoff id → parent **completed** (idempotent re-CALL) |

Default for documents is DMS-first ([files-via-dms](/use-cases/files-via-dms)). Byte upload is opt-in per route.

Default for risky writes is a process gate ([human-review-process-gate](/use-cases/human-review-process-gate)). The LLM signal ([human-review-llm-signal](/use-cases/human-review-llm-signal)) feeds the reviewer (or a later `branch`); it does not pause by itself. For Pattern 1 “file a ticket and end the turn,” use [escalate-to-human-handoff](/use-cases/escalate-to-human-handoff) — that is not a gate.

## Honest now vs later

Today jobs/chat are JSON. Seed document routes already pass `doc_id` (see [`msa_risk_review`](/catalogue/seed-use-cases)). Tool-mock does **not** GET the DMS; it returns canned `text`. Presigned URLs, `ingress_files`, and Front Door PUT to DMS are **not** built.

Seed refund/KYC workflows **execute** `human_gate` (pause/resume via `/turns`) and `branch` (slot → next stage). See [human-review-process-gate](/use-cases/human-review-process-gate) and [status](/catalogue/coverage-status).

Stage handoff after ingress: [data](/concepts/executing-a-request/run-data) — `goal`, `slots`, `notes`. Proof checklist: [dataflow-plan D13](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/dataflow-plan.md#verification-checklist-d13).
