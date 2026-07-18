#!/usr/bin/env node

/**
 * Maturity gate for stable releases (PILOT-5542).
 *
 * Removes every skill marked `in-development` in assets/skill-status.json
 * from the working tree so it never ships in the stable npm tarball, and
 * rewrites the manifest to drop the pruned entries (the shipped manifest
 * stays bijective with the shipped skills/ dirs).
 *
 * Run ONLY in the publish-release job of publish.yml, before `npm publish` —
 * an uncommitted working-tree mutation, exactly like the alpha version stamp.
 * The alpha track and the git-based Claude Code plugin channel are NOT gated:
 * they ship everything. See docs/RELEASE.md.
 *
 * Usage:
 *   node scripts/prune-dev-skills.mjs           # delete + rewrite manifest
 *   node scripts/prune-dev-skills.mjs --list    # report only, change nothing
 *
 * Exits non-zero if a manifest entry has no matching skills/<name>/ dir
 * (manifest drift — fix assets/skill-status.json before publishing).
 */

import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = join(ROOT, "assets", "skill-status.json");
const LIST_ONLY = process.argv.includes("--list");

const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));
const entries = manifest.skills ?? {};

const pruned = [];
const missing = [];

for (const name of Object.keys(entries).sort()) {
  if (entries[name].status !== "in-development") continue;
  const dir = join(ROOT, "skills", name);
  if (!existsSync(dir)) {
    missing.push(name);
    continue;
  }
  pruned.push(name);
}

if (missing.length > 0) {
  console.error(
    `✗ Manifest drift: ${missing.length} in-development entr(y/ies) have no skills/<name>/ dir:`,
  );
  for (const name of missing) console.error(`  - ${name}`);
  console.error("Fix assets/skill-status.json before publishing.");
  process.exit(1);
}

if (pruned.length === 0) {
  console.log("✓ No in-development skills — nothing to prune.");
  process.exit(0);
}

if (LIST_ONLY) {
  console.log(`Would prune ${pruned.length} in-development skill(s) (dry run):`);
  for (const name of pruned) console.log(`  - skills/${name}`);
  process.exit(0);
}

for (const name of pruned) {
  rmSync(join(ROOT, "skills", name), { recursive: true });
  delete entries[name];
}
writeFileSync(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`);

console.log(
  `✓ Pruned ${pruned.length} in-development skill(s) from the stable package:`,
);
for (const name of pruned) console.log(`  - skills/${name}`);
console.log(
  `${Object.keys(entries).length} skill(s) remain (stable/preview). Manifest rewritten.`,
);
