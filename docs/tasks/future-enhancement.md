# Future enhancement: versioned route table

**Status:** Proposal  
**Date:** 2026-08-21

v1 versions each route on its own (`route_id` + `route_version`) and marks one row `active` per route. Classify uses every currently active route. A session pin is `route_id` + `route_version`. There is no `route_tables` snapshot.

This document is the deferred design: freeze the **whole contest board** as one published cut.

## Why consider it later

A route is a complete workflow. Pinning Jane’s “yes” only needs that workflow’s row. Fee explain and payments should not share a release train just to change a prompt or a tool.

Classify is different. The first turn is a contest among eligible routes. Who wins “Why was I charged $42?” depends on **every** contestant’s keywords and claims, not only on `fee_explain`. Independently publishing payments can change the fee winner without the fee route changing.

A route table version is a named reprint of that contest:

| Field | Role |
|---|---|
| `product` | Which assistant / UX domain owns the board |
| `route_table_version` | One id for the whole set (e.g. `2026.08.1`) |
| `active` | Which reprint new chats classify against |

Promote = insert a new cut, flip `active`. Rollback = point `active` at the previous cut. Eval and replay use one number for “who sat the test that day.”

## What v1 does instead

- `dataplane.routes` is keyed by `(route_id, route_version)`.
- At most one `active` version per `route_id`.
- `GET /v1/catalog/routes` lists active rows only.
- `POST /v1/intent/decide` scores the active mix.
- Follow-up pin (when Front Door stores it): `route_id` + `route_version`.

Teams can publish a route without waiting on other routes. The live mix is whatever each route last activated.

## When to revive the table

Revisit if any of these become painful:

- A misroute cannot be replayed because the mix of independently published routes is unknown.
- Payments shipping poisons fee questions and there is no one-flip rollback of the contest.
- Golden-set eval needs a certified label set, not “latest of each.”
- Adding or removing a route should be an atomic catalogue publish.

## Sketch (not in v1)

Keep per-route `route_version`. Add `route_tables` as a **pointer set**, not a copy of workflow internals:

```text
route_tables
  route_table_version  2026.09.1
  product              corporate-assistant
  active               true

route_table_members
  route_table_version  2026.09.1
  route_id             fee_explain
  route_version        2026.08.1
  route_id             agent-payments-v2
  route_version        2026.09.1   -- payments shipped alone; fee stayed
```

New chats classify against the active table’s members. Jane’s pin stays `fee_explain@2026.08.1`. Payments can still version independently; the table only records **which editions share the contest**.

Do not merge fee and payments into one workflow. The table is composition of independently versioned routes.

## Out of scope for this proposal

- Implementing `route_tables` or a publish/activate API.
- Changing capability, manifest, or prompt versioning.
- Session stickiness in Front Door (still a separate follow-up).
