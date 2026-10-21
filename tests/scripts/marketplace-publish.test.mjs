import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { directoryManifest } from "../../.github/workflows/scripts/codex-directory-manifest.mjs";
import { bumpEntry } from "../../.github/workflows/scripts/bump-awesome-copilot-entry.mjs";
import { buildChecklist } from "../../.github/workflows/scripts/marketplace-release-checklist.mjs";
import { GEMINI_PLATFORMS, releaseAssetNames } from "../../.github/workflows/scripts/release-assets.mjs";

const SHA = "0123456789abcdef0123456789abcdef01234567";
const BUMP_SCRIPT = new URL("../../.github/workflows/scripts/bump-awesome-copilot-entry.mjs", import.meta.url);

test("directory manifest drops hooks and apps, keeps everything else", () => {
  const source = { name: "uipath", version: "1.206.0", skills: "./skills/", hooks: "./hooks/hooks.json", apps: "./.app.json", interface: { displayName: "UiPath" } };
  assert.deepEqual(directoryManifest(source), {
    name: "uipath",
    version: "1.206.0",
    skills: "./skills/",
    interface: { displayName: "UiPath" },
  });
  assert.equal(source.hooks, "./hooks/hooks.json", "source manifest is not mutated");
});

test("the committed Codex manifest yields a hook-free directory manifest", () => {
  const committed = JSON.parse(readFileSync(new URL("../../.codex-plugin/plugin.json", import.meta.url), "utf8"));
  const manifest = directoryManifest(committed);
  assert.equal(manifest.hooks, undefined);
  assert.equal(manifest.apps, undefined);
  assert.equal(manifest.skills, committed.skills);
});

const listing = [
  { name: "other", version: "0.1.0", source: { source: "github", repo: "acme/other", ref: "v0.1.0" } },
  { name: "uipath", version: "1.205.0", keywords: ["uipath"], source: { source: "github", repo: "UiPath/skills", ref: "v1.205.0", sha: "f".repeat(40) } },
];

test("bumpEntry updates only version, ref and sha of the named entry", () => {
  const bumped = bumpEntry(listing, { name: "uipath", version: "1.206.0", tag: "v1.206.0", sha: SHA });
  assert.deepEqual(bumped[1], {
    name: "uipath",
    version: "1.206.0",
    keywords: ["uipath"],
    source: { source: "github", repo: "UiPath/skills", ref: "v1.206.0", sha: SHA },
  });
  assert.equal(bumped[0], listing[0]);
  assert.equal(listing[1].version, "1.205.0", "input list is not mutated");
});

test("bumpEntry rejects a missing entry, a non-GitHub source and a short SHA", () => {
  const target = { name: "uipath", version: "1.206.0", tag: "v1.206.0", sha: SHA };
  assert.throws(() => bumpEntry(listing, { ...target, name: "missing" }), /No awesome-copilot entry named "missing"/);
  assert.throws(
    () => bumpEntry([{ name: "uipath", source: { source: "url" } }], target),
    /expected "github"/,
  );
  assert.throws(() => bumpEntry(listing, { ...target, sha: "abc123" }), /40-character commit SHA/);
});

test("bump script edits external.json and the generated marketplace.json in place", () => {
  const checkout = mkdtempSync(join(tmpdir(), "awesome-copilot-"));
  mkdirSync(join(checkout, "plugins"));
  mkdirSync(join(checkout, ".github", "plugin"), { recursive: true });
  writeFileSync(join(checkout, "plugins", "external.json"), `${JSON.stringify(listing, null, 2)}\n`);
  writeFileSync(join(checkout, ".github", "plugin", "marketplace.json"), JSON.stringify({ name: "awesome-copilot", plugins: listing }, null, 2));

  const run = spawnSync(process.execPath, [fileURLToPath(BUMP_SCRIPT)], {
    env: { ...process.env, CHECKOUT_DIR: checkout, PLUGIN_NAME: "uipath", VERSION: "1.206.0", TAG: "v1.206.0", SHA },
    encoding: "utf8",
  });
  assert.equal(run.status, 0, run.stderr);

  const external = readFileSync(join(checkout, "plugins", "external.json"), "utf8");
  assert.ok(external.endsWith("\n"), "keeps the trailing newline");
  assert.equal(JSON.parse(external)[1].source.sha, SHA);
  const marketplaceText = readFileSync(join(checkout, ".github", "plugin", "marketplace.json"), "utf8");
  assert.ok(!marketplaceText.endsWith("\n"), "does not add a trailing newline that was not there");
  const marketplace = JSON.parse(marketplaceText);
  assert.equal(marketplace.name, "awesome-copilot");
  assert.equal(marketplace.plugins[1].version, "1.206.0");
});

const checklistInput = {
  version: "1.206.0",
  releaseUrl: "https://github.com/UiPath/skills/releases/tag/v1.206.0",
  zipName: "uipath-codex-plugin-1.206.0.zip",
  runUrl: "https://github.com/UiPath/skills/actions/runs/1",
};

test("checklist always lists the manual catalogs and links the ZIP's release", () => {
  const { title, body } = buildChecklist({ ...checklistInput, copilot: { result: "skipped", prUrl: "" } });
  assert.equal(title, "Marketplace follow-ups for v1.206.0");
  assert.match(body, /OpenAI \/ Codex directory:\*\* download `uipath-codex-plugin-1\.206\.0\.zip` from the \[release\]\(https:\/\/github\.com\/UiPath\/skills\/releases\/tag\/v1\.206\.0\)/);
  assert.match(body, /Cursor Marketplace/);
  assert.match(body, /Anthropic Directory:\*\* confirm v1\.206\.0/);
  assert.doesNotMatch(body, /awesome-copilot:/, "a skipped bump job adds no item");
});

test("checklist tracks an opened awesome-copilot PR, or flags a failed one", () => {
  const opened = buildChecklist({ ...checklistInput, copilot: { result: "success", prUrl: "https://github.com/github/awesome-copilot/pull/9" } });
  assert.match(opened.body, /awesome-copilot:\*\* follow https:\/\/github\.com\/github\/awesome-copilot\/pull\/9/);

  const failed = buildChecklist({ ...checklistInput, copilot: { result: "failure", prUrl: "" } });
  assert.match(failed.body, /bump PR was not opened \(job failure\); see the \[workflow run\]\(https:\/\/github\.com\/UiPath\/skills\/actions\/runs\/1\)/);
});

// Mirror of findReleaseAsset in google-gemini/gemini-cli
// packages/cli/src/config/extensions/github.ts — how Gemini picks the asset it
// installs from our latest release.
function geminiPicks(assetNames, platform, arch) {
  const names = assetNames.map((name) => name.toLowerCase());
  const byPrefix = (prefix) => assetNames[names.findIndex((name) => name.startsWith(prefix))];
  return (
    byPrefix(`${platform}.${arch}.`) ??
    byPrefix(`${platform}.`) ??
    (assetNames.length === 1 && !/darwin|linux|win32/.test(names[0]) ? assetNames[0] : undefined)
  );
}

test("Gemini installs its own archive on every platform, never the Codex ZIP", () => {
  const { codex, gemini } = releaseAssetNames("1.206.0");
  const assets = [codex, ...gemini];
  for (const platform of GEMINI_PLATFORMS) {
    for (const arch of ["x64", "arm64"]) {
      assert.equal(geminiPicks(assets, platform, arch), `${platform}.uipath-gemini-extension-1.206.0.zip`);
    }
  }
  assert.doesNotMatch(codex, /darwin|linux|win32/i, "a platform name would let Gemini match the Codex ZIP");
});
