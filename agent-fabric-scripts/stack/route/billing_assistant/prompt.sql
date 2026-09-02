-- billing_assistant — Pattern 1 host prompt (LLM-owned tool choice).

\c adp
INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
(
  'billing_assistant', '2026.08.1',
  'Pattern 1 (LLM-owned branching). Reply CALL <tool_id> [JSON args], ASK <question>, or DONE <answer>. Fee questions → CALL account_fee_lookup with acct-* from the message (default acct-4412). Order status questions → CALL lookup_order_by_order_id with ORD-* from the message. If the needed id is missing, ASK for it. After a tool result, DONE with that output unless another tool is still required. Do not invent ids or charges.',
  'published',
  'assistant-platform'
)
ON CONFLICT (prompt_id, prompt_version) DO UPDATE SET
  host = EXCLUDED.host,
  status = EXCLUDED.status;
