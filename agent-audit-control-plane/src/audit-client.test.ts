import assert from "node:assert/strict";
import test from "node:test";
import { AuditDataPlaneClient } from "./audit-client.js";

test("getChain returns events from upstream JSON", async () => {
  const client = new AuditDataPlaneClient("http://audit.test", async () => {
    return new Response(
      JSON.stringify([
        {
          event_id: "11111111-1111-4111-8111-111111111111",
          event_type: "run.terminal",
          occurred_at: "2026-08-26T01:00:00Z",
          producer: "ar",
          correlation_id: "corr-1",
          session_id: null,
          decision_id: null,
          payload: { status: "completed" },
        },
      ]),
      { status: 200 },
    );
  });
  const result = await client.getChain("corr-1");
  assert.equal(result.status, 200);
  assert.equal(result.events.length, 1);
  assert.equal(result.events[0]?.event_type, "run.terminal");
});

test("listWorkflows returns paginated completed runs", async () => {
  const client = new AuditDataPlaneClient("http://audit.test", async (input) => {
    const url = new URL(String(input));
    assert.equal(url.pathname, "/v1/audit/workflows");
    assert.equal(url.searchParams.get("limit"), "50");
    assert.equal(url.searchParams.get("offset"), "0");
    return new Response(
      JSON.stringify({
        items: [
          {
            correlation_id: "corr-1",
            session_id: "sess-1",
            decision_id: null,
            route_id: "email_summarize",
            route_version: "2026.08.1",
            status: "completed",
            started_at: "2026-08-26T01:51:12Z",
            completed_at: "2026-08-26T01:51:24Z",
          },
        ],
        total: 1,
        limit: 50,
        offset: 0,
      }),
      { status: 200 },
    );
  });
  const result = await client.listWorkflows(50, 0);
  assert.equal(result.status, 200);
  assert.equal(result.total, 1);
  assert.equal(result.items[0]?.route_id, "email_summarize");
});
