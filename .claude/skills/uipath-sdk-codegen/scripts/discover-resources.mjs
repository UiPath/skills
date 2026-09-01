#!/usr/bin/env node
/**
 * discover-resources — list the tenant resources a case can actually reference, per SDK
 * task kind.
 *
 * WHY THIS EXISTS. The contract-execution case authored this session validates cleanly and
 * could never run: every task references a name I invented from the requirements doc
 * (`ContractIntakeValidation`, `OutsideCounselOpinion`, ...). Reference-mode tasks are just
 * `name` + `folderPath` strings, so the validator cannot tell an invented name from a real
 * one — it is not that layer's job. The gap between "validates" and "runs" is exactly this
 * lookup, and it is the parity item against the `uipath-maestro-case` skill in ~/src/skills.
 *
 * HOW. `uip maestro case registry pull` populates a local cache at `~/.uip/case-resources/`,
 * one `<type>-index.json` per resource type. Discovery reads those files DIRECTLY.
 * Deliberately not `uip maestro case registry search`: that command has known gaps and
 * returns empty for types that are present in the cache (most often action-apps / HITL).
 *
 *   node discover-resources.mjs [--kind <task-kind>] [--grep <substr>] [--json]
 *
 * A note on freshness, learned the hard way elsewhere in this repo: registry reads answer
 * from a local cache that does not refresh itself. Pull before trusting absence.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';

const HOME = process.env.HOME ?? '';
const CACHE = join(HOME, '.uip', 'case-resources');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const JSON_OUT = process.argv.includes('--json');
const ONLY = arg('--kind');
const GREP = (arg('--grep') ?? '').toLowerCase();

/**
 * SDK task kind -> the cache index that supplies its `name` + `folderPath`.
 *
 * `field` differs for action-apps, which is the one index that does not use
 * name/folders[0].fullyQualifiedName — a detail worth encoding rather than rediscovering.
 *
 * Kinds absent here are absent on purpose:
 *   document-extraction, function  no registry index exists; the reference is resolved by
 *                                  the platform at run time, not from this cache
 *   wait-for-timer                 no resource
 *   wait-for-connector             connector events come from the connector library, not here
 */
const KINDS = {
  // `process-index.json` and `processOrchestration-index.json` are DISJOINT sets (24 vs 21
  // entries, zero overlap) split by `entitySubType`: `Process` vs `ProcessOrchestration`.
  // These were crossed here — `--kind process` listed the RPA processes and `rpa` was not
  // listed at all — which mattered beyond cosmetics: `uip maestro case tasks describe
  // --type process` reads processOrchestration-index.json, so an id taken from this tool's
  // `process` output came back "No process entry found with entityKey … in
  // processOrchestration-index.json". Confirmed both ways on 2026-08-21.
  'process': { file: 'processOrchestration-index.json', note: 'published Maestro process-orchestration processes' },
  'rpa': { file: 'process-index.json', note: 'published RPA processes (entitySubType Process)' },
  'agent': { file: 'agent-index.json', note: 'published agents' },
  'api-workflow': { file: 'api-index.json', note: 'published API workflows' },
  'case-management': { file: 'caseManagement-index.json', note: 'other published cases (sub-cases)' },
  'flow-process': { file: 'flow-index.json', note: 'published Maestro flows' },
  'action': { file: 'action-apps-index.json', field: 'action-app', note: 'Action Center apps (HITL)' },
  // external-* are NOT separate registry types. "External" is about WHERE a resource lives —
  // published in a different solution from this case — so they read the same indexes and the
  // caller decides from the folder path. Recording this because the
  // `typecache-external-agent-*` indexes look like the right source and are NOT: all four
  // entries are `UiPath.IntegrationService.Activities`, i.e. activity PACKAGES, not resources.
  'external-agent': { file: 'agent-index.json', note: 'agents — external when the folder is another solution' },
  'external-workflow': { file: 'api-index.json', alt: 'flow-index.json', note: 'API workflows / flows in another solution' },
};

