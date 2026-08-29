-- shopassist_case — route row (chat, Pattern 1 autonomous). No workflow_id.

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'shopassist_case', '2026.08.1', TRUE, 'active', 'shopassist_case',
  'Pattern 1 (autonomous): ShopAssist front-line support. ASK for order/customer/email if missing, lookup order, then billing and policy domain APIs. Escalate when needed.',
  'http://agent-runtime:3008/v1/runs', 'agent-shopassist-case', 'shopassist_case', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'shopassist_case', NULL, NULL, 12, 'clarify',
  '["support:case"]'::jsonb, '["web","api"]'::jsonb, TRUE, '["damaged","damage","refund","jacket","charged twice","duplicate charge","ORD-77819"]'::jsonb, 1
)
ON CONFLICT (route_id, route_version) DO NOTHING;
