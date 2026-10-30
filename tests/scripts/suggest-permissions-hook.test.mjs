import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const HOOK = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "hooks", "suggest-permissions.mjs");
const NUDGE = "uipath: To skip 25+ approval prompts per uip build, run: /uipath:install-permissions\n";

/** Runs the hook in a sandbox: empty HOME, empty cwd, no project dir unless given. */
function run({ env = {}, setup } = {}) {
  const root = mkdtempSync(join(tmpdir(), "sp-"));
  const home = join(root, "home");
  const cwd = join(root, "cwd");
  mkdirSync(home, { recursive: true });
  mkdirSync(cwd, { recursive: true });
  setup?.({ root, home, cwd });
  const base = { PATH: process.env.PATH, SystemRoot: process.env.SystemRoot, HOME: home, USERPROFILE: home };
  if (process.env.NODE_V8_COVERAGE) base.NODE_V8_COVERAGE = process.env.NODE_V8_COVERAGE;
  try {
    const result = spawnSync(process.execPath, [HOOK], {
      cwd,
      encoding: "utf8",
      env: { ...base, CLAUDE_PLUGIN_ROOT: join(root, "plugin"), ...env },
    });
    return { ...result, root, home, cwd };
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

const writeSettings = (dir, name, content) => {
  mkdirSync(join(dir, ".claude"), { recursive: true });
  writeFileSync(join(dir, ".claude", name), content);
};

test("outside a Claude plugin context the hook stays silent", () => {
  const result = run({ env: { CLAUDE_PLUGIN_ROOT: "" } });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, "");
});

test("Codex sessions (PLUGIN_ROOT set) stay silent", () => {
  const result = run({ env: { PLUGIN_ROOT: "/codex" } });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, "");
});

test("no uip allowlist anywhere: prints the one-line nudge to stderr and exits 0", () => {
  const result = run();
  assert.equal(result.status, 0);
  assert.equal(result.stderr, NUDGE);
  assert.equal(result.stdout, "");
});

test("settings files that do not mention uip still get the nudge", () => {
  const result = run({
    setup: ({ cwd, home }) => {
      writeSettings(cwd, "settings.json", JSON.stringify({ permissions: { allow: ["Bash(git status)"] } }));
      writeSettings(home, "settings.json", "{ not even json");
    },
  });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, NUDGE);
});

for (const [where, place] of [
  ["the working directory's settings.local.json", ({ cwd }) => writeSettings(cwd, "settings.local.json", '{"permissions":{"allow":["Bash(uip:*)"]}}')],
  ["the working directory's settings.json", ({ cwd }) => writeSettings(cwd, "settings.json", '{"permissions":{"deny":["Bash(uip rpa delete:*)"]}}')],
  ["the user's home settings.json", ({ home }) => writeSettings(home, "settings.json", '{"permissions":{"ask":["Bash(uip login)"]}}')],
]) {
  test(`a uip rule in ${where} (allow, ask or deny) silences the nudge`, () => {
    const result = run({ setup: place });
    assert.equal(result.status, 0);
    assert.equal(result.stderr, "");
  });
}

test("a CLAUDE_PROJECT_DIR without settings still gets the nudge", () => {
  const result = run({ env: { CLAUDE_PROJECT_DIR: join(tmpdir(), "sp-does-not-exist") } });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, NUDGE);
});

test("a uip rule in CLAUDE_PROJECT_DIR settings silences the nudge", () => {
  const project = mkdtempSync(join(tmpdir(), "sp-proj-"));
  try {
    writeSettings(project, "settings.local.json", '{"permissions":{"allow":["Bash(uip:*)"]}}');
    const result = run({ env: { CLAUDE_PROJECT_DIR: project } });
    assert.equal(result.status, 0);
    assert.equal(result.stderr, "");
  } finally {
    rmSync(project, { recursive: true, force: true });
  }
});
