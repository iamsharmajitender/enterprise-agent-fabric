-- Two Pattern 1 parents that name kind=agent. Child jobs POST is catalogue-only.
-- ON CONFLICT: local volumes may already have these rows from seed-db.sh.
INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'fraud_investigate', '2026.08.1', 'Fraud parent: domain OCR/memo plus Legal agent capability',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"},
    {"name":"start_contract_review","capability_id":"start_contract_review","capability_version":"1.0.0","pdp_action":"start_contract_review","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'ops_start_kyc', '2026.08.1', 'Ops parent: parse ticket plus KYC agent capability',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"start_kyc_onboarding","capability_id":"start_kyc_onboarding","capability_version":"1.0.0","pdp_action":"start_kyc_onboarding","risk_tier":"high"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('fraud_investigate', '2026.08.1', 'Investigate the case with OCR and memo tools. You may propose start_contract_review to hand Legal a separate jobs run. Do not invent tools.', 'published', 'fraud-ops'),
  ('ops_start_kyc', '2026.08.1', 'Parse the onboarding ticket. You may propose start_kyc_onboarding to hand KYC a separate jobs run. Do not invent tools.', 'published', 'ops')
ON CONFLICT (prompt_id, prompt_version) DO NOTHING;

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'fraud_investigate', '2026.08.1', TRUE, 'active', 'fraud_investigate',
  'Open loop with domain tools plus one agent capability (start_contract_review → contract_review). Two freezes when Runtime posts jobs; today Runtime skips that HTTP. Prompt, memory, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-investigate', 'fraud_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_investigate', 'risk_memo', NULL, 8, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'ops_start_kyc', '2026.08.1', TRUE, 'active', 'ops_start_kyc',
  'Open loop with parse_ticket plus one agent capability (start_kyc_onboarding → kyc_onboarding). Child start is catalogue-only until Runtime posts jobs. Prompt, memory, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-ops-start-kyc', 'ops_start_kyc', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'ops_start_kyc', NULL, NULL, 6, 'clarify',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
)
ON CONFLICT (route_id, route_version) DO NOTHING;

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('fraud_investigate', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('ops_start_kyc', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb)
ON CONFLICT (route_id, route_version) DO NOTHING;
