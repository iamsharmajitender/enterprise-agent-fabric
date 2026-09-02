import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import { test } from "node:test";
import { createUiServer } from "./ui-server.js";

async function withServer(run: (origin: string) => Promise<void>): Promise<void> {
  const server = createUiServer(async () => new Response('{"status":"UP"}', { status: 200 }));
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address() as AddressInfo;
  try {
    await run(`http://127.0.0.1:${port}`);
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close((err) => (err ? reject(err) : resolve()));
    });
  }
}

test("GET /chat serves the chat scratchpad shell", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/chat`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /id="thread"/);
    assert.match(html, /client\/chat-main\.js/);
    assert.match(html, /id="chat-type"/);
  });
});

test("GET /jobs serves the jobs scratchpad shell", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/jobs`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /id="job-type"/);
    assert.match(html, /id="new-job"/);
    assert.match(html, /client\/jobs-main\.js/);
    assert.doesNotMatch(html, /id="route"/);
  });
});

test("GET /chats.json serves the seed catalog", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/chats.json`);
    assert.equal(res.status, 200);
    const body = (await res.json()) as { chats?: { route_id: string }[] };
    assert.ok((body.chats ?? []).some((row) => row.route_id === "shopassist_case"));
  });
});

test("GET /human serves the human gate scratchpad shell", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/human`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /id="correlation-id"/);
    assert.match(html, /id="packet"/);
    assert.match(html, /client\/human-main\.js/);
  });
});

test("GET /human.json serves the seed catalog", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/human.json`);
    assert.equal(res.status, 200);
    const body = (await res.json()) as { default_packet?: { decision?: string } };
    assert.equal(body.default_packet?.decision, "approve");
  });
});

test("GET /health returns UP", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/health`);
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { status: "UP" });
  });
});
