#!/usr/bin/env node
/**
 * extract-scheduler-grid — read the placement grid from the EXECUTING layer.
 *
 * WHY THIS EXISTS. Every other placement fact in this program was probed: emit a plan,
 * run `uip maestro case validate`, record the verbatim verdict. That measured 35 of 48
 * (rule, slot) cells ACCEPTED — including combinations that cannot mean anything, like
 * `case-entered` at task entry. The conclusion drawn at the time was "placement is
 * unenforced, so our tables are authoring guidance".
 *
 * That conclusion was half right. Placement is unenforced *by the validator*. It is
 * enforced downstream, by the scheduler that actually evaluates the rules — and that
 * schema is machine-readable, published, and versioned:
 *
 *   @uipath/scheduler-types (GitHub Packages, @uipath scope)
 *     CaseDeterministicRules.schema.json  ← per-slot `oneOf` unions: THE GRID
 *     dist/generated/*.d.ts               ← GENERATED from it, same build
 *
 * So a cell can be validator-ACCEPTED and scheduler-UNREACHABLE at the same time. That
 * gap is a real defect class, and our checker is the only gate positioned to catch it —
 * nothing between authoring and execution objects.
 *
 * TRUST NOTE. This package is the first source in this program whose published `.d.ts`
 * is trustworthy. `@uipath/case-schema` ships a hand-copied header (build step: `cp`),
 * wrong 3 for 3 against the platform — which is why extract-schema.mjs reads the zod
 * bundle instead. Here the header says "automatically generated from
 * CaseDeterministicRules.schema.json. DO NOT MODIFY IT BY HAND", and `build` is
 * `generate && tsc` via json-schema-to-typescript. Derived, not asserted. We still read
 * the JSON Schema rather than the .d.ts: it is the generator's input, so it cannot be
 * the staler of the two.
 *
 * WHAT THIS IS NOT. Source-read, not runtime-confirmed. It proves what the scheduler's
 * schema admits, not that any given plan reached the scheduler. Evidence class is
 * `scheduler-schema`, ranked below a probe verdict for legality claims and below a
 * running instance for anything behavioural.
 *
 * Usage:
 *   node extract-scheduler-grid.mjs [--schema <path/to/CaseDeterministicRules.schema.json>]
 *                                   [--json]
 */
import { readFileSync, existsSync } from 'node:fs';

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const JSON_OUT = process.argv.includes('--json');
const HOME = process.env.HOME ?? '';

/**
 * Resolve the schema in authority order. The installed package wins: it is the pinned,
 * lockfile-recorded artifact, so a change shows up as a reviewable diff. A sibling
 * checkout is HEAD of someone's working tree and can be ahead of, behind, or unrelated
 * to what anything consumes.
 */
const CANDIDATES = [
  { path: 'typescript/node_modules/@uipath/scheduler-types/CaseDeterministicRules.schema.json',
    label: 'installed @uipath/scheduler-types (AUTHORITY — pinned by package-lock)' },
  { path: `${HOME}/src/PO.Frontend/node_modules/@uipath/scheduler-types/CaseDeterministicRules.schema.json`,
    label: 'PO.Frontend node_modules (its pin, not ours)' },
  { path: `${HOME}/src/dmnscheduler/schemas/CaseDeterministicRules.schema.json`,
    label: 'dmnscheduler CHECKOUT (unpinned working tree — may be ahead of any release)' },
];

let SCHEMA = arg('--schema');
let SCHEMA_LABEL = 'explicit --schema';
if (!SCHEMA) {
  const hit = CANDIDATES.find((c) => existsSync(c.path));
  if (!hit) {
    console.error('extract-scheduler-grid: CaseDeterministicRules.schema.json not found.');
    console.error('Install it:  cd typescript && NODE_AUTH_TOKEN=$(gh auth token) npm i -D @uipath/scheduler-types');
    console.error('(@uipath scope is already redirected to GitHub Packages by typescript/.npmrc)');
    console.error(`Or pass --schema, or clone dmnscheduler to ${HOME}/src/dmnscheduler.`);
    process.exit(2);
  }
  SCHEMA = hit.path;
  SCHEMA_LABEL = hit.label;
  if (hit !== CANDIDATES[0]) {
    console.error(`⚠ using ${hit.label}`);
    console.error('  Not the pinned package — this grid is not reproducible from our lockfile.');
  }
}

const schema = JSON.parse(readFileSync(SCHEMA, 'utf8'));
const defs = schema.$defs ?? schema.definitions ?? {};

