-- Baseline schema + catalogue seed for database acr.
CREATE SCHEMA IF NOT EXISTS registry;

CREATE TABLE registry.capabilities (
  id TEXT NOT NULL,
  version TEXT NOT NULL,
  kind TEXT NOT NULL,
  description TEXT,
  input_schema JSONB NOT NULL,
  output_schema JSONB,
  invoke JSONB NOT NULL,
  snippet TEXT,
  owner TEXT,
  status TEXT NOT NULL,
  PRIMARY KEY (id, version)
);

CREATE TABLE registry.manifests (
  manifest_id TEXT NOT NULL,
  manifest_version TEXT NOT NULL,
  tools JSONB NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (manifest_id, manifest_version)
);

-- ShopAssist case route capabilities and manifest.

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'lookup_order',
  '1.0.0',
  'domain',
  'Look up order status, item, and price.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string"},"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"order_id":{"type":"string"},"item_id":{"type":"string"},"price":{"type":"number"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/lookup_order","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'lookup_order_by_customer',
  '1.0.0',
  'domain',
  'Look up order details by customer id.',
  '{"type":"object","required":["customer_id"],"properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"order_id":{"type":"string"},"customer_id":{"type":"string"},"item_id":{"type":"string"},"price":{"type":"number"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/lookup_order_by_customer","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'lookup_order_by_email',
  '1.0.0',
  'domain',
  'Look up order details by customer email.',
  '{"type":"object","required":["email"],"properties":{"email":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"order_id":{"type":"string"},"customer_id":{"type":"string"},"item_id":{"type":"string"},"price":{"type":"number"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/lookup_order_by_email","auth":"domain-oauth"}'::jsonb,
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
);

INSERT INTO registry.manifests (manifest_id, manifest_version, tools, status) VALUES
(
  'shopassist_case', '2026.08.1',
  $$[
    {"name":"lookup_order","capability_id":"lookup_order","capability_version":"1.0.0","pdp_action":"lookup_order","risk_tier":"low"},
    {"name":"lookup_order_by_customer","capability_id":"lookup_order_by_customer","capability_version":"1.0.0","pdp_action":"lookup_order_by_customer","risk_tier":"low"},
    {"name":"lookup_order_by_email","capability_id":"lookup_order_by_email","capability_version":"1.0.0","pdp_action":"lookup_order_by_email","risk_tier":"low"},
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"},
    {"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"},
    {"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0","pdp_action":"escalate_to_human","risk_tier":"high"}
  ]$$::jsonb,
  'published'
);
