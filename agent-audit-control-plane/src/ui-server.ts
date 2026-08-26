import { createServer, type ServerResponse } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { AuditDataPlaneClient } from "./audit-client.js";

const here = dirname(fileURLToPath(import.meta.url));

export function publicDir(): string {
  return join(here, "..", "public");
}

export function listenPort(): number {
  const raw = process.env.PORT ?? "3013";
  return Number.parseInt(raw, 10);
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const raw = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(raw),
  });
  res.end(raw);
}

function sendFile(res: ServerResponse, path: string, contentType: string): void {
  const body = readFileSync(path);
  res.writeHead(200, { "content-type": contentType });
  res.end(body);
}

export function createUiServer(client: AuditDataPlaneClient) {
  const pub = publicDir();
  return createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", "http://localhost");
    try {
      if (url.pathname === "/health") {
        sendJson(res, 200, { status: "UP" });
        return;
      }
      if (url.pathname === "/api/workflows" && req.method === "GET") {
        const limit = Number.parseInt(url.searchParams.get("limit") ?? "50", 10);
        const offset = Number.parseInt(url.searchParams.get("offset") ?? "0", 10);
        const status = url.searchParams.get("status") ?? "completed";
        try {
          const result = await client.listWorkflows(
            Number.isFinite(limit) ? limit : 50,
            Number.isFinite(offset) ? offset : 0,
            status,
          );
          sendJson(res, result.status >= 400 ? 502 : 200, {
            items: result.items,
            total: result.total,
            limit: result.limit,
            offset: result.offset,
            status: status === "in_progress" || status === "in-progress" ? "in_progress" : "completed",
            upstream: result.status,
            error: result.status >= 400 ? `audit-data-plane HTTP ${result.status}` : undefined,
          });
        } catch (err) {
          sendJson(res, 502, {
            items: [],
            total: 0,
            limit: 50,
            offset: 0,
            status: "completed",
            upstream: 0,
            error: `audit-data-plane unreachable (${String(err)}). Is :3012 up?`,
          });
        }
        return;
      }
      if (url.pathname === "/api/chains" && req.method === "GET") {
        const id = url.searchParams.get("correlation_id") ?? "";
        if (!id) {
          sendJson(res, 400, { error: "correlation_id required" });
          return;
        }
        try {
          const result = await client.getChain(id);
          sendJson(res, 200, {
            events: result.events,
            upstream: result.status,
            error: result.status >= 400 ? `audit-data-plane HTTP ${result.status}` : undefined,
          });
        } catch (err) {
          sendJson(res, 502, {
            events: [],
            upstream: 0,
            error: `audit-data-plane unreachable (${String(err)}). Is :3012 up?`,
          });
        }
        return;
      }
      if (url.pathname === "/api/sessions" && req.method === "GET") {
        const id = url.searchParams.get("session_id") ?? "";
        if (!id) {
          sendJson(res, 400, { error: "session_id required" });
          return;
        }
        try {
          const result = await client.getSession(id);
          sendJson(res, 200, {
            events: result.events,
            upstream: result.status,
            error: result.status >= 400 ? `audit-data-plane HTTP ${result.status}` : undefined,
          });
        } catch (err) {
          sendJson(res, 502, {
            events: [],
            upstream: 0,
            error: `audit-data-plane unreachable (${String(err)}). Is :3012 up?`,
          });
        }
        return;
      }
      if (url.pathname === "/" || url.pathname === "/index.html") {
        sendFile(res, join(pub, "index.html"), "text/html; charset=utf-8");
        return;
      }
      if (url.pathname === "/search" || url.pathname === "/search.html") {
        sendFile(res, join(pub, "search.html"), "text/html; charset=utf-8");
        return;
      }
      if (url.pathname === "/app.js") {
        sendFile(res, join(pub, "app.js"), "application/javascript; charset=utf-8");
        return;
      }
      if (url.pathname === "/landing.js") {
        sendFile(res, join(pub, "landing.js"), "application/javascript; charset=utf-8");
        return;
      }
      if (url.pathname === "/styles.css") {
        sendFile(res, join(pub, "styles.css"), "text/css; charset=utf-8");
        return;
      }
      sendJson(res, 404, { error: "not found" });
    } catch (err) {
      sendJson(res, 502, { error: String(err) });
    }
  });
}
