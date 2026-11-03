import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");
const SCRIPT = join(REPO_ROOT, "scripts", "npm-package-lifecycle.mjs");
const PRELOAD = pathToFileURL(join(HERE, "support", "redirect-preload.mjs")).href;

/** Runs the script as if the repository root were a fixture directory. */
function run(fixture, { args, lifecycleEvent }) {
  const env = { ...process.env, REDIRECT_FS_FROM: REPO_ROOT, REDIRECT_FS_TO: fixture };
  delete env.npm_lifecycle_event;
  if (lifecycleEvent) env.npm_lifecycle_event = lifecycleEvent;
  return spawnSync(process.execPath, ["--import", PRELOAD, SCRIPT, ...args], { encoding: "utf8", env });
}

function withFixture(body) {
  const fixture = mkdtempSync(join(tmpdir(), "npl-"));
  try {
    return body(fixture);
  } finally {
    rmSync(fixture, { recursive: true, force: true });
  }
}

function addComposerStub(fixture) {
  mkdirSync(join(fixture, "scripts"), { recursive: true });
  writeFileSync(join(fixture, "scripts", "compose-skill-flavor.mjs"), "");
}

test("an unknown lifecycle action is rejected with the offending value", () => {
  withFixture((fixture) => {
    const result = run(fixture, { args: ["publish"] });
    assert.equal(result.status, 1);
    assert.equal(result.stderr, 'ERROR: expected lifecycle action prepare, restore, or recover; got "publish"\n');
  });
});

test("with no argument and no npm lifecycle event the action is undefined and rejected", () => {
  withFixture((fixture) => {
    const result = run(fixture, { args: [] });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /expected lifecycle action .*; got undefined/);
  });
});

test("an installed package without the composer is a silent no-op", () => {
  withFixture((fixture) => {
    const result = run(fixture, { args: ["prepare"] });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout + result.stderr, "");
  });
});

test("the action may come from npm_lifecycle_event", () => {
  withFixture((fixture) => {
    const result = run(fixture, { args: [], lifecycleEvent: "restore" });
    assert.equal(result.status, 0, result.stderr);
  });
});

for (const indicator of [".git", "skill-flavors", join("build", ".root-pack-transaction")]) {
  test(`a source checkout (${indicator}) whose composer is missing is an error`, () => {
    withFixture((fixture) => {
      mkdirSync(join(fixture, indicator), { recursive: true });
      const result = run(fixture, { args: ["prepare"] });
      assert.equal(result.status, 1);
      assert.match(result.stderr, /^ERROR: skill package source was detected, but the flavor composer is missing: .*compose-skill-flavor\.mjs\n$/);
    });
  });
}

test("restore with the composer present and no transaction reports success without changing the tree", () => {
  withFixture((fixture) => {
    addComposerStub(fixture);
    const result = run(fixture, { args: ["restore"] });
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(readdirSync(fixture), ["scripts"]);
  });
});

test("recover takes the same path as restore", () => {
  withFixture((fixture) => {
    addComposerStub(fixture);
    const result = run(fixture, { args: ["recover"] });
    assert.equal(result.status, 0, result.stderr);
  });
});

test("prepare delegates to the composer, whose failure surfaces as ERROR with exit 1", () => {
  withFixture((fixture) => {
    addComposerStub(fixture);
    const result = run(fixture, { args: ["prepare"] });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /^ERROR: canonical skills root is not a real directory: .*skills\n$/);
    assert.ok(!existsSync(join(fixture, "build", ".root-pack-transaction")));
  });
});
