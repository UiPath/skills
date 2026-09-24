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
// (`uip codedapp` — neither has any host interception). Every one of those
// skills is written as a build pipeline around commands that fail in that
// host, so each studioweb flavor must say which tool is missing, and must
// carry the same note at the top of the references whose steps are imperative.
//
// The scopes deliberately differ. Rpa is read-only: with no `validate` and no
// `build`, nothing can check a workflow the agent writes, and one the designer
// cannot load leaves the project unable to open (UiPath/Autopilot#6371).
// Functions and coded apps have no such failure mode — their files are ordinary
// source — so those two flavors state the missing CLI and nothing more.
const READ_ONLY_HEADING = "## Studio Web Scope: Read and Analyze Only";
const COMMAND_SCOPE_HEADING = "## Studio Web Command Scope";

/**
 * Per skill: the heading its scope opens with, the sentence naming the
 * unavailable tool, canonical authoring instructions that must NOT survive
 * into the studioweb build, and the references carrying the host-scope note.
 */
const HOST_SCOPED_SKILLS = [
  {
    skill: "uipath-rpa",
    heading: READ_ONLY_HEADING,
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
    heading: COMMAND_SCOPE_HEADING,
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
    heading: COMMAND_SCOPE_HEADING,
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
  const output = mkdtempSync(join(tmpdir(), "studioweb-hostscope-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createCompositionPlan(REPO_ROOT, STUDIOWEB_ROOT), output);
  return output;
}

function buildDefault(t) {
  const output = mkdtempSync(join(tmpdir(), "default-hostscope-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createDefaultPlan(REPO_ROOT), output);
  return output;
}

for (const entry of HOST_SCOPED_SKILLS) {
  test(`the built studioweb ${entry.skill} skill states which CLI tool is missing`, (t) => {
    const output = buildStudioweb(t);
    const skillPath = join(entry.skill, "SKILL.md");
    const skill = readFileSync(join(output, skillPath), "utf8");

    assert.ok(skill.includes(entry.heading), `${skillPath} must open with ${entry.heading}`);
    assert.ok(skill.includes(entry.unavailable), `${skillPath} must state which CLI tool is unavailable`);
    assert.ok(
      skill.indexOf(entry.heading) < skill.indexOf("## When to Use This Skill"),
      `${skillPath} must place the scope before the When to Use section so the agent reads it first`,
    );
    for (const forbidden of entry.forbidden) {
      assert.ok(!skill.includes(forbidden), `${skillPath} must not keep the authoring instruction ${forbidden}`);
    }
    assert.ok(!skill.includes("skill-flavor:"), `${skillPath} must be marker-free`);

    for (const reference of entry.references) {
      const path = join(entry.skill, "references", reference);
      const text = readFileSync(join(output, path), "utf8");
      assert.ok(text.includes(entry.referenceNote), `${path} must open with the Studio Web note`);
      assert.ok(!text.includes("skill-flavor:"), `${path} must be marker-free`);
    }
  });

  test(`the default ${entry.skill} skill keeps its full authoring scope (the guards are not vacuous)`, (t) => {
    const output = buildDefault(t);
    const skillPath = join(entry.skill, "SKILL.md");
    const skill = readFileSync(join(output, skillPath), "utf8");

    assert.ok(!skill.includes(entry.heading));
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

// Only Rpa is read-only. A missing CLI is not on its own a reason to stop the
// agent editing, so the functions and coded-app flavors must not drift into
// forbidding edits the way the RPA one does.
test("the studioweb functions and coded-app flavors do not forbid editing", (t) => {
  const output = buildStudioweb(t);

  for (const skillName of ["uipath-functions", "uipath-coded-apps"]) {
    const skill = readFileSync(join(output, skillName, "SKILL.md"), "utf8");
    assert.ok(!skill.includes(READ_ONLY_HEADING), `${skillName} must not carry the read-only scope`);
    assert.ok(
      !/Do NOT create, write, edit/.test(skill),
      `${skillName} must not forbid editing — only Rpa is read-only in Studio Web`,
    );
    assert.ok(
      skill.includes("Read and edit"),
      `${skillName} must say editing stays available`,
    );
  }
});

// The Studio Web shell registers `node` / `js-exec` on QuickJS (Autopilot
// `shell/shellService.ts`), so the flavors must name what is really missing —
// npm and a full Node.js runtime — rather than deny that `node` exists.
test("the studioweb functions and coded-app flavors do not deny the QuickJS node command", (t) => {
  const output = buildStudioweb(t);

  for (const skillName of ["uipath-functions", "uipath-coded-apps"]) {
    const skillDir = join(output, skillName);
    const entry = HOST_SCOPED_SKILLS.find((candidate) => candidate.skill === skillName);
    const paths = ["SKILL.md", ...entry.references.map((reference) => join("references", reference))];
    for (const path of paths) {
      const text = readFileSync(join(skillDir, path), "utf8");
      assert.ok(!/no local (Python, )?Node/.test(text), `${skillName}/${path} must not claim there is no Node`);
    }
    const skill = readFileSync(join(skillDir, "SKILL.md"), "utf8");
    assert.ok(skill.includes("QuickJS sandbox"), `${skillName} must say the shell's node is a QuickJS sandbox`);
  }
});
