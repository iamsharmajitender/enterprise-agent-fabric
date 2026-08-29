import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { catalogKey, claimsFor, expandToken } from "./catalog.js";

const here = dirname(fileURLToPath(import.meta.url));
const pkgRoot = join(here, "..", "..");

function findRepoRoot(start: string): string | null {
  let dir = start;
  for (let i = 0; i < 6; i += 1) {
    if (existsSync(join(dir, "agent-fabric-scripts/catalogue-seed/chats.json"))) {
      return dir;
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

test("catalogKey prefers id over route_id", () => {
  assert.equal(catalogKey({ id: "shopassist_case_ask", route_id: "shopassist_case" }), "shopassist_case_ask");
});

test("expandToken replaces {id}", () => {
  assert.equal(expandToken("topic {id}", "abc"), "topic abc");
});

test("claimsFor builds jane stub claims", () => {
  assert.deepEqual(claimsFor(["accounts:read"]), { sub: "jane", emts: { "accounts:read": true } });
});

test("bundled chat catalog is present and seeded", () => {
  const chatPkg = readFileSync(join(pkgRoot, "catalog/chats.json"), "utf8");
  assert.match(chatPkg, /"id": "shopassist_case_ask"/);

  const repoRoot = findRepoRoot(pkgRoot);
  if (repoRoot) {
    assert.equal(
      chatPkg,
      readFileSync(join(repoRoot, "agent-fabric-scripts/catalogue-seed/chats.json"), "utf8"),
    );
  }
});
