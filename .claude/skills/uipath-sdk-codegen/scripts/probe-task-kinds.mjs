#!/usr/bin/env node
/**
 * probe-task-kinds — establish, per schema task type, what `uip maestro case validate`
 * actually accepts, by MUTATING a known-good caseplan rather than by reading a schema.
 *
 * WHY A SEPARATE HARNESS FROM run-probes. That one probes rule PLACEMENT through the
 * builder, which only works for things the builder can already emit. The whole point here
 * is the opposite case: 5 of 14 schema task types have no builder method, so they cannot be
 * authored at all. The only way to ask the validator about them is to compile a plan with a
 * type it DOES support and rewrite that node's `type`/`data` in the JSON.
 *
 * This is also the exact procedure that produced a wrong answer once before, so the failure
 * mode is worth naming: `external-agent` and `external-workflow` were marked `confirmed` on
 * the strength of reading the converter plus a mutation checked against the SHIPPED ZOD —
 * which this repo documents as lenient, and which is NOT what `uip` loads. A mutation is
 * only evidence when `uip` is the thing that judges it. Hence every row below records the
 * verbatim CLI verdict or it does not get recorded.
 *
 * Shapes, read from the validating bundle (maestro-tool), all `data` optional:
 *
 *   process | api-workflow | flow-process | function   BaseRunProcess
 *   document-extraction                                BaseRunProcess + serviceType
 *   external-agent | external-workflow                 BaseRunProcess + serviceType + bindings
 *
 * BaseRunProcess = { name?, folderPath?, inputs?, outputs?, context? } — every field
 * optional, which is why a shape-only argument cannot tell you what the platform accepts.
 *
 *   node probe-task-kinds.mjs [--only <type>] [--json] [--keep]
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..', '..', '..');
const SDK = join(REPO, 'typescript', 'sdk');
const SDK_DIST = join(SDK, 'dist', 'case');
const WORK = join(REPO, '.probe-task-kinds');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const JSON_OUT = process.argv.includes('--json');
const ONLY = arg('--only');

/**
 * Per-type `data`, and whether the type is a pure shape-clone of one we already support.
 * `sameShapeAs` is not cosmetic: where it holds, a builder method is a naming exercise
 * rather than a new payload to work out, and that changes the cost of covering it.
 */
const KINDS = {
  'process': { data: base(), sameShapeAs: null, note: 'the control — already supported; proves the harness is sound' },
  'api-workflow': { data: base(), sameShapeAs: 'process' },
  'flow-process': { data: base(), sameShapeAs: 'process' },
  'function': { data: base(), sameShapeAs: 'process' },
  'document-extraction': { data: { ...base(), serviceType: 'Intsvc.ActivityExecution' } },
  'external-agent': { data: { ...base(), serviceType: 'Orchestrator.StartAgenticProcess', bindings: [] } },
  'external-workflow': { data: { ...base(), serviceType: 'Orchestrator.StartJob', bindings: [] } },
  'agent': { data: base(), sameShapeAs: 'process', note: 'supported; probed for completeness' },
  'rpa': { data: base(), sameShapeAs: 'process', note: 'supported' },
  'case-management': { data: base(), sameShapeAs: 'process', note: 'supported' },
  // These three carry their own non-BaseRunProcess payloads that the builder already
  // constructs (action fields, connector subscription, timer). Mutating a process node into
  // them would probe a payload we deliberately do not hand-write, so they are probed only
  // for the type literal being accepted at all.
  'action': { data: base(), note: 'supported; real payload is built by .action(), not here' },
  'wait-for-connector': { data: base(), note: 'supported; real payload is the connector subscription' },
  'wait-for-timer': { data: base(), note: 'supported; real payload is the timer spec' },
  'execute-connector-activity': { data: base(), note: 'supported as .connector() — SDK name differs from the schema type' },
};

function base() {
  return { name: 'CoderEval TM Create TestCase', folderPath: 'Shared' };
}

/** A minimal case with one process task, which we then rewrite per kind. */
const SOURCE = `import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('ProbeKinds')
  .description('Task-kind probe baseline.')
  .identifier('PRB')
  .stage('Only', (s) => s
    .required()
    .entryWhen(rule('case-entered'))
    .task('Subject', (t) => t
      .process('CoderEval TM Create TestCase', { folder: 'Shared' })
      .required()
      .entryWhen(rule('current-stage-entered')))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'));
`;

function sh(cmd, args, cwd) {
  try {
    return { ok: true, out: execFileSync(cmd, args, { cwd, encoding: 'utf8', stdio: 'pipe' }) };
  } catch (e) {
    return { ok: false, out: `${String(e.stdout ?? '')}${String(e.stderr ?? '')}` };
  }
}

if (!existsSync(join(SDK_DIST, 'compile-cli.js'))) {
  console.error('probe-task-kinds: SDK not built. Run `npm run build` in typescript/sdk first.');
  process.exit(2);
}

