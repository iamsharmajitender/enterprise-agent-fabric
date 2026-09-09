---
title: Generic shapes this fabric supports
sidebar_label: Generic shapes
---

# Generic shapes this fabric supports

Domain-agnostic **caller, control-flow, and composition** shapes. Seed routes (`fee_explain`, `purchase_refund`, …) are proofs — not the product list. Autonomy integers live in [autonomy](/autonomy/). Seed matrix: [catalogue](/catalogue/). Runtime vs catalogue: [status](/catalogue/coverage-status).

Jobs vs chat is **ingress**, not a shape on this page. Autonomy mode does not invent a fifth document or human-review shape.

## Caller and control-flow

Detail pages in this section. One concern per page.

| Shape | Concern | Detail | Now |
| --- | --- | --- | --- |
| Document by enterprise id | DMS already holds the object; JSON carries `doc_id` (or short-lived GET) | [files-via-dms](/use-cases/files-via-dms) | JSON `doc_id` yes; real DMS GET mocked |
| Document via channel upload | Multipart → Front Door PUT → mint id → same JSON path | [files-bytes-upload](/use-cases/files-bytes-upload) | **Not built** (`ingress_files`) |
| Review evidence (no pause) | Classify emits structured `human_review_*` for a later branch or reviewer | [human-review-llm-signal](/use-cases/human-review-llm-signal) | Schema + notes yes; slot/`branch` consumers see [status](/catalogue/coverage-status) |
| In-run process gate | Designer `human_gate` → `waiting` → resume → `requires_approval` write | [human-review-process-gate](/use-cases/human-review-process-gate) | Pause/resume **runs** |
| Async human handoff | Domain `escalate_to_human` → ticket id → parent **completed** | [escalate-to-human-handoff](/use-cases/escalate-to-human-handoff) | Pattern 1 auto-complete + idempotent re-CALL **runs** |

Default document path: DMS-first. Default risky write: process gate. LLM signal never pauses by itself. Ticket-and-done is not a gate.

## Autonomy product shapes

Who picks the next step. Full contracts: [autonomy](/autonomy/).

| Mode | Generic product | Typical work |
| --- | --- | --- |
| **0** — single inference | One LLM reply, no tools | Summarize pasted text, greeting, policy-style chat without HTTP |
| **1** — autonomous loop | LLM `CALL` / `DONE` over a manifest | Lookup Q&A, research, multi-tool investigation, specialist fan-out |
| **2** — deterministic pipeline | Fixed workflow stages | Prefetch → act, OCR → classify → eligibility → write, risk **branch** |
| **3** — guided | Staged path; allowlist named on the route | Triage/draft, counsel-style review (allowlist **catalogue-only** today) |

## Orthogonal attachments

Compose beside `autonomy_mode`. Not new modes. See [patterns README](/autonomy/#orthogonal-attachments).

| Attachment | Generic capability |
| --- | --- |
| Retrieval | Pack corpus before generate, or model/tool `CALL` retrieve |
| Slots / schema handoff | Prior stage JSON → next HTTP only where `input_schema` allows |
| `kind=agent` child | Start another catalogue route as a job (projected payload) |
| Subagent join | Parent waits for specialist(s), then continues |
| Checkpoint resume | Failed run continues from `resume_index` |
| Side-effect latch | `side_effect` + `requires_approval` after a human packet |

## Platform shapes (not separate 07 files)

| Shape | Role | Track |
| --- | --- | --- |
| Named jobs bind | Caller supplies `route_id`; entitle → pin → run | [todo](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/todo.md) |
| Chat decide | Utterance → route / clarify / abstain (rules + retrieve) | [intent](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/intent-todo.md); Layer ③ LLM fallback deferred |
| Audit evidence chain | Decide → freeze → stages → terminal (incl. waiting) | [audit](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/audit-todo.md) |
| Generic tool failure | Business/technical envelope → retry / observe / escalate / fail_run | [tool-failure](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/tool-failure-todo.md) — in flight |
| Gate SLA timeout | Designer `on_timeout` on `human_gate` | Designed on [process gate](/use-cases/human-review-process-gate#review-sla-optional); **not built** |
| Shared Memory | Real `conversation` / `long_term` stores | [future-enhancement](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/future-enhancement.md#shared-memory-conversation-and-long_term) |

## Seed → generic map

| Seed proof | Generic shape |
| --- | --- |
| [`email_summarize`](/catalogue/seed-use-cases) | Pattern 0 synthesis |
| [`fee_explain`](/catalogue/seed-use-cases) | Pattern 1 lookup loop |
| [`msa_risk_review`](/catalogue/seed-use-cases) / [`contract_review`](/catalogue/seed-use-cases) | Doc-id intake → retrieve/score → memo |
| [`purchase_refund`](/catalogue/seed-use-cases) | Extract → LLM signal → **process gate** → write |
| [`kyc_onboarding`](/catalogue/seed-use-cases) | Screen → **branch** → gate or activate |
| [`shopassist_case`](/catalogue/routes) | Locator ASK → domain APIs → **async escalate** → complete |
| [`fraud_investigate`](/catalogue/seed-use-cases) / [`ops_start_kyc`](/catalogue/seed-use-cases) | Parent starts **child agent** job |
| [`policy_memo`](/catalogue/seed-use-cases) / `pack_then_*` | **Prefetch pack** then act/generate |

## Not on this page

| Topic | Where |
| --- | --- |
| Full Pattern 0–3 contracts and illegal combinations | [autonomy](/autonomy/) |
| Active route table and demo paths | [routes](/catalogue/routes) |
| What Runtime executes vs catalogue-only | [status](/catalogue/coverage-status) |
| Stage data (`goal` / `slots` / `notes`) | [data](/concepts/executing-a-request/run-data) |
