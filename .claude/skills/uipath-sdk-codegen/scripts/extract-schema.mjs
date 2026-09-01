#!/usr/bin/env node
/**
 * extract-schema — enumerate the case schema's closed unions PER SCHEMA VERSION,
 * from the executable artifact rather than from any hand-written header.
 *
 * WHY THIS EXISTS. `@uipath/case-schema` ships `dist/index.d.ts`, and it is a trap:
 * its build step is literally `cp packages/converter/src/index.d.ts dist/`, so it is
 * hand-maintained and pinned to whatever schema version someone last edited it at.
 * Three of three unions checked against the platform were wrong in it, each time
 * UNDERSTATING what the platform accepts:
 *
 *   CaseManagementNodeTaskType        header 10 members   zod accepts 11 (+external-workflow)
 *   SlaRule.unit                      header h|d|w|m      uip: min|h|d|w|m
 *   CaseManagementNodeExitRuleType    header omits exit-only, lists terminal/send-to-stage
 *                                     uip: exit-only Valid; terminal/send-to-stage Invalid
 *
 * The bundle (`dist/index.cjs`) is NOT minified — it carries the compiled zod source
 * complete with `// src/types/...` path comments. That is the enumerable source.
 *
 * Usage:
 *   node extract-schema.mjs [--bundle <path/to/@uipath/case-schema/dist/index.cjs>]
 *                           [--source <path/to/PO.Frontend/src/types/case-mgmt-zod>]
 *                           [--json]
 *
 * With --source it also reads MAINLINE zod (a sibling PO.Frontend clone) so you can
 * diff published-vs-mainline. Mainline members are NOT gaps: emitting a type the
 * installed converter rejects produces invalid caseplans. They are a forecast.
 */
import { readFileSync, existsSync } from 'node:fs';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const JSON_OUT = process.argv.includes('--json');
// Mainline zod is a FIRST-CLASS input, not an optional extra. Members that exist there
// but not in the validating bundle are PREVIEW: real, coming, and must never be emitted
// (they would produce caseplans the installed converter rejects) — but knowing about them
// stops a shipped-later capability from being mis-filed as a permanent platform limit.
// Three were mis-filed exactly that way before this was wired in.
const MAINLINE_DEFAULT = `${process.env.HOME ?? ''}/src/PO.Frontend/src/types/case-mgmt-zod`;
const noMain = process.argv.includes('--no-mainline');
let SOURCE = arg('--source', '');
if (!SOURCE && !noMain && existsSync(MAINLINE_DEFAULT)) SOURCE = MAINLINE_DEFAULT;

/**
 * Resolve the bundle that ACTUALLY VALIDATES, in authority order.
 *
 * `uip maestro case validate` does not load the repo's `@uipath/case-schema`. The
 * validating code is bundled inside `@uipath/maestro-tool`'s dist/tool.js, and its copy
 * is far newer than the one a downstream repo installs. Measured 2026-08-06:
 *
 *   maestro-tool 1.198.0 bundle   14 task types, 15 rules (has sla-status-change)
 *   repo @uipath/case-schema@0.859.0   11 task types, 14 rules (no sla-status-change)
 *
 * Auditing against the repo copy therefore UNDER-REPORTS by three task types and calls
 * shipped features "mainline-only". Default to the authority; fall back loudly.
 *
 * Note the versions do not agree with each other either: `uip --version` says 1.202.0
 * while the maestro-tool that performs case validation is 1.198.0 (re-measured
 * 2026-09-01; 1.200.0/1.198.0 on 2026-08-06 — launcher +4, validator +0). Record both.
 */
const HOME = process.env.HOME ?? '';
const CANDIDATES = [
  { path: `${HOME}/.bun/install/global/node_modules/@uipath/maestro-tool/dist/tool.js`, label: 'maestro-tool (AUTHORITY — what uip validates with)' },
  { path: `${HOME}/src/cli/node_modules/@uipath/case-schema/dist/index.cjs`, label: 'CLI dev checkout case-schema' },
  { path: 'typescript/node_modules/@uipath/case-schema/dist/index.cjs', label: 'repo case-schema (DOWNSTREAM — may lag badly)' },
];
let BUNDLE = arg('--bundle');
let BUNDLE_LABEL = 'explicit --bundle';
if (!BUNDLE) {
  const hit = CANDIDATES.find((c) => existsSync(c.path));
  if (hit) { BUNDLE = hit.path; BUNDLE_LABEL = hit.label; }
  else { BUNDLE = CANDIDATES[2].path; BUNDLE_LABEL = CANDIDATES[2].label; }
  if (hit && hit !== CANDIDATES[0]) {
    console.error(`⚠ maestro-tool bundle not found; falling back to ${hit.label}.`);
    console.error('  Numbers from a downstream copy under-report. Prefer the validating bundle.');
  }
}

if (!existsSync(BUNDLE)) {
  console.error(`extract-schema: bundle not found at ${BUNDLE}`);
  console.error('Run `npm ci` in typescript/ (needs NODE_AUTH_TOKEN), or pass --bundle.');
  process.exit(2);
}
const s = readFileSync(BUNDLE, 'utf8');
if (s.length < 100_000) {
  console.error(`extract-schema: ${BUNDLE} is only ${s.length} chars — refusing to report unions from it.`);
  console.error('A multi-file dist often has a small index.js and the real bundle beside it (e.g. tool.js).');
  process.exit(2);
}

