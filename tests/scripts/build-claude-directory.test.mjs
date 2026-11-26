import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { buildClaudeDirectory } from "../../scripts/build-claude-directory.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function tempDir(t, prefix) {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

function write(root, relativePath, text) {
  const file = join(root, ...relativePath.split("/"));
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, text);
}

function skillMd(name, frontmatter = "") {
  return `---\nname: ${name}\ndescription: "${name} test skill"\n${frontmatter}---\n\n# ${name}\n`;
}

/** A repository with one stable skill, one preview skill, and the default plugin root. */
function fixtureRepo(t, statuses = { "uipath-stable": "stable", "uipath-preview": "preview" }) {
  const repo = tempDir(t, "claude-directory-repo-");
  for (const name of Object.keys(statuses)) write(repo, `skills/${name}/SKILL.md`, skillMd(name));
  const skills = Object.fromEntries(Object.entries(statuses).map(([name, status]) => [name, { status }]));
  write(repo, "assets/skill-status.json", JSON.stringify({ skills }));
  write(repo, ".claude-plugin/plugin.json", JSON.stringify({ name: "uipath", skills: "./skills/" }));
  write(repo, ".claude-plugin/marketplace.json", "{}");
  write(repo, "hooks/hooks.json", "{}");
  write(repo, "commands/install-permissions.md", "# Install permissions\n");
  write(repo, "README.md", "# UiPath\n");
  write(repo, "LICENSE", "MIT\n");
  write(repo, "CLAUDE.md", "# Repository rules\n");
  return repo;
}

function build(t, repo) {
  const out = join(tempDir(t, "claude-directory-out-"), "edition");
  return { out, edition: buildClaudeDirectory(repo, out) };
}

const read = (root, relativePath) => readFileSync(join(root, ...relativePath.split("/")), "utf8");

test("ships stable skills and the plugin root, never hooks or repository files", (t) => {
  const { edition } = build(t, fixtureRepo(t));
  assert.deepEqual([...edition.files.keys()].sort(), [
    ".claude-plugin/plugin.json",
    "LICENSE",
    "README.md",
    "commands/install-permissions.md",
    "skills/uipath-stable/SKILL.md",
  ]);
});

test("keeps only the allowed-tools grants the directory accepts", (t) => {
  const repo = fixtureRepo(t, { "uipath-a": "stable", "uipath-b": "stable" });
  write(repo, "skills/uipath-a/SKILL.md", skillMd("uipath-a", "allowed-tools: Bash, Read, Write, Glob\nuser-invocable: true\n"));
  write(repo, "skills/uipath-b/SKILL.md", skillMd("uipath-b", "allowed-tools: Bash, Write\n"));
  const { out } = build(t, repo);
  assert.equal(read(out, "skills/uipath-a/SKILL.md"), skillMd("uipath-a", "allowed-tools: Read, Glob\nuser-invocable: true\n"));
  assert.equal(read(out, "skills/uipath-b/SKILL.md"), skillMd("uipath-b"));
});

test("ships examples and templates as Markdown and rewrites their citations", (t) => {
  const repo = fixtureRepo(t, { "uipath-flow": "stable" });
  const source = "const doc = `\n```\n`;\nexport default doc;\n";
  write(repo, "skills/uipath-flow/examples/Doorbell.flow.ts", source);
  write(repo, "skills/uipath-flow/assets/templates/app/index-template.css", ":root {}\n");
  write(
    repo,
    "skills/uipath-flow/SKILL.md",
    skillMd("uipath-flow") +
      "Copy `examples/Doorbell.flow.ts`, or the closest `examples/*.flow.ts`. See examples/Doorbell.flow.ts.\n" +
      "Copy [app/index-template.css](assets/templates/app/index-template.css), then `index-template.css` → `src/index.css`.\n" +
      "Write `.flow-sdk/Doorbell.flow.ts`; check every `*.flow.ts`.\n",
  );
  const { out, edition } = build(t, repo);

  assert.ok(!edition.files.has("skills/uipath-flow/examples/Doorbell.flow.ts"));
  assert.equal(
    read(out, "skills/uipath-flow/examples/Doorbell.flow.ts.md"),
    "# Doorbell.flow.ts\n\nThe code block is the exact content of `Doorbell.flow.ts`. To copy `Doorbell.flow.ts`, " +
      "write only the block's contents; never copy this Markdown file.\n\n" +
      "````ts\n" + source + "````\n",
  );
  assert.match(read(out, "skills/uipath-flow/assets/templates/app/index-template.css.md"), /^```css\n:root \{\}\n```\n$/m);
  assert.equal(
    read(out, "skills/uipath-flow/SKILL.md"),
    skillMd("uipath-flow") +
      "> **Claude directory edition:** each cited `<name>.md` wraps the file `<name>` in one fenced block. " +
      "To copy one, write only the block's contents to the destination; never copy the Markdown file.\n\n" +
      "Copy `examples/Doorbell.flow.ts.md`, or the closest `examples/*.flow.ts.md`. See examples/Doorbell.flow.ts.md.\n" +
      "Copy [app/index-template.css.md](assets/templates/app/index-template.css.md), then `index-template.css.md` → `src/index.css`.\n" +
      "Write `.flow-sdk/Doorbell.flow.ts`; check every `*.flow.ts`.\n",
  );
});

