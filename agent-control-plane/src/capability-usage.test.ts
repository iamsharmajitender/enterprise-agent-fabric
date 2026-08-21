import assert from "node:assert/strict";
import { test } from "node:test";
import { capabilityUsage } from "./capability-usage.js";

test("maps each capability to the latest manifests that reference it", () => {
  const rows = capabilityUsage(
    [
      {
        manifest_id: "fee_explain",
        manifest_version: "2026.08.1",
        tools: [
          { name: "account_fee_lookup", capability_id: "account_fee_lookup", capability_version: "1.0.0" },
        ],
      },
      {
        manifest_id: "fraud_investigate",
        manifest_version: "2026.08.1",
        tools: [
          { name: "ocr", capability_id: "ocr_extract", capability_version: "1.2.0" },
          { name: "start_review", capability_id: "start_contract_review", capability_version: "1.0.0" },
        ],
      },
    ],
    [
      { id: "account_fee_lookup", version: "1.0.0", description: "Look up a fee" },
      { id: "ocr_extract", version: "1.2.0", description: "OCR" },
      { id: "unused_cap", version: "1.0.0", description: "Orphan" },
    ],
  );
  assert.deepEqual(
    rows.map((row) => ({ id: row.capability_id, n: row.uses.length })),
    [
      { id: "account_fee_lookup", n: 1 },
      { id: "ocr_extract", n: 1 },
      { id: "start_contract_review", n: 1 },
      { id: "unused_cap", n: 0 },
    ],
  );
  assert.equal(rows[0]?.uses[0]?.manifest_id, "fee_explain");
  assert.equal(rows[2]?.uses[0]?.tool_name, "start_review");
});

test("expands one capability across every route that pins a referencing manifest", () => {
  const rows = capabilityUsage(
    [
      {
        manifest_id: "accounts-readonly-v2",
        manifest_version: "2026.08.1",
        tools: [{ name: "list_accounts", capability_id: "list_accounts", capability_version: "1.0.0" }],
      },
      {
        manifest_id: "account-balance-v1",
        manifest_version: "2026.08.1",
        tools: [{ name: "list_accounts", capability_id: "list_accounts", capability_version: "1.0.0" }],
      },
    ],
    [{ id: "list_accounts", version: "1.0.0", description: "List accounts" }],
    [
      {
        route_id: "agent-account-v3",
        route_version: "2026.08.1",
        tool_manifest: "accounts-readonly-v2",
        tool_manifest_version: "2026.08.1",
      },
      {
        route_id: "agent-balance-v1",
        route_version: "2026.08.1",
        tool_manifest: "account-balance-v1",
        tool_manifest_version: "2026.08.1",
      },
    ],
  );
  assert.deepEqual(
    rows[0]?.uses.map((use) => use.route_id),
    ["agent-account-v3", "agent-balance-v1"],
  );
});

test("skips tools without a capability id", () => {
  const rows = capabilityUsage(
    [{ manifest_id: "none", tools: [{ name: "local" }, { capability_id: "  " }] }],
    [],
  );
  assert.deepEqual(rows, []);
});
