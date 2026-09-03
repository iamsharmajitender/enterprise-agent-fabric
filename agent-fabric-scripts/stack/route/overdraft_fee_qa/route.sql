-- overdraft_fee_qa — Pattern 0 single inference with deterministic prefetch. No workflow, no tools, no memory.

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'overdraft_fee_qa', '2026.08.1', TRUE, 'active', 'overdraft_fee_qa',
  'Pattern 0 (single inference): one LLM call after catalogue prefetch of fee-schedule and product-disclosure. Grounded overdraft fee Q&A. No tools, no workflow, no session memory.',
  'http://agent-runtime-shared:3008/v1/runs', 'agent-overdraft-fee-qa', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'overdraft_fee_qa', 'cited_answer', NULL, 1, 'clarify',
  '[]'::jsonb, '["web","api"]'::jsonb, TRUE,
  '["overdraft","fee","everyday","business","corporate","student","premier","account fee"]'::jsonb,
  0
)
ON CONFLICT (route_id, route_version) DO NOTHING;
