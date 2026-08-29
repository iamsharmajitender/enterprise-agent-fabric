# Agent Control Plane

Catalogue **browser** for the local fabric. TypeScript process serves a static UI on **3006**. It has **no Fabric APIs** and **no database**. It only calls Data Plane (and Registry for capability detail) with workload identity `acp`.

## Job

Let an operator browse routes, prompts, workflows, corpora, and capability/manifest pointers. Do **not** classify turns, start Runtime, or sit on the chat/jobs hot path. Decide is **AFD-only**.

## Port / stack

| | |
| --- | --- |
| Port | **3006** (UI only) |
| Stack | TypeScript, Node 22, static UI + small HTTP server for assets/API proxy to siblings |
| Database | **None** |
| Compose | `agent-control-plane` |
| Auth (outbound) | `Authorization: Bearer fabric-internal` + `X-Workload: acp` |

Docs map: [docs/README.md](../../agent-fabric-docs/README.md). Stub auth: [05-reference/stub-auth.md](../../agent-fabric-docs/05-reference/stub-auth.md).

## Hexagonal layout

Not Java hexagonal. Layout:

| Path | Role |
| --- | --- |
| `src/ui-server.ts` | Serves `public/` and thin proxy helpers |
| `src/data-plane-client.ts` | Outbound ADP catalogue / eligible GETs |
| `src/registry-client.ts` | Outbound ACR capability/manifest GETs |
| `src/workload.ts` | `X-Workload: acp` headers |
| `public/` | Browser UI (`index.html`, `app.js`, styles) |

## Auth

Inbound: browser opens `http://localhost:3006` (no channel bearer required for local demo).

Outbound to siblings:

```http
Authorization: Bearer fabric-internal
X-Workload: acp
```

Optional: `X-Stub-Claims` when fetching eligible chips for a stub identity.

## APIs

**None** as a Fabric box. This process does not expose decide, jobs, or runs. The UI is not a substitute for Front Door.

## Contracts

Consumes ADP / ACR JSON as returned by those services. Frozen shapes live under [docs/05-reference/](../../agent-fabric-docs/05-reference/). This folder does not publish contract fixtures.

## Tables / schema

**No database.** Do not add `acp` Postgres. Catalogue truth stays on `adp` / `acr`.

## Sibling calls

| Direction | Call | Notes |
| --- | --- | --- |
| Out | ADP `GET /v1/intent/eligible` | Optional chips for stub claims |
| Out | ADP `GET /v1/catalog/routes` (+ `{id}`, versions) | Route matrix |
| Out | ADP `GET /v1/catalog/prompts|workflows|corpora|…` | Catalogue tabs |
| Out | ACR `GET /v1/capabilities…` / `GET /v1/manifests…` | Capability detail |
| Out | ADP `POST /v1/intent/decide` | **Forbidden** — ADP returns **403** for `acp` |
| In | — | Channels never call this process for a turn |

## Non-goals

- Decide, freeze, or `POST /v1/runs`
- Owning route/capability SQL
- Audit / decisions store
- Replacing Control Plane with a second Front Door

## Tests

```bash
cd agent-control-plane && npm test
```

Covers workload headers, data-plane / registry clients, UI server smoke, catalogue helpers.
