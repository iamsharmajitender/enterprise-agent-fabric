UPDATE registry.capabilities
SET invoke = jsonb_set(invoke, '{url}', '"http://tool-mock:3010/fees/explain"'::jsonb)
WHERE id = 'account_fee_lookup'
  AND version = '1.0.0';
