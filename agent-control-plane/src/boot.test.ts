import assert from "node:assert/strict";
import { test } from "node:test";
import { boot } from "./boot.js";

test("boot smoke logs client role and catalogue UI port", () => {
  const lines: string[] = [];
  boot((line) => lines.push(line));
  assert.equal(lines.length, 1);
  const payload = JSON.parse(lines[0] ?? "{}") as {
    service: string;
    role: string;
    listen: boolean;
    port: number;
    workload: string;
  };
  assert.equal(payload.service, "agent-control-plane");
  assert.equal(payload.role, "client");
  assert.equal(payload.listen, true);
  assert.equal(payload.port, 3006);
  assert.equal(payload.workload, "acp");
});
