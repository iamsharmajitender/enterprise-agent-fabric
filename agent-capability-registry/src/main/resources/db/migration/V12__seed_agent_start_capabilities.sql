-- Teaching agent_start capabilities. V8 replaced V3 rows; seed-db.sh also reloads docs/run/seed.
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'start_contract_review',
  '1.0.0',
  'agent_start',
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
  'agent_start',
  'Start governed KYC onboarding as a jobs run.',
  '{"type":"object","required":["applicant_id"],"properties":{"applicant_id":{"type":"string"},"ticket_id":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"kyc_onboarding"}}'::jsonb,
  NULL,
  'kyc-ops',
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
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;
