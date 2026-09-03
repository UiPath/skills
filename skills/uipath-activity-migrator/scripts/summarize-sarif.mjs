#!/usr/bin/env node
// summarize-sarif.mjs — classify a UiPath Activity Migrator SARIF log.
//
// Usage: node summarize-sarif.mjs <file.sarif | folder> [--json]
//   folder  → the newest *.sarif inside it is used
//   --json  → full classification as JSON instead of the Markdown summary
// Input may be UTF-8 (with or without BOM) or UTF-16 (PowerShell 5.1 redirection).
// No dependencies. Node 18+.

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, basename } from 'node:path';

const CORE_CRITICAL = new Set([
  'PROJECT-LOAD', 'XAML-WORKFLOW-PARSE', 'RESTORE-MISSING-PACKAGE', 'RESTORE-INCOMPATIBLE-PACKAGE',
  'RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED', 'ASSEMBLY-LOAD', 'WORKFLOW-LOAD', 'PROJECT-COPY',
]);
const CORE_RULES = new Set([
  ...CORE_CRITICAL, 'PROJECT-FRAMEWORK-UPDATE', 'RESTORE-PACKAGE', 'RESTORE-PACKAGE-UPGRADE',
  'REPAIR_LOCAL_ASSEMBLIES', 'TYPE-CHECK', 'TYPE-MISSING', 'REFERENCES-FIX', 'OBSOLETE-UIPATH-CORE-REPLACEMENT',
  'WORKFLOW-VALIDATION-SUCCESS', 'WORKFLOW-VALIDATION-ISSUE', 'WORKFLOW-COMPILATION-ERROR',
]);
const BLOCKERS = new Set([
  'RESTORE-MISSING-PACKAGE', 'RESTORE-INCOMPATIBLE-PACKAGE', 'RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED',
  'UIAUTOMATION-INVALID-UIA-PACKAGE', 'UIAUTOMATION-LANGUAGE-NOT-SUPPORTED',
  'UIAUTOMATION-PROJECT-SETTINGS-CONFIGURATION-NOT-SUPPORTED',
]);
const TYPE_ISSUES = new Set([
  'TYPE-MISSING', 'TYPE-CHECK', 'WORKFLOW-COMPILATION-ERROR', 'WORKFLOW-VALIDATION-ISSUE', 'REPAIR_LOCAL_ASSEMBLIES',
]);
const ACTION_TAG = '[PostMigration Action Required]';
const LIST_LIMIT = 60;
const MSG_LIMIT = 220;

const args = process.argv.slice(2);
const wantJson = args.includes('--json');
const target = args.find((a) => !a.startsWith('--'));
if (!target) {
  console.error('usage: node summarize-sarif.mjs <file.sarif | folder> [--json]');
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
  if (CORE_RULES.has(id)) return 'core';
  return 'other';
};
const reasonOf = (id, prefix) => (id.startsWith(prefix + '-') ? id.slice(prefix.length + 1) : '');

