-- Extra databases on the single Postgres 16 server.
-- POSTGRES_DB already created `afd`. Do not create `acp` or `aacp` (control planes have no database).

CREATE DATABASE adp;
CREATE DATABASE ar;
CREATE DATABASE acr;
CREATE DATABASE audit;
