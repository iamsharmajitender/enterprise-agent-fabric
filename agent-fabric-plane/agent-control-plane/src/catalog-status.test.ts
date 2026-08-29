import assert from "node:assert/strict";
import { test } from "node:test";
import {
  catalogStatus,
  catalogStatusClass,
  catalogStatusLabel,
  compareCatalogVersion,
  countCatalogStatuses,
  LIST_TAB_STATUSES,
  livePublishedInputs,
  parseListTabStatus,
} from "./catalog-status.js";

test("maps draft, deprecated, and live published onto one lifecycle", () => {
  assert.equal(catalogStatus({ status: "draft" }), "draft");
  assert.equal(catalogStatus({ status: "deprecated" }), "retired");
  assert.equal(catalogStatus({ status: "retired" }), "retired");
  assert.equal(catalogStatus({ status: "active" }), "active");
  assert.equal(catalogStatus({ status: "published", live: true }), "active");
  assert.equal(catalogStatus({ status: "published" }), "active");
  assert.equal(catalogStatus({ status: "published", live: false }), "published");
});

test("route active flag is Active vs Published for older cuts", () => {
  assert.equal(catalogStatus({ active: true }), "active");
  assert.equal(catalogStatus({ active: false }), "published");
});

test("labels and chip classes are stable", () => {
  assert.equal(catalogStatusLabel("active"), "Active");
  assert.equal(catalogStatusLabel("retired"), "Retired");
  assert.equal(catalogStatusClass("active"), "ok");
  assert.equal(catalogStatusClass("retired"), "warn");
  assert.equal(catalogStatusClass("published"), "info");
  assert.equal(catalogStatusClass("draft"), "");
});

test("live published is the highest published version per id", () => {
  const inputs = livePublishedInputs([
    { id: "ocr_extract", version: "1.1.0", status: "published" },
    { id: "ocr_extract", version: "1.2.0", status: "published" },
    { id: "ocr_extract", version: "1.3.0", status: "draft" },
    { id: "fax_ocr_legacy", version: "0.9.0", status: "retired" },
  ]);
  assert.deepEqual(
    inputs.map((input) => catalogStatus(input)),
    ["published", "active", "draft", "retired"],
  );
});

test("counts every lifecycle status including zeros via total", () => {
  const counts = countCatalogStatuses([
    { status: "draft" },
    { status: "published", live: false },
    { active: true },
    { status: "deprecated" },
  ]);
  assert.deepEqual(counts, { draft: 1, published: 1, active: 1, retired: 1, total: 4 });
  assert.ok(compareCatalogVersion("2026.08.1", "2026.07.1") > 0);
});

test("list tabs start at Active then Published, Draft, Retired", () => {
  assert.deepEqual(LIST_TAB_STATUSES, ["active", "published", "draft", "retired"]);
  assert.equal(parseListTabStatus(null), "active");
  assert.equal(parseListTabStatus("draft"), "draft");
  assert.equal(parseListTabStatus("versioned"), "active");
});
