#!/usr/bin/env node
/**
 * emit-sdk — generate the version-pinned LEAVES of the fluent SDK, plus the router.
 *
 * Generates: closed unions, per-task-kind data interfaces + defaults, and a router that
 * dispatches by schema version. Does NOT generate the fluent grammar or check.ts — the
 * schema carries shape, not semantics (see references/generate.md).
 *
 * Inputs, in trust order:
 *   1. extract-schema.mjs  — WHAT EXISTS, per schema version, from the shipped bundle
 *   2. semantics/case-semantics.json — WHAT IT MEANS: probe verdicts, defaults, JSDoc
 *
 * A member is emitted only when the schema HAS it and semantics marks it `confirmed`.
 * Enumerated-but-unprobed members are listed in meta.json and omitted from code — an
 * omission is honest; a commented-out method invites someone to uncomment it.
 *
 *   node emit-sdk.mjs [--out <dir>] [--version V13] [--check] [--json]
 *
 * --check re-emits into memory and diffs against what is on disk, exiting 1 when stale
 * (the same contract as gen-case-skill.mjs --check, so CI can gate it).
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const SKILL = join(HERE, '..');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const CHECK = process.argv.includes('--check');
const OUT = arg('--out', 'typescript/sdk/src/case/generated');

// ── inputs ───────────────────────────────────────────────────────────────────
let schema;
try {
  schema = JSON.parse(execFileSync('node', [join(HERE, 'extract-schema.mjs'), '--json'], { encoding: 'utf8' }));
} catch (e) {
  console.error('emit-sdk: extract-schema failed — cannot emit without knowing what exists.');
  console.error(String(e.stderr || e.message).trim().split('\n').slice(0, 3).join('\n'));
  process.exit(2);
}
const sem = JSON.parse(readFileSync(join(SKILL, 'semantics', 'case-semantics.json'), 'utf8'));

const targetVersion = arg('--version', schema.latestTaskSchemaVersion);
const schemaTasks = schema.taskTypesByVersion[targetVersion];
if (!schemaTasks) {
  console.error(`emit-sdk: schema version ${targetVersion} not present in the bundle.`);
  console.error(`Available: ${Object.keys(schema.taskTypesByVersion).join(', ')}`);
  console.error('Refusing to guess — an unknown pair must fail loudly, not fall back.');
  process.exit(2);
}

// ── provenance ───────────────────────────────────────────────────────────────
// Stamped into every file. A generated file whose provenance you cannot reconstruct is
// unreviewable: you cannot tell a missing member from a stale run.
const p = sem.$provenance;
const header = (what) => `/**
 * GENERATED — do not edit. Regenerate:
 *   node .claude/skills/uipath-sdk-codegen/scripts/emit-sdk.mjs
 *
 * ${what}
 *
 * cli:      ${p.cli}
 * package:  ${p.package}
 * schema:   ${targetVersion} (emitting) | package understands ${p.schemaSupportedByPackage} | sdk emits ${p.schemaEmitted}
 * mainline: ${p.mainline} — forecast only, NOT generated
 * probed:   ${p.probedOn}
 *
 * Only members the schema declares AND semantics marks 'confirmed' (probe-verified
 * against \`uip maestro case validate\`) are emitted. See meta.json for what was skipped.
 */
`;

/** Render a JSDoc block, wrapping at ~92 cols so generated docs stay readable. */
function jsdoc(lines, indent = '') {
  const flat = (Array.isArray(lines) ? lines : [lines]).filter(Boolean);
  if (!flat.length) return '';
  const wrapped = flat.flatMap((l) => {
    const out = []; let cur = '';
    for (const w of String(l).split(/\s+/)) {
      if ((cur + ' ' + w).trim().length > 92) { out.push(cur.trim()); cur = w; } else cur += ' ' + w;
    }
    if (cur.trim()) out.push(cur.trim());
    return out.length ? out : [''];
  });
  return `${indent}/**\n${wrapped.map((l) => `${indent} * ${l}`.trimEnd()).join('\n')}\n${indent} */\n`;
}

/**
 * JSDoc lines for the converter's `serviceType`, which splits task kinds in two and must not
 * be rendered with one template. Where the converter assigns unconditionally, telling an
 * author to "prefer passing it explicitly" is wrong — the platform overwrites whatever they
 * pass. Where it merely falls back, the value IS the author's (sync-vs-async decides whether
 * the case waits), so state it.
 */
function serviceTypeDoc(k) {
  const c = k.converterServiceType;
  if (!c) return [];
  return c.overridable
    ? ['', `@default serviceType \`${c.value}\` — a converter FALLBACK, not a rule. The author owns`,
       'this value, so the builder emits it explicitly rather than inheriting a guess.']
    : ['', `NOTE serviceType is assigned by the converter as \`${c.value}\` and is NOT yours to`,
       'set — a value passed here is overwritten. The builder deliberately emits none.'];
}

