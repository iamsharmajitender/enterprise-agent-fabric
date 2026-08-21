INSERT INTO dataplane.route_tables (route_table_version, product, active)
VALUES ('2026.08.1', 'corporate-assistant', TRUE);

INSERT INTO dataplane.routes (
  route_id, route_table_version, intent_label, description, activation_target, agent_client_id,
  tool_manifest, tool_manifest_version, policy_profile, model_profile, retrieval, memory_profile,
  workflow_id, prompt_id, output_schema_id, eval_suite_id, max_loop_steps, fallback,
  required_claims, channels, chat_visible, keywords
) VALUES
(
  'fee_explain', '2026.08.1', 'fee_explain', 'Explain an account fee',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain',
  'fee_explain_v1', '2026.08.1', 'read_only_standard', 'reasoning-standard',
  '{"mode":"tool","scope":["accounts"]}'::jsonb,
  '{"conversation":"session","working":"session","loop":"checkpoint","long_term":"retrieve_only","ttl_hours":24,"isolation":["tenant","user","session"]}'::jsonb,
  NULL, 'fee_explain_v1', 'fee_explain_out_v1', 'fee_explain_golden', 6, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["fee","charged","charge","42","monthly"]'::jsonb
),
(
  'agent-account-v3', '2026.08.1', 'account_history', 'Read-only account and transaction history',
  NULL, 'agent-account-v3',
  'accounts-readonly-v2', '2026.08.1', 'read_only_standard', 'reasoning-standard',
  '{"mode":"tool","scope":["accounts"]}'::jsonb,
  '{"conversation":"session","working":"session","loop":"checkpoint","long_term":"retrieve_only","ttl_hours":24,"isolation":["tenant","user","session"]}'::jsonb,
  NULL, 'account_history_v3', 'account_history_out_v1', 'account_history_golden', 6, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["account","transaction","history","balance","statement"]'::jsonb
),
(
  'agent-payments-v2', '2026.08.1', 'payment_initiate', 'Initiate outbound transfer',
  'https://payments-app.internal/v1/runs', 'agent-payments-v2',
  'payments-readwrite-v3', '2026.08.1', 'high_risk_step_up', 'reasoning-standard',
  '{"mode":"tool","scope":["policy-engine","accounts"]}'::jsonb,
  '{"conversation":"session","working":"session","loop":"checkpoint","long_term":"none","ttl_hours":8,"isolation":["tenant","user","session"]}'::jsonb,
  NULL, 'payments_v2', 'payments_out_v1', 'payments_golden', 8, 'escalate_human',
  '["payments:initiate"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["transfer","payment","pay","send"]'::jsonb
),
(
  'agent-policy-qa-v1', '2026.08.1', 'policy_qa', 'Policy and procedure Q&A via RAG',
  NULL, 'agent-policy-qa-v1',
  'none', NULL, 'read_only_standard', 'reasoning-standard',
  '{"mode":"deterministic_prefetch","scope":["policy-engine"]}'::jsonb,
  NULL,
  NULL, 'policy_qa_v1', 'policy_qa_out_v1', 'policy_qa_golden', NULL, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE,
  '["policy","procedure","handbook"]'::jsonb
),
(
  'agent-chat-v1', '2026.08.1', 'general_chat', 'Lightweight chat with no tools',
  NULL, 'agent-chat-v1',
  'none', NULL, 'low_risk_chat', 'lightweight-chat',
  NULL, NULL, NULL, 'chat_v1', NULL, NULL, 2, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE,
  '[]'::jsonb
),
(
  'agent-escalate-v1', '2026.08.1', 'escalate_human', 'Hand off to human agent',
  NULL, 'agent-escalate-v1',
  'handoff-v1', '2026.08.1', 'read_only_standard', 'lightweight-chat',
  NULL, NULL, NULL, 'escalate_v1', NULL, NULL, 3, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE,
  '["human","speak","escalate","handoff"]'::jsonb
);
