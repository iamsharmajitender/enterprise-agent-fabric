-- duplicate_charge_review — ACR capabilities (classify intake + ShopAssist tools + synthesis).
-- Apply: ./add.sh or ../../add-seed-data.sh duplicate_charge_review

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'duplicate_charge_intake',
  '1.0.0',
  'domain',
  'Classify customer utterance into order_id for duplicate-charge review. HTTP unused when llm_role=classify.',
  '{"type":"object","properties":{}}'::jsonb,
  '{"type":"object","required":["order_id"],"properties":{"order_id":{"type":"string","pattern":"^ORD-\\d+$","description":"ShopAssist order id from the customer message only"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/intake","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
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
),
(
  'investigate_duplicate_charge',
  '1.0.0',
  'domain',
  'Check whether an order has a duplicate captured charge. Requires order_id and customer_id from prior lookup.',
  '{"type":"object","required":["order_id","customer_id"],"properties":{"order_id":{"type":"string","pattern":"^ORD-\\d+$","x-ground-in-user-context":true},"customer_id":{"type":"string","pattern":"^CUS-\\d+$","x-ground-in-user-context":true}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"duplicate_charge_found":{"type":"boolean","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/investigate_duplicate_charge","auth":"domain-oauth"}'::jsonb,
  NULL,
  'shopassist',
  'published'
),
(
  'duplicate_charge_respond',
  '1.0.0',
  'domain',
  'Write the customer-facing duplicate-charge answer from prior stage outputs only. HTTP unused when llm_role=synthesis.',
  '{"type":"object","properties":{}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/shopassist/respond","auth":"domain-oauth"}'::jsonb,
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
