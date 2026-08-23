# Deterministic (Pattern 2)

The **workflow designer picks the next step**. The route points at a **workflow** (fixed stage list). The LLM does not invent the next stage. It only does the work a stage assigns (`llm_role`).

Manifest is required when any stage is a domain (or agent) tool. Omit the manifest for an LLM-only pipeline.

```
START → stage 0 → stage 1 → … → END
```

Every execution follows the same sequence. Branching, if any, is explicit in the workflow (`branch`, `human_gate`), not inventable by the model.

Prefetch on Pattern 2 is a **named stage** (typically `llm_role=none`, empty invoke on the tool side): pack `scope`, then the next stage generates. That is the same product intent as Pattern 0 prefetch, modeled as a stage list so later HTTP/LLM steps are fixed too.

If there is no `classify` or `synthesis` stage yet (HTTP-only tools, or `query_formulation` without a user-facing answer), hydrate still appends a `respond` `synthesis` node. The product is never domain-HTTP-only.

## How it is hooked together

The route row has `autonomy_mode=2`, `prompt_id`, and `workflow_id`. `tool_manifest` is required when any stage is a domain (or agent) tool; omit it for an LLM-only pipeline.

```
Front Door POST /v1/runs
        │
        ▼
   pin  route_id + route_version     goal never updates
        │
        ▼
   hydrate  agent-runtime/app/agents/hydrate.py
            WITH manifest: ACR hydrates capabilities; graph order = manifest order;
                           workflow only stamps llm_role + llm_prompt onto matching ids
            WITHOUT: one node per workflow stage, invoke {} (LLM-only skips HTTP)
            _ensure_llm: if no classify/synthesis yet, append
                         { id: respond, llm_role: synthesis, llm_prompt: …, invoke: {} }
        │
        ▼
   graph    build_tool_graph     START → n0 → n1 → … → END
            each node = _run_stage(llm_role)
            branch / human_gate stay on the catalogue row (this Runtime walks in order)
        │
        ▼
   attachments as stages, not a fifth mode
            prefetch: named llm_role=none + empty invoke, then the next stage generates
            retrieve-as-tool: stage names tool + corpus; order fixed
            memory: notes across later stages / a later turn
            kind=agent: fixed index, not model-chosen
```

Data that moves: every HTTP body is `dict(goal)`. `query_formulation` then sets `payload["query"]`. LLM stages read `goal` + `notes`. HTTP never reads `notes`. See [data](../02-understand/data.md).

This Runtime: prefetch invoke is empty (no pack); slots do not copy tool JSON into the next HTTP body; `branch` / `human_gate` / child start are not executed. Gaps: [status](../02-understand/status.md).

## Swimlane

![Pattern 2 swimlane](diagrams/pattern-2-swimlane.svg)

Front Door starts. Runtime pins a workflow. Catalogue stamps `llm_role`. Runtime walks a **linear** graph: each stage completes with the LLM or calls domain HTTP. [Open as a page](diagrams/pattern-2-swimlane.html).

## How the LLM is called

The designer does not “call the model.” Each stage’s `llm_role` does. `_run_stage` (`agent-runtime/app/graph/workflow.py`) runs `llm.complete(system, user)` **per LLM stage**, with domain HTTP **between** those calls when the stage has a url.

| `llm_role` | `llm.complete`? | Then |
| --- | --- | --- |
| `none` | No | HTTP if `invoke.url` is set; otherwise no-op (prefetch placeholder) |
| `query_formulation` | Yes — completion becomes `payload["query"]` | Then HTTP with `dict(goal)` plus that query |
| `classify` | Yes — completion appends to `notes` | Skip HTTP even if a url exists |
| `synthesis` | Yes — completion is `result` and appends to `notes` | Skip HTTP |

| Message | Source |
| --- | --- |
| **system** | Stamped `llm_prompt`: `by_llm_role.{role}.text` for that stage’s role. Two synthesis stages share one synthesis template. Workflow-only nodes fall back to `host`. Appended `respond` uses the synthesis template, else `host`, else `_DEFAULT_SYNTHESIS` (“write the answer from goal and prior stage outputs only”). |
| **user** | `_user_blob`: `goal: {…}` plus `prior stage outputs:` (HTTP `text`/`message` and earlier completions). |

Pattern 0 composition 2 vs this pattern’s prefetch-then-generate: both pack then call the model. Pattern 0 is packing **around** one synthesis node. Pattern 2 is an explicit stage list you can extend with more fixed LLM or HTTP stages. Prompt packs: [prompts](../02-understand/prompts.md).

## What you may attach

| Attachment | Allowed | Role |
| --- | --- | --- |
| Workflow | required | Stage order, `llm_role`, optional `tool` / `corpus` |
| Manifest | when there are tools | Capability pins. Graph order is the stage list |
| Retrieval omit | yes | No index |
| Retrieval prefetch | yes | First stage packs `scope`; model cannot skip |
| Retrieval tool | yes | Named retrieve stages (`tool` + `corpus` in `scope`). Order is fixed, so the model cannot skip unless the stage is a `branch` |
| Memory omit | yes | One-shot pipeline |
| Memory session | yes | Later stages / a later turn keep `notes`. `loop=checkpoint` is a crash cursor on a long stage list, not an open tool loop |
| `kind=agent` | yes | A **fixed** stage that starts another product (not LLM-chosen) |
| `branch` / `human_gate` | yes | Deterministic next-stage map / stop for a human. Not an LLM choice |

