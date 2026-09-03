-- ticket_triage — Pattern 3 guided route (jobs + chat).

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'ticket_triage', '2026.08.1', TRUE, 'active', 'ticket_triage',
  'Pattern 3 (guided): fixed outer stages parse → tag → draft_reply (kind=agent, join). Child route ticket_draft_reply drafts the customer reply.',
  'http://agent-runtime-custom:3008/v1/runs', 'agent-ticket-triage', 'ticket_triage', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'ticket_triage', 'ticket_triage', NULL, 'ticket_triage_tools', NULL, 'clarify',
  '["support:case"]'::jsonb, '["web","api"]'::jsonb, TRUE,
  '["ticket","triage","duplicate charge","billing","ORD-77819","support"]'::jsonb,
  3
)
ON CONFLICT (route_id, route_version) DO UPDATE SET
  description = EXCLUDED.description,
  activation_target = EXCLUDED.activation_target,
  tool_manifest = EXCLUDED.tool_manifest,
  workflow_id = EXCLUDED.workflow_id,
  prompt_id = EXCLUDED.prompt_id,
  autonomy_mode = EXCLUDED.autonomy_mode,
  keywords = EXCLUDED.keywords;
