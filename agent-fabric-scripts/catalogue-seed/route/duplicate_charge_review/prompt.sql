-- duplicate_charge_review — Pattern 2 prompt pack (classify + synthesis roles).

\c adp
INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
(
  'duplicate_charge_review', '2026.08.1',
  'Pattern 2. Do only the current stage. Do not choose the next tool. Do not invent order ids or charges.',
  'published',
  'shopassist'
)
ON CONFLICT (prompt_id, prompt_version) DO UPDATE SET
  host = EXCLUDED.host,
  status = EXCLUDED.status;

INSERT INTO dataplane.prompt_role_templates (
  prompt_id, prompt_version, llm_role, task_type, text
) VALUES
(
  'duplicate_charge_review', '2026.08.1', 'classify', 'classify',
  'Extract order_id from the goal utterance only. Return JSON with order_id matching ORD-<digits>. Do not invent ids.'
),
(
  'duplicate_charge_review', '2026.08.1', 'synthesis', 'synthesize',
  'Write a short customer reply about the duplicate-charge finding using prior stage outputs only. Mention order id and whether a duplicate capture was found.'
)
ON CONFLICT (prompt_id, prompt_version, llm_role) DO UPDATE SET
  task_type = EXCLUDED.task_type,
  text = EXCLUDED.text;
