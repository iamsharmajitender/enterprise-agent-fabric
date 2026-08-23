import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "public");
const js = readFileSync(join(root, "app.js"), "utf8");
const css = readFileSync(join(root, "styles.css"), "utf8");

test("history sits before JSON and opens a dedicated page", () => {
  assert.equal(js.includes("function buildHistory"), false);
  const historyNav = js.indexOf("/routes/${encodeURIComponent(routeId)}/history");
  const jsonBtn = js.indexOf('el("button", "ghost-btn", "JSON")', historyNav);
  assert.ok(historyNav > 0, "History must navigate to /history");
  assert.ok(jsonBtn > historyNav, "History control must be created before JSON");
  assert.match(js, /page === "history"/);
  assert.match(js, /revisionCount/);
  assert.match(js, /showing-history/);
});

test("routes page is a latest-routes table that opens route detail", () => {
  assert.match(js, /function showRoutes/);
  assert.match(js, /routes-table/);
  assert.match(js, /Activate a row to open route detail/);
  assert.match(js, /\/routes\/\$\{encodeURIComponent\(item.route_id\)\}/);
  assert.equal(js.includes("#route-list"), false);
});

test("detail nested values recurse into objects inside arrays", () => {
  const start = js.indexOf("function renderValue");
  const end = js.indexOf("function skeletonCards");
  const render = js.slice(start, end);
  assert.match(render, /nested-list/);
  assert.match(render, /typeof item !== "object"/);
});

test("capability schemas render as a field table", () => {
  const start = js.indexOf("function renderValue");
  const end = js.indexOf("function skeletonCards");
  const render = js.slice(start, end);
  assert.match(js, /function renderJsonSchema/);
  assert.match(js, /function schemaTypeLabel/);
  assert.match(render, /isObjectSchema\(value\)/);
  assert.match(js, /\["Field", "Type", "Required"\]/);
});

test("detail sections flatten retrieval, memory, invoke, and roles", () => {
  assert.match(js, /function appendSectionFields/);
  assert.match(js, /function appendExpandedFields/);
  assert.match(js, /function isRoleSpec/);
  assert.match(js, /field-wide/);
  assert.match(js, /role-text/);
  assert.match(js, /\$\{value\} hours/);
});

test("manifest field renders a HeroUI card with tools below", () => {
  assert.match(js, /function renderManifestTable/);
  assert.match(js, /function renderToolsTable/);
  assert.match(js, /card card--default/);
  assert.match(js, /table-root table-root--primary/);
  assert.match(js, /el\("hr", "separator"\)/);
  assert.match(js, /extraNodes: \(row\) => \[renderManifestTable\(row\)\]/);
});

test("catalogue UI uses human field labels instead of SQL types", () => {
  assert.equal(js.includes("schemaHead"), false);
  assert.equal(js.includes("jsonb"), false);
  assert.equal(js.includes("text NULL"), false);
  assert.equal(js.includes("PDP action"), false);
  assert.match(js, /function fieldLabel/);
  assert.match(js, /pdp_action: "Action"/);
});

test("autonomy chips use named labels and a color class per mode", () => {
  assert.match(js, /0: "Single inference"/);
  assert.match(js, /1: "Autonomous"/);
  assert.match(js, /2: "Deterministic"/);
  assert.match(js, /3: "Guided"/);
  assert.equal(js.includes("0 ·"), false);
  assert.equal(js.includes("1 ·"), false);
  assert.equal(js.includes("2 ·"), false);
  assert.equal(js.includes("3 ·"), false);
  assert.match(js, /0: "autonomy-single"/);
  assert.match(js, /1: "autonomy-autonomous"/);
  assert.match(js, /2: "autonomy-deterministic"/);
  assert.match(js, /3: "autonomy-guided"/);
  assert.match(js, /function autonomyModeClass/);
  assert.match(js, /function autonomyPill/);
  assert.match(js, /pill\(autonomyLabel, autonomyModeClass\(row\.autonomy_mode\)\)/);
  assert.match(js, /key === "autonomy_mode"/);
  assert.match(js, /return autonomyPill\(value\)/);
});

