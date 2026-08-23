# Prompts

A prompt pack is the text the LLM sees, not the route description. ADP owns `dataplane.prompt_packs` (`host`, status, owner) and `dataplane.prompt_role_templates` (`llm_role`, `task_type`, `text`). Every active route stores a `prompt_id`. AR GETs the published pack at hydrate. AFD and ACR do not load packs.

One pack per route. Pattern 0 and Pattern 1 use `host` only (Pattern 1 reuses that same host on every CALL/DONE turn). When a route makes more than one kind of LLM call, the pack holds more than one prompt text: `host` plus a role template for each distinct `llm_role`. Two synthesis stages share one synthesis template. Role templates are unique per `(prompt_id, llm_role)`.

`agent-runtime/app/agents/hydrate.py` stamps `llm_role` and `llm_prompt` onto each graph node. The pack JSON field is `by_llm_role`. Unknown roles fail the run.

## `llm_role`

`agent-runtime/app/graph/workflow.py` implements four values.

| `llm_role` | Graph | Example |
| --- | --- | --- |
| `none` | HTTP if `invoke.url` is set; otherwise no-op | `ocr_extract`, `notify_customer`, prefetch placeholders |
| `query_formulation` | LLM writes `payload["query"]` from `dict(goal)`, then HTTP | Retrieve stages on `msa_risk_review`, `clause_lookup` |
| `classify` | LLM only; skip HTTP even if a url exists | `llm_pipeline` extract |
| `synthesis` | LLM only; skip HTTP | Memo stages; Pattern 0 `host` node; write-path `respond` |

Pattern 0 (no workflow) uses `host` as a single `synthesis` node. Mixed workflows stamp `by_llm_role.{role}.text` onto matching stages. Pattern 1 has no workflow: the Runtime loop uses `host` as the CALL/DONE system prompt. Pattern 2/3 still append a `respond` `synthesis` node at hydrate when there is no classify/synthesis stage yet (HTTP-only tools, or `query_formulation` without a user-facing answer). Seed workflows already name that synthesis stage; hydrate is the safety net if the extra stage has no matching tool.

## Empty invoke skips HTTP

`invoke.url` empty (typical prefetch stage, or a workflow-only node) returns the last note and does not call HTTP. See [retrieve](retrieve.md).

LLM-only roles need the Runtime LLM. `none` stages with a url finish against tool-mock without a model.

Do not grow the pack into a transcript. That is catalogue `conversation`, not this pack. See [memory](memory.md).
