import assert from "node:assert/strict";
import { test } from "node:test";
import { catalogueStats, fabricWiring } from "./catalogue-stats.js";

test("counts unique prompts and manifests, skipping none", () => {
  const stats = catalogueStats({
    routes: [
      { prompt_id: "a", tool_manifest: "m1" },
      { prompt_id: "a", tool_manifest: "none" },
      { prompt_id: "b", tool_manifest: "m1" },
      { prompt_id: null, manifest: { manifest_id: "m2" } },
    ],
  });
  assert.deepEqual(stats, {
    routes: 4,
    prompts: 2,
    manifests: 2,
  });
});

test("empty catalogue has zero counts", () => {
  assert.deepEqual(catalogueStats({}), {
    routes: 0,
    prompts: 0,
    manifests: 0,
  });
});

test("fabric wiring counts used catalogue ids vs unbound routes", () => {
  const wiring = fabricWiring({
    routes: [
      { prompt_id: "fee_explain", workflow_id: "kyc_onboarding", tool_manifest: "fee_explain" },
      { prompt_id: "fee_explain", workflow_id: null, tool_manifest: "none" },
      { prompt_id: null, workflow_id: "kyc_onboarding", manifest: { manifest_id: "m2" } },
    ],
    prompts: [{ prompt_id: "fee_explain" }, { prompt_id: "unused_prompt" }, { prompt_id: "fee_explain" }],
    workflows: [{ workflow_id: "kyc_onboarding" }, { workflow_id: "orphan_flow" }],
    manifests: [
      {
        manifest_id: "fee_explain",
        tools: [{ capability_id: "account_fee_lookup" }, { capability_id: "  " }],
      },
      { manifest_id: "unused_manifest", tools: [] },
      { manifest_id: "m2", tools: [{ capability_id: "ocr_extract" }] },
    ],
    capabilities: [
      { id: "account_fee_lookup" },
      { id: "ocr_extract" },
      { id: "unused_cap" },
    ],
  });
  assert.deepEqual(wiring.prompts, { used: 1, total: 2, unused: 1, unboundRoutes: 1 });
  assert.deepEqual(wiring.manifests, { used: 2, total: 3, unused: 1, unboundRoutes: 1 });
  assert.deepEqual(wiring.workflows, { used: 1, total: 2, unused: 1, unboundRoutes: 1 });
  assert.deepEqual(wiring.capabilities, { used: 2, total: 3, unused: 1, unboundRoutes: 0 });
});

test("empty fabric wiring is zeros", () => {
  assert.deepEqual(fabricWiring({}), {
    prompts: { used: 0, total: 0, unused: 0, unboundRoutes: 0 },
    manifests: { used: 0, total: 0, unused: 0, unboundRoutes: 0 },
    workflows: { used: 0, total: 0, unused: 0, unboundRoutes: 0 },
    capabilities: { used: 0, total: 0, unused: 0, unboundRoutes: 0 },
  });
});
