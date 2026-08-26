# Agent Audit Control Plane (AACP)

Ops UI for fabric evidence. Port **3013**. **No database** — only calls agent-audit-data-plane (`AUDIT_DATA_PLANE_URL`, default `http://localhost:3012`).

Does not call ADP, AR, AFD, or ACR for audit data.

## Demo

1. Open http://localhost:3013 — landing has **Completed** (success + failed) and **In progress** tabs (50 per page).
2. Use **Nested** / **Flat** to switch layout. Nested families start closed; expand a parent to see agent children.
3. Click a **Route** value to open that route in Control Plane (`http://localhost:3006/routes/…`).
4. Use **Search** (or click a row / `correlation_id`) for chain lookup by `correlation_id` / `session_id`.
5. Expect Phase A events (decide → freeze/pin → hydrate → terminal); Phase B adds `stage.*`.

## Run

```bash
npm install && npm test && npm start
```
