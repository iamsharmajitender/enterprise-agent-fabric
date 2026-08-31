-- shopassist_case — tool manifest (ACR publish + ADP catalogue copy).

\c acr
INSERT INTO registry.manifests (
  manifest_id, manifest_version, tools, status
) VALUES
(
  'shopassist_case', '2026.08.1', $$[
    {"name":"lookup_order_by_order_id","capability_id":"lookup_order_by_order_id","capability_version":"1.0.0","pdp_action":"lookup_order_by_order_id","risk_tier":"low"},
    {"name":"lookup_order_by_customer","capability_id":"lookup_order_by_customer","capability_version":"1.0.0","pdp_action":"lookup_order_by_customer","risk_tier":"low"},
    {"name":"lookup_order_by_email","capability_id":"lookup_order_by_email","capability_version":"1.0.0","pdp_action":"lookup_order_by_email","risk_tier":"low"},
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"},
    {"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"},
    {"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0","pdp_action":"escalate_to_human","risk_tier":"high"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;

\c adp
INSERT INTO dataplane.manifests (
  manifest_id, manifest_version, description, tools, status
) VALUES
(
  'shopassist_case', '2026.08.1', 'ShopAssist front-line support: ASK for a locator, lookup order, billing/policy domain APIs, escalate',
  $$[
    {"name":"lookup_order_by_order_id","capability_id":"lookup_order_by_order_id","capability_version":"1.0.0","pdp_action":"lookup_order_by_order_id","risk_tier":"low"},
    {"name":"lookup_order_by_customer","capability_id":"lookup_order_by_customer","capability_version":"1.0.0","pdp_action":"lookup_order_by_customer","risk_tier":"low"},
    {"name":"lookup_order_by_email","capability_id":"lookup_order_by_email","capability_version":"1.0.0","pdp_action":"lookup_order_by_email","risk_tier":"low"},
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"},
    {"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"},
    {"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0","pdp_action":"escalate_to_human","risk_tier":"high"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;
