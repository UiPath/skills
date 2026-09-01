#!/usr/bin/env node
/**
 * run-probes — the automated half of phase 1d. Take the unprobed (rule, slot) cells,
 * emit a minimal case for each, run it through `uip maestro case validate`, classify
 * the verdict, and (with --apply) write the results into semantics.
 *
 *   node run-probes.mjs                      # dry run, report only
 *   node run-probes.mjs --apply              # also record confirmed cells
 *   node run-probes.mjs --only adhoc         # one rule (all slots)
 *   node run-probes.mjs --cell adhoc@stage-exit
 *
 * ~2.6 s per cell. The full unprobed grid is a couple of minutes unattended.
 *
 * THREE THINGS THIS GETS RIGHT THAT A NAIVE LOOP DOES NOT:
 *
 * 1. It supplies each rule's PAYLOAD. Without one you cannot tell "illegal in this
 *    slot" from "I forgot a field" — both surface as a semantic error. Cells probed
 *    without a payload are reported `payload-incomplete` and never recorded as
 *    `legal:false`.
 *
 * 2. It distinguishes OUR gate from THE PLATFORM'S. If check.ts or build() rejects
 *    first, `uip` never saw the case, so there is no verdict to record — that is
 *    `blocked-by-builder`, not evidence. (Observed: sla-status-change needs `{ sla }`,
 *    and our own resolver rejected the probe before the platform could answer.)
 *
 * 3. It records the VERBATIM verdict, because a cell with no evidence must never
 *    become a hard error in check.ts.
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, symlinkSync, copyFileSync, existsSync, chmodSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SKILL = join(HERE, '..');
const REPO = resolve(SKILL, '..', '..', '..');
const SEM_PATH = join(SKILL, 'semantics', 'case-semantics.json');
const sem = JSON.parse(readFileSync(SEM_PATH, 'utf8'));
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const APPLY = process.argv.includes('--apply');
const JSON_OUT = process.argv.includes('--json');

/**
 * What each rule needs to be COMPLETE. `null` = the rule carries no payload.
 * `unsatisfiable` = we cannot build a valid payload offline, so a semantic rejection
 * here is uninformative and must not be read as illegality.
 */
const PAYLOAD = {
  'selected-stage-completed': { stage: 'Alpha' },
  'selected-stage-exited': { stage: 'Alpha' },
  'selected-tasks-completed': { tasks: ['Work'] },
  'sla-status-change': { sla: 'Deadline' },
  'adhoc': { expression: '=js:true' },
  'wait-for-connector': '__unsatisfiable__', // needs a live connector subscription
  'case-entered': null, 'current-stage-entered': null, 'runs-sequentially': null,
  'required-tasks-completed': null, 'required-stages-completed': null,
  'user-selected-stage': null, 'timer': null, 'condition': null, 'stage-complete': null,
};

const lit = (o) => (o == null ? '' : `, ${JSON.stringify(o)}`);

/**
 * Rules that need a COMPANION construct elsewhere in the case to be reachable. Without
 * it the plan validates as unreachable ("will never be met") — which says nothing about
 * whether the rule is legal in that slot, only that the probe was under-specified.
 * `user-selected-stage` needs a `wait-for-user` exit somewhere for a person to choose from.
 */
const COMPANION = {
  'user-selected-stage': { anchorExitType: 'wait-for-user' },
};

/** A minimal case with the rule under test placed in `slot`. Stage Alpha is the anchor. */
function caseSource(rule, slot, payload) {
  const R = `rule('${rule}' as any${lit(payload)})`;
  const anchor = `.stage('Alpha', s => s.required().entryWhen(rule('case-entered'))
    .task('Work', t => t.process('p', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered')))
    .sla({ displayName: 'Deadline', count: 2, unit: 'd', escalations: [escalation({ trigger: 'sla-breached', notify: [toUser('a@b.com')] })] })
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true${COMPANION[rule]?.anchorExitType ? `, type: '${COMPANION[rule].anchorExitType}'` : ''} }))`;
  const bodies = {
    'stage-entry': `${anchor}
  .stage('Beta', s => s.required().entryWhen(${R})
    .task('More', t => t.process('q', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered')))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'))`,
    'stage-exit': `.stage('Alpha', s => s.required().entryWhen(rule('case-entered'))
    .task('Work', t => t.process('p', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered')))
    .sla({ displayName: 'Deadline', count: 2, unit: 'd', escalations: [escalation({ trigger: 'sla-breached', notify: [toUser('a@b.com')] })] })
    .exitWhen(${R}, { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'))`,
    'task-entry': `.stage('Alpha', s => s.required().entryWhen(rule('case-entered'))
    .task('Work', t => t.process('p', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered')))
    .sla({ displayName: 'Deadline', count: 2, unit: 'd', escalations: [escalation({ trigger: 'sla-breached', notify: [toUser('a@b.com')] })] })
    .task('Probe', t => t.process('q', { folder: 'Shared' }).entryWhen(${R}))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'))`,
    'case-exit': `${anchor}
  .completeWhen(${R})`,
  };
  return `import { casePlan, rule, escalation, toUser } from '@uipath/flow-sdk/case';
export default casePlan('probe').name('Probe').identifier('PR')
  ${bodies[slot]}
  .build();
`;
}

