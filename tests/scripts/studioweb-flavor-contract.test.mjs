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

// Studio Web creates coded apps through the `CreateProjects` host tool
// (Autopilot `services/projectCreation.ts`), and nothing compiles one before its
// first `tsc -b`, so the flavor routes creation to that tool and ships the
// create-vite base files, Vite client types included (TS2882 on `import './index.css'`).
const CODED_APP_CREATION_DENIAL =
  /cannot create an AppV2 project|cannot create function or coded-app projects|coded-app projects cannot be created/;
const CREATE_VITE_COMMAND = "npx --yes create-vite";
const SCAFFOLD_REFERENCES = ["create-web-app.md", "create-action-app.md"];
const SOLUTION_CODEDAPP_INIT_RULE = "`uip codedapp init` is the solution-side scaffolding entry point";

test("the built studioweb flavor creates coded apps with CreateProjects and writes buildable base files", (t) => {
  const output = buildStudioweb(t);
  const codedApps = join(output, "uipath-coded-apps");

  const skill = readFileSync(join(codedApps, "SKILL.md"), "utf8");
  assert.ok(skill.includes("`CreateProjects` host tool"), "uipath-coded-apps must create coded apps with CreateProjects");
  assert.ok(skill.includes("`projectSubType`"), "uipath-coded-apps must name the projectSubType field");
  assert.ok(
    skill.includes("Critical Rules 3 and 20") && skill.includes("Critical Rule 19:"),
    "uipath-coded-apps must replace the CLI-host build, scaffold and installed-types rules",
  );

  const solution = readFileSync(join(output, "uipath-solution", "SKILL.md"), "utf8");
  assert.ok(!solution.includes(SOLUTION_CODEDAPP_INIT_RULE), "uipath-solution must not send coded apps to `uip codedapp init`");

  const template = readFileSync(join(codedApps, "assets", "templates", "web-app-template.md"), "utf8");
  assert.ok(template.includes('"types": ["vite/client"]'), "the base files must declare the Vite client types");

  for (const reference of SCAFFOLD_REFERENCES) {
    const text = readFileSync(join(codedApps, "references", reference), "utf8");
    assert.ok(!text.includes(CREATE_VITE_COMMAND), `${reference} must not tell the agent to run create-vite`);
  }

  const denials = markdownFiles(output)
    .filter((file) => CODED_APP_CREATION_DENIAL.test(readFileSync(file, "utf8")))
    .map((file) => relative(output, file));
  assert.deepEqual(denials, [], "no studioweb skill may say coded apps cannot be created in Studio Web");
});

test("the default uipath-coded-apps skill keeps create-vite scaffolding (the guard is not vacuous)", (t) => {
  const output = buildDefault(t);
  const codedApps = join(output, "uipath-coded-apps");

  const template = readFileSync(join(codedApps, "assets", "templates", "web-app-template.md"), "utf8");
  assert.ok(!template.includes("## Studio Web base files"));
  const solution = readFileSync(join(output, "uipath-solution", "SKILL.md"), "utf8");
  assert.ok(solution.includes(SOLUTION_CODEDAPP_INIT_RULE), "the default uipath-solution must keep its `uip codedapp init` rule");
  for (const reference of SCAFFOLD_REFERENCES) {
    const text = readFileSync(join(codedApps, "references", reference), "utf8");
    assert.ok(text.includes(CREATE_VITE_COMMAND), `the default ${reference} must still run create-vite`);
  }
});

// The Studio Web panel has plan mode but no task tools. `EnterPlanMode` is
// called before research (the host names the plan files and attaches its
// authoring contract), `ExitPlanMode` puts the plan on the review card, and the
// host derives the task list from the approved plan. A planner that tells the
// agent to create tasks there, or to write a markdown plan, starts building with
// no approval. Frontmatter is excluded: marker blocks cannot sit inside YAML, so
// `description` and `allowed-tools` still carry the canonical text.
const TASK_TOOLS = /\b(TaskCreate|TaskUpdate|TaskList|addBlockedBy)\b/;
const RETIRED_PLAN_TOOLS = /\b(EnterPlan|ExitPlan)\b/;