// ── decide what is emittable ─────────────────────────────────────────────────
const kinds = [];
const skipped = [];
for (const t of schemaTasks) {
  const s = sem.taskKinds[t];
  if (s?.status === 'confirmed') kinds.push({ type: t, ...s });
  else skipped.push({ type: t, reason: s ? `semantics status '${s.status}'` : 'no semantics entry — unprobed' });
}

// ── unions.ts ────────────────────────────────────────────────────────────────
const placementDoc = sem.rulePlacement.cells
  .filter((c) => c.status === 'confirmed')
  .map((c) => `- \`${c.rule}\` @ ${c.slot}: ${c.legal ? 'LEGAL' : 'ILLEGAL'} — ${c.verdict}`);

const unionsTs = `${header('Closed unions lifted from the schema, with probe-verified semantics.')}
${jsdoc([
  'Schema task types confirmed for this version.',
  '',
  'Exhaustive by construction for the emitted schema version — this list is generated,',
  'so a member cannot silently go missing the way a hand-maintained table can.',
])}export type GeneratedTaskType =
${kinds.map((k) => `  | '${k.type}'`).join('\n') || "  | never"};

${jsdoc([
  'Rule placement verified against `uip maestro case validate`.',
  '',
  'Placement is NOT in the schema — every rule is structurally valid everywhere, and the',
  'platform rejects illegal combinations at a layer no type expresses. Each entry below',
  'carries the verdict text that established it.',
  '',
  ...placementDoc,
])}export const RULE_PLACEMENT_VERIFIED = ${JSON.stringify(
  sem.rulePlacement.cells.filter((c) => c.status === 'confirmed').map((c) => ({ rule: c.rule, slot: c.slot, legal: c.legal, verdict: c.verdict })),
  null, 2,
)} as const;
`;

// ── task-kinds.ts ────────────────────────────────────────────────────────────
const pascal = (s) => s.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join('');
const taskKindsTs = `${header('Per-task-kind data shapes and platform defaults.')}
${kinds.map((k) => {
  const defaults = Object.entries(k.defaults ?? {});
  return `${jsdoc([
    k.doc,
    ...serviceTypeDoc(k),
    ...(k.reuse ? ['', k.reuse] : []),
    ...(k.guidance ? ['', k.guidance] : []),
    '',
    `Schema shape: ${k.dataShape}`,
    `Available from schema ${k.minSchemaVersion}. Verified: ${p.probedOn}.`,
  ])}export interface ${pascal(k.type)}Data {
  /** Published name of the referenced resource. */
  name: string;
  /** Orchestrator folder path. */
  folderPath: string;
${k.converterServiceType?.overridable ? `  /** Converter falls back to \`${k.converterServiceType.value}\`; the builder emits it explicitly. */\n  serviceType?: string;` : ''}
  /** Reuses the same \`UiPathBindingJsonSchema\` mechanism \`.connector()\` resolves. */
  bindings?: unknown[];
}`;
}).join('\n\n')}

${jsdoc(['What `serviceType` the CONVERTER assigns per task kind, and whether the author may',
  'override it. `overridable: false` means the platform overwrites anything we emit — the',
  'builder emits nothing for those. Read from the converter, not guessed.'])}export const CONVERTER_SERVICE_TYPE = ${JSON.stringify(Object.fromEntries(kinds.filter((k) => k.converterServiceType).map((k) => [k.type, k.converterServiceType])), null, 2)} as const;

${jsdoc(['Builder method name per schema task type — the hand-written grammar wires these.'])}export const TASK_KIND_METHODS = ${JSON.stringify(Object.fromEntries(kinds.map((k) => [k.type, k.builderMethod])), null, 2)} as const;
`;