/**
 * Disposable authoring workspace.
 *
 * PORTED 2026-08-12 to the current CLI surface. The old harness copied
 * `typescript/sdk/check-case.sh` / `compile-case.sh` into the workspace; upstream
 * DELETED those wrappers and moved the loop into the published package:
 *
 *   check     node node_modules/@uipath/flow-sdk/dist/case/check-cli.js <Name>.case.ts
 *   compile   node node_modules/@uipath/flow-sdk/dist/case/compile-cli.js <Name>.case.ts -o <out>
 *   validate  uip maestro case validate <out> --output json
 *
 * Authors now import from the package subpath `@uipath/flow-sdk/case`, so the probe
 * does too — a symlinked node_modules entry exercises the real `exports` map instead of
 * a deep relative path that no longer reflects how anyone writes a case. We symlink the
 * locally built `typescript/sdk` rather than `npm install`ing the published package: the
 * probe must interrogate the SDK in the working tree, and installing would need
 * NODE_AUTH_TOKEN and pin a released version.
 */
function workspace() {
  const dir = mkdtempSync(join(tmpdir(), 'probe-'));
  writeFileSync(join(dir, 'package.json'), '{"type":"module"}\n');
  mkdirSync(join(dir, 'node_modules', '@uipath'), { recursive: true });
  symlinkSync(join(REPO, 'typescript', 'sdk'), join(dir, 'node_modules', '@uipath', 'flow-sdk'));
  return dir;
}

const SDK_DIST = join(REPO, 'typescript', 'sdk', 'dist', 'case');

/** compile (which runs the source check first) then validate. Returns combined output. */
function compileAndValidate(dir, name) {
  const out = [];
  const run = (cmd, args) => {
    try { out.push(execFileSync(cmd, args, { cwd: dir, encoding: 'utf8', stdio: 'pipe' })); return true; }
    catch (e) { out.push(String(e.stdout ?? ''), String(e.stderr ?? '')); return false; }
  };
  // compile-cli refuses to emit when the source check fails, so a failure here is OUR
  // gate, not the platform's — classify() keys on that distinction.
  const emitted = run('node', [join(SDK_DIST, 'compile-cli.js'), `${name}.case.ts`, '-o', 'caseplan.json']);
  if (emitted) run('uip', ['maestro', 'case', 'validate', 'caseplan.json', '--output', 'json']);
  return out.join('\n');
}

/**
 * Classify one run. Order matters: our own gates must be excluded BEFORE reading a
 * verdict, or a builder-side rejection gets recorded as a platform fact.
 */
