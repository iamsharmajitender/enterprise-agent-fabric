UPDATE registry.capabilities
SET invoke = jsonb_set(invoke, '{url}', '"http://tool-mock:3010/legal/playbook/search"'::jsonb)
WHERE id = 'policy_search'
  AND version = '1.0.0';

UPDATE registry.capabilities
SET invoke = jsonb_set(invoke, '{url}', '"http://tool-mock:3010/legal/clauses/search"'::jsonb)
WHERE id = 'clause_search'
  AND version = '1.0.0';

UPDATE registry.capabilities
SET invoke = jsonb_set(invoke, '{url}', '"http://tool-mock:3010/legal/risk"'::jsonb)
WHERE id = 'risk_engine'
  AND version = '1.0.0';

UPDATE registry.capabilities
SET invoke = jsonb_set(invoke, '{url}', '"http://tool-mock:3010/legal/memo"'::jsonb)
WHERE id = 'draft_memo'
  AND version = '1.0.0';