// ── placement.ts — the checker's table, generated from probe verdicts ────────
// This is the "three consumers, one source" promise made good. check.ts previously
// hand-maintained an ILLEGAL array with ONE entry; the probe grid establishes 13, each
// carrying the verbatim uip verdict. Hand-maintaining it also went wrong in the other
// direction once: an early table listed adhoc as task-entry-only and rejected plans the
// platform accepts.
const illegal = sem.rulePlacement.cells
  .filter((c) => c.legal === false && c.status === 'confirmed')
  .sort((a, b) => (a.rule + a.slot).localeCompare(b.rule + b.slot));
const discouraged = (sem.discouraged ?? []);

const placementTs = `${header("Rule placement — generated from probe verdicts. check.ts imports this.")}
${jsdoc([
  'Placements the platform REJECTS. Every entry was probed against',
  '`uip maestro case validate` and carries the verbatim verdict.',
  '',
  'ONLY these may be hard errors. The grid found the validator accepts',
  `${sem.rulePlacement.cells.filter((c) => c.legal).length} of ${sem.rulePlacement.cells.length} probed combinations,`,
  'so placement is largely UNENFORCED and the tables in the skill docs are',
  'authoring guidance, not validator behaviour. Widening this list requires a',
  'probe verdict, not an opinion.',
])}export const ILLEGAL_PLACEMENTS = ${JSON.stringify(
  illegal.map((c) => ({ rule: c.rule, slot: c.slot, verdict: c.verdict, verdictClass: c.verdictClass })),
  null, 2,
)} as const;

${jsdoc([
  'Placements the platform ACCEPTS but the authoring guidance advises against.',
  'Legality and advisability are different axes — warn, never hard-error.',
])}export const DISCOURAGED_PLACEMENTS = ${JSON.stringify(
  discouraged.map((d) => ({ id: d.id, claim: d.claim, source: d.source })),
  null, 2,
)} as const;

${jsdoc(['Probed cells, for tooling that wants the full grid rather than just the rejections.'])}export const PROBED_CELL_COUNT = ${sem.rulePlacement.cells.length};

${(() => {
  const sr = sem.schedulerReachability;
  if (!sr) {
    return `// No schedulerReachability in semantics — run:\n`
      + `//   node .claude/skills/uipath-sdk-codegen/scripts/extract-scheduler-grid.mjs --write\n`
      + `export const UNREACHABLE_PLACEMENTS = [] as const;\n`
      + `export const SCHEDULER_GRID_AVAILABLE = false;\n`;
  }
  const gaps = sr.unreachable.filter((u) => u.agreement === 'silent-gap');
  return `${jsdoc([
    'Placements the validator ACCEPTS but the SCHEDULER CANNOT EVALUATE.',
    '',
    `A THIRD verdict class, deliberately separate from ILLEGAL_PLACEMENTS above.`,
    'Those are validator-rejected — the platform tells you. These validate clean,',
    'pack, publish, and then quietly never fire: no layer between authoring and',
    'execution objects, so our checker is the only gate positioned to catch them.',
    '',
    `Derived from @uipath/scheduler-types ${sr.$provenance.packageVersion ?? '?'} —`,
    "the executing layer's own per-slot `oneOf` unions, pinned by package-lock.",
    'Regenerate with `extract-scheduler-grid.mjs --write`; never hand-edit.',
    '',
    `Evidence class: ${sr.$evidenceClass} (source-read). Weaker than a probe verdict:`,
    'it proves what the scheduler admits, not that a plan of ours reached it. The',
    'authoring-name mapping was read out of the PO.Frontend converter, not exercised.',
    '',
    `Coherence: ${sr.contradictions.length} contradictions against the probe grid`,
    '(expected zero — the scheduler should be strictly stricter than the validator).',
  ])}export const UNREACHABLE_PLACEMENTS = ${JSON.stringify(
    gaps.map((u) => ({ rule: u.rule, slot: u.slot, schedulerType: u.schedulerType, probeVerdict: u.probeVerdict })),
    null, 2,
  )} as const;

${jsdoc([
    'What each slot admits downstream, in the scheduler\'s own vocabulary.',
    'For diagnostics that want to say WHY a placement is unreachable.',
  ])}export const SCHEDULER_SLOT_ADMITS = ${JSON.stringify(sr.slotAdmits, null, 2)} as const;

${jsdoc(['Authoring rule name -> scheduler condition type. NOT one-to-one: selected-* and',
    'required-* pairs collapse onto one type, so they are reachable or not together.'])}export const SCHEDULER_RULE_MAP = ${JSON.stringify(sr.ruleMap, null, 2)} as const;

${jsdoc(['Rules with no cell-wise scheduler target, and why. Excluded from the grid rather',
    'than guessed — an uncheckable cell reads unknown, never reachable.'])}export const SCHEDULER_UNCHECKED_RULES = ${JSON.stringify(sr.excludedRules, null, 2)} as const;

export const SCHEDULER_GRID_AVAILABLE = true;

${(() => {
  // ── rung 1: the same grid, as TYPES ─────────────────────────────────────────
  // UNREACHABLE_PLACEMENTS above is a table a checker reads (rung 3). This is the same
  // fact expressed so the wrong call cannot be written (rung 1): one rule-name union per
  // slot, which the builder's slot methods accept instead of the full CaseRuleType.
  //
  // A rule is PERMITTED at a slot when the scheduler admits its condition type, OR when
  // we cannot check it at all. Uncheckable is not illegal — narrowing a rule out on the
  // strength of "we didn't model it" would encode our ignorance as a platform constraint,
  // which is the counter-rule this design explicitly forbids.
  const allRules = [...new Set(sem.rulePlacement.cells.map((c) => c.rule))].sort();
  const unchecked = new Set(Object.keys(sr.excludedRules));
  const gapSet = new Set(sr.unreachable.map((u) => `${u.rule}@${u.slot}`));
  const slots = Object.keys(sr.slotAdmits);
  const perSlot = Object.fromEntries(slots.map((slot) => [
    slot,
    allRules.filter((r) => unchecked.has(r) || !gapSet.has(`${r}@${slot}`)),
  ]));
  const union = (rs) => rs.map((r) => `'${r}'`).join('\n  | ');
  return `${jsdoc([
    'Rule names each slot may carry, as a TYPE — so an unreachable placement is a',
    'compile error at the call site rather than a checker finding after the fact.',
    '',
    'This is the same grid as UNREACHABLE_PLACEMENTS, moved one rung up: there is no',
    'diagnostic to read because there is no state to report. Prefer this. The table',
    'remains for tooling that inspects plans it did not author (decompile, review).',
    '',
    'A rule is permitted here when the scheduler admits its condition type OR when we',
    `cannot check it (${[...unchecked].join(', ')} — see SCHEDULER_UNCHECKED_RULES).`,
    'Uncheckable is not illegal; excluding it would encode our ignorance as a limit.',
  ])}export interface SlotRules {
${slots.map((s) => `  '${s}':\n  | ${union(perSlot[s])};`).join('\n')}
}

