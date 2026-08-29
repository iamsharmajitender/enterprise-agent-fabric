import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import { test } from "node:test";
import { DataPlaneClient } from "./data-plane-client.js";
import { RegistryClient } from "./registry-client.js";
import { createUiServer } from "./ui-server.js";

async function withServer(run: (origin: string) => Promise<void>): Promise<void> {
  const client = new DataPlaneClient("http://adp.test", async () => new Response("{}"));
  const registry = new RegistryClient("http://acr.test", async () => new Response("{}"));
  const server = createUiServer(client, registry);
  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", resolve);
  });
  const { port } = server.address() as AddressInfo;
  try {
    await run(`http://127.0.0.1:${port}`);
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close((err) => (err ? reject(err) : resolve()));
    });
  }
}

test("GET / serves the Enterprise Agent Fabric landing", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /Agent Fabric/);
    assert.match(html, /<h1>Enterprise Agent Fabric<\/h1>/);
  });
});

test("GET /app.js keeps KPI cards on home and the table on /routes", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/app.js`);
    assert.equal(res.status, 200);
    const js = await res.text();
    assert.match(js, /function buildCatalogRow/);
    assert.match(js, /function showLanding/);
    assert.match(js, /function showRoutes/);
    assert.match(js, /go\("\/routes"/);
    assert.match(js, /go\("\/capabilities"/);
    assert.match(js, /function showCapabilities/);
    assert.match(js, /function showPrompts/);
    assert.match(js, /function showWorkflows/);
    assert.match(js, /function showManifests/);
    assert.match(js, /function showCorpora/);
    assert.match(js, /function showUsage/);
    assert.equal(js.includes("replaceChildren(kpis, wrap)"), false);
  });
});

test("GET /prompts and /manifests serve the SPA shell", async () => {
  await withServer(async (origin) => {
    for (const path of ["/prompts", "/manifests", "/workflows", "/corpora", "/prompts/fee_explain", "/workflows/kyc_onboarding", "/corpora/policy-engine", "/capability/usage"]) {
      const res = await fetch(`${origin}${path}`);
      assert.equal(res.status, 200);
      assert.match(await res.text(), /<h1>Enterprise Agent Fabric<\/h1>/);
    }
  });
});

test("GET /capabilities serves the SPA shell", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/capabilities`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /<h1>Enterprise Agent Fabric<\/h1>/);
  });
});

test("GET /routes serves the SPA shell", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/routes`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /<h1>Enterprise Agent Fabric<\/h1>/);
  });
});

test("GET /catalogue-stats.js is served", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/catalogue-stats.js`);
    assert.equal(res.status, 200);
    const body = await res.text();
    assert.match(body, /export function catalogueStats/);
  });
});

test("GET /catalog-status.js is served", async () => {
  await withServer(async (origin) => {
    const res = await fetch(`${origin}/catalog-status.js`);
    assert.equal(res.status, 200);
    const body = await res.text();
    assert.match(body, /export function countCatalogStatuses/);
  });
});

test("GET /api/eligible and /api/routes/fee_explain proxy Data Plane", async () => {
  const seen: string[] = [];
  const client = new DataPlaneClient("http://adp.test/", async (input) => {
    seen.push(String(input));
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  });
  const registry = new RegistryClient("http://acr.test", async () => new Response("{}"));
  const server = createUiServer(client, registry);
  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", resolve);
  });
  const { port } = server.address() as AddressInfo;
  try {
    const eligible = await fetch(`http://127.0.0.1:${port}/api/eligible?channel=web`);
    assert.equal(eligible.status, 200);
    const catalogue = await fetch(
      `http://127.0.0.1:${port}/api/routes/fee_explain?route_version=2026.08.1`,
    );
    assert.equal(catalogue.status, 200);
    assert.ok(seen.some((href) => href.includes("/v1/intent/eligible")));
    assert.ok(seen.some((href) => href.includes("/v1/catalog/routes/fee_explain")));
    assert.equal(
      seen.some((href) => href.includes("/v1/decisions") || href.includes("/v1/intent/decide")),
      false,
    );
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close((err) => (err ? reject(err) : resolve()));
    });
  }
});

test("GET /capability/usage serves the SPA shell and capability-usage.js", async () => {
  await withServer(async (origin) => {
    const page = await fetch(`${origin}/capability/usage`);
    assert.equal(page.status, 200);
    assert.match(await page.text(), /<h1>Enterprise Agent Fabric<\/h1>/);
    const js = await fetch(`${origin}/capability-usage.js`);
    assert.equal(js.status, 200);
    assert.match(await js.text(), /export function capabilityUsage/);
  });
});
