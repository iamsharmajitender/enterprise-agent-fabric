# Catalogue matrix

How to read [routes.md](routes.md) and [use-cases.md](use-cases.md). This is the **active Pattern 0–3 seed** from [`../run/scripts/create-seed-data.sql`](../run/scripts/create-seed-data.sql) (`route_version=2026.08.1`, `status=active`). It is not a claim that every catalogue field runs.

**32** `route_id`s. Payload files are [`../run/dummy-request/job/jobs.json`](../run/dummy-request/job/jobs.json) and [`../run/dummy-request/chat/chats.json`](../run/dummy-request/chat/chats.json). Demo wrappers are the `*.sh` files under [`../run/dummy-request/`](../run/dummy-request/README.md).

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
| demo | Wrapper path under `docs/run/dummy-request/` when one exists. |

**Status vocabulary** (same words as [`../02-understand/status.md`](../02-understand/status.md)):

- **`runs`** — HTTP and/or LLM stages fire as implemented. HTTP = `goal` ∪ schema-selected **slots**. LLM reads **notes**. Workflow prefetch stages pack `working.slots.prefetch`. Branch, `human_gate`, `kind=agent`, checkpoint resume are wired ([status](../02-understand/status.md)).
- **`catalogue-only`** — Runtime does **not** execute: `conversation`, `long_term`, Pattern 3 inner **allowlist** enforcement.
- **`prefetch mode only`** — route names `deterministic_prefetch` but Pattern 0/1 has no workflow prefetch stage.

`working=session` and `loop=checkpoint` are stored on the run pin when the route asks for them. Failed runs with `loop=checkpoint` resume from the saved cursor via `/turns`. Dummy `completed` is pin/hydrate smoke — use [D13 verification](../tasks/dataflow-plan.md#verification-checklist-d13) for dataflow proof.

## How to run a row

Fabric up, then a wrapper from repo root. See [`../run/dummy-request/README.md`](../run/dummy-request/README.md).

```bash
./docs/run/scripts/start-app.sh
./docs/run/dummy-request/run-job.sh --list
./docs/run/dummy-request/job/1-autonomous/fee_explain.sh
./docs/run/dummy-request/run-chat.sh --list
./docs/run/dummy-request/chat/1-autonomous/fee_explain.sh
```

Tool-only HTTP paths can finish against agent-fabric-mocks. LLM stages still need Ollama.

## When to regenerate this folder

Rewrite these three files when **seed** or **dummy payloads/scripts** change. No generator in this pass. Walk:

1. Active seed `INSERT`s in [`../run/scripts/create-seed-data.sql`](../run/scripts/create-seed-data.sql) (`dataplane.routes`, `dataplane.workflows`, `dataplane.prompt_packs`, `dataplane.prompt_role_templates`, `dataplane.retrieval`, `dataplane.memory_profiles`). Skip lifecycle draft/retired cuts in the same file unless you add a tiny footnote.
2. Payload keys, channels, and **route_id spelling** from `jobs.json` / `chats.json` (source of demo wrappers).
3. Demo paths from `docs/run/dummy-request/**/*.sh`.
4. Status against Runtime ([status](../02-understand/status.md), [D13 verification](../tasks/dataflow-plan.md#verification-checklist-d13)) — not against dummy `completed` alone.
