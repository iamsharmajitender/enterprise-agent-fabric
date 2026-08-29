-- overdraft_fee_qa — Layer ① command for deterministic chat demos.

\c adp
INSERT INTO dataplane.intent_rules (rule_id, match_kind, match_value, route_id, sort_order) VALUES
  ('cmd-overdraft', 'command', '/overdraft', 'overdraft_fee_qa', 20)
ON CONFLICT (rule_id) DO NOTHING;
