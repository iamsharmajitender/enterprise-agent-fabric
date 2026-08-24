-- Layer ① command rules. First match (sort_order) wins. route_id must still be eligible or decide abstains.
CREATE TABLE dataplane.intent_rules (
  rule_id TEXT PRIMARY KEY,
  match_kind TEXT NOT NULL,
  match_value TEXT NOT NULL,
  route_id TEXT NOT NULL,
  sort_order INT NOT NULL,
  UNIQUE (match_kind, match_value),
  CONSTRAINT intent_rules_kind_chk CHECK (match_kind IN ('command', 'topic'))
);

INSERT INTO dataplane.intent_rules (rule_id, match_kind, match_value, route_id, sort_order) VALUES
  ('cmd-hr', 'command', '/hr', 'agent-chat', 10),
  ('cmd-human', 'command', 'talk to a human', 'agent-chat', 20),
  ('cmd-freeze', 'command', '/freeze', 'card_freeze', 30);
