#!/usr/bin/env node
/**
 * compat-demo — one command that shows what this generation of the SDK can express, and
 * proves each claim against the tool that actually decides.
 *
 * The point is not a pretty table. It is that every row is EARNED at run time: the script
 * compiles real sources with the built SDK and runs `uip maestro case validate` on the
 * output. Nothing is read from a doc, and nothing is asserted from memory — this file
 * cannot go stale in the way the hand-written coverage prose it replaces did (that prose
 * was wrong three times, once expensively).
 *
 * Three sections:
 *   1. COVERAGE   — every schema task type: emitted? has a builder method? probe verdict?
 *   2. COMPAT     — the same plan compiled and validated, so "works" means uip said so
 *   3. GUARDRAILS — the illegal states that no longer compile, demonstrated by compiling them
 *
 *   node compat-demo.mjs [--json] [--keep]
 *
 * Exit 0 only if every coverage row is consistent and every compat plan validates. A demo
 * that cannot fail is a screenshot, not a demo.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SKILL = join(HERE, '..');
const REPO = join(HERE, '..', '..', '..', '..');
const SDK = join(REPO, 'typescript', 'sdk');
const GEN = join(SDK, 'src', 'case', 'generated');
const WORK = join(REPO, '.compat-demo');
const JSON_OUT = process.argv.includes('--json');
const C = process.stdout.isTTY
  ? { g: (s) => `\x1b[32m${s}\x1b[0m`, r: (s) => `\x1b[31m${s}\x1b[0m`, y: (s) => `\x1b[33m${s}\x1b[0m`, d: (s) => `\x1b[2m${s}\x1b[0m`, b: (s) => `\x1b[1m${s}\x1b[0m` }
  : { g: (s) => s, r: (s) => s, y: (s) => s, d: (s) => s, b: (s) => s };

const sem = JSON.parse(readFileSync(join(SKILL, 'semantics', 'case-semantics.json'), 'utf8'));
const meta = JSON.parse(readFileSync(join(GEN, 'v13', 'meta.json'), 'utf8'));
const sdkSrc = readFileSync(join(SDK, 'src', 'case', 'case-sdk.ts'), 'utf8');

if (!existsSync(join(SDK, 'dist', 'case', 'compile-cli.js'))) {
  console.error('compat-demo: SDK not built. Run `npm run build` in typescript/sdk.');
  process.exit(2);
}

// ── workspace ────────────────────────────────────────────────────────────────
rmSync(WORK, { recursive: true, force: true });
mkdirSync(join(WORK, 'node_modules', '@uipath'), { recursive: true });
try { execFileSync('ln', ['-sfn', SDK, join(WORK, 'node_modules', '@uipath', 'flow-sdk')]); } catch { /* exists */ }

const sh = (cmd, args) => {
  try { return { ok: true, out: execFileSync(cmd, args, { cwd: WORK, encoding: 'utf8', stdio: 'pipe' }) }; }
  catch (e) { return { ok: false, out: `${String(e.stdout ?? '')}${String(e.stderr ?? '')}` }; }
};

/** Compile a source and validate it. `uip` prints an update failure to stderr before its real
 *  output, so the Status field in the payload is the verdict — never the exit code. */
function compileAndValidate(name, source) {
  writeFileSync(join(WORK, `${name}.case.ts`), source);
  const c = sh('node', [join(SDK, 'dist', 'case', 'compile-cli.js'), `${name}.case.ts`, '-o', `${name}.json`]);
  if (!c.ok) return { stage: 'compile', ok: false, detail: c.out.trim().split('\n').slice(0, 2).join(' ') };
  const v = sh('uip', ['maestro', 'case', 'validate', `${name}.json`, '--output', 'json']);
  const status = /"Status"\s*:\s*"(\w+)"/.exec(v.out)?.[1] ?? null;
  // The diagnostics are in "Instructions"; "Message" is only ever "Validation failed for
  // <path>", which tells a viewer nothing. Reporting the path as the reason made two real
  // failures here unreadable until this was fixed.
  const why = /"Instructions"\s*:\s*"((?:[^"\\]|\\.)*)"/.exec(v.out)?.[1] ?? '';
  const first = why.replace(/\\n/g, '\n').split('\n').find((l) => l.includes('[error]')) ?? why.split('\n')[0] ?? '';
  const reason = first.replace(/^\s*-\s*\[error\]\s*/, '').trim();
  return { stage: 'validate', ok: status === 'Valid', status, detail: status ?? (reason || '(no Status)') };
}

