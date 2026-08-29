import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "..", "public", "index.html"), "utf8");
const js = readFileSync(join(here, "..", "public", "app.js"), "utf8");
const css = readFileSync(join(here, "..", "public", "styles.css"), "utf8");

test("landing is titled Enterprise Agent Fabric", () => {
  assert.match(html, /<h1>Enterprise Agent Fabric<\/h1>/);
  assert.match(html, /<title>Enterprise Agent Fabric<\/title>/);
  assert.match(js, /Enterprise Agent Fabric/);
});

test("header has Audit then Glossary then Observability then Scratchpad", () => {
  assert.match(html, /class="header-actions"/);
  assert.match(html, /class="header-btn"/);
  assert.match(html, /href="http:\/\/localhost:3013\/"/);
  assert.match(html, /href="http:\/\/localhost:3000\/"/);
  assert.match(html, /href="http:\/\/localhost:3014\/chat"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, />Audit</);
  assert.match(html, />Glossary</);
  assert.match(html, />Observability</);
  assert.match(html, />Scratchpad</);
  const audit = html.indexOf(">Audit<");
  const glossary = html.indexOf(">Glossary<");
  const observability = html.indexOf(">Observability<");
  const scratchpad = html.indexOf(">Scratchpad<");
  assert.ok(
    audit > 0 &&
      glossary > audit &&
      observability > glossary &&
      scratchpad > observability,
  );
  assert.match(css, /\.header-btn/);
  assert.match(css, /\.top \{[\s\S]*position:\s*sticky/);
});

test("glossary button opens a term table for catalogue rows and fields", () => {
  assert.match(html, /id="glossary-open"/);
  assert.match(html, /id="glossary"/);
  assert.match(html, /role="dialog"/);
  assert.match(html, /class="glossary__panel"/);
  assert.match(html, /<details class="glossary__section">/);
  assert.equal(html.includes('glossary__section" open'), false);
  assert.match(html, /<summary>Route<\/summary>/);
  assert.match(html, /<summary>Capability<\/summary>/);
  assert.match(html, /<summary>Corpus<\/summary>/);
  assert.match(html, /<summary>Prompt<\/summary>/);
  assert.match(html, /<summary>Workflow<\/summary>/);
  assert.match(html, /<summary>Manifest<\/summary>/);
  assert.match(html, /<summary>Status<\/summary>/);
  assert.equal(html.includes("<summary>Autonomy</summary>"), false);
  assert.equal(html.includes("<summary>Kind</summary>"), false);
  assert.equal(html.includes("<summary>Policy</summary>"), false);
  assert.equal(html.includes("<summary>Model</summary>"), false);
  assert.equal(html.includes("<summary>Risk</summary>"), false);
  assert.equal(html.includes("<summary>Retrieval</summary>"), false);
  assert.equal(html.includes("<summary>LLM role</summary>"), false);
  assert.equal(html.includes("<summary>Workflow stage</summary>"), false);
  assert.match(html, />Route</);
  assert.match(html, />Capability</);
  assert.match(html, />Corpus</);
  assert.match(html, />Prompt</);
  assert.match(html, />Workflow</);
  assert.match(html, />Manifest</);
  assert.match(html, />Intent</);
  assert.match(html, />Autonomy</);
  assert.match(html, />Activation target</);
  assert.match(html, />Host</);
  assert.match(html, />Stage fields</);
  assert.match(html, />Tools</);
  assert.match(html, />Active</);
  assert.match(html, />Single inference</);
  assert.match(html, /route_id/);
  assert.match(html, /tool_manifest/);
  assert.match(html, /high_risk_step_up/);
  assert.match(html, /read_only_standard/);
  assert.match(html, /low_risk_chat/);
  assert.match(html, /reasoning-standard/);
  assert.match(html, /fast-chat/);
  assert.match(html, /lightweight-chat/);
  assert.match(html, /deterministic_prefetch/);
  assert.match(html, /risk_tier/);
  assert.match(html, /<span class="mono">low<\/span>/);
  assert.match(html, /<span class="mono">medium<\/span>/);
  assert.match(html, /<span class="mono">high<\/span>/);
  assert.match(html, /<span class="mono">domain<\/span>/);
  assert.match(html, /<span class="mono">agent<\/span>/);
  assert.match(html, /<span class="mono">classify<\/span>/);
  assert.match(html, /<span class="mono">synthesis<\/span>/);
  assert.match(html, /<span class="mono">query_formulation<\/span>/);
  assert.match(html, /<span class="mono">human_gate<\/span>/);
  assert.match(html, /glossary-key">side_effect</);
  assert.match(html, /glossary-key">requires_approval</);
  assert.match(html, /glossary-key">allowlist</);
  assert.match(html, /glossary-key">max_tool_calls</);
  assert.match(html, /glossary-key">branch</);
  assert.match(html, /glossary-key">corpus_id</);
  assert.match(html, /glossary-key">corpus</);
  assert.match(html, /aria-expanded="false"/);
  assert.match(js, /function setGlossaryOpen/);
  assert.match(js, /glossaryEl.hidden = !open/);
  assert.match(js, /function closeOtherGlossarySections/);
  assert.match(js, /section.open = false/);
  assert.match(css, /\.glossary-table/);
  assert.match(css, /\.glossary__panel/);
  assert.match(css, /\.glossary\[hidden\]/);
  assert.match(css, /\.glossary__section > summary/);
});

test("home shows a row of status tiles per catalogue type", () => {
  assert.match(js, /function showLanding/);
  assert.match(js, /function buildCatalogRow/);
  assert.match(js, /function buildStatusTile/);
  assert.match(js, /function countAutonomyModes/);
  assert.match(js, /function autonomyModeSummary/);
  assert.match(js, /catalog-row__tiles/);
  assert.match(js, /catalog-row__icon/);
  assert.match(js, /catalog-row__summary/);
  assert.match(js, /CATALOG_ICONS/);
  assert.match(js, /LIST_TAB_STATUSES/);
  assert.match(js, /include=all/);
  assert.match(js, /"Routes"/);
  assert.match(js, /"Capabilities"/);
  assert.match(js, /"Prompts"/);
  assert.match(js, /"Workflows"/);
  assert.match(js, /"Manifests"/);
  assert.match(js, /"Corpora"/);
  assert.match(js, /icon: "routes"/);
  assert.match(js, /icon: "corpora"/);
  const landingFn = js.indexOf("async function showLanding");
  const routesFn = js.indexOf("async function showRoutes");
  const landing = js.slice(landingFn, routesFn);
  assert.equal(landing.includes("Usage"), false);
  assert.equal(landing.includes("/capability/usage"), false);
  assert.match(landing, /summary: routeAutonomySummary/);
  assert.match(landing, /route\.active === true/);
  assert.match(css, /\.catalog-row__tiles/);
  assert.match(css, /\.catalog-row__icon/);
  assert.match(css, /\.catalog-row__summary/);
  assert.match(css, /\.tile--ok/);
  assert.match(css, /\.tile__value/);
});

test("catalogue lists show a page title for the current catalogue", () => {
  assert.match(js, /el\("h2", "page-title", title\)/);
  assert.match(js, /title: "Routes"/);
  assert.match(js, /title: "Capabilities"/);
  assert.match(js, /title: "Prompts"/);
  assert.match(js, /title: "Workflows"/);
  assert.match(js, /title: "Manifests"/);
  assert.match(js, /title: "Corpora"/);
  assert.match(css, /\.page-title/);
});

test("catalogue lists filter with Active-first status tabs", () => {
  assert.match(js, /function buildStatusTabs/);
  assert.match(js, /LIST_TAB_STATUSES/);
  assert.match(js, /role", "tablist"/);
  assert.match(js, /basePath: "\/routes"/);
  assert.match(js, /basePath: "\/capabilities"/);
  assert.match(js, /basePath: "\/prompts"/);
  assert.match(js, /basePath: "\/workflows"/);
  assert.match(js, /basePath: "\/manifests"/);
  assert.match(js, /basePath: "\/corpora"/);
  assert.match(css, /\.status-tabs__tab/);
  assert.match(css, /\.chip\.info/);
  assert.match(css, /\.chip\.autonomy-single/);
  assert.match(css, /\.chip\.autonomy-autonomous/);
  assert.match(css, /\.chip\.autonomy-deterministic/);
  assert.match(css, /\.chip\.autonomy-guided/);
  assert.match(js, /catalogStatusClass\(status\)/);
});

test("routes table lives on /routes", () => {
  assert.match(js, /path === "\/routes"/);
  assert.match(js, /go\("\/prompts"/);
  assert.match(js, /go\("\/workflows"/);
  assert.match(js, /go\("\/manifests"/);
  assert.match(js, /href: "\/prompts"/);
  assert.match(js, /href: "\/workflows"/);
  assert.match(js, /href: "\/manifests"/);
  assert.match(js, /href: "\/corpora"/);
  assert.match(js, /path === "\/corpora"/);
  assert.match(js, /path === "\/capability\/usage"/);
  assert.match(js, /path === "\/capability\/usage"/);
  const routesFn = js.indexOf("async function showRoutes");
  const landingFn = js.indexOf("async function showLanding");
  assert.ok(landingFn > 0 && routesFn > landingFn);
  assert.equal(js.slice(landingFn, routesFn).includes("routes-table"), false);
});

test("landing does not show catalogue product, version, or active pills", () => {
  const routesFn = js.indexOf("async function showRoutes");
  const landingFn = js.indexOf("async function showLanding");
  const landing = js.slice(landingFn, routesFn);
  assert.match(landing, /clearMeta\(\)/);
  assert.equal(landing.includes("applyMeta"), false);
});
