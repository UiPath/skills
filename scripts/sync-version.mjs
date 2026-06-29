#!/usr/bin/env node

/**
 * Single source of truth for the skills npm package version.
 *
 * `package.json` `version` is authoritative. This script propagates it to:
 *
 *   - version-manifest.json        .skillsVersion + .targetCli
 *   - .claude-plugin/plugin.json   .version (major.minor only — see below)
 *   - .claude-plugin/marketplace.json  .plugins[0].version (== plugin.json)
 *   - .codex-plugin/plugin.json    .version (== plugin.json — Codex channel)
 *
 * `targetCli` is derived as the matching @uipath/cli minor line
 * (`^MAJOR.MINOR.0`). A skills release tracks the CLI minor line it ships
 * with, so a given CLI release resolves to a compatible skills package and
 * the two never mismatch.
 *
 * The plugin manifests share `major.minor` with package.json but the patch is
 * an independent daily counter (advanced by --bump-patch from
 * daily-version-bump.yml to drive plugin auto-update). `.claude-plugin/plugin.json`
 * is the canonical plugin version; the marketplace and Codex manifests mirror
 * it. Rule enforced here:
 *   - plugin major.minor != package.json major.minor -> reset to `M.N.0`
 *     (errors out if package.json minor is BELOW the plugin minor — plugin
 *      auto-update never downgrades, so a lower version would freeze users)
 *   - plugin major.minor == package.json major.minor -> --bump-patch advances
 *     the patch by 1; without it the patch is left untouched
 *   - marketplace .plugins[0].version and .codex-plugin/plugin.json .version
 *     must always equal .claude-plugin/plugin.json .version
 * See docs/RELEASE.md.
 *
 * Usage:
 *   node scripts/sync-version.mjs               # rewrite derived manifests
 *   node scripts/sync-version.mjs --bump-patch  # also advance the plugin daily-counter patch
 *   node scripts/sync-version.mjs --check       # exit 1 if any are out of sync
 */

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");
const BUMP_PATCH = process.argv.includes("--bump-patch");

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

/** `1.196.4` -> `1.196`. */
function minorLine(version) {
  const [major, minor] = version.split(".");
  return `${major}.${minor}`;
}

/** Compare two `M.N` lines numerically. Returns -1, 0, or 1. */
function compareMinorLine(a, b) {
  const [am, an] = a.split(".").map(Number);
  const [bm, bn] = b.split(".").map(Number);
  if (am !== bm) return am < bm ? -1 : 1;
  if (an !== bn) return an < bn ? -1 : 1;
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

// .claude-plugin/plugin.json — canonical plugin version: shared major.minor
// with package.json, independent daily-counter patch.
const plugin = readJson(PATHS.plugin);
let pluginVersion = plugin.version;
if (minorLine(pluginVersion) !== minorLine(version)) {
  // Reset the patch counter onto package.json's minor line — but never
  // downgrade. Plugin auto-update doesn't go backwards, so resetting to a
  // lower minor (a bad manual edit / revert in package.json) would freeze
  // users on a version they can never leave. Fail loudly instead.
  if (compareMinorLine(minorLine(version), minorLine(pluginVersion)) < 0) {
    console.error(
      `✗ package.json minor (${minorLine(version)}) is below the plugin minor ` +
        `(${minorLine(pluginVersion)}). Refusing to downgrade .claude-plugin/plugin.json.`,
    );
    process.exit(1);
  }
  pluginVersion = `${minorLine(version)}.0`;
} else if (BUMP_PATCH && !CHECK) {
  const patch = Number(pluginVersion.split(".")[2]);
  pluginVersion = `${minorLine(version)}.${patch + 1}`;
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