function plannerBodyLinesNaming(root, pattern) {
  const plannerRoot = join(root, "uipath-planner");
  const hits = [];
  for (const file of markdownFiles(plannerRoot)) {
    let text = readFileSync(file, "utf8");
    if (file.endsWith("SKILL.md")) text = text.replace(/^---\n[\s\S]*?\n---\n/, "");
    text.split("\n").forEach((line, index) => {
      if (pattern.test(line)) hits.push(`${relative(plannerRoot, file)}:${index + 1}`);
    });
  }
  return hits;
}

test("the built studioweb uipath-planner uses plan mode and no task tools", (t) => {
  const output = buildStudioweb(t);

  assert.deepEqual(plannerBodyLinesNaming(output, TASK_TOOLS), []);
  assert.deepEqual(plannerBodyLinesNaming(output, RETIRED_PLAN_TOOLS), []);
  const laneB = readFileSync(join(output, "uipath-planner", "references", "non-pdd-lane-guide.md"), "utf8");
  assert.ok(
    laneB.includes("Call `EnterPlanMode` as soon as the user picks this option"),
    "explore-first must enter plan mode before discovery",
  );
  assert.ok(
    laneB.includes("call `ExitPlanMode` with outcome `complete`"),
    "explore-first must present the plan with ExitPlanMode",
  );
  const laneA = readFileSync(join(output, "uipath-planner", "references", "pdd-driven-lane-guide.md"), "utf8");
  assert.ok(laneA.includes("1. Call `EnterPlanMode`."), "Lane A interactive review must enter plan mode");
});

test("the default uipath-planner keeps its task tools (the guard is not vacuous)", (t) => {
  const output = buildDefault(t);

  assert.ok(plannerBodyLinesNaming(output, TASK_TOOLS).length > 0);
});