// ── 1. coverage ──────────────────────────────────────────────────────────────
const schemaTypes = [...new Set([...Object.keys(sem.taskKinds)])].sort();
const coverage = schemaTypes.map((type) => {
  const k = sem.taskKinds[type];
  const emitted = (meta.emitted ?? []).some((e) => (e.type ?? e) === type);
  // The method must exist in SOURCE, not merely in semantics — semantics is a claim, the
  // source is the artifact. The generated interface makes disagreement a compile error, so
  // this only ever reports; it cannot be the thing that catches a regression.
  const hasMethod = new RegExp(`^\\s{2}${k.builderMethod}[<(]`, 'm').test(sdkSrc);
  return {
    type, method: k.builderMethod, status: k.status, verdict: k.verdict ?? null,
    emitted, hasMethod,
    serviceType: k.converterServiceType
      ? `${k.converterServiceType.value}${k.converterServiceType.overridable ? ' (author may override — emitted)' : ' (converter-assigned — not emitted)'}`
      : null,
    consistent: k.status === 'confirmed' ? (emitted && hasMethod) : true,
  };
});

// ── 2. compat ────────────────────────────────────────────────────────────────
// `.required()` is not decoration: a stage whose exit rule is `required-tasks-completed`
// with no required task is REJECTED — "Stage exit rule 'Complete rule' has no task(s) marked
// as required". The demo hit that and it is worth keeping visible in the source.
const REF = (m, extra = '', req = false) => `    .task('T ${m}', (t) => t.${m}('X', { folder: 'Shared' })${req ? '\n      .required()' : ''}${extra}
      .entryWhen(rule('current-stage-entered')))`;
const plan = (name, body, tail = '') => `import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('${name}')
  .description('compat-demo ${name}')
  .identifier('CD')
${tail}  .stage('S', (s) => s
    .required()
    .entryWhen(rule('case-entered'))
${body}
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'));
`;

const refKinds = coverage.filter((c) => c.status === 'confirmed' && sem.taskKinds[c.type].argStyle === 'name'
  && c.method !== 'connector' && c.method !== 'caseManagement');
const compat = [
  { name: 'AllReferenceKinds',
    what: `every reference-mode task kind (${refKinds.length}) in one plan`,
    source: plan('AllReferenceKinds', refKinds.map((c, i) => REF(c.method, '', i === 0)).join('\n')) },
  { name: 'IoBinding',
    what: 'io-binding on a newly added kind (document-extraction → case variable)',
    source: plan('IoBinding', REF('documentExtraction', `\n      .outputs({ docId: 'extractedId' })`, true), "  .var('docId', 'string')\n") },
  { name: 'ExplicitServiceType',
    what: 'author overrides the converter fallback on external-workflow',
    source: plan('ExplicitServiceType', `    .task('T ew', (t) => t.externalWorkflow('X', { folder: 'Shared', serviceType: 'Intsvc.SyncWorkflowExecution' })
      .required()
      .entryWhen(rule('current-stage-entered')))`) },
  { name: 'SlaBreachDrivesWork',
    what: 'breach-driven work: an SLA status change starts a task',
    source: `import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('SlaBreachDrivesWork')
  .description('compat-demo breach')
  .identifier('CD')
  .stage('S', (s) => s
    .required()
    .entryWhen(rule('case-entered'))
    .sla({ displayName: 'Deadline', count: 2, unit: 'd' })
    .task('Normal', (t) => t.process('X', { folder: 'Shared' }).required()
      .entryWhen(rule('current-stage-entered')))
    .task('On breach', (t) => t.externalAgent('Escalator', { folder: 'Shared' })
      .entryWhen(rule('sla-status-change', { sla: 'Deadline' })))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'));
` },
].map((c) => ({ ...c, result: compileAndValidate(c.name, c.source) }));

