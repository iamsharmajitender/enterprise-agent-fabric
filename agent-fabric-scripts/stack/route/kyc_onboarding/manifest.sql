-- kyc_onboarding — tool manifest (ACR publish + ADP catalogue copy).

\c acr
INSERT INTO registry.manifests (
  manifest_id, manifest_version, tools, status
) VALUES
(
  'kyc_onboarding', '2026.08.1', $$[
    {"name":"kyc_doc_intake","capability_id":"kyc_doc_intake","capability_version":"1.0.0","pdp_action":"kyc_doc_intake","risk_tier":"low"},
    {"name":"kyc_id_verify","capability_id":"kyc_id_verify","capability_version":"1.0.0","pdp_action":"kyc_id_verify","risk_tier":"low"},
    {"name":"kyc_sanctions_api","capability_id":"kyc_sanctions_api","capability_version":"1.0.0","pdp_action":"kyc_sanctions_api","risk_tier":"low"},
    {"name":"kyc_risk_engine","capability_id":"kyc_risk_engine","capability_version":"1.0.0","pdp_action":"kyc_risk_engine","risk_tier":"medium"},
    {"name":"kyc_account_activate","capability_id":"kyc_account_activate","capability_version":"1.0.0","pdp_action":"kyc_account_activate","risk_tier":"high"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
  tools = EXCLUDED.tools,
  status = EXCLUDED.status;

\c adp
INSERT INTO dataplane.manifests (
  manifest_id, manifest_version, description, tools, status
) VALUES
(
  'kyc_onboarding', '2026.08.1',
  'Pattern 2 KYC pipeline: doc intake → verify → sanctions → risk (branch) → gate or activate → synthesis',
  $$[
    {"name":"kyc_doc_intake","capability_id":"kyc_doc_intake","capability_version":"1.0.0","pdp_action":"kyc_doc_intake","risk_tier":"low"},
    {"name":"kyc_id_verify","capability_id":"kyc_id_verify","capability_version":"1.0.0","pdp_action":"kyc_id_verify","risk_tier":"low"},
    {"name":"kyc_sanctions_api","capability_id":"kyc_sanctions_api","capability_version":"1.0.0","pdp_action":"kyc_sanctions_api","risk_tier":"low"},
    {"name":"kyc_risk_engine","capability_id":"kyc_risk_engine","capability_version":"1.0.0","pdp_action":"kyc_risk_engine","risk_tier":"medium"},
    {"name":"kyc_account_activate","capability_id":"kyc_account_activate","capability_version":"1.0.0","pdp_action":"kyc_account_activate","risk_tier":"high"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
  description = EXCLUDED.description,
  tools = EXCLUDED.tools,
  status = EXCLUDED.status;
