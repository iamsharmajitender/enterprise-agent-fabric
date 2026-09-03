-- duplicate_charge_review — Pattern 2 deterministic route (jobs + chat).

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'duplicate_charge_review', '2026.08.1', TRUE, 'active', 'duplicate_charge_review',
  'Pattern 2 (deterministic): classify order id, lookup order, duplicate-charge check with customer_id from lookup slot, synthesis reply. Fixed stage order; model does not pick tools.',
  'http://agent-runtime-custom:3008/v1/runs', 'agent-duplicate-charge-review', 'duplicate_charge_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'duplicate_charge_review', 'duplicate_charge_review', NULL, 'duplicate_charge_review_tools', NULL, 'clarify',
  '["support:case"]'::jsonb, '["web","api"]'::jsonb, TRUE,
  '["charged twice","duplicate charge","double charge","ORD-77819","twice on order"]'::jsonb,
  2
)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  description = EXCLUDED.description,
  activation_target = EXCLUDED.activation_target,
  tool_manifest = EXCLUDED.tool_manifest,
  workflow_id = EXCLUDED.workflow_id,
  prompt_id = EXCLUDED.prompt_id,
  autonomy_mode = EXCLUDED.autonomy_mode,
  keywords = EXCLUDED.keywords;
