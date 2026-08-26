import assert from "node:assert/strict";
import { test } from "node:test";
import { DataPlaneClient } from "./data-plane-client.js";

test("eligible and catalogue GET send X-Workload acp", async () => {
  const seen: Headers[] = [];
  const fetchImpl: typeof fetch = async (_input, init) => {
    seen.push(new Headers(init?.headers));
    return new Response("{}", { status: 404 });
  };
  const client = new DataPlaneClient("http://agent-data-plane:3007", fetchImpl);

  await client.getEligible();
  await client.listRoutes();
  await client.getCatalogueRoute("fee_explain", "2026.08.1");
  await client.listRouteVersions("fee_explain");
  await client.listPrompts();
  await client.getPrompt("fee_explain");
  await client.listPromptVersions("fee_explain");
  await client.listWorkflows();
  await client.getWorkflow("kyc_onboarding");
  await client.listWorkflowVersions("kyc_onboarding");
  await client.listManifests();
  await client.getManifest("fee_explain");
  await client.listManifestVersions("fee_explain");
  await client.listCorpora();
  await client.getCorpus("policy-engine");

  assert.equal(seen.length, 15);
  for (const headers of seen) {
    assert.equal(headers.get("X-Workload"), "acp");
    assert.equal(headers.get("Authorization"), "Bearer fabric-internal");
  }
});
