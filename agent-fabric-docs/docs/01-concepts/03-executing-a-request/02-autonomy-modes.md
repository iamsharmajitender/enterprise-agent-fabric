---
title: Autonomy modes
sidebar_label: Autonomy modes
description: "autonomy_mode 0-3 answers one question: who picks the next step. How this binary hydrates each mode."
---

# Autonomy modes

The catalogue seed is autonomy **0–3**. `autonomy_mode` on the route is that integer. Pattern answers **who picks the next step**. Every route still calls the LLM at least once. There is no domain-HTTP-only route.

| Pattern | Mode | What the route points at | What Runtime runs |
| --- | --- | --- | --- |
| 0 Single inference | `0` | Prompt pack. No tools, no workflow | One `synthesis` node from `host` (one LLM call) |
| 1 Autonomous | `1` | Manifest + `max_loop_steps`. No workflow | LLM `CALL` / `ASK` / `DONE` loop. `CALL` runs a domain tool; `ASK` pauses for a customer locator |
| 2 Deterministic | `2` | Workflow required. Manifest when there are tools | Fixed stage list. Mix `none` (HTTP) with `classify` / `query_formulation` / `synthesis`. Hydrate appends a `respond` synthesis node if there is no classify/synthesis stage yet |
| 3 Guided | `3` | Workflow required; stages may carry an allowlist | Same linear graph as Pattern 2. Allowlist is catalogue-only |

Intended compositions (what is possible, including rows not in the seed): [autonomy](/autonomy/). Examples in this binary’s seed: Pattern 0 `email_summarize`; Pattern 1 `fee_explain`; Pattern 2 `llm_pipeline`, `card_freeze`, `policy_memo`. Catalogue matrix: [catalogue](/catalogue/).

Pattern 1/2/3 may call the LLM many times, with domain HTTP **between** those calls. Pattern 0 never calls a domain API.

## Workflow is a stage list

ADP owns `dataplane.workflows`. The route stores `workflow_id`. AR GETs the published workflow at hydrate.

A stage is a named step: `id`, optional `tool`, `llm_role`. Catalogue also stores `branch`, `type=human_gate`. Runtime does not execute those last two. `kyc_onboarding` names both; AR still walks the tool list in order.

With a manifest, ACR hydrates every capability; the workflow only stamps `llm_role` (and prompt text) onto matching tools. Graph order is **manifest order**. Without a manifest, `agent-runtime/app/agents/hydrate.py` builds one node per stage and `invoke` is empty.

## Pattern 0/2/3 are linear; Pattern 1 is a loop

`agent-runtime/app/graph/workflow.py` builds Pattern 0/2/3 as `START → n0 → n1 → … → END`. Pattern 1 is an LLM `CALL` / `DONE` loop over the manifest tools. There is no workflow `branch` edge.

Stage data that actually moves: [data](/concepts/executing-a-request/run-data). Catalogue vs Runtime: [status](/catalogue/coverage-status).
