# Capabilities

The registry has **two kinds**. That is the catalog contract. A kind is how Runtime calls after PEP, not a taxonomy of “things an agent can do.”

| `kind` | Invoke | What it is |
| --- | --- | --- |
| `domain` | HTTP to a governed business API (local: agent-fabric-mocks) | OCR, fee lookup, freeze, notify. |
| `agent` | Front Door `POST /v1/jobs` with a **fixed** `route_id` in `invoke.body` | Start another catalogue product. New freeze, new entitle, callee `agent_client_id`. Not a POST to the callee Runtime. |

Same `id` + `version` UX for both. Control Plane lists them together. Manifests only store `{capability_id, capability_version}`; `kind` lives on the capability row (`acr.registry.capabilities.kind`).

Seed `agent` rows: `start_contract_review` → `contract_review`, `start_kyc_onboarding` → `kyc_onboarding`. Parents: `fraud_investigate`, `ops_start_kyc`. Runtime skips that HTTP today; see [status](status.md).

## Do not add a kind for

These already have a home. A new `kind` would split the catalog and confuse hydrate.

| Temptation | Home |
| --- | --- |
| Retrieve / RAG / named corpus | Route `retrieval` + [retrieve](retrieve.md). Not a capability kind. |
| Prompt pack / `llm_role` | [prompts](prompts.md). Not a capability. |
| JSON Schema in/out | [schemas](schemas.md). `output_schema` binds on LLM stages; `input_schema` is catalogue today. |
| Workflow stage, `branch`, `human_gate` | ADP workflow JSON. Linear graph today; see [patterns](patterns.md) and [status](status.md). |
| Memory policy | [memory](memory.md). |
| MCP `list_tools` | Not the catalog. Exam and pin need a frozen `id@version`. |
| “Any agent” / model-chosen `route_id` | An `agent` capability **is** a named product. The invoke body already has `route_id`. The model proposes the capability id, not a free route. |

## When a third kind would earn keep

Only if **invoke is a different gate**: not domain HTTP and not AFD jobs. Example: a human work-item API, or a non-HTTP bus. Until then, two kinds.

Register with `PUT` on ACR (port 3009), not Control Plane. After `add-seed-data.sh`, seed rows reload from `agent-fabric-scripts/catalogue-seed/route/`.
