INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'contract_review_staged_v3',
  '2026.08.1',
  'Guided contract review: fixed outer stages, flexible tools in Analyse',
  $$[
    {
      "name": "ocr_extract",
      "capability_id": "ocr_extract",
      "capability_version": "1.2.0",
      "pdp_action": "ocr_extract",
      "risk_tier": "low"
    },
    {
      "name": "clause_search",
      "capability_id": "clause_search",
      "capability_version": "1.0.0",
      "pdp_action": "clause_search",
      "risk_tier": "low"
    },
    {
      "name": "policy_search",
      "capability_id": "policy_search",
      "capability_version": "1.0.0",
      "pdp_action": "policy_search",
      "risk_tier": "low"
    },
    {
      "name": "risk_engine",
      "capability_id": "risk_engine",
      "capability_version": "1.0.0",
      "pdp_action": "risk_engine",
      "risk_tier": "medium"
    },
    {
      "name": "draft_memo",
      "capability_id": "draft_memo",
      "capability_version": "1.0.0",
      "pdp_action": "draft_memo",
      "risk_tier": "medium"
    }
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.workflows (
  workflow_id, workflow_version, description, stages, status
) VALUES
(
  'contract_review_v3',
  '2026.08.1',
  'Pattern 3: Extract → Analyse (allowlisted tools) → Generate Report',
  $$[
    {"id":"extract","tool":"ocr_extract","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":6},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
(
  'contract_review_v3',
  '2026.08.1',
  'You are counsel''s contract-review worker. Stay inside the current stage. Inside Analyse you may choose among the stage allowlist. Do not invent stages.',
  'published',
  'legal-agents'
);

INSERT INTO dataplane.prompt_role_templates (
  prompt_id, prompt_version, llm_role, task_type, "text"
) VALUES
(
  'contract_review_v3',
  '2026.08.1',
  'synthesis',
  'synthesize',
  'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'
);

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, pattern
) VALUES
(
  'contract_review',
  '2026.08.1',
  TRUE,
  'active',
  'contract_review',
  'Pattern 3 job: fixed stages, flexible tools inside Analyse',
  'http://agent-runtime:3008/v1/runs',
  'agent-contract-review',
  'contract_review_staged_v3',
  '2026.08.1',
  'read_only_standard',
  'reasoning-standard',
  'contract_review_v3',
  'contract_review_v3',
  'counsel_memo_v1',
  'contract_review_golden',
  NULL,
  'clarify',
  '["legal:read"]'::jsonb,
  '["api"]'::jsonb,
  FALSE,
  '[]'::jsonb,
  3
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('contract_review', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('contract_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);
