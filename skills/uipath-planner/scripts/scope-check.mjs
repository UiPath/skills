#!/usr/bin/env node
// Checks an SDD's Constraint Gate record: on Automation Suite older than 2.2510.2 the
// `## Recommended Scope` block's `Blocked by platform:` line names Maestro.
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

if (fails.length) {
  for (const f of fails) console.log(`FAIL: ${f}`);
  process.exit(1);
}
console.log(`OK: Constraint Gate record${as ? `; Automation Suite ${as[1]}` : ""}${blocked ? `; blocked: ${blocked.slice(0, 80)}` : ""}`);
