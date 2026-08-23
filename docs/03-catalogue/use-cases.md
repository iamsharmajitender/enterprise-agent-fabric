# Teaching use cases

What each Pattern 0–3 cluster is for. Route ids link to [routes.md](routes.md). HTTP tools receive the original job/chat **goal**, not prior-stage JSON — OCR text is **not** posted to `risk_engine`. Dummy `completed` does not prove prefetch, slots, branch, or Shared Memory. Status words: [`../02-understand/status.md`](../02-understand/status.md).

## Pattern 0 — single inference

One model reply, no tools. [`agent-chat`](routes.md#agent-chat) is a greeting. [`chat_session`](routes.md#chat_session) names session conversation memory (catalogue-only until Shared Memory exists). [`email_summarize`](routes.md#email_summarize) turns a pasted email into banker bullets. [`agent-policy-qa`](routes.md#agent-policy-qa) and [`policy_chat`](routes.md#policy_chat) are handbook questions the catalogue pretends to ground in `policy-engine`; prefetch is **not packed**.

## Pattern 1 — autonomous

Open lookup loops. [`search_only`](routes.md#search_only) is one web search. [`research_assistant`](routes.md#research_assistant) may search, fetch, note, and draft. [`fee_explain`](routes.md#fee_explain) answers “why was I charged?” via `account_fee_lookup`. [`fraud_one_tool`](routes.md#fraud_one_tool) drafts a memo after a named accounts prefetch (not packed). [`fraud_casefile`](routes.md#fraud_casefile) and [`contract_investigation`](routes.md#contract_investigation) chain OCR, retrieve/score, and memo — each HTTP call still sees goal ids, not extracted clause text. [`fraud_investigate`](routes.md#fraud_investigate) and [`ops_start_kyc`](routes.md#ops_start_kyc) name an `agent` tool (`start_contract_review` → `contract_review`, `start_kyc_onboarding` → `kyc_onboarding`). Those are separate catalogue products; Runtime does not POST child jobs yet.

## Pattern 2 — deterministic

Fixed pipelines. [`llm_pipeline`](routes.md#llm_pipeline) is extract → rewrite → format. [`policy_memo`](routes.md#policy_memo) is prefetch-then-generate (`topic`); prefetch not packed. [`account_notify`](routes.md#account_notify) / [`pack_then_notify`](routes.md#pack_then_notify) send notify. [`card_freeze`](routes.md#card_freeze) / [`pack_then_freeze`](routes.md#pack_then_freeze) are identity → limits → freeze. [`dispute_intake`](routes.md#dispute_intake) opens a packet. [`clause_lookup`](routes.md#clause_lookup) / [`template_retrieve`](routes.md#template_retrieve) are named retrieve. [`pack_then_review`](routes.md#pack_then_review) and [`msa_risk_review`](routes.md#msa_risk_review) are OCR → retrieve → score → memo on `doc_id` — score HTTP does not receive OCR output. [`claims_adjudicate`](routes.md#claims_adjudicate) is the same shape for a claim. [`kyc_onboarding`](routes.md#kyc_onboarding) screens and activates; `branch` and `human_gate` are catalogue-only, so Runtime walks the tool list linearly.

## Pattern 3 — guided

Staged work with an Analyse allowlist the graph does not walk yet. [`ticket_triage`](routes.md#ticket_triage) parses and drafts a reply. [`product_explain`](routes.md#product_explain) explains an offer in chat after naming product-terms prefetch (not packed). [`narrow_review`](routes.md#narrow_review), [`contract_review`](routes.md#contract_review), and [`due_diligence`](routes.md#due_diligence) are counsel review on `doc_id`. Later HTTP stages still get the goal `doc_id`, not OCR JSON.
