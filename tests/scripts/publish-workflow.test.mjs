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

test("publishing to npmjs cannot start without the release gate", () => {
  assert.match(job("publish-npmjs"), /needs: \[guard, release-gate\]/);
});

// Drift here is the failure that matters: a channel that reaches npmjs
// without a gate run would publish without the blocking FOSSA scan, and a
// gate run for a channel that never reaches npmjs burns an agent for nothing.
test("the release gate and the npmjs gate are the same condition", () => {
  assert.equal(gate("release-gate"), gate("publish-npmjs"));
});

// dev publishes on every push to main. Gating each one buys nothing for a
// channel no end user installs, and would queue an ADO run per merge.
test("the dev channel does not depend on the release gate", () => {
  assert.match(job("publish-dev"), /needs: \[guard\]/);
});

test("the packed tarball is the tarball that gets published", () => {
  assert.match(PUBLISH, /TARBALL=\$\(ls uipath-skills-\*\.tgz\)/);
  assert.match(PUBLISH, /npm publish "\$\{\{ steps\.pack\.outputs\.tarball \}\}"/);
});

test("gate failure has no ungated fallback", () => {
  assert.match(PUBLISH, /^\s*run: node scripts\/run-release-gate\.mjs\s*$/m);
  assert.doesNotMatch(PUBLISH, /REQUIRE_HOOK_SIGNING|REQUIRE_SIGNING|REQUIRE_GATE/);
  assert.doesNotMatch(PUBLISH, /publishing ungated|publishing unsigned/i);
});

test("the gate job pins its OIDC subject through an environment", () => {
  const gateJob = job("release-gate");
  assert.match(gateJob, /^\s*environment: release-gate\s*$/m);
  assert.match(gateJob, /^\s*id-token: write\s*$/m);
});

// The hooks are Node scripts; nothing in the publish path may resurrect the
// retired PowerShell signing seam (overlay/verify steps, .ps1 artifacts).
test("no signing remnants survive in the publish path", () => {
  assert.doesNotMatch(PUBLISH, /signed-hooks|check-hook-signatures|fetch-signed-hooks|\.ps1/);
});

// The npmjs trusted publisher names one workflow file. A second workflow
// publishing to npmjs cannot authenticate, so there is exactly one.
test("publish.yml is the only publish workflow", () => {
  assert.ok(!existsSync(join(WORKFLOWS, "publish-signed.yml")));
});

test("the flavor publisher scans with its own copy of the gate, not the built commit's", () => {
  // A stable build re-cuts a commit that may predate the sensitive-content
  // gate (added 23 Oct 2026), and the gate's rules must be today's anyway.
  const flavorPublish = readFileSync(join(WORKFLOWS, "publish-skill-flavor.yml"), "utf8");
  // Fixed indentation on purpose: `\s` would span lines and backtrack for ages.
  const gateCheckout = flavorPublish.match(
    /^ {6}- uses: actions\/checkout@v4\n {8}with:\n(?: {10}[^\n]*\n)*? {10}path: \.publisher\n/m,
  );
  assert.ok(gateCheckout, "no second checkout of the publisher's own ref into .publisher");
  assert.doesNotMatch(gateCheckout[0], /^\s*ref:/m, "the gate checkout takes the triggering ref, never inputs.commit");
  assert.match(
    flavorPublish,
    /^\s*run: python3 \.publisher\/scripts\/check-sensitive-content\.py "\$TARBALL"\s*$/m,
  );
  assert.doesNotMatch(flavorPublish, /python3 scripts\/check-sensitive-content\.py/);
});
