---
title: LLM
sidebar_label: LLM
description: "How Agent Runtime calls the model: one global backend, four llm_role values, structured output binding, and the retry envelope around every call."
---

# LLM

Every route calls the model at least once. This page is what happens on that call: which backend, what the model receives, what comes back, and what an author can actually change.

**The short version: not much.** The model, temperature, and timeout are global to the Runtime process. What you author is *when* the model is called and *what it sees* — the stage list, the `llm_role` on each stage, the [prompt pack](/concepts/authoring-a-product/prompts), and the capability [output schema](/concepts/authoring-a-product/schema) bound to the response.

## The backend

Runtime wraps one LLM port in two decorators: `TelemetryLlm(RetryLlm(backend))`. Telemetry emits `run.llm.*` events ([observability](/concepts/authoring-a-product/observability)), retry handles transient failures, and the backend is either a seeded stub or a real provider through LangChain's `init_chat_model`.

| Variable | Default | Effect |
| --- | --- | --- |
| `FABRIC_LLM_STUB` | off | Truthy swaps the provider for `SeedStubLlm`. Used by tests and offline demos |
| `OLLAMA_MODEL` | unset | Model string. Wins over `FABRIC_LLM_MODEL` |
| `FABRIC_LLM_MODEL` | `ollama:qwen3:14b` in code, `google_genai:gemini-3.5-flash-lite` in Compose | Model string |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` in Compose | Only used when the model string starts with `ollama:` |
| `FABRIC_LLM_RETRY_MAX` | `3` | Attempts per call |
| `FABRIC_LLM_RETRY_BASE_S` | `1.0` | Backoff base, jittered |
| `FABRIC_LLM_RETRY_MAX_BACKOFF_S` | `30.0` | Backoff cap |

**Temperature (`0.1`), max tokens (`4096`), and timeout (`300s`) are hardcoded.** There is no environment override and no per-route override.

### There is no per-route model

`model_profile` is a required route column with a foreign key, and Front Door passes it on the start contract. **Runtime never reads it.** It is catalogue metadata today.

The only per-route steering that exists is deployment-level: `activation_target` picks which Runtime fleet serves the route (`agent-runtime-shared` or `agent-runtime-custom`), and each fleet is configured with its own environment. That is a fleet choice, not a model choice.

## The four `llm_role` values

`llm_role` sits on a workflow stage and decides how that stage executes. Hydrate stamps it, along with the resolved prompt text, onto each graph node.

| `llm_role` | Calls the LLM | What the stage does |
| --- | --- | --- |
| `none` | No | HTTP tool when `invoke.url` is set; otherwise prefetch passthrough or a `kind=agent` child start |
| `classify` | Yes | LLM only. Result lands on notes and in `slots[stage_id]` |
| `synthesis` | Yes | LLM only. Same handling as classify |
| `query_formulation` | Yes | LLM sets `payload["query"]`, then the stage calls HTTP if a URL is present |

An unknown role fails the run rather than defaulting. Pattern 1 forces `llm_role = "none"` on tool execution, because the loop itself already made the model call.

## What the model receives

**System** is the `llm_prompt` that hydrate stamped on the node, which comes from the prompt pack. If it resolves to empty, the provider substitutes `Follow the user request. Reply with the result only.`

Prompt resolution differs by path, and the difference matters:

| Path | Resolution |
| --- | --- |
| Workflow-only, and branched paths | The role template, falling back to `host` |
| Manifest plus a linear workflow | The role template **only**. No `host` fallback |
| Pattern 1 | `host`, wrapped in the agent prompt with the tool list |
| Appended synthesis node | The synthesis template, then `host`, then a built-in default |

**User** is the same blob everywhere, built from run state:

```
goal: {the immutable goal dict}
packed chunks:            # only when a prefetch pack is present
- ...
prior stage outputs:      # compressed notes
- ...
```

That is the whole context. There is no transcript — see [memory](/concepts/authoring-a-product/memory) for why `conversation=session` does not add one.

## Structured output

When a stage has an `llm_role` of `classify`, `synthesis`, or `query_formulation` **and** its capability carries a bindable `output_schema`, Runtime converts that JSON Schema into a Pydantic model and calls `with_structured_output`. The response is validated against it.

Bindable means a **flat object**. Nested objects are rejected, and an empty `{type: object}` is not bindable.

Two things happen after validation:

- **Text envelopes unwrap.** If the schema's properties are a subset of `{text, message}`, the string value is returned rather than JSON, so a memo stays prose.
- **Everything else becomes compact JSON**, stored on notes and in the stage slot.

A validation failure is **not retried** — it raises, the call emits `run.llm.failed`, and the stage emits `run.stage.failed`. This is deliberate: a schema violation is a bug in the prompt or the schema, and retrying the same prompt will not fix it.

## Mode 1: the decision loop

The [autonomous mode](/autonomy/mode-1-autonomous) loop asks the model for a **structured decision**, not free text. The bound schema is `AgentDecision`:

| Field | Values |
| --- | --- |
| `action` | `tool_call`, `ask`, or `done` |
| `tool_name` | Capability to invoke, when `action=tool_call` |
| `arguments` | Arguments for that capability |
| `message` | Text for `ask` or `done` |

The system prompt is the pack `host` plus enterprise rules, the hydrated tool list, and each tool's input schema.

`max_loop_steps` from the route bounds the loop, defaulting to `8`. Exceeding it raises rather than returning a partial answer. A tool error inside the loop does **not** end the run: it is caught, appended to notes, and the model gets another turn.

:::note
Older pages describe a text `CALL` / `ASK` / `DONE` protocol. That parser still exists and the seeded stub still speaks it, but the live provider path uses the structured `AgentDecision` above.
:::

## Failure behaviour

| Failure | What happens |
| --- | --- |
| Timeout, connection error, network error | Retried up to `FABRIC_LLM_RETRY_MAX` with jittered backoff |
| Schema validation, unknown tool, loop budget exceeded | **Not retried.** Raises immediately |
| Any LLM failure | `run.llm.failed` with a `reason_class`, then `run.stage.failed` |
| Tool failure inside the Mode 1 loop | Caught, noted, loop continues |

Every call is wrapped in an `llm.complete` span.
