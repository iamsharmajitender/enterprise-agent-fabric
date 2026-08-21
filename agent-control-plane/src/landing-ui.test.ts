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

test("header has Observability then Scratchpad buttons that open in a new tab", () => {
  assert.match(html, /class="header-actions"/);
  assert.match(html, /class="header-btn"/);
  assert.match(html, /href="http:\/\/localhost:3000\/"/);
  assert.match(html, /href="http:\/\/localhost:3005\/chat\.html"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, />Observability</);
  assert.match(html, />Scratchpad</);
  const observability = html.indexOf(">Observability<");
  const scratchpad = html.indexOf(">Scratchpad<");
  assert.ok(observability > 0 && scratchpad > observability);
  assert.match(css, /\.header-btn/);
  assert.match(css, /\.top \{[\s\S]*position:\s*sticky/);
});

test("home shows a row of status tiles per catalogue type", () => {
  assert.match(js, /function showLanding/);
  assert.match(js, /function buildCatalogRow/);
  assert.match(js, /function buildStatusTile/);
  assert.match(js, /catalog-row__tiles/);
  assert.match(js, /catalog-row__icon/);
  assert.match(js, /CATALOG_ICONS/);
  assert.match(js, /LIST_TAB_STATUSES/);
  assert.match(js, /include=all/);
  assert.match(js, /"Routes"/);
  assert.match(js, /"Capabilities"/);
  assert.match(js, /"Prompts"/);
  assert.match(js, /"Workflows"/);
  assert.match(js, /"Manifests"/);
  assert.match(js, /icon: "routes"/);
  const landingFn = js.indexOf("async function showLanding");
  const routesFn = js.indexOf("async function showRoutes");
  const landing = js.slice(landingFn, routesFn);
  assert.equal(landing.includes("Usage"), false);
  assert.equal(landing.includes("/capability/usage"), false);
  assert.match(css, /\.catalog-row__tiles/);
  assert.match(css, /\.catalog-row__icon/);
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
