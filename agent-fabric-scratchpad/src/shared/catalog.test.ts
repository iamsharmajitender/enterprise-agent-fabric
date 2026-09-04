import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { catalogKey, claimsFor, expandToken, pickDemoHintId } from "./catalog.js";
import type { ChatRow } from "./types.js";

const here = dirname(fileURLToPath(import.meta.url));
const pkgRoot = join(here, "..", "..");

test("catalogKey prefers id over route_id", () => {
  assert.equal(catalogKey({ id: "shopassist_case_ask", route_id: "shopassist_case" }), "shopassist_case_ask");
});

test("expandToken replaces {id}", () => {
  assert.equal(expandToken("topic {id}", "abc"), "topic abc");
});

test("claimsFor builds jane stub claims", () => {
  assert.deepEqual(claimsFor(["accounts:read"]), { sub: "jane", emts: { "accounts:read": true } });
});

test("pickDemoHintId pins ticket_triage via hint_contains among support chips", () => {
  const hints = [
    { hint_id: "hint-shop", label: "Pattern 1 (autonomous): ShopAssist front-line support." },
    { hint_id: "hint-dup", label: "Pattern 2 (deterministic): duplicate-charge check." },
    { hint_id: "hint-triage", label: "Pattern 3 (guided): parse → tag → draft_reply." },
  ];
  assert.equal(
    pickDemoHintId(hints, { route_id: "ticket_triage", hint_contains: "Pattern 3" }),
    "hint-triage",
  );
});

test("pickDemoHintId fails closed when catalog route is ambiguous without hint_contains", () => {
  const hints = [
    { hint_id: "hint-a", label: "ShopAssist" },
    { hint_id: "hint-b", label: "Pattern 3 guided" },
  ];
  assert.throws(
    () => pickDemoHintId(hints, { route_id: "ticket_triage" }),
    /ambiguous hints for ticket_triage/,
  );
});

test("bundled chat catalog pins every route with hint_contains", () => {
  const chatPkg = readFileSync(join(pkgRoot, "catalog/chats.json"), "utf8");
  assert.match(chatPkg, /"id": "shopassist_case_ask"/);
  assert.match(chatPkg, /"id": "duplicate_charge_review"/);
  assert.match(chatPkg, /"id": "ticket_triage"/);
  const body = JSON.parse(chatPkg) as { chats?: ChatRow[] };
  for (const chat of body.chats ?? []) {
    assert.ok(chat.hint_contains, `${catalogKey(chat)} needs hint_contains to pin route_id`);
  }
});