const byRule = {};
const byLevel = { error: 0, warning: 0, note: 0 };
const byFamily = {};
const blockers = [];
const packages = [];
const effectiveVersions = {};
const typeIssues = [];
const actionRequired = [];
const uia = { migrated: 0, migratedByType: {}, notMigrated: [], partial: [], warnings: [], workflow: [] };
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

  const entry = { rule: id, level: lvl, file: fileOf(r), activity: activityOf(r), property: propsOf(r).propertyName || '', message: msgOf(r) };

  if (CORE_CRITICAL.has(id) && lvl === 'error') hasCriticalError = true;
  if (id.startsWith('WORKFLOW-VALIDATION') || id === 'WORKFLOW-COMPILATION-ERROR') sawValidation = true;
  if (id === 'PROJECT-FRAMEWORK-UPDATE') frameworkChanged = true;
  if (id === 'RESTORE-PACKAGE-UPGRADE' || id.endsWith('-PACKAGE-UPGRADE') || id.endsWith('-PACKAGE-MIGRATION')) {
    packages.push(entry.message);
    // "Updated package 'X' from 'a' to 'b'." / "Upgraded package 'X' from version 'a' to compatible .NET Core version 'b'"
    const m = entry.message.match(/package '([^']+)' from (?:version )?'([^']+)' to (?:compatible \.NET Core version )?'([^']+)'/i);
    if (m) effectiveVersions[m[1]] = { from: m[2], to: m[3] };
  }
  if (BLOCKERS.has(id)) blockers.push(entry);
  if (TYPE_ISSUES.has(id) && lvl !== 'note') typeIssues.push(entry);
  if (entry.message.includes(ACTION_TAG)) actionRequired.push(entry);

  if (fam === 'uia') {
    if (/^UIAUTOMATION-ACTIVITY-.+-MIGRATION-SUCCESS$/.test(id)) {
      uia.migrated += 1;
      const fullType = propsOf(r).activityType || id.replace(/^UIAUTOMATION-ACTIVITY-/, '').replace(/-MIGRATION-SUCCESS$/, '');
      const type = fullType.split('.').pop();
      uia.migratedByType[type] = (uia.migratedByType[type] || 0) + 1;
    } else if (id.startsWith('UIAUTOMATION-ACTIVITY-MIGRATION-ERROR')) {
      uia.notMigrated.push({ ...entry, reason: reasonOf(id, 'UIAUTOMATION-ACTIVITY-MIGRATION-ERROR') });
    } else if (id === 'UIAUTOMATION-ACTIVITY-MIGRATION-PARTIAL') {
      uia.partial.push(entry);
    } else if (id.startsWith('UIAUTOMATION-ACTIVITY-MIGRATION-WARNING')) {
      uia.warnings.push({ ...entry, reason: reasonOf(id, 'UIAUTOMATION-ACTIVITY-MIGRATION-WARNING') });
    } else if (id.startsWith('UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-')) {
      const prefix = id.startsWith('UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-ERROR') ? 'UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-ERROR' : 'UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-WARNING';
      uia.warnings.push({ ...entry, reason: reasonOf(id, prefix) });
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
const leftovers = uia.notMigrated.length + uia.partial.length + productivity.notMigrated.length + actionRequired.length + typeIssues.length;
let status;
if (hasCriticalError) status = 'failed';
else if (results.length === 0) status = 'unknown';
else if (!sawValidation && !results.some((r) => (r.ruleId || '') === 'PROJECT-COPY')) status = byLevel.error > 0 ? 'failed' : 'unknown';
else if (byLevel.error > 0 || byLevel.warning > 0 || leftovers > 0) status = 'partial';
else status = 'success';

const summary = {
  file,
  status,
  outputPath: (run.properties && run.properties.outputPath) || null,
  totals: { results: results.length, ...byLevel },
  frameworkChanged,
  packages,
  effectiveVersions,
  blockers,
  byFamily,
  uia,
  productivity,
  typeIssues,
  actionRequired,
  byRule,
  files: [...new Set(results.map(fileOf).filter(Boolean))].sort(),
};

if (wantJson) {
  console.log(JSON.stringify(summary, null, 2));
  process.exit(0);
}

const md = [];
const list = (items, fmt) => {
  const shown = items.slice(0, LIST_LIMIT);
  for (const it of shown) md.push(`- ${fmt(it)}`);
  if (items.length > shown.length) md.push(`- … and ${items.length - shown.length} more`);
  if (!items.length) md.push('- none');
};
const loc = (e) => `${e.file || '(project)'}${e.activity ? ': ' + e.activity : ''}${e.property ? ' / ' + e.property : ''}`;

md.push(`# Migration SARIF summary — ${basename(file)}`);
md.push('');
md.push(`Status: **${status}** | Results: ${results.length} (errors ${byLevel.error || 0}, warnings ${byLevel.warning || 0}, notes ${byLevel.note || 0})${summary.outputPath ? ` | Output: ${summary.outputPath}` : ''}`);
md.push('');
md.push('| Area | Count | Detail |');
md.push('|---|---|---|');
md.push(`| Framework | ${frameworkChanged ? 1 : 0} | ${frameworkChanged ? 'Legacy → Windows' : 'unchanged'} |`);
md.push(`| Package versions | ${packages.length} | ${Object.entries(effectiveVersions).map(([p, v]) => `${p} ${v.from} → ${v.to}`).slice(0, 8).join('; ') || packages.slice(0, 6).join('; ')} |`);
md.push(`| UIA activities migrated | ${uia.migrated} | ${Object.entries(uia.migratedByType).map(([t, n]) => `${t} ×${n}`).slice(0, 12).join(', ')} |`);
md.push(`| UIA activities not migrated | ${uia.notMigrated.length} | see list |`);
md.push(`| UIA partial / warnings | ${uia.partial.length} / ${uia.warnings.length} | see lists |`);
md.push(`| Productivity migrated / not migrated / warnings | ${productivity.migrated} / ${productivity.notMigrated.length} / ${productivity.warnings.length} | Mail, GSuite, Office 365 |`);
md.push(`| Manual action required | ${actionRequired.length} | messages tagged ${ACTION_TAG} |`);
md.push(`| Type / compile issues | ${typeIssues.length} | TYPE-MISSING, compilation, validation |`);
md.push(`| Blockers | ${blockers.length} | ${blockers.map((b) => b.rule).filter((v, i, a) => a.indexOf(v) === i).join(', ')} |`);
md.push('');
md.push('## Blockers');
list(blockers, (e) => `**${e.rule}** — ${e.message}${e.file ? ` (${e.file})` : ''}`);
md.push('');
md.push('## UIA not migrated');
list(uia.notMigrated, (e) => `${loc(e)} — ${e.reason || e.rule}`);
md.push('');
md.push('## UIA partial');
list(uia.partial, (e) => `${loc(e)} — ${e.message}`);
md.push('');
md.push('## UIA warnings (activity and property)');
list(uia.warnings, (e) => `${loc(e)} — ${e.reason || e.rule}${e.message ? ': ' + e.message : ''}`);
md.push('');
md.push('## UIA workflow-level');
list(uia.workflow, (e) => `${e.file || '(project)'} — ${e.rule}: ${e.message}`);
md.push('');
md.push('## Productivity not migrated');
list(productivity.notMigrated, (e) => `${loc(e)} — ${e.rule}: ${e.message}`);
md.push('');
md.push('## Productivity warnings');
list(productivity.warnings, (e) => `${loc(e)} — ${e.rule}: ${e.message}`);
md.push('');
md.push('## Manual action required');
list(actionRequired, (e) => `${loc(e)} — ${e.message}`);
md.push('');
md.push('## Type / compile issues');
list(typeIssues, (e) => `${e.file || '(project)'} — ${e.rule}: ${e.message}`);
md.push('');
md.push('## Rule counts');
md.push('| Rule | Level | Count |');
md.push('|---|---|---|');
for (const [id, v] of Object.entries(byRule).sort((a, b) => b[1].count - a[1].count)) md.push(`| ${id} | ${v.level} | ${v.count} |`);
console.log(md.join('\n'));
