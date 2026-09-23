import assert from "node:assert/strict";
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  createCompositionPlan,
  createDefaultPlan,
  materializeComposition,
} from "../../scripts/compose-skill-flavor.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const STUDIOWEB_ROOT = join(REPO_ROOT, "skill-flavors", "studioweb");

// Studio Web works on one open solution, already scaffolded as the workspace
// root, and its host refuses `uip solution init`. Guidance that tells the agent
// to run it there sends every build down a dead end (coder_eval studio-web
// nightly 13250238: 98 tasks). The studioweb flavor must therefore never
// contain the command; every canonical mention sits in a marker block with a
// sparse studioweb replacement.
const FORBIDDEN = "uip solution init";

function markdownFiles(root) {
  const out = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (entry.endsWith(".md")) out.push(full);
    }
  };
  walk(root);
  return out;
}

function filesMentioning(root, needle) {
  return markdownFiles(root)
    .filter((file) => readFileSync(file, "utf8").includes(needle))
    .map((file) => relative(root, file))
    .sort();
}

test("the built studioweb flavor never tells the agent to run `uip solution init`", (t) => {
  const output = mkdtempSync(join(tmpdir(), "studioweb-flavor-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createCompositionPlan(REPO_ROOT, STUDIOWEB_ROOT), output);

  assert.deepEqual(
    filesMentioning(output, FORBIDDEN),
    [],
    `studioweb flavor still mentions \`${FORBIDDEN}\` — wrap the passage in a marker block and add a sparse override under skill-flavors/studioweb/`,
  );
});

test("the default flavor keeps `uip solution init` (the guard is not vacuous)", (t) => {
  const output = mkdtempSync(join(tmpdir(), "default-flavor-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createDefaultPlan(REPO_ROOT), output);

  assert.ok(filesMentioning(output, FORBIDDEN).length > 0);
});

// Three Studio Web project types have a bundled skill whose CLI family the
// browser bundle does not ship: Rpa (`uip rpa` — only the host-intercepted
// `init` and `run` work), Function (`uip function`) and AppV2
// (`uip codedapp` — neither has any host interception). Their canonical skills
// are written as build pipelines around those commands, so the studioweb
// flavor must scope each one to reading and analyzing and must not leave the
// pipeline instructions in place. See UiPath/Autopilot#6371 for the incident
// that motivated the RPA case.
const READ_ONLY_HEADING = "## Studio Web Scope: Read and Analyze Only";

/**
 * Per skill: the sentence naming the unavailable tool, canonical authoring
 * instructions that must NOT survive into the studioweb build, and the
 * references whose imperative steps carry the host-scope note.
 */
const READ_ONLY_SKILLS = [
  {
    skill: "uipath-rpa",
    unavailable: "The `uip rpa` CLI tool is not available in Studio Web.",
    forbidden: ["**ALWAYS use `uip rpa init`**", "**Phase-gated validation.**"],
    references: [
      "environment-setup.md",
      "execution-maps-guide.md",
      "cli-reference.md",
      join("xaml", "xaml-basics-and-rules.md"),
      join("coded", "operations-guide.md"),
    ],
    referenceNote: "> **Studio Web:** the `uip rpa` CLI tool is not available here",
  },
  {
    skill: "uipath-functions",
    unavailable: "The `uip function` CLI tool is not available in Studio Web.",
    forbidden: [],
    references: [
      join("js", "local-dev-guide.md"),
      join("js", "deployment-guide.md"),
      join("python", "workflow-guide.md"),
    ],
    referenceNote: "> **Studio Web:** the `uip function` CLI tool is not available here",
  },
  {
    skill: "uipath-coded-apps",
    unavailable: "The `uip codedapp` CLI tool is not available in Studio Web.",
    forbidden: [],
    references: [
      "commands-reference.md",
      "pack-publish-deploy.md",
      "create-web-app.md",
      "create-action-app.md",
    ],
    referenceNote: "> **Studio Web:** the `uip codedapp` CLI tool is not available here",
  },
];

function buildStudioweb(t) {
  const output = mkdtempSync(join(tmpdir(), "studioweb-readonly-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createCompositionPlan(REPO_ROOT, STUDIOWEB_ROOT), output);
  return output;
}

function buildDefault(t) {
  const output = mkdtempSync(join(tmpdir(), "default-readonly-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createDefaultPlan(REPO_ROOT), output);
  return output;
}

for (const entry of READ_ONLY_SKILLS) {
  test(`the built studioweb ${entry.skill} skill is scoped to reading and analyzing`, (t) => {
    const output = buildStudioweb(t);
    const skillPath = join(entry.skill, "SKILL.md");
    const skill = readFileSync(join(output, skillPath), "utf8");

    assert.ok(skill.includes(READ_ONLY_HEADING), `${skillPath} must open with the read-only scope`);
    assert.ok(skill.includes(entry.unavailable), `${skillPath} must state which CLI tool is unavailable`);
    assert.ok(
      skill.indexOf(READ_ONLY_HEADING) < skill.indexOf("## When to Use This Skill"),
      `${skillPath} must place the scope before the When to Use section so the agent reads it first`,
    );
    for (const forbidden of entry.forbidden) {
      assert.ok(!skill.includes(forbidden), `${skillPath} must not keep the authoring instruction ${forbidden}`);
    }
    assert.ok(!skill.includes("skill-flavor:"), `${skillPath} must be marker-free`);

    for (const reference of entry.references) {
      const path = join(entry.skill, "references", reference);
      const text = readFileSync(join(output, path), "utf8");
      assert.ok(text.includes(entry.referenceNote), `${path} must open with the Studio Web read-only note`);
      assert.ok(!text.includes("skill-flavor:"), `${path} must be marker-free`);
    }
  });

  test(`the default ${entry.skill} skill keeps its full authoring scope (the guards are not vacuous)`, (t) => {
    const output = buildDefault(t);
    const skillPath = join(entry.skill, "SKILL.md");
    const skill = readFileSync(join(output, skillPath), "utf8");

    assert.ok(!skill.includes(READ_ONLY_HEADING));
    assert.ok(!skill.includes(entry.unavailable));
    assert.ok(skill.includes("## When to Use This Skill"));
    for (const forbidden of entry.forbidden) {
      assert.ok(skill.includes(forbidden), `the default ${skillPath} must still carry ${forbidden}`);
    }
    assert.ok(!skill.includes("skill-flavor:"), `${skillPath} must be marker-free`);

    for (const reference of entry.references) {
      const path = join(entry.skill, "references", reference);
      const text = readFileSync(join(output, path), "utf8");
      assert.ok(!text.includes(entry.referenceNote), `${path} must not carry the Studio Web note in the default`);
      assert.ok(!text.includes("skill-flavor:"), `${path} must be marker-free`);
    }
  });
}

// `uip rpa init` and `uip rpa run` are served by the Studio Web host's
// subcommand interceptors (Autopilot `cli/subcommandInterceptors/index.ts`), so
// the flavor must not claim they fail; every other `uip rpa` verb genuinely
// does not exist in the browser bundle.
test("the studioweb uipath-rpa flavor keeps the host-served rpa verbs available", (t) => {
  const output = buildStudioweb(t);
  const skill = readFileSync(join(output, "uipath-rpa", "SKILL.md"), "utf8");

  assert.ok(
    skill.includes("`uip rpa init <ProjectName>` creates the project"),
    "the scope must say the host still serves `uip rpa init`",
  );
  assert.ok(skill.includes("`uip rpa run` runs an existing project"), "the scope must say the host still serves `uip rpa run`");
});
