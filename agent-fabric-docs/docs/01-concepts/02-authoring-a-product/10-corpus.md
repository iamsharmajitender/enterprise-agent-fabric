---
title: Corpus
sidebar_label: Corpus
description: "A corpus is a registered search gateway. What the row holds, how retrieval.scope references it, and exactly what Runtime does with the chunks."
---

# Corpus

A corpus is a **registered search gateway**, not a document store. The Fabric never holds your content: the row records where to ask, and Runtime POSTs a query there at run time.

Corpora are the other half of [retrieval](/concepts/authoring-a-product/retrieval). The retrieval row on a route says *how* to retrieve; the corpus rows it names say *where from*.

## The row

`dataplane.corpora`, keyed by `corpus_id`.

| Column | Notes |
| --- | --- |
| `corpus_id` | Primary key. This is the string that appears in a route's `retrieval.scope` |
| `display_name` | Label for the Control Plane |
| `url` | The search gateway endpoint Runtime POSTs to |
| `collection` | Collection name sent in the request body. Defaults to `corpus_id` when empty |
| `auth` | Defaults to `workload-oauth` |
| `owner` | Owning team |
| `status` | `draft`, `published`, or `deprecated` |
| `region` | Optional |
| `updated_at` | Set on write |

## How a route references one

`dataplane.retrieval.scope` is a **JSON array of `corpus_id` strings** — not URLs, not collection names.

```sql
INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope)
VALUES ('overdraft_fee_qa', '2026.08.1', 'deterministic_prefetch',
        '["fee-schedule","product-disclosure"]'::jsonb);
```

Publish-time lint checks that every id in `scope` exists and is `published`, so a typo or an unpublished corpus fails before a caller reaches it.

The two retrieval modes treat scope very differently:

| Mode | What Runtime does with `scope` |
| --- | --- |
| `deterministic_prefetch` | **Reads it.** Packs every listed corpus before generate |
| `tool` | **Ignores it.** Scope is catalogue documentation of which corpora a retrieve capability is expected to hit; the actual call goes through a manifest tool over ordinary HTTP |

If you are on `mode=tool`, the corpus rows are governance metadata. The thing that executes is the [capability](/concepts/authoring-a-product/capability).

## What prefetch actually does

For a route with `mode=deterministic_prefetch`, hydrate prepends a synthetic `prefetch` stage with `llm_role: none`. When it runs, for each corpus id in scope:

1. Fetch the corpus row from the catalogue.
2. **Refuse anything not `published`** — the run fails rather than silently retrieving less.
3. POST `{collection, goal}` to the corpus `url`.
4. Tag every returned chunk with its `corpus_id` and accumulate.

Then, once across all corpora: **if no chunks came back at all, the run fails.** Prefetch fails closed. A grounded route that silently answers ungrounded is worse than a route that stops.

### Where the chunks land

| Destination | Contents |
| --- | --- |
| `working.slots.prefetch` | `{"chunks": [...]}` — everything, flattened |
| `working.slots["prefetch:{corpus_id}"]` | Per-corpus hits, for audit and debugging |
| The LLM user message | A `packed chunks:` block, ahead of prior stage outputs |
| An HTTP tool body | `packed_text`, but **only** if that tool's `input_schema` declares the key |

The slots persist on the run pin when the [memory](/concepts/authoring-a-product/memory) profile sets `working=session`.

The model does not search and cannot skip the pack — that is the whole point of "deterministic" in the mode name. Compare [Mode 1](/autonomy/mode-1-autonomous), where the model chooses whether to call a retrieve tool at all.

## The seed example

`overdraft_fee_qa` is the worked case: an [autonomy mode 0](/autonomy/mode-0-single-inference) route with a prompt pack and two corpora.

| `corpus_id` | Gateway |
| --- | --- |
| `fee-schedule` | `http://agent-mocks:3010/corpora/fee-schedule/search` |
| `product-disclosure` | `http://agent-mocks:3010/corpora/product-disclosure/search` |

Both are `published`, both are named in the route's `retrieval.scope`. The mock gateway returns `{"chunks": [{id, text, tags}]}`.

:::note Only one seed loads corpora
`overdraft_fee_qa/corpora.sql` is the sole stack seed that inserts into `dataplane.corpora`. Other corpus ids you may see — `policy-engine`, `accounts` — exist in in-memory stores for unit tests, not in the database. The frozen [`corpus-policy-engine.json`](/fixtures/corpus-policy-engine.json) fixture is one of those: a reference shape, not a seeded row.
:::

## Managing corpora

The [Control Plane](http://localhost:3006/corpora) browses them: a list with status counts, a detail view with a JSON inspector, and a **Uses** panel that lists every route whose `retrieval.scope` names the corpus. That reverse lookup is the one to check before deprecating anything.

It is read-only. Like [routes](/concepts/authoring-a-product/route), corpora are authored as seed SQL — the Data Plane exposes no create, update, or delete endpoint.

## Catalogue-only

| Thing | Reality |
| --- | --- |
| `retrieval.mode=tool` scope | Stored and linted. Never read by Runtime |
| Workflow stage `corpus` field | Editable in the Control Plane workflow UI. Not wired to prefetch execution |
| `long_term=retrieve_only` | A memory policy value with no store behind it |
