import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SIGNED = readFileSync(join(REPO_ROOT, ".github", "workflows", "publish-signed.yml"), "utf8");
const DEFAULT = readFileSync(join(REPO_ROOT, ".github", "workflows", "publish.yml"), "utf8");

test("signed publish runs only on manual dispatch, so it cannot race publish.yml", () => {
  assert.match(SIGNED, /^on:\n\s+workflow_dispatch:/m);
  assert.doesNotMatch(SIGNED, /^\s+push:/m);
  assert.doesNotMatch(SIGNED, /^\s+schedule:/m);
});

test("both publish workflows share a concurrency group per channel", () => {
  assert.match(SIGNED, /group: publish-\$\{\{ inputs\.channel \}\}/);
  assert.match(DEFAULT, /group: publish-/);
});

test("signed publish offers only the npmjs channels", () => {
  const options = SIGNED.slice(SIGNED.indexOf("options:")).split("\n").slice(1, 3);
  assert.deepEqual(
    options.map((line) => line.trim()),
    ["- preview", "- latest"],
  );
});

test("hooks are overlaid before the package is packed", () => {
  const overlay = SIGNED.indexOf("name: Overlay signed hooks");
  const pack = SIGNED.indexOf("npm pack --pack-destination");
  assert.ok(overlay > -1 && pack > -1);
  // A signature covers exact bytes, so the signed file must be the packed one.
  assert.ok(overlay < pack, "overlay must precede pack");
});

test("the packed tarball is verified, then that same tarball is published", () => {
  assert.match(SIGNED, /TARBALL=\$\(ls uipath-skills-\*\.tgz\)/);
  assert.match(
    SIGNED,
    /run: node scripts\/check-hook-signatures\.mjs "\$\{\{ steps\.pack\.outputs\.tarball \}\}"/,
  );
  assert.match(
    SIGNED,
    /npm publish "\$\{\{ steps\.pack\.outputs\.tarball \}\}" \\\n\s*--access public --provenance --tag "\$\{\{ steps\.dist\.outputs\.tag \}\}"/,
  );

  const verify = SIGNED.indexOf("check-hook-signatures.mjs");
  const publish = SIGNED.indexOf("npm publish ");
  assert.ok(verify < publish, "verification must precede publish");
});

test("signing failure has no unsigned fallback", () => {
  assert.match(SIGNED, /^\s*run: node scripts\/fetch-signed-hooks\.mjs\s*$/m);
  assert.doesNotMatch(SIGNED, /REQUIRE_HOOK_SIGNING|REQUIRE_SIGNING/);
  assert.doesNotMatch(SIGNED, /publishing unsigned/i);
});

test("the gate job pins its OIDC subject through an environment", () => {
  assert.match(SIGNED, /^\s*environment: release-gate\s*$/m);
  assert.match(SIGNED, /^\s*id-token: write\s*$/m);
});

test("publish.yml carries no signing steps", () => {
  assert.doesNotMatch(DEFAULT, /fetch-signed-hooks|check-hook-signatures|signed-hooks/);
});
