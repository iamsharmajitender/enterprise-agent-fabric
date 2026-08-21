CREATE TABLE IF NOT EXISTS registry.capabilities (
  id TEXT NOT NULL,
  version TEXT NOT NULL,
  kind TEXT NOT NULL,
  description TEXT,
  input_schema JSONB NOT NULL,
  output_schema JSONB NOT NULL,
  invoke JSONB NOT NULL,
  snippet TEXT,
  owner TEXT,
  status TEXT NOT NULL,
  PRIMARY KEY (id, version)
);

CREATE TABLE IF NOT EXISTS registry.manifests (
  manifest_id TEXT NOT NULL,
  manifest_version TEXT NOT NULL,
  tools JSONB NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (manifest_id, manifest_version)
);
