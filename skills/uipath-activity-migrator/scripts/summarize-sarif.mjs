#!/usr/bin/env node
// summarize-sarif.mjs — classify a UiPath Activity Migrator SARIF log.
//
// Usage: node summarize-sarif.mjs <file.sarif | folder> [--out <file.md>] [--json]
//   folder      → the newest *.sarif inside it is used
//   --out FILE  → write the full per-item report (every list, rule counts) to FILE; stdout stays short
//   --json      → full classification as JSON instead of the Markdown summary
// stdout is a short summary: status, counts, blockers, and what needs attention grouped by reason
// and by file. Items are listed inline only when there are few (INLINE_LIMIT).
// Input may be UTF-8 (with or without BOM) or UTF-16 (PowerShell 5.1 redirection).
// No dependencies. Node 18+.

import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, basename } from 'node:path';

// Core (tool-owned) rule prefixes, used only to label the family in the output.
const CORE_PREFIXES = ['PROJECT-', 'XAML-', 'RESTORE-', 'ASSEMBLY-', 'REPAIR_', 'TYPE-', 'REFERENCES-', 'OBSOLETE-', 'WORKFLOW-'];
// Project-level stop conditions that extensions report below error level (the tool's own core
// failures need no list: any non-activity-scoped error is critical, see isCritical below).
const WARNING_LEVEL_BLOCKERS = new Set([
  'UIAUTOMATION-INVALID-UIA-PACKAGE', 'UIAUTOMATION-LANGUAGE-NOT-SUPPORTED',
  'UIAUTOMATION-PROJECT-SETTINGS-CONFIGURATION-NOT-SUPPORTED',
]);
// Per-file issues: reported, carried into verification, never fatal for the run.
const TYPE_ISSUES = new Set([
  'TYPE-MISSING', 'TYPE-CHECK', 'WORKFLOW-COMPILATION-ERROR', 'WORKFLOW-VALIDATION-ISSUE', 'REPAIR_LOCAL_ASSEMBLIES',
  'WORKFLOW-LOAD',
]);
// Activity- or workflow-scoped extension rules: an error there means one activity was left classic, not a failed run.
const isActivityScoped = (id) => /^UIAUTOMATION-(ACTIVITY|WORKFLOW)-/.test(id) || id.endsWith('-ACTIVITY-MIGRATION');
const isCritical = (id, lvl) => lvl === 'error' && !isActivityScoped(id) && !TYPE_ISSUES.has(id);
const ACTION_TAG = '[PostMigration Action Required]';
const INLINE_LIMIT = 10;
const MSG_LIMIT = 320;

const args = process.argv.slice(2);
const wantJson = args.includes('--json');
let outFile = null;
let target = null;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--out') { outFile = args[++i] || null; continue; }
  if (args[i] === '--json') continue;
  if (!args[i].startsWith('--') && !target) target = args[i];
}
if (!target) {
  console.error('usage: node summarize-sarif.mjs <file.sarif | folder> [--out <file.md>] [--json]');
  process.exit(2);
}

function pickFile(p) {
  const st = statSync(p);
  if (!st.isDirectory()) return p;
  const files = readdirSync(p)
    .filter((f) => f.toLowerCase().endsWith('.sarif'))
    .map((f) => ({ f: join(p, f), m: statSync(join(p, f)).mtimeMs }))
    .sort((a, b) => b.m - a.m);
  if (!files.length) {
    console.error(`no .sarif files in ${p}`);
    process.exit(2);
  }
  return files[0].f;
}

function decode(buf) {
  if (buf.length >= 2 && buf[0] === 0xff && buf[1] === 0xfe) return buf.toString('utf16le', 2);
  if (buf.length >= 2 && buf[0] === 0xfe && buf[1] === 0xff) {
    const sw = Buffer.alloc(buf.length - 2);
    for (let i = 2; i + 1 < buf.length; i += 2) { sw[i - 2] = buf[i + 1]; sw[i - 1] = buf[i]; }
    return sw.toString('utf16le');
  }
  if (buf.length >= 3 && buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf) return buf.toString('utf8', 3);
  return buf.toString('utf8');
}

