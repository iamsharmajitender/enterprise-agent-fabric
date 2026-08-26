# Generic shapes this fabric supports

Domain-agnostic **caller, control-flow, and composition** shapes. Seed routes (`fee_explain`, `purchase_refund`, …) are proofs — not the product list. Autonomy integers live in [06-patterns](../06-patterns/). Seed matrix: [03-catalogue](../03-catalogue/). Runtime vs catalogue: [status](../02-understand/status.md).

Jobs vs chat is **ingress**, not a shape on this page. Autonomy mode does not invent a fifth document or human-review shape.

## Caller and control-flow

Detail pages in this shelf. One concern per file.

| Shape | Concern | Detail | Now |
| --- | --- | --- | --- |
| Document by enterprise id | DMS already holds the object; JSON carries `doc_id` (or short-lived GET) | [files-via-dms](files-via-dms.md) | JSON `doc_id` yes; real DMS GET mocked |
| Document via channel upload | Multipart → Front Door PUT → mint id → same JSON path | [files-bytes-upload](files-bytes-upload.md) | **Not built** (`ingress_files`) |
| Review evidence (no pause) | Classify emits structured `human_review_*` for a later branch or reviewer | [human-review-llm-signal](human-review-llm-signal.md) | Schema + notes yes; slot/`branch` consumers see [status](../02-understand/status.md) |
| In-run process gate | Designer `human_gate` → `waiting` → resume → `requires_approval` write | [human-review-process-gate](human-review-process-gate.md) | Pause/resume **runs** |
| Async human handoff | Domain `escalate_to_human` → ticket id → parent **completed** | [escalate-to-human-handoff](escalate-to-human-handoff.md) | Pattern 1 auto-complete + idempotent re-CALL **runs** |

Default document path: DMS-first. Default risky write: process gate. LLM signal never pauses by itself. Ticket-and-done is not a gate.

## Autonomy product shapes

Who picks the next step. Full contracts: [06-patterns](../06-patterns/).

| Mode | Generic product | Typical work |
| --- | --- | --- |
| **0** — single inference | One LLM reply, no tools | Summarize pasted text, greeting, policy-style chat without HTTP |
| **1** — autonomous loop | LLM `CALL` / `DONE` over a manifest | Lookup Q&A, research, multi-tool investigation, specialist fan-out |
| **2** — deterministic pipeline | Fixed workflow stages | Prefetch → act, OCR → classify → eligibility → write, risk **branch** |
| **3** — guided | Staged path; allowlist named on the route | Triage/draft, counsel-style review (allowlist **catalogue-only** today) |

## Orthogonal attachments

Compose beside `autonomy_mode`. Not new modes. See [patterns README](../06-patterns/README.md#orthogonal-attachments).

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
| Named jobs bind | Caller supplies `route_id`; entitle → pin → run | [todo](../tasks/todo.md) |
| Chat decide | Utterance → route / clarify / abstain (rules + retrieve) | [intent](../tasks/intent-todo.md); Layer ③ LLM fallback deferred |
| Audit evidence chain | Decide → freeze → stages → terminal (incl. waiting) | [audit](../tasks/audit-todo.md) |
| Generic tool failure | Business/technical envelope → retry / observe / escalate / fail_run | [tool-failure](../tasks/tool-failure-todo.md) — in flight |
| Gate SLA timeout | Designer `on_timeout` on `human_gate` | Designed on [process gate](human-review-process-gate.md#review-sla-optional); **not built** |
| Shared Memory | Real `conversation` / `long_term` stores | [future-enhancement](../tasks/future-enhancement.md#shared-memory-conversation-and-long_term) |

## Seed → generic map

| Seed proof | Generic shape |
| --- | --- |
| [`email_summarize`](../03-catalogue/routes.md#email_summarize) | Pattern 0 synthesis |
| [`fee_explain`](../03-catalogue/routes.md#fee_explain) | Pattern 1 lookup loop |
| [`msa_risk_review`](../03-catalogue/routes.md#msa_risk_review) / [`contract_review`](../03-catalogue/routes.md#contract_review) | Doc-id intake → retrieve/score → memo |
| [`purchase_refund`](../03-catalogue/routes.md#purchase_refund) | Extract → LLM signal → **process gate** → write |
| [`kyc_onboarding`](../03-catalogue/routes.md#kyc_onboarding) | Screen → **branch** → gate or activate |
| [`shopassist_case`](../03-catalogue/routes.md#shopassist_case) | Specialist **join** → **async escalate** → complete |
| [`fraud_investigate`](../03-catalogue/routes.md#fraud_investigate) / [`ops_start_kyc`](../03-catalogue/routes.md#ops_start_kyc) | Parent starts **child agent** job |
| [`policy_memo`](../03-catalogue/routes.md#policy_memo) / `pack_then_*` | **Prefetch pack** then act/generate |

## Not on this page

| Topic | Where |
| --- | --- |
| Full Pattern 0–3 contracts and illegal combinations | [06-patterns](../06-patterns/) |
| Active route table and demo paths | [03-catalogue/routes](../03-catalogue/routes.md) |
| What Runtime executes vs catalogue-only | [status](../02-understand/status.md) |
| Stage data (`goal` / `slots` / `notes`) | [data](../02-understand/data.md) |
