-- Wipe all application data across fabric Postgres databases.
-- Schemas and tables remain (Flyway). Run via ./delete-seed-data.sh

\c acr
TRUNCATE registry.manifests, registry.capabilities CASCADE;

\c adp
TRUNCATE
  dataplane.retrieval,
  dataplane.memory_profiles,
  dataplane.routes,
  dataplane.prompt_role_templates,
  dataplane.prompt_packs,
  dataplane.workflows,
  dataplane.manifests,
  dataplane.intent_rules,
  dataplane.corpora,
  dataplane.model_profiles
CASCADE;

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
  )
ON CONFLICT (id) DO NOTHING;

\c afd
TRUNCATE frontdoor.freeze, frontdoor.opaque_ids CASCADE;

\c ar
TRUNCATE runtime.runs CASCADE;

\c audit
TRUNCATE audit.events;
