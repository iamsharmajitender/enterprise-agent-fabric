import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { DataPlaneClient } from "./data-plane-client.js";
import { RegistryClient } from "./registry-client.js";

const here = dirname(fileURLToPath(import.meta.url));

export function publicDir(): string {
  return join(here, "..", "public");
}

export function listenPort(): number {
  const raw = process.env.PORT ?? "3006";
  return Number.parseInt(raw, 10);
}

export function createUiServer(client: DataPlaneClient, registry: RegistryClient) {
  return createServer((req, res) => {
    void handle(req, res, client, registry);
  });
}

async function handle(
  req: IncomingMessage,
  res: ServerResponse,
  client: DataPlaneClient,
  registry: RegistryClient,
): Promise<void> {
  const url = new URL(req.url ?? "/", "http://control-plane.local");
  try {
    if (req.method === "GET" && url.pathname === "/api/eligible") {
      const jane = JSON.stringify({ sub: "jane", emts: { "accounts:read": true } });
      return proxy(res, await client.getEligible(url.searchParams.get("channel") ?? "web", jane));
    }
    if (req.method === "GET" && url.pathname === "/api/routes") {
      const upstream = await client.listRoutes(url.searchParams.get("include") ?? undefined);
      return proxy(res, upstream);
    }
    const versionsMatch = url.pathname.match(/^\/api\/routes\/([^/]+)\/versions$/);
    if (req.method === "GET" && versionsMatch) {
      const routeId = decodeURIComponent(versionsMatch[1] ?? "");
      return proxy(res, await client.listRouteVersions(routeId));
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/routes/")) {
      const routeId = decodeURIComponent(url.pathname.slice("/api/routes/".length));
      const upstream = await client.getCatalogueRoute(
        routeId,
        url.searchParams.get("route_version") ?? undefined,
      );
      return proxy(res, upstream);
    }
    if (req.method === "GET" && url.pathname === "/api/capabilities") {
      const upstream = await registry.listCapabilities(
        url.searchParams.get("q") ?? undefined,
        url.searchParams.get("include") ?? undefined,
      );
      return proxy(res, upstream);
    }
    const capVersionsMatch = url.pathname.match(/^\/api\/capabilities\/([^/]+)\/versions$/);
    if (req.method === "GET" && capVersionsMatch) {
      const capabilityId = decodeURIComponent(capVersionsMatch[1] ?? "");
      return proxy(res, await registry.listCapabilityVersions(capabilityId));
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/capabilities/")) {
      const capabilityId = decodeURIComponent(url.pathname.slice("/api/capabilities/".length));
      return proxy(
        res,
        await registry.getCapability(capabilityId, url.searchParams.get("version") ?? undefined),
      );
    }
    if (req.method === "GET" && url.pathname === "/api/prompts") {
      return proxy(res, await client.listPrompts(url.searchParams.get("include") ?? undefined));
    }
    const promptVersionsMatch = url.pathname.match(/^\/api\/prompts\/([^/]+)\/versions$/);
    if (req.method === "GET" && promptVersionsMatch) {
      const promptId = decodeURIComponent(promptVersionsMatch[1] ?? "");
      return proxy(res, await client.listPromptVersions(promptId));
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/prompts/")) {
      const promptId = decodeURIComponent(url.pathname.slice("/api/prompts/".length));
      return proxy(res, await client.getPrompt(promptId, url.searchParams.get("version") ?? undefined));
    }
    if (req.method === "GET" && url.pathname === "/api/workflows") {
      return proxy(res, await client.listWorkflows(url.searchParams.get("include") ?? undefined));
    }
    const workflowVersionsMatch = url.pathname.match(/^\/api\/workflows\/([^/]+)\/versions$/);
    if (req.method === "GET" && workflowVersionsMatch) {
      const workflowId = decodeURIComponent(workflowVersionsMatch[1] ?? "");
      return proxy(res, await client.listWorkflowVersions(workflowId));
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/workflows/")) {
      const workflowId = decodeURIComponent(url.pathname.slice("/api/workflows/".length));
      return proxy(
        res,
        await client.getWorkflow(workflowId, url.searchParams.get("version") ?? undefined),
      );
    }
    if (req.method === "GET" && url.pathname === "/api/manifests") {
      return proxy(res, await client.listManifests(url.searchParams.get("include") ?? undefined));
    }
    const manifestVersionsMatch = url.pathname.match(/^\/api\/manifests\/([^/]+)\/versions$/);
    if (req.method === "GET" && manifestVersionsMatch) {
      const manifestId = decodeURIComponent(manifestVersionsMatch[1] ?? "");
      return proxy(res, await client.listManifestVersions(manifestId));
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/manifests/")) {
      const manifestId = decodeURIComponent(url.pathname.slice("/api/manifests/".length));
      return proxy(
        res,
        await client.getManifest(manifestId, url.searchParams.get("version") ?? undefined),
      );
    }
    if (req.method === "GET" && url.pathname === "/api/corpora") {
      return proxy(res, await client.listCorpora(url.searchParams.get("include") ?? undefined));
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/corpora/")) {
      const corpusId = decodeURIComponent(url.pathname.slice("/api/corpora/".length));
      return proxy(res, await client.getCorpus(corpusId));
    }
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (req.method === "GET" && (url.pathname === "/routes" || url.pathname.startsWith("/routes/"))) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (
      req.method === "GET" &&
      (url.pathname === "/capabilities" || url.pathname.startsWith("/capabilities/"))
    ) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (
      req.method === "GET" &&
      (url.pathname === "/prompts" || url.pathname.startsWith("/prompts/"))
    ) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (
      req.method === "GET" &&
      (url.pathname === "/workflows" || url.pathname.startsWith("/workflows/"))
    ) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (
      req.method === "GET" &&
      (url.pathname === "/manifests" || url.pathname.startsWith("/manifests/"))
    ) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (
      req.method === "GET" &&
      (url.pathname === "/corpora" || url.pathname.startsWith("/corpora/"))
    ) {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/styles.css") {
      return file(res, "styles.css", "text/css; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/app.js") {
      return file(res, "app.js", "text/javascript; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/catalogue-stats.js") {
      return compiled(res, "catalogue-stats.js", "text/javascript; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/catalog-status.js") {
      return compiled(res, "catalog-status.js", "text/javascript; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/capability-usage.js") {
      return compiled(res, "capability-usage.js", "text/javascript; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/capability/usage") {
      return file(res, "index.html", "text/html; charset=utf-8");
    }
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: { code: "NOT_FOUND", message: "not found" } }));
  } catch (err) {
    res.writeHead(502, { "content-type": "application/json" });
    res.end(
      JSON.stringify({
        error: { code: "UPSTREAM", message: err instanceof Error ? err.message : "upstream" },
      }),
    );
  }
}

async function proxy(res: ServerResponse, upstream: Response): Promise<void> {
  const body = await upstream.text();
  res.writeHead(upstream.status, { "content-type": "application/json" });
  res.end(body);
}

function send(res: ServerResponse, body: Buffer | string, type: string): void {
  res.writeHead(200, {
    "content-type": type,
    "cache-control": "no-store",
  });
  res.end(body);
}

function file(res: ServerResponse, name: string, type: string): void {
  send(res, readFileSync(join(publicDir(), name)), type);
}

function compiled(res: ServerResponse, name: string, type: string): void {
  send(res, readFileSync(join(here, name)), type);
}