function classify(out, payloadSupplied) {
  const clean = out.replace(/^Updating.*$|^Update .*$|.*pinned version.*$/gm, '');
  const ourGate = /\[([A-Z_]+)\]/.exec(clean);
  if (/Cannot build case|CaseBuildError/.test(clean)) return { outcome: 'blocked-by-builder', detail: 'build() threw before serialization', verdict: firstLine(clean) };
  // OUR gates, in the shapes the package CLIs emit. If any fires, `uip` never ran.
  if (/^check: \d+ error/m.test(clean) && ourGate) return { outcome: 'blocked-by-builder', detail: `check.ts ${ourGate[1]} rejected it; uip never saw this case`, verdict: firstLine(clean) };
  if (/compile: \d+ error|not emitting|references unknown/.test(clean)) return { outcome: 'blocked-by-builder', detail: 'the SDK check/resolver rejected it before emit', verdict: firstLine(clean) };
  if (/Cannot find (module|package)|ERR_MODULE_NOT_FOUND/.test(clean)) return { outcome: 'blocked-by-builder', detail: 'workspace wiring broken — the probe never compiled', verdict: firstLine(clean) };
  if (/"Status":\s*"Valid"/.test(clean)) return { outcome: 'accepted', legal: true, verdictClass: 'accepted', verdict: '"Status": "Valid"' };
  const err = /\[error\][^\\"]{0,160}/.exec(clean)?.[0]?.trim();
  // REACHABILITY is a third category beside legal/illegal: the rule was ACCEPTED in the
  // slot, but the resulting graph is unsatisfiable. Usually the probe is missing a
  // companion construct rather than the placement being wrong — so never record it as
  // a placement fact.
  if (/will never be met|unreachable/i.test(clean)) {
    return { outcome: 'unreachable', verdictClass: 'unreachable', verdict: err ?? 'will never be met',
             note: 'rule accepted in the slot; the graph is unsatisfiable. Supply the companion construct (see COMPANION) and re-probe before drawing any placement conclusion.' };
  }
  if (/Invalid input|Invalid option/.test(clean)) return { outcome: 'rejected', legal: false, verdictClass: 'illegal-in-slot', verdict: err ?? 'Invalid input', note: 'Cross-check the CLI VALID_RULE_TYPES: if the rule is in it, this is a slot rejection, not an unknown rule.' };
  if (err) {
    return payloadSupplied
      ? { outcome: 'rejected', legal: false, verdictClass: 'illegal-in-slot', verdict: err, note: 'semantic rejection WITH a complete payload' }
      : { outcome: 'inconclusive', verdictClass: 'payload-incomplete', verdict: err, note: 'semantic rejection with NO payload — cannot distinguish illegal-slot from missing field' };
  }
  return { outcome: 'inconclusive', verdict: firstLine(clean) || '(no recognisable verdict)' };
}
const firstLine = (s) => s.split('\n').map((l) => l.trim()).filter(Boolean)[0]?.slice(0, 160) ?? '';

// ── pick the work ────────────────────────────────────────────────────────────
const slots = sem.rulePlacement.slots;
const probed = new Set(sem.rulePlacement.cells.map((c) => `${c.rule}@${c.slot}`));
let targets = [];
const one = arg('--cell');
if (one) {
  const [r, s] = one.split('@');
  targets = [{ rule: r, slot: s }];
} else {
  const only = arg('--only');
  const rules = Object.keys(PAYLOAD).filter((r) => !only || r === only);
  targets = rules.flatMap((r) => slots.filter((s) => !probed.has(`${r}@${s}`)).map((s) => ({ rule: r, slot: s })));
}
if (!targets.length) { console.log('run-probes: nothing to probe — every cell in the payload table is already recorded.'); process.exit(0); }
for (const f of ['case-sdk.js', 'compile-cli.js']) {
  if (!existsSync(join(SDK_DIST, f))) {
    console.error(`run-probes: ${f} missing from ${SDK_DIST}.`);
    console.error('Run `npm run build` in typescript/sdk first — the probe interrogates the WORKING TREE build.');
    process.exit(2);
  }
}

// ── run ──────────────────────────────────────────────────────────────────────
const dir = workspace();
const results = [];
for (const t of targets) {
  const p = PAYLOAD[t.rule];
  const unsat = p === '__unsatisfiable__';
  const payload = unsat ? null : p;
  writeFileSync(join(dir, 'Probe.case.ts'), caseSource(t.rule, t.slot, payload));
  const out = compileAndValidate(dir, 'Probe');
  const c = classify(out, payload != null);
  if (unsat && c.outcome === 'rejected') { c.outcome = 'inconclusive'; c.note = 'payload is unsatisfiable offline (needs a live connector subscription) — rejection is uninformative'; delete c.legal; }
  results.push({ ...t, payload: unsat ? '(unsatisfiable offline)' : payload, ...c });
  if (!JSON_OUT) console.log(`${(t.rule + '@' + t.slot).padEnd(42)} ${String(c.outcome).padEnd(20)} ${String(c.verdict).slice(0, 70)}`);
}

// ── apply ────────────────────────────────────────────────────────────────────
const recordable = results.filter((r) => r.outcome === 'accepted' || r.outcome === 'rejected');
if (APPLY && recordable.length) {
  for (const r of recordable) {
    const args = ['--cell', `${r.rule}@${r.slot}`, '--legal', String(r.legal), '--verdict', r.verdict, '--class', r.verdictClass];
    if (r.note) args.push('--guidance', `${r.note} (run-probes, payload: ${JSON.stringify(r.payload)})`);
    execFileSync('node', [join(HERE, 'semantics-update.mjs'), ...args], { cwd: REPO, stdio: 'ignore' });
  }
  console.log(`\napplied ${recordable.length} cell(s) to semantics.`);
}

if (JSON_OUT) { console.log(JSON.stringify({ results }, null, 2)); process.exit(0); }
const by = (o) => results.filter((r) => r.outcome === o).length;
console.log(`\n${results.length} probed  |  accepted ${by('accepted')}  rejected ${by('rejected')}  inconclusive ${by('inconclusive')}  blocked-by-builder ${by('blocked-by-builder')}`);
if (by('blocked-by-builder')) console.log('blocked-by-builder = OUR gate fired first; uip never answered. Not evidence — fix the probe payload or the gate.');
if (by('inconclusive')) console.log('inconclusive = no payload, or a payload we cannot satisfy offline. Never recorded as legal:false.');
if (!APPLY && recordable.length) console.log(`\n${recordable.length} cell(s) are recordable — re-run with --apply to write them.`);
