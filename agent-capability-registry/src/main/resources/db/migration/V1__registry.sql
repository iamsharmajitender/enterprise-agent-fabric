-- Baseline schema + catalogue seed for database acr.
CREATE SCHEMA IF NOT EXISTS registry;

CREATE TABLE registry.capabilities (
  id TEXT NOT NULL,
  version TEXT NOT NULL,
  kind TEXT NOT NULL,
  description TEXT,
  input_schema JSONB NOT NULL,
  output_schema JSONB,
  invoke JSONB NOT NULL,
  snippet TEXT,
  owner TEXT,
  status TEXT NOT NULL,
  PRIMARY KEY (id, version)
);

CREATE TABLE registry.manifests (
  manifest_id TEXT NOT NULL,
  manifest_version TEXT NOT NULL,
  tools JSONB NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (manifest_id, manifest_version)
);

-- Catalogue capabilities and manifests. Scripts/seed is the operational source of truth.

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
  '{"method":"POST","url":"http://agent-mocks:3010/search/web","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/fetch","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/notes","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/briefs","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/legal/memo","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/ocr/extract","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/legal/risk","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/fees/explain","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/legal/clauses/search","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/legal/playbook/search","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/notify","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/cards/identity","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/cards/limits","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/cards/freeze","auth":"domain-oauth"}'::jsonb,
  NULL,
  'cards',
  'published'
),
(
  'extract_fields',
  '1.0.0',
  'domain',
  'Classify receipt OCR notes into structured receipt JSON. HTTP is unused when llm_role=classify.',
  '{"type":"object","properties":{}}'::jsonb,
  '{"type":"object","description":"Receipt extraction from OCR notes and the goal. Always emit every required key. Use null when a value is not in the notes; do not invent. Set human_review_required when a receipt field is null or confidence is low.","required":["merchant","amount","currency","date","tax","missing_information","confidence","human_review_required","human_review_reason"],"properties":{"merchant":{"type":["string","null"],"minLength":1,"maxLength":120,"description":"Merchant name as printed, or null if missing. Copy from OCR notes; do not invent."},"amount":{"type":["number","null"],"minimum":0,"description":"Total charged, or null if missing. Use the receipt total, not tax alone."},"currency":{"type":["string","null"],"enum":["USD","AUD","EUR","GBP"],"description":"ISO 4217 code when stated, or null if the receipt does not name a currency."},"date":{"type":["string","null"],"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$","description":"Purchase date as YYYY-MM-DD, or null if missing. Convert printed dates to this form."},"tax":{"type":["number","null"],"minimum":0,"description":"Tax amount when printed, or null if not stated. Do not invent."},"missing_information":{"type":"array","items":{"type":"string"},"description":"Property names that are null or too unclear to extract. Empty array if complete."},"confidence":{"type":"number","minimum":0,"maximum":1,"description":"Confidence score from 0 to 1 for the extraction as a whole."},"human_review_required":{"type":"boolean","description":"True when a receipt field is null, confidence is low, or the notes are ambiguous."},"human_review_reason":{"type":["string","null"],"description":"Why review is required, or null when human_review_required is false."}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/receipts/extract","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'match_purchase',
  '1.0.0',
  'domain',
  'Match a purchase on the account ledger.',
  '{"type":"object","required":["account_id","merchant","amount","date"],"properties":{"account_id":{"type":"string"},"doc_id":{"type":"string"},"merchant":{"type":"string"},"amount":{"type":"number"},"date":{"type":"string","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/receipts/match","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'refund_eligibility',
  '1.0.0',
  'domain',
  'Check refund window and duplicate payout rules.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/receipts/eligibility","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'post_refund',
  '1.0.0',
  'domain',
  'Post a refund to the ledger.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/receipts/refund","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'refund_confirm',
  '1.0.0',
  'domain',
  'User-facing refund confirm. HTTP is unused when llm_role=synthesis.',
  '{"type":"object","properties":{}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/receipts/confirm","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'doc_intake',
  '1.0.0',
  'domain',
  'Collect and store onboarding documents.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/docs","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/disputes/open","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/disputes/summarize","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/id-verify","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/sanctions","auth":"domain-oauth"}'::jsonb,
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
  '{"type":"object","required":["risk","text"],"properties":{"risk":{"type":"string","enum":["low","high"]},"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/risk","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/activate","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/tickets/parse","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/tickets/tag","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"http://agent-mocks:3010/tickets/reply","auth":"domain-oauth"}'::jsonb,
  NULL,
  'ops',
  'published'
),
(
  'score_offer',
  '1.0.0',
  'domain',
  'Score a product offer.',
  '{"type":"object","required":["utterance"],"properties":{"utterance":{"type":"string"},"product_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/product/score","auth":"domain-oauth"}'::jsonb,
  NULL,
  'product',
  'published'
),
(
  'compare_options',
  '1.0.0',
  'domain',
  'Compare product options.',
  '{"type":"object","required":["utterance"],"properties":{"utterance":{"type":"string"},"product_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/product/compare","auth":"domain-oauth"}'::jsonb,
  NULL,
  'product',
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
  'purchase_refund', '2026.08.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"extract_fields","capability_id":"extract_fields","capability_version":"1.0.0","pdp_action":"extract_fields","risk_tier":"low"},
    {"name":"match_purchase","capability_id":"match_purchase","capability_version":"1.0.0","pdp_action":"match_purchase","risk_tier":"medium"},
    {"name":"refund_eligibility","capability_id":"refund_eligibility","capability_version":"1.0.0","pdp_action":"refund_eligibility","risk_tier":"medium"},
    {"name":"post_refund","capability_id":"post_refund","capability_version":"1.0.0","pdp_action":"post_refund","risk_tier":"high"},
    {"name":"refund_confirm","capability_id":"refund_confirm","capability_version":"1.0.0","pdp_action":"refund_confirm","risk_tier":"low"}
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
);


INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'kyc_document_verify',
  '1.0.0',
  'domain',
  'Verify identity documents against KYC policy. Not wired to a manifest yet.',
  '{"type":"object","required":["document_id"],"properties":{"document_id":{"type":"string"},"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["verified"],"properties":{"verified":{"type":"boolean"},"reason":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/verify","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
),
(
  'aml_watchlist_screen',
  '1.0.0',
  'domain',
  'Screen a party against AML watchlists. Not wired to a manifest yet.',
  '{"type":"object","required":["party_name"],"properties":{"party_name":{"type":"string"},"jurisdiction":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["hits"],"properties":{"hits":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/aml/screen","auth":"domain-oauth"}'::jsonb,
  NULL,
  'financial-crime',
  'published'
),
(
  'credit_limit_lookup',
  '1.0.0',
  'domain',
  'Look up the entitled credit limit for an account. Not wired to a manifest yet.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["limit"],"properties":{"limit":{"type":"number"},"currency":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/credit/limit","auth":"domain-oauth"}'::jsonb,
  NULL,
  'lending',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;

-- Agent-start capabilities. seed-db.sh also reloads docs/run/scripts.
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
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
),
(
  'extract_case_facts',
  '1.0.0',
  'domain',
  'Extract structured ShopAssist case facts from the customer message.',
  '{"type":"object","required":[],"properties":{"utterance":{"type":"string"},"order_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text","order_id"],"properties":{"text":{"type":"string"},"order_id":{"type":"string"},"customer_id":{"type":"string"},"item_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/extract_case_facts","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'lookup_order',
  '1.0.0',
  'domain',
  'Look up order status, item, price, and damage flags.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"order_id":{"type":"string"},"item_id":{"type":"string"},"price":{"type":"number"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/lookup_order","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'investigate_duplicate_charge',
  '1.0.0',
  'domain',
  'Check whether an order has a duplicate captured charge.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"duplicate_charge_found":{"type":"boolean"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/investigate_duplicate_charge","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'check_return_policy',
  '1.0.0',
  'domain',
  'Check return and refund policy for a ShopAssist case.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"item_id":{"type":"string"},"reason":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"eligible":{"type":"boolean"},"automatic_refund_limit":{"type":"number"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/check_return_policy","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'escalate_to_human',
  '1.0.0',
  'domain',
  'Create a structured human escalation handoff for ShopAssist.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"customer_id":{"type":"string"},"escalation_reason":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"handoff_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/handoff/escalate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'start_order_specialist',
  '1.0.0',
  'agent',
  'Start order/damage specialist as a jobs run and join its result.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"customer_id":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"order_damaged"},"join":true}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'start_billing_specialist',
  '1.0.0',
  'agent',
  'Start billing/duplicate-charge specialist as a jobs run and join its result.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"customer_id":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"billing_duplicate"},"join":true}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'start_policy_specialist',
  '1.0.0',
  'agent',
  'Start policy/refund specialist as a jobs run and join its result.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"item_id":{"type":"string"},"reason":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"policy_refund"},"join":true}'::jsonb,
  NULL,
  'shopassist',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;

INSERT INTO registry.manifests (manifest_id, manifest_version, tools, status) VALUES
(
  'fraud_investigate', '2026.08.1',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"},
    {"name":"start_contract_review","capability_id":"start_contract_review","capability_version":"1.0.0","pdp_action":"start_contract_review","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'ops_start_kyc', '2026.08.1',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"start_kyc_onboarding","capability_id":"start_kyc_onboarding","capability_version":"1.0.0","pdp_action":"start_kyc_onboarding","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'shopassist_case', '2026.08.1',
  $$[
    {"name":"extract_case_facts","capability_id":"extract_case_facts","capability_version":"1.0.0","pdp_action":"extract_case_facts","risk_tier":"low"},
    {"name":"start_order_specialist","capability_id":"start_order_specialist","capability_version":"1.0.0","pdp_action":"start_order_specialist","risk_tier":"medium"},
    {"name":"start_billing_specialist","capability_id":"start_billing_specialist","capability_version":"1.0.0","pdp_action":"start_billing_specialist","risk_tier":"medium"},
    {"name":"start_policy_specialist","capability_id":"start_policy_specialist","capability_version":"1.0.0","pdp_action":"start_policy_specialist","risk_tier":"medium"},
    {"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0","pdp_action":"escalate_to_human","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'order_damaged', '2026.08.1',
  '[{"name":"lookup_order","capability_id":"lookup_order","capability_version":"1.0.0","pdp_action":"lookup_order","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'billing_duplicate', '2026.08.1',
  '[{"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'policy_refund', '2026.08.1',
  '[{"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"}]'::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;
