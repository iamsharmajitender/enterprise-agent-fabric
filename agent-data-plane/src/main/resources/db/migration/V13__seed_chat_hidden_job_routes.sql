INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'contract_investigate_v1',
  '2026.08.1',
  'Contract investigation tools (read-only + memo draft)',
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
),
(
  'msa_risk_review_v1',
  '2026.08.1',
  'Fixed MSA risk review tools',
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
),
(
  'kyc_onboarding_v2',
  '2026.08.1',
  'KYC onboarding tools with gated account activation',
  $$[
    {
      "name": "doc_intake",
      "capability_id": "doc_intake",
      "capability_version": "1.0.0",
      "pdp_action": "doc_intake",
      "risk_tier": "low"
    },
    {
      "name": "id_verify",
      "capability_id": "id_verify",
      "capability_version": "1.0.0",
      "pdp_action": "id_verify",
      "risk_tier": "medium"
    },
    {
      "name": "sanctions_api",
      "capability_id": "sanctions_api",
      "capability_version": "1.0.0",
      "pdp_action": "sanctions_screen",
      "risk_tier": "high"
    },
    {
      "name": "kyc_risk_engine",
      "capability_id": "kyc_risk_engine",
      "capability_version": "1.0.0",
      "pdp_action": "kyc_risk_score",
      "risk_tier": "medium"
    },
    {
      "name": "account_activate",
      "capability_id": "account_activate",
      "capability_version": "1.0.0",
      "pdp_action": "account_activate",
      "risk_tier": "high"
    }
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
(
  'contract_investigate_v1',
  '2026.08.1',
  'Investigate the document using only allowed tools. Prefer evidence over speculation. Stop when risk is assessed or budget is exhausted.',
  'published',
  'legal-agents'
),
(
  'kyc_onboarding_v2',
  '2026.08.1',
  'Summarize KYC evidence for a human reviewer. Do not recommend activation. Do not skip stages.',
  'published',
  'kyc-ops'
)
ON CONFLICT (prompt_id, prompt_version) DO NOTHING;

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords
) VALUES
(
  'email_summarize',
  '2026.08.1',
  TRUE,
  'active',
  'summarize_email',
  'Pattern 0 job: one-shot email summary, API/event only',
  'http://agent-runtime:3008/v1/runs',
  'agent-email-summarize',
  NULL,
  NULL,
  'read_only_standard',
  'fast-chat',
  NULL,
  'email_summarize_v2',
  'exec_bullets_v1',
  'email_summarize_golden',
  1,
  'clarify',
  '[]'::jsonb,
  '["api"]'::jsonb,
  FALSE,
  '[]'::jsonb
),
(
  'contract_investigation',
  '2026.08.1',
  TRUE,
  'active',
  'contract_investigate',
  'Pattern 1 internal job: open-loop contract investigation',
  'http://agent-runtime:3008/v1/runs',
  'agent-contract-investigate',
  'contract_investigate_v1',
  '2026.08.1',
  'read_only_standard',
  'reasoning-standard',
  NULL,
  'contract_investigate_v1',
  'risk_memo_v1',
  'contract_investigate_golden',
  12,
  'clarify',
  '["legal:read"]'::jsonb,
  '["api"]'::jsonb,
  FALSE,
  '[]'::jsonb
),
(
  'msa_risk_review',
  '2026.08.1',
  TRUE,
  'active',
  'msa_risk_review',
  'Pattern 2 job: fixed-stage MSA risk review',
  'http://agent-runtime:3008/v1/runs',
  'agent-msa-risk-review',
  'msa_risk_review_v1',
  '2026.08.1',
  'read_only_standard',
  'reasoning-standard',
  'msa_risk_review_v1',
  'msa_risk_review_v1',
  'msa_memo_v1',
  'msa_risk_review_golden',
  NULL,
  'clarify',
  '["legal:read"]'::jsonb,
  '["api"]'::jsonb,
  FALSE,
  '[]'::jsonb
),
(
  'kyc_onboarding',
  '2026.08.1',
  TRUE,
  'active',
  'kyc_onboard',
  'Pattern 2 job: KYC onboarding with gated account activation',
  'http://agent-runtime:3008/v1/runs',
  'agent-kyc-onboarding',
  'kyc_onboarding_v2',
  '2026.08.1',
  'high_risk_step_up',
  'reasoning-standard',
  'kyc_onboarding_v2',
  'kyc_onboarding_v2',
  'kyc_result_v1',
  'kyc_onboarding_golden',
  NULL,
  'escalate_human',
  '["kyc:onboard"]'::jsonb,
  '["api"]'::jsonb,
  FALSE,
  '[]'::jsonb
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('contract_investigation', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('contract_investigation', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('kyc_onboarding', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb);
