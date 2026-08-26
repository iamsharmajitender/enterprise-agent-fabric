# Catalogue use cases

What each Pattern 0–3 cluster is for. Route ids link to [routes.md](routes.md). HTTP tools receive **`goal` ∪ schema-selected slots** where the next `input_schema` declares keys — not unbounded prior JSON. Dummy `completed` is pin/hydrate smoke; dataflow proof: [D13 checklist](../tasks/dataflow-plan.md#verification-checklist-d13). Status words: [`../02-understand/status.md`](../02-understand/status.md).

## Pattern 0 — single inference

One model reply, no tools. [`agent-chat`](routes.md#agent-chat) is a greeting. [`chat_session`](routes.md#chat_session) names session conversation memory (catalogue-only until Shared Memory exists). [`email_summarize`](routes.md#email_summarize) turns a pasted email into banker bullets. [`agent-policy-qa`](routes.md#agent-policy-qa) and [`policy_chat`](routes.md#policy_chat) name `deterministic_prefetch` but have no workflow prefetch stage — pack does not run.

## Pattern 1 — autonomous

Open lookup loops. [`search_only`](routes.md#search_only) is one web search. [`research_assistant`](routes.md#research_assistant) may search, fetch, note, and draft. [`fee_explain`](routes.md#fee_explain) answers “why was I charged?” via `account_fee_lookup`. [`fraud_one_tool`](routes.md#fraud_one_tool) and [`fraud_casefile`](routes.md#fraud_casefile) name accounts prefetch on the route but Pattern 1 has no prefetch workflow stage. [`contract_investigation`](routes.md#contract_investigation) chains OCR, retrieve/score, and memo — most hops are still goal ids unless a slot merge is declared on `input_schema`. [`fraud_investigate`](routes.md#fraud_investigate) and [`ops_start_kyc`](routes.md#ops_start_kyc) **POST child jobs** via `kind=agent` with projected payload (D10). [`shopassist_case`](routes.md#shopassist_case) joins order/billing/policy specialists then may `escalate_to_human` (async handoff; parent completes — [escalate-to-human-handoff](../07-usecases/escalate-to-human-handoff.md)).

## Pattern 2 — deterministic

Fixed pipelines. [`llm_pipeline`](routes.md#llm_pipeline) is extract → rewrite → format (notes only). [`policy_memo`](routes.md#policy_memo) is prefetch-then-generate (**D7**). [`account_notify`](routes.md#account_notify) / [`pack_then_notify`](routes.md#pack_then_notify) prefetch then notify. [`card_freeze`](routes.md#card_freeze) / [`pack_then_freeze`](routes.md#pack_then_freeze) are identity → limits → freeze (goal-only HTTP today). [`dispute_intake`](routes.md#dispute_intake) opens a packet. [`purchase_refund`](routes.md#purchase_refund) is OCR → classify → **slot merge to match** → eligibility → **human_gate** → refund (**D5** proof). [`clause_lookup`](routes.md#clause_lookup) / [`template_retrieve`](routes.md#template_retrieve) use query_formulation. [`pack_then_review`](routes.md#pack_then_review) and [`msa_risk_review`](routes.md#msa_risk_review) are OCR → retrieve → score → memo — score HTTP does not receive OCR JSON unless schemas declare it. [`claims_adjudicate`](routes.md#claims_adjudicate) is the same shape for a claim. [`kyc_onboarding`](routes.md#kyc_onboarding) screens and activates; **branch** and **human_gate** execute (D8–D9).

## Pattern 3 — guided

Staged work with an Analyse allowlist the graph does not walk yet (allowlist is catalogue-only). [`ticket_triage`](routes.md#ticket_triage) parses and drafts a reply. [`product_explain`](routes.md#product_explain) prefetches product terms then explains an offer in chat. [`narrow_review`](routes.md#narrow_review), [`contract_review`](routes.md#contract_review), and [`due_diligence`](routes.md#due_diligence) are counsel review on `doc_id`.
