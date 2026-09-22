---
title: Your first request
sidebar_label: Your first request
slug: /guides/first-request
description: "Send one job and one chat turn through Front Door, then follow the same correlation_id through Runtime."
---

# Your first request

The stack is up from [Start the fabric](/running-locally). You will send two calls through the **Agent Front Door**. Nothing else is public. Set `FRONT_DOOR` to that ingress URL (stack README).

Local identity is stubbed. Every channel call needs both headers from [stub auth](/reference/stub-auth):

```http
Authorization: Bearer stub
X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}
```

`jane` is entitled to account-read routes, including `fee_explain`.

## 1. Start a job

A job names the route. Front Door still entitles the caller. It skips classification, freezes `fee_explain`, and starts Runtime.

```bash
curl -sS "$FRONT_DOOR/v1/jobs" \
  -H 'Authorization: Bearer stub' \
  -H 'Content-Type: application/json' \
  -H 'X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}' \
  -d '{
    "route_id": "fee_explain",
    "idempotency_key": "job-fee-explain:docs",
    "payload": { "account_id": "acc-42" }
  }'
```

You should get `202` and a `correlation_id`. Front Door does not mint that id — Runtime does.

```json
{ "correlation_id": "corr-…" }
```

Poll until the run completes:

```bash
curl -sS "$FRONT_DOOR/v1/jobs/corr-…" \
  -H 'Authorization: Bearer stub' \
  -H 'X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}'
```

Bodies for this call: [jobs-start.json](/fixtures/jobs-start.json) and [jobs-accepted.json](/fixtures/jobs-accepted.json).

## 2. Send a chat turn

Chat does **not** name a route. Front Door asks the Agent Data Plane to classify the utterance. Only `outcome=route` starts Runtime. `clarify` and `abstain` talk back and never pin.

```bash
curl -sS "$FRONT_DOOR/v1/assistant/turns" \
  -H 'Authorization: Bearer stub' \
  -H 'Content-Type: application/json' \
  -H 'X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}' \
  -d '{ "message": "Why was I charged $42?" }'
```

Accepted turns return a `session_id`. Follow-ups reuse that session and skip classify — the frozen route stays pinned.

```json
{ "session_id": "chat-…", "status": "accepted" }
```

Request body: [assistant-turn-request.json](/fixtures/assistant-turn-request.json).

Or open the local chat scratchpad and type the same sentence.

## What just happened

```
Caller → Front Door → Data Plane (entitle / classify)
                   → freeze route_id@version
                   → Runtime (hydrate + run)
                   → 202 + correlation_id
```

| Step | Who | What you can prove |
| --- | --- | --- |
| Entitle | Front Door + Data Plane | `jane` may use this route |
| Classify | Data Plane, chat only | Why `fee_explain`, not another agent |
| Freeze | Front Door | The version that will run, before the first LLM call |
| Hydrate | Runtime | Every capability `id@version` on the pin |
| Run | Runtime | The graph for that route's autonomy mode |

The same `correlation_id` is the handle for [audit](/concepts/authoring-a-product/audit) and [observability](/concepts/authoring-a-product/observability).

## If something fails

| Symptom | Likely cause |
| --- | --- |
| Connection refused | Stack is not up — [start the fabric](/running-locally) |
| `401` | Missing `Authorization` or `X-Stub-Claims` |
| `403` | Claims do not entitle the route |
| `202` then a failed run | Seed or mocks — reload seed |

## Next

- Author the rows that made `fee_explain` exist: [author an agent](/guides/author-an-agent)
- The same path in more detail: [request lifecycle](/concepts/executing-a-request/request-lifecycle)
