---
title: Autonomy
sidebar_label: Overview
description: "Four autonomy modes. The only question is who picks the next step. Retrieval, memory, tools, and human gates compose around that choice."
---

# Autonomy

`autonomy_mode` answers one question: **who picks the next step**. That is a product decision, not an accident of the model.

The story: [how it hangs together](/how-it-hangs-together). How Runtime hydrates each mode: [autonomy modes](/concepts/executing-a-request/autonomy-modes).

| Mode | Who picks the next step | Typical work |
| --- | --- | --- |
| **0** [Single inference](/autonomy/mode-0-single-inference) | Nobody. One model call. No tools. | Summarise, policy Q&A |
| **1** [Autonomous](/autonomy/mode-1-autonomous) | The model, inside a tool budget | Investigate, look up, fan out |
| **2** [Deterministic](/autonomy/mode-2-deterministic) | The workflow designer | Refund, KYC, any fixed pipeline |
| **3** [Guided](/autonomy/mode-3-guided) | Designer for stages; model inside an allowlist | Triage then draft, counsel-style review |

Every route still calls the model at least once. There is no domain-HTTP-only product. A mode is not a use case — documents, human review, and handoff compose **on top** of these four. See [use cases](/use-cases/).

<div className="gain-diagram-wrap">

![Four autonomy modes. Mode 0 nobody. Mode 1 the model inside a budget. Mode 2 the designer. Mode 3 the designer outside and a named allowlist inside.](/diagrams/autonomy-who-picks.svg)

</div>

## What this means in the room

- Mode 0 is a governed completion. Use it when there is nothing to invoke.
- Mode 1 is a bounded investigation. Use it when the path is not known in advance, and a budget is the control.
- Mode 2 is a process. Use it when the business already knows the stages, including a [human gate](/use-cases/human-review-process-gate).
- Mode 3 is a process with a short leash inside a stage. Use it when the outer order must be fixed and the inner choice must still be named.

Two runs of Mode 1 with the same goal may take different paths. Two runs of Mode 2 must not.

## Attachments, not extra modes {#orthogonal-attachments}

These sit on the route beside `autonomy_mode`. Combining them is a **composition**, not a fifth pattern.

| Attachment | When omitted | When on |
| --- | --- | --- |
| Retrieval | No index | Pack a corpus before generate, or call a retrieve tool |
| Memory | One-shot | Session conversation and working notes |
| Tools | Mode 0, or a Mode 2 LLM-only pipeline | Published capabilities on a manifest |
| Workflow | Mode 0 and 1 | Required on Mode 2 and 3 |
| Ingress | — | Jobs or chat. Not a mode. |

Treat memory as **omit versus session**. Do not explode conversation × working × loop × long-term into sixteen products.

## Illegal combinations

| Combination | Why |
| --- | --- |
| Mode 0 + manifest | Single inference never calls a domain API |
| Mode 0 + workflow | One call has no stage list |
| Mode 0 + retrieve-as-tool | That is a tool |
| Mode 1 + no manifest | The loop has nothing to call |
| Mode 1 + workflow | The model picks the path; a stage list would fight it |
| Mode 2 or 3 without workflow | The designer cannot pick the next step |
| Mode 3 with no tools | An allowlist over an empty set |
| Long-term memory without retrieve | Facts must be recalled, not stuffed into every prompt |