/**
 * Our authoring slot -> the scheduler slot definition(s) it lands in.
 *
 * `stage-exit` maps to TWO scheduler slots because the converter emits an authored stage
 * exit condition as `exitConditionType` or `completionConditionType` depending on the
 * stage's shape. They are checked as a union. Verified identical at v1.20.0 — asserted
 * below so a future divergence fails loudly instead of silently picking one.
 */
const SLOT_MAP = {
  'stage-entry': ['StageEntryCondition'],
  'stage-exit': ['StageExitCondition', 'StageCompletionCondition'],
  'task-entry': ['TaskEntryCondition'],
  'case-exit': ['CaseCompletionCondition'],
};

/**
 * Authoring rule literal -> scheduler condition type.
 *
 * Read out of the two-hop converter in PO.Frontend (source-read, not probed):
 *   hop 1  new-structured/utils/CaseManagementGenerateCaseJsonConditionForRules.ts
 *   hop 2  generate-case-plan-json/ConvertToSchedulerCasePlanJSONUtils.ts
 *
 * Note it is NOT one-to-one. `selected-*` and `required-*` collapse onto the same
 * condition type, with the distinction demoted into `parameters` — so the executing
 * artifact cannot tell you which the author wrote. Reachability is therefore a property
 * of the TARGET type, and a collapsed pair is reachable or unreachable together.
 */
const RULE_MAP = {
  'case-entered': 'CaseEntered',
  'current-stage-entered': 'StageEntered',
  'selected-stage-completed': 'StagesCompleted',
  'required-stages-completed': 'StagesCompleted',
  'selected-stage-exited': 'StagesExited',
  'selected-tasks-completed': 'TasksCompleted',
  'required-tasks-completed': 'TasksCompleted',
  'wait-for-connector': 'ConnectorTrigger',
  'adhoc': 'UserAdhocTrigger', // via CasePlanJsonConditionType.ManualTrigger — three names, one concept
  'user-selected-stage': 'Expression',
  'sla-status-change': 'SlaStatusChange',
};

/**
 * Rules with no cell-wise mapping. Excluded from the reachability verdict rather than
 * guessed at — a cell we cannot check must read `unknown`, never `reachable`.
 */
const UNMAPPED = {
  'runs-sequentially': {
    reason: 'DESUGARS, not a condition. CaseManagementGenerateTaskSequentialEntryConditionsJSON.ts '
      + 'expands it to StageEntered / TasksCompleted / Operator / Expression depending on the '
      + "task's position in the sequence, so it has no single target type to check.",
  },
  'timer': { reason: 'Deprecated. Rejected by CaseManagementJsonRulesSchemaV29 refine; no converter branch.' },
  'condition': { reason: 'Deprecated. Rejected by CaseManagementJsonRulesSchemaV29 refine; no converter branch.' },
  'stage-complete': { reason: 'Deprecated. Rejected by CaseManagementJsonRulesSchemaV29 refine; no converter branch.' },
};

/**
 * Pull the condition-type literals a slot definition admits, from its `oneOf` branches.
 *
 * Branches are frequently `{"$ref": "#/$defs/ExpressionEntryCondition"}` rather than
 * inline objects, so refs MUST be resolved before looking for a discriminator. Not doing
 * so cost a wrong answer on first run: every `Expression` cell came back unreachable,
 * which contradicted the converter — hop 2 demonstrably emits
 * `entryConditionType: "Expression"` at stage entry. The contradiction is what caught it.
 */