/**
 * `lastSync` from the index's meta file — NOT the index file's mtime.
 *
 * mtime lies: the CLI does not rewrite an index whose content hash is unchanged, only its
 * meta. So a successful pull can leave a four-day-old mtime on a file that is current, and
 * this script reported "cache pulled 2026-08-14" immediately after a clean pull today.
 */
function lastSync(file) {
  const m = join(CACHE, file.replace(/-index\.json$/, '-index.meta.json'));
  if (!existsSync(m)) return null;
  try { return JSON.parse(readFileSync(m, 'utf8')).lastSync ?? null; } catch { return null; }
}

function readIndex(file) {
  const p = join(CACHE, file);
  // Missing file is NOT an empty result — it means the pull never ran, or ran and this type
  // has no entries. Those are different answers and conflating them turns a precondition
  // failure into a confident "the tenant has none of these".
  if (!existsSync(p)) return { missing: true, rows: [], sync: null };
  try {
    const rows = JSON.parse(readFileSync(p, 'utf8'));
    return { missing: false, rows: Array.isArray(rows) ? rows : [], sync: lastSync(file) };
  } catch {
    return { missing: false, rows: [], unreadable: true, sync: lastSync(file) };
  }
}

/**
 * Refuse to report a cache that is not demonstrably current for THIS tenant.
 *
 * Two failures this catches, both hit for real on 2026-08-18:
 *
 * 1. PARTIAL PULL. `uip maestro case registry pull` can return `PartialSuccess` (six
 *    server-side 503s) and leave the previous tenant's index files in place. Only the
 *    typecaches and action-apps refreshed. Discovery then reported 24 processes and 15
 *    agents from a DIFFERENT TENANT, with no warning, because the files existed.
 * 2. TENANT SWITCH. No index records which tenant wrote it, so timestamps alone cannot
 *    distinguish "stale" from "different tenant". We stamp it ourselves.
 *
 * The rule this enforces is one the skill already stated and the code did not: the cache
 * never refreshes itself, so absence of a warning is not evidence of freshness.
 */
const STAMP = join(CACHE, '.discover-tenant-stamp.json');
function currentTenant() {
  try {
    const out = execFileSync('uip', ['login', 'status', '--output', 'json'],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 60_000 });
    const d = JSON.parse(out).Data ?? {};
    return d.TenantId ? { tenantId: d.TenantId, tenant: d.Tenant, org: d.Organization } : null;
  } catch { return null; }
}

function freshnessGate(indexFiles) {
  const syncs = indexFiles.map((f) => ({ f, t: lastSync(f) })).filter((x) => x.t);
  const problems = [];
  if (!syncs.length) problems.push('no index meta files — the pull has never run');
  const newest = Math.max(...syncs.map((x) => x.t), 0);
  // A partial pull leaves a wide spread: some indexes rewritten, others left behind.
  const stale = syncs.filter((x) => newest - x.t > 60_000)
    .map((x) => `${x.f.replace('-index.json', '')} (${Math.round((newest - x.t) / 60000)} min older)`);
  if (stale.length) {
    problems.push(`PARTIAL PULL — these indexes were not refreshed: ${stale.join(', ')}`);
  }
  const now = currentTenant();
  let prev = null;
  try { prev = JSON.parse(readFileSync(STAMP, 'utf8')); } catch { /* first run */ }
  if (now && prev && prev.tenantId !== now.tenantId) {
    problems.push(`TENANT CHANGED — cache was stamped for ${prev.tenant ?? prev.tenantId}, `
      + `you are on ${now.tenant} (${now.tenantId})`);
  }
  if (!now) problems.push('could not read `uip login status` — cannot confirm which tenant this cache is for');
  return { problems, newest, tenant: now };
}

function normalise(row, field) {
  if (field === 'action-app') {
    return {
      name: row.deploymentTitle ?? row.name ?? null,
      folder: row.deploymentFolder?.fullyQualifiedName ?? null,
      id: row.id ?? null,
    };
  }
  return {
    name: row.name ?? null,
    folder: row.folders?.[0]?.fullyQualifiedName ?? null,
    id: row.entityKey ?? null,
  };
}

