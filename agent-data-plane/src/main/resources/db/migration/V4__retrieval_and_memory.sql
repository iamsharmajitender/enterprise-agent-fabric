CREATE TABLE dataplane.retrieval (
  route_id TEXT NOT NULL,
  route_table_version TEXT NOT NULL,
  mode TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (route_id, route_table_version),
  FOREIGN KEY (route_id, route_table_version)
    REFERENCES dataplane.routes (route_id, route_table_version)
);

CREATE TABLE dataplane.memory_profiles (
  route_id TEXT NOT NULL,
  route_table_version TEXT NOT NULL,
  conversation TEXT,
  working TEXT,
  "loop" TEXT,
  long_term TEXT,
  ttl_hours INTEGER,
  isolation JSONB NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (route_id, route_table_version),
  FOREIGN KEY (route_id, route_table_version)
    REFERENCES dataplane.routes (route_id, route_table_version)
);

INSERT INTO dataplane.retrieval (route_id, route_table_version, mode, scope)
SELECT route_id,
       route_table_version,
       retrieval->>'mode',
       COALESCE(retrieval->'scope', '[]'::jsonb)
  FROM dataplane.routes
 WHERE retrieval IS NOT NULL
   AND retrieval->>'mode' IS NOT NULL;

INSERT INTO dataplane.memory_profiles (
  route_id, route_table_version, conversation, working, "loop", long_term, ttl_hours, isolation
)
SELECT route_id,
       route_table_version,
       memory_profile->>'conversation',
       memory_profile->>'working',
       memory_profile->>'loop',
       memory_profile->>'long_term',
       NULLIF(memory_profile->>'ttl_hours', '')::integer,
       COALESCE(memory_profile->'isolation', '[]'::jsonb)
  FROM dataplane.routes
 WHERE memory_profile IS NOT NULL;

ALTER TABLE dataplane.routes DROP COLUMN retrieval;
ALTER TABLE dataplane.routes DROP COLUMN memory_profile;
