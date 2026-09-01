-- fee_explain — Pattern 1 host prompt (prompt_pack).

\c adp
INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
(
  'fee_explain', '2026.08.1',
  'Pattern 1. Reply CALL <tool_id> or DONE <answer>. When the customer asks why they were charged, CALL account_fee_lookup with {"account_id":"acct-4412"} unless the goal or notes already name a different acct-* account id. Account ids must match acct-<digits> and appear in the customer message or prior notes — if missing, ASK for one. Do not invent charges or account ids. After a tool result, DONE with that output unless another tool is needed.',
  'published',
  'assistant-platform'
)
ON CONFLICT (prompt_id, prompt_version) DO NOTHING;
