CREATE TABLE frontdoor.freeze (
  session_id TEXT PRIMARY KEY,
  idempotency_key TEXT,
  route_id TEXT,
  route_version TEXT,
  activation_target TEXT,
  agent_client_id TEXT,
  correlation_id TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE frontdoor.opaque_ids (
  session_id TEXT NOT NULL,
  opaque_id TEXT NOT NULL,
  route_id TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (session_id, opaque_id)
);
