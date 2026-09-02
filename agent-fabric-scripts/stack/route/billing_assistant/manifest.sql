-- billing_assistant — tool manifest (ACR publish + ADP catalogue copy).

\c acr
INSERT INTO registry.manifests (
  manifest_id, manifest_version, tools, status
) VALUES
(
  'billing_assistant', '2026.08.1', $$[
    {"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"},
    {"name":"lookup_order_by_order_id","capability_id":"lookup_order_by_order_id","capability_version":"1.0.0","pdp_action":"lookup_order_by_order_id","risk_tier":"low"}
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
  'billing_assistant', '2026.08.1',
  'Pattern 1: LLM picks account_fee_lookup vs lookup_order_by_order_id from the customer message',
  $$[
    {"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"},
    {"name":"lookup_order_by_order_id","capability_id":"lookup_order_by_order_id","capability_version":"1.0.0","pdp_action":"lookup_order_by_order_id","risk_tier":"low"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
  description = EXCLUDED.description,
  tools = EXCLUDED.tools,
  status = EXCLUDED.status;
