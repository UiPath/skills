import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";

import { activateSkillFlavor, main } from "../../scripts/activate-skill-flavor.mjs";

const CANONICAL =
  "---\nname: uipath-example\ndescription: \"uipath-example test skill\"\n---\n\n# uipath-example\n\n" +
  "<!--skill-flavor:host:start-->\nCanonical guidance.\n<!--skill-flavor:host:end-->\n";

function write(file, text) {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, text);
}

function fixtureRepo(t) {
  const repo = mkdtempSync(join(tmpdir(), "activate-skill-flavor-"));
  t.after(() => rmSync(repo, { recursive: true, force: true }));
  write(join(repo, "skills", "uipath-example", "SKILL.md"), CANONICAL);
  write(
    join(repo, "skill-flavors", "as-host", "uipath-example", "SKILL.md"),
    "<!--skill-flavor:host:start-->\nAS guidance.\n<!--skill-flavor:host:end-->\n",
  );
  return repo;
}

const skillText = (repo) => readFileSync(join(repo, "skills", "uipath-example", "SKILL.md"), "utf8");

test("activation swaps skills/ for the flavor's marker-free built tree", (t) => {
  const repo = fixtureRepo(t);
  assert.deepEqual(activateSkillFlavor(repo, "as-host"), { skillCount: 1, fileCount: 1 });
  assert.match(skillText(repo), /AS guidance\./);
  assert.doesNotMatch(skillText(repo), /skill-flavor:|Canonical guidance/);
  assert.equal(
    readFileSync(join(repo, "build", "skills", ".canonical", "uipath-example", "SKILL.md"), "utf8"),
    CANONICAL,
  );
});

test("default leaves the canonical tree untouched and builds nothing", (t) => {
  const repo = fixtureRepo(t);
  assert.equal(activateSkillFlavor(repo, "default"), null);
  assert.equal(skillText(repo), CANONICAL);
  assert.ok(!existsSync(join(repo, "build")));
});

test("an unknown flavor fails before anything is built or moved", (t) => {
  const repo = fixtureRepo(t);
  assert.throws(() => activateSkillFlavor(repo, "missing-host"), /not a skill flavor under skill-flavors\//);
  assert.equal(skillText(repo), CANONICAL);
  assert.ok(!existsSync(join(repo, "build")));
});

test("the CLI refuses to replace skills/ outside CI", (t) => {
  const repo = fixtureRepo(t);
  assert.equal(main(["as-host"], { env: {}, repoRoot: repo }), 1);
  assert.equal(skillText(repo), CANONICAL);
  assert.equal(main([], { env: { CI: "true" }, repoRoot: repo }), 1);
  assert.equal(main(["as-host"], { env: { CI: "true" }, repoRoot: repo }), 0);
  assert.match(skillText(repo), /AS guidance\./);
});
