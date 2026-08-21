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
  '{"method":"POST","url":"https://api.internal/kyc/verify","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"https://api.internal/aml/screen","auth":"domain-oauth"}'::jsonb,
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
  '{"method":"POST","url":"https://api.internal/credit/limit","auth":"domain-oauth"}'::jsonb,
  NULL,
  'lending',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;
