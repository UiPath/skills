#!/usr/bin/env node
// Compares a finalized Case Management SDD with the draft it was finalized from, before the ready flip
// (references/design/case-review-and-conformance-guide.md § Finalizing a Case Draft, checklist items 20 and 30–33).
//
// Usage: node case-draft-parity.mjs <NAME>.draft.md <NAME>.md
// Exit 0 and "OK" when the final keeps the draft's: first heading form; stages in order, each with its kind
// (`### Stage <N>:` primary, `### Secondary Stage:` secondary); tasks in order under each stage; Case
// Variables rows by name; every `=js:` expression verbatim; every comparator + money amount of the draft as a `=js:`
// cell holding the numeral written out — on a line naming a draft persona, an expression that picks a `Role:`.
// In the final alone: every Tasks table row has its header's cell count, and a plain `**Recipient:** Role:<X>` names
// its task's Persona cell (checklist item 20). Exit 1 with one FAIL line per difference.
// Names compare with a trailing id suffix stripped, backticked or not: `(`t01`)`, `(t01)`.
import { existsSync, readFileSync } from "node:fs";

const STAGE = /^###\s+(Stage\s+\d+|Secondary\s+Stage|Exception\s+Stage):\s*(.+?)\s*$/;
const TASK = /^#####\s+Task\s+[^:\n]+:\s*(.+?)\s*$/;
const clean = (name) => name.replace(/\s+\(`?[A-Za-z][\w-]*`?\)\s*$/, "").trim();

function read(path) {
  if (!existsSync(path)) { console.error(`FAIL: ${path} not found`); process.exit(1); }
  return readFileSync(path, "utf8").replace(/\r/g, "");
}