test("route detail stacks manifest then retrieval under tools and retrieval", () => {
  assert.match(js, /stacked: true/);
  assert.match(js, /function buildSection/);
  assert.match(js, /function renderRetrievalCard/);
  assert.match(js, /function hasRetrieval/);
  assert.match(js, /pill\(retrievalListLabel\(value\), "info"\)/);
  assert.match(js, /hasRetrieval\(row\.retrieval\)/);
  assert.match(js, /"Retrieval", "Chat"/);
  assert.match(js, /"Autonomy", "Description"/);
  assert.match(js, /autonomyCell\(item\.autonomy_mode\)/);
  assert.match(js, /retrievalListLabel\(item\.retrieval\)/);
  assert.match(css, /\.section-stack/);
  assert.equal(js.includes("Who starts retrieve"), false);
  assert.equal(js.includes("LLM may propose retrieve inside scope"), false);
  assert.equal(js.includes("function appendRetrievalFields"), false);
});

test("route detail links prompt, workflow, and capability ids", () => {
  assert.match(js, /prompt_id: "prompts"/);
  assert.match(js, /workflow_id: "workflows"/);
  assert.match(js, /capability_id: "capabilities"/);
  assert.match(js, /catalogHref\("capability_id", tool.capability_id\)/);
  assert.match(js, /catalogHref\("prompt_id", item.prompt_id\)/);
  assert.match(js, /function showPrompts/);
  assert.match(js, /function showWorkflows/);
  assert.match(js, /function showManifests/);
  assert.match(js, /function renderStagesTable/);
  assert.match(js, /Object.hasOwn\(CATALOG_PATH, key\)/);
});

test("capability usage page lists manifests per capability", () => {
  assert.match(js, /function showUsage/);
  assert.match(js, /Used by/);
  assert.match(js, /capabilityUsage/);
  assert.match(js, /use\.route_id/);
});

test("routes Manifest column shows a tool-count icon from embedded manifest", () => {
  const routes = js.slice(js.indexOf("async function showRoutes"), js.indexOf("async function showCapabilities"));
  assert.match(js, /function countIcon/);
  assert.match(js, /function manifestCell/);
  assert.match(js, /TOOL_COUNT_ICON/);
  assert.match(routes, /manifestCell\(item\)/);
  assert.match(css, /\.count-icon/);
  assert.match(css, /\.cell-with-count/);
});

test("catalogue lists omit Status because tabs already filter", () => {
  assert.match(
    js,
    /columns: \["Route", "Intent", "Autonomy", "Description", "Model", "Policy", "Manifest", "Prompt", "Retrieval", "Chat"\]/,
  );
  assert.match(js, /columns: \["Capability", "Kind", "Description", "Owner", "Version"\]/);
  assert.match(js, /columns: \["Prompt", "Version", "Owner", "Host"\]/);
  assert.match(js, /columns: \["Workflow", "Version", "Description", "Stages"\]/);
  assert.match(js, /columns: \["Manifest", "Version", "Description", "Tools"\]/);
  const routes = js.slice(js.indexOf("async function showRoutes"), js.indexOf("async function showCapabilities"));
  const caps = js.slice(js.indexOf("async function showCapabilities"), js.indexOf("async function showCapability("));
  const prompts = js.slice(js.indexOf("async function showPrompts"), js.indexOf("async function showWorkflows"));
  const workflows = js.slice(js.indexOf("async function showWorkflows"), js.indexOf("async function showManifests"));
  const manifests = js.slice(js.indexOf("async function showManifests"), js.indexOf("function usageList"));
  for (const [name, slice] of [
    ["showRoutes", routes],
    ["showCapabilities", caps],
    ["showPrompts", prompts],
    ["showWorkflows", workflows],
    ["showManifests", manifests],
  ]) {
    assert.ok(slice.length > 0, `${name} slice must exist`);
    assert.equal(slice.includes("statusCell("), false, `${name} list must not render statusCell`);
  }
});

test("catalogue pages map status through Draft Published Active Retired", () => {
  assert.match(js, /function statusPill/);
  assert.match(js, /function statusCell/);
  assert.match(js, /key === "status"/);
  assert.equal(js.includes("cell(item.status)"), false);
  assert.match(js, /catalogStatusLabel/);
});

test("JSON panel renders a collapsible tree per object and array", () => {
  assert.match(js, /function renderJsonNode/);
  assert.match(js, /el\("details", "json-node"\)/);
  assert.match(js, /el\("div", "json-tree"\)/);
  assert.match(js, /querySelector\("summary"\)/);
  assert.equal(js.includes("pre.textContent = json"), false);
});
