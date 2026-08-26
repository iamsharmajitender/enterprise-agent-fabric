-- Catalogue seed: live Pattern 0–3 rows, plus extra lifecycle cuts for History pages.
-- Run via ./docs/run/scripts/seed-db.sh (deletes first).

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
),
(
  'shopassist_case', '2026.08.1', $$[
    {"name":"extract_case_facts","capability_id":"extract_case_facts","capability_version":"1.0.0","pdp_action":"extract_case_facts","risk_tier":"low"},
    {"name":"start_order_specialist","capability_id":"start_order_specialist","capability_version":"1.0.0","pdp_action":"start_order_specialist","risk_tier":"medium"},
    {"name":"start_billing_specialist","capability_id":"start_billing_specialist","capability_version":"1.0.0","pdp_action":"start_billing_specialist","risk_tier":"medium"},
    {"name":"start_policy_specialist","capability_id":"start_policy_specialist","capability_version":"1.0.0","pdp_action":"start_policy_specialist","risk_tier":"medium"},
    {"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0","pdp_action":"escalate_to_human","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'order_damaged', '2026.08.1', $$[
    {"name":"lookup_order","capability_id":"lookup_order","capability_version":"1.0.0","pdp_action":"lookup_order","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'billing_duplicate', '2026.08.1', $$[
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'policy_refund', '2026.08.1', $$[
    {"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"}
  ]$$::jsonb,
  'published'
);


\c adp
-- Pattern 0–3 catalogue seed. Safe to re-run after delete-seed-data.sql.

-- Flyway baseline corpora: refresh search gateway urls (shared + dedicated hosts).
UPDATE dataplane.corpora SET url = 'http://agent-mocks:3010/v1/search/assistant'
  WHERE corpus_id IN ('policy-engine', 'product-faq', 'accounts');
UPDATE dataplane.corpora SET url = 'http://agent-mocks:3010/v1/search/legal'
  WHERE corpus_id IN ('clause-index', 'legal-playbook');
UPDATE dataplane.corpora SET url = 'http://agent-mocks:3010/v1/search/kyc'
  WHERE corpus_id IN ('sanctions-lists', 'kyc-policy');
UPDATE dataplane.corpora SET url = 'http://agent-mocks:3010/corpora/research-index/search'
  WHERE corpus_id = 'research-index';

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
  ('product-terms', 'Product terms', 'http://agent-mocks:3010/corpora/product-terms/search', 'product-terms', 'workload-oauth', 'product', 'published', NULL),
  ('fee-schedule', 'Fee schedule', 'http://agent-mocks:3010/corpora/fee-schedule/search', 'fee-schedule', 'workload-oauth', 'product', 'published', NULL)
ON CONFLICT (corpus_id) DO UPDATE SET url = EXCLUDED.url;

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
  'purchase_refund', '2026.08.1', 'Receipt refund: OCR, classify JSON, match, eligibility, gated refund, synthesis confirm.',
  $$[
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
),
(
  'shopassist_case', '2026.08.1', 'ShopAssist coordinator: extract facts, optional join specialists, escalate',
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
  'order_damaged', '2026.08.1', 'ShopAssist order/damage specialist',
  '[{"name":"lookup_order","capability_id":"lookup_order","capability_version":"1.0.0","pdp_action":"lookup_order","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'billing_duplicate', '2026.08.1', 'ShopAssist billing/duplicate specialist',
  '[{"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'policy_refund', '2026.08.1', 'ShopAssist policy/refund specialist',
  '[{"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"}]'::jsonb,
  'published'
);

INSERT INTO dataplane.workflows (workflow_id, workflow_version, description, stages, status) VALUES
(
  'llm_pipeline', '2026.08.1', 'Pattern 2: three LLM stages (classify then two synthesis). No domain HTTP.',
  $$[
    {"id":"extract","llm_role":"classify"},
    {"id":"rewrite","llm_role":"synthesis"},
    {"id":"format","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'policy_memo', '2026.08.1', 'Pattern 2: prefetch placeholder then one synthesis call. No domain HTTP.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"generate","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'account_notify', '2026.08.1', 'Pattern 2: one domain HTTP notify, then synthesis confirm.',
  $$[
    {"id":"notify","tool":"notify_customer","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'card_freeze', '2026.08.1', 'Pattern 2: three domain HTTP writes, then synthesis confirm.',
  $$[
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'dispute_intake', '2026.08.1', 'Pattern 2: two domain HTTP steps, then synthesis on the packet.',
  $$[
    {"id":"intake","tool":"doc_intake","llm_role":"none"},
    {"id":"open","tool":"case_open","llm_role":"none"},
    {"id":"summarize","tool":"packet_summarize","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'purchase_refund', '2026.08.1', 'Pattern 2: OCR, classify receipt JSON, match, eligibility, gated refund. human_gate is catalogue-only.',
  $$[
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"extract_fields","tool":"extract_fields","llm_role":"classify"},
    {"id":"match_purchase","tool":"match_purchase","llm_role":"none"},
    {"id":"eligibility","tool":"refund_eligibility","llm_role":"none"},
    {"id":"manual_review","type":"human_gate"},
    {"id":"post_refund","tool":"post_refund","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","tool":"refund_confirm","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_notify', '2026.08.1', 'Pattern 2: prefetch placeholder, domain notify, then synthesis confirm.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"notify","tool":"notify_customer","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_freeze', '2026.08.1', 'Pattern 2: prefetch placeholder, three domain HTTP writes, then synthesis confirm.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_review', '2026.08.1', 'Pattern 2: prefetch placeholder, two domain HTTP tools, then synthesis memo.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'clause_lookup', '2026.08.1', 'Pattern 2: LLM writes the retrieve query, HTTP search, then synthesis.',
  $$[
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'template_retrieve', '2026.08.1', 'Pattern 2: two query_formulation retrieves, HTTP score, then synthesis.',
  $$[
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'msa_risk_review', '2026.08.1', 'Pattern 2: HTTP OCR, two query_formulation retrieves, HTTP score, synthesis memo.',
  $$[
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
    {"id":"risk_engine","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'kyc_onboarding', '2026.08.1', 'Pattern 2: domain HTTP KYC tools then synthesis packet. branch and human_gate are catalogue-only.',
  $$[
    {"id":"collect_docs","tool":"doc_intake","llm_role":"none"},
    {"id":"identity_check","tool":"id_verify","llm_role":"none"},
    {"id":"sanctions_screen","tool":"sanctions_api","llm_role":"none"},
    {"id":"risk_score","tool":"kyc_risk_engine","llm_role":"none","branch":{"high":"manual_review","low":"activate_account"}},
    {"id":"manual_review","type":"human_gate"},
    {"id":"activate_account","tool":"account_activate","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"summarize","llm_role":"synthesis"}
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
  'ticket_triage', '2026.08.1', 'Pattern 3: HTTP parse/tag, then synthesis reply. Stage allowlists are catalogue-only.',
  $$[
    {"id":"extract","tool":"parse_ticket","llm_role":"none","allowlist":["parse_ticket"],"max_tool_calls":2},
    {"id":"analyse","tool":"tag_intent","llm_role":"none","allowlist":["parse_ticket","tag_intent"],"max_tool_calls":4},
    {"id":"reply","tool":"draft_reply","llm_role":"synthesis","allowlist":["draft_reply"],"max_tool_calls":2}
  ]$$::jsonb, 'published'
),
(
  'product_explain', '2026.08.1', 'Pattern 3: prefetch placeholder, HTTP score/compare, then synthesis. Allowlists are catalogue-only.',
  $$[
    {"id":"extract","tool":"score_offer","llm_role":"none","allowlist":["score_offer"],"max_tool_calls":2},
    {"id":"analyse","tool":"compare_options","llm_role":"none","allowlist":["score_offer","compare_options"],"max_tool_calls":4},
    {"id":"explain","llm_role":"synthesis","allowlist":["compare_options"],"max_tool_calls":2}
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
),
(
  'order_damaged', '2026.08.1', 'ShopAssist order specialist: lookup then synthesize findings.',
  $$[
    {"id":"lookup","tool":"lookup_order","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'billing_duplicate', '2026.08.1', 'ShopAssist billing specialist: investigate then synthesize findings.',
  $$[
    {"id":"investigate","tool":"investigate_duplicate_charge","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'policy_refund', '2026.08.1', 'ShopAssist policy specialist: check policy then synthesize findings.',
  $$[
    {"id":"policy","tool":"check_return_policy","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('agent-chat', '2026.08.1', 'Pattern 0. One synthesis turn. Be a concise corporate assistant. No tools.', 'published', 'assistant-platform'),
  ('email_summarize', '2026.08.1', 'Pattern 0. One synthesis turn. Summarize this email for the banker. No tools. Return short bullets.', 'published', 'assistant-platform'),
  ('chat_session', '2026.08.1', 'Pattern 0. One synthesis turn per message. Continue the conversation. No tools. Do not invent facts.', 'published', 'assistant-platform'),
  ('agent-policy-qa', '2026.08.1', 'Pattern 0. One synthesis turn. Answer from retrieved policy text only. Do not invent policy. Cite chunk ids.', 'published', 'assistant-platform'),
  ('policy_chat', '2026.08.1', 'Pattern 0. One synthesis turn. Answer from prefetched policy chunks. Use session memory. No tools.', 'published', 'assistant-platform'),
  ('search_only', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use web_search before DONE when search can answer. Do not invent results.', 'published', 'assistant-platform'),
  ('research_assistant', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use allowed tools. Prefer primary sources. Do not invent tool results.', 'published', 'assistant-platform'),
  ('fraud_one_tool', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. The case file is already in context. CALL draft_memo before DONE.', 'published', 'fraud-ops'),
  ('fraud_casefile', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR, risk, and draft tools. Do not invent tool results.', 'published', 'fraud-ops'),
  ('fee_explain', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. CALL account_fee_lookup before DONE. Do not invent charges. After a tool result, DONE with that output unless another tool is needed.', 'published', 'assistant-platform'),
  ('contract_investigate', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use only allowed tools. Prefer evidence. Do not invent tool results.', 'published', 'legal-agents'),
  ('fraud_investigate', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR and memo tools. You may CALL start_contract_review. Do not invent tools.', 'published', 'fraud-ops'),
  ('ops_start_kyc', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Parse the ticket. You may CALL start_kyc_onboarding. Do not invent tools.', 'published', 'ops'),
  ('shopassist_case', '2026.08.1', 'Pattern 1. You are the ShopAssist coordinator. Reply CALL <tool_id> or DONE <answer>. First CALL extract_case_facts. Then CALL only the specialists needed (start_order_specialist, start_billing_specialist, start_policy_specialist) based on customer issues. After specialist findings, CALL escalate_to_human when refund exceeds auto limits or human review is required. After escalate_to_human succeeds, DONE immediately with a customer-facing summary that includes the handoff id — never CALL escalate_to_human twice. Do not invent tool results. DONE with the customer-facing summary only after required findings are collected.', 'published', 'shopassist'),
  ('order_damaged', '2026.08.1', 'Pattern 2. Order specialist. Do only the current stage. Return damage/order facts only. Do not contact the customer.', 'published', 'shopassist'),
  ('billing_duplicate', '2026.08.1', 'Pattern 2. Billing specialist. Do only the current stage. Return payment facts only. Do not contact the customer.', 'published', 'shopassist'),
  ('policy_refund', '2026.08.1', 'Pattern 2. Policy specialist. Do only the current stage. Return eligibility and limits only. Do not promise refunds.', 'published', 'shopassist'),
  ('llm_pipeline', '2026.08.1', 'Pattern 2. Do only the current stage. Do not choose the next stage. No tools.', 'published', 'assistant-platform'),
  ('policy_memo', '2026.08.1', 'Pattern 2. Do only the current stage. Draft from prefetched policy only.', 'published', 'assistant-platform'),
  ('account_notify', '2026.08.1', 'Pattern 2. Confirm the notify from stage outputs only. Do not invent send status.', 'published', 'ops'),
  ('card_freeze', '2026.08.1', 'Pattern 2. Confirm the freeze from identity, limit, and freeze outputs only. Do not invent card state.', 'published', 'ops'),
  ('dispute_intake', '2026.08.1', 'Pattern 2. Do only the current stage. Do not open extra cases.', 'published', 'ops'),
  ('purchase_refund', '2026.08.1', 'Pattern 2. Do only the current stage. Do not invent a refund. Classify returns JSON only.', 'published', 'ops'),
  ('pack_then_notify', '2026.08.1', 'Pattern 2. Confirm the notify from stage outputs only. Prefetch chunks may be empty.', 'published', 'ops'),
  ('pack_then_freeze', '2026.08.1', 'Pattern 2. Confirm the freeze from stage outputs only. Prefetch chunks may be empty.', 'published', 'ops'),
  ('pack_then_review', '2026.08.1', 'Pattern 2. Do only the current stage. Draft the memo from packed playbook and stage outputs.', 'published', 'legal-agents'),
  ('clause_lookup', '2026.08.1', 'Pattern 2. Do only the current stage. Do not invent clauses.', 'published', 'legal-agents'),
  ('template_retrieve', '2026.08.1', 'Pattern 2. Do only the current stage. Write the query for this stage corpus only, or synthesize from notes.', 'published', 'legal-agents'),
  ('msa_risk_review', '2026.08.1', 'Pattern 2. You are counsel''s MSA risk-review worker. Do only the current stage. Do not invent tools.', 'published', 'legal-agents'),
  ('kyc_onboarding', '2026.08.1', 'Pattern 2. Summarize KYC evidence for a human reviewer. Do not recommend activation.', 'published', 'kyc-ops'),
  ('claims_adjudicate', '2026.08.1', 'Pattern 2. Do only the current stage. Do not reorder stages.', 'published', 'claims-ops'),
  ('ticket_triage', '2026.08.1', 'Pattern 3. Do only the current stage. Draft the reply from parse and tag outputs. Do not invent stages.', 'published', 'ops'),
  ('product_explain', '2026.08.1', 'Pattern 3. Product terms may already be packed. Explain from score and compare outputs only.', 'published', 'product'),
  ('narrow_review', '2026.08.1', 'Pattern 3. Do only the current stage. Analyse may use clause_search and risk_engine only.', 'published', 'legal-agents'),
  ('contract_review', '2026.08.1', 'Pattern 3. Stay inside the current stage. Analyse may choose among the stage allowlist. Do not invent stages.', 'published', 'legal-agents'),
  ('due_diligence', '2026.08.1', 'Pattern 3. Extract always retrieves the playbook. Analyse may retrieve again. Do not invent stages.', 'published', 'legal-agents');

INSERT INTO dataplane.prompt_role_templates (prompt_id, prompt_version, llm_role, task_type, "text") VALUES
  ('order_damaged', '2026.08.1', 'synthesis', 'synthesize', 'Summarize order and damage facts from the lookup tool only. Do not invent evidence.'),
  ('billing_duplicate', '2026.08.1', 'synthesis', 'synthesize', 'Summarize payment/duplicate findings from the investigate tool only. Do not invent captures.'),
  ('policy_refund', '2026.08.1', 'synthesis', 'synthesize', 'State eligibility, auto refund limit, and recommended next step from the policy tool only. Do not promise a payout.'),
  ('llm_pipeline', '2026.08.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.08.1', 'synthesis', 'synthesize', 'Rewrite or format using the previous stage output only.'),
  ('policy_memo', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from prefetched chunks only. Cite chunk ids.'),
  ('account_notify', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from the notify tool output only.'),
  ('card_freeze', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from identity, limit, and freeze outputs only.'),
  ('dispute_intake', '2026.08.1', 'synthesis', 'synthesize', 'Summarize the dispute packet for a human reviewer. Do not recommend a payout.'),
  ('purchase_refund', '2026.08.1', 'classify', 'classify', 'Extract receipt fields from OCR notes and the goal only. Always emit every output_schema key. Use null when a value is not in the notes; do not invent.'),
  ('purchase_refund', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing refund confirm from match, eligibility, and refund outputs only. Do not invent a payout.'),
  ('pack_then_notify', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from the notify tool output only.'),
  ('pack_then_freeze', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from freeze-path stage outputs only.'),
  ('pack_then_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from packed playbook and stage outputs only.'),
  ('clause_lookup', '2026.08.1', 'query_formulation', 'plan', 'Write the clause-index query from the goal only.'),
  ('clause_lookup', '2026.08.1', 'synthesis', 'synthesize', 'Explain the retrieved clause in plain language. Do not invent text that is not in notes.'),
  ('template_retrieve', '2026.08.1', 'query_formulation', 'plan', 'Write the search query for this stage''s corpus only. Do not pick a different index.'),
  ('template_retrieve', '2026.08.1', 'synthesis', 'synthesize', 'Summarize retrieved clauses, playbook hits, and the score. Do not invent sources.'),
  ('msa_risk_review', '2026.08.1', 'query_formulation', 'plan', 'Write the search query for this stage''s corpus only. Do not pick a different index.'),
  ('msa_risk_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'),
  ('kyc_onboarding', '2026.08.1', 'synthesis', 'synthesize', 'Summarize KYC stage outputs for a human reviewer. Do not recommend activation.'),
  ('claims_adjudicate', '2026.08.1', 'query_formulation', 'plan', 'Write the clause-index query. Do not skip the forced playbook retrieve.'),
  ('claims_adjudicate', '2026.08.1', 'synthesis', 'synthesize', 'Draft the claims memo from stage outputs only.'),
  ('ticket_triage', '2026.08.1', 'synthesis', 'synthesize', 'Draft the customer reply from parse and tag outputs only.'),
  ('product_explain', '2026.08.1', 'synthesis', 'synthesize', 'Explain the offer from score and compare outputs only. Do not invent rates.'),
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
  'Pattern 0 (single inference): one LLM call from host. No tools, no workflow, no memory, no retrieval.',
  'http://agent-runtime:3008/v1/runs', 'agent-chat', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'agent-chat', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'email_summarize', '2026.08.1', TRUE, 'active', 'summarize_email',
  'Pattern 0 (single inference): one LLM call from host. Summarize the pasted email. Prompt plus output schema. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-email-summarize', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'email_summarize', 'exec_bullets', 'email_summarize_golden', 1, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'chat_session', '2026.08.1', TRUE, 'active', 'chat_session',
  'Pattern 0 (single inference): one LLM call per turn from host. Session conversation memory. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-chat-session', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'chat_session', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'agent-policy-qa', '2026.08.1', TRUE, 'active', 'policy_qa',
  'Pattern 0 (single inference): one LLM call from host after catalogue prefetch of policy-engine and product-faq. Prefetch is not packed today. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-qa', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'agent-policy-qa', 'cited_answer', 'policy_qa_golden', 1, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["policy","procedure","handbook"]'::jsonb, 0
),
(
  'policy_chat', '2026.08.1', TRUE, 'active', 'policy_chat',
  'Pattern 0 (single inference): one LLM call per turn from host. Catalogue prefetch of policy-engine plus session memory. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-chat', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'policy_chat', 'cited_answer', 'policy_qa_golden', 1, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["policy","handbook"]'::jsonb, 0
),
(
  'search_only', '2026.08.1', TRUE, 'active', 'search_only',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over web_search, up to max_loop_steps. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-search-only', 'search_only', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'search_only', NULL, NULL, 8, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["search","google"]'::jsonb, 1
),
(
  'research_assistant', '2026.08.1', TRUE, 'active', 'research_topic',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over web_search, fetch_url, note_store, draft_brief. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-research-assistant', 'research_assistant', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'research_assistant', 'research_brief', 'research_assistant_golden', 16, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["research","sources"]'::jsonb, 1
),
(
  'fraud_one_tool', '2026.08.1', TRUE, 'active', 'fraud_one_tool',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over draft_memo after catalogue prefetch of accounts. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-one-tool', 'fraud_one_tool', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_one_tool', 'risk_memo', NULL, 6, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fraud_casefile', '2026.08.1', TRUE, 'active', 'fraud_casefile',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, risk_engine, draft_memo after catalogue prefetch. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-casefile', 'fraud_casefile', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_casefile', 'risk_memo', NULL, 10, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fee_explain', '2026.08.1', TRUE, 'active', 'fee_explain',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over account_fee_lookup. One host prompt reused each turn. Domain HTTP only on CALL. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', 'fee_explain_golden', 6, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged","charge","42","monthly"]'::jsonb, 1
),
(
  'contract_investigation', '2026.08.1', TRUE, 'active', 'contract_investigate',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, clause_search, policy_search, risk_engine, draft_memo. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-investigate', 'contract_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'contract_investigate', 'risk_memo', 'contract_investigate_golden', 12, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fraud_investigate', '2026.08.1', TRUE, 'active', 'fraud_investigate',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, draft_memo, start_contract_review. One host prompt reused each turn. kind=agent child start is catalogue-only. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-investigate', 'fraud_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_investigate', 'risk_memo', NULL, 8, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'ops_start_kyc', '2026.08.1', TRUE, 'active', 'ops_start_kyc',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over parse_ticket and start_kyc_onboarding. One host prompt reused each turn. kind=agent child start is catalogue-only. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-ops-start-kyc', 'ops_start_kyc', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'ops_start_kyc', NULL, NULL, 6, 'clarify',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'shopassist_case', '2026.08.1', TRUE, 'active', 'shopassist_case',
  'Pattern 1 (autonomous): ShopAssist coordinator. CALL extract_case_facts then optional join specialists (order/billing/policy). Escalate when needed.',
  'http://agent-runtime:3008/v1/runs', 'agent-shopassist-case', 'shopassist_case', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'shopassist_case', NULL, NULL, 12, 'clarify',
  '["support:case"]'::jsonb, '["web","api"]'::jsonb, TRUE, '["damaged","damage","refund","jacket","charged twice","duplicate charge","ORD-77819"]'::jsonb, 1
),
(
  'order_damaged', '2026.08.1', TRUE, 'active', 'order_damaged',
  'Pattern 2 (deterministic): ShopAssist order/damage specialist. lookup_order then synthesis.',
  'http://agent-runtime:3008/v1/runs', 'agent-order-damaged', 'order_damaged', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'order_damaged', 'order_damaged', NULL, NULL, NULL, 'clarify',
  '["support:case"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'billing_duplicate', '2026.08.1', TRUE, 'active', 'billing_duplicate',
  'Pattern 2 (deterministic): ShopAssist billing specialist. investigate_duplicate_charge then synthesis.',
  'http://agent-runtime:3008/v1/runs', 'agent-billing-duplicate', 'billing_duplicate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'billing_duplicate', 'billing_duplicate', NULL, NULL, NULL, 'clarify',
  '["support:case"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'policy_refund', '2026.08.1', TRUE, 'active', 'policy_refund',
  'Pattern 2 (deterministic): ShopAssist policy specialist. check_return_policy then synthesis.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-refund', 'policy_refund', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'policy_refund', 'policy_refund', NULL, NULL, NULL, 'clarify',
  '["support:case"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'llm_pipeline', '2026.08.1', TRUE, 'active', 'llm_pipeline',
  'Pattern 2 (deterministic): fixed workflow of three LLM stages. Prompts: host plus classify and synthesis templates. No domain HTTP.',
  'http://agent-runtime:3008/v1/runs', 'agent-llm-pipeline', NULL, NULL,
  'read_only_standard', 'fast-chat', 'llm_pipeline', 'llm_pipeline', NULL, 'llm_pipeline_tools', NULL, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'policy_memo', '2026.08.1', TRUE, 'active', 'policy_memo',
  'Pattern 2 (deterministic): prefetch placeholder then one synthesis call. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-memo', NULL, NULL,
  'read_only_standard', 'reasoning-standard', 'policy_memo', 'policy_memo', 'msa_memo', 'policy_memo_tools', NULL, 'clarify',
  '["policy:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'account_notify', '2026.08.1', TRUE, 'active', 'account_notify',
  'Pattern 2 (deterministic): domain HTTP notify_customer, then synthesis confirm. Prompts: host plus synthesis template.',
  'http://agent-runtime:3008/v1/runs', 'agent-account-notify', 'account_notify', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'account_notify', 'account_notify', NULL, 'account_notify_tools', NULL, 'escalate_human',
  '["notify:send"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'card_freeze', '2026.08.1', TRUE, 'active', 'card_freeze',
  'Pattern 2 (deterministic): domain HTTP identity_check, limit_check, freeze_card, then synthesis confirm. Prompts: host plus synthesis template. Freeze remains a gated side effect in catalogue.',
  'http://agent-runtime:3008/v1/runs', 'agent-card-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'card_freeze', 'card_freeze', NULL, 'card_freeze_tools', NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'dispute_intake', '2026.08.1', TRUE, 'active', 'dispute_intake',
  'Pattern 2 (deterministic): two domain HTTP steps then synthesis on packet_summarize. Prompts: host plus synthesis template.',
  'http://agent-runtime:3008/v1/runs', 'agent-dispute-intake', 'dispute_intake', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'dispute_intake', 'dispute_intake', NULL, 'dispute_intake_tools', NULL, 'clarify',
  '["disputes:write"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'purchase_refund', '2026.08.1', TRUE, 'active', 'purchase_refund',
  'Pattern 2 (deterministic): HTTP OCR, classify receipt JSON, HTTP match and eligibility, gated refund, synthesis confirm. output_schema_id receipt_fields is not enforced. human_gate is catalogue-only. HTTP stays goal-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-purchase-refund', 'purchase_refund', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'purchase_refund', 'purchase_refund', 'receipt_fields', 'purchase_refund_tools', NULL, 'escalate_human',
  '["refunds:write"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_notify', '2026.08.1', TRUE, 'active', 'pack_then_notify',
  'Pattern 2 (deterministic): prefetch placeholder, domain HTTP notify, then synthesis confirm. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-notify', 'account_notify', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'pack_then_notify', 'pack_then_notify', NULL, 'pack_then_notify_tools', NULL, 'escalate_human',
  '["notify:send"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_freeze', '2026.08.1', TRUE, 'active', 'pack_then_freeze',
  'Pattern 2 (deterministic): prefetch placeholder, three domain HTTP writes, then synthesis confirm. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'pack_then_freeze', 'pack_then_freeze', NULL, 'pack_then_freeze_tools', NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_review', '2026.08.1', TRUE, 'active', 'pack_then_review',
  'Pattern 2 (deterministic): prefetch placeholder, two domain HTTP tools, then synthesis memo. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-review', 'pack_then_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'pack_then_review', 'pack_then_review', 'msa_memo', 'pack_then_review_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'clause_lookup', '2026.08.1', TRUE, 'active', 'clause_lookup',
  'Pattern 2 (deterministic): LLM query_formulation, HTTP clause_search, then synthesis. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-clause-lookup', 'clause_lookup', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'clause_lookup', 'clause_lookup', NULL, 'clause_lookup_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'template_retrieve', '2026.08.1', TRUE, 'active', 'template_retrieve',
  'Pattern 2 (deterministic): two query_formulation retrieves, HTTP score, then synthesis. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-template-retrieve', 'template_retrieve', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'template_retrieve', 'template_retrieve', NULL, 'template_retrieve_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'msa_risk_review', '2026.08.1', TRUE, 'active', 'msa_risk_review',
  'Pattern 2 (deterministic): HTTP OCR, two query_formulation retrieves, HTTP score, synthesis memo. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-msa-risk-review', 'msa_risk_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'msa_risk_review', 'msa_risk_review', 'msa_memo', 'msa_risk_review_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'kyc_onboarding', '2026.08.1', TRUE, 'active', 'kyc_onboard',
  'Pattern 2 (deterministic): domain HTTP KYC tools then synthesis packet. Prompts: host plus synthesis template. branch and human_gate are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-kyc-onboarding', 'kyc_onboarding', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'kyc_onboarding', 'kyc_onboarding', 'kyc_result', 'kyc_onboarding_tools', NULL, 'escalate_human',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'claims_adjudicate', '2026.08.1', TRUE, 'active', 'claims_adjudicate',
  'Pattern 2 (deterministic): HTTP playbook retrieve, query_formulation clause search, HTTP score, synthesis memo. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-claims-adjudicate', 'claims_adjudicate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'claims_adjudicate', 'claims_adjudicate', 'msa_memo', 'claims_adjudicate_tools', NULL, 'clarify',
  '["claims:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'ticket_triage', '2026.08.1', TRUE, 'active', 'ticket_triage',
  'Pattern 3 (guided): HTTP parse and tag, then synthesis reply. Prompts: host plus synthesis template. Stage allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-ticket-triage', 'ticket_triage', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'ticket_triage', 'ticket_triage', NULL, NULL, NULL, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'product_explain', '2026.08.1', TRUE, 'active', 'product_explain',
  'Pattern 3 (guided): prefetch placeholder, HTTP score/compare, then synthesis. Prompts: host plus synthesis template. Allowlists are catalogue-only. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-product-explain', 'product_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'product_explain', 'product_explain', NULL, NULL, NULL, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["loan","offer","product"]'::jsonb, 3
),
(
  'narrow_review', '2026.08.1', TRUE, 'active', 'narrow_review',
  'Pattern 3 (guided): HTTP OCR, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-narrow-review', 'narrow_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'narrow_review', 'narrow_review', 'counsel_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'contract_review', '2026.08.1', TRUE, 'active', 'contract_review',
  'Pattern 3 (guided): HTTP OCR, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-review', 'contract_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'contract_review', 'contract_review', 'counsel_memo', 'contract_review_golden', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'due_diligence', '2026.08.1', TRUE, 'active', 'due_diligence',
  'Pattern 3 (guided): HTTP playbook extract, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.',
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
  ('shopassist_case', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 24, '["tenant","user","session"]'::jsonb),
  ('order_damaged', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('billing_duplicate', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('policy_refund', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('dispute_intake', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('purchase_refund', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('pack_then_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('kyc_onboarding', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('claims_adjudicate', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('ticket_triage', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('product_explain', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('narrow_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('contract_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('due_diligence', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);

-- Extra catalogue cuts: published / draft / retired (or deprecated) for each type,
-- plus extra versions so History pages have something to compare.

\c acr

-- Capabilities: history on seed ids, plus standalone draft / retired / published.
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'ocr_extract', '1.0.0', 'domain',
  'Extract text from a document id (first cut, retired).',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'retired'
),
(
  'ocr_extract', '1.1.0', 'domain',
  'Extract text from a document id (superseded published cut).',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'published'
),
(
  'web_search', '0.9.0', 'domain',
  'Search the public web (retired prototype).',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/search/web","auth":"domain-oauth"}'::jsonb,
  NULL, 'assistant-platform', 'retired'
),
(
  'web_search', '1.1.0', 'domain',
  'Search the public web (draft next cut).',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"},"site":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/search/web","auth":"domain-oauth"}'::jsonb,
  NULL, 'assistant-platform', 'draft'
),
(
  'account_fee_lookup', '0.9.0', 'domain',
  'Look up why an account was charged a fee (retired first cut).',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/fees/explain","auth":"domain-oauth"}'::jsonb,
  NULL, 'accounts', 'retired'
),
(
  'account_fee_lookup', '1.1.0', 'domain',
  'Look up why an account was charged a fee (draft next cut).',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"},"as_of_date":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/fees/explain","auth":"domain-oauth"}'::jsonb,
  NULL, 'accounts', 'draft'
),
(
  'invoice_intake', '0.1.0', 'domain',
  'Draft invoice intake extractor, not published.',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["fields"],"properties":{"fields":{"type":"object"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/invoices/intake","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'draft'
),
(
  'fax_ocr_legacy', '0.9.0', 'domain',
  'Retired fax OCR. Do not activate again.',
  '{"type":"object","required":["fax_id"],"properties":{"fax_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/ocr/fax","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'retired'
),
(
  'credit_limit_lookup', '1.0.0', 'domain',
  'Look up the entitled credit limit for an account. Not wired to a manifest yet.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["limit"],"properties":{"limit":{"type":"number"},"currency":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/credit/limit","auth":"domain-oauth"}'::jsonb,
  NULL, 'lending', 'published'
);

INSERT INTO registry.manifests (manifest_id, manifest_version, tools, status) VALUES
(
  'fee_explain', '2026.04.1',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'fee_explain', '2026.07.1',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'search_only', '2026.09.1',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.1.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'research_tools', '2026.08.1',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'fax_lookup', '2026.04.1',
  '[{"name":"fax_ocr_legacy","capability_id":"fax_ocr_legacy","capability_version":"0.9.0","pdp_action":"fax_ocr","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'credit_lookup', '2026.08.1',
  '[{"name":"credit_limit_lookup","capability_id":"credit_limit_lookup","capability_version":"1.0.0","pdp_action":"credit_limit_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'research_assistant', '2026.04.1',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'research_assistant', '2026.07.1', $$[
    {"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"},
    {"name":"fetch_url","capability_id":"fetch_url","capability_version":"1.0.0","pdp_action":"fetch_url","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'card_freeze', '2026.04.1', $$[
    {"name":"identity_check","capability_id":"identity_check","capability_version":"1.0.0","pdp_action":"identity_check","risk_tier":"medium"},
    {"name":"freeze_card","capability_id":"freeze_card","capability_version":"1.0.0","pdp_action":"freeze_card","risk_tier":"high"}
  ]$$::jsonb,
  'retired'
),
(
  'contract_review', '2026.04.1', $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'retired'
);

\c adp

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
  ('credit-policy', 'Credit policy', 'http://agent-mocks:3010/corpora/credit-policy/search', 'credit-policy', 'workload-oauth', 'lending', 'published', NULL),
  ('research-notes', 'Research notes', 'http://agent-mocks:3010/corpora/research-notes/search', 'research-notes', 'workload-oauth', 'assistant-platform', 'draft', NULL),
  ('fax-archive', 'Fax archive', 'http://agent-mocks:3010/corpora/fax-archive/search', 'fax-archive', 'workload-oauth', 'document-intel', 'deprecated', NULL);

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'fee_explain', '2026.04.1', 'One retrieve tool for account fees (retired cut)',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'fee_explain', '2026.07.1', 'One retrieve tool for account fees (published, not live)',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'search_only', '2026.09.1', 'One web search tool (draft next cut)',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.1.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'research_tools', '2026.08.1', 'Draft research tools, not live',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'fax_lookup', '2026.04.1', 'Retired fax lookup tools',
  '[{"name":"fax_ocr_legacy","capability_id":"fax_ocr_legacy","capability_version":"0.9.0","pdp_action":"fax_ocr","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'credit_lookup', '2026.08.1', 'One credit-limit retrieve tool',
  '[{"name":"credit_limit_lookup","capability_id":"credit_limit_lookup","capability_version":"1.0.0","pdp_action":"credit_limit_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'research_assistant', '2026.04.1', 'Open research with web_search only (retired cut)',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'research_assistant', '2026.07.1', 'Open research with web_search and fetch_url (published, not live)',
  $$[
    {"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"},
    {"name":"fetch_url","capability_id":"fetch_url","capability_version":"1.0.0","pdp_action":"fetch_url","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'card_freeze', '2026.04.1', 'Identity then freeze (retired cut, no limit check)',
  $$[
    {"name":"identity_check","capability_id":"identity_check","capability_version":"1.0.0","pdp_action":"identity_check","risk_tier":"medium"},
    {"name":"freeze_card","capability_id":"freeze_card","capability_version":"1.0.0","pdp_action":"freeze_card","risk_tier":"high"}
  ]$$::jsonb,
  'retired'
),
(
  'contract_review', '2026.04.1', 'OCR then memo (retired cut, no Analyse tools)',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'retired'
);

-- Older workflow versions cannot be published (one published per id).
INSERT INTO dataplane.workflows (workflow_id, workflow_version, description, stages, status) VALUES
(
  'llm_pipeline', '2026.04.1', 'Fixed LLM stages (retired first cut)',
  '[{"id":"extract","llm_role":"classify"},{"id":"format","llm_role":"synthesis"}]'::jsonb,
  'deprecated'
),
(
  'llm_pipeline', '2026.09.1', 'Fixed LLM stages (draft next cut)',
  '[{"id":"extract","llm_role":"classify"},{"id":"rewrite","llm_role":"synthesis"},{"id":"format","llm_role":"synthesis"}]'::jsonb,
  'draft'
),
(
  'contract_review', '2026.04.1', 'Extract → report only (retired)',
  '[{"id":"extract","tool":"ocr_extract","llm_role":"none"},{"id":"report","tool":"draft_memo","llm_role":"synthesis"}]'::jsonb,
  'deprecated'
),
(
  'research_draft', '2026.08.1', 'Draft research stages, not published',
  '[{"id":"search","tool":"web_search","llm_role":"none"}]'::jsonb,
  'draft'
),
(
  'fax_pipeline', '2026.04.1', 'Retired fax OCR pipeline',
  '[{"id":"ocr","tool":"fax_ocr_legacy","llm_role":"none"}]'::jsonb,
  'deprecated'
),
(
  'credit_check', '2026.08.1', 'Look up entitled credit limit',
  '[{"id":"lookup","tool":"credit_limit_lookup","llm_role":"none"},{"id":"respond","llm_role":"synthesis"}]'::jsonb,
  'published'
),
(
  'card_freeze', '2026.04.1', 'Identity then freeze (retired, no limit check)',
  $$[
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb,
  'deprecated'
),
(
  'card_freeze', '2026.09.1', 'Identity, limit, freeze, then confirm (draft next cut)',
  $$[
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb,
  'draft'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('fee_explain', '2026.04.1', 'Look up why an account fee posted.', 'deprecated', 'assistant-platform'),
  ('fee_explain', '2026.07.1', 'You explain account fees. Use the fee lookup tool.', 'published', 'assistant-platform'),
  ('llm_pipeline', '2026.04.1', 'Do only the current stage. Do not choose the next stage. No tools.', 'deprecated', 'assistant-platform'),
  ('llm_pipeline', '2026.09.1', 'Do only the current stage. Draft next host. No tools.', 'draft', 'assistant-platform'),
  ('agent-chat', '2026.09.1', 'Be a concise corporate assistant. Draft next host.', 'draft', 'assistant-platform'),
  ('research_v0', '2026.08.1', 'Draft research host. Not published.', 'draft', 'assistant-platform'),
  ('fax_summarize', '2026.04.1', 'Summarize a fax. Retired.', 'deprecated', 'document-intel'),
  ('credit_explain', '2026.08.1', 'Explain the entitled credit limit. Do not invent numbers.', 'published', 'lending'),
  ('search_only', '2026.09.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Draft next host. Prefer web_search.', 'draft', 'assistant-platform'),
  ('research_assistant', '2026.04.1', 'Pattern 1. Reply CALL web_search or DONE <answer>. First cut. Do not invent results.', 'deprecated', 'assistant-platform'),
  ('research_assistant', '2026.07.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use web_search and fetch_url. Prefer primary sources.', 'published', 'assistant-platform'),
  ('email_summarize', '2026.04.1', 'Summarize this email. No tools. Return short bullets.', 'deprecated', 'assistant-platform'),
  ('email_summarize', '2026.09.1', 'Pattern 0. One synthesis turn. Summarize this email for the banker. Redact secrets. No tools.', 'draft', 'assistant-platform'),
  ('card_freeze', '2026.04.1', 'Pattern 2. Confirm the freeze from identity and freeze outputs only. Do not invent card state.', 'deprecated', 'ops'),
  ('card_freeze', '2026.09.1', 'Pattern 2. Confirm the freeze from identity, limit, and freeze outputs. Draft next host.', 'draft', 'ops'),
  ('contract_review', '2026.04.1', 'Pattern 3. Extract then report. Do not invent stages.', 'deprecated', 'legal-agents');

INSERT INTO dataplane.prompt_role_templates (prompt_id, prompt_version, llm_role, task_type, "text") VALUES
  ('llm_pipeline', '2026.04.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.04.1', 'synthesis', 'synthesize', 'Format using the previous stage output only.'),
  ('llm_pipeline', '2026.09.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.09.1', 'synthesis', 'synthesize', 'Rewrite or format using the previous stage output only.'),
  ('credit_explain', '2026.08.1', 'synthesis', 'synthesize', 'Explain the entitled credit limit from the lookup output only. Do not invent numbers.'),
  ('card_freeze', '2026.04.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from identity and freeze outputs only.'),
  ('card_freeze', '2026.09.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from identity, limit, and freeze outputs only.'),
  ('contract_review', '2026.04.1', 'synthesis', 'synthesize', 'Draft the counsel memo from extract and report outputs only.');

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'fee_explain', '2026.04.1', FALSE, 'retired', 'fee_explain',
  'Look up a charged fee (retired cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.04.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', NULL, 3, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged"]'::jsonb, 1
),
(
  'fee_explain', '2026.07.1', FALSE, 'published', 'fee_explain',
  'Explain an account fee (published, not the live contestant).',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.07.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', 'fee_explain_golden', 5, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged","charge"]'::jsonb, 1
),
(
  'search_only', '2026.09.1', FALSE, 'draft', 'search_only',
  'Open loop with one tool (draft next cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-search-only', 'search_only', '2026.09.1',
  'read_only_standard', 'reasoning-standard', NULL, 'search_only', NULL, NULL, 8, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["search","google"]'::jsonb, 1
),
(
  'agent-chat', '2026.07.1', FALSE, 'published', 'general_chat',
  'One LLM call. Prompt only (published, not live).',
  'http://agent-runtime:3008/v1/runs', 'agent-chat', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'agent-chat', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'research_draft', '2026.08.1', FALSE, 'draft', 'research_draft',
  'Draft research worker, not yet live.',
  NULL, 'agent-research-v0', 'research_tools', '2026.08.1',
  'read_only_standard', 'lightweight-chat', NULL, 'research_v0', NULL, NULL, 4, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fax_lookup', '2026.04.1', FALSE, 'retired', 'fax_lookup',
  'Retired fax lookup. Do not activate again.',
  'http://agent-runtime:3008/v1/runs', 'agent-fax-lookup', 'fax_lookup', '2026.04.1',
  'read_only_standard', 'fast-chat', NULL, 'fax_summarize', NULL, NULL, 2, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'credit_explain', '2026.08.1', FALSE, 'published', 'credit_explain',
  'Published credit-limit explain. Not the live contestant.',
  'http://agent-runtime:3008/v1/runs', 'agent-credit-explain', 'credit_lookup', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'credit_check', 'credit_explain', NULL, NULL, 4, 'clarify',
  '["accounts:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'research_assistant', '2026.04.1', FALSE, 'retired', 'research_topic',
  'Open loop with web_search only (retired cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-research-assistant', 'research_assistant', '2026.04.1',
  'read_only_standard', 'reasoning-standard', NULL, 'research_assistant', 'research_brief', NULL, 8, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["research"]'::jsonb, 1
),
(
  'research_assistant', '2026.07.1', FALSE, 'published', 'research_topic',
  'Open loop with web_search and fetch_url (published, not live).',
  'http://agent-runtime:3008/v1/runs', 'agent-research-assistant', 'research_assistant', '2026.07.1',
  'read_only_standard', 'reasoning-standard', NULL, 'research_assistant', 'research_brief', 'research_assistant_golden', 12, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["research","sources"]'::jsonb, 1
),
(
  'email_summarize', '2026.04.1', FALSE, 'retired', 'summarize_email',
  'One LLM call. Summarize the pasted email (retired cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-email-summarize', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'email_summarize', 'exec_bullets', NULL, 1, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'email_summarize', '2026.09.1', FALSE, 'draft', 'summarize_email',
  'One LLM call. Summarize the pasted email (draft next cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-email-summarize', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'email_summarize', 'exec_bullets', 'email_summarize_golden', 1, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'card_freeze', '2026.04.1', FALSE, 'retired', 'card_freeze',
  'Identity then freeze (retired cut, no limit check).',
  'http://agent-runtime:3008/v1/runs', 'agent-card-freeze', 'card_freeze', '2026.04.1',
  'high_risk_step_up', 'reasoning-standard', 'card_freeze', 'card_freeze', NULL, 'card_freeze_tools', NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'card_freeze', '2026.09.1', FALSE, 'draft', 'card_freeze',
  'Identity, limit, freeze, then confirm (draft next cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-card-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'card_freeze', 'card_freeze', NULL, 'card_freeze_tools', NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'contract_review', '2026.04.1', FALSE, 'retired', 'contract_review',
  'Extract then report (retired cut, no Analyse allowlist).',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-review', 'contract_review', '2026.04.1',
  'read_only_standard', 'reasoning-standard', 'contract_review', 'contract_review', 'counsel_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('fee_explain', '2026.04.1', 'tool', '["accounts"]'::jsonb),
  ('fee_explain', '2026.07.1', 'tool', '["accounts"]'::jsonb),
  ('credit_explain', '2026.08.1', 'tool', '["credit-policy"]'::jsonb),
  ('contract_review', '2026.04.1', 'tool', '["clause-index"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('fee_explain', '2026.04.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user"]'::jsonb),
  ('fee_explain', '2026.07.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('search_only', '2026.09.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('research_draft', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('research_assistant', '2026.04.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user"]'::jsonb),
  ('research_assistant', '2026.07.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('contract_review', '2026.04.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user"]'::jsonb);
