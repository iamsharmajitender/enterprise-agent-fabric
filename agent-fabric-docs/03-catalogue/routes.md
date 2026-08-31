# Catalogue routes

Active route rows match [`route/shopassist_case/`](../../agent-fabric-scripts/catalogue-seed/route/shopassist_case/) and [`chats.json`](../../agent-fabric-scratchpad/catalog/chats.json).

Status vocabulary ([`../02-understand/status.md`](../02-understand/status.md)):

- **`runs`** — stages execute as hydrated. HTTP = `goal` ∪ schema-selected **slots**. LLM reads **notes**. Pattern 1 CALL/ASK/DONE with `loop=checkpoint` resume is wired.
- **`catalogue-only`** — Runtime does **not** execute: `conversation`.

## Pattern 1 — autonomous

| route_id | Pattern | chat | goal / payload keys | tools | retrieval | memory | status | demo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="shopassist_case"></a>`shopassist_case` | 1 | chat | `message` | `lookup_order`, `lookup_order_by_customer`, `lookup_order_by_email`, `investigate_duplicate_charge`, `check_return_policy`, `escalate_to_human` | — | conversation=session, working=session, loop=checkpoint | `runs` (CALL/ASK/DONE; ASK pauses for a locator; lookups get schema-only JSON; billing/policy via domain HTTP; escalate auto-completes + idempotent — [handoff use case](../07-usecases/escalate-to-human-handoff.md)). catalogue-only: conversation | [`shopassist_case_ask`](http://localhost:3014/chat) |
