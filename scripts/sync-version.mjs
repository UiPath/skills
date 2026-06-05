#!/usr/bin/env node

/**
 * Single source of truth for the skills npm package version.
 *
 * `package.json` `version` is authoritative. This script propagates it to:
 *
 *   - version-manifest.json   .skillsVersion + .targetCli
 *
 * `targetCli` is derived as the matching @uipath/cli minor line
 * (`^MAJOR.MINOR.0`). A skills release tracks the CLI minor line it ships
 * with, so a given CLI release resolves to a compatible skills package and
 * the two never mismatch.
 *
 * Note: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
 * are deliberately NOT managed here yet — they stay on their own version
 * track (bumped by daily-version-bump.yml) until the alignment task lands.
 * See docs/RELEASE.md.
 *
 * Usage:
 *   node scripts/sync-version.mjs           # rewrite derived manifests
 *   node scripts/sync-version.mjs --check    # exit 1 if any are out of sync
 */

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");

const PATHS = {
  pkg: join(ROOT, "package.json"),
  manifest: join(ROOT, "version-manifest.json"),
};

function readJson(p) {
  return JSON.parse(readFileSync(p, "utf-8"));
}

/** Write JSON with a trailing newline, 2-space indent (repo convention). */
function writeJson(p, obj) {
  writeFileSync(p, `${JSON.stringify(obj, null, 2)}\n`);
}

/** `1.196.4` -> `^1.196.0` (the matching CLI minor line). */
function cliLine(version) {
  const [major, minor] = version.split(".");
  return `^${major}.${minor}.0`;
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

if (CHECK) {
  if (drift.length > 0) {
    console.error("✗ Version drift detected (run `npm run version:sync`):");
    for (const d of drift) console.error(`  - ${d}`);
    process.exit(1);
  }
  console.log(`✓ All manifests in sync at ${version} (targetCli ${targetCli}).`);
  process.exit(0);
}

if (writes.length === 0) {
  console.log(`✓ Already in sync at ${version} (targetCli ${targetCli}).`);
} else {
  for (const w of writes) w();
  console.log(`✓ Synced ${writes.length} manifest(s) to ${version} (targetCli ${targetCli}):`);
  for (const d of drift) console.log(`  - ${d}`);
}
