-- kyc_onboarding — Pattern 2 deterministic route with workflow branch + human_gate.

\c adp
INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'kyc_onboarding', '2026.08.1', TRUE, 'active', 'kyc_onboarding',
  'Pattern 2 (deterministic): KYC pipeline with designer-owned branch on risk_score slot (high → manual_review gate, low → activate_account).',
  'http://agent-runtime-shared:3008/v1/runs', 'agent-kyc-onboarding', 'kyc_onboarding', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'kyc_onboarding', 'kyc_onboarding', NULL, NULL, NULL, 'clarify',
  '["kyc:operate"]'::jsonb, '["api"]'::jsonb, FALSE,
  '["kyc","onboarding","activate","manual review","applicant"]'::jsonb,
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