// Workspace with a node_modules symlink so the probe source imports the SDK the way a real
// author's project does, rather than through a relative path no user would write.
rmSync(WORK, { recursive: true, force: true });
mkdirSync(join(WORK, 'node_modules', '@uipath'), { recursive: true });
try {
  execFileSync('ln', ['-sfn', SDK, join(WORK, 'node_modules', '@uipath', 'flow-sdk')]);
} catch { /* symlink may already exist */ }
writeFileSync(join(WORK, 'probe.case.ts'), SOURCE);

const compiled = sh('node', [join(SDK_DIST, 'compile-cli.js'), 'probe.case.ts', '-o', 'base.json'], WORK);
if (!compiled.ok) {
  console.error('probe-task-kinds: baseline failed to COMPILE — the harness is broken, not the platform.');
  console.error(compiled.out.split('\n').slice(0, 8).join('\n'));
  process.exit(2);
}
const baseline = JSON.parse(readFileSync(join(WORK, 'base.json'), 'utf8'));

/**
 * Locate the single task node.
 *
 * A caseplan is FLOW-shaped at the top (`nodes`/`edges`), with stages as
 * `case-management:Stage` nodes and tasks nested at `node.data.tasks` — itself an array OF
 * ARRAYS, one inner array per lane. Guessing this wrong is why the first run of this script
 * aborted instead of probing: worth keeping the abort, since a harness that cannot find its
 * subject would otherwise report 14 confident failures about the platform.
 */
function findTask(plan) {
  for (const node of plan.nodes ?? []) {
    const lanes = node.data?.tasks;
    if (!Array.isArray(lanes)) continue;
    for (const lane of lanes) {
      const arr = Array.isArray(lane) ? lane : [lane];
      const hit = arr.find((n) => n && typeof n.type === 'string');
      if (hit) return hit;
    }
  }
  return null;
}

if (!findTask(baseline)) {
  console.error('probe-task-kinds: could not find the task node in the compiled plan.');
  console.error('The serializer\'s shape changed. Refusing to probe a node we cannot locate.');
  console.error(`Top-level keys: ${Object.keys(baseline).join(', ')}`);
  process.exit(2);
}

const results = [];
for (const [type, spec] of Object.entries(KINDS)) {
  if (ONLY && type !== ONLY) continue;
  const plan = JSON.parse(JSON.stringify(baseline));
  const node = findTask(plan);
  node.type = type;
  node.data = spec.data;
  const file = `probe-${type}.json`;
  writeFileSync(join(WORK, file), JSON.stringify(plan, null, 2));

  const r = sh('uip', ['maestro', 'case', 'validate', file, '--output', 'json'], WORK);
  const text = r.out;
  // Judge the payload's Status field, never the exit code or the presence of stderr — every
  // `uip` call in this environment prints a self-update failure to stderr before its real
  // output, so "stderr is empty" is always false here.
  const status = /"Status"\s*:\s*"(\w+)"/.exec(text)?.[1] ?? null;
  // Diagnostics live in "Instructions" — "Message" is only "Validation failed for <path>".
  const instr = /"Instructions"\s*:\s*"((?:[^"\\]|\\.)*)"/.exec(text)?.[1] ?? '';
  const msg = instr.replace(/\\n/g, '\n').split('\n')
    .filter((l) => l.includes('[error]'))
    .map((l) => l.replace(/^\s*-\s*\[error\]\s*/, '').trim());
  results.push({
    type,
    status,
    verdict: status ? `"Status": "${status}"` : '(no Status in output)',
    messages: [...new Set(msg)].slice(0, 3),
    accepted: status === 'Valid',
    sameShapeAs: spec.sameShapeAs ?? null,
    note: spec.note ?? null,
  });
}

if (!process.argv.includes('--keep')) rmSync(WORK, { recursive: true, force: true });

if (JSON_OUT) { console.log(JSON.stringify({ probedOn: new Date().toISOString().slice(0, 10), results }, null, 2)); process.exit(0); }

const pad = (s, n) => String(s).padEnd(n);
console.log(`probed ${results.length} task type(s) against \`uip maestro case validate\`\n`);
console.log(`${pad('type', 30)}${pad('verdict', 22)}shape`);
console.log('-'.repeat(72));
for (const r of results) {
  console.log(`${pad(r.type, 30)}${pad(r.verdict, 22)}${r.sameShapeAs ? `= ${r.sameShapeAs}` : ''}`);
  if (r.messages.length && !r.accepted) for (const m of r.messages) console.log(`${' '.repeat(30)}↳ ${m}`);
}
const acc = results.filter((r) => r.accepted).length;
console.log(`\n${acc}/${results.length} accepted.`);
console.log('A verdict here licenses EMITTING the type. It does not prove the platform can');
console.log('execute it — that needs a running instance, which the debug rung cannot yet give us.');