/** Every `…SchemaV<n>` suffix present, i.e. the schema versions this build knows. */
const versions = [...new Set([...s.matchAll(/Schema(V\d+)\b/g)].map((m) => m[1]))]
  .sort((a, b) => Number(a.slice(1)) - Number(b.slice(1)));

/** Task-type literals per version: `var …TaskXSchemaV13 = Base.extend({ type: literal("x") …`. */
const tasksByVersion = {};
for (const m of s.matchAll(/var\s+\w*Task\w*?Schema(V\d+)\s*=\s*\w+\.extend\(\{\s*type:\s*\w+\.literal\("([a-z0-9-]+)"\)/g)) {
  (tasksByVersion[m[1]] ??= new Set()).add(m[2]);
}
/** Rule literals: `rule: z.literal("…")`. Not version-suffixed consistently — collect flat. */
const rules = [...new Set([...s.matchAll(/rule:\s*\w+\.literal\("([a-z0-9-]+)"\)/g)].map((m) => m[1]))].sort();
/** Named enums we care about, by the field they sit on. */
const enumFor = (field) => {
  const m = new RegExp(`${field}:\\s*\\w+\\.enum\\(\\[([^\\]]+)\\]`).exec(s);
  return m ? [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1]) : null;
};

const latest = Object.keys(tasksByVersion).sort((a, b) => Number(b.slice(1)) - Number(a.slice(1)))[0];
const out = {
  bundle: BUNDLE,
  bundleLabel: BUNDLE_LABEL,
  schemaVersionsPresent: versions,
  latestTaskSchemaVersion: latest ?? null,
  taskTypesByVersion: Object.fromEntries(Object.entries(tasksByVersion).map(([v, set]) => [v, [...set].sort()])),
  ruleLiterals: rules,
  enums: { unit: enumFor('unit'), scope: enumFor('scope'), type: enumFor('type') },
};

if (SOURCE) {
  if (!existsSync(SOURCE)) {
    console.error(`extract-schema: --source path not found: ${SOURCE}`);
    process.exit(2);
  }
  const walk = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(join(dir, e.name)) : e.name.endsWith('.ts') && !e.name.endsWith('.test.ts') ? [join(dir, e.name)] : []);
  const src = walk(SOURCE).map((f) => readFileSync(f, 'utf8')).join('\n');
  out.mainline = {
    source: SOURCE,
    taskTypes: [...new Set([...src.matchAll(/type:\s*z\.literal\("([a-z0-9-]+)"\)/g)].map((m) => m[1]))].sort(),
    ruleLiterals: [...new Set([...src.matchAll(/rule:\s*z\.literal\("([a-z0-9-]+)"\)/g)].map((m) => m[1]))].sort(),
    schemaVersions: [...new Set([...src.matchAll(/SchemaV(\d+)\b/g)].map((m) => Number(m[1])))].sort((a, b) => a - b),
  };
  const pub = new Set(out.taskTypesByVersion[latest] ?? []);
  out.mainline.preview = out.mainline.taskTypes.filter((t) => !pub.has(t));
  out.mainline.previewRules = (out.mainline.ruleLiterals ?? []).filter((r) => !rules.includes(r));
}

if (JSON_OUT) { console.log(JSON.stringify(out, null, 2)); process.exit(0); }

console.log(`bundle: ${BUNDLE}`);
console.log(`source: ${BUNDLE_LABEL}`);
console.log(`schema versions present: ${versions.join(', ')}`);
console.log(`\ntask types by version (latest = ${latest}):`);
for (const [v, list] of Object.entries(out.taskTypesByVersion)) console.log(`  ${v.padEnd(5)} ${list.length}: ${list.join(', ')}`);
console.log(`\nrule literals (${rules.length}): ${rules.join(', ')}`);
for (const [k, v] of Object.entries(out.enums)) if (v) console.log(`enum ${k}: ${v.join(' | ')}`);
if (out.mainline) {
  console.log(`\nmainline (${SOURCE}):`);
  console.log(`  schema versions: up to V${Math.max(...out.mainline.schemaVersions)}`);
  console.log(`  task types (${out.mainline.taskTypes.length}): ${out.mainline.taskTypes.join(', ')}`);
  console.log(`  rules (${out.mainline.ruleLiterals.length}): ${out.mainline.ruleLiterals.join(', ')}`);
  console.log(`  PREVIEW task types — real but unpublished, do NOT emit: ${out.mainline.preview.join(', ') || '(none)'}`);
  console.log(`  PREVIEW rules: ${out.mainline.previewRules.join(', ') || '(none)'}`);
  console.log('  Preview members are not gaps and not limits — they are scheduled. Record, do not emit.');
}
console.log('\nReminder: this enumerates. It does not prove the platform accepts a member.');
console.log('Confirm with `uip maestro case validate` before generating a builder method.');
