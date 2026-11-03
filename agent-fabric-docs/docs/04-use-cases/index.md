---
title: Use cases
sidebar_label: Overview
description: "Documents, human review, and handoff. The shapes the fabric supports, independent of industry."
---

# Use cases

These are the shapes a CIO or Chief Architect actually asks about: a document is already in the enterprise store; a person must approve a write; a bot must hand a case to operations.

Who picks the next step is [autonomy](/autonomy/), not a new shape. Jobs versus chat is ingress, not a new use case. The story: [how it hangs together](/how-it-hangs-together).

## Documents

The fabric does not become a file store.

| Shape | What the business wants | What the fabric sees |
| --- | --- | --- |
| [Files already in the DMS](/use-cases/files-via-dms) | Review the contract that is already filed | A document id, or a short-lived GET |
| [Bytes on the channel](/use-cases/files-bytes-upload) | The user uploaded a PDF in chat | Front Door puts the bytes in the DMS, then starts the run with an id |

Default is DMS-first. Byte upload is opt-in per route. Runtime and the model never keep bytes.

## People in the loop

Three different ideas, often collapsed into “human in the loop.”

| Shape | What the business wants | What the fabric does |
| --- | --- | --- |
| [LLM review signal](/use-cases/human-review-llm-signal) | The model thinks a person should look | Structured evidence. The run does **not** pause. |
| [Process gate](/use-cases/human-review-process-gate) | Do not post the refund until a person says so | The run **stops**. A resume packet continues it. |
| [Escalate to a human](/use-cases/escalate-to-human-handoff) | File a ticket and finish this turn | The parent run **completes**. The human works later, elsewhere. |

Default for a risky write is a process gate. The model’s signal feeds the reviewer; it does not pause by itself. Opening a ticket is not a gate.

## Domain-agnostic index

The control-flow catalogue, seed map, and “now versus later” honesty live on [generic shapes](/use-cases/generic-shapes).
