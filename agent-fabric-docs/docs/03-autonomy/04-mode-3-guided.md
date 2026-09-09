---
title: "Mode 3 — Guided"
sidebar_label: "Mode 3 — Guided"
description: "autonomy_mode 3. The designer fixes the outer stage order; the LLM picks tools inside a stage from that stage's allowlist."
---

import useBaseUrl from '@docusaurus/useBaseUrl';

# Mode 3 — Guided

The **designer picks the stages**; the **LLM picks tools inside a stage** from that stage’s **allowlist**. The route points at a **workflow** (required) and a **manifest** (required). Outer order is fixed. Inner choice is bounded.

This is the hybrid: Pattern 2 on the outside, a small Pattern 1 loop on the inside of each stage that carries an allowlist.

```
START → stage 0 (LLM may CALL tools in allowlist until the stage completes)
      → stage 1 (new allowlist)
      → …
      → END
```

`max_tool_calls` (per stage) caps the inner loop. It is not `max_loop_steps` for the whole run — that budget belongs to [autonomous](/autonomy/mode-1-autonomous).

No-tools guided is not a product: an allowlist over an empty set is Pattern 2 LLM-only, or Pattern 0.

## How it is hooked together

The route row has `autonomy_mode=3`, `prompt_id`, `workflow_id`, and `tool_manifest` (required). Stages that grant inner choice carry an **allowlist** of capability ids. `max_tool_calls` caps that inner loop (per stage), not `max_loop_steps` for the whole run.

```
Front Door POST /v1/runs
        │
        ▼
   pin  route_id + route_version     goal immutable
        │
        ▼
   hydrate  ACR hydrates the manifest
            workflow stamps llm_role / llm_prompt AND per-stage allowlist
            outer order = stage list (manifest order + allowlist membership)
            _ensure_llm still appends respond if no classify/synthesis exists
        │
        ▼
   graph    INTENDED: linear outer walk (Pattern 2)
                      + inner build_agent_loop per allowlisted stage
                        (catalog = that stage’s allowlist, cap = max_tool_calls)
            THIS RUNTIME: build_tool_graph only
                      agent-runtime/app/core/agent_core.py  (mode != 1)
                      allowlist is catalogue-only; inner CALL/DONE is not wired
        │
        ▼
   attachments
            prefetch: pack before / as a non-skippable stage
            retrieve: capability on an allowlist (may skip search, not the stage)
            memory: working notes + loop checkpoint for inner loops
            kind=agent: CALL only on stages that list it
            branch / human_gate: designer-owned edges between stages
```

How this binary hydrates: [patterns](/concepts/executing-a-request/autonomy-modes). Gaps: [status](/catalogue/coverage-status). Data channels: HTTP is `dict(goal)`; the LLM reads `notes`. See [data](/concepts/executing-a-request/run-data).

## Swimlane

![Pattern 3 swimlane](/diagrams/pattern-3-swimlane.svg)

Intended: designer owns **outer** stages; the LLM **CALL**s inside an allowlist. This Runtime still walks the Pattern 2 linear graph — the inner loop is catalogue-only. <a href={useBaseUrl('/diagrams/pattern-3-swimlane.html')} target="_blank" rel="noreferrer">Open as a page</a>.

## How the LLM is called

**Intended — two kinds of `llm.complete` on the same run**

| Where | What the model does | System / user |
| --- | --- | --- |
| Stage with no allowlist | Same as Pattern 2 `_run_stage`: `llm_role` is `none` / `query_formulation` / `classify` / `synthesis` | `llm_prompt` for that role; user is `_user_blob` (`goal` + `prior stage outputs`) |
| Stage with an allowlist | Inner `CALL` / `DONE` over **that stage’s** ids only, up to `max_tool_calls` | Same contract as Pattern 1, plus pack `host` (or the stage role text); `Tools:` is the allowlist, not the whole manifest |
| After HTTP-only outer stages | Hydrate still appends `respond` `synthesis` if no classify/synthesis exists yet | Same `_ensure_llm` safety net as Pattern 2 |

The designer picks the next **stage**. The LLM picks the next **tool inside** an allowlisted stage. It cannot jump to a later stage, and it cannot `CALL` a capability that stage did not list.

Prefetch is still packing, not an inner CALL. A retrieve capability on an allowlist **is** an inner CALL (the model may skip it). Mixing allowlisted stages with Pattern 2 stages on one workflow is still Pattern 3 as long as **some** stage grants inner choice.

