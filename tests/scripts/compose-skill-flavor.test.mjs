import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  chmodSync,
  copyFileSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, relative, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  FlavorCompositionError,
  ROOT_PACK_TRANSACTION_DIRNAME,
  buildAllSkillTrees,
  composeText,
  containsFlavorMarker,
  createAllVariants,
  createCompositionPlan,
  createDefaultPlan,
  materializeComposition,
  packageName,
  packAllVariants,
  parseMarkerBlocks,
  prepareRootDefaultPackage,
  readTarballEntries,
  restoreRootDefaultPackage,
  stripMarkerBoundaries,
  treeFileBytes,
} from "../../scripts/compose-skill-flavor.mjs";
import { selectSkillPackage } from "../../scripts/select-skill-package.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SCRIPT = join(REPO_ROOT, "scripts", "compose-skill-flavor.mjs");
const LIFECYCLE_DRIVER = join(REPO_ROOT, "scripts", "npm-package-lifecycle.mjs");
const DEFAULT_PUBLISH_WORKFLOW = join(REPO_ROOT, ".github", "workflows", "publish.yml");
const FLAVOR_PUBLISH_WORKFLOW = join(
  REPO_ROOT,
  ".github",
  "workflows",
  "publish-skill-flavor.yml",
);
const SELECT_SKILL_PACKAGE_SCRIPT = join(
  REPO_ROOT,
  "scripts",
  "select-skill-package.mjs",
);
const CUSTOM_PACKAGE_PUBLISH_CONFIG = {
  registry: "https://npm.pkg.github.com/",
  "@uipath:registry": "https://npm.pkg.github.com/",
};

function fixtureRepo(t) {
  const repo = mkdtempSync(join(tmpdir(), "skill-flavor-node-test-"));
  mkdirSync(join(repo, "skills"));
  t.after(() => rmSync(repo, { recursive: true, force: true }));
  return repo;
}

function entrypoint(name, body = "Canonical guidance.\n") {
  return (
    "---\n" +
    `name: ${name}\n` +
    `description: "${name} test skill"\n` +
    "---\n\n" +
    `# ${name}\n\n` +
    body
  );
}

function addSkill(repo, name, body = "Canonical guidance.\n") {
  const skill = join(repo, "skills", name);
  mkdirSync(skill, { recursive: true });
  writeFileSync(join(skill, "SKILL.md"), entrypoint(name, body));
  return skill;
}

function block(name, body, newline = "\n") {
  return (
    `<!--skill-flavor:${name}:start-->${newline}` +
    `${body}${newline}` +
    `<!--skill-flavor:${name}:end-->${newline}`
  );
}

function flavorRoot(repo, name) {
  const root = join(repo, "skill-flavors", name);
  mkdirSync(root, { recursive: true });
  return root;
}

function writeOverride(repo, flavor, relativePath, text) {
  const root = flavorRoot(repo, flavor);
  const target = join(root, ...relativePath.split("/"));
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, text);
  return root;
}

