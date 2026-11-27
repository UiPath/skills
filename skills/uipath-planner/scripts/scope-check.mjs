#!/usr/bin/env node
// Checks an SDD's Constraint Gate record: on Automation Suite older than 2.2510.2 the
// `## Recommended Scope` block's `Blocked by platform:` line names Maestro, and the block carries its
// `**Need profile:**` line. An RPA SDD (its `## Master Project Architecture` / `## Implementation Mode`
// sections) also keeps §11's `### Project Mode Decision` table with its Attendance and Initiation columns.
// Usage: node scope-check.mjs <NAME>-sdd.md
// Prints `OK: ...` (exit 0) or one `FAIL: ...` line per defect (exit 1).
import { readFileSync } from "node:fs";

const path = process.argv[2];
if (!path) {
  console.log("usage: node scope-check.mjs <NAME>-sdd.md");
  process.exit(2);
}
const text = readFileSync(path, "utf8").replace(/\r\n/g, "\n");
const fails = [];

const line = (label) => text.match(new RegExp(`^\\*\\*${label}:\\*\\*\\s*(.*)$`, "m"))?.[1].trim();

// true when the version is older than Automation Suite 2.2510.2 (Maestro's minimum)
function olderThanMaestro(version) {
  if (/^20\d\d\.\d+/.test(version)) return true; // calendar releases (2023.10, 2024.10) predate 2.2510
  const m = version.match(/^(\d+)\.(\d+)(?:\.(\d+))?/);
  if (!m) return false;
  const [a, b, c] = [Number(m[1]), Number(m[2]), Number(m[3] ?? 0)];
  return a < 2 || (a === 2 && (b < 2510 || (b === 2510 && c < 2)));
}

const delivery = line("Delivery model") ?? "";
const blocked = line("Blocked by platform") ?? "";
const as = delivery.match(/automation[- ]suite\s+v?([\d.]+)/i);
if (as && olderThanMaestro(as[1]) && !/maestro/i.test(blocked)) {
  fails.push(`Delivery model is Automation Suite ${as[1]}, older than 2.2510.2, and '**Blocked by platform:**' does not name Maestro — add 'Maestro (Flow, BPMN, Case) → <alternative the design applies>' even when no Maestro product was picked`);
}

if (/^## Recommended Scope\s*$/m.test(text) && !line("Need profile")) {
  fails.push("'## Recommended Scope' has no '**Need profile:** <core need and target KPI>' line — copy it from the Phase 1 summary (design-guide.md Step 3.5)");
}

if (/^##\s+.*\b(Master Project Architecture|Implementation Mode)\s*$/m.test(text)) {
  const at = text.search(/^###\s+.*Project Mode Decision\s*$/m);
  if (at < 0) {
    fails.push("RPA SDD has no '### Project Mode Decision' under §11 Project Structure — write the template's ten-column table (Project | Type | Compatibility | Authoring | Attendance | Initiation | Framework | Persistence | Packaging), one row per project");
  } else {
    const body = text.slice(at).split("\n").slice(1);
    const end = body.findIndex((l) => /^#{1,3}\s/.test(l));
    const section = (end < 0 ? body : body.slice(0, end)).join("\n");
    const header = section.split("\n").find((l) => /^\|/.test(l.trim())) ?? "";
    const missing = ["Attendance", "Initiation", "Framework", "Packaging"].filter((c) => !header.includes(c));
    if (missing.length) fails.push(`'### Project Mode Decision' table lacks the ${missing.join(", ")} column(s) — write the template's ten-column table, never a Decision / Selected mode / Reason table`);
  }
}

if (fails.length) {
  for (const f of fails) console.log(`FAIL: ${f}`);
  process.exit(1);
}
console.log(`OK: Constraint Gate record and template lines${as ? `; Automation Suite ${as[1]}` : ""}${blocked ? `; blocked: ${blocked.slice(0, 80)}` : ""}`);
