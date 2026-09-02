-- kyc_onboarding — ACR capabilities (KYC domain tools + synthesis).
-- Apply: ./add.sh or ../../add-seed-data.sh kyc_onboarding

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'kyc_doc_intake',
  '1.0.0',
  'domain',
  'Collect and index applicant identity documents.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string","description":"Applicant id from the job goal"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"status":{"type":"string","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/doc_intake","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc',
  'published'
),
(
  'kyc_id_verify',
  '1.0.0',
  'domain',
  'Verify government id for an applicant.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string","description":"Applicant id from the job goal"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"verified":{"type":"boolean","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/verify","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc',
  'published'
),
(
  'kyc_sanctions_api',
  '1.0.0',
  'domain',
  'Screen applicant against sanctions lists.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string","description":"Applicant id from the job goal"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"cleared":{"type":"boolean","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/sanctions","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc',
  'published'
),
(
  'kyc_risk_engine',
  '1.0.0',
  'domain',
  'Score KYC risk for an applicant. Returns risk tier used by workflow branch.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string","description":"Applicant id from the job goal"}}}'::jsonb,
  '{"type":"object","required":["text","risk"],"properties":{"text":{"type":"string"},"risk":{"type":"string","enum":["low","high"],"description":"Branch key for workflow routing"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/risk","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc',
  'published'
),
(
  'kyc_account_activate',
  '1.0.0',
  'domain',
  'Activate account after KYC approval.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string","description":"Applicant id from the job goal"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"activated":{"type":"boolean","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/kyc/activate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'kyc',
  'published'
)
ON CONFLICT (id, version) DO UPDATE SET
  kind = EXCLUDED.kind,
  description = EXCLUDED.description,
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  invoke = EXCLUDED.invoke,
  status = EXCLUDED.status;
