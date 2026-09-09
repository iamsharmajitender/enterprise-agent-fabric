---
title: Prompts
sidebar_label: Prompts
description: "Prompt packs and llm_role: the text the LLM actually sees, who owns it, and how hydrate stamps one llm_prompt per graph node."
---

# Prompts

A prompt pack is the text the LLM sees, not the route description. ADP owns `dataplane.prompt_packs` (`host`, status, owner) and `dataplane.prompt_role_templates` (`llm_role`, `task_type`, `text`). Every active route stores a `prompt_id`. AR GETs the published pack at hydrate. AFD and ACR do not load packs.

One pack per route. Pattern 0 and Pattern 1 use `host` only (Pattern 1 reuses that same host on every CALL/DONE turn). When a route makes more than one kind of LLM call, the pack holds a role template for each distinct `llm_role`. Two synthesis stages share one synthesis template. Role templates are unique per `(prompt_id, llm_role)`. `host` is a fallback when a stage’s role has no `text`, not a prefix: hydrate stamps **one** `llm_prompt` per node, and `llm.complete` uses that string as system. `task_type` is not sent.

`agent-runtime/app/agents/hydrate.py` stamps `llm_role` and `llm_prompt` onto each graph node. The pack JSON field is `by_llm_role`. Unknown roles fail the run. Seeded packs with more than one role: `llm_pipeline` (`classify` + `synthesis`); `clause_lookup`, `template_retrieve`, `msa_risk_review`, `claims_adjudicate` (`query_formulation` + `synthesis`); `purchase_refund` (`classify` + `synthesis`). Any LLM stage (`classify`, `synthesis`, `query_formulation`) with a bindable capability `output_schema` binds that schema on `llm.complete` via `with_structured_output` and validates. See [schemas](/concepts/authoring-a-product/schema) for `required` + `null`, `enum`, arrays, and the `extract_fields` seed. `{text}` / `{message}` envelopes unwrap to the string after validation so memos stay prose; richer objects stay compact JSON on notes. Empty `{type: object}` is not bindable. HTTP `none` stages do not use this path. Route `output_schema_id` is still a pointer only.

## `llm_role`

`agent-runtime/app/graph/workflow.py` implements four values.

| `llm_role` | Graph | Example |
| --- | --- | --- |
| `none` | HTTP if `invoke.url` is set; otherwise no-op | `ocr_extract`, `notify_customer`, prefetch placeholders |
| `query_formulation` | LLM writes `payload["query"]` from `dict(goal)`, then HTTP. Bindable `output_schema` is validated; `{text}` unwraps to the query string | Retrieve stages on `msa_risk_review`, `clause_lookup` |
| `classify` | LLM only; skip HTTP even if a url exists. Bindable `output_schema` is validated | `purchase_refund` extract_fields |
| `synthesis` | LLM only; skip HTTP. Bindable `output_schema` is validated; `{text}` unwraps to prose | Memo stages; Pattern 0 `host` node; write-path `respond` |

Pattern 0 (no workflow) uses `host` as a single `synthesis` node. Mixed workflows stamp `by_llm_role.{role}.text` onto matching stages. Pattern 1 has no workflow: the Runtime loop uses `host` as the CALL/DONE system prompt. Pattern 2/3 still append a `respond` `synthesis` node at hydrate when there is no classify/synthesis stage yet (HTTP-only tools, or `query_formulation` without a user-facing answer). Seed workflows already name that synthesis stage; hydrate is the safety net if the extra stage has no matching tool.

## Empty invoke skips HTTP

`invoke.url` empty (typical prefetch stage, or a workflow-only node) returns the last note and does not call HTTP. See [retrieve](/concepts/authoring-a-product/retrieval).

LLM-only roles need the Runtime LLM. `none` stages with a url finish against agent-fabric-mocks without a model.

Do not grow the pack into a transcript. That is catalogue `conversation`, not this pack. See [memory](/concepts/authoring-a-product/memory).
