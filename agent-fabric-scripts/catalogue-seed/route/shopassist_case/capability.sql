-- shopassist_case — ACR capabilities (domain tools).
-- Apply: ./add.sh or ../../add-seed-data.sh shopassist_case

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'lookup_order_by_order_id',
  '1.0.0',
  'domain',
  'Look up order details by order id (ORD-*). Use when the customer provides an order number.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string","pattern":"^ORD-\\d+$","description":"ShopAssist order id (ORD-*)","x-ground-in-user-context":true}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"order_id":{"type":"string","x-agent-context":true},"customer_id":{"type":"string","x-agent-context":true},"item_id":{"type":"string","x-agent-context":true},"price":{"type":"number"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/lookup_order","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
)
ON CONFLICT (id, version) DO UPDATE SET
  kind = EXCLUDED.kind,
  description = EXCLUDED.description,
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  invoke = EXCLUDED.invoke,
  status = EXCLUDED.status;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'investigate_duplicate_charge',
  '1.0.0',
  'domain',
  'Check whether an order has a duplicate captured charge.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string","pattern":"^ORD-\\d+$","x-ground-in-user-context":true},"customer_id":{"type":"string","pattern":"^CUS-\\d+$","x-ground-in-user-context":true}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"duplicate_charge_found":{"type":"boolean"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/investigate_duplicate_charge","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
)
ON CONFLICT (id, version) DO UPDATE SET
  kind = EXCLUDED.kind,
  description = EXCLUDED.description,
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  invoke = EXCLUDED.invoke,
  status = EXCLUDED.status;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'check_return_policy',
  '1.0.0',
  'domain',
  'Check return and refund policy for a ShopAssist case.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string","pattern":"^ORD-\\d+$","x-ground-in-user-context":true},"item_id":{"type":"string","pattern":"^[a-z][a-z0-9_]*$"},"reason":{"type":"string","minLength":1}}}'::jsonb,
  '{"type":"object","required":["text","policy_id","eligible","automatic_refund_limit","recommended_action"],"properties":{"text":{"type":"string"},"policy_id":{"type":"string","x-agent-context":true},"eligible":{"type":"boolean","x-agent-context":true},"automatic_refund_limit":{"type":"number"},"recommended_action":{"type":"string","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/check_return_policy","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
)
ON CONFLICT (id, version) DO UPDATE SET
  kind = EXCLUDED.kind,
  description = EXCLUDED.description,
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  invoke = EXCLUDED.invoke,
  status = EXCLUDED.status;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'escalate_to_human',
  '1.0.0',
  'domain',
  'Create a structured human escalation handoff for ShopAssist.',
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string","pattern":"^ORD-\\d+$","x-ground-in-user-context":true},"customer_id":{"type":"string","pattern":"^CUS-\\d+$","x-ground-in-user-context":true},"escalation_reason":{"type":"string","minLength":1}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"handoff_id":{"type":"string","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/handoff/escalate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
)
ON CONFLICT (id, version) DO UPDATE SET
  kind = EXCLUDED.kind,
  description = EXCLUDED.description,
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  invoke = EXCLUDED.invoke,
  status = EXCLUDED.status;
