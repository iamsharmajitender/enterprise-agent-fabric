-- fee_explain — ACR capability (domain tool: account_fee_lookup).
-- Apply: ./add.sh or ../../add-seed-data.sh fee_explain

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'account_fee_lookup',
  '1.0.0',
  'domain',
  'Look up why an account was charged a fee.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/fees/explain","auth":"domain-oauth"}'::jsonb,
  NULL,
  'accounts',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;