${jsdoc([
    'Slot names, for a caller that wants to iterate them.',
    '',
    'NOTE what is deliberately NOT here: the argument type for a slot method. That would',
    'need `CaseRule`, and generated leaves must not depend on the hand-written grammar.',
    'The generated half owns the FACTS (which rule names each slot admits); case-sdk.ts',
    'composes them with its own types:',
    '',
    "  type RuleArg<S extends keyof SlotRules> =",
    '    | CaseRule<SlotRules[S]>',
    '    | CaseRule<SlotRules[S]>[];',
    '',
    'A structural mirror of CaseRule was tried here instead and did not typecheck — the',
    'mirror is not the type the builder actually stores.',
  ])}export type CaseSlot = keyof SlotRules;
`;
})()}`;
})()}`;

// ── builder methods for confirmed task kinds ─────────────────────────────────
// The leaves of the fluent surface. The grammar (chaining, build()) stays hand-written;
// this emits one method per confirmed kind with the JSDoc that reaches the skill doc.
const methodsTs = `${header('Task-kind builder methods — one per probe-confirmed schema task type.')}
${jsdoc([
  'Coverage contract the hand-written TaskBuilder implements. Generated so a probe-confirmed',
  'schema task type cannot exist WITHOUT a builder method: `tsc` refuses to compile until one',
  'does. Rung 2 of "make illegal states unrepresentable" — a compile error cannot be skipped',
  'the way an audit script can.',
  '',
  'It asserts EXISTENCE, not signatures. `...opts: never[]` deliberately declines to dictate',
  "each method's parameters: the schema carries the WIRE shape (`folderPath`, `inputs[]`),",
  'while the builder owns ERGONOMICS (`{ folder }`). An earlier version emitted',
  "`opts?: Omit<XData, 'name'>` and could not be implemented — it was requiring the fluent",
  'surface to mirror the wire, which is precisely the coupling the generate/hand-write split',
  'exists to avoid. Argument correctness is covered by the per-method types and the suite.',
])}export interface GeneratedTaskMethods {
${kinds.map((k) => `${jsdoc([
    k.doc,
    ...serviceTypeDoc(k),
    ...(k.reuse ? ['', k.reuse] : []),
    `@see schema type \`${k.type}\`, available from ${k.minSchemaVersion}`,
  ], '  ')}  ${k.builderMethod}(${k.argStyle === 'name' ? 'name: string, ' : ''}...opts: never[]): this;`).join('\n\n')}
}
`;

