-- fee_explain — route row (chat + jobs, Pattern 1 autonomous). No workflow_id.

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'fee_explain', '2026.08.1', TRUE, 'active', 'fee_explain',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over account_fee_lookup. One host prompt reused each turn. Domain HTTP only on CALL. No workflow.',
  'http://agent-runtime-shared:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', NULL, 6, 'clarify',
  '["accounts:read"]'::jsonb, '["web","api"]'::jsonb, TRUE, '["fee","charged","charge","42","monthly","why was i charged"]'::jsonb, 1
)
ON CONFLICT (route_id, route_version) DO NOTHING;
