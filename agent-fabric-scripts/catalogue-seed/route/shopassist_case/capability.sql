-- shopassist_case — ACR capabilities (domain tools).
-- Apply: ./agent-fabric-scripts/catalogue-seed/add-seed-data.sh shopassist_case

\c acr
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
)
ON CONFLICT (id, version) DO NOTHING;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
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
)
ON CONFLICT (id, version) DO NOTHING;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
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
)
ON CONFLICT (id, version) DO NOTHING;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
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
)
ON CONFLICT (id, version) DO NOTHING;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
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
)
ON CONFLICT (id, version) DO NOTHING;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
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
)
ON CONFLICT (id, version) DO NOTHING;
