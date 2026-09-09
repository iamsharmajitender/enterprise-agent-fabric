---
title: User uploads bytes
sidebar_label: Files as bytes
---

# User uploads bytes

The channel request carries file bytes. The fabric must not keep them. **Front Door** is the only box that may see bytes: entitle the route, enforce the route allowlist, PUT to the DMS, mint an id, then start Runtime with JSON `goal` only.

After mint, this use case is identical to [files-via-dms](/use-cases/files-via-dms). The domain tool GETs the DMS. Runtime and the LLM never see bytes.

Prefer DMS-first when the UI can talk to the DMS (presigned PUT **to the DMS**, then jobs JSON). Use this page only when the caller cannot.

## Who does what

```
UI / partner
    │  multipart: payload JSON + part "document" (bytes)
    ▼
Front Door
    │  entitle route
    │  if no ingress_files row → 415
    │  if count / mime / size / part name miss → 422
    │  PUT bytes → DMS  →  mint doc_id
    │  write goal.doc_id (map). drop bytes.
    ▼
Runtime  →  POST dict(goal) to ocr_extract  →  DMS GET  →  notes text
```

**Who must not upload:** Runtime, the LLM, Data Plane, Capability Registry, `ocr_extract` (that tool **reads** the DMS).

Bind the PUT to the entitled `route_id` and jobs `idempotency_key`. A `fee_explain` caller must not mint objects into Legal’s vault.

## Route contract (opt-in)

Omitted `ingress_files` means JSON only — today’s behaviour. Present means this use case is allowed.

```json
{
  "ingress_files": {
    "max_count": 1,
    "max_bytes": 10485760,
    "mime": ["application/pdf", "image/png"],
    "map": [{ "part": "document", "goal_key": "doc_id" }]
  }
}
```

| Field | Allows |
| --- | --- |
| `max_count` | How many file parts. `1` = one document. |
| `max_bytes` | Per-file cap (here 10 MiB). Ingress, not token budget. |
| `mime` | Allowlist. Sniff magic bytes; do not trust the filename. |
| `map.part` | Multipart field name the caller must use (`document`). |
| `map.goal_key` | Catalogue key on `goal` (`doc_id` matches `ocr_extract` `input_schema`). |

`part` is the channel name. `goal_key` is the capability name. Do not invent a fabric-wide `files[]` that every HTTP body would have to understand.

Sibling of `retrieval` and `memory_profile` on the route. Not a fifth `autonomy_mode`. Example composition: [`msa_risk_review`](/catalogue/seed-use-cases) would keep Pattern 2, retrieval, memory, and add this block.

## Request

```http
POST /v1/jobs
Content-Type: multipart/form-data

route_id=msa_risk_review
idempotency_key=job-4412:v1
payload={"matter_id":"m-88"}
document=<msa.pdf; application/pdf>
```

After intake, Runtime `goal`:

```json
{ "doc_id": "dms:msa-19", "matter_id": "m-88" }
```

JSON-only `{ "doc_id": "dms:msa-19" }` stays legal on the same route (DMS-first). **File part and `payload.doc_id` together → 422** (one source of truth).

## Chat

Jobs with an explicit `route_id` are the first path (entitle, then accept parts). Chat must not accept files on an unrouted first turn. After freeze, the same `ingress_files` row may apply. Until then, reject.

## Pattern 0

A single synthesis node has no OCR tool. Either the caller still sends `text`, or this route should not be Pattern 0. Do not hide an OCR HTTP call inside Pattern 0.

## Not this use case

| Shape | Where |
| --- | --- |
| Ids or presigned GET already in JSON | [files-via-dms](/use-cases/files-via-dms) |
| Base64 on `goal` | Never |
| Multipart through Runtime | Never |
| Free `POST /v1/files` unbound to a route | Never (confused deputy) |

## Status

| Piece | Now |
| --- | --- |
| JSON jobs / chat | Yes |
| `ingress_files` on the catalogue | No |
| Front Door multipart + DMS PUT | No |
| Runtime blob store | Never planned. DMS only. |
