-- One-shot catalogue seed: capabilities + manifests (acr), then catalogue (adp).
-- Run via ./docs/run/scripts/seed-db.sh (deletes first, then loads lifecycle cuts).

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'web_search',
  '1.0.0',
  'domain',
  'Search the public web.',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/search/web","auth":"domain-oauth"}'::jsonb,
  NULL,
  'assistant-platform',
  'published'
),
(
  'fetch_url',
  '1.0.0',
  'domain',
  'Fetch a URL and return text.',
  '{"type":"object","required":["url"],"properties":{"url":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/fetch","auth":"domain-oauth"}'::jsonb,
  NULL,
  'assistant-platform',
  'published'
),
(
  'note_store',
  '1.0.0',
  'domain',
  'Store a research note.',
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/notes","auth":"domain-oauth"}'::jsonb,
  NULL,
  'assistant-platform',
  'published'
),
(
  'draft_brief',
  '1.0.0',
  'domain',
  'Draft a research brief.',
  '{"type":"object","required":["audience"],"properties":{"audience":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/briefs","auth":"domain-oauth"}'::jsonb,
  NULL,
  'assistant-platform',
  'published'
),
(
  'draft_memo',
  '1.0.0',
  'domain',
  'Draft a counsel-ready memo.',
  '{"type":"object","required":["audience"],"properties":{"audience":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/legal/memo","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'ocr_extract',
  '1.2.0',
  'domain',
  'Extract text from a document id.',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL,
  'document-intel',
  'published'
),
(
  'risk_engine',
  '1.0.0',
  'domain',
  'Score risk from extracted clauses.',
  '{"type":"object","required":["score_profile"],"properties":{"score_profile":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/legal/risk","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'account_fee_lookup',
  '1.0.0',
  'domain',
  'Look up why an account was charged a fee.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/fees/explain","auth":"domain-oauth"}'::jsonb,
  NULL,
  'accounts',
  'published'
),
(
  'clause_search',
  '1.0.0',
  'domain',
  'Search extracted text for clause topics.',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/legal/clauses/search","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'policy_search',
  '1.0.0',
  'domain',
  'Search a policy or playbook corpus.',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/legal/playbook/search","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'notify_customer',
  '1.0.0',
  'domain',
  'Send a customer notification.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/notify","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'identity_check',
  '1.0.0',
  'domain',
  'Verify cardholder identity.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/cards/identity","auth":"domain-oauth"}'::jsonb,
  NULL,
  'cards',
  'published'
),
(
  'limit_check',
  '1.0.0',
  'domain',
  'Check product and freeze limits.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/cards/limits","auth":"domain-oauth"}'::jsonb,
  NULL,
  'cards',
  'published'
),
(
  'freeze_card',
  '1.0.0',
  'domain',
  'Freeze a payment card.',
  '{"type":"object","required":["card_id"],"properties":{"card_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/cards/freeze","auth":"domain-oauth"}'::jsonb,
  NULL,
  'cards',
  'published'
),
(
  'doc_intake',
  '1.0.0',
  'domain',
  'Collect and store onboarding documents.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/kyc/docs","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
),
(
  'case_open',
  '1.0.0',
  'domain',
  'Open a dispute case.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/disputes/open","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'packet_summarize',
  '1.0.0',
  'domain',
  'Summarize an intake packet.',
  '{"type":"object","required":["packet_id"],"properties":{"packet_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/disputes/summarize","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'id_verify',
  '1.0.0',
  'domain',
  'Verify identity documents for KYC.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/kyc/id-verify","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
),
(
  'sanctions_api',
  '1.0.0',
  'domain',
  'Screen a customer against sanctions lists.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/kyc/sanctions","auth":"domain-oauth"}'::jsonb,
  NULL,
  'financial-crime',
  'published'
),
(
  'kyc_risk_engine',
  '1.0.0',
  'domain',
  'Score KYC risk as low or high.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/kyc/risk","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
),
(
  'account_activate',
  '1.0.0',
  'domain',
  'Activate a customer account after KYC approvals.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/kyc/activate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
),
(
  'parse_ticket',
  '1.0.0',
  'domain',
  'Parse a support ticket.',
  '{"type":"object","required":["ticket_id"],"properties":{"ticket_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/tickets/parse","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'tag_intent',
  '1.0.0',
  'domain',
  'Tag ticket intent.',
  '{"type":"object","required":["ticket_id"],"properties":{"ticket_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/tickets/tag","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'draft_reply',
  '1.0.0',
  'domain',
  'Draft a ticket reply.',
  '{"type":"object","required":["ticket_id"],"properties":{"ticket_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/tickets/reply","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'score_offer',
  '1.0.0',
  'domain',
  'Score a product offer.',
  '{"type":"object","required":["product_id"],"properties":{"product_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/product/score","auth":"domain-oauth"}'::jsonb,
  NULL,
  'product',
  'published'
),
(
  'compare_options',
  '1.0.0',
  'domain',
  'Compare product options.',
  '{"type":"object","required":["product_id"],"properties":{"product_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/product/compare","auth":"domain-oauth"}'::jsonb,
  NULL,
  'product',
  'published'
),
(
  'start_contract_review',
  '1.0.0',
  'agent',
  'Start governed Legal MSA review as a jobs run.',
  '{"type":"object","required":["document_id"],"properties":{"document_id":{"type":"string"},"matter_id":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"contract_review"}}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'start_kyc_onboarding',
  '1.0.0',
  'agent',
  'Start governed KYC onboarding as a jobs run.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string"},"ticket_id":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"kyc_onboarding"}}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
);