**This Runtime:** only the Pattern 2 column runs — `llm.complete` per `llm_role` in `_run_stage`, plus appended `respond` when needed. The inner CALL/DONE loop is not built.

Prompt packs: [prompts](/concepts/authoring-a-product/prompts).

## What you may attach

| Attachment | Allowed | Role |
| --- | --- | --- |
| Workflow | required | Stage order + per-stage `allowlist` |
| Manifest | required | Every tool that any allowlist may name |
| Retrieval omit | yes | Inner tools are domain APIs / parsers, not a corpus |
| Retrieval prefetch | yes | App packs `scope` before or as a stage the model cannot skip; later stages still have allowlists |
| Retrieval tool | yes | Retrieve capabilities appear **on an allowlist**. The model may skip search **inside that stage**; it cannot skip the stage itself |
| Memory omit | yes | One-shot guided job |
| Memory session | yes | Conversation, working, loop checkpoint for inner loops; `long_term=retrieve_only` when retrieve exists |
| `kind=agent` | yes | Allowlist may include a child start. The model may propose it only inside that stage |
| `branch` / `human_gate` | yes | Still designer-owned edges between stages |

A stage without an allowlist is a Pattern 2 stage (exactly one tool, or LLM-only). Mixing those with allowlisted stages is still Pattern 3 as long as **some** stage grants inner choice.

## Supported compositions

Retrieval × memory, tools always on. Child start and process control are overlays.

| # | Retrieval | Memory | Product | Seed illustration |
| --- | --- | --- | --- | --- |
| 1 | omit | no | Guided stages, one-shot | not in seed |
| 2 | omit | yes | Guided triage / copilot | `ticket_triage` |
| 3 | prefetch | no | Pack, then guided, one-shot | not in seed |
| 4 | prefetch | yes | Pack, then guided, sticky | `product_explain` |
| 5 | tool | no | Guided retrieve, one-shot | not in seed |
| 6 | tool | yes | Guided review | `narrow_review`, `contract_review`, `due_diligence` |
| 7 | any | usually yes | Inner allowlist may start a child | not in seed |
| 8 | any | usually yes | Guided stages plus `branch` / `human_gate` | not in seed |

---

## 1–2. Guided, no index

Fixed stages such as parse → tag → draft. Inside a stage the model may pick `parse_ticket` vs `tag_intent` only if both are on that stage’s allowlist; it cannot jump to draft before the designer said so.

**1.** One-shot job. No session.

**2.** Session + loop checkpoint for the inner loops. Seed: `ticket_triage` (`parse_ticket`, `tag_intent`, `draft_reply`).

**Use when** the business process is mandated (triage, copilot) but tool order inside a step can vary.

---

## 3–4. Pack, then guided

Prefetch (or a non-skippable pack stage) grounds the run. Later stages keep allowlists.

**Use when** the model must not skip policy/product text, but may choose how to compare or score **after** the pack.

Seed: `product_explain` — prefetch `product-terms`, `fee-schedule`; tools `score_offer`, `compare_options`; chat + session.

---

## 5–6. Guided retrieve

Retrieve tools sit on a stage allowlist. The model may search clause-index, or policy, or both, **inside** that stage, then must move on when the stage completes. It cannot invent a new stage.

**5.** One-shot.

**6.** Review packet with session and long_term. Seed:

- `narrow_review` — one corpus (`clause-index`)
- `contract_review` — `clause-index` and `legal-playbook`
- `due_diligence` — same corpora, policy-first allowlist

**Use when** enterprise review is a mandated sequence (intake → search → score → memo) but search order inside the search stage should flex.

Narrow vs wide allowlists are the same pattern. A smaller allowlist is not a new mode.

---

## 7. Child agent on an allowlist

A `kind=agent` capability may appear only on the stages that are allowed to hand off. The model cannot start KYC from the OCR stage unless that stage lists `start_kyc_onboarding`.

Not in the Pattern 3 seed; Pattern 1 composition 7 is unbounded child start, Pattern 2 composition 12 is a fixed-stage child start.

---

## 8. Guided plus process control

`branch` and `human_gate` still belong to the designer. Inner allowlists do not create new edges. Use when a copilot stage sits in front of a mandatory approval path.

---

## Not guided

| Shape | Where it lives |
| --- | --- |
| One LLM call, no stages | [single-inference](/autonomy/mode-0-single-inference) |
| Model picks the next step for the **whole** run | [autonomous](/autonomy/mode-1-autonomous) |
| No inner choice; every stage names exactly one tool | [deterministic](/autonomy/mode-2-deterministic) |
