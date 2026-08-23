# Teaching catalogue matrix

How to read [routes.md](routes.md) and [use-cases.md](use-cases.md). This is the **active Pattern 0–3 teaching set** from [`../run/seed/create-seed-data.sql`](../run/seed/create-seed-data.sql) (`route_version=2026.08.1`, `status=active`). It is not a claim that every catalogue field runs.

**29** `route_id`s. Payload files are [`../run/dummy-jobs/jobs.json`](../run/dummy-jobs/jobs.json) and [`../run/dummy-jobs/chats.json`](../run/dummy-jobs/chats.json). Demo wrappers are the `*.sh` files under [`../run/dummy-jobs/`](../run/dummy-jobs/README.md).

## How to read the matrix

Each row is one `route_id`. Columns are facts from seed + dummy payloads, plus an honest **status**.

| Column | Meaning |
| --- | --- |
| `route_id` | Seed / dummy-job id. Anchor in `routes.md`. If seed SQL and `jobs.json` ever disagree, this matrix follows the wrappers you can run. |
| Pattern | `autonomy_mode` 0–3 (single inference, autonomous, deterministic, guided). |
| jobs / chat | Dummy channel. `fee_explain` is both. |
| goal / payload keys | Keys from `jobs.json` (`payload`) or `chats.json` (`message`). `{id}` is replaced per run. |
| tools or workflow | Manifest tool names, and/or `workflow_id` when the route pins one. |
| retrieval | Omitted when there is no `dataplane.retrieval` row. Else `mode` + corpus ids in `scope`. |
| memory | Omitted when there is no `dataplane.memory_profiles` row. Else the four flags (only `working` and `loop` are honored today). |
| status | What Runtime actually does vs what the row names. Vocabulary below. |
| demo | Wrapper path under `docs/run/dummy-jobs/` when one exists. |

**Status vocabulary** (same words as [`../02-understand/status.md`](../02-understand/status.md)):

- **`runs`** — HTTP and/or LLM stages fire as implemented: the graph is **linear**, HTTP bodies are the original **goal** (plus an LLM `query` on `query_formulation` stages), later LLM stages see prior output as **notes** strings.
- **`catalogue-only`** — the route *names* `branch`, `human_gate`, a prefetch pack, `conversation`, or `long_term`, and Runtime does **not** execute that extra. Dummy `completed` does not prove those extras.
- **`prefetch not packed`** — on every `deterministic_prefetch` route. Prefetch stages with empty `invoke` skip HTTP. Chunks are not packed into working memory or the prompt.

`working=session` and `loop=checkpoint` are stored on the run pin when the route asks for them. Crash resume-from-step is not wired. A green dummy job is pin/hydrate/HTTP-or-LLM smoke, not “slots, branch, and RAG work.”

## How to run a row

Fabric up, then a wrapper from repo root. See [`../run/dummy-jobs/README.md`](../run/dummy-jobs/README.md).

```bash
./docs/run/scripts/start-app.sh
./docs/run/dummy-jobs/run-job.sh --list
./docs/run/dummy-jobs/1-autonomous/fee_explain.sh
./docs/run/dummy-jobs/run-chat.sh --list
./docs/run/dummy-jobs/chat/1-autonomous/fee_explain.sh
```

Tool-only HTTP paths can finish against tool-mock. LLM stages still need Ollama.

## When to regenerate this folder

Rewrite these three files when **seed** or **dummy payloads/scripts** change. No generator in this pass. Walk:

1. Active teaching `INSERT`s in [`../run/seed/create-seed-data.sql`](../run/seed/create-seed-data.sql) (`dataplane.routes`, `dataplane.workflows`, `dataplane.retrieval`, `dataplane.memory_profiles`). Skip lifecycle draft/retired cuts in `create-lifecycle-seed-data.sql` unless you add a tiny footnote.
2. Payload keys, channels, and **route_id spelling** from `jobs.json` / `chats.json` (source of demo wrappers).
3. Demo paths from `docs/run/dummy-jobs/**/*.sh`.
4. Status against Runtime (linear graph, goal-only HTTP, prefetch not packed) — not against dummy `completed`.
