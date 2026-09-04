-- ticket_triage — Pattern 3 host + synthesis prompt.

\c adp
INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
(
  'ticket_triage', '2026.08.1',
  'Pattern 3. Outer stages are fixed. Inside an allowlisted stage the model may CALL only tools on that stage allowlist (catalogue metadata today). Reply stage starts ticket_draft_reply child agent with join. After join, return the drafted customer reply from the joined subagent output verbatim — do not invent tool calls.',
  'published',
  'support'
)
ON CONFLICT (prompt_id, prompt_version) DO UPDATE SET
  host = EXCLUDED.host,
  status = EXCLUDED.status;
