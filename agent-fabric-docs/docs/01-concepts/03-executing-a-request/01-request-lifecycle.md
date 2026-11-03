---
title: Request lifecycle
sidebar_label: Request lifecycle
description: "How a request moves: verify, route, pin, execute, record. Chat and jobs are the same idea. Only how the path is chosen differs."
---

# Request lifecycle

A request has one job: leave a governed, provable outcome. The boxes are names for the steps.

The story: [how it hangs together](/how-it-hangs-together#how-a-request-moves). The walk-through: [your first request](/guides/first-request).

## The sequence

1. **Ask.** A person or a system arrives at the [Front Door](/architecture/service-packs/agent-front-door). Channels talk only to this box.
2. **Verify.** Front Door authenticates the caller. The Data Plane entitles them against the route. Missing identity is a refusal. Work does not start.
3. **Route.** Chat is classified. Jobs name the route. Both still have to be entitled. Outcomes: `route`, `clarify`, or `abstain`. Only `route` continues.
4. **Pin.** Front Door freezes the route version and the agent identity, then starts Runtime. From this moment the run is immune to catalogue changes.
5. **Execute.** Runtime hydrates the pinned capabilities once, then runs the [autonomy mode](/autonomy/) the route declared.
6. **Record.** Audit and observability share one `correlation_id`. Evidence is not optional.

<div className="gain-diagram-wrap">

![Request swimlane: caller asks; Fabric verifies and routes; domain AI executes; audit records evidence; outcome returned.](/diagrams/agent-fabric-executive-swimlane-jobs.svg)

</div>

## Who does which job

| Process | Job | Does not |
| --- | --- | --- |
| **Front Door** | Only public ingress. Entitle, freeze, start Runtime. | Classify. Run the agent. |
| **Data Plane** | Catalogue and classify. | Pin. Start Runtime. |
| **Control Plane** | Catalogue UI. | Own a database. Decide. |
| **Runtime** | Pin the freeze, hydrate, run the graph. | Re-read `active`. Classify. |
| **Capability Plane** | Published capabilities and manifests. | Execute. |

## Chat versus jobs

Same contract. Different how the path is chosen.

| | Jobs | Chat |
| --- | --- | --- |
| How the path is chosen | Caller names `route_id` | Data Plane classifies the utterance |
| Classify | Skipped | Required. Only `route` starts work |
| Entitle | Always | Always |
| Freeze key | Idempotency key | Session |
| What becomes the goal | Job payload | Utterance |
| Follow-up | Duplicate key returns the original correlation | Freeze reuses the pin |

A job never skips entitlement. A chat `clarify` or `abstain` never pins. Both return an accepted correlation id. Front Door does not mint that id — Runtime does.

## Pin, then hydrate, then run

These three words are the technical expression of "lock the version, then do the work."

1. **Pin.** Front Door receives a startable decide outcome, reads that catalogue version, starts Runtime, and writes a freeze. Runtime copies `route_id` and `route_version` onto a durable run pin. It does not re-read `active`. Hydrate failure is a client error. Start acknowledgement is async.
2. **Hydrate.** Runtime resolves the pinned route, then the pinned manifest and each capability (or a workflow / prompt pack when there is no manifest). The model sees that snapshot. Mid-loop registry reads do not happen.
3. **Run.** Modes 0, 2, and 3 walk a linear (or designer-owned branch) graph. Mode 1 is a model `CALL` / `DONE` loop inside a budget. A `human_gate` pauses until a person resumes.

What Runtime passes between stages: [run data](/concepts/executing-a-request/run-data). Who the three principals are: [identities](/concepts/executing-a-request/identities). User claims versus agent scopes: [claims and scopes](/concepts/executing-a-request/claims-and-scopes). Who mints which id: [identifiers](/concepts/executing-a-request/identifiers).