// ── meta.json ────────────────────────────────────────────────────────────────
const meta = {
  provenance: { ...p, emittedSchemaVersion: targetVersion },
  emitted: kinds.map((k) => ({ type: k.type, method: k.builderMethod, status: 'confirmed' })),
  skipped,
  schemaVersionsAvailable: Object.keys(schema.taskTypesByVersion),
  preview: {
    source: schema.mainline?.source ?? null,
    taskTypes: schema.mainline?.preview ?? [],
    rules: schema.mainline?.previewRules ?? [],
    $note: 'PREVIEW = present in PO.Frontend mainline but not in the validating bundle. Real and scheduled, NOT gaps and NOT platform limits. Never emitted: a type the installed converter rejects produces invalid caseplans. Recorded so a shipped-later capability is not mis-filed as impossible — three were, before this was tracked.',
  },
  capabilityGaps: sem.capabilityGaps.map((g) => g.id),
  knownUnknowns: sem.knownUnknowns.map((u) => u.id),
};

// ── router ───────────────────────────────────────────────────────────────────
// SUPPORTED_VERSIONS must be what was EMITTED, not what the bundle declares. First
// version of this listed every bundle version, so resolveSchemaVersion('V5') returned
// V5 for a directory that was never generated — the router advertising support it did
// not have, failing at import time instead of at the guard.
const emittedDirs = new Set([targetVersion.toLowerCase()]);
if (existsSync(OUT)) {
  for (const d of readdirSync(OUT, { withFileTypes: true })) {
    if (d.isDirectory() && /^v\d+$/.test(d.name) && existsSync(join(OUT, d.name, 'unions.ts'))) emittedDirs.add(d.name);
  }
}
const emitted = [...emittedDirs].sort((a, b) => Number(a.slice(1)) - Number(b.slice(1))).map((d) => d.toUpperCase());
// The pin is explicit (--pin) or the semantics baseline — never "whichever ran last".
const pinArg = arg('--pin');
const pinned = pinArg ?? (emitted.includes(sem.$provenance.pinnedSchemaVersion) ? sem.$provenance.pinnedSchemaVersion : emitted[0]);
if (pinArg && !emitted.includes(pinArg)) {
  console.error(`emit-sdk: --pin ${pinArg} is not among emitted versions (${emitted.join(', ')}). Emit it first.`);
  process.exit(2);
}

