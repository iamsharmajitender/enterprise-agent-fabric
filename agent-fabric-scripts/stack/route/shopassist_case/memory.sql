-- shopassist_case — memory profile (conversation + working + checkpoint loop).

\c adp
INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
('shopassist_case', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 24, '["tenant","user","session"]'::jsonb)
ON CONFLICT (route_id, route_version) DO NOTHING;
