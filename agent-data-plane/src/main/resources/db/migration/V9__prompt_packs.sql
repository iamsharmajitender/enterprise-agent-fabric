CREATE TABLE dataplane.prompt_packs (
  prompt_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  host TEXT NOT NULL,
  status TEXT NOT NULL,
  owner TEXT NOT NULL,
  PRIMARY KEY (prompt_id, prompt_version),
  CONSTRAINT prompt_packs_status_chk
    CHECK (status IN ('draft', 'published', 'deprecated'))
);

CREATE UNIQUE INDEX prompt_packs_one_published
  ON dataplane.prompt_packs (prompt_id)
  WHERE status = 'published';

CREATE TABLE dataplane.prompt_role_templates (
  prompt_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  llm_role TEXT NOT NULL,
  task_type TEXT NOT NULL,
  "text" TEXT NOT NULL,
  PRIMARY KEY (prompt_id, prompt_version, llm_role),
  FOREIGN KEY (prompt_id, prompt_version)
    REFERENCES dataplane.prompt_packs (prompt_id, prompt_version),
  CONSTRAINT prompt_role_templates_llm_role_chk CHECK (llm_role <> 'none'),
  CONSTRAINT prompt_role_templates_task_type_chk
    CHECK (task_type IN ('plan', 'synthesize', 'classify'))
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
(
  'msa_risk_review_v1',
  '2026.08.1',
  'You are counsel''s MSA risk-review worker. Do only the current stage. Do not choose the next stage. Do not invent tools.',
  'published',
  'legal-agents'
),
(
  'email_summarize_v2',
  '2026.08.1',
  'Summarize this email for the banker. No tools. Return short bullets.',
  'published',
  'assistant-platform'
),
(
  'fee_explain_v0',
  '2026.04.1',
  'Look up why an account fee posted.',
  'deprecated',
  'assistant-platform'
),
(
  'fee_explain_v1',
  '2026.08.1',
  'You explain account fees. Use the fee lookup tool. Do not invent charges.',
  'published',
  'assistant-platform'
),
(
  'account_history_v3',
  '2026.08.1',
  'Answer account and transaction history questions. Read-only tools only.',
  'published',
  'assistant-platform'
),
(
  'payments_v2',
  '2026.08.1',
  'Help initiate an outbound payment. Do not skip validation.',
  'published',
  'payments-agents'
),
(
  'policy_qa_v1',
  '2026.08.1',
  'Answer from retrieved policy text only. Do not invent policy.',
  'published',
  'assistant-platform'
),
(
  'chat_v1',
  '2026.08.1',
  'Be a concise corporate assistant. No tools.',
  'published',
  'assistant-platform'
),
(
  'escalate_v1',
  '2026.08.1',
  'Hand the conversation to a human agent. Do not continue the task.',
  'published',
  'assistant-platform'
);

INSERT INTO dataplane.prompt_role_templates (
  prompt_id, prompt_version, llm_role, task_type, "text"
) VALUES
(
  'msa_risk_review_v1',
  '2026.08.1',
  'query_formulation',
  'plan',
  'Write the search query for this stage''s corpus only. Do not pick a different index.'
),
(
  'msa_risk_review_v1',
  '2026.08.1',
  'synthesis',
  'synthesize',
  'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'
);
