# Files via DMS (id vs presigned)

The caller never sends file bytes to the fabric. The enterprise document management system (DMS) already holds the object. The request is JSON. The **domain tool** (for example `ocr_extract`) fetches the bytes from the DMS.

This is the default document shape. Routes that only need this use case **omit** `ingress_files`. Front Door rejects multipart.

## Who does what

```
UI / partner
    │  (optional) PUT bytes via DMS presigned upload — outside the fabric
    ▼
DMS  ── already stores the object ──  doc_id (durable)
    │
    │  jobs/chat JSON: doc_id  or  doc_url (presigned GET)
    ▼
Front Door  →  copies payload onto goal  →  Runtime
    │
    │  POST dict(goal) to ocr_extract
    ▼
Domain tool  →  GET from DMS (by id or presigned URL)  →  { text }
    │
    ▼
Runtime notes  (string only). LLM never sees bytes.
```

Front Door does not GET the DMS. Runtime does not GET the DMS.

## Variant A — durable id (preferred)

The UI uploaded earlier, or the object already existed. The job names the DMS id.

```json
{
  "route_id": "msa_risk_review",
  "idempotency_key": "job-4412:v1",
  "payload": { "doc_id": "dms:msa-19" }
}
```

`goal` for the whole run:

```json
{ "doc_id": "dms:msa-19" }
```

`ocr_extract` POSTs that object. The tool uses its own DMS credentials (or asks DMS for a short-lived GET) and reads `dms:msa-19`.

**Use when** the DMS can authorize a service identity. The signed URL never sits on the run pin or in logs.

Seed illustration: [`msa_risk_review`](../03-catalogue/routes.md#msa_risk_review), [`contract_review`](../03-catalogue/routes.md#contract_review) — payload key `doc_id`.

## Variant B — presigned GET in the request

The UI asked the DMS for a short-lived GET URL and put that URL on the payload. The domain tool GETs that URL. The UI must **not** pass a presigned **PUT** URL into the job.

```json
{
  "route_id": "msa_risk_review",
  "idempotency_key": "job-4412:v1",
  "payload": {
    "doc_id": "dms:msa-19",
    "doc_url": "https://dms.example/objects/msa-19?X-Amz-Expires=300&sig=…"
  }
}
```

Prefer still sending `doc_id` next to the URL so a later stage can re-resolve after expiry.

**Use when** the tool cannot hold DMS credentials and can only GET a caller-supplied URL.

### Limits (this Runtime, and the design)

| Risk | Why |
| --- | --- |
| Goal is copied onto **every** HTTP tool | Today `payload = dict(goal)`. `risk_engine` would receive `doc_url` too. Treat the URL as a secret. Later: fill from `input_schema` / slots so only OCR sees it. |
| Expiry | A 5-minute URL dies on a long Pattern 1 loop. First OCR stage must fetch, or the tool re-resolves by `doc_id`. |
| Logs | `goal` is logged. Query-string `sig=` is a credential. Prefer variant A. |
| Chat freeze | A later turn reuses `goal`. A dead URL fails OCR on retry unless `doc_id` remains. |

## Several documents

Still JSON. Pick one payload shape and keep it on the capability schema:

```json
{ "doc_id": "dms:msa-19", "annex_ids": ["dms:a-1", "dms:a-2"] }
```

or

```json
{ "doc_ids": ["dms:msa-19", "dms:a-1"] }
```

`ocr_extract` today requires a single `doc_id`. Many ids means the tool accepts an array, or the workflow / CALL loop invokes OCR once per id. The fabric still never opens the file.

## Not this use case

| Shape | Where |
| --- | --- |
| Multipart bytes on Front Door | [files-bytes-upload](files-bytes-upload.md) |
| Bytes in `goal` or `notes` | Never. [data](../02-understand/data.md) |
| Pattern 0 with no OCR tool | Caller must already send `text` (see [`email_summarize`](../03-catalogue/routes.md#email_summarize)) |

## Status

| Piece | Now |
| --- | --- |
| JSON `doc_id` on jobs | Yes. Dummy payloads already do this. |
| Domain GET from a real DMS | No. Tool-mock ignores the body and returns canned `text`. |
| Presigned `doc_url` on `goal` | Not a seed field. Same Runtime path if the caller puts it on payload. |
| Strip `doc_url` from non-OCR HTTP | No. Whole `goal` is posted. |
