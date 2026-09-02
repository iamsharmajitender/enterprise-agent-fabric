# Catalogue matrix

How to read [routes.md](routes.md) and [use-cases.md](use-cases.md). This is the **active seed** from [`route/shopassist_case/`](../../agent-fabric-scripts/stack/route/shopassist_case/) (`route_version=2026.08.1`, `status=active`). It is not a claim that every catalogue field runs.

**32** `route_id`s. Payload files are [`chats.json`](../../agent-fabric-scratchpad/catalog/chats.json). Run demos at [http://localhost:3014/chat](http://localhost:3014/chat).

## How to read the matrix

Each row is one `route_id`. Columns are facts from seed + dummy payloads, plus an honest **status**.

| Column | Meaning |
| --- | --- |
| `route_id` | Seed / dummy-request id. Anchor in `routes.md`. If seed SQL and `jobs.json` ever disagree, this matrix follows the wrappers you can run. |
| Pattern | `autonomy_mode` 0–3 (single inference, autonomous, deterministic, guided). |
| jobs / chat | Dummy channel. `fee_explain` is both. |
| goal / payload keys | Keys from `jobs.json` (`payload`) or `chats.json` (`message`). `{id}` is replaced per run. |
| tools or workflow | Manifest tool names, and/or `workflow_id` when the route pins one. |
| retrieval | Omitted when there is no `dataplane.retrieval` row. Else `mode` + corpus ids in `scope`. |
| memory | Omitted when there is no `dataplane.memory_profiles` row. Else the four flags (only `working` and `loop` are honored today). |
| status | What Runtime actually does vs what the row names. Vocabulary below. |
| demo | [chat scratchpad](http://localhost:3014/chat) when a row exists in `chats.json`. |

**Status vocabulary** (same words as [`../02-understand/status.md`](../02-understand/status.md)):

- **`runs`** — HTTP and/or LLM stages fire as implemented. HTTP = `goal` ∪ schema-selected **slots**. LLM reads **notes**. Workflow prefetch stages pack `working.slots.prefetch`. Branch, `human_gate`, `kind=agent`, checkpoint resume are wired ([status](../02-understand/status.md)).
- **`catalogue-only`** — Runtime does **not** execute: `conversation`, `long_term`, Pattern 3 inner **allowlist** enforcement.
- **`prefetch mode only`** — route names `deterministic_prefetch` but Pattern 0/1 has no workflow prefetch stage.

`working=session` and `loop=checkpoint` are stored on the run pin when the route asks for them. Failed runs with `loop=checkpoint` resume from the saved cursor via `/turns`. Dummy `completed` is pin/hydrate smoke — use [D13 verification](../tasks/dataflow-plan.md#verification-checklist-d13) for dataflow proof.

## How to run a row

Fabric up, then open [http://localhost:3014/chat](http://localhost:3014/chat). See [stack/README.md](../../agent-fabric-scripts/stack/README.md).

```bash
./agent-fabric-scripts/stack/start-app.sh
./agent-fabric-scripts/stack/add-seed-data.sh
```

Tool-only HTTP paths can finish against agent-fabric-mocks. LLM stages still need Ollama.

## When to regenerate this folder

Rewrite these three files when **seed** or **dummy payloads/scripts** change. No generator in this pass. Walk:

1. Active seed `INSERT`s in [`route/shopassist_case/`](../../agent-fabric-scripts/stack/route/shopassist_case/) (`dataplane.routes`, `dataplane.prompt_packs`, `dataplane.memory_profiles`, ACR capabilities/manifests).
2. Payload keys, channels, and **route_id spelling** from `jobs.json` / `chats.json` (source of demo wrappers).
3. Demo ids from `chats.json` and the [chat scratchpad](http://localhost:3014/chat).
4. Status against Runtime ([status](../02-understand/status.md), [D13 verification](../tasks/dataflow-plan.md#verification-checklist-d13)) — not against dummy `completed` alone.
