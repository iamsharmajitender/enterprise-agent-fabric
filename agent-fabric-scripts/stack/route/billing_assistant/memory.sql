-- billing_assistant — memory profile (conversation + working + checkpoint loop).

\c adp
INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
('billing_assistant', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  conversation = EXCLUDED.conversation,
  working = EXCLUDED.working,
  "loop" = EXCLUDED."loop";
