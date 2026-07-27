#!/usr/bin/env node

/**
 * Single source of truth for the skills npm package version.
 *
 * `package.json` `version` is authoritative. This script propagates it to:
 *
 *   - version-manifest.json        .skillsVersion + .targetCli
 *   - .claude-plugin/plugin.json   .version (== package.json base version)
 *   - .claude-plugin/marketplace.json  .plugins[0].version (== plugin.json)
 *   - .codex-plugin/plugin.json    .version (== plugin.json — Codex channel)
 *
 * `targetCli` is derived as the matching @uipath/cli minor line
 * (`^MAJOR.MINOR.0`). A skills release tracks the CLI minor line it ships
 * with, so a given CLI release resolves to a compatible skills package and
 * the two never mismatch.
 *
 * The plugin manifests mirror package.json's base `M.N.P` version exactly —
 * there is no independent plugin patch counter. Pre-release suffixes (the
 * alpha stamp from publish.yml) are NOT propagated: plugin auto-update wants
 * plain versions, and the plugin channel is a git ref, not the npm tarball.
 * `.claude-plugin/plugin.json` is the canonical plugin version; the
 * marketplace and Codex manifests mirror it. Rules enforced here:
 *   - plugin version != package.json base version -> rewrite to the base
 *     version (errors out if package.json's base version is BELOW the plugin
 *     version — plugin auto-update never downgrades, so a lower version
 *     would freeze users)
 *   - marketplace .plugins[0].version and .codex-plugin/plugin.json .version
 *     must always equal .claude-plugin/plugin.json .version
 * See docs/RELEASE.md.
 *
 * Usage:
 *   node scripts/sync-version.mjs               # rewrite derived manifests
 *   node scripts/sync-version.mjs --check       # exit 1 if any are out of sync
 */

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");

if (process.argv.includes("--bump-patch")) {
  console.error(
    "✗ --bump-patch was removed: the plugin version mirrors package.json " +
      "exactly (no independent patch counter). Bump package.json and rerun.",
  );
  process.exit(1);
}

const PATHS = {
  pkg: join(ROOT, "package.json"),
  manifest: join(ROOT, "version-manifest.json"),
  plugin: join(ROOT, ".claude-plugin", "plugin.json"),
  marketplace: join(ROOT, ".claude-plugin", "marketplace.json"),
  codexPlugin: join(ROOT, ".codex-plugin", "plugin.json"),
};

function readJson(p) {
  return JSON.parse(readFileSync(p, "utf-8"));
}

/** Write JSON with a trailing newline, 2-space indent (repo convention). */
function writeJson(p, obj) {
  writeFileSync(p, `${JSON.stringify(obj, null, 2)}\n`);
}

/** `1.197.4` -> `^1.197.0` (the matching CLI minor line). */
function cliLine(version) {
  const [major, minor] = version.split(".");
  return `^${major}.${minor}.0`;
}

/** `1.198.0-alpha.20260713.42` -> `1.198.0` (pre-release suffix stripped). */
function baseVersion(version) {
  return version.split("-")[0];
}

/** Compare two base `M.N.P` versions numerically. Returns -1, 0, or 1. */
function compareBaseVersion(a, b) {
  const pa = baseVersion(a).split(".").map(Number);
  const pb = baseVersion(b).split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    if (pa[i] !== pb[i]) return pa[i] < pb[i] ? -1 : 1;
  }
  return 0;
}

const version = readJson(PATHS.pkg).version;
const targetCli = cliLine(version);

const drift = [];
const writes = [];

// version-manifest.json
const manifest = readJson(PATHS.manifest);
if (manifest.skillsVersion !== version || manifest.targetCli !== targetCli) {
  drift.push(
    `version-manifest.json: ${manifest.skillsVersion}/${manifest.targetCli} -> ${version}/${targetCli}`,
  );
  manifest.skillsVersion = version;
  manifest.targetCli = targetCli;
  writes.push(() => writeJson(PATHS.manifest, manifest));
}

// .claude-plugin/plugin.json — canonical plugin version: mirrors package.json's
// base version exactly (pre-release suffix stripped).
const plugin = readJson(PATHS.plugin);
const pluginVersion = baseVersion(version);
if (compareBaseVersion(pluginVersion, plugin.version) < 0) {
  // Never downgrade. Plugin auto-update doesn't go backwards, so writing a
  // lower version (a bad manual edit / revert in package.json) would freeze
  // users on a version they can never leave. Fail loudly instead.
  console.error(
    `✗ package.json version (${pluginVersion}) is below the plugin version ` +
      `(${plugin.version}). Refusing to downgrade .claude-plugin/plugin.json.`,
  );
  process.exit(1);
}

if (plugin.version !== pluginVersion) {
  drift.push(`.claude-plugin/plugin.json: ${plugin.version} -> ${pluginVersion}`);
  plugin.version = pluginVersion;
  writes.push(() => writeJson(PATHS.plugin, plugin));
}

// .claude-plugin/marketplace.json — must equal plugin.json exactly.
const marketplace = readJson(PATHS.marketplace);
if (!Array.isArray(marketplace.plugins) || marketplace.plugins.length === 0) {
  console.error("✗ .claude-plugin/marketplace.json has no plugins[] entry to sync.");
  process.exit(1);
}
if (marketplace.plugins[0].version !== pluginVersion) {
  drift.push(
    `.claude-plugin/marketplace.json: ${marketplace.plugins[0].version} -> ${pluginVersion}`,
  );
  marketplace.plugins[0].version = pluginVersion;
  writes.push(() => writeJson(PATHS.marketplace, marketplace));
}

// .codex-plugin/plugin.json — Codex distribution channel; must equal plugin.json.
const codexPlugin = readJson(PATHS.codexPlugin);
if (codexPlugin.version !== pluginVersion) {
  drift.push(
    `.codex-plugin/plugin.json: ${codexPlugin.version} -> ${pluginVersion}`,
  );
  codexPlugin.version = pluginVersion;
  writes.push(() => writeJson(PATHS.codexPlugin, codexPlugin));
}

if (CHECK) {
  if (drift.length > 0) {
    console.error("✗ Version drift detected (run `npm run version:sync`):");
    for (const d of drift) console.error(`  - ${d}`);
    process.exit(1);
  }
  console.log(
    `✓ All manifests in sync (package ${version}, plugin ${pluginVersion}, targetCli ${targetCli}).`,
  );
  process.exit(0);
}

if (writes.length === 0) {
  console.log(
    `✓ Already in sync (package ${version}, plugin ${pluginVersion}, targetCli ${targetCli}).`,
  );
} else {
  for (const w of writes) w();
  console.log(
    `✓ Synced ${writes.length} manifest(s) (package ${version}, plugin ${pluginVersion}, targetCli ${targetCli}):`,
  );
  for (const d of drift) console.log(`  - ${d}`);
}
