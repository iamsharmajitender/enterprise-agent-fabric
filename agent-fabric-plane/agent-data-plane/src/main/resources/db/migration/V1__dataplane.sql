-- Baseline schema for database adp.
CREATE SCHEMA IF NOT EXISTS dataplane;

CREATE TABLE dataplane.model_profiles (
  id TEXT PRIMARY KEY,
  typical_use TEXT NOT NULL
);

CREATE TABLE dataplane.corpora (
  corpus_id     TEXT PRIMARY KEY,
  display_name  TEXT NOT NULL,
  url           TEXT NOT NULL,
  collection    TEXT,
  auth          TEXT NOT NULL DEFAULT 'workload-oauth',
  owner         TEXT NOT NULL,
  status        TEXT NOT NULL CHECK (status IN ('draft', 'published', 'deprecated')),
  region        TEXT,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dataplane.manifests (
  manifest_id TEXT NOT NULL,
  manifest_version TEXT NOT NULL,
  description TEXT,
  tools JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'published',
  PRIMARY KEY (manifest_id, manifest_version),
  CONSTRAINT manifests_status_chk CHECK (status IN ('draft', 'published', 'retired'))
);

CREATE TABLE dataplane.prompt_packs (
  prompt_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  host TEXT NOT NULL,
  status TEXT NOT NULL,
  owner TEXT NOT NULL,
  PRIMARY KEY (prompt_id, prompt_version),
  CONSTRAINT prompt_packs_status_chk CHECK (status IN ('draft', 'published', 'deprecated'))
);

CREATE TABLE dataplane.prompt_role_templates (
  prompt_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  llm_role TEXT NOT NULL,
  task_type TEXT NOT NULL,
  text TEXT NOT NULL,
  PRIMARY KEY (prompt_id, prompt_version, llm_role),
  FOREIGN KEY (prompt_id, prompt_version)
    REFERENCES dataplane.prompt_packs (prompt_id, prompt_version),
  CONSTRAINT prompt_role_templates_llm_role_chk CHECK (llm_role <> 'none'),
  CONSTRAINT prompt_role_templates_task_type_chk
    CHECK (task_type IN ('plan', 'synthesize', 'classify'))
);

CREATE TABLE dataplane.workflows (
  workflow_id TEXT NOT NULL,
  workflow_version TEXT NOT NULL,
  description TEXT,
  stages JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL,
  PRIMARY KEY (workflow_id, workflow_version),
  CONSTRAINT workflows_status_chk CHECK (status IN ('draft', 'published', 'deprecated'))
);

CREATE UNIQUE INDEX workflows_one_published
  ON dataplane.workflows (workflow_id)
  WHERE status = 'published';

CREATE TABLE dataplane.routes (
  route_id TEXT NOT NULL,
  intent_label TEXT NOT NULL,
  description TEXT,
  activation_target TEXT,
  agent_client_id TEXT,
  tool_manifest TEXT,
  tool_manifest_version TEXT,
  policy_profile TEXT NOT NULL,
  model_profile TEXT NOT NULL,
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
  route_version TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  status TEXT NOT NULL DEFAULT 'published',
  autonomy_mode SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (route_id, route_version),
  CONSTRAINT routes_autonomy_mode_chk CHECK (autonomy_mode >= 0 AND autonomy_mode <= 3),
  CONSTRAINT routes_status_chk CHECK (status IN ('draft', 'published', 'active', 'retired')),
  CONSTRAINT routes_status_active_chk CHECK (
    (active AND status = 'active') OR ((NOT active) AND status <> 'active')
  ),
  CONSTRAINT routes_model_profile_fk FOREIGN KEY (model_profile)
    REFERENCES dataplane.model_profiles (id),
  CONSTRAINT routes_tool_manifest_fk FOREIGN KEY (tool_manifest, tool_manifest_version)
    REFERENCES dataplane.manifests (manifest_id, manifest_version)
);

CREATE UNIQUE INDEX dataplane_one_active_version_per_route
  ON dataplane.routes (route_id)
  WHERE active;

CREATE TABLE dataplane.retrieval (
  route_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '[]'::jsonb,
  route_version TEXT NOT NULL,
  PRIMARY KEY (route_id, route_version),
  CONSTRAINT retrieval_route_fk FOREIGN KEY (route_id, route_version)
    REFERENCES dataplane.routes (route_id, route_version)
);

CREATE TABLE dataplane.memory_profiles (
  route_id TEXT NOT NULL,
  conversation TEXT,
  working TEXT,
  "loop" TEXT,
  long_term TEXT,
  ttl_hours INTEGER,
  isolation JSONB NOT NULL DEFAULT '[]'::jsonb,
  route_version TEXT NOT NULL,
  PRIMARY KEY (route_id, route_version),
  CONSTRAINT memory_profiles_route_fk FOREIGN KEY (route_id, route_version)
    REFERENCES dataplane.routes (route_id, route_version)
);

INSERT INTO dataplane.model_profiles (id, typical_use) VALUES
  (
    'reasoning-standard',
    'Plan / multi-step / high-stakes synthesis. Capability matrix + most route examples.'
  ),
  (
    'fast-chat',
    'Cheap synthesize / classify. Capability matrix + inference handoff.'
  ),
  (
    'lightweight-chat',
    'No-tools / cheap chat. Route contract examples (general_chat, escalate_human). Same idea as fast-chat.'
  );