function parseSarif(text) {
  try { return JSON.parse(text); } catch { /* fall through */ }
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end <= start) throw new Error('no JSON object found');
  return JSON.parse(text.slice(start, end + 1));
}

const file = pickFile(target);
let sarif;
try {
  sarif = parseSarif(decode(readFileSync(file)));
} catch (e) {
  console.error(`cannot parse ${file}: ${e.message}`);
  process.exit(2);
}

const run = (sarif.runs && sarif.runs[0]) || {};
const rules = new Map(((run.tool && run.tool.driver && run.tool.driver.rules) || []).map((r) => [r.id, r]));
const results = run.results || [];

const levelOf = (r) => r.level || (rules.get(r.ruleId) && rules.get(r.ruleId).defaultConfiguration && rules.get(r.ruleId).defaultConfiguration.level) || 'note';
const fileOf = (r) => {
  const loc = r.locations && r.locations[0] && r.locations[0].physicalLocation && r.locations[0].physicalLocation.artifactLocation;
  return (loc && (loc.uri || loc.description)) || '';
};
const msgOf = (r) => {
  const m = (r.message && (r.message.text || r.message.markdown)) || '';
  return m.length > MSG_LIMIT ? m.slice(0, MSG_LIMIT) + '…' : m;
};
const propsOf = (r) => r.properties || {};
const activityOf = (r) => {
  const p = propsOf(r);
  return p.sourceActivity || p.activityType || p.destinationActivity || '';
};
const familyOf = (id) => {
  if (!id) return 'other';
  if (id.startsWith('UIAUTOMATION-')) return 'uia';
  if (id.endsWith('-ACTIVITY-MIGRATION')) return 'productivity';
  if (id.endsWith('-PACKAGE-UPGRADE') || id.endsWith('-PACKAGE-MIGRATION')) return 'package';
  if (CORE_PREFIXES.some((p) => id.startsWith(p))) return 'core';
  return 'other';
};

const byRule = {};
const byLevel = { error: 0, warning: 0, note: 0 };
const byFamily = {};
const blockers = [];
const packages = [];
const effectiveVersions = {};
const typeIssues = [];
const actionRequired = [];
const uia = { migrated: 0, migratedByType: {}, migratedItems: [], notMigrated: [], partial: [], warnings: [], workflow: [] };
const productivity = { migrated: 0, notMigrated: [], warnings: [] };
let frameworkChanged = false;
let hasCriticalError = false;
let sawValidation = false;

