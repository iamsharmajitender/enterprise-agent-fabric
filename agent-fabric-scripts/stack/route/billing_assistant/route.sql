-- billing_assistant — Pattern 1 autonomous route (no workflow_id).

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'billing_assistant', '2026.08.1', TRUE, 'active', 'billing_assistant',
  'Pattern 1 (autonomous): LLM CALL/DONE loop — picks account_fee_lookup or lookup_order_by_order_id based on the customer question.',
  'http://agent-runtime-shared:3008/v1/runs', 'agent-billing-assistant', 'billing_assistant', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'billing_assistant', NULL, NULL, 8, 'clarify',
  '["accounts:read","support:case"]'::jsonb, '["web","api"]'::jsonb, TRUE,
  '["fee","charged","charge","order","ORD-","acct-","status","delivery"]'::jsonb,
  1
)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  description = EXCLUDED.description,
  activation_target = EXCLUDED.activation_target,
  tool_manifest = EXCLUDED.tool_manifest,
  prompt_id = EXCLUDED.prompt_id,
  autonomy_mode = EXCLUDED.autonomy_mode,
  keywords = EXCLUDED.keywords;
