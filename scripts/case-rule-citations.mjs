#!/usr/bin/env node
// Resolve every `Rule N` citation in the case skill to the TITLE it lands on.
//
// Numbers are the fragile part: inserting a rule mid-list shifts every citation
// at or above it, silently (measured: an insertion at Rule 4 moves 205 of 224
// citations onto the wrong rule). Titles are stable under renumbering, so a
// title-keyed snapshot is invisible to a correct renumber and loud about an
// incorrect one -- and costs nothing in an agent's context, unlike annotating
// all 224 citations inline (+1,449 tokens per run, forever).
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const SKILL_DIR = join(REPO_ROOT, "skills", "uipath-maestro-case");

export function ruleTitles(skillMd) {
  const sec = /^## Critical Rules\s*$([\s\S]*?)(?=^## )/m.exec(skillMd);
  if (!sec) throw new Error("no `## Critical Rules` section");
  const out = new Map();
  for (const m of sec[1].matchAll(/^(\d+)\. \*\*(.+?)\*\*/gm)) {
    out.set(Number(m[1]), m[2].replace(/\.$/, ""));
  }
  return out;
}

function mdFiles(root) {
  const out = [];
  const walk = (d) => {
    for (const e of readdirSync(d)) {
      const full = join(d, e);
      if (statSync(full).isDirectory()) walk(full);
      else if (e.endsWith(".md")) out.push(full);
    }
  };
  walk(root);
  return out.sort();
}

export function citationMap(skillDir = SKILL_DIR) {
  const titles = ruleTitles(readFileSync(join(skillDir, "SKILL.md"), "utf8"));
  const map = {};
  for (const file of mdFiles(skillDir)) {
    const hits = [];
    for (const m of readFileSync(file, "utf8").matchAll(/\bRule (\d+)\b/g)) {
      const n = Number(m[1]);
      hits.push(titles.get(n) ?? `<<UNRESOLVED Rule ${n}>>`);
    }
    if (hits.length) {
      const counts = {};
      for (const h of hits) counts[h] = (counts[h] ?? 0) + 1;
      map[relative(skillDir, file)] = Object.fromEntries(
        Object.entries(counts).sort(([a], [b]) => a.localeCompare(b)),
      );
    }
  }
  return map;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  process.stdout.write(JSON.stringify(citationMap(), null, 2) + "\n");
}
