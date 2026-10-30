#!/usr/bin/env node
// Check that the genome core is byte-identical in uipath-planner and uipath-genome-builder. Node >= 20, built-ins only.
//
// uipath-planner writes genomes (author, extract, edit) and uipath-genome-builder builds them (build). Each
// skill is installed on its own and may not read the other's files, so both ship the genome core: the format
// guides, the shared source-frameworks guide, the genome templates and the checker. The canonical copies live
// in skills/uipath-planner/ (its CLAUDE.md § Genome core); this script names every copy that is missing or
// differs, and --fix copies the canonical files over the builder's.
//
// A core file links only to other core files or to SKILL.md (both skills have one); a guide outside the core
// is named by its skill and file name, never linked, so every link resolves in both skills.
//
// Usage:
//   node scripts/check-genome-core.mjs          # check, exit 1 on any difference
//   node scripts/check-genome-core.mjs --fix    # copy the canonical files over uipath-genome-builder's copies
//
// Exit 0 when the copies are identical, 1 otherwise.

import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..");
const CANONICAL = join(REPO, "skills", "uipath-planner");
const COPY = join(REPO, "skills", "uipath-genome-builder");
const CORE = [
  "references/genome-format-guide.md",
  "references/extracted-genome-guide.md",
  "references/transactional-shape-guide.md",
  "references/skill-mapping-guide.md",
  "references/uipath-source-guide.md",
  "references/parts-guide.md",
  "references/source-frameworks-guide.md",
  "assets/templates/component-genome-template.md",
  "assets/templates/process-genome-template.md",
  "scripts/check-genome.mjs",
];
const LINK = /\]\((?:\.\/)?([^)#\s]+\.md)(?:#[^)]*)?\)/g;

// line endings are a checkout setting, not content
const read = (path) => readFileSync(path).toString("utf-8").replace(/\r\n/g, "\n");

const fix = process.argv.includes("--fix");
const coreNames = new Set(CORE.map((rel) => basename(rel)));
const failures = [];
for (const rel of CORE) {
  const source = join(CANONICAL, rel);
  const target = join(COPY, rel);
  const shown = `skills/uipath-genome-builder/${rel}`;
  if (!existsSync(source)) {
    failures.push(`FAIL: canonical skills/uipath-planner/${rel} is missing`);
    continue;
  }
  if (rel.endsWith(".md")) {
    for (const [, link] of read(source).matchAll(LINK)) {
      const name = basename(link);
      if (!coreNames.has(name) && name !== "SKILL.md") {
        failures.push(`FAIL: ${rel} links ${link}, which only one skill has — name it by skill and file instead`);
      }
    }
  }
  if (fix) {
    mkdirSync(dirname(target), { recursive: true });
    copyFileSync(source, target);
  } else if (!existsSync(target)) {
    failures.push(`FAIL: ${shown} is missing (run with --fix)`);
  } else if (read(source) !== read(target)) {
    failures.push(`FAIL: ${shown} differs from the planner's copy (run with --fix)`);
  }
}
for (const failure of failures) console.log(failure);
if (!failures.length) console.log(`OK - ${CORE.length} genome core files identical in uipath-planner and uipath-genome-builder.`);
process.exitCode = failures.length ? 1 : 0;
