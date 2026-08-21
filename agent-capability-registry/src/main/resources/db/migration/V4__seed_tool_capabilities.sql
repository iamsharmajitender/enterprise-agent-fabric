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
  '{"method":"POST","url":"https://api.internal/fees/explain","auth":"domain-oauth"}'::jsonb,
  NULL,
  'accounts',
  'published'
),
(
  'list_accounts',
  '1.0.0',
  'domain',
  'List accounts for the entitled user.',
  '{"type":"object","properties":{"customer_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["accounts"],"properties":{"accounts":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/accounts/list","auth":"domain-oauth"}'::jsonb,
  NULL,
  'accounts',
  'published'
),
(
  'list_transactions',
  '1.0.0',
  'domain',
  'List transactions for an account.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["transactions"],"properties":{"transactions":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/transactions/list","auth":"domain-oauth"}'::jsonb,
  NULL,
  'accounts',
  'published'
),
(
  'lookup_beneficiary',
  '1.0.0',
  'domain',
  'Resolve payee name and invoice to beneficiary id.',
  '{"type":"object","required":["payee_name","invoice_ref"],"properties":{"payee_name":{"type":"string"},"invoice_ref":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["beneficiary_id"],"properties":{"beneficiary_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/payments/beneficiaries/lookup","auth":"domain-oauth"}'::jsonb,
  NULL,
  'payments-agents',
  'published'
),
(
  'validate_payment',
  '1.0.0',
  'domain',
  'Pre-auth: limits, sanctions, cut-off for a payment.',
  '{"type":"object","required":["beneficiary_id","amount","source_account","reference"],"properties":{"beneficiary_id":{"type":"string"},"amount":{"type":"number"},"source_account":{"type":"string"},"reference":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["ok"],"properties":{"ok":{"type":"boolean"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/payments/validate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'payments-agents',
  'published'
),
(
  'initiate_wire',
  '1.0.0',
  'domain',
  'Initiate wire transfer on payment hub.',
  '{"type":"object","required":["beneficiary_id","amount","source_account","reference"],"properties":{"beneficiary_id":{"type":"string"},"amount":{"type":"number"},"source_account":{"type":"string"},"reference":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["payment_id"],"properties":{"payment_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/payments/wires","auth":"domain-oauth"}'::jsonb,
  NULL,
  'payments-agents',
  'published'
),
(
  'escalate_to_human',
  '1.0.0',
  'domain',
  'Open a human-agent handoff with conversation context.',
  '{"type":"object","required":["reason"],"properties":{"reason":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["handoff_id"],"properties":{"handoff_id":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/handoff/escalate","auth":"domain-oauth"}'::jsonb,
  NULL,
  'assistant-platform',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;
