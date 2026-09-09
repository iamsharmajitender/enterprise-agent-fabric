---
title: Catalogue use cases
sidebar_label: Seed use cases
---

# Catalogue use cases

What each Pattern 0–3 cluster is for. Route ids link to [routes](/catalogue/routes). HTTP tools receive **`goal` ∪ schema-selected slots** where the next `input_schema` declares keys — not unbounded prior JSON. Dummy `completed` is pin/hydrate smoke; dataflow proof: [D13 checklist](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/dataflow-plan.md#verification-checklist-d13). Status words: [coverage status](/catalogue/coverage-status).

## Pattern 0 — single inference

One model reply, no tools. `agent-chat` is a greeting. `chat_session` names session conversation memory (catalogue-only until Shared Memory exists). `email_summarize` turns a pasted email into banker bullets. `agent-policy-qa` and `policy_chat` name `deterministic_prefetch` but have no workflow prefetch stage — pack does not run.

## Pattern 1 — autonomous

Open lookup loops. `search_only` is one web search. `research_assistant` may search, fetch, note, and draft. `fee_explain` answers “why was I charged?” via `account_fee_lookup`. `fraud_one_tool` and `fraud_casefile` name accounts prefetch on the route but Pattern 1 has no prefetch workflow stage. `contract_investigation` chains OCR, retrieve/score, and memo — most hops are still goal ids unless a slot merge is declared on `input_schema`. `fraud_investigate` and `ops_start_kyc` **POST child jobs** via `kind=agent` with projected payload (D10). [`shopassist_case`](/catalogue/routes) ASKs for a locator, looks up the order, then calls billing and policy **domain APIs** (`investigate_duplicate_charge`, `check_return_policy`) before optional `escalate_to_human` (async handoff; parent completes — [escalate-to-human-handoff](/use-cases/escalate-to-human-handoff)).

## Pattern 2 — deterministic

Fixed pipelines. `llm_pipeline` is extract → rewrite → format (notes only). `policy_memo` is prefetch-then-generate (**D7**). `account_notify` / `pack_then_notify` prefetch then notify. `card_freeze` / `pack_then_freeze` are identity → limits → freeze (goal-only HTTP today). `dispute_intake` opens a packet. `purchase_refund` is OCR → classify → **slot merge to match** → eligibility → **human_gate** → refund (**D5** proof). `clause_lookup` / `template_retrieve` use query_formulation. `pack_then_review` and `msa_risk_review` are OCR → retrieve → score → memo — score HTTP does not receive OCR JSON unless schemas declare it. `claims_adjudicate` is the same shape for a claim. `kyc_onboarding` screens and activates; **branch** and **human_gate** execute (D8–D9).

## Pattern 3 — guided

Staged work with an Analyse allowlist the graph does not walk yet (allowlist is catalogue-only). `ticket_triage` parses and drafts a reply. `product_explain` prefetches product terms then explains an offer in chat. `narrow_review`, `contract_review`, and `due_diligence` are counsel review on `doc_id`.
