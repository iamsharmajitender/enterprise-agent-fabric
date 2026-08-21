import assert from "node:assert/strict";
import { test } from "node:test";
import { RegistryClient } from "./registry-client.js";

test("capability GET sends X-Workload acp", async () => {
  const seen: { href: string; headers: Headers }[] = [];
  const fetchImpl: typeof fetch = async (input, init) => {
    seen.push({ href: String(input), headers: new Headers(init?.headers) });
    return new Response("{}", { status: 404 });
  };
  const client = new RegistryClient("http://agent-capability-registry:3009", fetchImpl);

  await client.listCapabilities();
  await client.getCapability("ocr_extract");
  await client.getCapability("ocr_extract", "1.2.0");
  await client.listCapabilityVersions("ocr_extract");

  assert.equal(seen.length, 4);
  assert.match(seen[0]?.href ?? "", /\/v1\/capabilities$/);
  assert.match(seen[1]?.href ?? "", /\/v1\/capabilities\/ocr_extract$/);
  assert.match(seen[2]?.href ?? "", /\/v1\/capabilities\/ocr_extract\/versions\/1\.2\.0$/);
  assert.match(seen[3]?.href ?? "", /\/v1\/capabilities\/ocr_extract\/versions$/);
  for (const call of seen) {
    assert.equal(call.headers.get("X-Workload"), "acp");
    assert.equal(call.headers.get("Authorization"), "Bearer fabric-internal");
  }
});
