CREATE TABLE dataplane.route_tables (
  route_table_version TEXT PRIMARY KEY,
  product TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX dataplane_one_active_table
  ON dataplane.route_tables (active)
  WHERE active;

CREATE TABLE dataplane.routes (
  route_id TEXT NOT NULL,
  route_table_version TEXT NOT NULL REFERENCES dataplane.route_tables (route_table_version),
  intent_label TEXT NOT NULL,
  description TEXT,
  activation_target TEXT,
  agent_client_id TEXT,
  tool_manifest TEXT NOT NULL,
  tool_manifest_version TEXT,
  policy_profile TEXT NOT NULL,
  model_profile TEXT NOT NULL,
  retrieval JSONB,
  memory_profile JSONB,
  workflow_id TEXT,
  prompt_id TEXT,
  output_schema_id TEXT,
  eval_suite_id TEXT,
  max_loop_steps INTEGER,
  fallback TEXT,
  required_claims JSONB NOT NULL DEFAULT '[]'::jsonb,
  channels JSONB NOT NULL DEFAULT '["web"]'::jsonb,
  chat_visible BOOLEAN NOT NULL DEFAULT TRUE,
  keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (route_id, route_table_version)
);