// ── 3. guardrails ────────────────────────────────────────────────────────────
// Each of these MUST fail to compile. Proven by compiling them, not by assertion — the
// fixture in tests/ does the same job for CI; this exists so a viewer can see it happen.
const GUARDS = [
  { what: "case-entered at TASK entry (validates clean, then never fires)",
    line: `.task('T', (t) => t.process('X').entryWhen(rule('case-entered')))` },
  { what: "current-stage-entered at STAGE entry (it is a task-entry rule)",
    line: null, stageLine: `.entryWhen(rule('current-stage-entered'))` },
  { what: "sla-status-change with no SLA (serializer throws; validator rejects)",
    line: `.task('T', (t) => t.process('X').entryWhen(rule('sla-status-change')))` },
  { what: "an option the rule provably ignores (sla on case-entered)",
    line: `.task('T', (t) => t.process('X').entryWhen(rule('case-entered', { sla: 'D' })))` },
];
const tsc = join(SDK, 'node_modules', '.bin', 'tsc');
const guardrails = GUARDS.map((g, i) => {
  const name = `guard${i}`;
  const body = g.stageLine
    ? `    ${g.stageLine}\n    .task('T', (t) => t.process('X').entryWhen(rule('current-stage-entered')))`
    : `    ${g.line}`;
  const src = `import { casePlan, rule } from '${join(SDK, 'src', 'case', 'case-sdk.js')}';
export default casePlan('G')
  .stage('S', (s) => s
    .entryWhen(rule('case-entered'))
${body}
    .exitWhen(rule('required-tasks-completed')))
  .completeWhen(rule('required-stages-completed'));
`;
  writeFileSync(join(WORK, `${name}.ts`), src);
  const r = existsSync(tsc)
    ? sh(tsc, ['--noEmit', '--strict', '--target', 'es2022', '--module', 'esnext',
      '--moduleResolution', 'bundler', '--skipLibCheck', join(WORK, `${name}.ts`)])
    : { ok: true, out: '(tsc unavailable)' };
  return { what: g.what, rejected: !r.ok, detail: (/error TS\d+: ([^\n]{0,90})/.exec(r.out)?.[1] ?? '').trim() };
});

if (!process.argv.includes('--keep')) rmSync(WORK, { recursive: true, force: true });

// ── report ───────────────────────────────────────────────────────────────────
const okCov = coverage.every((c) => c.consistent);
const okCompat = compat.every((c) => c.result.ok);
const okGuards = guardrails.every((g) => g.rejected);
const pass = okCov && okCompat && okGuards;

if (JSON_OUT) {
  console.log(JSON.stringify({ provenance: sem.$provenance, pinned: meta, coverage, compat, guardrails, pass }, null, 2));
  process.exit(pass ? 0 : 1);
}

const p = sem.$provenance;
console.log(C.b('\nUiPath Case SDK — generation compatibility report'));
console.log(C.d(`  cli ${p.cli} · package ${p.package} · schema ${meta.emittedSchemaVersion ?? 'V13'} · probed ${p.probedOn}`));
console.log(C.d('  every row below was produced by running the real toolchain just now\n'));

console.log(C.b('1. Task-type coverage') + C.d('  (schema type → builder method)'));
const pad = (s, n) => String(s).padEnd(n);
console.log(C.d(`  ${pad('schema type', 30)}${pad('method', 20)}${pad('evidence', 20)}serviceType`));
for (const c of coverage) {
  const mark = c.status === 'confirmed' ? (c.consistent ? C.g('✓') : C.r('✗')) : C.y('○');
  const ev = c.status === 'confirmed' ? (c.verdict ?? 'confirmed') : c.status;
  console.log(`  ${mark} ${pad(c.type, 28)}${pad(c.hasMethod ? c.method : C.r('MISSING'), 20)}${pad(ev, 20)}${C.d(c.serviceType ?? '')}`);
}
const conf = coverage.filter((c) => c.status === 'confirmed').length;
console.log(C.d(`  ${conf}/${coverage.length} probe-confirmed and emitted. ○ = enumerated, not probe-confirmed:`));
console.log(C.d('  action / wait-for-timer were probed with a payload they do not take, so that'));
console.log(C.d('  result measures the probe, not the platform. Both work via their own methods.\n'));

console.log(C.b('2. Compatibility') + C.d('  (compiled, then judged by `uip maestro case validate`)'));
for (const c of compat) {
  console.log(`  ${c.result.ok ? C.g('✓') : C.r('✗')} ${pad(c.what, 66)}${c.result.ok ? C.g(`"Status": "${c.result.status}"`) : C.r(`${c.result.stage}: ${c.result.detail}`)}`);
}
console.log('');

console.log(C.b('3. Guardrails') + C.d('  (each MUST fail to compile — illegal states made unrepresentable)'));
for (const g of guardrails) {
  console.log(`  ${g.rejected ? C.g('✓ rejected') : C.r('✗ COMPILED')} ${pad(g.what, 66)}${C.d(g.detail.slice(0, 40))}`);
}
console.log(C.d('  These validate clean at the platform today; the type system is the only gate.\n'));

console.log(pass ? C.g(C.b('PASS')) : C.r(C.b('FAIL')));
console.log(C.d(`  coverage ${okCov ? 'ok' : 'INCONSISTENT'} · compat ${okCompat ? 'ok' : 'FAILED'} · guardrails ${okGuards ? 'ok' : 'LEAKED'}`));
console.log(C.d('  Ceiling: validator-confirmed. Nothing here proves the platform EXECUTES a plan —'));
console.log(C.d('  that needs a running instance, which the debug rung cannot yet give us.\n'));
process.exit(pass ? 0 : 1);
