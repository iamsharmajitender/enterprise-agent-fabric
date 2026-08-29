CREATE SCHEMA IF NOT EXISTS runtime;

CREATE TABLE runtime.runs (
  correlation_id TEXT PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  session_id TEXT NOT NULL,
  route_id TEXT NOT NULL,
  route_version TEXT NOT NULL,
  activation_target TEXT,
  agent_client_id TEXT,
  hydrated_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL,
  result JSONB,
  checkpoint JSONB,
  working JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX runs_session_status ON runtime.runs (session_id, status);
