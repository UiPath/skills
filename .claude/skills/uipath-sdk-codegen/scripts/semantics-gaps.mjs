#!/usr/bin/env node
/**
 * semantics-gaps — "what don't we know yet?"
 *
 * The semantics file is hand-seeded, so it goes stale silently. This reports what is
 * missing or expired and emits a work list in three buckets, ORDERED BY HOW THEY MUST
 * BE ANSWERED. That order is the point:
 *
 *   1. PROBE      — an artifact can decide it. Always prefer this.
 *   2. DOCS       — a document states it; still needs a probe to become 'confirmed'.
 *   3. INTERVIEW  — only intent/policy/roadmap, which no artifact carries.
 *
 * Never interview for something probeable. A human recalling platform behaviour is how
 * this repo produced its two worst wrong answers — both times the recollection was
 * confident, agreed with, and false.
 *
 *   node semantics-gaps.mjs [--json] [--probe-plan]
 *
 * --probe-plan prints copy-pasteable probe cases for every unprobed cell.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const SKILL = join(HERE, '..');
const SEM_PATH = join(SKILL, 'semantics', 'case-semantics.json');
const sem = JSON.parse(readFileSync(SEM_PATH, 'utf8'));
const JSON_OUT = process.argv.includes('--json');
const PLAN = process.argv.includes('--probe-plan');

const sh = (cmd, args) => { try { return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { return null; } };

// ── 1. provenance staleness ──────────────────────────────────────────────────
// Recorded-vs-live. Every one of these has moved during a single working session.
const live = {
  cli: (sh('uip', ['--version']) || '').split('\n').pop() || 'unknown',
  package: sh('node', ['-p', "require('./typescript/node_modules/@uipath/case-schema/package.json').version"]) || 'unknown',
  sdkEmits: (sh('grep', ['-o', "_version = '[0-9.]*'", 'typescript/sdk/src/case/case-sdk.ts']) || '').replace(/.*'([^']*)'.*/, '$1') || 'unknown',
};
const recorded = { cli: (sem.$provenance.cli || '').replace(/^uip\s*/, ''), package: (sem.$provenance.package || '').split('@').pop(), sdkEmits: sem.$provenance.schemaEmitted };
const drift = Object.entries(live)
  .filter(([k, v]) => v !== 'unknown' && !String(recorded[k] ?? '').includes(v) && !v.includes(String(recorded[k] ?? '')))
  .map(([k, v]) => ({ field: k, recorded: recorded[k], live: v }));

// ── 2. schema members with no semantics entry ────────────────────────────────
let schema = null;
try { schema = JSON.parse(execFileSync('node', [join(HERE, 'extract-schema.mjs'), '--json'], { encoding: 'utf8' })); } catch { /* reported below */ }
const latest = schema?.latestTaskSchemaVersion;
const schemaTasks = latest ? schema.taskTypesByVersion[latest] : [];
const unknownTasks = schemaTasks.filter((t) => !sem.taskKinds[t]);
const unconfirmedTasks = Object.entries(sem.taskKinds).filter(([, v]) => v.status !== 'confirmed').map(([k]) => k);

// ── 3. unprobed placement cells ──────────────────────────────────────────────
const slots = sem.rulePlacement.slots;
const knownRules = [...new Set([...(schema?.ruleLiterals ?? []), ...sem.rulePlacement.cells.map((c) => c.rule)])].sort();
const probed = new Set(sem.rulePlacement.cells.map((c) => `${c.rule}@${c.slot}`));
const unprobedCells = knownRules.flatMap((r) => slots.filter((s) => !probed.has(`${r}@${s}`)).map((s) => ({ rule: r, slot: s })));

