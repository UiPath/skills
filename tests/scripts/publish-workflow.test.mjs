import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const WORKFLOWS = join(REPO_ROOT, ".github", "workflows");
const PUBLISH = readFileSync(join(WORKFLOWS, "publish.yml"), "utf8");

/** Text of one top-level job, up to the next job key at two-space indent. */
function job(name) {
  const start = PUBLISH.indexOf(`\n  ${name}:\n`);
  assert.notEqual(start, -1, `no ${name} job in publish.yml`);
  const rest = PUBLISH.slice(start + 1);
  const end = rest.slice(1).search(/\n {2}[a-z][a-z0-9-]*:\n/);
  return end === -1 ? rest : rest.slice(0, end + 1);
}

/** The `if:` expression of a job, normalized to one line. */
function gate(name) {
  const match = job(name).match(/^\s{4}if: >-\n([\s\S]*?)\n\s{4}[a-z]/m);
  assert.ok(match, `no multi-line if: on ${name}`);
  return match[1].replace(/\s+/g, " ").trim();
}

test("publishing to npmjs cannot start without the signing job", () => {
  assert.match(job("publish-npmjs"), /needs: \[guard, sign-hooks\]/);
});

// Drift here is the failure that matters: a channel that reaches npmjs
// without a gate run would publish unsigned hooks, and a gate run for a
// channel that never reaches npmjs burns a Windows agent for nothing.
test("the signing gate and the npmjs gate are the same condition", () => {
  assert.equal(gate("sign-hooks"), gate("publish-npmjs"));
});

// dev publishes on every push to main. Signing each one buys nothing for a
// channel no end user installs, and would queue an ADO run per merge.
test("the dev channel does not depend on signing", () => {
  assert.match(job("publish-dev"), /needs: \[guard\]/);
});

test("hooks are overlaid before the package is packed", () => {
  const npmjs = job("publish-npmjs");
  const overlay = npmjs.indexOf("name: Overlay signed hooks");
  const pack = npmjs.indexOf("npm pack --pack-destination");
  assert.ok(overlay > -1 && pack > -1);
  // A signature covers exact bytes, so the signed file must be the packed one.
  assert.ok(overlay < pack, "overlay must precede pack");
});

test("the packed tarball is verified, then that same tarball is published", () => {
  assert.match(PUBLISH, /TARBALL=\$\(ls uipath-skills-\*\.tgz\)/);
  assert.match(
    PUBLISH,
    /run: node scripts\/check-hook-signatures\.mjs "\$\{\{ steps\.pack\.outputs\.tarball \}\}"/,
  );
  assert.match(PUBLISH, /npm publish "\$\{\{ steps\.pack\.outputs\.tarball \}\}"/);

  const verify = PUBLISH.indexOf("check-hook-signatures.mjs");
  const publish = PUBLISH.indexOf("npm publish \"");
  assert.ok(verify < publish, "verification must precede publish");
});

test("signing failure has no unsigned fallback", () => {
  assert.match(PUBLISH, /^\s*run: node scripts\/fetch-signed-hooks\.mjs\s*$/m);
  assert.doesNotMatch(PUBLISH, /REQUIRE_HOOK_SIGNING|REQUIRE_SIGNING/);
  assert.doesNotMatch(PUBLISH, /publishing unsigned/i);
});

test("the gate job pins its OIDC subject through an environment", () => {
  const sign = job("sign-hooks");
  assert.match(sign, /^\s*environment: release-gate\s*$/m);
  assert.match(sign, /^\s*id-token: write\s*$/m);
});

// The npmjs trusted publisher names one workflow file. A second workflow
// publishing to npmjs cannot authenticate, so there is exactly one.
test("publish.yml is the only publish workflow", () => {
  assert.ok(!existsSync(join(WORKFLOWS, "publish-signed.yml")));
});
