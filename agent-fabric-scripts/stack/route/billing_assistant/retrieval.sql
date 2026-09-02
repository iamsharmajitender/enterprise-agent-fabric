-- billing_assistant — retrieval policy (tool mode).

\c adp
INSERT INTO dataplane.retrieval (
  route_id, route_version, mode, scope
) VALUES
('billing_assistant', '2026.08.1', 'tool', '["accounts"]'::jsonb)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  mode = EXCLUDED.mode,
  scope = EXCLUDED.scope;
