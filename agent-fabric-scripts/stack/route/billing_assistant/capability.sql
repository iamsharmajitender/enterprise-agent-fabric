-- billing_assistant — reuses published domain tools (fee + order lookup).
-- Apply: ./add.sh or ../../add-seed-data.sh billing_assistant

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'account_fee_lookup',
  '1.0.0',
  'domain',
  'Look up why an account was charged a fee.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string","pattern":"^acct-\\d+$","description":"Customer account id (acct-*)","x-ground-in-user-context":true}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/fees/explain","auth":"domain-oauth"}'::jsonb,
  NULL,
  'accounts',
  'published'
),
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
ON CONFLICT (id, version) DO NOTHING;
