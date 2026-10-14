import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  checkActor,
  parseMaintainers,
  resolveOwners,
  SKILL_RE,
  toRegex,
} from "../../.github/workflows/scripts/codeowners-check.mjs";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, ".github", "workflows", "scripts", "codeowners-check.mjs");
const CODEOWNERS = readFileSync(join(REPO_ROOT, "CODEOWNERS"), "utf8");

const noTeams = async () => {
  throw new Error("no team lookup expected");
};
const run = (owners, actor, { maintainers = [], membership = noTeams, matched = true } = {}) =>
  checkActor({ skill: "uipath-x", owners, matched, actor, maintainers, membership });

// ---- pattern matching: GitHub's CODEOWNERS rules, not gitignore's ----

test("a literal directory pattern covers everything under it", () => {
  assert.ok(toRegex("/skills/uipath-rpa/").test("skills/uipath-rpa/SKILL.md"));
  assert.ok(toRegex("/skills/uipath-rpa").test("skills/uipath-rpa/references/a.md"));
  assert.ok(!toRegex("/skills/uipath-rpa/").test("skills/uipath-rpa-legacy/SKILL.md"));
});

test("a glob in the last segment matches direct children only (docs/*)", () => {
  const re = toRegex("/skills/*");
  assert.ok(re.test("skills/README.md"));
  assert.ok(!re.test("skills/uipath-rpa/SKILL.md"), "/skills/* must not own every skill");
});

test("/**/ spans zero or more directories", () => {
  const re = toRegex("a/**/b");
  assert.ok(re.test("a/b"));
  assert.ok(re.test("a/x/y/b"));
  assert.ok(re.test("a/x/b/file.md"));
});

test("a pattern without a leading or inner slash matches at any depth", () => {
  assert.ok(toRegex("*.md").test("skills/uipath-rpa/SKILL.md"));
  assert.ok(toRegex("SKILL.md").test("skills/uipath-rpa/SKILL.md"));
});

// ---- resolving owners ----

test("the last matching rule wins over the global *", () => {
  const text = "* @everyone\n/skills/uipath-rpa/ @rpa-owner # inline comment\n";
  assert.deepEqual(resolveOwners(text, "skills/uipath-rpa/SKILL.md"), { matched: true, owners: ["@rpa-owner"] });
  assert.deepEqual(resolveOwners(text, "skills/other/SKILL.md"), { matched: true, owners: ["@everyone"] });
});

test("a pattern-only line leaves the path explicitly unowned", async () => {
  const text = "* @everyone\n/skills/uipath-x/\n";
  const r = resolveOwners(text, "skills/uipath-x/SKILL.md");
  assert.deepEqual(r, { matched: true, owners: [] });
  const { code, lines } = await run(r.owners, "everyone");
  assert.equal(code, 1);
  assert.match(lines[0].text, /explicitly unowned/);
});

test("a path no rule covers is refused with its own message", async () => {
  const { code, lines } = await run([], "someone", { matched: false });
  assert.equal(code, 1);
  assert.match(lines[0].text, /No CODEOWNERS rule covers/);
});

// ---- who may run it ----

test("a listed user matches case-insensitively", async () => {
  assert.equal((await run(["@Some-Owner"], "some-owner")).code, 0);
});

test("ALSO_ALLOWED admits a maintainer for any skill, with or without @", async () => {
  assert.deepEqual(parseMaintainers("@CarlesUIPath, other  third"), ["CarlesUIPath", "other", "third"]);
  assert.equal((await run(["@owner"], "carlesuipath", { maintainers: parseMaintainers("@CarlesUIPath") })).code, 0);
});

test("a team owner is admitted only on 200 + active", async () => {
  const membership = async (org, slug, actor) => ({ status: 200, state: actor === "member" ? "active" : "pending" });
  assert.equal((await run(["@UiPath/SomeTeam"], "member", { membership })).code, 0);
  assert.equal((await run(["@UiPath/SomeTeam"], "invitee", { membership })).code, 1);
});

for (const status of [403, 404, 429, 500]) {
  test(`a team lookup answering ${status} fails closed and says whom to ask`, async () => {
    const { code, lines } = await run(["@owner", "@UiPath/team"], "stranger", {
      membership: async () => ({ status, state: null }),
    });
    assert.equal(code, 1);
    assert.ok(lines.every((l) => l.level === "error"));
    assert.match(lines.at(-1).text, /ask @owner/);
  });
}

test("a network error on one team is recorded, not thrown", async () => {
  const { code, lines } = await run(["@UiPath/team"], "stranger", {
    membership: async () => {
      throw new Error("fetch failed");
    },
  });
  assert.equal(code, 1);
  assert.match(lines.at(-1).text, /network error: fetch failed/);
});

// ---- the CLI ----

test("importing the module does not run the CLI", async () => {
  // reaching this file at all proves it: the import above would have exited the worker
  assert.equal(typeof checkActor, "function");
});

for (const bad of ["BAD", "../x", "", "uipath x", "-leading"]) {
  test(`skill name ${JSON.stringify(bad)} exits 2`, () => {
    const r = spawnSync(process.execPath, [SCRIPT, join(REPO_ROOT, "CODEOWNERS"), bad, "someone"], { encoding: "utf8" });
    assert.equal(r.status, 2, r.stdout + r.stderr);
    assert.match(r.stdout, /^::error::usage/m);
  });
}

test("a refusal is printed as a workflow error annotation", () => {
  const r = spawnSync(process.execPath, [SCRIPT, join(REPO_ROOT, "CODEOWNERS"), "uipath-rpa", "not-a-real-owner-xyz"], {
    encoding: "utf8",
    env: { ...process.env, ALSO_ALLOWED: "", GH_TOKEN: "" },
  });
  assert.equal(r.status, 1, r.stdout + r.stderr);
  assert.match(r.stdout, /^::error::@not-a-real-owner-xyz is not a CODEOWNER of skills\/uipath-rpa\//m);
});

// ---- the real CODEOWNERS stays in the subset toRegex is known to match like GitHub ----

const rules = CODEOWNERS.split("\n")
  .map((raw) => raw.replace(/\s+#.*$/, "").trim())
  .filter((line) => line && !line.startsWith("#"))
  .map((line) => line.split(/\s+/));

test("every CODEOWNERS pattern is the global * or a literal path", () => {
  for (const [pattern] of rules) {
    if (pattern === "*") continue;
    assert.doesNotMatch(pattern, /[*?\\]/, `${pattern}: globs are not covered by tests/scripts/codeowners-check.test.mjs`);
  }
});

test("every CODEOWNERS rule lists at least one owner", () => {
  for (const [pattern, ...owners] of rules) assert.ok(owners.length > 0, `${pattern} has no owners`);
});

test("the skill-name format is the one the workflow validates", () => {
  const yml = readFileSync(join(REPO_ROOT, ".github", "workflows", "optimize-skill.yml"), "utf8");
  assert.ok(yml.includes(`[[ "$SKILL" =~ ${SKILL_RE.source} ]]`), "optimize-skill.yml validates a different skill format");
});
