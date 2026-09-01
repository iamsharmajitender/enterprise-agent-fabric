-- ticket_triage — ACR capabilities (Pattern 3 guided support triage).
-- Apply: ./add.sh or ../../add-seed-data.sh ticket_triage

\c acr
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'parse_ticket',
  '1.0.0',
  'domain',
  'Parse inbound support ticket text into structured fields.',
  '{"type":"object","properties":{"ticket_text":{"type":"string"},"utterance":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text","category","order_ref"],"properties":{"text":{"type":"string"},"category":{"type":"string","x-agent-context":true},"order_ref":{"type":"string","x-agent-context":true},"customer_email":{"type":"string","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/support/parse_ticket","auth":"domain-oauth"}'::jsonb,
  NULL,
  'support',
  'published'
),
(
  'tag_intent',
  '1.0.0',
  'domain',
  'Tag parsed ticket fields with intent and priority. Reads category and order_ref from prior parse_ticket slot.',
  '{"type":"object","required":["category","order_ref"],"properties":{"category":{"type":"string"},"order_ref":{"type":"string","pattern":"^ORD-\\d+$"}}}'::jsonb,
  '{"type":"object","required":["text","intent","priority"],"properties":{"text":{"type":"string"},"intent":{"type":"string","x-agent-context":true},"priority":{"type":"string","x-agent-context":true}}}'::jsonb,
  '{"method":"POST","url":"http://agent-mocks:3010/support/tag_intent","auth":"domain-oauth"}'::jsonb,
  NULL,
  'support',
  'published'
),
(
  'draft_reply',
  '1.0.0',
  'agent',
  'Start ticket_draft_reply child agent (join=true) with triage fields projected from goal and prior slots.',
  '{"type":"object","required":["utterance","category","order_ref","intent","priority"],"properties":{"utterance":{"type":"string"},"category":{"type":"string"},"order_ref":{"type":"string","pattern":"^ORD-\\d+$"},"intent":{"type":"string"},"priority":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","join":true,"body":{"route_id":"ticket_draft_reply"}}'::jsonb,
  NULL,
  'support',
  'published'
)
ON CONFLICT (id, version) DO UPDATE SET
  kind = EXCLUDED.kind,
  description = EXCLUDED.description,
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  invoke = EXCLUDED.invoke,
  status = EXCLUDED.status;
