-- Point remaining domain capability invoke URLs at local tool-mock.
-- Skip agent_start jobs URLs (api-afd.internal). Do not edit prior Flyway files.

UPDATE registry.capabilities
SET invoke = jsonb_set(
  invoke,
  '{url}',
  to_jsonb(replace(invoke->>'url', 'https://api.internal', 'http://tool-mock:3010'))
)
WHERE invoke->>'url' LIKE 'https://api.internal/%';
