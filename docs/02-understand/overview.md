# Overview

Five processes. Channels talk only to Front Door.

| Port | Process | Job |
| --- | --- | --- |
| 3005 | Agent Front Door (AFD) | Only public ingress. Entitle, freeze, start Runtime. Chat and jobs share this process. |
| 3006 | Agent Control Plane (ACP) | Catalogue UI. No database. Not a Fabric box. |
| 3007 | Agent Data Plane (ADP) | Catalogue and classify. `POST /v1/intent/decide`. Does not start Runtime. |
| 3008 | Agent Runtime (AR) | Pin the freeze, hydrate, run a linear LangGraph. |
| 3009 | Agent Capability Registry (ACR) | Published capabilities and manifests. Hydrate once at pin. |

Catalogue matrix: [03-catalogue](../03-catalogue/). Box packs: [04-architecture](../04-architecture/). Contracts: [05-reference](../05-reference/).

## Pin, then hydrate, then linear LangGraph

1. **Pin.** AFD gets a startable decide outcome (`route`), GETs that catalogue version, `POST /v1/runs` on AR, then writes a freeze (`frontdoor.freeze`). AR copies `route_id` + `route_version` onto a durable run pin. It does not re-read `active`. Hydrate failure is `422`; AR returns `202 { "correlation_id" }`. AFD does not mint that id.
2. **Hydrate.** `agent-runtime/app/agents/hydrate.py` resolves the pinned row from ADP, then the pinned manifest and each capability from ACR (or a workflow / prompt pack when there is no manifest). It stamps `llm_role` and `llm_prompt` onto each node. `invoke` freezes on the pin. Mid-loop registry GET does not happen.
3. **Linear LangGraph.** `agent-runtime/app/graph/workflow.py` builds one node per hydrated record, in order. `GraphState` is `result`, `goal`, `notes`. The graph has no branches. `branch` and `human_gate` are stored on ADP and shown in Control Plane; AR does not walk them.

## Jobs vs chat

| | Jobs `POST /v1/jobs` | Chat `POST /v1/assistant/turns` |
| --- | --- | --- |
| Route | Caller names `route_id` | ADP keyword-classifies. Only `outcome=route` starts |
| Classify | Skipped. Decide still entitles (`ingress: "jobs"`) | Layer ② keywords. `clarify` / `abstain` never pin |
| Freeze key | `job:{idempotency_key}` | `session_id` |
| Body | Job `payload` becomes immutable `goal` | Utterance becomes `goal` |
| Follow-up | Duplicate key returns the original `correlation_id` | Freeze reuses the pin (skip classify) |

Both return `202 { "correlation_id" }`. AFD never mints that id.

What Runtime passes between stages: [data](data.md). Capability kinds (`domain` vs `agent`): [capabilities](capabilities.md). Catalogue vs Runtime: [status](status.md).