const routerTs = `${header('Router — resolves a schema version to its generated leaves.')}
${jsdoc([
  'Resolution order, most specific first:',
  '  1. explicit  — casePlan(id, { schemaVersion })',
  '  2. env       — UIPATH_CASE_SCHEMA_VERSION',
  '  3. detected  — installed @uipath/case-schema',
  '  4. default   — the pinned baseline',
  '',
  'An unknown version FAILS LOUDLY. It never falls back to the nearest match: silent',
  'fallback emits documents the converter rejects while every local gate still passes.',
  '',
  'NOTE — two numbering systems, do not conflate them:',
  '  * SCHEMA version (`V13`) — the zod schema generation. What this router keys on.',
  '  * DOCUMENT version (`20.0.0`) — the `version` field in caseplan.json, set by',
  '    case-sdk.ts `_version`. What authors and `uip` see.',
  'They move independently and there is no derivable mapping between them; the pairing',
  'below is recorded from the emitting toolchain, not computed.',
])}export const PINNED_DEFAULT = '${pinned}';

/** Schema versions with generated leaves ON DISK — not merely present in the bundle. */
export const SUPPORTED_VERSIONS = ${JSON.stringify(emitted)} as const;
export type SupportedVersion = (typeof SUPPORTED_VERSIONS)[number];

${jsdoc([
  'Document version emitted by the SDK at the time these leaves were generated.',
  'Recorded for provenance — re-pinning the SDK is a deliberate act with migration cost.',
])}export const DOCUMENT_VERSION_AT_GENERATION = '${p.schemaEmitted}';

export function resolveSchemaVersion(explicit?: string): SupportedVersion {
  const want = explicit ?? process.env.UIPATH_CASE_SCHEMA_VERSION ?? PINNED_DEFAULT;
  if (!(SUPPORTED_VERSIONS as readonly string[]).includes(want)) {
    throw new Error(
      \`Unsupported case schema version "\${want}". Generated: \${SUPPORTED_VERSIONS.join(', ')}.\\n\` +
        'Regenerate with emit-sdk.mjs against the target package, or pin explicitly. ' +
        'Not falling back — a near-miss version emits documents the converter rejects.',
    );
  }
  return want as SupportedVersion;
}
`;

// ── write / check ────────────────────────────────────────────────────────────
const files = {
  [join(OUT, targetVersion.toLowerCase(), 'unions.ts')]: unionsTs,
  [join(OUT, targetVersion.toLowerCase(), 'task-kinds.ts')]: taskKindsTs,
  [join(OUT, targetVersion.toLowerCase(), 'placement.ts')]: placementTs,
  [join(OUT, targetVersion.toLowerCase(), 'task-methods.ts')]: methodsTs,
  [join(OUT, targetVersion.toLowerCase(), 'meta.json')]: JSON.stringify(meta, null, 2) + '\n',
  [join(OUT, 'index.ts')]: routerTs,
};

if (process.argv.includes('--json')) { console.log(JSON.stringify({ meta, files: Object.keys(files) }, null, 2)); process.exit(0); }

if (CHECK) {
  const stale = Object.entries(files).filter(([f, body]) => !existsSync(f) || readFileSync(f, 'utf8') !== body);
  if (stale.length) {
    console.error('emit-sdk --check: generated SDK is STALE:');
    for (const [f] of stale) console.error(`  ${existsSync(f) ? 'differs' : 'missing'}: ${f}`);
    console.error('\nRun: node .claude/skills/uipath-sdk-codegen/scripts/emit-sdk.mjs');
    process.exit(1);
  }
  console.log('emit-sdk --check: OK');
  process.exit(0);
}

for (const [f, body] of Object.entries(files)) { mkdirSync(dirname(f), { recursive: true }); writeFileSync(f, body); }
console.log(`emit-sdk: schema ${targetVersion} -> ${OUT}`);
console.log(`  emitted ${kinds.length} task kind(s): ${kinds.map((k) => k.type).join(', ') || '(none)'}`);
if (skipped.length) {
  console.log(`  skipped ${skipped.length} (present in schema, not confirmed):`);
  for (const s of skipped) console.log(`    ${s.type.padEnd(28)} ${s.reason}`);
  console.log('  -> probe them (references/verify.md), add semantics, re-run.');
}
if (meta.preview.taskTypes.length || meta.preview.rules.length) {
  console.log(`  PREVIEW (mainline-only, recorded but NOT emitted): ${[...meta.preview.taskTypes, ...meta.preview.rules].join(', ')}`);
} else if (meta.preview.source) {
  console.log('  preview: none — mainline and the validating bundle agree.');
}