/** [{ name, kind, tasks: [name] }] in document order. */
function inventory(text) {
  const stages = [];
  for (const line of text.split("\n")) {
    const s = line.match(STAGE);
    if (s) { stages.push({ name: clean(s[2]), kind: /^Stage/.test(s[1]) ? "primary" : "secondary", tasks: [] }); continue; }
    const t = line.match(TASK);
    if (t && stages.length) stages.at(-1).tasks.push(clean(t[1]));
  }
  // a `**Stage Kind:**` line overrides the heading form
  for (const st of stages) {
    const block = text.split(/^###\s+/m).find((b) => /^(?:Stage\s+\d+|Secondary\s+Stage|Exception\s+Stage):/.test(b) && clean(b.split("\n")[0].replace(/^[^:]+:\s*/, "")) === st.name);
    const k = [...new Set([...(block ?? "").matchAll(/^\*\*Stage Kind:\*\*\s*(primary|secondary)/gm)].map((m) => m[1]))];
    if (k.length === 1) st.kind = k[0];
    else if (k.length > 1) st.kind = "both primary and secondary";
  }
  return stages;
}

function variables(text) {
  const m = text.match(/^### Case Variables\s*\n([\s\S]*?)(?=^#{2,3} )/m);
  if (!m) return [];
  return m[1].split("\n").filter((l) => /^\|/.test(l) && !/^\|\s*-/.test(l)).slice(1)
    .map((l) => l.split("|")[1].trim().replace(/`/g, "")).filter(Boolean);
}

// an expression ends at its cell, its line or its code span
const expressions = (text) => [...new Set(text.match(/=js:[^|`\n]*[^|`\s]/g) ?? [])];

const [draftPath, finalPath] = process.argv.slice(2);
if (!draftPath || !finalPath) { console.error("usage: node case-draft-parity.mjs <NAME>.draft.md <NAME>.md"); process.exit(2); }
const draft = read(draftPath), final = read(finalPath);
const fails = [];

if (!/^# SDD — \S/.test(final.trimStart())) fails.push("first line is not '# SDD — <Case Name>'");

const want = inventory(draft), got = inventory(final);
for (let i = 0; i < Math.max(want.length, got.length); i++) {
  const w = want[i], g = got[i];
  if (!w) { fails.push(`stage ${i + 1}: '${g.name}' is not in the draft`); continue; }
  if (!g) { fails.push(`stage ${i + 1}: '${w.name}' is missing from the final`); continue; }
  if (w.name !== g.name) { fails.push(`stage ${i + 1}: draft '${w.name}', final '${g.name}'`); continue; }
  if (w.kind !== g.kind) fails.push(`stage '${w.name}': draft ${w.kind}, final ${g.kind}`);
  for (let j = 0; j < Math.max(w.tasks.length, g.tasks.length); j++) {
    if (w.tasks[j] !== g.tasks[j]) fails.push(`stage '${w.name}' task ${j + 1}: draft '${w.tasks[j] ?? "<none>"}', final '${g.tasks[j] ?? "<none>"}'`);
  }
}

const finalVars = new Set(variables(final));
for (const v of variables(draft)) if (!finalVars.has(v)) fails.push(`Case Variables: '${v}' is missing from the final`);

for (const e of expressions(draft)) if (!final.includes(e)) fails.push(`expression missing from the final: ${e}`);

// checklist item 20: a plain `Role:` Recipient names its task's Persona from the stage's Tasks table
const persona = new Map();
for (const table of final.match(/^\|[^\n]*\bTask Name\b[^\n]*\bPersona\b[^\n]*\|\n(?:\|[^\n]*\|\n?)+/gm) ?? []) {
  const rows = table.trim().split("\n").map((r) => r.split("|").slice(1, -1).map((c) => c.trim()));
  const ni = rows[0].indexOf("Task Name"), pi = rows[0].indexOf("Persona");
  for (const r of rows.slice(2)) {
    if (r.length !== rows[0].length) { fails.push(`Tasks table row '${r[ni] ?? r.join(" | ")}' has ${r.length} cells, its header ${rows[0].length}`); continue; }
    if (r[ni] && r[pi]) persona.set(clean(r[ni].replace(/`/g, "")), r[pi]);
  }
}
const blocks = final.split(/^(?=#{3,5} )/m);
for (const b of blocks) {
  const t = b.split("\n")[0].match(TASK);
  const rc = b.match(/^\*\*Recipient:\*\*\s*Role:\s*([^\n]+?)\s*$/m);
  if (!t || !rc) continue;
  const want = persona.get(clean(t[1]));
  if (want && !/^(system|—|-)$/i.test(want) && rc[1] !== want) fails.push(`task '${clean(t[1])}': Recipient Role:${rc[1]}, Persona ${want}`);
}

// checklist item 32: every comparator + money amount in the draft is a `=js:` cell in the final, the numeral written out
const UNIT = { k: 1e3, thousand: 1e3, m: 1e6, million: 1e6, b: 1e9, billion: 1e9 };
const THRESHOLD = /(?:≤|≥|<=?|>=?|\b(?:over|above|under|below|at least|at most|more than|less than|greater than|up to)\s+)\s*\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k|m|b|thousand|million|billion)?\b/gi;
const cells = (final.match(/=js:[^\n]*/g) ?? []).join("\n");
// a role-picking expression: the amount and a `Role:` on one =js: line (a Recipient, an Inputs cell)
const roleCells = (final.match(/=js:[^\n]*Role:[^\n]*/g) ?? []).join("\n");
const personas = (draft.match(/^### Personas\s*\n([\s\S]*?)(?=^#{2,3} )/m)?.[1] ?? "").split("\n")
  .filter((l) => /^\|/.test(l) && !/^\|\s*-/.test(l)).slice(1).map((l) => l.split("|")[1].trim()).filter(Boolean);
const seen = new Set();
for (const m of draft.matchAll(THRESHOLD)) {
  const amount = Math.round(Number(m[1].replace(/,/g, "")) * (UNIT[(m[2] ?? "").toLowerCase()] ?? 1));
  const line = draft.slice(draft.lastIndexOf("\n", m.index) + 1, draft.indexOf("\n", m.index));
  // a threshold on a line naming a persona picks who does the work: its home is a task's Recipient
  const picksRole = personas.some((p) => line.toLowerCase().includes(p.toLowerCase()));
  const key = `${amount}:${picksRole}`;
  if (seen.has(key)) continue;
  seen.add(key);
  const has = new RegExp(`(?<![\\d.])${amount}(?![\\d])`);
  if (picksRole && !has.test(roleCells)) {
    fails.push(`threshold '${m[0].trim()}' picks a role, and no =js: line holds ${amount} with a Role: (write the owning task's **Recipient:** as =js:vars.<amount> > ${amount} ? "Role:<above>" : "Role:<at or below>")`);
  } else if (!picksRole && !has.test(cells)) {
    fails.push(`threshold '${m[0].trim()}' has no =js: cell holding ${amount} in the final`);
  }
}

if (fails.length) {
  for (const f of fails) console.log(`FAIL: ${f}`);
  process.exit(1);
}
console.log(`OK: ${got.length} stages, ${got.reduce((n, s) => n + s.tasks.length, 0)} tasks, ${finalVars.size} variables and every draft =js: expression kept`);