// Studio Web intercepts `uip maestro <flow|case|bpmn> debug|pack`, the form the
// Node CLI ships, and its debug takes a project name and prints plain text. A
// two-token spelling, a path positional, or a JSON-parsing debug example sends
// the agent back to the drift these flavors had (skills#3008, #4100, #4209).
const MAESTRO_SKILLS = ["uipath-maestro-flow", "uipath-maestro-case", "uipath-maestro-bpmn", "uipath-agents"];
const TWO_TOKEN_VERB = /(^|[^a-z-])uip (flow|case|bpmn) (debug|pack)\b/;
const JSON_DEBUG = /uip maestro (flow|case|bpmn) debug\b.*--output json/;
const PATH_DEBUG = /uip maestro (flow|case|bpmn) debug +("?\.|"?\/|"?<[\w-]*(dir|path)>)/;

function maestroLinesMatching(root, pattern) {
  const hits = [];
  for (const skill of MAESTRO_SKILLS) {
    for (const file of markdownFiles(join(root, skill))) {
      readFileSync(file, "utf8").replace(/\\\n\s*/g, " ").split("\n").forEach((line, index) => {
        if (pattern.test(line)) hits.push(`${relative(root, file)}:${index + 1}`);
      });
    }
  }
  return hits;
}

test("the built studioweb maestro skills debug with the three-token verb and no JSON output", (t) => {
  const output = buildStudioweb(t);

  assert.deepEqual(maestroLinesMatching(output, TWO_TOKEN_VERB), []);
  assert.deepEqual(maestroLinesMatching(output, JSON_DEBUG), []);
  assert.deepEqual(maestroLinesMatching(output, PATH_DEBUG), []);
});

test("the default maestro skills keep JSON debug output (the guard is not vacuous)", (t) => {
  const output = buildDefault(t);

  assert.ok(maestroLinesMatching(output, JSON_DEBUG).length > 0);
  assert.ok(maestroLinesMatching(output, PATH_DEBUG).length > 0);
});

test("the studioweb Flow skill is the builder-SDK skill", (t) => {
  const skill = readFileSync(join(buildStudioweb(t), "uipath-maestro-flow", "SKILL.md"), "utf8");

  assert.ok(skill.includes("@uipath/maestro-builder-sdk"));
});

// Studio Web runs the Flow builder SDK inside the page: no npm, no Node, no
// local connector-library cache, no pipeline helper, no `flow-sdk` bin, no
// local `.uipx` to refresh, no project-path debug, no login step, and a
// `flow debug` that ignores `--output` and `--output-filter`.
// Guidance that tells the agent to run any of these fails there, so the
// Studio Web Flow skill must never contain them. Each pattern matches the
// instruction form only, not the flavor's own "not available" text.
const FLOW_TERMINAL_ONLY = [
  "npm install",
  "FLOW_SDK_LIBRARY",
  "registry path --library",
  "pipeline.mjs",
  "flow-sdk flow merge",
  "/tmp/flow-sdk",
  "from './connectors/",
  "resources refresh --solution-folder",
  "uip maestro flow debug <project-dir>",
  ["flow debug --output", /flow debug(?![-\w])[^\n]*--output/],
  ["uip login", /uip login(?!` \| Not available)/],
].map((entry) => (Array.isArray(entry) ? entry : [entry, entry]));

function flowLinesNaming(root) {
  const flowRoot = join(root, "uipath-maestro-flow");
  return markdownFiles(flowRoot).flatMap((file) =>
    readFileSync(file, "utf8")
      .split("\n")
      .flatMap((line, index) =>
        FLOW_TERMINAL_ONLY.filter(([, pattern]) =>
          typeof pattern === "string" ? line.includes(pattern) : pattern.test(line),
        ).map(([label]) => `${relative(flowRoot, file)}:${index + 1}: ${label}`),
      ),
  );
}

test("the studioweb Flow skill names no terminal-only command", (t) => {
  assert.deepEqual(flowLinesNaming(buildStudioweb(t)), []);
});

test("the default uipath-maestro-flow skill keeps its terminal commands (the guard is not vacuous)", (t) => {
  const hits = flowLinesNaming(buildDefault(t)).map((hit) => hit.split(": ").pop());
  assert.deepEqual(
    [...new Set(hits)].sort(),
    FLOW_TERMINAL_ONLY.map(([label]) => label)
      .filter((label) => label !== "/tmp/flow-sdk")
      .sort(),
  );
});

// The siblings that author Flow nodes take the canonical builder-SDK text, so
// they must name no classic `.flow` JSON authoring instruction.
const FLOW_SIBLINGS = ["uipath-agents", "uipath-human-in-the-loop", "uipath-platform"];
const CLASSIC_FLOW_INSTRUCTIONS = [
  "uip maestro flow node add",
  "uip agent refresh --inline-in-flow",
  "uip maestro flow debug <",
  "Write node JSON directly",
  "directly into the `.flow` file as JSON",
  "direct `.flow` authoring",
  "Hand-written `.flow` JSON",
];

function siblingLinesNaming(root) {
  return FLOW_SIBLINGS.flatMap((skill) =>
    markdownFiles(join(root, skill)).flatMap((file) =>
      readFileSync(file, "utf8")
        .split("\n")
        .flatMap((line, index) =>
          CLASSIC_FLOW_INSTRUCTIONS.filter((needle) => line.includes(needle)).map(
            (needle) => `${relative(root, file)}:${index + 1}: ${needle}`,
          ),
        ),
    ),
  );
}

test("the studioweb Flow siblings name no classic Flow instruction", (t) => {
  assert.deepEqual(siblingLinesNaming(buildStudioweb(t)), []);
});
