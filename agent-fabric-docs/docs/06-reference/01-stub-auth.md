---
title: Stub identity (v1)
sidebar_label: Stub auth
---

# Stub identity (v1)

No real IdP. Every service enforces these headers. Reject anything else with 401.

## Channel (humans → Front Door)

| Header | Value |
| --- | --- |
| `Authorization` | `Bearer stub` |
| `X-Stub-Claims` | JSON object of claims |

v1 stub user `jane`:

```http
Authorization: Bearer stub
X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}
```

Front Door maps `accounts:read` onto eligible chat-visible routes. Missing or invalid bearer: 401. Do not decide. Do not start AR.

## Workload (service → service)

| Header | Value |
| --- | --- |
| `Authorization` | `Bearer fabric-internal` |
| `X-Workload` | one of `afd` \| `adp` \| `acp` \| `ar` \| `acr` |

Caller identity is `X-Workload`, not the channel user. Channel bearer on a service API is 401.

| Caller | `X-Workload` | May call |
| --- | --- | --- |
| Front Door | `afd` | Data Plane decide, eligible, catalogue GET. AR start / resume / status / open-run |
| Data Plane | `adp` | (none outbound in v1) |
| Control Plane | `acp` | Data Plane eligible GET, catalogue GET. Registry capability GET (list, detail, versions). **Not** decide |
| Agent Runtime | `ar` | Data Plane catalogue GET (pinned version only). Registry capability/manifest GET |
| Registry | `acr` | (none outbound in v1) |

AR on decide → 403. Channel caller on Data Plane / AR / Registry → 401.

## Not in v1

Real JWT validation, mTLS, Kafka, decision audit.