for (const r of results) {
  const id = r.ruleId || '';
  const lvl = levelOf(r);
  const fam = familyOf(id);
  byLevel[lvl] = (byLevel[lvl] || 0) + 1;
  byRule[id] = byRule[id] || { level: lvl, count: 0 };
  byRule[id].count += 1;
  byFamily[fam] = byFamily[fam] || { error: 0, warning: 0, note: 0 };
  byFamily[fam][lvl] = (byFamily[fam][lvl] || 0) + 1;

  // Reason suffix of an extension rule id, e.g. UIAUTOMATION-ACTIVITY-MIGRATION-WARNING-VariableSelector → VariableSelector.
  // A bare outcome (…-MIGRATION-ERROR with no suffix) gets a plain label; the message carries the detail.
  const reasonMatch = id.match(/-(?:ERROR|WARNING|INFO)-(.+)$/);
  const bareOutcome = id.match(/-MIGRATION-(ERROR|WARNING|PARTIAL)$/);
  let reason = '';
  if (reasonMatch) reason = reasonMatch[1];
  else if (bareOutcome && bareOutcome[1] === 'WARNING') {
    // Message shape: "<display name> - Type: <type> migrated with warnings in N ms. Warnings: Property: <path> - <text>. <more>"
    // The grouping label is the first sentence of <text>, which is templated and therefore identical across activities.
    const body = (msgOf(r).match(/(?:Warnings|Errors):\s*(?:Property:\s*\S+\s*-\s*)?([\s\S]+)/) || [])[1] || msgOf(r);
    reason = (body.split(/(?<=[.!?])\s/)[0] || 'warning').replace(/[.!?]$/, '').trim().slice(0, 110);
  }
  else if (bareOutcome) reason = { ERROR: 'not migrated', PARTIAL: 'partial' }[bareOutcome[1]];
  const entry = { rule: id, level: lvl, file: fileOf(r), activity: activityOf(r), guid: propsOf(r).activityGuid || '', property: propsOf(r).propertyName || '', reason, bare: Boolean(bareOutcome), outcome: (bareOutcome || reasonMatch ? (id.match(/-(ERROR|WARNING|PARTIAL|INFO)(?:-|$)/) || [])[1] : '') || '', message: msgOf(r) };

  const critical = isCritical(id, lvl);
  if (critical) hasCriticalError = true;
  if (id.startsWith('WORKFLOW-VALIDATION') || id === 'WORKFLOW-COMPILATION-ERROR') sawValidation = true;
  if (id === 'PROJECT-FRAMEWORK-UPDATE') frameworkChanged = true;
  if (id === 'RESTORE-PACKAGE-UPGRADE' || id.endsWith('-PACKAGE-UPGRADE') || id.endsWith('-PACKAGE-MIGRATION')) {
    packages.push(entry.message);
    // "Updated package 'X' from 'a' to 'b'." / "Upgraded package 'X' from version 'a' to compatible .NET Core version 'b'"
    const m = entry.message.match(/package '([^']+)' from (?:version )?'([^']+)' to (?:compatible \.NET Core version )?'([^']+)'/i);
    if (m) effectiveVersions[m[1]] = { from: m[2], to: m[3] };
  }
  if (critical || WARNING_LEVEL_BLOCKERS.has(id)) blockers.push(entry);
  if (TYPE_ISSUES.has(id) && lvl !== 'note') typeIssues.push(entry);
  if (entry.message.includes(ACTION_TAG)) actionRequired.push(entry);

  if (fam === 'uia') {
    if (/^UIAUTOMATION-ACTIVITY-.+-MIGRATION-SUCCESS$/.test(id)) {
      uia.migrated += 1;
      // destinationActivity in the SARIF is the migrated activity's display name (kept equal to the
      // source), not its modern type; the modern type is only visible in the output XAML.
      const fullType = propsOf(r).activityType || id.replace(/^UIAUTOMATION-ACTIVITY-/, '').replace(/-MIGRATION-SUCCESS$/, '');
      const type = fullType.split('.').pop();
      uia.migratedByType[type] = (uia.migratedByType[type] || 0) + 1;
      // Ledger for the runtime check: which activities the tool rewrote, so a failing run can be attributed.
      uia.migratedItems.push({ file: entry.file, activity: entry.activity, guid: entry.guid, type });
    } else if (id.startsWith('UIAUTOMATION-ACTIVITY-MIGRATION-ERROR')) {
      uia.notMigrated.push(entry);
    } else if (id === 'UIAUTOMATION-ACTIVITY-MIGRATION-PARTIAL') {
      uia.partial.push(entry);
    } else if (id.startsWith('UIAUTOMATION-ACTIVITY-MIGRATION-WARNING')) {
      uia.warnings.push(entry);
    } else if (id.startsWith('UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-')) {
      uia.warnings.push(entry);
    } else if (id.startsWith('UIAUTOMATION-WORKFLOW-')) {
      uia.workflow.push(entry);
    }
  } else if (fam === 'productivity') {
    if (lvl === 'error') productivity.notMigrated.push(entry);
    else if (lvl === 'warning') productivity.warnings.push(entry);
    else productivity.migrated += 1;
  }
}

// Status keys off rule IDs as well as levels: the UIA extension reports unmigrated
// activities at note or warning level, so a level-only reading would call them success.
const leftovers = uia.notMigrated.length + uia.partial.length + uia.warnings.length + productivity.notMigrated.length + productivity.warnings.length + actionRequired.length + typeIssues.length;
let status;
if (hasCriticalError || blockers.length > 0) status = 'failed';
else if (results.length === 0) status = 'unknown';
else if (!sawValidation && !results.some((r) => (r.ruleId || '') === 'PROJECT-COPY')) status = byLevel.error > 0 ? 'failed' : 'unknown';
else if (byLevel.error > 0 || byLevel.warning > 0 || leftovers > 0) status = 'partial';
else status = 'success';

