import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

export function listenPort(): number {
  return Number.parseInt(process.env.PORT ?? "3014", 10);
}

export function afdBaseUrl(): string {
  return (process.env.AFD_URL ?? "http://localhost:3005").replace(/\/$/, "");
}

export function publicDir(): string {
  return join(here, "..", "..", "public");
}

export function catalogDir(): string {
  return join(here, "..", "..", "catalog");
}

export function createUiServer(fetchImpl: typeof fetch = fetch) {
  return createServer((req, res) => {
    void handle(req, res, fetchImpl);
  });
}

async function handle(
  req: IncomingMessage,
  res: ServerResponse,
  fetchImpl: typeof fetch,
): Promise<void> {
  const url = new URL(req.url ?? "/", "http://scratchpad.local");
  const path = url.pathname;

  if (req.method === "GET" && path === "/health") {
    return json(res, 200, { status: "UP" });
  }

  if (req.method === "GET" && path === "/chats.json") {
    return file(res, join(catalogDir(), "chats.json"), "application/json; charset=utf-8");
  }
  if (req.method === "GET" && path === "/jobs.json") {
    return file(res, join(catalogDir(), "jobs.json"), "application/json; charset=utf-8");
  }
  if (req.method === "GET" && path === "/human.json") {
    return file(res, join(catalogDir(), "human.json"), "application/json; charset=utf-8");
  }

  if (path.startsWith("/v1/")) {
    return proxy(req, res, fetchImpl, path + url.search);
  }

  if (req.method === "GET" && (path === "/" || path === "/chat" || path === "/chat.html")) {
    return file(res, join(publicDir(), "chat.html"), "text/html; charset=utf-8");
  }
  if (req.method === "GET" && (path === "/jobs" || path === "/jobs.html")) {
    return file(res, join(publicDir(), "jobs.html"), "text/html; charset=utf-8");
  }
  if (req.method === "GET" && (path === "/human" || path === "/human.html")) {
    return file(res, join(publicDir(), "human.html"), "text/html; charset=utf-8");
  }
  if (req.method === "GET" && path === "/styles.css") {
    return file(res, join(publicDir(), "styles.css"), "text/css; charset=utf-8");
  }

  if (req.method === "GET" && path.startsWith("/client/")) {
    const name = path.slice("/client/".length);
    if (!name || name.includes("..")) {
      return json(res, 404, { error: "not found" });
    }
    return file(res, join(publicDir(), "client", name), contentType(name));
  }
  if (req.method === "GET" && path.startsWith("/shared/")) {
    const name = path.slice("/shared/".length);
    if (!name || name.includes("..")) {
      return json(res, 404, { error: "not found" });
    }
    return file(res, join(publicDir(), "shared", name), contentType(name));
  }

  json(res, 404, { error: "not found" });
}

async function proxy(
  req: IncomingMessage,
  res: ServerResponse,
  fetchImpl: typeof fetch,
  pathWithQuery: string,
): Promise<void> {
  const target = `${afdBaseUrl()}${pathWithQuery}`;
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value == null || key === "host") continue;
    if (Array.isArray(value)) {
      for (const part of value) headers.append(key, part);
    } else {
      headers.set(key, value);
    }
  }
  const body =
    req.method === "GET" || req.method === "HEAD"
      ? undefined
      : Buffer.from(await readBody(req));
  const upstream = await fetchImpl(target, { method: req.method, headers, body });
  const text = Buffer.from(await upstream.arrayBuffer());
  res.writeHead(upstream.status, {
    "content-type": upstream.headers.get("content-type") ?? "application/json",
    "cache-control": "no-store",
  });
  res.end(text);
}

function readBody(req: IncomingMessage): Promise<Uint8Array> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function file(res: ServerResponse, path: string, type: string): void {
  send(res, readFileSync(path), type);
}

function send(res: ServerResponse, body: Buffer | string, type: string, status = 200): void {
  res.writeHead(status, { "content-type": type, "cache-control": "no-store" });
  res.end(body);
}

function json(res: ServerResponse, status: number, body: unknown): void {
  send(res, JSON.stringify(body), "application/json; charset=utf-8", status);
}

function contentType(name: string): string {
  if (name.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (name.endsWith(".css")) return "text/css; charset=utf-8";
  if (name.endsWith(".map")) return "application/json; charset=utf-8";
  return "application/octet-stream";
}
