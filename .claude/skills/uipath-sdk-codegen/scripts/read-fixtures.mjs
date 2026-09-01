#!/usr/bin/env node
/**
 * read-fixtures — tier 2. What the platform is REQUIRED to decide, in seconds.
 *
 * `~/src/dmnscheduler/test-cases/<NN>/` holds behaviour fixtures as triples:
 *
 *   case-deterministic-rules.json   the rules
 *   <NN>-input.json                 an execution state + one event
 *   <NN>-output.json                the decisions the scheduler MUST produce
 *
 * That is a different class of answer from anything else available. A schema says what is
 * EXPRESSIBLE; a probe says what is ACCEPTED; evaluator source says what the code APPEARS to
 * do. A fixture says what is REQUIRED, and ships negative cases. It is also the cheapest of
 * the four — local JSON, no CLI, no network — which is why the precedence table puts it
 * second and probing fourth.
 *
 * This exists because the design doc claimed tier 2 was "fully scripted" while the only
 * scripted tiers were the schema readers. Consulting fixtures was a manual grep, so in
 * practice it did not happen: this program probed a validator and read evaluator source for
 * a day to answer questions `07-sla-direct-task-trigger` answers outright.
 *
 *   node read-fixtures.mjs                       # every scenario, with its specified rules
 *   node read-fixtures.mjs --grep sla            # scenarios touching SLA
 *   node read-fixtures.mjs --type SlaStatusChange
 *   node read-fixtures.mjs --show 07             # full triple for one scenario
 *   node read-fixtures.mjs --json
 */
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const HOME = process.env.HOME ?? '';
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const ROOT = arg('--root', join(HOME, 'src', 'dmnscheduler', 'test-cases'));
const JSON_OUT = process.argv.includes('--json');
const GREP = (arg('--grep') ?? '').toLowerCase();
const TYPE = arg('--type');
const SHOW = arg('--show');

if (!existsSync(ROOT)) {
  console.error(`read-fixtures: no fixtures at ${ROOT}`);
  console.error('Clone dmnscheduler, or pass --root. Absence of the checkout is NOT evidence');
  console.error('that a behaviour is unspecified — it is evidence you cannot see the spec.');
  process.exit(2);
}

/** Every `ruleName` in a rules file, with the condition type it belongs to.
 *  Rule names in these fixtures read as prose specifications — that is the whole trick. */
function rulesOf(obj, acc = []) {
  if (Array.isArray(obj)) { obj.forEach((o) => rulesOf(o, acc)); return acc; }
  if (obj && typeof obj === 'object') {
    const type = obj.entryConditionType ?? obj.completionConditionType
      ?? obj.exitConditionType ?? obj.conditionType ?? null;
    if (obj.ruleName) acc.push({ type, name: obj.ruleName, params: obj.parameters ?? null });
    Object.values(obj).forEach((v) => rulesOf(v, acc));
  }
  return acc;
}