// ── 4. things only a human can answer ────────────────────────────────────────
// Deliberately short. Anything probeable must NOT appear here.
const interview = [];
if (drift.some((d) => d.field === 'sdkEmits') || live.sdkEmits !== 'unknown') {
  interview.push({
    id: 'version-pin-intent',
    question: `The SDK emits schema ${live.sdkEmits} while the installed package understands ${sem.$provenance.schemaSupportedByPackage} and mainline is ${sem.$provenance.mainline}. Is staying pinned deliberate, or inertia?`,
    whyHuman: 'Roadmap/intent. No artifact records why a version was chosen.',
    consequence: 'If inertia, the V21..V31 diff (mainline reached V31 on 2026-09-01) is a list of things we currently cannot express. Re-pinning also has migration cost (V27 requires escalation displayName).',
  });
}
if (unknownTasks.length) {
  interview.push({
    id: 'task-kind-scope',
    question: `Schema declares ${unknownTasks.join(', ')} with no semantics entry. Are any of these intentionally NOT authorable from this SDK (editor-internal), rather than gaps?`,
    whyHuman: 'Product scope. The schema cannot say whether a type is meant for authors.',
    consequence: 'Out-of-scope types should carry an explicit allowlist entry with a reason, not be reported as permanent gaps.',
  });
}
for (const u of sem.knownUnknowns) {
  interview.push({ id: u.id, question: u.question, whyHuman: u.why, consequence: `Settled by: ${u.settledBy}`, workaround: u.workaround });
}

const report = { drift, unknownTasks, unconfirmedTasks, unprobedCells, interview, schemaAvailable: Boolean(schema) };

if (JSON_OUT) { console.log(JSON.stringify(report, null, 2)); process.exit(0); }

console.log('── provenance drift ──');
if (!drift.length) console.log('  none — recorded versions match live.');
for (const d of drift) console.log(`  ${d.field}: recorded "${d.recorded}" vs live "${d.live}"  -> re-probe and restamp`);

console.log('\n── PROBE (an artifact can decide these) ──');
if (!schema) console.log('  extract-schema failed; cannot enumerate. Run npm ci in typescript/.');
if (unknownTasks.length) console.log(`  task types in schema, no semantics entry (${unknownTasks.length}): ${unknownTasks.join(', ')}`);
if (unconfirmedTasks.length) console.log(`  semantics entries not yet confirmed (${unconfirmedTasks.length}): ${unconfirmedTasks.join(', ')}`);
console.log(`  unprobed placement cells: ${unprobedCells.length} of ${knownRules.length * slots.length} (rule x slot)`);
if (unprobedCells.length) {
  const byRule = {};
  for (const c of unprobedCells) (byRule[c.rule] ??= []).push(c.slot);
  for (const [r, ss] of Object.entries(byRule).slice(0, 8)) console.log(`    ${r.padEnd(28)} ${ss.join(', ')}`);
  if (Object.keys(byRule).length > 8) console.log(`    … ${Object.keys(byRule).length - 8} more rules`);
}

console.log('\n── INTERVIEW (no artifact can answer these) ──');
for (const q of interview) {
  console.log(`  [${q.id}]`);
  console.log(`    Q: ${q.question}`);
  console.log(`    why a human: ${q.whyHuman}`);
  console.log(`    matters because: ${q.consequence}`);
}
console.log('\n  Answers are recorded with status "asserted" — NEVER "confirmed".');
console.log('  A human statement about platform behaviour is a hypothesis to probe, not evidence.');

if (PLAN) {
  console.log('\n── probe plan ──');
  console.log('For each cell, emit the minimal case from references/verify.md with the rule in that slot,');
  console.log('run ./compile.sh, and record the VERBATIM verdict. Read the verdict class:');
  console.log('  "Invalid input" / "Invalid option"  -> member NOT recognised');
  console.log('  a semantic complaint                -> member IS recognised, payload incomplete (a PASS)');
  console.log('\nThen write results back:');
  console.log('  node semantics-update.mjs --cell "<rule>@<slot>" --legal <true|false> --verdict "<text>"');
}
