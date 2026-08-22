import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { INTERNAL_BEARER, WORKLOAD_ID, workloadHeaders } from "./workload.js";

test("outbound identity is acp only", () => {
  const headers = workloadHeaders();
  assert.equal(WORKLOAD_ID, "acp");
  assert.equal(headers["X-Workload"], "acp");
  assert.equal(headers.Authorization, INTERNAL_BEARER);
  assert.equal(Object.keys(headers).length, 2);
});

test("package has no HTTP server or Postgres client", () => {
  const pkg = JSON.parse(readFileSync("package.json", "utf8")) as {
    dependencies?: Record<string, string>;
  };
  const deps = Object.keys(pkg.dependencies ?? {});
  const forbidden = deps.filter(
    (name) =>
      name === "express" ||
      name === "fastify" ||
      name === "koa" ||
      name === "pg" ||
      name === "postgres" ||
      name.startsWith("@nestjs/"),
  );
  assert.deepEqual(forbidden, []);
  for (const name of deps) {
    assert.ok(
      name.startsWith("@opentelemetry/"),
      `unexpected runtime dependency: ${name}`,
    );
  }
});
