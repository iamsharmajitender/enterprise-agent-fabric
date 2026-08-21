INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'clause_search',
  '1.0.0',
  'domain',
  'Search extracted text for clause topics.',
  '{"type":"object","required":["topics"],"properties":{"topics":{"type":"array","items":{"type":"string"}}}}'::jsonb,
  '{"type":"object","required":["hits"],"properties":{"hits":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/legal/clauses/search","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'policy_search',
  '1.0.0',
  'domain',
  'Search the legal playbook.',
  '{"type":"object","required":["policy_set"],"properties":{"policy_set":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["hits"],"properties":{"hits":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/legal/playbook/search","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'risk_engine',
  '1.0.0',
  'domain',
  'Score risk from extracted clauses.',
  '{"type":"object","required":["score_profile"],"properties":{"score_profile":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["score"],"properties":{"score":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/legal/risk","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'draft_memo',
  '1.0.0',
  'domain',
  'Draft counsel-ready memo from investigation context.',
  '{"type":"object","required":["audience"],"properties":{"audience":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["memo"],"properties":{"memo":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/legal/memo","auth":"domain-oauth"}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'doc_intake',
  '1.0.0',
  'domain',
  'Collect and store KYC onboarding documents.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["packet_id"],"properties":{"packet_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/kyc/docs","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
),
(
  'id_verify',
  '1.0.0',
  'domain',
  'Verify identity documents for KYC.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["verified"],"properties":{"verified":{"type":"boolean"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/kyc/id-verify","auth":"domain-oauth"}'::jsonb,
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
  '{"type":"object","required":["hits"],"properties":{"hits":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/kyc/sanctions","auth":"domain-oauth"}'::jsonb,
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
  '{"type":"object","required":["risk"],"properties":{"risk":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/kyc/risk","auth":"domain-oauth"}'::jsonb,
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
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/kyc/activate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc-ops',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;
