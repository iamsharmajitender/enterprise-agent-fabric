-- shopassist_case — Layer ① command for deterministic chat demos.

\c adp
INSERT INTO dataplane.intent_rules (rule_id, match_kind, match_value, route_id, sort_order) VALUES
  ('cmd-shopassist', 'command', '/shopassist', 'shopassist_case', 10)
ON CONFLICT (rule_id) DO NOTHING;
