#!/usr/bin/env node
/**
 * semantics-update — write a finding back into case-semantics.json. The self-update
 * half of the loop: gaps -> probe/ask -> record -> regenerate.
 *
 * Refuses to record a claim without provenance. That refusal is the whole safety
 * property: the failures this skill exists to prevent were all confident claims with
 * no recorded verdict behind them.
 *
 *   # a probe result (becomes status 'confirmed')
 *   node semantics-update.mjs --cell "adhoc@stage-entry" --legal true \
 *        --verdict "Status: Valid" [--guidance "..."]
 *
 *   # a human answer (becomes status 'asserted' — deliberately weaker)
 *   node semantics-update.mjs --interview version-pin-intent \
 *        --answer "deliberate until Q4" --who cliff
 *
 *   # restamp provenance after re-probing against current tooling
 *   node semantics-update.mjs --restamp
 *
 * --date lets a caller pass today's date (the runtime forbids Date.now() in some
 * harnesses); it defaults to the system date when omitted.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const SEM_PATH = join(HERE, '..', 'semantics', 'case-semantics.json');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const today = arg('--date', new Date().toISOString().slice(0, 10));
const sem = JSON.parse(readFileSync(SEM_PATH, 'utf8'));
const sh = (c, a) => { try { return execFileSync(c, a, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { return null; } };
const save = () => writeFileSync(SEM_PATH, JSON.stringify(sem, null, 2) + '\n');

// ── probe result -> a placement cell ─────────────────────────────────────────
const cell = arg('--cell');
if (cell) {
  const [rule, slot] = cell.split('@');
  const legalArg = arg('--legal');
  const verdict = arg('--verdict');
  if (!rule || !slot) { console.error('--cell must be "<rule>@<slot>"'); process.exit(2); }
  if (legalArg !== 'true' && legalArg !== 'false') { console.error('--legal must be true or false'); process.exit(2); }
  if (!verdict) {
    console.error('REFUSED: --verdict is required.');
    console.error('Record the VERBATIM uip output. A cell with no verdict is a claim with no evidence,');
    console.error('and only verdict-backed cells may become hard errors in check.ts.');
    process.exit(2);
  }
  if (!sem.rulePlacement.slots.includes(slot)) {
    console.error(`Unknown slot "${slot}". Known: ${sem.rulePlacement.slots.join(', ')}`);
    process.exit(2);
  }
  const legal = legalArg === 'true';
  const looksUnrecognised = /invalid input|invalid option/i.test(verdict);
  // Verdict text cannot decide legality on its own, so the class is explicit.
  // 'task selection missing' is semantic yet the rule is genuinely illegal at stage
  // entry (re-probed WITH the payload); 'has no SLA selected' is semantic and the rule
  // is legal. Same shape of message, opposite meaning.
  let cls = arg('--class');
  if (!cls) cls = looksUnrecognised ? 'unrecognised' : legal ? (/missing|has no/i.test(verdict) ? 'payload-incomplete' : 'accepted') : null;
  if (!cls) {
    console.error('REFUSED: --class is required for legal:false with a semantic verdict.');
    console.error('  unrecognised    — "Invalid input"/"Invalid option"; the rule does not exist here');
    console.error('  illegal-in-slot — rejected EVEN WITH a complete payload (re-probe to be sure)');
    console.error('If you have not probed it with the payload supplied, do that first: a short');
    console.error('payload looks identical to an illegal slot, and guessing invents a false gate.');
    process.exit(2);
  }
  if (!legal && !['unrecognised', 'illegal-in-slot'].includes(cls)) {
    console.error(`REFUSED: legal:false cannot carry class "${cls}" — that class means the rule IS legal here.`);
    process.exit(2);
  }
  const existing = sem.rulePlacement.cells.find((c) => c.rule === rule && c.slot === slot);
  const entry = { rule, slot, legal, status: 'confirmed', verdict, verdictClass: cls, probedOn: today, ...(arg('--guidance') ? { guidance: arg('--guidance') } : {}) };
  if (existing) { Object.assign(existing, entry); console.log(`updated cell ${cell}`); }
  else { sem.rulePlacement.cells.push(entry); console.log(`added cell ${cell}`); }
  sem.rulePlacement.cells.sort((a, b) => (a.rule + a.slot).localeCompare(b.rule + b.slot));
  save();
  console.log(`  legal=${legal}  verdict="${verdict}"`);
  console.log('  next: re-run emit-sdk.mjs and gen-case-skill.mjs so consumers pick it up.');
  process.exit(0);
}

// ── human answer -> recorded as 'asserted', never 'confirmed' ────────────────
const interviewId = arg('--interview');
if (interviewId) {
  const answer = arg('--answer');
  const who = arg('--who');
  if (!answer || !who) {
    console.error('REFUSED: --answer and --who are both required.');
    console.error('An unattributed assertion cannot be re-checked with the person who made it.');
    process.exit(2);
  }
  sem.interviewAnswers ??= [];
  const prior = sem.interviewAnswers.find((a) => a.id === interviewId);
  const rec = {
    id: interviewId, answer, who, askedOn: today, status: 'asserted',
    $note: 'HUMAN ASSERTION — not evidence of platform behaviour. If this claims something an artifact could decide, probe it and supersede this entry.',
  };
  if (prior) Object.assign(prior, rec); else sem.interviewAnswers.push(rec);
  // If it resolved a known unknown, mark it — but do not delete the unknown; the
  // question stays visible until an artifact settles it.
  const ku = sem.knownUnknowns.find((u) => u.id === interviewId);
  if (ku) ku.assertedAnswer = { answer, who, askedOn: today };
  save();
  console.log(`recorded interview answer "${interviewId}" as status 'asserted' (by ${who})`);
  if (ku) console.log('  the knownUnknown remains open — a human answer does not settle it.');
  process.exit(0);
}

// ── restamp provenance ───────────────────────────────────────────────────────
if (process.argv.includes('--restamp')) {
  const cli = (sh('uip', ['--version']) || '').split('\n').pop();
  const pkg = sh('node', ['-p', "require('./typescript/node_modules/@uipath/case-schema/package.json').version"]);
  const emits = (sh('grep', ['-o', "_version = '[0-9.]*'", 'typescript/sdk/src/case/case-sdk.ts']) || '').replace(/.*'([^']*)'.*/, '$1');
  const fe = sh('git', ['-C', `${process.env.HOME}/src/PO.Frontend`, 'log', '--oneline', '-1']);
  if (cli) sem.$provenance.cli = `uip ${cli}`;
  if (pkg) sem.$provenance.package = `@uipath/case-schema@${pkg}`;
  if (emits) sem.$provenance.schemaEmitted = emits;
  if (fe) sem.$provenance.mainline = fe;
  sem.$provenance.probedOn = today;
  save();
  console.log('restamped $provenance:', JSON.stringify(sem.$provenance, null, 2));
  console.warn('\n⚠ Restamping records WHEN, not WHETHER. If the tooling moved, the cells');
  console.warn('  themselves may now be wrong — re-run the probes before trusting them.');
  process.exit(0);
}

console.error('nothing to do. Pass --cell, --interview, or --restamp (see header).');
process.exit(2);