function addPackageManifest(repo, version = "1.2.3", overrides = {}) {
  const manifest = {
    name: "@uipath/skills",
    version,
    description: "Fixture skills package",
    license: "MIT",
    repository: { type: "git", url: "https://github.com/UiPath/skills.git" },
    keywords: ["uipath", "skills"],
    private: false,
    uipathSkillsFlavor: "default",
    files: [
      "skills",
      "assets",
      "hooks",
      "version-manifest.json",
      "README.md",
      "LICENSE",
      "scripts/npm-package-lifecycle.mjs",
    ],
    scripts: {
      prepack: "node scripts/npm-package-lifecycle.mjs prepare",
      postpack: "node scripts/npm-package-lifecycle.mjs restore",
      "skills:recover": "node scripts/npm-package-lifecycle.mjs recover",
    },
    ...overrides,
  };
  writeFileSync(join(repo, "package.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  writeFileSync(join(repo, "README.md"), "# Fixture package\n");
  writeFileSync(join(repo, "LICENSE"), "MIT fixture\n");
  writeFileSync(
    join(repo, "version-manifest.json"),
    `${JSON.stringify({ skillsVersion: version })}\n`,
  );
  mkdirSync(join(repo, "assets"));
  writeFileSync(join(repo, "assets", "shared.txt"), "default-only payload\n");
  mkdirSync(join(repo, "hooks"));
  writeFileSync(join(repo, "hooks", "tool.sh"), "#!/bin/sh\necho fixture\n");
  chmodSync(join(repo, "hooks", "tool.sh"), 0o755);
  mkdirSync(join(repo, "scripts"));
  copyFileSync(SCRIPT, join(repo, "scripts", "compose-skill-flavor.mjs"));
  copyFileSync(
    LIFECYCLE_DRIVER,
    join(repo, "scripts", "npm-package-lifecycle.mjs"),
  );
}

function runCli(repo, ...args) {
  return spawnSync(process.execPath, [SCRIPT, "--repo-root", repo, ...args], {
    encoding: "utf8",
    env: {
      ...process.env,
      npm_config_cache: join(repo, ".npm-cache"),
    },
  });
}

function runCliAsync(repo, ...args) {
  return new Promise((resolvePromise) => {
    const child = spawn(process.execPath, [SCRIPT, "--repo-root", repo, ...args], {
      env: {
        ...process.env,
        npm_config_cache: join(repo, ".npm-cache"),
      },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("close", (status, signal) => {
      resolvePromise({ status, signal, stdout, stderr });
    });
  });
}

function invokeNpm(repo, args, extraEnv = {}) {
  const env = {
    ...process.env,
    npm_config_cache: join(repo, ".npm-cache"),
    ...extraEnv,
  };
  if (process.env.npm_execpath) {
    return spawnSync(process.execPath, [process.env.npm_execpath, ...args], {
      cwd: repo,
      encoding: "utf8",
      env,
    });
  }
  return spawnSync(process.platform === "win32" ? "npm.cmd" : "npm", args, {
    cwd: repo,
    encoding: "utf8",
    env,
  });
}

function runNpm(repo, ...args) {
  return invokeNpm(repo, args);
}

function expectFlavorError(action, pattern) {
  assert.throws(action, (error) => {
    assert.ok(error instanceof FlavorCompositionError);
    assert.match(error.message, pattern);
    return true;
  });
}

function buffersMapEqual(left, right) {
  if (left.size !== right.size) return false;
  for (const [name, data] of left) {
    if (!right.get(name)?.equals(data)) return false;
  }
  return true;
}

function sha512File(file) {
  return createHash("sha512").update(readFileSync(file)).digest("hex");
}

function assertMarkerFreeSkillTarball(tarball, expectedName, expectedFlavor) {
  const entries = readTarballEntries(tarball);
  const manifestBytes = entries.get("package/package.json");
  assert.ok(manifestBytes, `${tarball} must contain package/package.json`);
  const manifest = JSON.parse(manifestBytes.toString("utf8"));
  assert.equal(manifest.name, expectedName);
  assert.equal(manifest.uipathSkillsFlavor, expectedFlavor);

  let skillFileCount = 0;
  for (const [name, bytes] of entries) {
    if (name.startsWith("package/skills/")) skillFileCount += 1;
    assert.ok(
      !containsFlavorMarker(bytes),
      `${tarball} leaked a flavor marker in ${name}`,
    );
  }
  assert.ok(skillFileCount > 0, `${tarball} must contain packaged skill files`);
}

function workflowJob(workflow, jobName) {
  const escapedName = jobName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = workflow.match(
    new RegExp(`^  ${escapedName}:\\s*\\n([\\s\\S]*?)(?=^  [a-zA-Z0-9_-]+:\\s*\\n|$(?![\\s\\S]))`, "m"),
  );
  assert.ok(match, `workflow must contain the ${jobName} job`);
  return match[0];
}

function withNpmCache(repo, action) {
  const previous = process.env.npm_config_cache;
  process.env.npm_config_cache = join(repo, ".npm-cache");
  try {
    return action();
  } finally {
    if (previous === undefined) delete process.env.npm_config_cache;
    else process.env.npm_config_cache = previous;
  }
}

function runRealNpmPack({ packageDir, npmRoot }, repo) {
  const npmArguments = [
    "pack",
    packageDir,
    "--json",
    "--pack-destination",
    npmRoot,
  ];
  const env = {
    ...process.env,
    npm_config_cache: join(repo, ".npm-cache"),
  };
  if (process.env.npm_execpath) {
    return spawnSync(process.execPath, [process.env.npm_execpath, ...npmArguments], {
      encoding: "utf8",
      env,
    });
  }
  return spawnSync(
    process.platform === "win32" ? "npm.cmd" : "npm",
    npmArguments,
    { encoding: "utf8", env },
  );
}

function extractTarball(t, tarball) {
  const output = mkdtempSync(join(tmpdir(), "skill-flavor-tar-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  const tar =
    process.platform === "win32"
      ? join(process.env.SystemRoot ?? "C:\\Windows", "System32", "tar.exe")
      : "tar";
  const result = spawnSync(tar, ["-xzf", tarball, "-C", output], {
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return join(output, "package");
}

test("a flavor includes the complete catalog and replaces only matching blocks", (t) => {
  const repo = fixtureRepo(t);
  const changedBody =
    "Canonical introduction.\n\n" +
    block("project-creation", "Use the default project workflow.") +
    "\nShared middle.\n\n" +
    block("validation", "Run the default validation workflow.") +
    "\nCanonical ending.\n";
  const changed = addSkill(repo, "uipath-changed", changedBody);
  mkdirSync(join(changed, "references"));
  writeFileSync(join(changed, "references", "guide.md"), "Shared guide.\n");
  writeFileSync(join(changed, "asset.bin"), Buffer.from([0, 1, 2, 3]));
  addSkill(repo, "uipath-pass-through");
  addSkill(repo, "uipath-another");

  const studio = writeOverride(
    repo,
    "studioweb",
    "uipath-changed/SKILL.md",
    block("validation", "Use Studio Web validation.") +
      "\n" +
      block("project-creation", "Use the Studio Web project tool."),
  );
  const canonicalBefore = readFileSync(join(changed, "SKILL.md"));
  const plan = createCompositionPlan(repo, studio);

  assert.deepEqual(plan.skills, [
    "uipath-another",
    "uipath-changed",
    "uipath-pass-through",
  ]);
  assert.equal(plan.replacementCount, 2);
  assert.deepEqual(plan.overriddenFiles, ["uipath-changed/SKILL.md"]);

  const output = join(repo, "complete-flavor");
  materializeComposition(plan, output);
  const composed = readFileSync(join(output, "uipath-changed", "SKILL.md"), "utf8");
  assert.match(composed, /Canonical introduction/);
  assert.match(composed, /Use the Studio Web project tool/);
  assert.match(composed, /Use Studio Web validation/);
  assert.doesNotMatch(composed, /default project workflow|default validation workflow/);
  assert.ok(composed.indexOf("Studio Web project tool") < composed.indexOf("Studio Web validation"));
  assert.ok(!containsFlavorMarker(composed));
  assert.ok(existsSync(join(output, "uipath-another", "SKILL.md")));
  assert.ok(existsSync(join(output, "uipath-pass-through", "SKILL.md")));
  assert.deepEqual(readFileSync(join(output, "uipath-changed", "asset.bin")), Buffer.from([0, 1, 2, 3]));
  assert.deepEqual(readFileSync(join(changed, "SKILL.md")), canonicalBefore);
});

test("empty canonical blocks add flavor guidance without shadowing shared edits", (t) => {
  const repo = fixtureRepo(t);
  const skillName = "uipath-additive";
  const canonicalBody = (sharedRows) =>
    "## Reference Navigation\n\n" +
    `${sharedRows}\n` +
    block("reference-navigation-extra", "") +
    "\nShared ending.\n";
  const skill = addSkill(
    repo,
    skillName,
    canonicalBody("| references/cli-reference.md | Shared CLI reference |"),
  );
  const studio = writeOverride(
    repo,
    "studioweb",
    `${skillName}/SKILL.md`,
    block(
      "reference-navigation-extra",
      "> Studio Web keeps shared references and adds host scope.",
    ),
  );

  const firstOutput = join(repo, "additive-first");
  materializeComposition(createCompositionPlan(repo, studio), firstOutput);
  const firstBuilt = readFileSync(join(firstOutput, skillName, "SKILL.md"), "utf8");
  assert.match(firstBuilt, /Shared CLI reference/);
  assert.match(firstBuilt, /Studio Web keeps shared references/);

  writeFileSync(
    join(skill, "SKILL.md"),
    entrypoint(
      skillName,
      canonicalBody(
        "| references/cli-reference.md | Shared CLI reference |\n" +
          "| references/new-capability.md | Newly shared capability |",
      ),
    ),
  );
  const secondOutput = join(repo, "additive-second");
  materializeComposition(createCompositionPlan(repo, studio), secondOutput);
  const secondBuilt = readFileSync(join(secondOutput, skillName, "SKILL.md"), "utf8");
  assert.match(secondBuilt, /Newly shared capability/);
  assert.match(secondBuilt, /Studio Web keeps shared references/);
  assert.ok(!containsFlavorMarker(secondBuilt));
});

test("Studio Web inherits API Workflow authoring guidance and applies its host command contract", (t) => {
  const canonicalPath = join(REPO_ROOT, "skills", "uipath-api-workflow", "SKILL.md");
  const overridePath = join(
    REPO_ROOT,
    "skill-flavors",
    "studioweb",
    "uipath-api-workflow",
    "SKILL.md",
  );
  const canonical = readFileSync(canonicalPath, "utf8");
  const override = readFileSync(overridePath, "utf8");
  assert.match(
    canonical,
    /description: "UiPath API Workflow assistant — author, run, validate, package, publish, deploy, and troubleshoot JSON workflows/,
  );
  assert.match(
    canonical,
    /Run with `--no-auth --output json` after each addition\. Fix what breaks\. Repeat\./,
  );
  const findings = [];
  const composed = stripMarkerBoundaries(
    composeText(
      canonical,
      parseMarkerBlocks(canonicalPath, canonical, findings),
      parseMarkerBlocks(overridePath, override, findings),
    ),
  );

  assert.deepEqual(findings, []);
  assert.doesNotMatch(canonical, /skill-flavor:reference-navigation:(?:start|end)/);
  assert.match(canonical, /skill-flavor:reference-navigation-extra:start/);
  assert.match(override, /skill-flavor:reference-navigation-extra:start/);
  for (const reference of [
    "references/connector-activity-discovery.md",
    "references/cli-reference.md",
    "references/operating-published-workflows.md",
    "references/troubleshooting.md",
  ]) {
    assert.match(composed, new RegExp(reference.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(
    composed,
    /shared references for JSON authoring, troubleshooting, static validation, `uip api-workflow registry resolve` \/ `stub`, read-only Integration Service discovery, and the host-intercepted active-solution publish bridge/,
  );
  assert.match(
    composed,
    /Authoring HTTP Request \/ Gmail \/ Outlook \/ GitHub \/ Slack \/ etc\. activities via `uip api-workflow registry resolve` \+ `stub`/,
  );
  assert.match(composed, /Apply the Studio Web capability map above and inspect live host schemas/);
  assert.ok(!containsFlavorMarker(composed));

  const studioRoot = join(REPO_ROOT, "skill-flavors", "studioweb");
  const output = mkdtempSync(join(tmpdir(), "api-workflow-studioweb-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createCompositionPlan(REPO_ROOT, studioRoot), output);

  const builtSkillRoot = join(output, "uipath-api-workflow");
  const builtFiles = new Map(
    [
      "SKILL.md",
      "references/cli-reference.md",
      "references/connector-activity-discovery.md",
      "references/expressions-and-context.md",
      "references/operating-published-workflows.md",
      "references/task-types.md",
      "references/troubleshooting.md",
      "references/workflow-file-format.md",
    ].map((relativePath) => [
      relativePath,
      readFileSync(join(builtSkillRoot, relativePath), "utf8"),
    ]),
  );
  const builtContract = [...builtFiles.values()].join("\n");
  // Flavor markers are Markdown comments and cannot safely split YAML frontmatter.
  // The canonical description is preserved and asserted above; audit the composed guidance body here.
  const builtGuidance = [...builtFiles]
    .map(([relativePath, source]) =>
      relativePath === "SKILL.md" ? source.replace(/^---\n[\s\S]*?\n---\n/, "") : source,
    )
    .join("\n");

  for (const [relativePath, source] of builtFiles) {
    assert.ok(!containsFlavorMarker(source), `${relativePath} must be marker-free`);
  }
  assert.match(builtFiles.get("SKILL.md"), /Studio Web Capability Map/);
  assert.match(
    builtFiles.get("SKILL.md"),
    /verify the returned `\/solution\/<projectName>` directory with `LsDirectory`/,
  );
  assert.match(builtContract, /\/solution\/<projectName>\/Workflow\.json/);
  assert.match(builtContract, /uip api-workflow validate Workflow\.json --output json/);
  assert.match(builtContract, /uip api-workflow registry resolve/);
  assert.match(builtContract, /uip api-workflow registry stub/);
  assert.match(builtContract, /uip is connections ping/);
  assert.match(builtContract, /\/skills\/synthetic\/proxy-tools-Api\/SKILL\.md/);
  assert.match(builtContract, /RunProject/);
  assert.match(builtContract, /explicit (?:user )?consent[\s\S]*RunProject/);
  assert.match(builtContract, /actual (?:host )?tool result as execution evidence/);
  assert.match(builtContract, /uip solution publish --help/);
  assert.match(builtContract, /explicit user publish request or approval/);
  assert.match(builtContract, /active Studio Web solution is implicit/);
  assert.match(
    builtContract,
    /uip solution publish \[--description <text>\].*\[--release-notes <text>\].*\[--version <version>\].*\[--location <value>\].*\[--location-name <value>\].*\[--personal-workspace\]/,
  );
  assert.match(builtContract, /request was accepted[\s\S]*Publish history/);
  assert.doesNotMatch(builtContract, /--input-arguments/);
  assert.doesNotMatch(builtContract, /uip is resources run/);
  assert.doesNotMatch(builtContract, /uip api-workflow run/);
  assert.doesNotMatch(builtContract, /^\s*uip solution publish\s+[^\n]*\.zip/m);
  assert.match(builtFiles.get("references/troubleshooting.md"), /jq empty Workflow\.json/);
  assert.doesNotMatch(
    builtContract,
    /uip (?:login|logout|auth|config|api-workflow (?:init|build|pack|run|bindings sync)|solution (?:init|pack|deploy|resources refresh)|is connections edit|or |traces )|\.uipx|bindings_v2\.json|project\.uiproj|entry-points\.json|userProfile\/|No worker implementation available/i,
  );
  assert.doesNotMatch(
    builtGuidance,
    /\brun --no-auth\b|\bruns? locally\b|\bruns? from the CLI\b|\blocal CLI runtime\b|\bresource refresh\b/i,
  );
  assert.doesNotMatch(builtContract, /^\s*node -e /m);
  assert.doesNotMatch(
    builtFiles.get("references/operating-published-workflows.md"),
    /uip or jobs (?:start|list|logs|stop)/,
  );

  const flavorSource = [...treeFileBytes(join(studioRoot, "uipath-api-workflow"))]
    .filter(([relativePath]) => relativePath.endsWith(".md"))
    .map(([, source]) => source.toString("utf8"))
    .join("\n");
  assert.doesNotMatch(
    flavorSource,
    /\b(?:do not|don't|never|forbidden|unsupported|must not|instead of|rather than)\b/i,
  );
  assert.doesNotMatch(
    flavorSource,
    /uip (?:login|logout|auth|config|api-workflow (?:init|build|pack|run|bindings sync)|solution (?:init|pack|deploy|resources refresh)|is connections edit|or |traces )|\.uipx|bindings_v2\.json|project\.uiproj|entry-points\.json|userProfile\/|No worker implementation available/i,
  );

  const defaultCliReference = readFileSync(
    join(REPO_ROOT, "skills", "uipath-api-workflow", "references", "cli-reference.md"),
    "utf8",
  );
  assert.match(defaultCliReference, /^uip api-workflow init <name>/m);
  assert.match(defaultCliReference, /^uip api-workflow run <file>/m);
  assert.match(defaultCliReference, /^uip solution publish <packagePath>/m);
  assert.match(
    readFileSync(
      join(
        REPO_ROOT,
        "skills",
        "uipath-api-workflow",
        "references",
        "expressions-and-context.md",
      ),
      "utf8",
    ),
    /--input-arguments '\{"name":"Alice","count":3\}'/,
  );
});

test("new canonical skills are automatically included in existing flavors", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-first", block("host", "Default host guidance."));
  const studio = writeOverride(
    repo,
    "studioweb",
    "uipath-first/SKILL.md",
    block("host", "Studio Web guidance."),
  );
  assert.deepEqual(createCompositionPlan(repo, studio).skills, ["uipath-first"]);
  addSkill(repo, "uipath-new-skill");
  assert.deepEqual(createCompositionPlan(repo, studio).skills, [
    "uipath-first",
    "uipath-new-skill",
  ]);
});

test("default plan includes every canonical skill and strips CRLF marker boundaries", (t) => {
  const repo = fixtureRepo(t);
  addSkill(
    repo,
    "uipath-marked",
    `Before.\r\n\r\n${block("project-creation", "Canonical body.", "\r\n")}\r\nAfter.\r\n`,
  );
  addSkill(repo, "uipath-plain");
  const plan = createDefaultPlan(repo);
  assert.deepEqual(plan.skills, ["uipath-marked", "uipath-plain"]);
  const output = join(repo, "default");
  materializeComposition(plan, output);
  const text = readFileSync(join(output, "uipath-marked", "SKILL.md"), "utf8");
  assert.match(text, /Canonical body/);
  assert.ok(!containsFlavorMarker(text));
  assert.equal(stripMarkerBoundaries(block("x", "body")), "body\n");
});

test("explicit build commands preserve their legacy output contract", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("project", "Canonical."));
  const studio = writeOverride(
    repo,
    "studioweb",
    "uipath-example/SKILL.md",
    block("project", "Studio Web."),
  );

  const output = join(repo, "paired");
  const build = runCli(repo, "build", studio, output);
  assert.equal(build.status, 0, build.stderr);
  assert.ok(existsSync(join(output, "default", "uipath-example", "SKILL.md")));
  assert.match(
    readFileSync(join(output, "studioweb", "uipath-example", "SKILL.md"), "utf8"),
    /Studio Web/,
  );

  const defaultOutput = join(repo, "first-class-default");
  const defaultBuild = runCli(repo, "build-default", defaultOutput);
  assert.equal(defaultBuild.status, 0, defaultBuild.stderr);
  assert.ok(existsSync(join(defaultOutput, "uipath-example", "SKILL.md")));
});

test("paired build preflights both destinations before writing either", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("project", "Canonical."));
  const studio = writeOverride(
    repo,
    "studioweb",
    "uipath-example/SKILL.md",
    block("project", "Studio Web."),
  );
  const output = join(repo, "paired");
  mkdirSync(join(output, "studioweb"), { recursive: true });
  writeFileSync(join(output, "studioweb", "keep.txt"), "user data\n");

  const result = runCli(repo, "build", studio, output);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must be empty/);
  assert.ok(!existsSync(join(output, "default")));
  assert.equal(readFileSync(join(output, "studioweb", "keep.txt"), "utf8"), "user data\n");
});

test("marker sentinel catches compact and whitespace-malformed forms", () => {
  for (const value of [
    "<!--skill-flavor:x:start-->",
    "<!-- skill-flavor:x:start -->",
    "<!--skill-flavor :x:start-->",
    "<!--skill-flavor\t:x:start-->",
  ]) {
    assert.equal(containsFlavorMarker(value), true, value);
    assert.equal(containsFlavorMarker(Buffer.from(value)), true, value);
  }
  assert.equal(containsFlavorMarker("skill-flavors/studioweb"), false);
});

test("marker parser rejects malformed state and preserves valid canonical order", () => {
  const cases = [
    ["inline <!--skill-flavor:x:start-->\n", /malformed flavor marker/],
    ["<!-- skill-flavor:x:start -->\n", /contain no whitespace/],
    ["<!--skill-flavor :x:start-->\n", /contain no whitespace/],
    ["<!--skill-flavor:x:start--> \n", /contain no whitespace/],
    [
      "    <!--skill-flavor:x:start-->\nbody\n<!--skill-flavor:x:end-->\n",
      /markers must start at column 1/,
    ],
    ["<!--skill-flavor:x:end-->\n", /ends without a start/],
    ["<!--skill-flavor:x:start-->\nbody\n", /has no end marker/],
    [
      "<!--skill-flavor:x:start-->\n<!--skill-flavor:y:end-->\n",
      /does not match/,
    ],
    [
      "<!--skill-flavor:x:start-->\n<!--skill-flavor:y:start-->\n",
      /nested flavor marker/,
    ],
  ];
  for (const [source, expected] of cases) {
    const findings = [];
    parseMarkerBlocks("fixture.md", source, findings);
    assert.match(findings.join("\n"), expected);
  }
});

test("duplicate canonical markers are rejected", (t) => {
  const repo = fixtureRepo(t);
  addSkill(
    repo,
    "uipath-example",
    block("same", "First.") + "\n" + block("same", "Second."),
  );
  expectFlavorError(() => createDefaultPlan(repo), /duplicate flavor block/);
});

test("invalid sparse overrides fail with actionable diagnostics", async (t) => {
  const scenarios = [
    {
      name: "missing-marker",
      relative: "uipath-example/SKILL.md",
      text: block("unknown", "Replacement."),
      expected: /no matching canonical marker/,
    },
    {
      name: "missing-target",
      relative: "uipath-example/references/missing.md",
      text: block("project", "Replacement."),
      expected: /canonical target does not exist/,
    },
    {
      name: "stray-content",
      relative: "uipath-example/SKILL.md",
      text: `Unmarked.\n${block("project", "Replacement.")}`,
      expected: /stray unmarked content/,
    },
    {
      name: "non-markdown",
      relative: "uipath-example/override.txt",
      text: block("project", "Replacement."),
      expected: /only Markdown files/,
    },
    {
      name: "root-file",
      relative: "skills.allowlist",
      text: "uipath-example\n",
      expected: /override path must mirror/,
    },
  ];

  for (const scenario of scenarios) {
    await t.test(scenario.name, (child) => {
      const repo = fixtureRepo(child);
      addSkill(repo, "uipath-example", block("project", "Canonical."));
      const studio = writeOverride(
        repo,
        "studioweb",
        scenario.relative,
        scenario.text,
      );
      expectFlavorError(() => createCompositionPlan(repo, studio), scenario.expected);
    });
  }
});

test("invalid UTF-8 canonical and override Markdown are rejected", async (t) => {
  await t.test("canonical", (child) => {
    const repo = fixtureRepo(child);
    const skill = addSkill(repo, "uipath-example");
    writeFileSync(join(skill, "SKILL.md"), Buffer.from([0xff, 0xfe]));
    expectFlavorError(() => createDefaultPlan(repo), /must be UTF-8/);
  });
  await t.test("override", (child) => {
    const repo = fixtureRepo(child);
    addSkill(repo, "uipath-example", block("project", "Canonical."));
    const studio = writeOverride(
      repo,
      "studioweb",
      "uipath-example/SKILL.md",
      block("project", "Replacement."),
    );
    writeFileSync(join(studio, "uipath-example", "SKILL.md"), Buffer.from([0xff]));
    expectFlavorError(() => createCompositionPlan(repo, studio), /must be UTF-8/);
  });
});

test("materializer refuses non-empty and symlink output destinations", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example");
  const plan = createDefaultPlan(repo);
  const output = join(repo, "output");
  mkdirSync(output);
  writeFileSync(join(output, "keep.txt"), "user data\n");
  assert.throws(() => materializeComposition(plan, output), /must be empty/);
  assert.equal(readFileSync(join(output, "keep.txt"), "utf8"), "user data\n");

  if (process.platform !== "win32") {
    const outside = join(repo, "outside");
    mkdirSync(outside);
    const linked = join(repo, "linked-output");
    symlinkSync(outside, linked, "dir");
    assert.throws(() => materializeComposition(plan, linked), /symlink/);
  }
});

test("generic discovery is stable and every flavor has the full catalog", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-first", block("host", "Default."));
  addSkill(repo, "uipath-second");
  writeOverride(repo, "zeta-host", "uipath-first/SKILL.md", block("host", "Zeta."));
  writeOverride(repo, "alpha-host", "uipath-first/SKILL.md", block("host", "Alpha."));

  const variants = createAllVariants(repo);
  assert.deepEqual(variants.map(({ name }) => name), [
    "default",
    "alpha-host",
    "zeta-host",
  ]);
  for (const variant of variants) {
    assert.deepEqual(variant.plan.skills, ["uipath-first", "uipath-second"]);
  }
});

test("invalid, reserved, empty, and symlinked flavors are rejected", async (t) => {
  for (const flavor of ["StudioWeb", "studio_web", "default"]) {
    await t.test(flavor, (child) => {
      const repo = fixtureRepo(child);
      addSkill(repo, "uipath-example", block("host", "Default."));
      writeOverride(repo, flavor, "uipath-example/SKILL.md", block("host", "Custom."));
      expectFlavorError(() => createAllVariants(repo), /invalid flavor name|reserved/);
    });
  }

  await t.test("empty", (child) => {
    const repo = fixtureRepo(child);
    addSkill(repo, "uipath-example");
    flavorRoot(repo, "empty-host");
    expectFlavorError(() => createAllVariants(repo), /at least one Markdown override/);
  });

  if (process.platform !== "win32") {
    await t.test("symlink", (child) => {
      const repo = fixtureRepo(child);
      addSkill(repo, "uipath-example");
      const external = join(repo, "external");
      mkdirSync(external);
      mkdirSync(join(repo, "skill-flavors"));
      symlinkSync(external, join(repo, "skill-flavors", "linked-host"), "dir");
      expectFlavorError(() => createAllVariants(repo), /symlink/);
    });
  }
});

test("failed generic rebuild preserves the last successful output", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Default."));
  const studio = writeOverride(
    repo,
    "studioweb",
    "uipath-example/SKILL.md",
    block("host", "Studio Web."),
  );
  buildAllSkillTrees(repo);
  const before = treeFileBytes(join(repo, "build", "skills"));
  writeFileSync(
    join(studio, "uipath-example", "SKILL.md"),
    `stray\n${block("host", "Broken.")}`,
  );
  expectFlavorError(() => buildAllSkillTrees(repo), /stray unmarked content/);
  assert.ok(buffersMapEqual(before, treeFileBytes(join(repo, "build", "skills"))));
  assert.equal(
    readdirSync(join(repo, "build")).filter((name) => name.startsWith(".skill-flavor-")).length,
    0,
  );
});

test("generic build rejects a symlinked generated target without touching it", (t) => {
  if (process.platform === "win32") return t.skip("symlink creation needs privileges");
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example");
  const outside = join(repo, "outside");
  mkdirSync(outside);
  writeFileSync(join(outside, "keep.txt"), "user data\n");
  mkdirSync(join(repo, "build"));
  symlinkSync(outside, join(repo, "build", "skills"), "dir");
  assert.throws(() => buildAllSkillTrees(repo), /cannot replace a symlink/);
  assert.equal(readFileSync(join(outside, "keep.txt"), "utf8"), "user data\n");
});

test("package names derive generically and enforce npm's length limit", () => {
  assert.equal(packageName("@uipath/skills", "default"), "@uipath/skills");
  assert.equal(
    packageName("@uipath/skills", "studioweb"),
    "@uipath/skills-studioweb",
  );
  assert.equal(packageName("skills", "future-host"), "skills-future-host");
  assert.throws(
    () => packageName("@uipath/skills", "a".repeat(200)),
    /derived npm package name is too long/,
  );
});

test("pack builds complete, marker-free default and custom npm packages", (t) => {
  const repo = fixtureRepo(t);
  const changed = addSkill(
    repo,
    "uipath-changed",
    `Before.\n\n${block("project", "Canonical project workflow.")}\nAfter.\n`,
  );
  writeFileSync(join(changed, "asset.bin"), Buffer.from([0, 1, 2, 3]));
  addSkill(repo, "uipath-pass-through");
  writeOverride(
    repo,
    "studioweb",
    "uipath-changed/SKILL.md",
    block("project", "Studio Web project tool."),
  );
  writeOverride(
    repo,
    "future-host",
    "uipath-changed/SKILL.md",
    block("project", "Future host project tool."),
  );
  addPackageManifest(repo, "1.2.3-preview.45", {
    publishConfig: {
      registry: "https://registry.npmjs.org/",
      tag: "latest",
    },
  });

  const packages = withNpmCache(repo, () => packAllVariants(repo));
  assert.deepEqual(packages.map(({ variant }) => variant), [
    "default",
    "future-host",
    "studioweb",
  ]);
  const byVariant = new Map(packages.map((item) => [item.variant, item]));
  assert.equal(byVariant.get("default").packageName, "@uipath/skills");
  assert.equal(
    byVariant.get("future-host").packageName,
    "@uipath/skills-future-host",
  );
  assert.equal(
    byVariant.get("studioweb").packageName,
    "@uipath/skills-studioweb",
  );
  assert.deepEqual(new Set(packages.map(({ version }) => version)), new Set(["1.2.3-preview.45"]));

  assertMarkerFreeSkillTarball(
    byVariant.get("default").tarball,
    "@uipath/skills",
    "default",
  );
  assertMarkerFreeSkillTarball(
    byVariant.get("future-host").tarball,
    "@uipath/skills-future-host",
    "future-host",
  );
  assertMarkerFreeSkillTarball(
    byVariant.get("studioweb").tarball,
    "@uipath/skills-studioweb",
    "studioweb",
  );
  assert.equal(
    selectSkillPackage({
      directory: dirname(byVariant.get("future-host").tarball),
      packageName: "@uipath/skills-future-host",
      flavor: "future-host",
      version: "1.2.3-preview.45",
    }),
    byVariant.get("future-host").tarball,
  );
  assert.equal(
    selectSkillPackage({
      directory: dirname(byVariant.get("default").tarball),
      packageName: "@uipath/skills",
      flavor: "default",
      version: "1.2.3-preview.45",
    }),
    byVariant.get("default").tarball,
  );
  const selectedStudioWeb = selectSkillPackage({
    directory: dirname(byVariant.get("studioweb").tarball),
    packageName: "@uipath/skills-studioweb",
    flavor: "studioweb",
    version: "1.2.3-preview.45",
  });
  assert.equal(selectedStudioWeb, byVariant.get("studioweb").tarball);
  assert.throws(
    () =>
      selectSkillPackage({
        directory: dirname(selectedStudioWeb),
        packageName: "@uipath/skills-studioweb",
        flavor: "studioweb",
        version: "1.2.3-preview.46",
      }),
    /selected package version mismatch/,
  );

  const duplicateStudioWeb = join(dirname(selectedStudioWeb), "duplicate-studioweb.tgz");
  copyFileSync(selectedStudioWeb, duplicateStudioWeb);
  assert.throws(
    () =>
      selectSkillPackage({
        directory: dirname(selectedStudioWeb),
        packageName: "@uipath/skills-studioweb",
        flavor: "studioweb",
        version: "1.2.3-preview.45",
      }),
    /expected exactly one @uipath\/skills-studioweb tarball/,
  );
  rmSync(duplicateStudioWeb);

  const packCustomPolicyFixture = (
    label,
    mutateManifest,
    skillBody = "Safe content.\n",
  ) => {
    const packageDir = join(repo, `${label}-studioweb-package`);
    const outputDir = join(repo, `${label}-studioweb-output`);
    mkdirSync(join(packageDir, "skills", "uipath-leaky"), { recursive: true });
    mkdirSync(outputDir);
    const manifest = {
      name: "@uipath/skills-studioweb",
      version: "1.2.3-preview.45",
      uipathSkillsFlavor: "studioweb",
      files: ["skills"],
      publishConfig: { ...CUSTOM_PACKAGE_PUBLISH_CONFIG },
    };
    mutateManifest(manifest);
    writeFileSync(
      join(packageDir, "package.json"),
      `${JSON.stringify(manifest)}\n`,
    );
    writeFileSync(
      join(packageDir, "skills", "uipath-leaky", "SKILL.md"),
      entrypoint("uipath-leaky", skillBody),
    );
    const packed = runNpm(
      packageDir,
      "pack",
      "--json",
      "--pack-destination",
      outputDir,
    );
    assert.equal(packed.status, 0, packed.stderr || packed.stdout);
    return outputDir;
  };

  const unsafePolicyCases = [
    ["missing-policy", (manifest) => delete manifest.publishConfig],
    [
      "npmjs-registry",
      (manifest) => {
        manifest.publishConfig.registry = "https://registry.npmjs.org/";
      },
    ],
    [
      "public-access",
      (manifest) => {
        manifest.publishConfig.access = "public";
      },
    ],
    [
      "extra-setting",
      (manifest) => {
        manifest.publishConfig.provenance = true;
      },
    ],
  ];
  for (const [label, mutateManifest] of unsafePolicyCases) {
    const outputDir = packCustomPolicyFixture(label, mutateManifest);
    assert.throws(
      () =>
        selectSkillPackage({
          directory: outputDir,
          packageName: "@uipath/skills-studioweb",
          flavor: "studioweb",
          version: "1.2.3-preview.45",
        }),
      /selected custom package must use the GitHub Packages-only publish policy/,
    );
  }

  const linkedRepositoryOutput = packCustomPolicyFixture(
    "linked-repository",
    (manifest) => {
      manifest.repository = {
        type: "git",
        url: "https://github.com/UiPath/skills.git",
      };
    },
  );
  assert.throws(
    () =>
      selectSkillPackage({
        directory: linkedRepositoryOutput,
        packageName: "@uipath/skills-studioweb",
        flavor: "studioweb",
        version: "1.2.3-preview.45",
      }),
    /selected custom package must not define package\.json repository/,
  );

  const leakyOutput = packCustomPolicyFixture(
    "leaky-marker",
    () => {},
    block("host", "Leaked marker."),
  );
  assert.throws(
    () =>
      selectSkillPackage({
        directory: leakyOutput,
        packageName: "@uipath/skills-studioweb",
        flavor: "studioweb",
        version: "1.2.3-preview.45",
      }),
    /flavor marker leaked into selected npm tarball/,
  );

  for (const variant of ["default", "future-host", "studioweb"]) {
    const packageDir = byVariant.get(variant).packageDir;
    assert.ok(existsSync(join(packageDir, "skills", "uipath-changed", "SKILL.md")));
    assert.ok(existsSync(join(packageDir, "skills", "uipath-pass-through", "SKILL.md")));
    const manifest = JSON.parse(readFileSync(join(packageDir, "package.json"), "utf8"));
    assert.equal(manifest.uipathSkillsFlavor, variant);
    assert.equal(manifest.version, "1.2.3-preview.45");
    if (variant === "default") {
      assert.deepEqual(manifest.publishConfig, {
        registry: "https://registry.npmjs.org/",
        tag: "latest",
      });
      assert.equal(
        manifest.scripts.prepack,
        "node scripts/npm-package-lifecycle.mjs prepare",
      );
      assert.ok(existsSync(join(packageDir, "scripts", "npm-package-lifecycle.mjs")));
    } else {
      assert.ok(!("scripts" in manifest));
      assert.deepEqual(manifest.publishConfig, CUSTOM_PACKAGE_PUBLISH_CONFIG);
      assert.ok(!Object.hasOwn(manifest, "repository"));
      assert.equal(manifest.private, false);
      assert.ok(!existsSync(join(packageDir, "scripts")));
    }
    for (const data of treeFileBytes(packageDir).values()) {
      assert.ok(!containsFlavorMarker(data));
    }
  }

  const studioDir = byVariant.get("studioweb").packageDir;
  assert.match(
    readFileSync(join(studioDir, "skills", "uipath-changed", "SKILL.md"), "utf8"),
    /Studio Web project tool/,
  );
  assert.ok(!existsSync(join(studioDir, "assets")));
  assert.ok(!existsSync(join(studioDir, "hooks")));
  assert.ok(existsSync(join(byVariant.get("default").packageDir, "assets", "shared.txt")));
  assert.ok(existsSync(join(byVariant.get("default").packageDir, "hooks", "tool.sh")));

  const forcedPublicUserConfig = join(repo, "npmrc-forced-public-registry");
  writeFileSync(
    forcedPublicUserConfig,
    "registry=https://registry.npmjs.org/\n@uipath:registry=https://registry.npmjs.org/\n",
  );
  const customPublishDryRun = invokeNpm(
    repo,
    ["publish", selectedStudioWeb, "--dry-run", "--tag", "preview"],
    { npm_config_userconfig: forcedPublicUserConfig },
  );
  assert.equal(
    customPublishDryRun.status,
    0,
    customPublishDryRun.stderr || customPublishDryRun.stdout,
  );
  const customPublishOutput = [
    customPublishDryRun.stdout,
    customPublishDryRun.stderr,
  ].join("\n");
  assert.match(customPublishOutput, /Publishing to https:\/\/npm\.pkg\.github\.com\//);
  assert.doesNotMatch(
    customPublishOutput,
    /Publishing to https:\/\/registry\.npmjs\.org\//,
  );

  for (const item of packages) {
    assert.ok(existsSync(item.tarball));
    const entries = readTarballEntries(item.tarball);
    assert.ok(entries.has("package/package.json"));
    assert.ok(![...entries.keys()].some((name) => name.startsWith("package/skill-flavors/")));
    assert.ok(!entries.has("package/scripts/compose-skill-flavor.mjs"));
    assert.equal(
      entries.has("package/scripts/npm-package-lifecycle.mjs"),
      item.variant === "default",
    );
    const tarballManifest = JSON.parse(
      entries.get("package/package.json").toString("utf8"),
    );
    if (item.variant !== "default") {
      assert.deepEqual(
        tarballManifest.publishConfig,
        CUSTOM_PACKAGE_PUBLISH_CONFIG,
      );
      assert.ok(!Object.hasOwn(tarballManifest, "repository"));
    }
    const extracted = extractTarball(t, item.tarball);
    assert.ok(
      buffersMapEqual(
        treeFileBytes(join(item.packageDir, "skills")),
        treeFileBytes(join(extracted, "skills")),
      ),
    );
  }

  if (process.platform !== "win32") {
    const extractedDefault = extractTarball(t, byVariant.get("default").tarball);
    assert.notEqual(statSync(join(extractedDefault, "hooks", "tool.sh")).mode & 0o111, 0);

    const repackOutput = join(repo, "repacked-generated-default");
    mkdirSync(repackOutput);
    const repack = runNpm(
      extractedDefault,
      "pack",
      "--json",
      "--pack-destination",
      repackOutput,
    );
    assert.equal(repack.status, 0, repack.stderr || repack.stdout);
    const repacked = JSON.parse(repack.stdout);
    assert.equal(repacked.length, 1);
    const repackedEntries = readTarballEntries(join(repackOutput, repacked[0].filename));
    assert.ok(repackedEntries.has("package/skills/uipath-changed/SKILL.md"));
    assert.ok(!repackedEntries.has("package/scripts/compose-skill-flavor.mjs"));
  }
});

test("npm pack output parses on both the npm 11 array and npm 12 object shapes", (t) => {
  // npm <= 11 prints `[ { ...packResult } ]`; npm >= 12 prints
  // `{ "<packageName>": { ...packResult } }`. Reshape the real npm output into
  // each form so both are covered whatever npm major runs the suite -- the
  // object shape broke publishing to npmjs when CI's unpinned `npm@latest`
  // moved to npm 12.
  for (const shape of ["array", "object"]) {
    const repo = fixtureRepo(t);
    addSkill(repo, "uipath-example");
    addPackageManifest(repo);

    const runNpmPack = (options) => {
      const result = runRealNpmPack(options, repo);
      if (result.status !== 0) return result;
      const parsed = JSON.parse(result.stdout);
      const results = Array.isArray(parsed) ? parsed : Object.values(parsed);
      const reshaped =
        shape === "array"
          ? results
          : Object.fromEntries(results.map((entry) => [entry.name, entry]));
      return { ...result, stdout: JSON.stringify(reshaped, null, 2) };
    };

    const packages = withNpmCache(repo, () =>
      packAllVariants(repo, { runNpmPack }),
    );
    assert.equal(packages.length, 1, `${shape}: expected one package`);
    assert.equal(packages[0].packageName, "@uipath/skills", `${shape}: package name`);
    assert.ok(existsSync(packages[0].tarball), `${shape}: tarball exists`);
  }
});

test("npm pack output that names no tarball still fails loudly", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example");
  addPackageManifest(repo);

  assert.throws(
    () =>
      withNpmCache(repo, () =>
        packAllVariants(repo, {
          runNpmPack: () => ({ status: 0, stdout: "{}", stderr: "" }),
        }),
      ),
    /could not parse npm pack output/,
  );
});

test("a failed npm pack preserves every last successful generated output", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Default."));
  writeOverride(
    repo,
    "studioweb",
    "uipath-example/SKILL.md",
    block("host", "Studio Web."),
  );
  addPackageManifest(repo);

  withNpmCache(repo, () => packAllVariants(repo));
  const generatedRoots = ["skills", "packages", "npm"];
  const before = new Map(
    generatedRoots.map((name) => [
      name,
      treeFileBytes(join(repo, "build", name)),
    ]),
  );

  let calls = 0;
  const runNpmPack = (options) => {
    calls += 1;
    if (calls === 2) {
      return {
        status: 1,
        stdout: "",
        stderr: "simulated npm pack failure",
      };
    }
    return runRealNpmPack(options, repo);
  };

  assert.throws(
    () => packAllVariants(repo, { runNpmPack }),
    /simulated npm pack failure/,
  );
  assert.equal(calls, 2);
  for (const name of generatedRoots) {
    assert.ok(
      buffersMapEqual(
        before.get(name),
        treeFileBytes(join(repo, "build", name)),
      ),
      `${name} should remain byte-identical after a failed pack`,
    );
  }
  assert.deepEqual(
    readdirSync(join(repo, "build")).filter((name) =>
      name.startsWith(".skill-flavor-"),
    ),
    [],
  );
});

test("compact or malformed marker tokens in binary assets fail before output replacement", (t) => {
  for (const token of ["<!--skill-flavor:", "<!-- skill-flavor:", "<!--skill-flavor :"]) {
    const repo = fixtureRepo(t);
    const skill = addSkill(repo, "uipath-example");
    writeFileSync(join(skill, "asset.bin"), Buffer.from(`prefix ${token} suffix`));
    assert.throws(() => buildAllSkillTrees(repo), /marker leaked/);
    assert.ok(!existsSync(join(repo, "build", "skills")));
  }
});

test("repacking removes artifacts for a deleted flavor", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Default."));
  const temporaryFlavor = writeOverride(
    repo,
    "temporary-host",
    "uipath-example/SKILL.md",
    block("host", "Temporary."),
  );
  addPackageManifest(repo);
  const first = withNpmCache(repo, () => packAllVariants(repo));
  assert.deepEqual(new Set(first.map(({ variant }) => variant)), new Set(["default", "temporary-host"]));
  rmSync(temporaryFlavor, { recursive: true, force: true });
  const second = withNpmCache(repo, () => packAllVariants(repo));
  assert.deepEqual(second.map(({ variant }) => variant), ["default"]);
  assert.ok(!existsSync(join(repo, "build", "skills", "temporary-host")));
  assert.ok(!existsSync(join(repo, "build", "packages", "temporary-host")));
  assert.ok(
    !readdirSync(join(repo, "build", "npm")).some((name) => name.includes("temporary-host")),
  );
});

test("invalid root package manifests and payload paths fail safely", async (t) => {
  const cases = [
    ["not json\n", /invalid JSON/],
    [`${JSON.stringify({ name: "@uipath/skills", version: "1.0.0" })}\n`, /files.*list/],
    [
      `${JSON.stringify({ name: "@uipath/skills", version: "1.0.0", files: ["../outside"] })}\n`,
      /unsupported npm package 'files' entry/,
    ],
  ];
  for (const [manifest, expected] of cases) {
    await t.test(expected.source, (child) => {
      const repo = fixtureRepo(child);
      addSkill(repo, "uipath-example");
      writeFileSync(join(repo, "package.json"), manifest);
      assert.throws(() => withNpmCache(repo, () => packAllVariants(repo)), expected);
    });
  }
});

test("root npm pack emits one marker-free default package and restores canonical sources", (t) => {
  const repo = fixtureRepo(t);
  addSkill(
    repo,
    "uipath-example",
    `Before.\n\n${block("host", "Canonical default guidance.")}\nAfter.\n`,
  );
  addSkill(repo, "uipath-pass-through");
  writeOverride(
    repo,
    "studioweb",
    "uipath-example/SKILL.md",
    block("host", "Studio Web guidance."),
  );
  addPackageManifest(repo, "1.2.3-preview.7");
  const canonicalBefore = treeFileBytes(join(repo, "skills"));
  const generatedPackages = withNpmCache(repo, () => packAllVariants(repo));
  const generatedDefault = generatedPackages.find(({ variant }) => variant === "default");
  assert.ok(generatedDefault, "the all-flavor build must emit the default package");
  assertMarkerFreeSkillTarball(
    generatedDefault.tarball,
    "@uipath/skills",
    "default",
  );
  const output = join(repo, "root-pack-output");
  mkdirSync(output);

  const result = runNpm(repo, "pack", "--json", "--pack-destination", output);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const packed = JSON.parse(result.stdout);
  assert.equal(packed.length, 1);
  const tarball = join(output, packed[0].filename);
  assert.ok(existsSync(tarball));
  assert.equal(
    sha512File(tarball),
    sha512File(generatedDefault.tarball),
    "root npm pack and the generated default tarball must be byte-identical",
  );

  const entries = readTarballEntries(tarball);
  const manifest = JSON.parse(entries.get("package/package.json").toString("utf8"));
  assert.equal(manifest.name, "@uipath/skills");
  assert.equal(manifest.version, "1.2.3-preview.7");
  assert.equal(manifest.uipathSkillsFlavor, "default");
  assert.equal(
    manifest.scripts.prepack,
    "node scripts/npm-package-lifecycle.mjs prepare",
  );
  const skill = entries.get("package/skills/uipath-example/SKILL.md").toString("utf8");
  assert.match(skill, /Canonical default guidance/);
  assert.doesNotMatch(skill, /Studio Web guidance/);
  assert.ok(!containsFlavorMarker(skill));
  assert.ok(entries.has("package/skills/uipath-pass-through/SKILL.md"));
  assert.ok(entries.has("package/scripts/npm-package-lifecycle.mjs"));
  assert.ok(!entries.has("package/scripts/compose-skill-flavor.mjs"));
  for (const [name, bytes] of entries) {
    if (name.startsWith("package/skills/")) {
      assert.ok(!containsFlavorMarker(bytes), name);
    }
  }

  assert.ok(buffersMapEqual(canonicalBefore, treeFileBytes(join(repo, "skills"))));
  assert.ok(!existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
  assert.deepEqual(readdirSync(output), [packed[0].filename]);
});

test("root npm publish dry-run keeps the old default-only behavior and restores sources", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Canonical default guidance."));
  writeOverride(
    repo,
    "studioweb",
    "uipath-example/SKILL.md",
    block("host", "Studio Web guidance."),
  );
  addPackageManifest(repo);
  const canonicalBefore = treeFileBytes(join(repo, "skills"));

  const result = runNpm(
    repo,
    "publish",
    "--dry-run",
    "--json",
    "--access",
    "public",
    "--tag",
    "test",
  );
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(`${result.stdout}\n${result.stderr}`, /@uipath\/skills|"name"\s*:\s*"@uipath\/skills"/);
  assert.doesNotMatch(`${result.stdout}\n${result.stderr}`, /skills-studioweb/);
  assert.ok(buffersMapEqual(canonicalBefore, treeFileBytes(join(repo, "skills"))));
  assert.ok(!existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
});

test("publishing workflows isolate root publishing behind a generic flavor publisher", () => {
  const defaultWorkflow = readFileSync(DEFAULT_PUBLISH_WORKFLOW, "utf8");
  const flavorWorkflow = readFileSync(FLAVOR_PUBLISH_WORKFLOW, "utf8");
  const selectorScript = readFileSync(SELECT_SKILL_PACKAGE_SCRIPT, "utf8");
  const publishDev = workflowJob(defaultWorkflow, "publish-dev");
  const publishNpmjs = workflowJob(defaultWorkflow, "publish-npmjs");
  const publishStudioWebDev = workflowJob(defaultWorkflow, "publish-studioweb-dev");
  const publishStudioWebPreview = workflowJob(
    defaultWorkflow,
    "publish-studioweb-preview",
  );
  const flavorPublish = workflowJob(flavorWorkflow, "publish");

  assert.match(
    defaultWorkflow,
    /^  group: publish-\$\{\{ github\.event_name == 'workflow_dispatch' && github\.event\.inputs\.channel \|\| \(github\.ref == 'refs\/heads\/main' && 'dev' \|\| 'preview'\) \}\}$/m,
  );
  const concurrencyGroup = ({ eventName, ref, channel }) =>
    `publish-${
      eventName === "workflow_dispatch"
        ? channel
        : ref === "refs/heads/main"
          ? "dev"
          : "preview"
    }`;
  assert.equal(
    concurrencyGroup({ eventName: "push", ref: "refs/heads/main" }),
    concurrencyGroup({ eventName: "workflow_dispatch", channel: "dev" }),
  );
  assert.equal(
    concurrencyGroup({ eventName: "push", ref: "refs/heads/release/v1.200" }),
    concurrencyGroup({ eventName: "workflow_dispatch", channel: "preview" }),
  );

  assert.match(publishDev, /^\s*run:\s*npm publish --tag dev\s*$/m);
  assert.match(
    publishNpmjs,
    /^\s*npm publish --access public --provenance --tag \$\{\{ steps\.dist\.outputs\.tag \}\}\s*$/m,
  );
  for (const job of [publishDev, publishNpmjs]) {
    assert.doesNotMatch(job, /npm run skills:pack|build\/npm|\.tgz/);
    assert.doesNotMatch(job, /ENABLE_SKILL_FLAVOR_PUBLISH/);
  }
  assert.doesNotMatch(defaultWorkflow, /npm run skills:pack|build\/npm\/\*\.tgz/);
  for (const job of [publishStudioWebDev, publishStudioWebPreview]) {
    assert.match(
      job,
      /^\s*uses:\s*\.\/\.github\/workflows\/publish-skill-flavor\.yml\s*$/m,
    );
    assert.match(job, /^\s*flavor:\s*studioweb\s*$/m);
    assert.match(job, /^\s*packages:\s*write\s*$/m);
    assert.doesNotMatch(job, /npm run skills:pack|npm publish|build\/npm/);
    assert.doesNotMatch(job, /npmjs|id-token\s*:|--provenance/i);
  }
  assert.match(publishStudioWebDev, /github\.ref == 'refs\/heads\/main'/);
  assert.match(publishStudioWebDev, /^\s*channel:\s*dev\s*$/m);
  assert.match(publishStudioWebPreview, /startsWith\(github\.ref, 'refs\/heads\/release\/'\)/);
  assert.match(publishStudioWebPreview, /^\s*channel:\s*preview\s*$/m);

  assert.doesNotMatch(defaultWorkflow, /publish-studioweb\.yml/);

  assert.match(flavorWorkflow, /^\s*workflow_call:\s*$/m);
  assert.match(
    flavorPublish,
    /^    if: \$\{\{ vars\.ENABLE_SKILL_FLAVOR_PUBLISH == 'true' \}\}$/m,
  );
  const workflowInputs = flavorWorkflow.match(
    /^ {4}inputs:\s*\n(?<body>[\s\S]*?)^permissions:/m,
  )?.groups?.body;
  assert.ok(workflowInputs, "generic flavor workflow must declare workflow_call inputs");
  assert.deepEqual(
    [...workflowInputs.matchAll(/^ {6}([a-z][a-z0-9_-]*):\s*$/gm)].map(
      (match) => match[1],
    ),
    ["flavor", "channel"],
  );
  assert.match(flavorWorkflow, /FLAVOR:\s*\$\{\{ inputs\.flavor \}\}/);
  assert.match(flavorWorkflow, /https:\/\/npm\.pkg\.github\.com/);
  assert.match(flavorWorkflow, /^\s*packages:\s*write\s*$/m);
  assert.match(flavorWorkflow, /^\s*run:\s*npm run skills:pack\s*$/m);
  assert.doesNotMatch(
    flavorWorkflow,
    /npmjs|id-token\s*:|--provenance/i,
  );
  assert.match(flavorWorkflow, /NODE_AUTH_TOKEN:\s*\$\{\{ secrets\.GITHUB_TOKEN \}\}/);
  assert.match(
    flavorWorkflow,
    /RUN_NUMBER:\s*\$\{\{ github\.run_number \}\}/,
  );
  assert.match(
    flavorWorkflow,
    /VERSION="\$\{BASE\}-\$\{CHANNEL\}\.\$\{RUN_NUMBER\}"/,
  );

  assert.match(flavorWorkflow, /Unsupported skill flavor/);
  assert.match(flavorWorkflow, /\[ "\$FLAVOR" = "default" \]/);
  assert.match(flavorWorkflow, /skill-flavors\/\$FLAVOR/);
  assert.match(flavorWorkflow, /import \{ packageName \} from/);
  assert.match(flavorWorkflow, /packageName\(manifest\.name, process\.env\.FLAVOR\)/);
  assert.match(flavorWorkflow, /--name "\$PACKAGE_NAME"/);
  assert.match(flavorWorkflow, /--flavor "\$FLAVOR"/);
  assert.match(flavorWorkflow, /--version "\$VERSION"/);
  assert.doesNotMatch(flavorWorkflow, /skills-studioweb|--flavor\s+studioweb/);
  assert.match(flavorWorkflow, /node scripts\/select-skill-package\.mjs/);
  assert.match(flavorWorkflow, /npm config get @uipath:registry/);
  assert.match(
    flavorWorkflow,
    /\[ "\$REGISTRY" != "https:\/\/npm\.pkg\.github\.com\/" \]/,
  );
  assert.match(
    flavorWorkflow,
    /TARBALL:\s*\$\{\{ steps\.package\.outputs\.tarball \}\}/,
  );
  assert.match(flavorWorkflow, /CHANNEL:\s*\$\{\{ inputs\.channel \}\}/);
  assert.match(
    flavorWorkflow,
    /npm publish "\$TARBALL"[\s\S]*--registry https:\/\/npm\.pkg\.github\.com\/[\s\S]*--tag "\$CHANNEL"/,
  );
  assert.doesNotMatch(flavorWorkflow, /--access (?:public|restricted)/);

  assert.match(selectorScript, /manifest\.name !== packageName/);
  assert.match(selectorScript, /manifest\.uipathSkillsFlavor !== flavor/);
  assert.match(selectorScript, /matches\.length !== 1/);
  assert.match(selectorScript, /containsFlavorMarker/);
  assert.match(
    selectorScript,
    /selected custom package must use the GitHub Packages-only publish policy/,
  );
  assert.match(
    selectorScript,
    /selected custom package must not define package\.json repository/,
  );

  const publishCommands = flavorWorkflow
    .split(/\r?\n/)
    .map((line) => line.trim().replace(/^run:\s*/, ""))
    .filter((line) => line.startsWith("npm publish "));
  assert.equal(publishCommands.length, 1);
  assert.doesNotMatch(publishCommands[0], /build\/npm\/\*|\*\.tgz/);
});

test("root package preflight failure leaves canonical sources active", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Canonical default guidance."));
  addPackageManifest(repo);
  const canonicalBefore = treeFileBytes(join(repo, "skills"));

  assert.throws(
    () =>
      prepareRootDefaultPackage(repo, {
        runNpmPack: () => ({
          status: 1,
          stdout: "",
          stderr: "simulated npm cache failure",
        }),
      }),
    /simulated npm cache failure/,
  );
  assert.ok(buffersMapEqual(canonicalBefore, treeFileBytes(join(repo, "skills"))));
  assert.ok(!existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
});

test("an interrupted root package transaction is explicit and recoverable", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Canonical default guidance."));
  addPackageManifest(repo);
  const canonicalBefore = treeFileBytes(join(repo, "skills"));

  const prepared = withNpmCache(repo, () => prepareRootDefaultPackage(repo));
  assert.equal(prepared.skillCount, 1);
  assert.ok(existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
  assert.ok(
    !containsFlavorMarker(
      readFileSync(join(repo, "skills", "uipath-example", "SKILL.md"), "utf8"),
    ),
  );
  assert.throws(
    () => withNpmCache(repo, () => prepareRootDefaultPackage(repo)),
    /already active.*skills:recover/s,
  );

  const restored = restoreRootDefaultPackage(repo);
  assert.equal(restored.restored, true);
  assert.ok(buffersMapEqual(canonicalBefore, treeFileBytes(join(repo, "skills"))));
  assert.ok(!existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
  assert.equal(restoreRootDefaultPackage(repo).restored, false);
});

test("simultaneous root package preparation leaves exactly one active transaction", async (t) => {
  const repo = fixtureRepo(t);
  const skill = addSkill(
    repo,
    "uipath-example",
    block("host", "Canonical default guidance."),
  );
  const references = join(skill, "references");
  mkdirSync(references);
  for (let index = 0; index < 600; index += 1) {
    writeFileSync(join(references, `reference-${index}.md`), `Reference ${index}.\n`);
  }
  addPackageManifest(repo);
  const canonicalBefore = treeFileBytes(join(repo, "skills"));

  const results = await Promise.all([
    runCliAsync(repo, "prepare-root-pack"),
    runCliAsync(repo, "prepare-root-pack"),
  ]);
  assert.equal(
    results.filter((result) => result.status === 0).length,
    1,
    results.map((result) => result.stderr || result.stdout).join("\n---\n"),
  );
  assert.equal(results.filter((result) => result.status !== 0).length, 1);
  assert.ok(existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
  assert.ok(
    !containsFlavorMarker(
      readFileSync(join(repo, "skills", "uipath-example", "SKILL.md"), "utf8"),
    ),
  );

  assert.equal(restoreRootDefaultPackage(repo).restored, true);
  assert.ok(buffersMapEqual(canonicalBefore, treeFileBytes(join(repo, "skills"))));
  assert.ok(!existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
});

test("recovery preserves unexpected overlay edits while restoring canonical sources", (t) => {
  const repo = fixtureRepo(t);
  addSkill(repo, "uipath-example", block("host", "Canonical default guidance."));
  addPackageManifest(repo);
  const canonicalBefore = treeFileBytes(join(repo, "skills"));

  withNpmCache(repo, () => prepareRootDefaultPackage(repo));
  writeFileSync(
    join(repo, "skills", "uipath-example", "SKILL.md"),
    entrypoint("uipath-example", "Unexpected edit during packaging.\n"),
  );
  assert.throws(
    () => restoreRootDefaultPackage(repo),
    /unexpected packaging-time changes were preserved/,
  );

  assert.ok(buffersMapEqual(canonicalBefore, treeFileBytes(join(repo, "skills"))));
  assert.ok(!existsSync(join(repo, "build", ROOT_PACK_TRANSACTION_DIRNAME)));
  const recoveries = readdirSync(join(repo, "build")).filter((name) =>
    name.startsWith(".root-pack-recovery-"),
  );
  assert.equal(recoveries.length, 1);
  assert.match(
    readFileSync(
      join(
        repo,
        "build",
        recoveries[0],
        "modified-packed-skills",
        "uipath-example",
        "SKILL.md",
      ),
      "utf8",
    ),
    /Unexpected edit during packaging/,
  );
});
