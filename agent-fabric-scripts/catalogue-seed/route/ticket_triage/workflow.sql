-- ticket_triage — Pattern 3 workflow (fixed outer stages + per-stage allowlists).

\c adp
INSERT INTO dataplane.workflows (
  workflow_id, workflow_version, description, stages, status
) VALUES
(
  'ticket_triage', '2026.08.1',
  'Pattern 3: parse ticket, tag intent, then start ticket_draft_reply child agent (kind=agent join). Inner CALL/DONE per allowlist is catalogue-only in this Runtime.',
  $$[
    {"id":"extract","tool":"parse_ticket","llm_role":"none","allowlist":["parse_ticket"],"max_tool_calls":2},
    {"id":"analyse","tool":"tag_intent","llm_role":"none","allowlist":["parse_ticket","tag_intent"],"max_tool_calls":4},
    {"id":"reply","tool":"draft_reply","llm_role":"none","allowlist":["draft_reply"],"max_tool_calls":2}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (workflow_id, workflow_version) DO UPDATE SET
  description = EXCLUDED.description,
  stages = EXCLUDED.stages,
  status = EXCLUDED.status;