/** Summarise a triple: the event that goes in, and the decisions required out. */
function pair(dir, inputFile) {
  const stem = inputFile.replace(/-input\.json$/, '');
  const outFile = `${stem}-output.json`;
  const read = (f) => { try { return JSON.parse(readFileSync(join(dir, f), 'utf8')); } catch { return null; } };
  const inp = read(inputFile);
  const out = read(outFile);
  if (!inp) return null;
  const ev = inp.event ?? {};
  const p = ev.parameters ?? {};
  const evStr = [ev.type, p.status, p.scope, p.stageName ?? (p.stageNames ?? []).join('|'), p.taskName]
    .filter(Boolean).join(' ');
  // Key names read from the fixtures themselves, not guessed. The first version of this
  // invented `stagesToEnter`/`stagesToComplete` by analogy with `tasksToRun`; the real keys
  // are PAST TENSE (`stagesEntered`, `stagesCompleted`, `stagesExited`). Every scenario that
  // entered a stage therefore printed "NOTHING (negative case)" — a wrong answer that looked
  // like a meaningful finding. Fifth instance in this program of a correct check bound to the
  // wrong field; caught only by reading a raw output file.
  const decisions = [];
  for (const t of out?.tasksToRun ?? []) decisions.push(`run task ${t.taskName}`);
  for (const t of out?.tasksToCancel ?? []) decisions.push(`cancel task ${t.identifier ?? t.taskName}`);
  for (const st of out?.stagesEntered ?? []) decisions.push(`enter stage ${st.stageName}`);
  for (const st of out?.stagesCompleted ?? []) decisions.push(`complete stage ${st.stageName}`);
  for (const st of out?.stagesExited ?? []) decisions.push(`exit stage ${st.stageName}`);
  if (out?.caseResolution) {
    const r = out.caseResolution;
    decisions.push(`resolve CASE${typeof r === 'object' && r.resolution ? ` (${r.resolution})` : ''}`);
  }
  // An empty decision set is the NEGATIVE case and is the most useful row in the file:
  // it proves the rule is selective rather than firing on everything.
  // `runCaseAgent` is present in every output, so an output carrying ONLY that is a genuine
  // no-decision case. Distinguish that from an unparsed output, which is a bug in this script.
  const knownKeys = ['version', 'caseAgent', 'tasksToRun', 'tasksToCancel', 'stagesEntered',
    'stagesCompleted', 'stagesExited', 'caseResolution', 'traces'];
  const unknown = Object.keys(out ?? {}).filter((k) => !knownKeys.includes(k));
  return { input: inputFile, event: evStr || '(no event)', decisions,
    negative: decisions.length === 0, hasOutput: !!out, unknownKeys: unknown };
}

const scenarios = readdirSync(ROOT, { withFileTypes: true })
  .filter((e) => e.isDirectory())
  .map((e) => {
    const dir = join(ROOT, e.name);
    const files = readdirSync(dir);
    const rulesFile = files.find((f) => f.endsWith('rules.json'));
    const rules = rulesFile ? rulesOf(JSON.parse(readFileSync(join(dir, rulesFile), 'utf8'))) : [];
    const pairs = files.filter((f) => f.endsWith('-input.json')).sort().map((f) => pair(dir, f)).filter(Boolean);
    return { name: e.name, rules, pairs };
  })
  .filter((sc) => !SHOW || sc.name.startsWith(SHOW) || sc.name.includes(SHOW))
  .filter((sc) => !TYPE || sc.rules.some((r) => r.type === TYPE))
  .filter((sc) => !GREP || JSON.stringify(sc).toLowerCase().includes(GREP))
  .sort((a, b) => a.name.localeCompare(b.name));

if (JSON_OUT) { console.log(JSON.stringify({ root: ROOT, scenarios }, null, 2)); process.exit(0); }

console.log(`\nspecified behaviour — ${scenarios.length} scenario(s)   ${ROOT}\n`);
for (const sc of scenarios) {
  console.log(`  ${sc.name}`);
  for (const r of sc.rules) {
    // The rule NAME is the specification; print it verbatim.
    console.log(`      ${String(r.type ?? '—').padEnd(18)} ${r.name}`);
    if (SHOW && r.params && Object.keys(r.params).length) {
      console.log(`      ${''.padEnd(18)} ${JSON.stringify(r.params)}`);
    }
  }
  for (const p of sc.pairs) {
    const verdict = p.unknownKeys.length
      ? `?? UNPARSED output keys: ${p.unknownKeys.join(',')} — fix this script, do not read as a negative`
      : p.negative ? 'NOTHING  (negative case — proves selectivity)' : p.decisions.join(', ');
    console.log(`      ${'▸'.padEnd(18)} ${p.event}  →  ${verdict}`);
  }
  console.log('');
}
console.log('A fixture states what the platform is REQUIRED to decide. It outranks a probe');
console.log('(which only says "accepted") and costs seconds rather than minutes per cell.');
console.log('Absence of a fixture is not evidence of absent behaviour — only of absent spec.');