INSERT INTO registry.manifests (manifest_id, manifest_version, tools, status) VALUES
(
  'search_only', '2026.08.1', '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'research_assistant', '2026.08.1', $$[
    {"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"},
    {"name":"fetch_url","capability_id":"fetch_url","capability_version":"1.0.0","pdp_action":"fetch_url","risk_tier":"low"},
    {"name":"note_store","capability_id":"note_store","capability_version":"1.0.0","pdp_action":"note_store","risk_tier":"low"},
    {"name":"draft_brief","capability_id":"draft_brief","capability_version":"1.0.0","pdp_action":"draft_brief","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fraud_one_tool', '2026.08.1', '[{"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]'::jsonb,
  'published'
),
(
  'fraud_casefile', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fee_explain', '2026.08.1', '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'contract_investigate', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'account_notify', '2026.08.1', '[{"name":"notify_customer","capability_id":"notify_customer","capability_version":"1.0.0","pdp_action":"notify_customer","risk_tier":"medium"}]'::jsonb,
  'published'
),
(
  'card_freeze', '2026.08.1', $$[
    {"name":"identity_check","capability_id":"identity_check","capability_version":"1.0.0","pdp_action":"identity_check","risk_tier":"medium"},
    {"name":"limit_check","capability_id":"limit_check","capability_version":"1.0.0","pdp_action":"limit_check","risk_tier":"medium"},
    {"name":"freeze_card","capability_id":"freeze_card","capability_version":"1.0.0","pdp_action":"freeze_card","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'dispute_intake', '2026.08.1', $$[
    {"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
    {"name":"case_open","capability_id":"case_open","capability_version":"1.0.0","pdp_action":"case_open","risk_tier":"medium"},
    {"name":"packet_summarize","capability_id":"packet_summarize","capability_version":"1.0.0","pdp_action":"packet_summarize","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'clause_lookup', '2026.08.1', '[{"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'template_retrieve', '2026.08.1', $$[
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'msa_risk_review', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'kyc_onboarding', '2026.08.1', $$[
    {"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
    {"name":"id_verify","capability_id":"id_verify","capability_version":"1.0.0","pdp_action":"id_verify","risk_tier":"medium"},
    {"name":"sanctions_api","capability_id":"sanctions_api","capability_version":"1.0.0","pdp_action":"sanctions_screen","risk_tier":"high"},
    {"name":"kyc_risk_engine","capability_id":"kyc_risk_engine","capability_version":"1.0.0","pdp_action":"kyc_risk_score","risk_tier":"medium"},
    {"name":"account_activate","capability_id":"account_activate","capability_version":"1.0.0","pdp_action":"account_activate","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'claims_adjudicate', '2026.08.1', $$[
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'ticket_triage', '2026.08.1', $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"tag_intent","capability_id":"tag_intent","capability_version":"1.0.0","pdp_action":"tag_intent","risk_tier":"low"},
    {"name":"draft_reply","capability_id":"draft_reply","capability_version":"1.0.0","pdp_action":"draft_reply","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'product_explain', '2026.08.1', $$[
    {"name":"score_offer","capability_id":"score_offer","capability_version":"1.0.0","pdp_action":"score_offer","risk_tier":"low"},
    {"name":"compare_options","capability_id":"compare_options","capability_version":"1.0.0","pdp_action":"compare_options","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'narrow_review', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'contract_review', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'due_diligence', '2026.08.1', $$[
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'pack_then_review', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fraud_investigate', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"},
    {"name":"start_contract_review","capability_id":"start_contract_review","capability_version":"1.0.0","pdp_action":"start_contract_review","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'ops_start_kyc', '2026.08.1', $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"start_kyc_onboarding","capability_id":"start_kyc_onboarding","capability_version":"1.0.0","pdp_action":"start_kyc_onboarding","risk_tier":"high"}
  ]$$::jsonb,
  'published'
);


\c adp
-- Pattern 0–3 catalogue seed. Safe to re-run after delete-seed-data.sql.

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
  ('product-terms', 'Product terms', 'https://retrieve.internal/v1/search', 'product-terms', 'workload-oauth', 'product', 'published', NULL),
  ('fee-schedule', 'Fee schedule', 'https://retrieve.internal/v1/search', 'fee-schedule', 'workload-oauth', 'product', 'published', NULL)
ON CONFLICT (corpus_id) DO NOTHING;

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'search_only', '2026.08.1', 'One web search tool',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'research_assistant', '2026.08.1', 'Open research tools (no corpus retrieve)',
  $$[
    {"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"},
    {"name":"fetch_url","capability_id":"fetch_url","capability_version":"1.0.0","pdp_action":"fetch_url","risk_tier":"low"},
    {"name":"note_store","capability_id":"note_store","capability_version":"1.0.0","pdp_action":"note_store","risk_tier":"low"},
    {"name":"draft_brief","capability_id":"draft_brief","capability_version":"1.0.0","pdp_action":"draft_brief","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fraud_one_tool', '2026.08.1', 'Draft memo after prefetch',
  '[{"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]'::jsonb,
  'published'
),
(
  'fraud_casefile', '2026.08.1', 'Non-retrieve fraud tools after prefetch',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fee_explain', '2026.08.1', 'One retrieve tool for account fees',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'contract_investigate', '2026.08.1', 'Multiple tools including two retrieve tools',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'account_notify', '2026.08.1', 'One notify tool',
  '[{"name":"notify_customer","capability_id":"notify_customer","capability_version":"1.0.0","pdp_action":"notify_customer","risk_tier":"medium"}]'::jsonb,
  'published'
),
(
  'card_freeze', '2026.08.1', 'Multi-tool card freeze write path',
  $$[
    {"name":"identity_check","capability_id":"identity_check","capability_version":"1.0.0","pdp_action":"identity_check","risk_tier":"medium"},
    {"name":"limit_check","capability_id":"limit_check","capability_version":"1.0.0","pdp_action":"limit_check","risk_tier":"medium"},
    {"name":"freeze_card","capability_id":"freeze_card","capability_version":"1.0.0","pdp_action":"freeze_card","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'dispute_intake', '2026.08.1', 'Multi-tool dispute intake',
  $$[
    {"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
    {"name":"case_open","capability_id":"case_open","capability_version":"1.0.0","pdp_action":"case_open","risk_tier":"medium"},
    {"name":"packet_summarize","capability_id":"packet_summarize","capability_version":"1.0.0","pdp_action":"packet_summarize","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'clause_lookup', '2026.08.1', 'One named retrieve tool',
  '[{"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'template_retrieve', '2026.08.1', 'Two retrieve tools plus score',
  $$[
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'msa_risk_review', '2026.08.1', 'Fixed MSA risk review tools',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'kyc_onboarding', '2026.08.1', 'KYC onboarding tools with gated activation',
  $$[
    {"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
    {"name":"id_verify","capability_id":"id_verify","capability_version":"1.0.0","pdp_action":"id_verify","risk_tier":"medium"},
    {"name":"sanctions_api","capability_id":"sanctions_api","capability_version":"1.0.0","pdp_action":"sanctions_screen","risk_tier":"high"},
    {"name":"kyc_risk_engine","capability_id":"kyc_risk_engine","capability_version":"1.0.0","pdp_action":"kyc_risk_score","risk_tier":"medium"},
    {"name":"account_activate","capability_id":"account_activate","capability_version":"1.0.0","pdp_action":"account_activate","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'claims_adjudicate', '2026.08.1', 'Forced playbook retrieve then named clause retrieve',
  $$[
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'ticket_triage', '2026.08.1', 'Parser and scorer tools, no corpus retrieve',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"tag_intent","capability_id":"tag_intent","capability_version":"1.0.0","pdp_action":"tag_intent","risk_tier":"low"},
    {"name":"draft_reply","capability_id":"draft_reply","capability_version":"1.0.0","pdp_action":"draft_reply","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'product_explain', '2026.08.1', 'Non-retrieve analyse tools after prefetch',
  $$[
    {"name":"score_offer","capability_id":"score_offer","capability_version":"1.0.0","pdp_action":"score_offer","risk_tier":"low"},
    {"name":"compare_options","capability_id":"compare_options","capability_version":"1.0.0","pdp_action":"compare_options","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'narrow_review', '2026.08.1', 'Many tools, one retrieve tool in Analyse',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'contract_review', '2026.08.1', 'Guided contract review with multiple retrieve tools',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'due_diligence', '2026.08.1', 'Forced playbook retrieve then allowlisted retrieve',
  $$[
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'pack_then_review', '2026.08.1', 'Tools after playbook prefetch',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fraud_investigate', '2026.08.1', 'Fraud parent: domain OCR/memo plus Legal agent capability',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"},
    {"name":"start_contract_review","capability_id":"start_contract_review","capability_version":"1.0.0","pdp_action":"start_contract_review","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'ops_start_kyc', '2026.08.1', 'Ops parent: parse ticket plus KYC agent capability',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"start_kyc_onboarding","capability_id":"start_kyc_onboarding","capability_version":"1.0.0","pdp_action":"start_kyc_onboarding","risk_tier":"high"}
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.workflows (workflow_id, workflow_version, description, stages, status) VALUES
(
  'llm_pipeline', '2026.08.1', 'Fixed LLM stages, no tools',
  $$[
    {"id":"extract","llm_role":"classify"},
    {"id":"rewrite","llm_role":"synthesis"},
    {"id":"format","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'policy_memo', '2026.08.1', 'Prefetch then generate, no tools',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"generate","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'account_notify', '2026.08.1', 'One-tool notify',
  '[{"id":"notify","tool":"notify_customer","llm_role":"none"}]'::jsonb, 'published'
),
(
  'card_freeze', '2026.08.1', 'Multi-tool freeze write path',
  $$[
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true}
  ]$$::jsonb, 'published'
),
(
  'dispute_intake', '2026.08.1', 'Multi-tool dispute chain',
  $$[
    {"id":"intake","tool":"doc_intake","llm_role":"none"},
    {"id":"open","tool":"case_open","llm_role":"none"},
    {"id":"summarize","tool":"packet_summarize","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_notify', '2026.08.1', 'Prefetch then one notify tool',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"notify","tool":"notify_customer","llm_role":"none"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_freeze', '2026.08.1', 'Prefetch then freeze tools',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true}
  ]$$::jsonb, 'published'
),
(
  'pack_then_review', '2026.08.1', 'Prefetch playbook then tools then memo',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'clause_lookup', '2026.08.1', 'One named retrieve stage',
  '[{"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"none"}]'::jsonb, 'published'
),
(
  'template_retrieve', '2026.08.1', 'Two named retrieve stages plus score',
  $$[
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"none"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
    {"id":"score","tool":"risk_engine","llm_role":"none"}
  ]$$::jsonb, 'published'
),
(
  'msa_risk_review', '2026.08.1', 'Fixed MSA retrieve stages',
  $$[
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
    {"id":"risk_engine","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'kyc_onboarding', '2026.08.1', 'KYC with branch, human gate, gated activate',
  $$[
    {"id":"collect_docs","tool":"doc_intake"},
    {"id":"identity_check","tool":"id_verify"},
    {"id":"sanctions_screen","tool":"sanctions_api"},
    {"id":"risk_score","tool":"kyc_risk_engine","branch":{"high":"manual_review","low":"activate_account"}},
    {"id":"manual_review","type":"human_gate"},
    {"id":"activate_account","tool":"account_activate","side_effect":true,"requires_approval":true}
  ]$$::jsonb, 'published'
),
(
  'claims_adjudicate', '2026.08.1', 'Forced playbook retrieve then named clause retrieve',
  $$[
    {"id":"pack_playbook","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'ticket_triage', '2026.08.1', 'Fixed stages, flexible non-retrieve tools in Analyse',
  $$[
    {"id":"extract","allowlist":["parse_ticket"],"max_tool_calls":2},
    {"id":"analyse","allowlist":["parse_ticket","tag_intent"],"max_tool_calls":4},
    {"id":"reply","allowlist":["draft_reply"],"max_tool_calls":2}
  ]$$::jsonb, 'published'
),
(
  'product_explain', '2026.08.1', 'Prefetch product terms, no retrieve tools',
  $$[
    {"id":"extract","allowlist":["score_offer"],"max_tool_calls":2},
    {"id":"analyse","allowlist":["score_offer","compare_options"],"max_tool_calls":4},
    {"id":"explain","allowlist":["compare_options"],"max_tool_calls":2}
  ]$$::jsonb, 'published'
),
(
  'narrow_review', '2026.08.1', 'Analyse allowlists one retrieve tool',
  $$[
    {"id":"extract","tool":"ocr_extract","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","risk_engine"],"max_tool_calls":4},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'contract_review', '2026.08.1', 'Analyse allowlists multiple retrieve tools',
  $$[
    {"id":"extract","tool":"ocr_extract","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":6},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'due_diligence', '2026.08.1', 'Forced playbook retrieve then allowlisted retrieve',
  $$[
    {"id":"extract","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":8},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('agent-chat', '2026.08.1', 'Be a concise corporate assistant. No tools.', 'published', 'assistant-platform'),
  ('email_summarize', '2026.08.1', 'Summarize this email for the banker. No tools. Return short bullets.', 'published', 'assistant-platform'),
  ('chat_session', '2026.08.1', 'Continue the conversation. No tools. Do not invent facts.', 'published', 'assistant-platform'),
  ('agent-policy-qa', '2026.08.1', 'Answer from retrieved policy text only. Do not invent policy. Cite chunk ids.', 'published', 'assistant-platform'),
  ('policy_chat', '2026.08.1', 'Answer from prefetched policy chunks. Use session memory. No tools.', 'published', 'assistant-platform'),
  ('search_only', '2026.08.1', 'Research with web_search only. Stop when the budget is exhausted.', 'published', 'assistant-platform'),
  ('research_assistant', '2026.08.1', 'Research using only allowed tools. Prefer primary sources. Stop when the brief is evidence-backed or the budget is exhausted.', 'published', 'assistant-platform'),
  ('fraud_one_tool', '2026.08.1', 'The case file is already in context. Draft a memo with draft_memo only.', 'published', 'fraud-ops'),
  ('fraud_casefile', '2026.08.1', 'The case file is already in context. Use OCR, risk, and draft tools. Do not retrieve corpora.', 'published', 'fraud-ops'),
  ('fee_explain', '2026.08.1', 'You explain account fees. Use the fee lookup tool. Do not invent charges.', 'published', 'assistant-platform'),
  ('contract_investigate', '2026.08.1', 'Investigate the document using only allowed tools. Prefer evidence over speculation. Stop when risk is assessed or budget is exhausted.', 'published', 'legal-agents'),
  ('llm_pipeline', '2026.08.1', 'Do only the current stage. Do not choose the next stage. No tools.', 'published', 'assistant-platform'),
  ('policy_memo', '2026.08.1', 'Draft the memo from prefetched policy only. Do not skip retrieve.', 'published', 'assistant-platform'),
  ('dispute_intake', '2026.08.1', 'Summarize the dispute packet. Do not open extra cases. Do not skip stages.', 'published', 'ops'),
  ('pack_then_review', '2026.08.1', 'The playbook is already packed. Draft the memo from stage outputs only.', 'published', 'legal-agents'),
  ('msa_risk_review', '2026.08.1', 'You are counsel''s MSA risk-review worker. Do only the current stage. Do not choose the next stage. Do not invent tools.', 'published', 'legal-agents'),
  ('kyc_onboarding', '2026.08.1', 'Summarize KYC evidence for a human reviewer. Do not recommend activation. Do not skip stages.', 'published', 'kyc-ops'),
  ('claims_adjudicate', '2026.08.1', 'Formulate the clause query or draft the memo. Do not reorder stages.', 'published', 'claims-ops'),
  ('ticket_triage', '2026.08.1', 'Stay inside the current stage. Inside Analyse pick parser/scorer tools. Do not invent stages.', 'published', 'ops'),
  ('product_explain', '2026.08.1', 'Product terms are already packed. Stay inside the current stage allowlist.', 'published', 'product'),
  ('narrow_review', '2026.08.1', 'Stay inside the current stage. Analyse may use clause_search and risk_engine only.', 'published', 'legal-agents'),
  ('contract_review', '2026.08.1', 'You are counsel''s contract-review worker. Stay inside the current stage. Inside Analyse you may choose among the stage allowlist. Do not invent stages.', 'published', 'legal-agents'),
  ('fraud_investigate', '2026.08.1', 'Investigate the case with OCR and memo tools. You may propose start_contract_review to hand Legal a separate jobs run. Do not invent tools.', 'published', 'fraud-ops'),
  ('ops_start_kyc', '2026.08.1', 'Parse the onboarding ticket. You may propose start_kyc_onboarding to hand KYC a separate jobs run. Do not invent tools.', 'published', 'ops'),
  ('due_diligence', '2026.08.1', 'Extract always retrieves the playbook. Inside Analyse you may retrieve again. Do not invent stages.', 'published', 'legal-agents');

INSERT INTO dataplane.prompt_role_templates (prompt_id, prompt_version, llm_role, task_type, "text") VALUES
  ('llm_pipeline', '2026.08.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.08.1', 'synthesis', 'synthesize', 'Rewrite or format using the previous stage output only.'),
  ('policy_memo', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from prefetched chunks only. Cite chunk ids.'),
  ('dispute_intake', '2026.08.1', 'synthesis', 'synthesize', 'Summarize the dispute packet for a human reviewer. Do not recommend a payout.'),
  ('pack_then_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from packed playbook and stage outputs only.'),
  ('msa_risk_review', '2026.08.1', 'query_formulation', 'plan', 'Write the search query for this stage''s corpus only. Do not pick a different index.'),
  ('msa_risk_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'),
  ('claims_adjudicate', '2026.08.1', 'query_formulation', 'plan', 'Write the clause-index query. Do not skip the forced playbook retrieve.'),
  ('claims_adjudicate', '2026.08.1', 'synthesis', 'synthesize', 'Draft the claims memo from stage outputs only.'),
  ('narrow_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from Analyse outputs only.'),
  ('contract_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'),
  ('due_diligence', '2026.08.1', 'synthesis', 'synthesize', 'Draft the diligence memo from Extract and Analyse outputs only.');

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'agent-chat', '2026.08.1', TRUE, 'active', 'general_chat',
  'One LLM call. Prompt only. Pattern 0 cannot take tools, retrieve tools, or a workflow. No memory, no retrieval.',
  'http://agent-runtime:3008/v1/runs', 'agent-chat', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'agent-chat', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'email_summarize', '2026.08.1', TRUE, 'active', 'summarize_email',
  'One LLM call. Prompt, output schema, eval. No tools, no workflow, no retrieval, no memory. Summarize the pasted email.',
  'http://agent-runtime:3008/v1/runs', 'agent-email-summarize', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'email_summarize', 'exec_bullets', 'email_summarize_golden', 1, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'chat_session', '2026.08.1', TRUE, 'active', 'chat_session',
  'One LLM call per turn with session conversation memory. Still no tools, no retrieve, no workflow. Memory is the only extra artefact.',
  'http://agent-runtime:3008/v1/runs', 'agent-chat-session', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'chat_session', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'agent-policy-qa', '2026.08.1', TRUE, 'active', 'policy_qa',
  'App prefetches policy-engine and product-faq, then one grounded answer. No tools, no retrieve tool, no workflow, no memory.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-qa', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'agent-policy-qa', 'cited_answer', 'policy_qa_golden', 1, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["policy","procedure","handbook"]'::jsonb, 0
),
(
  'policy_chat', '2026.08.1', TRUE, 'active', 'policy_chat',
  'Prefetch of policy-engine plus session memory. Still Pattern 0: one call per turn, no tools, no workflow, no retrieve tool.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-chat', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'policy_chat', 'cited_answer', 'policy_qa_golden', 1, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["policy","handbook"]'::jsonb, 0
),
(
  'search_only', '2026.08.1', TRUE, 'active', 'search_only',
  'Open loop with one tool (web_search). Prompt, memory, max_loop_steps. No workflow. No corpus prefetch and no retrieve tool.',
  'http://agent-runtime:3008/v1/runs', 'agent-search-only', 'search_only', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'search_only', NULL, NULL, 8, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["search","google"]'::jsonb, 1
),
(
  'research_assistant', '2026.08.1', TRUE, 'active', 'research_topic',
  'Open loop with multiple tools (web_search, fetch_url, note_store, draft_brief). Prompt and memory. No workflow. No corpus RAG — tools are not retrieve-from-index.',
  'http://agent-runtime:3008/v1/runs', 'agent-research-assistant', 'research_assistant', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'research_assistant', 'research_brief', 'research_assistant_golden', 16, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["research","sources"]'::jsonb, 1
),
(
  'fraud_one_tool', '2026.08.1', TRUE, 'active', 'fraud_one_tool',
  'Case file is prefetched, then the model may call one non-retrieve tool (draft_memo). Prompt, memory, no workflow. Retrieval.mode is prefetch.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-one-tool', 'fraud_one_tool', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_one_tool', 'risk_memo', NULL, 6, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fraud_casefile', '2026.08.1', TRUE, 'active', 'fraud_casefile',
  'Case file is prefetched, then the model loops across multiple non-retrieve tools (ocr_extract, risk_engine, draft_memo). Prompt, memory, no workflow. No retrieve tool on the manifest.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-casefile', 'fraud_casefile', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_casefile', 'risk_memo', NULL, 10, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fee_explain', '2026.08.1', TRUE, 'active', 'fee_explain',
  'Open loop with one retrieve tool (account_fee_lookup) over accounts. Prompt, memory, max_loop_steps. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', 'fee_explain_golden', 6, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged","charge","42","monthly"]'::jsonb, 1
),
(
  'contract_investigation', '2026.08.1', TRUE, 'active', 'contract_investigate',
  'Open loop with multiple tools including two retrieve tools (ocr_extract, clause_search, policy_search, risk_engine, draft_memo). Tool-mode over clause-index and legal-playbook. Prompt, memory, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-investigate', 'contract_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'contract_investigate', 'risk_memo', 'contract_investigate_golden', 12, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fraud_investigate', '2026.08.1', TRUE, 'active', 'fraud_investigate',
  'Open loop with domain tools plus one agent capability (start_contract_review → contract_review). Two freezes when Runtime posts jobs; today Runtime skips that HTTP. Prompt, memory, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-investigate', 'fraud_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_investigate', 'risk_memo', NULL, 8, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'ops_start_kyc', '2026.08.1', TRUE, 'active', 'ops_start_kyc',
  'Open loop with parse_ticket plus one agent capability (start_kyc_onboarding → kyc_onboarding). Child start is catalogue-only until Runtime posts jobs. Prompt, memory, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-ops-start-kyc', 'ops_start_kyc', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'ops_start_kyc', NULL, NULL, 6, 'clarify',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'llm_pipeline', '2026.08.1', TRUE, 'active', 'llm_pipeline',
  'Fixed LLM stages (extract → rewrite → format). Workflow and prompt only. No tools, no prefetch, no retrieve, no memory.',
  'http://agent-runtime:3008/v1/runs', 'agent-llm-pipeline', NULL, NULL,
  'read_only_standard', 'fast-chat', 'llm_pipeline', 'llm_pipeline', NULL, NULL, NULL, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'policy_memo', '2026.08.1', TRUE, 'active', 'policy_memo',
  'Fixed retrieve-then-generate workflow. App prefetches the corpus; generate uses the prompt. No tools, no retrieve tool, no memory. Model cannot skip prefetch.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-memo', NULL, NULL,
  'read_only_standard', 'reasoning-standard', 'policy_memo', 'policy_memo', 'msa_memo', NULL, NULL, 'clarify',
  '["policy:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'account_notify', '2026.08.1', TRUE, 'active', 'account_notify',
  'Fixed one-tool write (notify_customer). Workflow and manifest. No prompt, no prefetch, no retrieve, no memory. llm_role none.',
  'http://agent-runtime:3008/v1/runs', 'agent-account-notify', 'account_notify', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'account_notify', NULL, NULL, NULL, NULL, 'escalate_human',
  '["notify:send"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'card_freeze', '2026.08.1', TRUE, 'active', 'card_freeze',
  'Fixed multi-tool write: identity_check → limit_check → freeze_card. Workflow and manifest. No prompt, no prefetch, no retrieve, no memory. Freeze is a gated side effect.',
  'http://agent-runtime:3008/v1/runs', 'agent-card-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'card_freeze', NULL, NULL, NULL, NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'dispute_intake', '2026.08.1', TRUE, 'active', 'dispute_intake',
  'Fixed multi-tool dispute chain (doc_intake, case_open, packet_summarize). Workflow, prompt on the packet, memory. No prefetch and no retrieve tool.',
  'http://agent-runtime:3008/v1/runs', 'agent-dispute-intake', 'dispute_intake', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'dispute_intake', 'dispute_intake', NULL, NULL, NULL, 'clarify',
  '["disputes:write"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_notify', '2026.08.1', TRUE, 'active', 'pack_then_notify',
  'Prefetch product/limit policy, then one tool (notify_customer). Workflow, no prompt, no retrieve tool, no memory.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-notify', 'account_notify', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'pack_then_notify', NULL, NULL, NULL, NULL, 'escalate_human',
  '["notify:send"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_freeze', '2026.08.1', TRUE, 'active', 'pack_then_freeze',
  'Prefetch product/limit policy, then multiple tool-only stages (identity_check, limit_check, freeze_card). Workflow, no prompt, no retrieve tool, no memory.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'pack_then_freeze', NULL, NULL, NULL, NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_review', '2026.08.1', TRUE, 'active', 'pack_then_review',
  'Prefetch the playbook, then multiple fixed tools, then an LLM memo. Workflow, prompt on memo, memory. Retrieve is not a tool — mode is prefetch.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-review', 'pack_then_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'pack_then_review', 'pack_then_review', 'msa_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'clause_lookup', '2026.08.1', TRUE, 'active', 'clause_lookup',
  'One named retrieve stage (clause_search) with a templated query. Workflow and one retrieve tool. No prompt, no prefetch, no memory. llm_role none.',
  'http://agent-runtime:3008/v1/runs', 'agent-clause-lookup', 'clause_lookup', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'clause_lookup', NULL, NULL, NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'template_retrieve', '2026.08.1', TRUE, 'active', 'template_retrieve',
  'Two named retrieve stages (clause_search then policy_search) plus score. Multiple retrieve tools, templated queries. Workflow, no prompt, no prefetch, no memory.',
  'http://agent-runtime:3008/v1/runs', 'agent-template-retrieve', 'template_retrieve', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'template_retrieve', NULL, NULL, NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'msa_risk_review', '2026.08.1', TRUE, 'active', 'msa_risk_review',
  'Fixed OCR → clause_search → policy_search → risk_engine → draft_memo. Multiple tools, two of them retrieve. Workflow, prompt on query/memo, memory. No prefetch — retrieve is named stages.',
  'http://agent-runtime:3008/v1/runs', 'agent-msa-risk-review', 'msa_risk_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'msa_risk_review', 'msa_risk_review', 'msa_memo', 'msa_risk_review_golden', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'kyc_onboarding', '2026.08.1', TRUE, 'active', 'kyc_onboard',
  'Fixed KYC: doc_intake, id_verify, sanctions_api, risk, human gate, activate. Multiple tools, tool retrieve over sanctions-lists and kyc-policy. Workflow, prompt on the review packet, memory.',
  'http://agent-runtime:3008/v1/runs', 'agent-kyc-onboarding', 'kyc_onboarding', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'kyc_onboarding', 'kyc_onboarding', 'kyc_result', 'kyc_onboarding_golden', NULL, 'escalate_human',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'claims_adjudicate', '2026.08.1', TRUE, 'active', 'claims_adjudicate',
  'Workflow with multiple tools. First stage always retrieves legal-playbook (forced pack). Later named stage retrieves clause-index. Prompt on memo, memory. One retrieval.mode (tool); prefetch is a designer-forced retrieve stage, not a second mode.',
  'http://agent-runtime:3008/v1/runs', 'agent-claims-adjudicate', 'claims_adjudicate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'claims_adjudicate', 'claims_adjudicate', 'msa_memo', NULL, NULL, 'clarify',
  '["claims:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'ticket_triage', '2026.08.1', TRUE, 'active', 'ticket_triage',
  'Fixed Extract → Analyse → Reply. Multiple allowlisted tools per stage (parse_ticket, tag_intent, draft_reply). Workflow, prompt, memory. No prefetch, no retrieve tool.',
  'http://agent-runtime:3008/v1/runs', 'agent-ticket-triage', 'ticket_triage', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'ticket_triage', 'ticket_triage', NULL, NULL, NULL, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'product_explain', '2026.08.1', TRUE, 'active', 'product_explain',
  'Fixed stages. App prefetches product-terms and fee-schedule. Analyse allowlist is multiple non-retrieve tools (score_offer, compare_options). Workflow, prompt, memory. No retrieve tool.',
  'http://agent-runtime:3008/v1/runs', 'agent-product-explain', 'product_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'product_explain', 'product_explain', NULL, NULL, NULL, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["loan","offer","product"]'::jsonb, 3
),
(
  'narrow_review', '2026.08.1', TRUE, 'active', 'narrow_review',
  'Fixed Extract → Analyse → Report. Multiple tools overall, but Analyse allowlists one retrieve tool (clause_search) plus risk_engine. Workflow, prompt, memory. Tool-mode, stage-scoped. No prefetch.',
  'http://agent-runtime:3008/v1/runs', 'agent-narrow-review', 'narrow_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'narrow_review', 'narrow_review', 'counsel_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'contract_review', '2026.08.1', TRUE, 'active', 'contract_review',
  'Fixed Extract → Analyse → Report. Multiple tools including multiple retrieve tools (clause_search, policy_search, risk_engine). Workflow, prompt, memory, output, eval. Tool-mode, stage-scoped. No prefetch.',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-review', 'contract_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'contract_review', 'contract_review', 'counsel_memo', 'contract_review_golden', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'due_diligence', '2026.08.1', TRUE, 'active', 'due_diligence',
  'Workflow, multiple tools, memory, prompt. Extract always retrieves legal-playbook (forced). Analyse may retrieve again (clause_search, policy_search). One retrieval.mode (tool). This is prefetch-as-a-stage plus retrieve tools.',
  'http://agent-runtime:3008/v1/runs', 'agent-due-diligence', 'due_diligence', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'due_diligence', 'due_diligence', 'counsel_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('agent-policy-qa', '2026.08.1', 'deterministic_prefetch', '["policy-engine","product-faq"]'::jsonb),
  ('policy_chat', '2026.08.1', 'deterministic_prefetch', '["policy-engine"]'::jsonb),
  ('fraud_one_tool', '2026.08.1', 'deterministic_prefetch', '["accounts"]'::jsonb),
  ('fraud_casefile', '2026.08.1', 'deterministic_prefetch', '["accounts"]'::jsonb),
  ('fee_explain', '2026.08.1', 'tool', '["accounts"]'::jsonb),
  ('contract_investigation', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('policy_memo', '2026.08.1', 'deterministic_prefetch', '["policy-engine"]'::jsonb),
  ('pack_then_notify', '2026.08.1', 'deterministic_prefetch', '["product-terms"]'::jsonb),
  ('pack_then_freeze', '2026.08.1', 'deterministic_prefetch', '["product-terms"]'::jsonb),
  ('pack_then_review', '2026.08.1', 'deterministic_prefetch', '["legal-playbook"]'::jsonb),
  ('clause_lookup', '2026.08.1', 'tool', '["clause-index"]'::jsonb),
  ('template_retrieve', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('kyc_onboarding', '2026.08.1', 'tool', '["sanctions-lists","kyc-policy"]'::jsonb),
  ('claims_adjudicate', '2026.08.1', 'tool', '["legal-playbook","clause-index"]'::jsonb),
  ('product_explain', '2026.08.1', 'deterministic_prefetch', '["product-terms","fee-schedule"]'::jsonb),
  ('narrow_review', '2026.08.1', 'tool', '["clause-index"]'::jsonb),
  ('contract_review', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('due_diligence', '2026.08.1', 'tool', '["legal-playbook","clause-index"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('chat_session', '2026.08.1', 'session', 'session', 'none', 'none', 24, '["tenant","user","session"]'::jsonb),
  ('policy_chat', '2026.08.1', 'session', 'session', 'none', 'none', 24, '["tenant","user","session"]'::jsonb),
  ('search_only', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('research_assistant', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fraud_one_tool', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fraud_casefile', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fee_explain', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('contract_investigation', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fraud_investigate', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('ops_start_kyc', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('dispute_intake', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('pack_then_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('kyc_onboarding', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('claims_adjudicate', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('ticket_triage', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('product_explain', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('narrow_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('contract_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('due_diligence', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);