// Everything that needs a human decision or hand, grouped for the short summary.
// Everything that needs a human decision or hand: activities left classic or partially migrated,
// activity/property warnings (they become [PostMigration Action Required] annotations in the XAML),
// productivity warnings, and per-file type issues. One SARIF result may sit in several lists; dedupe.
const attentionResults = [...new Set([
  ...uia.notMigrated, ...uia.partial, ...uia.warnings, ...productivity.notMigrated, ...productivity.warnings,
  ...actionRequired, ...typeIssues,
])];
const countBy = (items, keyFn) => {
  const m = new Map();
  for (const it of items) { const k = keyFn(it); m.set(k, (m.get(k) || 0) + 1); }
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
};
// Headline count is per activity: an activity with an activity-level and a property-level result is one item.
// The tool emits two results per finding: an activity-level one with a bare rule id carrying the prose,
// and a property-level one carrying the reason suffix. Group per activity; a bare result is the prose
// companion of a suffixed result with the same outcome and adds no reason of its own. It keeps its label
// only when it is the sole result for that activity.
const activityMap = new Map();
for (const e of attentionResults) {
  // The tool stamps every result about one activity with the same activityGuid; the display name is the fallback.
  const key = `${e.file}::${e.guid || e.activity || e.rule}`;
  const slot = activityMap.get(key) || { file: e.file, activity: e.activity, reasons: [], bareByOutcome: {}, suffixedOutcomes: new Set(), messages: [] };
  if (e.bare) slot.bareByOutcome[e.outcome] = e.reason || e.rule;
  else {
    slot.suffixedOutcomes.add(e.outcome);
    if (!slot.reasons.includes(e.reason || e.rule)) slot.reasons.push(e.reason || e.rule);
  }
  if (e.message && !slot.messages.includes(e.message)) slot.messages.push(e.message);
  activityMap.set(key, slot);
}
for (const slot of activityMap.values()) {
  for (const [outcome, label] of Object.entries(slot.bareByOutcome)) if (!slot.suffixedOutcomes.has(outcome) && !slot.reasons.includes(label)) slot.reasons.push(label);
  delete slot.bareByOutcome;
  delete slot.suffixedOutcomes;
}
const attention = [...activityMap.values()];
// Per activity, one count per distinct reason: sums to the activity count unless an activity has several reasons.
const attentionByReason = countBy(attention.flatMap((a) => a.reasons), (x) => x);
const attentionByFile = countBy(attention, (e) => e.file || '(project)');
const migratedTotal = uia.migrated + productivity.migrated;
const unknownRules = Object.entries(byRule).filter(([id]) => familyOf(id) === 'other');

const summary = {
  file,
  status,
  outputPath: (run.properties && run.properties.outputPath) || null,
  totals: { results: results.length, ...byLevel, migrated: migratedTotal, attention: attention.length, attentionResults: attentionResults.length },
  frameworkChanged,
  packages,
  effectiveVersions,
  blockers,
  attention: { total: attention.length, results: attentionResults.length, byReason: Object.fromEntries(attentionByReason), byFile: Object.fromEntries(attentionByFile), items: attention },
  byFamily,
  uia,
  productivity,
  typeIssues,
  actionRequired,
  unknownRules: Object.fromEntries(unknownRules),
  byRule,
  files: [...new Set(results.map(fileOf).filter(Boolean))].sort(),
};

if (wantJson) {
  console.log(JSON.stringify(summary, null, 2));
  process.exit(0);
}

const loc = (e) => `${e.file || '(project)'}${e.activity ? ': ' + e.activity : ''}${e.property ? ' / ' + e.property : ''}`;
const itemLine = (e) => `- ${loc(e)} — ${e.reason || e.rule}${e.message ? ': ' + e.message : ''}`;
const pkgLine = Object.entries(effectiveVersions).map(([p, v]) => `${p} ${v.from} → ${v.to}`).join('; ') || packages.join('; ');