const DISCRIMINATORS = ['conditionType', 'entryConditionType', 'exitConditionType', 'completionConditionType'];
const deref = (node, seen = new Set()) => {
  let n = node;
  while (n && typeof n.$ref === 'string') {
    if (seen.has(n.$ref)) return n; // cyclic $ref (composite conditions nest) — stop
    seen.add(n.$ref);
    const name = n.$ref.replace(/^#\/(\$defs|definitions)\//, '');
    if (!defs[name]) return n;
    n = defs[name];
  }
  return n;
};

function acceptedTypes(defName) {
  const def = defs[defName];
  if (!def) return null;
  const branches = (def.oneOf ?? def.anyOf ?? [def]).map((b) => deref(b));
  const types = new Set();
  const composites = [];
  for (const b of branches) {
    const props = b.properties ?? {};
    let found = false;
    for (const key of DISCRIMINATORS) {
      const p = props[key];
      if (!p) continue;
      found = true;
      if (p.const) types.add(p.const);
      else if (Array.isArray(p.enum)) p.enum.forEach((v) => types.add(v));
    }
    // Still unkeyed after deref: the composite (operator + conditions) form, which carries
    // no condition type of its own. Recorded by property signature so a NEW unkeyed shape
    // is visible rather than silently absorbed.
    if (!found) composites.push(Object.keys(props).sort().join('+') || '(no properties)');
  }
  return { types: [...types].sort(), composites, branchCount: branches.length };
}

const slots = {};
for (const [ourSlot, defNames] of Object.entries(SLOT_MAP)) {
  const parts = defNames.map((n) => ({ def: n, ...(acceptedTypes(n) ?? { types: null }) }));
  const missing = parts.filter((p) => p.types === null).map((p) => p.def);
  if (missing.length) {
    console.error(`extract-scheduler-grid: slot definition(s) absent from schema: ${missing.join(', ')}`);
    console.error('The schema shape changed. Refusing to emit a grid from a stale SLOT_MAP.');
    process.exit(2);
  }
  // Fail loudly if the two stage-exit definitions ever diverge — the union would then be
  // hiding a real distinction rather than collapsing an equivalent one.
  if (parts.length > 1) {
    const sig = parts.map((p) => p.types.join(','));
    if (new Set(sig).size > 1) {
      console.error(`⚠ ${ourSlot}: mapped definitions DISAGREE — ${parts.map((p) => `${p.def}=[${p.types}]`).join(' vs ')}`);
      console.error('  Treating as a union, but this slot now needs a real disambiguation rule.');
    }
  }
  slots[ourSlot] = {
    schedulerDefs: defNames,
    accepted: [...new Set(parts.flatMap((p) => p.types))].sort(),
    compositeShapes: [...new Set(parts.flatMap((p) => p.composites))],
  };
}

/** Slot definitions in the schema that our authoring model has no counterpart for. */
const unmappedSlots = Object.keys(defs)
  .filter((k) => /Condition$/.test(k) && (defs[k].oneOf || defs[k].anyOf))
  .filter((k) => !Object.values(SLOT_MAP).flat().includes(k));

// ── the reachability grid ────────────────────────────────────────────────────
const cells = [];
for (const [rule, target] of Object.entries(RULE_MAP)) {
  for (const [slot, info] of Object.entries(slots)) {
    cells.push({
      rule,
      slot,
      schedulerType: target,
      reachable: info.accepted.includes(target),
      evidence: 'scheduler-schema',
      source: `@uipath/scheduler-types ${schema.$id ?? ''}`.trim(),
    });
  }
}

const out = {
  schema: SCHEMA,
  schemaLabel: SCHEMA_LABEL,
  schemaId: schema.$id ?? null,
  schemaTitle: schema.title ?? null,
  slots,
  unmappedSlots,
  unmappedRules: UNMAPPED,
  cells,
  unreachable: cells.filter((c) => !c.reachable),
};

// ── --write: record into semantics, the one source the three consumers read ──
// Derived data, so it is REGENERATED rather than curated. Writing it here (instead of
// having emit-sdk re-derive) keeps a single reader of the schema, and makes an upstream
// change arrive as a reviewable diff in git rather than as a silent difference in output.
if (process.argv.includes('--write')) {
  const SEM = '.claude/skills/uipath-sdk-codegen/semantics/case-semantics.json';
  if (!existsSync(SEM)) {
    console.error(`extract-scheduler-grid: ${SEM} not found — run from the repo root.`);
    process.exit(2);
  }
  const sem = JSON.parse(readFileSync(SEM, 'utf8'));
  const probed = new Map(sem.rulePlacement.cells.map((c) => [`${c.rule}@${c.slot}`, c]));

  // Cross-classify against the probe grid. The two axes answer different questions, so
  // the disagreements are the interesting output, not a problem to reconcile away.
  const classify = (c) => {
    const p = probed.get(`${c.rule}@${c.slot}`);
    if (!p) return 'not-probed';
    if (p.legal === false) return 'agrees-rejected';   // both gates reject — triangulated
    return 'silent-gap';                               // validates clean, cannot execute
  };
  const unreachable = out.unreachable.map((c) => ({
    rule: c.rule, slot: c.slot, schedulerType: c.schedulerType,
    agreement: classify(c),
    probeVerdict: probed.get(`${c.rule}@${c.slot}`)?.verdict ?? null,
  }));

  const reverse = sem.rulePlacement.cells
    .filter((c) => c.legal === false)
    .filter((c) => out.cells.some((x) => x.rule === c.rule && x.slot === c.slot && x.reachable))
    .map((c) => ({ rule: c.rule, slot: c.slot, note: 'validator rejects but scheduler admits' }));

  sem.schedulerReachability = {
    $comment: 'GENERATED by extract-scheduler-grid.mjs --write. Do not hand-edit; re-run it. '
      + 'Reachability is a SEPARATE AXIS from validator legality: a cell can validate clean and '
      + 'still be unevaluatable downstream. Never merge these into rulePlacement.cells — the '
      + 'evidence classes differ (source-read schema vs verbatim probe verdict) and so do the remedies.',
    $evidenceClass: 'scheduler-schema',
    $provenance: {
      schema: SCHEMA,
      schemaLabel: SCHEMA_LABEL,
      schemaId: out.schemaId,
      packageVersion: (() => {
        const pj = SCHEMA.replace(/CaseDeterministicRules\.schema\.json$/, 'package.json');
        try { return JSON.parse(readFileSync(pj, 'utf8')).version ?? null; } catch { return null; }
      })(),
      ruleMapSource: [
        'PO.Frontend .../new-structured/utils/CaseManagementGenerateCaseJsonConditionForRules.ts',
        'PO.Frontend .../generate-case-plan-json/ConvertToSchedulerCasePlanJSONUtils.ts',
      ],
      ruleMapEvidence: 'source-read — the mapping was read out of the converter, not exercised',
    },
    slotAdmits: Object.fromEntries(Object.entries(out.slots).map(([k, v]) => [k, v.accepted])),
    ruleMap: RULE_MAP,
    excludedRules: Object.fromEntries(Object.entries(UNMAPPED).map(([k, v]) => [k, v.reason])),
    unmappedSlots: out.unmappedSlots,
    unreachable,
    contradictions: reverse,
    $coherence: `${unreachable.filter((u) => u.agreement === 'agrees-rejected').length} of `
      + `${unreachable.length} unreachable cells are ALSO validator-rejected (independent agreement); `
      + `${reverse.length} contradictions (validator stricter than scheduler). Zero contradictions is `
      + 'the expected shape — the scheduler should be strictly stricter. A nonzero count means the '
      + 'rule map is wrong, not that the platform is inconsistent.',
  };
  const { writeFileSync } = await import('node:fs');
  writeFileSync(SEM, `${JSON.stringify(sem, null, 2)}\n`);
  console.error(`✓ wrote schedulerReachability to ${SEM}`);
  console.error(`  ${unreachable.length} unreachable · ${unreachable.filter((u) => u.agreement === 'silent-gap').length} silent gaps · ${reverse.length} contradictions`);
}

if (JSON_OUT) { console.log(JSON.stringify(out, null, 2)); process.exit(0); }

console.log(`schema: ${SCHEMA}`);
console.log(`source: ${SCHEMA_LABEL}`);
if (schema.$id) console.log(`$id:    ${schema.$id}`);
console.log('\nwhat each slot ADMITS (scheduler vocabulary):');
for (const [slot, info] of Object.entries(slots)) {
  console.log(`  ${slot.padEnd(12)} ${info.accepted.length}: ${info.accepted.join(', ')}`);
  console.log(`  ${''.padEnd(12)} via ${info.schedulerDefs.join(' ∪ ')}${info.compositeShapes.length ? ` (+ composite: ${info.compositeShapes.join(' | ')})` : ''}`);
}
if (unmappedSlots.length) {
  console.log(`\nslot definitions with no authoring counterpart: ${unmappedSlots.join(', ')}`);
  console.log('  (CaseAgentCondition carries agent-only Fallback/Override — not authorable today.)');
}
console.log(`\nUNREACHABLE cells (${out.unreachable.length} of ${cells.length}) — validator may accept these, the scheduler cannot evaluate them:`);
for (const c of out.unreachable) console.log(`  ${c.rule} @ ${c.slot}  →  ${c.schedulerType} not in slot union`);
console.log('\nrules excluded from the grid (no cell-wise target):');
for (const [r, v] of Object.entries(UNMAPPED)) console.log(`  ${r}: ${v.reason.split('.')[0]}.`);
console.log('\nEvidence class: scheduler-schema (source-read). Ranks BELOW a probe verdict for');
console.log('legality and BELOW a running instance for behaviour. It proves what the scheduler');
console.log('admits — not that any plan of ours reached the scheduler.');
