ALTER TABLE dataplane.routes
  ADD COLUMN route_version TEXT,
  ADD COLUMN active BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE dataplane.routes SET route_version = route_table_version;

UPDATE dataplane.routes r
   SET active = TRUE
  FROM dataplane.route_tables t
 WHERE r.route_table_version = t.route_table_version
   AND t.active = TRUE;

ALTER TABLE dataplane.routes ALTER COLUMN route_version SET NOT NULL;

ALTER TABLE dataplane.retrieval ADD COLUMN route_version TEXT;
UPDATE dataplane.retrieval SET route_version = route_table_version;
ALTER TABLE dataplane.retrieval ALTER COLUMN route_version SET NOT NULL;

ALTER TABLE dataplane.memory_profiles ADD COLUMN route_version TEXT;
UPDATE dataplane.memory_profiles SET route_version = route_table_version;
ALTER TABLE dataplane.memory_profiles ALTER COLUMN route_version SET NOT NULL;

ALTER TABLE dataplane.retrieval DROP CONSTRAINT retrieval_route_id_route_table_version_fkey;
ALTER TABLE dataplane.memory_profiles DROP CONSTRAINT memory_profiles_route_id_route_table_version_fkey;

ALTER TABLE dataplane.retrieval DROP CONSTRAINT retrieval_pkey;
ALTER TABLE dataplane.memory_profiles DROP CONSTRAINT memory_profiles_pkey;

ALTER TABLE dataplane.routes DROP CONSTRAINT routes_route_table_version_fkey;
ALTER TABLE dataplane.routes DROP CONSTRAINT routes_pkey;

ALTER TABLE dataplane.routes DROP COLUMN route_table_version;
ALTER TABLE dataplane.retrieval DROP COLUMN route_table_version;
ALTER TABLE dataplane.memory_profiles DROP COLUMN route_table_version;

ALTER TABLE dataplane.routes ADD PRIMARY KEY (route_id, route_version);
ALTER TABLE dataplane.retrieval ADD PRIMARY KEY (route_id, route_version);
ALTER TABLE dataplane.memory_profiles ADD PRIMARY KEY (route_id, route_version);

ALTER TABLE dataplane.retrieval
  ADD CONSTRAINT retrieval_route_fk
  FOREIGN KEY (route_id, route_version)
  REFERENCES dataplane.routes (route_id, route_version);

ALTER TABLE dataplane.memory_profiles
  ADD CONSTRAINT memory_profiles_route_fk
  FOREIGN KEY (route_id, route_version)
  REFERENCES dataplane.routes (route_id, route_version);

CREATE UNIQUE INDEX dataplane_one_active_version_per_route
  ON dataplane.routes (route_id)
  WHERE active;

DROP TABLE dataplane.route_tables;
