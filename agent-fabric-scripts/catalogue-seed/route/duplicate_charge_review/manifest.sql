-- duplicate_charge_review — tool manifest (ACR publish + ADP catalogue copy).

\c acr
INSERT INTO registry.manifests (
  manifest_id, manifest_version, tools, status
) VALUES
(
  'duplicate_charge_review', '2026.08.1', $$[
    {"name":"duplicate_charge_intake","capability_id":"duplicate_charge_intake","capability_version":"1.0.0","pdp_action":"duplicate_charge_intake","risk_tier":"low"},
    {"name":"lookup_order_by_order_id","capability_id":"lookup_order_by_order_id","capability_version":"1.0.0","pdp_action":"lookup_order_by_order_id","risk_tier":"low"},
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"},
    {"name":"duplicate_charge_respond","capability_id":"duplicate_charge_respond","capability_version":"1.0.0","pdp_action":"duplicate_charge_respond","risk_tier":"low"}
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
  'duplicate_charge_review', '2026.08.1',
  'Pattern 2: classify order id, lookup order, duplicate-charge check (customer_id from lookup slot), synthesis reply',
  $$[
    {"name":"duplicate_charge_intake","capability_id":"duplicate_charge_intake","capability_version":"1.0.0","pdp_action":"duplicate_charge_intake","risk_tier":"low"},
    {"name":"lookup_order_by_order_id","capability_id":"lookup_order_by_order_id","capability_version":"1.0.0","pdp_action":"lookup_order_by_order_id","risk_tier":"low"},
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"},
    {"name":"duplicate_charge_respond","capability_id":"duplicate_charge_respond","capability_version":"1.0.0","pdp_action":"duplicate_charge_respond","risk_tier":"low"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
  description = EXCLUDED.description,
  tools = EXCLUDED.tools,
  status = EXCLUDED.status;