// --- short summary (stdout) --------------------------------------------------
const out = [];
out.push(`# Migration summary — ${basename(file)}`);
out.push('');
out.push(`Status: **${status}** | ${migratedTotal} activities migrated | ${attention.length} need attention | ${blockers.length} blockers${summary.outputPath ? ` | Output: ${summary.outputPath}` : ''}`);
if (frameworkChanged) out.push('Framework: Legacy → Windows');
if (pkgLine) out.push(`Packages: ${pkgLine}`);
if (blockers.length) {
  out.push('', `## Blockers (${blockers.length})`);
  for (const b of blockers) out.push(`- **${b.rule}** — ${b.message}${b.file ? ` (${b.file})` : ''}`);
}
if (attention.length) {
  out.push('', `## Needs attention (${attention.length})`);
  out.push(`- By reason: ${attentionByReason.map(([k, n]) => `${k} ×${n}`).join(', ')}`);
  out.push(`- By file: ${attentionByFile.slice(0, 5).map(([k, n]) => `${k} (${n})`).join(', ')}${attentionByFile.length > 5 ? `, … ${attentionByFile.length - 5} more files` : ''}`);
  if (attention.length <= INLINE_LIMIT) { for (const a of attention) out.push(`- ${a.file || '(project)'}${a.activity ? ': ' + a.activity : ''} — ${a.reasons.join('; ')}${a.messages[0] ? ': ' + a.messages[0] : ''}`); }
  else out.push(outFile ? `- Full list: ${outFile}` : '- Full list: rerun with --out <file.md>');
}
if (unknownRules.length) {
  out.push('', '## Rules outside the known families (read their descriptions in tool.driver.rules)');
  for (const [id, v] of unknownRules) out.push(`- ${id} [${v.level}] ×${v.count}`);
}
console.log(out.join('\n'));

// --- full report (file) --------------------------------------------------------
if (outFile) {
  const md = [];
  const section = (title, items, fmt) => {
    if (!items.length) return;
    md.push('', `## ${title} (${items.length})`);
    for (const it of items) md.push(fmt(it));
  };
  md.push(`# Migration report — ${basename(file)}`, '');
  md.push(`Status: **${status}** | ${migratedTotal} activities migrated | ${attention.length} need attention | ${blockers.length} blockers${summary.outputPath ? ` | Output: ${summary.outputPath}` : ''}`);
  if (frameworkChanged) md.push('Framework: Legacy → Windows');
  if (pkgLine) md.push(`Packages: ${pkgLine}`);
  if (Object.keys(uia.migratedByType).length) md.push(`Migrated by classic type: ${Object.entries(uia.migratedByType).map(([t, n]) => `${t} ×${n}`).join(', ')}`);
  section('Blockers', blockers, (e) => `- **${e.rule}** — ${e.message}${e.file ? ` (${e.file})` : ''}`);
  section('UIA not migrated', uia.notMigrated, itemLine);
  section('UIA partial', uia.partial, itemLine);
  section('Manual action required', actionRequired, itemLine);
  section('Type / compile issues', typeIssues, itemLine);
  section('Productivity not migrated', productivity.notMigrated, itemLine);
  section('Productivity warnings', productivity.warnings, itemLine);
  section('UIA warnings (activity and property), informational', uia.warnings.filter((e) => !e.message.includes(ACTION_TAG)), itemLine);
  section('UIA workflow-level', uia.workflow, (e) => `- ${e.file || '(project)'} — ${e.rule}: ${e.message}`);
  md.push('', '## Rule counts', '| Rule | Level | Count |', '|---|---|---|');
  for (const [id, v] of Object.entries(byRule).sort((a, b) => b[1].count - a[1].count)) md.push(`| ${id} | ${v.level} | ${v.count} |`);
  writeFileSync(outFile, md.join('\n') + '\n', 'utf8');
}
