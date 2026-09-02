-- kyc_onboarding — Pattern 2 prompt pack (synthesis role only; HTTP stages are llm_role=none).

\c adp
INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
(
  'kyc_onboarding', '2026.08.1',
  'Pattern 2 KYC. Do only the current stage. Branching and human gate are designer-owned — do not invent the next step.',
  'published',
  'kyc-ops'
)
ON CONFLICT (prompt_id, prompt_version) DO UPDATE SET
  host = EXCLUDED.host,
  status = EXCLUDED.status;

INSERT INTO dataplane.prompt_role_templates (
  prompt_id, prompt_version, llm_role, task_type, text
) VALUES
(
  'kyc_onboarding', '2026.08.1', 'synthesis', 'synthesize',
  'Write a short KYC onboarding summary for ops using prior stage outputs only. State whether the account was activated or is awaiting manual review.'
)
ON CONFLICT (prompt_id, prompt_version, llm_role) DO UPDATE SET
  task_type = EXCLUDED.task_type,
  text = EXCLUDED.text;
