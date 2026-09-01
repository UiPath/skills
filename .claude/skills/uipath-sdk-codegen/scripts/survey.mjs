#!/usr/bin/env node
/**
 * survey — ONE command. Runs every cheap tier in cost order, then tells you what is left.
 *
 * The skill grew to eleven scripts and eight documented commands, and nothing enforced the
 * order they should run in. That is not a hypothetical cost: this program probed a validator
 * (tier 4, minutes per cell) for a day to answer questions the fixtures (tier 2, seconds)
 * answer outright, having already written down that fixtures come first. An ordering rule
 * that lives only in prose gets run backwards.
 *
 * So: tiers 1 and 2 are automatic and always run. Anything they cannot settle is printed as
 * a NEXT STEP naming the exact slower command — so the expensive tiers are reached
 * deliberately, and only for what is genuinely unanswered.
 *
 *   node survey.mjs              # where do I stand?
 *   node survey.mjs --json
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SKILL = join(HERE, '..');
const JSON_OUT = process.argv.includes('--json');
const C = process.stdout.isTTY
  ? { g: (s) => `\x1b[32m${s}\x1b[0m`, r: (s) => `\x1b[31m${s}\x1b[0m`, y: (s) => `\x1b[33m${s}\x1b[0m`,
      d: (s) => `\x1b[2m${s}\x1b[0m`, b: (s) => `\x1b[1m${s}\x1b[0m` }
  : { g: (s) => s, r: (s) => s, y: (s) => s, d: (s) => s, b: (s) => s };

const run = (script, args = []) => {
  try {
    return { ok: true, out: execFileSync('node', [join(HERE, script), ...args],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 120_000 }) };
  } catch (e) {
    return { ok: false, out: `${String(e.stdout ?? '')}${String(e.stderr ?? '')}`, code: e.status };
  }
};

const report = { tiers: {}, next: [] };

// ── tier 1 · ms · the schema and the slot grid ───────────────────────────────
const schema = run('extract-schema.mjs', ['--json']);
if (schema.ok) {
  const d = JSON.parse(schema.out);
  const latest = d.latestTaskSchemaVersion;
  report.tiers.schema = { version: latest, taskTypes: (d.taskTypesByVersion?.[latest] ?? []).length,
    rules: (d.ruleLiterals ?? []).length, bundle: d.bundleLabel };
} else {
  report.tiers.schema = { error: schema.out.trim().split('\n')[0] };
  report.next.push('FIX tier 1 — extract-schema failed; nothing downstream is trustworthy until it runs');
}

const grid = run('extract-scheduler-grid.mjs', ['--json']);
if (grid.ok) {
  const d = JSON.parse(grid.out);
  report.tiers.grid = { unreachable: d.unreachable.length, contradictions: d.contradictions?.length ?? 0,
    slots: Object.keys(d.slots ?? {}).length };
} else {
  report.tiers.grid = { error: grid.out.trim().split('\n')[0] };
  report.next.push('INSTALL the slot grid — cd typescript && NODE_AUTH_TOKEN=$(gh auth token) npm i -D @uipath/scheduler-types');
}

// ── tier 2 · seconds · required behaviour ───────────────────────────────────
const fx = run('read-fixtures.mjs', ['--json']);
if (fx.ok) {
  const d = JSON.parse(fx.out);
  const pairs = d.scenarios.reduce((n, s) => n + s.pairs.length, 0);
  const negatives = d.scenarios.reduce((n, s) => n + s.pairs.filter((p) => p.negative).length, 0);
  const unparsed = d.scenarios.reduce((n, s) => n + s.pairs.filter((p) => p.unknownKeys?.length).length, 0);
  report.tiers.fixtures = { scenarios: d.scenarios.length, pairs, negatives, unparsed };
  if (unparsed) report.next.push(`FIX read-fixtures — ${unparsed} output(s) have unrecognised keys; do NOT read those as negatives`);
} else {
  report.tiers.fixtures = { error: fx.out.trim().split('\n')[0] };
  report.next.push('CLONE dmnscheduler to ~/src/dmnscheduler — tier 2 is the cheapest behaviour evidence and it is unavailable');
}

// ── what semantics already records, and what it does not ────────────────────
const semPath = join(SKILL, 'semantics', 'case-semantics.json');
if (existsSync(semPath)) {
  const sem = JSON.parse(readFileSync(semPath, 'utf8'));
  const kinds = Object.entries(sem.taskKinds ?? {});
  const confirmed = kinds.filter(([, k]) => k.status === 'confirmed');
  const unconfirmed = kinds.filter(([, k]) => k.status !== 'confirmed');
  report.semantics = { confirmed: confirmed.length, total: kinds.length,
    unconfirmed: unconfirmed.map(([t]) => t),
    unknowns: (sem.knownUnknowns ?? []).length,
    asserted: kinds.filter(([, k]) => k.status === 'asserted').length };
  if (unconfirmed.length) {
    report.next.push(`PROBE (tier 4, slow) only what tiers 1-2 left open: ${unconfirmed.map(([t]) => t).join(', ')} — node scripts/probe-task-kinds.mjs`);
  }
  if ((sem.knownUnknowns ?? []).length) {
    report.next.push(`ASK a human (tier 6) for ${(sem.knownUnknowns ?? []).length} open unknown(s) — node scripts/semantics-gaps.mjs`);
  }
}

// ── resource discovery is environment state, reported separately ─────────────
const disc = run('discover-resources.mjs', ['--json']);
report.tiers.resources = disc.ok
  ? { ok: true, kinds: Object.fromEntries(Object.entries(JSON.parse(disc.out).kinds).map(([k, v]) => [k, v.count])) }
  : { ok: false, blocked: disc.out.trim().split('\n').filter((l) => l.includes('✗')).join('; ') || 'unavailable' };
if (!disc.ok) report.next.push('REFRESH the registry cache before referencing any resource — uip maestro case registry pull --force');

if (JSON_OUT) { console.log(JSON.stringify(report, null, 2)); process.exit(0); }

const ok = (b) => (b ? C.g('✓') : C.r('✗'));
console.log(C.b('\nwhere you stand') + C.d('  — cheap tiers run automatically, in cost order\n'));

const s = report.tiers.schema;
console.log(`  ${ok(!s.error)} ${C.b('tier 1')} schema        ${s.error ?? `${s.version} · ${s.taskTypes} task types · ${s.rules} rules`}`);
console.log(`    ${C.d(s.bundle ?? '')}`);
const g = report.tiers.grid;
console.log(`  ${ok(!g.error)} ${C.b('tier 1')} slot grid     ${g.error ?? `${g.slots} slots · ${g.unreachable} unreachable cells · ${g.contradictions} contradictions`}`);
const f = report.tiers.fixtures;
console.log(`  ${ok(!f.error)} ${C.b('tier 2')} fixtures      ${f.error ?? `${f.scenarios} scenarios · ${f.pairs} input/output pairs · ${f.negatives} negative cases`}`);
const r = report.tiers.resources;
console.log(`  ${ok(r.ok)} ${C.d('env')}    resources     ${r.ok ? Object.entries(r.kinds).map(([k, v]) => `${k} ${v}`).join(' · ') : C.y(r.blocked)}`);

if (report.semantics) {
  const m = report.semantics;
  console.log(`\n  ${C.b('recorded')}  ${m.confirmed}/${m.total} task kinds confirmed · ${m.unknowns} open unknown(s) · ${m.asserted} asserted`);
}

console.log(C.b('\nnext, in this order') + C.d('  — everything below costs minutes or a person\n'));
if (!report.next.length) console.log(`  ${C.g('nothing outstanding')} — tiers 1-2 settled everything currently recorded\n`);
for (const n of report.next) console.log(`  → ${n}`);
console.log(C.d('\n  Probing is TIER 4. Reach for it for what the cheap tiers structurally cannot answer'));
console.log(C.d('  (shape questions only), not first. See references/sources.md.\n'));
