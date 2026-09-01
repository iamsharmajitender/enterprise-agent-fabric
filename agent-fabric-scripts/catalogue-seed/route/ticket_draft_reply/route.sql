-- ticket_draft_reply — Pattern 0 child route (jobs-only; started by ticket_triage kind=agent).

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'ticket_draft_reply', '2026.08.1', TRUE, 'active', 'ticket_draft_reply',
  'Pattern 0 child agent: draft customer reply from triage payload projected by parent ticket_triage draft_reply stage (kind=agent, join=true).',
  'http://agent-runtime-custom:3008/v1/runs', 'agent-ticket-draft-reply', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'ticket_draft_reply', NULL, NULL, 1, 'clarify',
  '["support:case"]'::jsonb, '["api"]'::jsonb, FALSE,
  '[]'::jsonb,
  0
)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  description = EXCLUDED.description,
  activation_target = EXCLUDED.activation_target,
  prompt_id = EXCLUDED.prompt_id,
  chat_visible = EXCLUDED.chat_visible,
  autonomy_mode = EXCLUDED.autonomy_mode;
