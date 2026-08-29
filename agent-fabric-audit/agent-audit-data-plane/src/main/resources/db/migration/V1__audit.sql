-- Append-only fabric audit events. Application must not UPDATE/DELETE rows for rewrite.
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.events (
  event_id         UUID PRIMARY KEY,
  event_type       TEXT NOT NULL,
  occurred_at      TIMESTAMPTZ NOT NULL,
  producer         TEXT NOT NULL,
  correlation_id   TEXT,
  session_id       TEXT,
  decision_id      TEXT,
  payload          JSONB NOT NULL,
  received_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_events_correlation ON audit.events (correlation_id, occurred_at, received_at);
CREATE INDEX idx_audit_events_session ON audit.events (session_id, occurred_at, received_at);
CREATE INDEX idx_audit_events_type_time ON audit.events (event_type, occurred_at);
