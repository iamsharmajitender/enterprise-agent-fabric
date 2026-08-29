-- fee_explain — retrieval policy (tool mode over accounts corpus).

\c adp
INSERT INTO dataplane.retrieval (
  route_id, route_version, mode, scope
) VALUES
('fee_explain', '2026.08.1', 'tool', '["accounts"]'::jsonb)
ON CONFLICT (route_id, route_version) DO NOTHING;
