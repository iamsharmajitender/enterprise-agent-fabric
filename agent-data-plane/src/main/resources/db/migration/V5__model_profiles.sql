CREATE TABLE dataplane.model_profiles (
  id TEXT PRIMARY KEY,
  typical_use TEXT NOT NULL
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

ALTER TABLE dataplane.routes
  ADD CONSTRAINT routes_model_profile_fk
  FOREIGN KEY (model_profile) REFERENCES dataplane.model_profiles (id);