`query_formulation` on a retrieve stage is an `llm_role`, not a new pattern: the LLM writes `payload.query`, then HTTP runs. `classify` / `synthesis` are LLM-only stages.

## Supported compositions

Two families: **LLM-only** (no manifest) and **with tools**. Same retrieval × memory grid. Process control and child start are overlays.

### LLM-only (no tools)

Same four attachments as [single-inference](single-inference.md), but **N LLM calls in a fixed order**.

| # | Prefetch | Memory | Product | Seed illustration |
| --- | --- | --- | --- | --- |
| 1 | no | no | Fixed LLM stages | `llm_pipeline` |
| 2 | yes | no | Pack, then fixed LLM stages | `policy_memo` |
| 3 | no | yes | Fixed LLM stages, sticky | not in seed |
| 4 | yes | yes | Pack, then fixed LLM stages, sticky | not in seed |

### With tools

| # | Retrieval | Memory | Product | Seed illustration |
| --- | --- | --- | --- | --- |
| 5 | omit | no | Fixed HTTP (+ respond) | `account_notify`, `card_freeze` |
| 6 | omit | yes | Fixed HTTP/LLM, sticky | `dispute_intake` |
| 7 | prefetch | no | Pack, then fixed HTTP | `pack_then_notify`, `pack_then_freeze` |
| 8 | prefetch | yes | Pack, then fixed HTTP/LLM, sticky | `pack_then_review` |
| 9 | tool | no | Fixed retrieve stages | `clause_lookup`, `template_retrieve` |
| 10 | tool | yes | Fixed retrieve + score/memo, sticky | `msa_risk_review`, `claims_adjudicate` |

### Overlays

| # | Overlay | Product | Seed illustration |
| --- | --- | --- | --- |
| 11 | `branch` / `human_gate` | Process control on a fixed pipeline | `kyc_onboarding` |
| 12 | `kind=agent` stage | Fixed child start | not in seed (Pattern 1 has the loop form) |

---

## 1–4. LLM-only pipeline

No domain API. Each stage is `classify` or `synthesis` (and prefetch as `none` when composition 2 or 4).

**1 — `llm_pipeline`.** Extract then rewrite from the previous stage’s notes only. Use when process control matters and tools do not.

**2 — `policy_memo`.** Prefetch `policy-engine`, then draft a memo from packed chunks. Use when retrieve → generate must be a **workflow**, not packing around a single Pattern 0 call.

**3.** Same as 1, with session memory so a later turn or a long job keeps notes.

**4.** Same as 2, with session memory.

Pattern 0 composition 2 vs Pattern 2 composition 2: both prefetch then generate. Pattern 0 is one call with packing around it. Pattern 2 is an explicit stage list you can extend with more fixed LLM (or later HTTP) stages.

---

## 5–6. Fixed HTTP, no index

Stages name domain tools in order (`identity_check` → `limit_check` → `freeze_card`). HTTP bodies are the job `goal`. LLM stages (or the appended `respond`) write the user-facing result from `notes`.

**5.** One-shot write path. Seed: `account_notify`, `card_freeze`.

**6.** Same pipeline, session memory for later stages or a later turn. Seed: `dispute_intake`.

---

## 7–8. Pack, then fixed HTTP

Prefetch stage first (model cannot skip), then the same HTTP chain as 5–6.

**Use when** a write path must be grounded in product terms / playbook **and** the side-effect order is non-negotiable.

Seed: `pack_then_notify`, `pack_then_freeze` (no memory); `pack_then_review` (memory + long_term).

---

## 9–10. Fixed retrieve stages

`retrieval.mode=tool`. Each retrieve stage names `tool` + `corpus` (must be in `scope`). Order is fixed: OCR then clause search then policy search then score then memo cannot be rearranged by the model.

A retrieve stage may be HTTP-only (`llm_role=none`) or `query_formulation` (LLM writes the query, then HTTP).

**9.** One-shot lookup / template retrieve. Seed: `clause_lookup`, `template_retrieve`.

**10.** Full review packet with session + long_term. Seed: `msa_risk_review`, `claims_adjudicate`.

---

## 11. Branch and human gate

Still Pattern 2: the designer wrote the next-stage map. A risk score of `high` goes to `manual_review`; a `human_gate` stage stops for a person. The LLM does not invent those edges.

**Use when** KYC, payments, or claims require an explicit approval path.

Seed: `kyc_onboarding` names both. Side-effect stages stay gated (`requires_approval` / `side_effect` on the stage).

---

## 12. Fixed child start

A workflow stage bound to a `kind=agent` capability starts another product at a **known** point in the pipeline (not when the model feels like it). Parent → child field projection is part of this composition.

Not in the Pattern 2 seed; Pattern 1 compositions 7 is the open-loop form of the same capability kind.

---

## Not deterministic

| Shape | Where it lives |
| --- | --- |
| One LLM call, no stage list | [single-inference](single-inference.md) |
| Model chooses the next tool | [autonomous](autonomous.md) |
| Model chooses tools **inside** a fixed stage | [guided](guided.md) |
