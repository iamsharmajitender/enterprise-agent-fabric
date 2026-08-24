# Use cases

Intended **ingress and document** shapes this fabric will support. Not a dump of seed routes (those live in [03-catalogue](../03-catalogue/)). Not autonomy patterns (those live in [06-patterns](../06-patterns/)).

Add a file here when a new caller shape is real. One concern per file. Each page should say: who holds the bytes, what the request contains, who fetches, what Runtime `goal` looks like, and what is out of scope.

Autonomy mode does not change these pages. Jobs vs chat is ingress, not a new use case.

## Files

| File | Caller has | Fabric sees |
| --- | --- | --- |
| [files-via-dms](files-via-dms.md) | Objects already in the enterprise DMS | JSON ids, or a short-lived presigned GET |
| [files-bytes-upload](files-bytes-upload.md) | Raw bytes on the channel request | Multipart on Front Door; DMS id on `goal` after mint |

Default is DMS-first ([files-via-dms](files-via-dms.md)). Byte upload is opt-in per route.

## Honest now vs later

Today jobs/chat are JSON. Seed document routes already pass `doc_id` (see [`msa_risk_review`](../03-catalogue/routes.md#msa_risk_review)). Tool-mock does **not** GET the DMS; it returns canned `text`. Presigned URLs, `ingress_files`, and Front Door PUT to DMS are **not** built. These pages are the contract to build toward.

Data movement after ingress is still [data](../02-understand/data.md): HTTP is `dict(goal)`; the LLM reads `notes` strings.