if (!existsSync(CACHE)) {
  console.error(`discover-resources: no registry cache at ${CACHE}`);
  console.error('Run:  uip maestro case registry pull');
  console.error('Refusing to report "no resources" from a cache that was never populated.');
  process.exit(2);
}

const INDEX_FILES = [...new Set(Object.values(KINDS).flatMap((k) => [k.file, k.alt].filter(Boolean)))];
const gate = freshnessGate(INDEX_FILES);
if (gate.problems.length && !process.argv.includes('--ignore-staleness')) {
  console.error('\ndiscover-resources: REFUSING to report — the cache is not demonstrably current.\n');
  for (const p of gate.problems) console.error(`  ✗ ${p}`);
  console.error('\n  Fix:  uip maestro case registry pull --force');
  console.error('  Then re-run. If the pull reports PartialSuccess, retry — the 503s are transient.');
  console.error('  Override with --ignore-staleness only if you know what the cache holds.\n');
  process.exit(3);
}
// Stamp the tenant this cache was READ for, so a later switch is detectable rather than
// inferred from timestamps that cannot distinguish stale from foreign.
if (gate.tenant) {
  try {
    const { writeFileSync } = await import('node:fs');
    writeFileSync(STAMP, JSON.stringify({ ...gate.tenant, stampedAt: gate.newest }, null, 2));
  } catch { /* cache dir may be read-only; the gate still ran */ }
}

const out = {};
let missingAny = false;
for (const [kind, spec] of Object.entries(KINDS)) {
  if (ONLY && kind !== ONLY) continue;
  const primary = readIndex(spec.file);
  const extra = spec.alt ? readIndex(spec.alt) : { rows: [] };
  if (primary.missing) { missingAny = true; }
  const rows = [...primary.rows, ...extra.rows]
    .map((r) => normalise(r, spec.field))
    .filter((r) => r.name)
    // The indexes carry one row per folder binding, so the same resource appears repeatedly.
    .filter((r, i, a) => a.findIndex((x) => x.name === r.name && x.folder === r.folder) === i)
    .filter((r) => !GREP || r.name.toLowerCase().includes(GREP) || (r.folder ?? '').toLowerCase().includes(GREP))
    .sort((a, b) => a.name.localeCompare(b.name));
  out[kind] = { source: spec.file + (spec.alt ? ` + ${spec.alt}` : ''), note: spec.note,
    cacheMissing: primary.missing, count: rows.length, resources: rows };
}

if (JSON_OUT) {
  console.log(JSON.stringify({ cache: CACHE, kinds: out }, null, 2));
  process.exit(0);
}

const when = gate.newest ? new Date(gate.newest).toISOString().slice(0, 16).replace('T', ' ') : 'unknown';
const who = gate.tenant ? `${gate.tenant.org}/${gate.tenant.tenant}` : 'tenant unknown';
console.log(`\ntenant resources referenceable from a case`);
console.log(`  ${who}   ·   cache synced ${when}   ·   ${CACHE}\n`);
for (const [kind, info] of Object.entries(out)) {
  if (info.cacheMissing) {
    console.log(`  ${kind}  — INDEX MISSING (${info.source}); run \`uip maestro case registry pull\``);
    continue;
  }
  console.log(`  ${kind}  (${info.count})  ${info.note}`);
  for (const r of info.resources.slice(0, 8)) {
    console.log(`      ${r.name.slice(0, 40).padEnd(42)}${r.folder ?? '(no folder)'}`);
  }
  if (info.count > 8) console.log(`      … ${info.count - 8} more`);
  console.log('');
}
console.log('Kinds with no registry index — document-extraction, function, wait-for-timer,');
console.log('wait-for-connector — are resolved elsewhere and are not discoverable here.');
if (missingAny) console.log('\n⚠ at least one index is absent: that is a pull failure, NOT a tenant with no resources.');
