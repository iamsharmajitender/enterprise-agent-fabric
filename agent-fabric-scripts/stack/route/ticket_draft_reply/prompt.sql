-- ticket_draft_reply — child route prompt (Pattern 0 synthesis for parent ticket_triage).

\c adp
INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
(
  'ticket_draft_reply', '2026.08.1',
  'Pattern 0 child agent. Draft a short, professional customer reply using only the job payload fields (utterance, category, order_ref, intent, priority). Do not invent order ids, charges, or policy outcomes.',
  'published',
  'support'
)
ON CONFLICT (prompt_id, prompt_version) DO UPDATE SET
  host = EXCLUDED.host,
  status = EXCLUDED.status;