test("omits scripts and fixtures and reports them", (t) => {
  const repo = fixtureRepo(t, { "uipath-apps": "stable" });
  write(repo, "skills/uipath-apps/scripts/validate.js", "console.log(1);\n");
  write(repo, "skills/uipath-apps/assets/fixtures/kit.tar.gz", "binary");
  const { out, edition } = build(t, repo);
  assert.deepEqual(edition.omitted, ["skills/uipath-apps/assets/fixtures/kit.tar.gz", "skills/uipath-apps/scripts/validate.js"]);
  assert.ok(!existsSync(join(out, "skills", "uipath-apps", "scripts")));
});

test("refuses a file no rule classifies and writes nothing", (t) => {
  const repo = fixtureRepo(t);
  write(repo, "skills/uipath-stable/references/probe.py", "print(1)\n");
  const out = join(tempDir(t, "claude-directory-out-"), "edition");
  assert.throws(() => buildClaudeDirectory(repo, out), /skills\/uipath-stable\/references\/probe\.py: the directory refuses/);
  assert.ok(!existsSync(out));
});

test("refuses a shipped file that starts with a shebang", (t) => {
  const repo = fixtureRepo(t);
  write(repo, "skills/uipath-stable/references/run.txt", "#!/bin/sh\n");
  assert.throws(() => build(t, repo), /run\.txt: files starting with #! are refused/);
});

test("refuses a manifest that declares hooks or an agent it does not ship", (t) => {
  const repo = fixtureRepo(t);
  write(repo, ".claude-plugin/plugin.json", JSON.stringify({ hooks: "./hooks/hooks.json", agents: ["./skills/uipath-preview/agents/a.md"] }));
  write(repo, "skills/uipath-preview/agents/a.md", "# Agent\n");
  assert.throws(() => build(t, repo), (error) => {
    assert.match(error.message, /plugin\.json: declares hooks/);
    assert.match(error.message, /agent \.\/skills\/uipath-preview\/agents\/a\.md is not in the directory edition/);
    return true;
  });
});

// The edition is pushed to a public branch; a followed link would publish
// whatever it points at, such as the token checkout keeps in .git/config.
test("refuses a symbolic link in the plugin root and reads nothing through it", (t) => {
  const repo = fixtureRepo(t);
  const secret = join(tempDir(t, "claude-directory-secret-"), "config");
  writeFileSync(secret, "AUTHORIZATION: basic token\n");
  rmSync(join(repo, "README.md"));
  symlinkSync(secret, join(repo, "README.md"));
  rmSync(join(repo, "commands"), { recursive: true });
  symlinkSync(dirname(secret), join(repo, "commands"));
  const out = join(tempDir(t, "claude-directory-out-"), "edition");
  assert.throws(() => buildClaudeDirectory(repo, out), (error) => {
    assert.match(error.message, /README\.md: must be a regular file, not a link/);
    assert.match(error.message, /commands: must be a directory, not a link/);
    assert.doesNotMatch(error.message, /AUTHORIZATION/);
    return true;
  });
  assert.ok(!existsSync(out));
});

test("refuses a link the citation rewrite cannot reach", (t) => {
  const repo = fixtureRepo(t, { "uipath-flow": "stable" });
  write(repo, "skills/uipath-flow/examples/Doorbell.flow.ts", "export {};\n");
  write(repo, "skills/uipath-flow/examples/README.md", "[Doorbell](./Doorbell.flow.ts)\n");
  assert.throws(() => build(t, repo), /examples\/README\.md: links skills\/uipath-flow\/examples\/Doorbell\.flow\.ts/);
});

// Builds this repository, so the pull request that adds a file the directory
// would refuse fails here instead of at the next stable release.
test("the repository builds a directory edition of its stable skills", (t) => {
  const { out, edition } = build(t, REPO_ROOT);
  const { skills } = JSON.parse(read(REPO_ROOT, "assets/skill-status.json"));
  const stable = Object.keys(skills).filter((name) => skills[name].status === "stable").sort();
  assert.deepEqual(readdirSync(join(out, "skills")).sort(), stable);
  assert.deepEqual(edition.skills.sort(), stable);
  assert.ok(!existsSync(join(out, "hooks")));
  for (const relativePath of edition.files.keys()) {
    assert.match(relativePath, /(\.(md|txt|json|ya?ml|png|jpe?g|gif|webp|ico)|^LICENSE)$/i, relativePath);
  }
});
