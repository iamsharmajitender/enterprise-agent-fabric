# Prompts

A prompt pack is the text the LLM sees, not the route description. ADP owns `dataplane.prompt_packs` (`host`, status, owner) and `dataplane.prompt_role_templates` (`llm_role`, `task_type`, `text`). The route stores `prompt_id` only. AR GETs the published pack at hydrate. AFD and ACR do not load packs.

`agent-runtime/app/agents/hydrate.py` stamps `llm_role` and `llm_prompt` onto each graph node. The pack JSON field is `by_llm_role`. Unknown roles fail the run.

## `llm_role`

`agent-runtime/app/graph/workflow.py` implements four values.

| `llm_role` | Graph | Example |
| --- | --- | --- |
| `none` | HTTP if `invoke.url` is set; otherwise no-op | `ocr_extract`, `notify_customer`, prefetch placeholders |
| `query_formulation` | LLM writes `payload["query"]` from `dict(goal)`, then HTTP | Retrieve stages on `msa_risk_review` |
| `classify` | LLM only; skip HTTP even if a url exists | `llm_pipeline` extract |
| `synthesis` | LLM only; skip HTTP | Memo stages; Pattern 0 `host` node |

Pattern 0 (no workflow) uses `host` as a single `synthesis` node. Mixed workflows stamp `by_llm_role.{role}.text` onto matching stages. Pure write paths (`account_notify`, `card_freeze`) omit the pack; every stage is `none`.

## Empty invoke skips HTTP

`invoke.url` empty (typical prefetch stage, or a workflow-only node) returns the last note and does not call HTTP. See [retrieve](retrieve.md).

LLM-only roles need the Runtime LLM. `none` stages with a url finish against tool-mock without a model.

Do not grow the pack into a transcript. That is catalogue `conversation`, not this pack. See [memory](memory.md).
