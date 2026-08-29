-- fee_explain — tool manifest (ACR publish + ADP catalogue copy).

\c acr
INSERT INTO registry.manifests (
  manifest_id, manifest_version, tools, status
) VALUES
(
  'fee_explain', '2026.08.1', $$[
    {"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;

\c adp
INSERT INTO dataplane.manifests (
  manifest_id, manifest_version, description, tools, status
) VALUES
(
  'fee_explain', '2026.08.1', 'One retrieve tool for account fees',
  $$[
    {"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;
