-- ticket_triage — session memory + loop checkpoint for guided inner loops.

\c adp
INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
(
  'ticket_triage', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 24,
  '["tenant","user","session"]'::jsonb
)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  conversation = EXCLUDED.conversation,
  working = EXCLUDED.working,
  "loop" = EXCLUDED."loop",
  long_term = EXCLUDED.long_term,
  ttl_hours = EXCLUDED.ttl_hours,
  isolation = EXCLUDED.isolation;
