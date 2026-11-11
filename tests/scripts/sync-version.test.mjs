import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, "scripts", "sync-version.mjs");
const PRELOAD = pathToFileURL(join(dirname(fileURLToPath(import.meta.url)), "support", "redirect-preload.mjs")).href;

const FILES = {
  manifest: "version-manifest.json",
  plugin: ".claude-plugin/plugin.json",
  marketplace: ".claude-plugin/marketplace.json",
  codexPlugin: ".codex-plugin/plugin.json",
  codexMarketplace: ".agents/plugins/marketplace.json",
  cursorPlugin: ".cursor-plugin/plugin.json",
  geminiExtension: "gemini-extension.json",
};

/** A fixture repo whose manifests all agree with `pkgVersion`, unless overridden. */
function makeRepo({ pkgVersion, pluginVersion = pkgVersion.split("-")[0], overrides = {} }) {
  const root = mkdtempSync(join(tmpdir(), "sv-"));
  const [major, minor] = pkgVersion.split(".");
  const docs = {
    manifest: { skillsVersion: pkgVersion, targetCli: `^${major}.${minor}.0` },
    plugin: { name: "p", version: pluginVersion },
    marketplace: { plugins: [{ name: "p", version: pluginVersion }] },
    codexPlugin: { name: "p", version: pluginVersion },
    codexMarketplace: { plugins: [{ name: "p", version: pluginVersion }] },
    cursorPlugin: { name: "p", version: pluginVersion },
    geminiExtension: { name: "p", version: pluginVersion },
    ...overrides,
  };
  const write = (rel, doc) => {
    mkdirSync(dirname(join(root, rel)), { recursive: true });
    writeFileSync(join(root, rel), `${JSON.stringify(doc, null, 2)}\n`);
  };
  write("package.json", { name: "x", version: pkgVersion });
  for (const [key, rel] of Object.entries(FILES)) write(rel, docs[key]);
  return root;
}

const readDoc = (root, rel) => JSON.parse(readFileSync(join(root, rel), "utf8"));

function run(root, ...args) {
  const result = spawnSync(process.execPath, ["--import", PRELOAD, SCRIPT, ...args], {
    encoding: "utf8",
    env: { ...process.env, REDIRECT_FS_FROM: REPO_ROOT, REDIRECT_FS_TO: root },
  });
  return result;
}

function withRepo(options, body) {
  const root = makeRepo(options);
  try {
    body(root);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

test("--list-paths prints every owned file as one repo-relative POSIX path per line", () => {
  const result = spawnSync(process.execPath, [SCRIPT, "--list-paths"], { encoding: "utf8" });
  assert.equal(result.status, 0);
  assert.deepEqual(result.stdout.trim().split("\n"), [
    "package.json",
    "version-manifest.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".cursor-plugin/plugin.json",
    "gemini-extension.json",
  ]);
});

test("--bump-patch is refused because the plugin version mirrors package.json", () => {
  const result = spawnSync(process.execPath, [SCRIPT, "--bump-patch"], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /--bump-patch was removed/);
});

test("manifests already in sync: reports it and leaves the files byte-identical", () => {
  withRepo({ pkgVersion: "1.205.0" }, (root) => {
    const before = readFileSync(join(root, FILES.plugin), "utf8");
    const result = run(root);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /Already in sync \(package 1\.205\.0, plugin 1\.205\.0, targetCli \^1\.205\.0\)/);
    assert.equal(readFileSync(join(root, FILES.plugin), "utf8"), before);
  });
});

test("--check on in-sync manifests exits 0", () => {
  withRepo({ pkgVersion: "1.205.0" }, (root) => {
    const result = run(root, "--check");
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /All manifests in sync/);
  });
});

test("rewrites every derived manifest to the package base version, stripping the pre-release suffix", () => {
  const stale = { name: "p", version: "1.204.0" };
  withRepo(
    {
      pkgVersion: "1.206.1-alpha.20260713.42",
      pluginVersion: "1.204.0",
      overrides: {
        manifest: { skillsVersion: "1.204.0", targetCli: "^1.204.0" },
        plugin: stale,
      },
    },
    (root) => {
      const result = run(root);
      assert.equal(result.status, 0, result.stderr);
      assert.match(result.stdout, /Synced 7 manifest\(s\)/);
      assert.deepEqual(readDoc(root, FILES.manifest), {
        skillsVersion: "1.206.1-alpha.20260713.42",
        targetCli: "^1.206.0",
      });
      assert.equal(readDoc(root, FILES.plugin).version, "1.206.1");
      assert.equal(readDoc(root, FILES.marketplace).plugins[0].version, "1.206.1");
      assert.equal(readDoc(root, FILES.codexPlugin).version, "1.206.1");
      assert.equal(readDoc(root, FILES.codexMarketplace).plugins[0].version, "1.206.1");
      assert.equal(readDoc(root, FILES.cursorPlugin).version, "1.206.1");
      assert.equal(readDoc(root, FILES.geminiExtension).version, "1.206.1");
      assert.ok(readFileSync(join(root, FILES.plugin), "utf8").endsWith("}\n"), "trailing newline kept");

      const again = run(root, "--check");
      assert.equal(again.status, 0, again.stderr);
    },
  );
});

test("--check lists each drifted manifest, exits 1 and writes nothing", () => {
  withRepo(
    {
      pkgVersion: "1.205.0",
      overrides: { cursorPlugin: { name: "p", version: "1.204.0" }, codexPlugin: { name: "p", version: "1.204.0" } },
    },
    (root) => {
      const result = run(root, "--check");
      assert.equal(result.status, 1);
      assert.match(result.stderr, /Version drift detected/);
      assert.match(result.stderr, /\.cursor-plugin\/plugin\.json: 1\.204\.0 -> 1\.205\.0/);
      assert.match(result.stderr, /\.codex-plugin\/plugin\.json: 1\.204\.0 -> 1\.205\.0/);
      assert.equal(readDoc(root, FILES.cursorPlugin).version, "1.204.0");
    },
  );
});

test("a marketplace plugins[0] drift is reported by its file label and fixed", () => {
  withRepo(
    {
      pkgVersion: "1.205.0",
      overrides: {
        marketplace: { plugins: [{ name: "p", version: "1.1.0" }] },
        codexMarketplace: { plugins: [{ name: "p", version: "1.1.0" }] },
      },
    },
    (root) => {
      const result = run(root);
      assert.equal(result.status, 0, result.stderr);
      assert.match(result.stdout, /\.claude-plugin\/marketplace\.json: 1\.1\.0 -> 1\.205\.0/);
      assert.match(result.stdout, /\.agents\/plugins\/marketplace\.json: 1\.1\.0 -> 1\.205\.0/);
      assert.equal(readDoc(root, FILES.marketplace).plugins[0].version, "1.205.0");
      assert.equal(readDoc(root, FILES.codexMarketplace).plugins[0].version, "1.205.0");
    },
  );
});

test("refuses to downgrade the plugin when package.json is below it", () => {
  withRepo({ pkgVersion: "1.204.0", pluginVersion: "1.205.0" }, (root) => {
    const result = run(root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /package\.json version \(1\.204\.0\) is below the plugin version \(1\.205\.0\)/);
    assert.equal(readDoc(root, FILES.plugin).version, "1.205.0");
  });
});

test("a marketplace manifest without plugins[] is a hard error, not a no-op", () => {
  withRepo({ pkgVersion: "1.205.0", overrides: { marketplace: { plugins: [] } } }, (root) => {
    const result = run(root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /\.claude-plugin\/marketplace\.json has no plugins\[\] entry to sync/);
  });
});
