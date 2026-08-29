# Agent Capability Registry

Published **capabilities** and **tool manifests** (`id@version`). Runtime hydrates from here after Front Door pins a route. This box does **not** decide, start runs, or invoke tools.

## Job

Own the immutable catalogue of tool schemas and `invoke` URLs. Publishers `PUT` draft/published cuts. Runtime (`ar`) and Control Plane (`acp`) `GET` published pins. Do not invent a “latest” for a missing version — the caller names `(id, version)`.

## Port / stack

| | |
| --- | --- |
| Port | **3009** |
| Stack | Java 21, Spring Boot 3.5, Flyway |
| Database | `acr` (schema `registry`) |
| Compose | `agent-capability-registry` |
| Auth | Workload only: `Authorization: Bearer fabric-internal` + `X-Workload` |

Docs map: [docs/README.md](../agent-fabric-docs/README.md). Box pack: [docs/04-architecture/agent-capability-registry.md](../agent-fabric-docs/04-architecture/agent-capability-registry.md). Stub auth: [05-reference/stub-auth.md](../agent-fabric-docs/05-reference/stub-auth.md).

## Hexagonal layout

| Package | Role |
| --- | --- |
| `domain` | Capability/manifest records, `PublishedConflictException`. No Spring or SQL. |
| `application` | `CapabilityService`, `ManifestService`, store ports |
| `adapters.in.http` | Controllers, workload auth filter, health |
| `adapters.out.jdbc` | Flyway-backed stores |

## Auth

Every path except `GET /health`:

```http
Authorization: Bearer fabric-internal
X-Workload: ar
```

`X-Workload` is one of `afd` · `adp` · `acp` · `ar` · `acr`. Channel `Bearer stub` → **401**.

| Caller | Typical use |
| --- | --- |
| `ar` | Hydrate: GET published capability / manifest at pin. **Draft GET fails closed** (not 200). |
| `acp` | Catalogue UI browse |
| Others | May GET published rows; publishers `PUT` with a workload identity |

## APIs

Base: `http://localhost:3009`.

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/health` | No auth. `{"status":"UP"}` |
| `GET` | `/v1/capabilities` | Published search (`?q=`). `?include=all` includes drafts |
| `GET` | `/v1/capabilities/{id}` | Latest for workload (AR skips drafts) |
| `GET` | `/v1/capabilities/{id}/versions` | Version list |
| `GET` | `/v1/capabilities/{id}/versions/{version}` | Exact pin. AR + draft → fail closed |
| `PUT` | `/v1/capabilities/{id}/versions/{version}` | Upsert. Body includes `kind`, schemas, `invoke`, `status` (`draft` / `published`) |
| `PUT` | `/v1/manifests/{manifestId}/versions/{manifestVersion}` | Upsert tools JSON + status |
| `GET` | `/v1/manifests/{manifestId}/versions/{manifestVersion}` | Exact pin. AR + draft → fail closed |

**Immutability:** a second `PUT` of an already **published** `(id, version)` or `(manifest_id, manifest_version)` → **409**.

Capability body fields: `id`, `version`, `kind` (`domain` / `agent`), `description`, `input_schema`, `output_schema`, `invoke` (`method`, `url`, `auth`), `snippet`, `owner`, `status`.

Manifest body fields: `manifest_id`, `manifest_version`, `tools[]` (`name`, `capability_id`, `capability_version`, `pdp_action`, `risk_tier`), `status`.

## Contracts

- [`agent-fabric-docs/05-reference/capability-account-fee-lookup.json`](../agent-fabric-docs/05-reference/capability-account-fee-lookup.json)
- [`agent-fabric-docs/05-reference/manifest-fee-explain.json`](../agent-fabric-docs/05-reference/manifest-fee-explain.json)
- [`agent-fabric-docs/05-reference/stub-auth.md`](../agent-fabric-docs/05-reference/stub-auth.md)

## Tables / schema

Flyway `V1__registry.sql` on database `acr`:

| Table | Primary key | Holds |
| --- | --- | --- |
| `registry.capabilities` | `(id, version)` | kind, schemas, invoke JSON, status |
| `registry.manifests` | `(manifest_id, manifest_version)` | tools JSON, status |

Seed includes **`account_fee_lookup@1.0.0`** (published domain tool) and manifest **`fee_explain@2026.08.1`** that refs it. Operational reload: `./agent-fabric-scripts/catalogue-seed/add-seed-data.sh` (and Compose migrations).

## Sibling calls

| Direction | Who | Notes |
| --- | --- | --- |
| In | Runtime (`ar`) | Hydrate GET at pin — published only |
| In | Control Plane (`acp`) | UI list/detail |
| Out | — | This box does not call ADP, AFD, or AR |

## Non-goals

- Decide / eligible / classify
- Starting Runtime or owning run pins
- HTTP-invoking `invoke.url` (Runtime + agent-fabric-mocks)
- PDP / Shared PEP enforcement
- Channel-facing APIs

## Tests

Image build runs `mvn test`. Locally (JDK 21):

```bash
cd agent-capability-registry && mvn -q -B test
```

Covers publish/get, **409** on published overwrite, AR GET of draft fails closed, seed SQL smoke.
