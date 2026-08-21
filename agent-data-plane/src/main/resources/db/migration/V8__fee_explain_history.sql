INSERT INTO dataplane.route_tables (route_table_version, product, active) VALUES
  ('2026.04.1', 'corporate-assistant', FALSE),
  ('2026.05.1', 'corporate-assistant', FALSE),
  ('2026.06.1', 'corporate-assistant', FALSE),
  ('2026.07.1', 'corporate-assistant', FALSE);

INSERT INTO dataplane.routes (
  route_id, route_table_version, intent_label, description, activation_target, agent_client_id,
  tool_manifest, tool_manifest_version, policy_profile, model_profile,
  workflow_id, prompt_id, output_schema_id, eval_suite_id, max_loop_steps, fallback,
  required_claims, channels, chat_visible, keywords
) VALUES
(
  'fee_explain', '2026.04.1', 'fee_explain', 'Look up a charged fee',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain',
  'fee_explain_v1', '2026.08.1', 'read_only_standard', 'reasoning-standard',
  NULL, 'fee_explain_v0', 'fee_explain_out_v1', NULL, 3, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["fee","charged"]'::jsonb
),
(
  'fee_explain', '2026.05.1', 'fee_explain', 'Look up a charged fee',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain',
  'fee_explain_v1', '2026.08.1', 'read_only_standard', 'reasoning-standard',
  NULL, 'fee_explain_v1', 'fee_explain_out_v1', NULL, 4, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["fee","charged","charge"]'::jsonb
),
(
  'fee_explain', '2026.06.1', 'fee_explain', 'Explain why an account fee posted',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain',
  'fee_explain_v1', '2026.08.1', 'read_only_standard', 'fast-chat',
  NULL, 'fee_explain_v1', 'fee_explain_out_v1', 'fee_explain_golden', 4, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["fee","charged","charge"]'::jsonb
),
(
  'fee_explain', '2026.07.1', 'fee_explain', 'Explain an account fee',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain',
  'fee_explain_v1', '2026.08.1', 'read_only_standard', 'reasoning-standard',
  NULL, 'fee_explain_v1', 'fee_explain_out_v1', 'fee_explain_golden', 5, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["fee","charged","charge","42"]'::jsonb
);

INSERT INTO dataplane.retrieval (route_id, route_table_version, mode, scope)
SELECT 'fee_explain', v.route_table_version, 'tool', '["accounts"]'::jsonb
  FROM (VALUES ('2026.04.1'), ('2026.05.1'), ('2026.06.1'), ('2026.07.1')) AS v(route_table_version);

INSERT INTO dataplane.memory_profiles (
  route_id, route_table_version, conversation, working, "loop", long_term, ttl_hours, isolation
)
VALUES
  ('fee_explain', '2026.04.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user"]'::jsonb),
  ('fee_explain', '2026.05.1', 'session', 'session', 'checkpoint', 'none', 12, '["tenant","user","session"]'::jsonb),
  ('fee_explain', '2026.06.1', 'session', 'session', 'checkpoint', 'retrieve_only', 12, '["tenant","user","session"]'::jsonb),
  ('fee_explain', '2026.07.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);
