import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  chmodSync,
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
  buildAllSkillTrees,
  createAllVariants,
  createCompositionPlan,
  createDefaultPlan,
  materializeComposition,
  packageName,
  packAllVariants,
  parseMarkerBlocks,
  readTarballEntries,
  stripMarkerBoundaries,
  treeFileBytes,
} from "../../scripts/compose-skill-flavor.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SCRIPT = join(REPO_ROOT, "scripts", "compose-skill-flavor.mjs");

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
    `<!-- skill-flavor:${name}:start -->${newline}` +
    `${body}${newline}` +
    `<!-- skill-flavor:${name}:end -->${newline}`
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

function addPackageManifest(repo, version = "1.2.3") {
  const manifest = {
    name: "@uipath/skills",
    version,
    description: "Fixture skills package",
    license: "MIT",
    repository: { type: "git", url: "https://github.com/UiPath/skills.git" },
    keywords: ["uipath", "skills"],
    files: [
      "skills",
      "assets",
      "hooks",
      "version-manifest.json",
      "README.md",
      "LICENSE",
    ],
    scripts: { prepack: "exit 99" },
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
  assert.doesNotMatch(composed, /<!-- skill-flavor:/);
  assert.ok(existsSync(join(output, "uipath-another", "SKILL.md")));
  assert.ok(existsSync(join(output, "uipath-pass-through", "SKILL.md")));
  assert.deepEqual(readFileSync(join(output, "uipath-changed", "asset.bin")), Buffer.from([0, 1, 2, 3]));
  assert.deepEqual(readFileSync(join(changed, "SKILL.md")), canonicalBefore);
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
  assert.doesNotMatch(text, /skill-flavor:/);
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

test("marker parser rejects malformed state and preserves valid canonical order", () => {
  const cases = [
    ["inline <!-- skill-flavor:x:start -->\n", /malformed flavor marker/],
    ["<!-- skill-flavor:x:end -->\n", /ends without a start/],
    ["<!-- skill-flavor:x:start -->\nbody\n", /has no end marker/],
    [
      "<!-- skill-flavor:x:start -->\n<!-- skill-flavor:y:end -->\n",
      /does not match/,
    ],
    [
      "<!-- skill-flavor:x:start -->\n<!-- skill-flavor:y:start -->\n",
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
  addPackageManifest(repo, "1.2.3-preview.45");

  const packages = withNpmCache(repo, () => packAllVariants(repo));
  assert.deepEqual(packages.map(({ variant }) => variant), [
    "default",
    "future-host",
    "studioweb",
  ]);
  const byVariant = new Map(packages.map((item) => [item.variant, item]));
  assert.equal(byVariant.get("default").packageName, "@uipath/skills");
  assert.equal(
    byVariant.get("studioweb").packageName,
    "@uipath/skills-studioweb",
  );
  assert.deepEqual(new Set(packages.map(({ version }) => version)), new Set(["1.2.3-preview.45"]));

  for (const variant of ["default", "future-host", "studioweb"]) {
    const packageDir = byVariant.get(variant).packageDir;
    assert.ok(existsSync(join(packageDir, "skills", "uipath-changed", "SKILL.md")));
    assert.ok(existsSync(join(packageDir, "skills", "uipath-pass-through", "SKILL.md")));
    const manifest = JSON.parse(readFileSync(join(packageDir, "package.json"), "utf8"));
    assert.equal(manifest.uipathSkillsFlavor, variant);
    assert.equal(manifest.version, "1.2.3-preview.45");
    assert.ok(!("scripts" in manifest));
    for (const data of treeFileBytes(packageDir).values()) {
      assert.ok(!data.includes(Buffer.from("<!-- skill-flavor:")));
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

  for (const item of packages) {
    assert.ok(existsSync(item.tarball));
    const entries = readTarballEntries(item.tarball);
    assert.ok(entries.has("package/package.json"));
    assert.ok(![...entries.keys()].some((name) => name.startsWith("package/skill-flavors/")));
    assert.ok(![...entries.keys()].some((name) => name.startsWith("package/scripts/")));
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
  }
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

test("a marker token in a binary canonical asset fails before output replacement", (t) => {
  const repo = fixtureRepo(t);
  const skill = addSkill(repo, "uipath-example");
  writeFileSync(join(skill, "asset.bin"), Buffer.from("prefix <!-- skill-flavor: suffix"));
  assert.throws(() => buildAllSkillTrees(repo), /marker leaked/);
  assert.ok(!existsSync(join(repo, "build", "skills")));
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

test("root npm pack guard exits with the safe generated-package command", (t) => {
  const repo = fixtureRepo(t);
  const result = runCli(repo, "guard-root-pack");
  assert.equal(result.status, 1);
  assert.match(result.stderr, /npm run skills:pack/);
});
