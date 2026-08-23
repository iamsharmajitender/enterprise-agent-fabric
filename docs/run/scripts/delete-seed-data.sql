-- Wipe catalogue + lifecycle seed in Capability Registry (acr) and Data Plane (adp).
-- Does not drop schema or model profiles. Flyway corpora are kept; lifecycle corpora are removed.
-- Run via ./docs/run/scripts/seed-db.sh (first of two).

\c acr
DELETE FROM registry.manifests;
DELETE FROM registry.capabilities;

\c adp
DELETE FROM dataplane.retrieval;
DELETE FROM dataplane.memory_profiles;
DELETE FROM dataplane.routes;
DELETE FROM dataplane.prompt_role_templates;
DELETE FROM dataplane.prompt_packs;
DELETE FROM dataplane.workflows;
DELETE FROM dataplane.manifests;
DELETE FROM dataplane.corpora
 WHERE corpus_id IN ('credit-policy', 'research-notes', 'fax-archive');
