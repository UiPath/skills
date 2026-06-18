import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, mkdtempSync, writeFileSync, rmSync, mkdirSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import { validateIntent, resolveMetric, buildWidgetFile, generateViewFile, generateKeyedDetailViewFile, buildViewSpec, compileColumns, emit, parseEvent, classifyEditIntent, resolveChangeMetric, widgetLayoutGroup, VALID_DISPLAY_TYPES, metricModuleSpecifier, buildVersions, SCAFFOLD_VERSION, INTENT_SCHEMA_VERSION, STATE_SCHEMA_VERSION, scaffoldDrift, runIntentMigrations, VALID_EDIT_OPS } from '../build-dashboard.mjs'
import { zipDir, unzipTo, contentHash } from '../lib/zip.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REGISTRY_PATH = resolve(__dirname, '../capability-registry.json')

const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'))

// ── Phase 2: version stamps ───────────────────────────────────────────────────
test('buildVersions stamps skill/scaffold/intentSchema/sdk', () => {
  const v = buildVersions('1.4.1')
  assert.equal(v.scaffold, SCAFFOLD_VERSION)
  assert.equal(v.intentSchema, INTENT_SCHEMA_VERSION)
  assert.equal(v.sdk, '1.4.1')
  assert.ok(typeof v.skill === 'string' && v.skill.length > 0)
})

test('buildVersions tolerates a missing sdk version', () => {
  assert.equal(buildVersions().sdk, null)
})

test('STATE_SCHEMA_VERSION is 2', () => {
  assert.equal(STATE_SCHEMA_VERSION, 2)
})

// ── Phase 2: scaffold drift ───────────────────────────────────────────────────
test('scaffoldDrift: none when stamped scaffold equals current', () => {
  assert.equal(scaffoldDrift({ versions: { scaffold: SCAFFOLD_VERSION } }), null)
})

test('scaffoldDrift: detected when stamped differs', () => {
  assert.deepEqual(scaffoldDrift({ versions: { scaffold: '0.9.0' } }), { from: '0.9.0', to: SCAFFOLD_VERSION })
})

test('scaffoldDrift: detected for a pre-versioning project (no versions block)', () => {
  assert.deepEqual(scaffoldDrift({ widgets: {} }), { from: null, to: SCAFFOLD_VERSION })
})

// ── Phase 2: migrations + UPGRADE op ──────────────────────────────────────────
test('runIntentMigrations: no-op when already at target', async () => {
  const out = await runIntentMigrations({ schemaVersion: 2, metrics: [] }, '/no/such/dir', 2)
  assert.equal(out.schemaVersion, 2)
})

test('runIntentMigrations: applies a sequenced migration from a dir', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'mig-'))
  writeFileSync(join(dir, 'intent-v2-to-v3.mjs'), 'export function migrate(i){ return { ...i, bumped: true } }')
  try {
    const out = await runIntentMigrations({ schemaVersion: 2, metrics: [] }, dir, 3)
    assert.equal(out.bumped, true)
    assert.equal(out.schemaVersion, 3)
  } finally { rmSync(dir, { recursive: true, force: true }) }
})

test('VALID_EDIT_OPS includes UPGRADE', () => {
  assert.ok(VALID_EDIT_OPS.includes('UPGRADE'))
})

test('classifyEditIntent accepts a no-target UPGRADE op', () => {
  const plan = classifyEditIntent({ projectDir: '/p', op: 'UPGRADE' })
  assert.equal(plan.ops[0].op, 'UPGRADE')
})

// ── Phase 3: zip library ──────────────────────────────────────────────────────
test('zip round-trip preserves files and bytes (incl. nested dirs)', () => {
  const src = mkdtempSync(join(tmpdir(), 'zsrc-'))
  const dst = mkdtempSync(join(tmpdir(), 'zdst-'))
  writeFileSync(join(src, 'a.txt'), 'hello')
  mkdirSync(join(src, 'sub'), { recursive: true })
  writeFileSync(join(src, 'sub', 'b.ts'), 'export const x = 1\n')
  try {
    unzipTo(zipDir(src), dst)
    assert.equal(readFileSync(join(dst, 'a.txt'), 'utf8'), 'hello')
    assert.equal(readFileSync(join(dst, 'sub', 'b.ts'), 'utf8'), 'export const x = 1\n')
  } finally {
    rmSync(src, { recursive: true, force: true })
    rmSync(dst, { recursive: true, force: true })
  }
})

test('contentHash is stable for identical content and changes when content changes', () => {
  const a = mkdtempSync(join(tmpdir(), 'zha-'))
  const b = mkdtempSync(join(tmpdir(), 'zhb-'))
  writeFileSync(join(a, 'f.txt'), 'same')
  writeFileSync(join(b, 'f.txt'), 'same')
  try {
    assert.equal(contentHash(a), contentHash(b))
    writeFileSync(join(b, 'f.txt'), 'different')
    assert.notEqual(contentHash(a), contentHash(b))
  } finally {
    rmSync(a, { recursive: true, force: true })
    rmSync(b, { recursive: true, force: true })
  }
})

test('committed starter-kit archive matches the loose scaffold (re-pack to refresh)', () => {
  const scaffoldDir = resolve(__dirname, '../../templates/dashboard/scaffold')
  const manifest = JSON.parse(readFileSync(resolve(__dirname, '../../fixtures/governance-dashboard-starter-kit.manifest.json'), 'utf8'))
  assert.equal(contentHash(scaffoldDir), manifest.sha256, 'Scaffold changed but archive not re-packed — run pack-scaffold.mjs and commit the refreshed zip + manifest')
})

// Build a single stored-entry zip with an arbitrary (possibly malicious) name.
function makeZipWithName(name) {
  const nameBuf = Buffer.from(name, 'utf8')
  const local = Buffer.alloc(30)
  local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4); local.writeUInt16LE(0, 8)
  local.writeUInt16LE(nameBuf.length, 26)
  const cen = Buffer.alloc(46)
  cen.writeUInt32LE(0x02014b50, 0); cen.writeUInt16LE(20, 4); cen.writeUInt16LE(20, 6)
  cen.writeUInt16LE(0, 10); cen.writeUInt16LE(nameBuf.length, 28); cen.writeUInt32LE(0, 42)
  const localPart = Buffer.concat([local, nameBuf])
  const cenPart = Buffer.concat([cen, nameBuf])
  const eocd = Buffer.alloc(22)
  eocd.writeUInt32LE(0x06054b50, 0); eocd.writeUInt16LE(1, 8); eocd.writeUInt16LE(1, 10)
  eocd.writeUInt32LE(cenPart.length, 12); eocd.writeUInt32LE(localPart.length, 16)
  return Buffer.concat([localPart, cenPart, eocd])
}

test('unzipTo rejects zip-slip entries that escape destDir', () => {
  const dst = mkdtempSync(join(tmpdir(), 'zslip-'))
  try {
    assert.throws(() => unzipTo(makeZipWithName('../escape.txt'), dst), /escape|unsafe/)
    assert.throws(() => unzipTo(makeZipWithName('a/../../escape.txt'), dst), /escape|unsafe/)
  } finally {
    rmSync(dst, { recursive: true, force: true })
  }
})

function resolveT1(metricName) {
  const entry = registry.t1[metricName]
  if (!entry) return null
  return { tier: 'T1', entry }
}

function resolveAlias(userText) {
  const lower = userText.toLowerCase()
  for (const [key, entry] of Object.entries(registry.t1)) {
    if (entry.aliases.some(a => lower.includes(a))) return { tier: 'T1', key, entry }
  }
  for (const [key, entry] of Object.entries(registry.t2)) {
    if (entry.aliases.some(a => lower.includes(a))) return { tier: 'T2', key, entry }
  }
  return null
}

test('T1 exact name lookup returns entry', () => {
  const result = resolveT1('job-failures')
  assert.ok(result)
  assert.equal(result.tier, 'T1')
  assert.equal(result.entry.template, 'data-table')
})

test('T1 exact name lookup returns null for unknown metric', () => {
  const result = resolveT1('completely-unknown-metric')
  assert.equal(result, null)
})

test('alias lookup finds job-failures by natural language', () => {
  const result = resolveAlias('show me faulted jobs')
  assert.ok(result)
  assert.equal(result.tier, 'T1')
  assert.equal(result.key, 'job-failures')
})

test('alias lookup finds T2 jobs-duration-threshold', () => {
  const result = resolveAlias('long running jobs over threshold')
  assert.ok(result)
  assert.equal(result.tier, 'T2')
  assert.equal(result.key, 'jobs-duration-threshold')
})

test('alias lookup returns null for unknown text', () => {
  const result = resolveAlias('completely unrelated nonsense xyz')
  assert.equal(result, null)
})

test('all T1 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t1)) {
    assert.ok(entry.template, `${key} missing template`)
    assert.ok(entry.description, `${key} missing description`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
    assert.ok(entry.defaults?.title, `${key} missing defaults.title`)
    // SDK fields must NOT be present — registry is hints-only
    assert.equal(entry.sdkImport, undefined, `${key} should not have sdkImport (removed)`)
    assert.equal(entry.sdkService, undefined, `${key} should not have sdkService (removed)`)
    assert.equal(entry.sdkMethod, undefined, `${key} should not have sdkMethod (removed)`)
    assert.equal(entry.responseType, undefined, `${key} should not have responseType (removed)`)
  }
})

test('all T2 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t2)) {
    assert.ok(entry.description, `${key} missing description`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
    // SDK fields must NOT be present — registry is hints-only
    assert.equal(entry.sdkImport, undefined, `${key} should not have sdkImport (removed)`)
    assert.equal(entry.sdkService, undefined, `${key} should not have sdkService (removed)`)
    assert.equal(entry.method, undefined, `${key} should not have method (removed)`)
    assert.equal(entry.filterField, undefined, `${key} should not have filterField (removed)`)
    assert.equal(entry.filterType, undefined, `${key} should not have filterType (removed)`)
    assert.equal(entry.sortField, undefined, `${key} should not have sortField (removed)`)
    assert.equal(entry.sortDir, undefined, `${key} should not have sortDir (removed)`)
    assert.equal(entry.defaultDisplayAs, undefined, `${key} should not have defaultDisplayAs (removed)`)
  }
})

test('all hardRefuse entries have pattern, reason, alternative', () => {
  for (const entry of registry.hardRefuse) {
    assert.ok(entry.pattern, 'hardRefuse entry missing pattern')
    assert.ok(entry.reason, 'hardRefuse entry missing reason')
    assert.ok(entry.alternative, 'hardRefuse entry missing alternative')
    // Verify pattern is a valid regex
    assert.doesNotThrow(() => new RegExp(entry.pattern), `invalid regex: ${entry.pattern}`)
  }
})

test('hardRefuse matches cost/dollar phrases', () => {
  const dollarEntry = registry.hardRefuse.find(e => e.pattern.includes('dollar'))
  assert.ok(dollarEntry)
  assert.ok(new RegExp(dollarEntry.pattern).test('cost in dollars'))
})

test('hardRefuse does not collide with valid T1 aliases', () => {
  for (const refuseEntry of registry.hardRefuse) {
    const re = new RegExp(refuseEntry.pattern)
    for (const [key, t1Entry] of Object.entries(registry.t1)) {
      for (const alias of t1Entry.aliases) {
        assert.ok(!re.test(alias), `hardRefuse pattern "${refuseEntry.pattern}" collides with T1 alias "${alias}" (${key})`)
      }
    }
  }
})

// ── validateIntent tests ──────────────────────────────────────────────────────

test('validateIntent: valid T1 intent passes', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'My Dashboard',
    timeRange: '30d',
    metrics: [{ name: 'agent-memory-timeline', tier: 'T1', title: 'Agent Memory' }]
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: T1 metric without fnBody is valid (fnBody no longer required in v2)', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'agent-memory-timeline', tier: 'T1', title: 'Agent Memory' }]
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: rejects T1 metric without title', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'agent-memory-timeline', tier: 'T1' }]
  })
  assert.ok(errors.some(e => e.includes('T1') && e.includes('title')))
})

test('validateIntent: T2 metric without fnBody is valid (fnBody no longer required in v2)', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'jobs-by-state', tier: 'T2', title: 'Jobs', params: { value: 'Faulted' } }]
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: rejects missing dashboardName', () => {
  const errors = validateIntent({ schemaVersion: 2, timeRange: '30d', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('dashboardName')))
})

test('validateIntent: rejects invalid timeRange', () => {
  const errors = validateIntent({ schemaVersion: 2, dashboardName: 'x', timeRange: '2w', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('timeRange')))
})

test('validateIntent: rejects T2 metric without params', () => {
  const errors = validateIntent({ schemaVersion: 2, dashboardName: 'x', timeRange: '7d', metrics: [{ name: 'queue-failure-threshold', tier: 'T2' }] })
  assert.ok(errors.some(e => e.includes('T2') && e.includes('params')))
})

test('validateIntent: T3 metric without fnBody is valid when displayAs and title present (v2 contract)', () => {
  const errors = validateIntent({ schemaVersion: 2, dashboardName: 'x', timeRange: '7d', metrics: [{ name: 'custom', tier: 'T3', displayAs: 'ranked-table', title: 'Custom' }] })
  assert.deepEqual(errors, [])
})

// ── resolveMetric tests ───────────────────────────────────────────────────────

test('resolveMetric: T1 known name returns entry with template', () => {
  const result = resolveMetric({ name: 'job-failures', tier: 'T1' })
  assert.equal(result.tier, 'T1')
  assert.equal(result.entry.template, 'data-table')
})

test('resolveMetric: T2 known name returns entry with description', () => {
  const result = resolveMetric({ name: 'jobs-duration-threshold', tier: 'T2', params: { threshold: 300, direction: 'gt' } })
  assert.equal(result.tier, 'T2')
  assert.ok(result.entry.description)
})

test('resolveMetric: T3 always resolves with null entry', () => {
  const result = resolveMetric({ name: 'custom-thing', tier: 'T3', fnBody: 'return []', displayAs: 'kpi-card', title: 'X' })
  assert.equal(result.tier, 'T3')
  assert.equal(result.entry, null)
})

test('resolveMetric: unknown T1 name throws with "not found in registry"', () => {
  assert.throws(() => resolveMetric({ name: 'nonexistent-metric', tier: 'T1' }), /not found in registry/)
})

// ── buildWidgetFile tests (unified path for all tiers) ────────────────────────

test('buildWidgetFile: T1 chart metric imports fetchData from metric module (not spliced fnBody)', () => {
  const entry = registry.t1['memory-calls-trend']
  const content = buildWidgetFile(
    {
      name: 'memory-calls-trend',
      tier: 'T1',
      title: 'Memory Calls',
      displayAs: 'area-chart',
      xKey: 'timeSlice',
      yKey: 'memoryCallsCount',
    },
    entry,
    '30d'
  )
  assert.ok(content.includes("import { fetchData } from '@/metrics/memory-calls-trend'"))
  assert.ok(content.includes('useWidgetData(fetchData, [])'))
  assert.ok(!content.includes('customDataFn'))
  // No hardcoded type params from registry
  assert.ok(!content.includes('useWidgetData<'))
})

test('buildWidgetFile: uses registry defaults for xKey/yKey when not in metric', () => {
  const entry = registry.t1['memory-calls-trend']
  const content = buildWidgetFile(
    { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', displayAs: 'area-chart', fnBody: 'return []' },
    entry,
    '30d'
  )
  // xKey from registry defaults
  assert.ok(content.includes('timeSlice'))
})

test('buildWidgetFile: T2 chart metric imports fetchData from metric module', () => {
  const entry = registry.t2['jobs-duration-threshold']
  const content = buildWidgetFile(
    {
      name: 'jobs-duration-threshold',
      tier: 'T2',
      title: 'Long Running Jobs',
      displayAs: 'bar-chart',
      xKey: 'name',
      yKey: 'duration',
    },
    entry,
    '30d'
  )
  assert.ok(content.includes("import { fetchData } from '@/metrics/jobs-duration-threshold'"))
  assert.ok(content.includes('useWidgetData(fetchData, [])'))
  assert.ok(!content.includes('customDataFn'))
  assert.ok(!content.includes('useWidgetData<'))
})

test('buildWidgetFile: T3 metric (null registry entry) uses shell path for kpi-card', () => {
  const content = buildWidgetFile(
    {
      name: 'running-jobs-kpi',
      tier: 'T3',
      title: 'Running Jobs',
      displayAs: 'kpi-card',
      fnBody: 'return [{ count: 42 }]',
      valueField: 'count',
      valueLabel: 'running jobs'
    },
    null,
    '30d'
  )
  assert.ok(content.includes('RunningJobsKpi'))
  assert.ok(content.includes('Running Jobs'))
  assert.ok(content.includes("const VALUE_FIELD = 'count'"))
  assert.ok(content.includes("const VALUE_LABEL = 'running jobs'"))
  assert.ok(!content.includes('<<FN_BODY>>'))
})

test('buildWidgetFile: throws if title is missing', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', displayAs: 'kpi-card', fnBody: 'return []' }, null),
    /missing title/
  )
})

test('buildWidgetFile throws when title is missing', () => {
  assert.throws(() => buildWidgetFile({ name: 'x', tier: 'T1', displayAs: 'data-table' }, null, '30d'), /missing title/)
})

test('buildWidgetFile: throws if displayAs cannot be determined', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', title: 'X', fnBody: 'return []' }, null),
    /needs displayAs/
  )
})

test('buildWidgetFile: shell ranked-table imports fetchData from metric module', () => {
  const content = buildWidgetFile({
    name: 'faulted-queues', tier: 'T3', title: 'Faulted Queues', description: 'Queues with faults',
    displayAs: 'ranked-table',
  }, null, '30d')
  assert.ok(content.includes('FaultedQueues'), 'component name not injected')
  assert.ok(content.includes('Faulted Queues'), 'title not injected')
  assert.ok(content.includes("import { fetchData } from '@/metrics/faulted-queues'"), 'fetchData import not injected')
  assert.ok(content.includes('fetchData(sdk, getToken)'), 'fetchData call not injected')
  assert.ok(!content.includes('const customDataFn = async'), 'customDataFn must not appear')
  assert.ok(!content.includes('<<COMPONENT_NAME>>'), 'COMPONENT_NAME placeholder not replaced')
  assert.ok(!content.includes('<<METRIC_IMPORT>>'), 'METRIC_IMPORT placeholder not replaced')
})

test('buildWidgetFile: no unresolved << >> placeholders remain', () => {
  const content = buildWidgetFile({
    name: 'test', tier: 'T3', title: 'Test Widget',
    displayAs: 'ranked-table',
    fnBody: 'return []',
    valueField: '', valueLabel: '',
  }, null, '30d')
  const unresolved = content.match(/<<[A-Z_]+>>/g)
  assert.equal(unresolved, null, `Unresolved placeholders: ${(unresolved ?? []).join(', ')}`)
})

test('buildWidgetFile: uses registry defaults for icon when metric has none', () => {
  const entry = registry.t1['agent-health']
  const content = buildWidgetFile(
    { name: 'agent-health', tier: 'T1', title: 'Agent Health', displayAs: 'ranked-table', fnBody: 'return []' },
    entry,
    '30d'
  )
  assert.ok(content.includes('HeartPulse'))
})

// ── emit + parseEvent tests ───────────────────────────────────────────────────

test('emit: writes structured event with payload', () => {
  const lines = []
  emit('WIDGET_READY', { name: 'ErrorRateTrend', index: 1, total: 4 }, { write: s => lines.push(s) })
  assert.equal(lines.length, 1)
  const parsed = JSON.parse(lines[0].replace('WIDGET_READY:', ''))
  assert.equal(parsed.name, 'ErrorRateTrend')
})

test('emit: writes simple event with no payload', () => {
  const lines = []
  emit('PREWARM_DONE', null, { write: s => lines.push(s) })
  assert.equal(lines[0].trim(), 'PREWARM_DONE')
})

test('parseEvent: parses WIDGET_READY with payload', () => {
  const result = parseEvent('WIDGET_READY:{"name":"Foo","index":2,"total":5}')
  assert.equal(result.type, 'WIDGET_READY')
  assert.equal(result.payload.name, 'Foo')
})

test('parseEvent: parses simple event with no payload', () => {
  const result = parseEvent('PREWARM_DONE')
  assert.equal(result.type, 'PREWARM_DONE')
  assert.equal(result.payload, null)
})

test('parseEvent: returns null for non-event lines', () => {
  const result = parseEvent('regular log line')
  assert.equal(result, null)
})

// ── classifyEditIntent tests ──────────────────────────────────────────────────

test('classifyEditIntent: normalizes legacy single op to a one-element batch', () => {
  const result = classifyEditIntent({ op: 'ADD', projectDir: '/tmp/x', metric: { name: 'agent-health', tier: 'T1' } })
  assert.equal(result.ops.length, 1)
  assert.equal(result.ops[0].op, 'ADD')
  assert.equal(result.ops[0].metric.name, 'agent-health')
  assert.equal(result.projectDir, '/tmp/x')
})

test('classifyEditIntent: accepts an ops batch and preserves order', () => {
  const result = classifyEditIntent({
    projectDir: '/tmp/x',
    ops: [
      { op: 'CHANGE', target: 'A', delta: { timeRange: '7d' } },
      { op: 'REMOVE', target: 'B' },
      { op: 'ADD', metric: { name: 'agent-health', tier: 'T1' } },
    ],
  })
  assert.deepEqual(result.ops.map(o => o.op), ['CHANGE', 'REMOVE', 'ADD'])
  assert.equal(result.ops[1].target, 'B')
})

test('classifyEditIntent: throws on invalid op with its batch index', () => {
  assert.throws(() => classifyEditIntent({ op: 'DELETE', projectDir: '/tmp/x' }), /invalid op "DELETE" \(ops\[0\]\)/)
  assert.throws(
    () => classifyEditIntent({ projectDir: '/tmp/x', ops: [{ op: 'ADD', metric: { name: 'x' } }, { op: 'RENAME' }] }),
    /invalid op "RENAME" \(ops\[1\]\)/
  )
})

test('classifyEditIntent: throws on empty ops array', () => {
  assert.throws(() => classifyEditIntent({ projectDir: '/tmp/x', ops: [] }), /empty/)
})

test('parseEvent: recognizes AUTH_MISSING event', () => {
  const result = parseEvent('AUTH_MISSING:{"var":"clientId","message":"No client ID"}')
  assert.equal(result.type, 'AUTH_MISSING')
  assert.equal(result.payload.var, 'clientId')
})

// ── VALID_DISPLAY_TYPES + displayAs validation tests ─────────────────────────

test('VALID_DISPLAY_TYPES includes all chart and table types', () => {
  assert.ok(VALID_DISPLAY_TYPES.includes('kpi-card'))
  assert.ok(VALID_DISPLAY_TYPES.includes('ranked-table'))
  assert.ok(VALID_DISPLAY_TYPES.includes('data-table'))
  assert.ok(VALID_DISPLAY_TYPES.includes('area-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('line-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('bar-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('donut-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('multi-line-chart'))
})

test('validateIntent: accepts T3-SDK with chart displayAs (area-chart, line-chart, bar-chart, donut-chart)', () => {
  for (const chartType of ['area-chart', 'line-chart', 'bar-chart', 'donut-chart']) {
    const errors = validateIntent({
      schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
      metrics: [{ name: 'custom', tier: 'T3', title: 'X', displayAs: chartType }]
    })
    assert.deepEqual(errors, [], `${chartType} should be valid for T3-SDK`)
  }
})

test('validateIntent: rejects T3-SDK with truly unsupported displayAs', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', title: 'X', displayAs: 'unknown-widget' }]
  })
  assert.ok(errors.some(e => e.includes('unsupported displayAs')))
})

test('validateIntent: accepts T3-SDK with ranked-table displayAs', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', title: 'X', displayAs: 'ranked-table' }]
  })
  assert.deepEqual(errors, [])
})

test('buildWidgetFile: injects valueField and valueLabel placeholders', () => {
  const content = buildWidgetFile({
    name: 'running-jobs', tier: 'T3', title: 'Running Jobs', displayAs: 'kpi-card',
    fnBody: 'return []', valueField: 'count', valueLabel: 'running jobs'
  }, null)
  assert.ok(content.includes("const VALUE_FIELD = 'count'"))
  assert.ok(content.includes("const VALUE_LABEL = 'running jobs'"))
  assert.ok(!content.includes('<<VALUE_FIELD>>'))
  assert.ok(!content.includes('<<VALUE_LABEL>>'))
})

// ── Presentation overhaul: headline / delta / subtitle / columns / rate ───────

test('VALID_DISPLAY_TYPES includes rate-chart', () => {
  assert.ok(VALID_DISPLAY_TYPES.includes('rate-chart'))
})

test('buildWidgetFile: chart injects headline aggregate + delta (not last point)', () => {
  const content = buildWidgetFile(
    { name: 'runs-trend', tier: 'T3', title: 'Runs', displayAs: 'line-chart', xKey: 'date', yKey: 'count', headlineMode: 'sum', deltaPolarity: 'up-good', fnBody: 'return []' },
    null, '30d'
  )
  assert.ok(content.includes("headline(chartData, 'count', 'sum')"), 'headline aggregate not injected')
  assert.ok(content.includes("delta(chartData, 'count', 'up-good')"), 'delta not injected')
  assert.equal(content.match(/<SUBTITLE>|<HEADLINE_MODE>|<DELTA_POLARITY>/g), null, 'placeholders not replaced')
})

test('buildWidgetFile: chart subtitle auto-fills from time range when none given', () => {
  const content = buildWidgetFile(
    { name: 'x', tier: 'T3', title: 'X', displayAs: 'area-chart', yKey: 'value', fnBody: 'return []' },
    null, '7d'
  )
  assert.ok(content.includes('Last 7 days'))
})

test('buildWidgetFile: rate-chart injects rate helpers + num/den fields', () => {
  const content = buildWidgetFile(
    { name: 'err-rate', tier: 'T3', title: 'Error Rate', displayAs: 'rate-chart', xKey: 'date', rateNum: 'faulted', rateDen: 'total', deltaPolarity: 'up-bad', fnBody: 'return []' },
    null, '30d'
  )
  assert.ok(content.includes("rateSeries(raw, 'faulted', 'total', 'date')"))
  assert.ok(content.includes("overallRate(raw, 'faulted', 'total')"))
  assert.ok(!content.includes('<RATE_NUM>'))
})

test('compileColumns: passes a string literal through unchanged', () => {
  const lit = '[{key:"name",label:"Name"}]'
  assert.equal(compileColumns(lit), lit)
})

test('compileColumns: compiles an array with format/color into render fns', () => {
  const out = compileColumns([
    { key: 'processName', label: 'Process' },
    { key: 'duration', label: 'Duration', align: 'right', format: 'duration' },
    { key: 'successRate', label: 'Success', align: 'right', format: 'percent', color: 'goodHigh' },
  ])
  assert.ok(out.includes('key:"processName"'))
  assert.ok(out.includes('fmtDuration(Number(v))'))
  assert.ok(out.includes('fmtPercent(Number(v))'))
  assert.ok(out.includes('toneClass(Number(v),"goodHigh")'))
})

test('validateIntent: rejects invalid headlineMode', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', headlineMode: 'median' }],
  })
  assert.ok(errors.some(e => e.includes('headlineMode')))
})

test('validateIntent: rejects invalid deltaPolarity', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', deltaPolarity: 'sideways' }],
  })
  assert.ok(errors.some(e => e.includes('deltaPolarity')))
})

test('validateIntent: rate-chart requires rateNum + rateDen', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'rate-chart' }],
  })
  assert.ok(errors.some(e => e.includes('rateNum')))
})

test('validateIntent: accepts valid presentation hints', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', headlineMode: 'avg', deltaPolarity: 'up-bad' }],
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: rejects detailColumns entry with bad format', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', detailColumns: [{ key: 'd', label: 'D', format: 'bogus' }] }],
  })
  assert.ok(errors.some(e => e.includes('invalid format')))
})

test('buildWidgetFile: every chart type generates with no leftover placeholders and imports fetchData', () => {
  for (const displayAs of ['line-chart', 'area-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart']) {
    const metric = {
      name: 'm', tier: 'T3', title: 'M', displayAs,
      xKey: 'date', yKey: 'value', rateNum: 'num', rateDen: 'den',
    }
    const content = buildWidgetFile(metric, null, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${displayAs} has leftover placeholders`)
    assert.ok(content.includes("import { fetchData } from '@/metrics/m'"), `${displayAs} missing fetchData import`)
    assert.ok(content.includes('useWidgetData(fetchData, [])'), `${displayAs} missing useWidgetData(fetchData, [])`)
    assert.ok(!content.includes('customDataFn'), `${displayAs} should not splice customDataFn`)
  }
})

test('generateViewFile: imports metric module and uses compiled detailColumns', () => {
  const view = generateViewFile({
    componentName: 'FaultedJobs',
    title: 'Faulted Jobs',
    subtitle: 'Last 30 days',
    moduleSpecifier: '@/metrics/faulted-jobs',
    detailExport: 'fetchData',
    detailColumns: compileColumns([
      { key: 'processName', label: 'Process' },
      { key: 'startTime', label: 'Started', format: 'timeAgo' },
    ]),
    defaultSortKey: 'startTime',
  })
  assert.ok(view.includes('FaultedJobsView'))
  assert.ok(view.includes("import { fetchData } from '@/metrics/faulted-jobs'"), 'metric import not present')
  assert.ok(view.includes('useWidgetData(fetchData, [])'), 'useWidgetData call not present')
  assert.ok(!view.includes('const customDataFn = async'), 'customDataFn must not appear')
  assert.ok(view.includes('fmtTimeAgo(String(v))'), 'formatted column not embedded')
  assert.ok(view.includes('defaultSortKey={"startTime"}'), 'explicit sort key not used')
  assert.ok(!view.includes('autoColumns(rows)') || view.includes('function autoColumns'), 'autoColumns only as fallback definition')
})

test('generateViewFile: falls back to autoColumns when no detailColumns', () => {
  const view = generateViewFile({
    componentName: 'Trend', title: 'Trend', subtitle: '',
    moduleSpecifier: '@/metrics/trend',
    detailExport: 'fetchData',
    detailColumns: null,
  })
  assert.ok(view.includes('const columns = autoColumns(rows)'))
})

// ── SDK 1.4.1: agent / memory / governance metrics ────────────────────────────

test('1.4.1: previously-refused agent metrics now resolve as T1', () => {
  for (const [text, expected] of [
    ['show active agents', 'active-agents-kpi'],
    ['agu consumption by agent', 'agent-consumption'],
    ['agents by health', 'agent-health'],
    ['memory calls over time', 'memory-calls-trend'],
    ['top memory spaces', 'top-memory-spaces'],
    ['policy denials this week', 'policy-denials'],
    ['governance summary', 'governance-verdicts'],
  ]) {
    const result = resolveAlias(text)
    assert.ok(result, `"${text}" did not resolve`)
    assert.equal(result.key, expected, `"${text}" resolved to ${result.key}, expected ${expected}`)
  }
})

test('1.4.1: agent/trace timeline metrics now resolve as T1', () => {
  for (const [text, expected] of [
    ['agent error rate trend', 'agent-error-timeline'],
    ['errors over time', 'agent-error-timeline'],
    ['agent latency p95', 'agent-latency-timeline'],
    ['latency over time', 'agent-latency-timeline'],
    ['consumption timeline', 'agent-consumption-timeline'],
    ['consumption over time', 'agent-consumption-timeline'],
    ['top errors', 'agent-errors'],
    ['errors by type', 'agent-errors'],
    ['trace latency', 'trace-latency-timeline'],
    ['trace errors', 'trace-error-timeline'],
    ['unit consumption', 'agent-unit-consumption'],
  ]) {
    const result = resolveAlias(text)
    assert.ok(result, `"${text}" did not resolve`)
    assert.equal(result.key, expected, `"${text}" resolved to ${result.key}, expected ${expected}`)
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(!refused, `"${text}" should NOT be hard-refused — SDK 1.4.1 supports it`)
  }
})

test('1.4.1: invocation-count timelines (no SDK endpoint) are still hard-refused', () => {
  for (const text of ['invocation volume over time', 'invocations over time', 'invocation count by day']) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(refused, `"${text}" should be hard-refused (no SDK 1.4.1 invocation-count endpoint)`)
  }
})

test('1.4.1: t1_unavailable section is gone (stale PR #438 entries removed)', () => {
  assert.equal(registry.t1_unavailable, undefined)
})

test('1.4.1: agent-health shell build compiles formatted/colored columnDefs', () => {
  const entry = registry.t1['agent-health']
  const content = buildWidgetFile(
    { name: 'agent-health', tier: 'T1', title: 'Agent Health', displayAs: 'ranked-table', fnBody: 'return []' },
    entry,
    '30d'
  )
  assert.ok(content.includes('toneClass(Number(v),"goodHigh")'), 'healthScore colour not compiled')
  assert.ok(content.includes('fmtTimeAgo(String(v))'), 'lastRun timeAgo format not compiled')
})

// ── fnBody harness signature: SDK interface arrays must be accepted ───────────
// SDK response types are interfaces (no implicit index signature) — NOT assignable
// to Record<string, unknown>[]. The injected customDataFn must be Promise<any[]>
// so `return result?.items ?? []` typechecks without casts. (Repro: TS2322.)

test('harness: chart widget imports fetchData from metric module (no spliced Promise<any[]> wrapper)', () => {
  const content = buildWidgetFile(
    { name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', yKey: 'v' },
    null, '7d'
  )
  assert.ok(content.includes("import { fetchData } from '@/metrics/m'"), 'chart must import fetchData from metric module')
  assert.ok(content.includes('useWidgetData(fetchData, [])'), 'chart must use useWidgetData(fetchData, [])')
  assert.ok(!content.includes('customDataFn'), 'chart must not splice customDataFn')
  assert.ok(!content.includes('Promise<Record<string, unknown>[]>'), 'old index-signature-demanding wrapper must be gone')
})

test('harness: shell widget imports fetchData from metric module (no embedded customDataFn)', () => {
  const content = buildWidgetFile(
    { name: 'm', tier: 'T3', title: 'M', displayAs: 'data-table' },
    null, '7d'
  )
  assert.ok(content.includes("import { fetchData } from '@/metrics/m'"), 'shell must import fetchData from metric module')
  assert.ok(content.includes('fetchData(sdk, getToken)'), 'shell must call fetchData')
  assert.ok(!content.includes('const customDataFn = async'), 'shell must not embed customDataFn')
})

test('harness: detail view imports metric module (no customDataFn, no Promise<any[]> wrapper)', () => {
  const view = generateViewFile({
    componentName: 'X', title: 'X', subtitle: '',
    moduleSpecifier: '@/metrics/x',
    detailExport: 'fetchData',
    detailColumns: null,
  })
  assert.ok(view.includes("import { fetchData } from '@/metrics/x'"), 'metric import not present')
  assert.ok(view.includes('useWidgetData(fetchData, [])'), 'useWidgetData call not present')
  assert.ok(!view.includes('const customDataFn = async'), 'customDataFn must not appear')
  assert.ok(!view.includes('Promise<any[]>'), 'old Promise<any[]> wrapper must be gone')
})

// ── Incremental edit: change-merge + layout grouping ──────────────────────────

test('resolveChangeMetric: timeRange-only delta keeps persisted metadata', () => {
  const stored = {
    tier: 'T1', metric: 'memory-calls-trend', template: 'area-chart',
    intentMetric: { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', displayAs: 'area-chart' },
  }
  const merged = resolveChangeMetric(stored, 'MemoryCallsTrend', { timeRange: '7d' })
  assert.equal(merged.title, 'Memory Calls')
  assert.equal(merged.displayAs, 'area-chart')
  assert.equal(merged.timeRange, '7d')
})

test('resolveChangeMetric: delta fields override persisted intentMetric', () => {
  const stored = { intentMetric: { name: 'm', tier: 'T3', title: 'Old', displayAs: 'area-chart' } }
  const merged = resolveChangeMetric(stored, 'M', { displayAs: 'data-table', module: 'metrics/m.ts' })
  assert.equal(merged.displayAs, 'data-table')
  assert.equal(merged.module, 'metrics/m.ts')
  assert.equal(merged.title, 'Old')
})

test('resolveChangeMetric: legacy state without intentMetric yields a minimal ref', () => {
  const merged = resolveChangeMetric({ tier: 'T1', metric: 'job-failures' }, 'JobFailures', { timeRange: '7d' })
  assert.equal(merged.name, 'job-failures')
  assert.equal(merged.tier, 'T1')
  assert.equal(merged.title, undefined)
})

test('widgetLayoutGroup: classifies only buildable types', () => {
  assert.equal(widgetLayoutGroup('kpi-card'), 'kpi')
  assert.equal(widgetLayoutGroup('data-table'), 'table')
  assert.equal(widgetLayoutGroup('ranked-table'), 'table')
  assert.equal(widgetLayoutGroup('rate-chart'), 'chart')
  assert.equal(widgetLayoutGroup('area-chart'), 'chart')
})

test('1.4.1: governance-verdicts donut uses name/value keys from defaults', () => {
  const entry = registry.t1['governance-verdicts']
  const content = buildWidgetFile(
    { name: 'governance-verdicts', tier: 'T1', title: 'Governance Verdicts', displayAs: 'donut-chart', fnBody: 'return []' },
    entry,
    '7d'
  )
  assert.ok(content.includes('dataKey="value"'))
  assert.ok(content.includes('nameKey="name"'))
})

// ── metricModuleSpecifier tests ───────────────────────────────────────────────

test('metricModuleSpecifier derives @/metrics/<name> by default', () => {
  assert.equal(metricModuleSpecifier({ name: 'agent-health' }), '@/metrics/agent-health')
})

test('metricModuleSpecifier honors explicit module field and strips .ts', () => {
  assert.equal(metricModuleSpecifier({ name: 'x', module: 'metrics/custom-thing.ts' }), '@/metrics/custom-thing')
})

test('validateIntent accepts a metadata-only metric (no fnBody)', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'agent-health', tier: 'T1', title: 'Agent Health', displayAs: 'ranked-table' }],
  })
  assert.deepEqual(errors, [])
})

test('validateIntent rejects intent missing schemaVersion 2', () => {
  const errors = validateIntent({
    dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'kpi-card' }],
  })
  assert.ok(errors.some(e => /schemaVersion/.test(e)))
})

test('buildWidgetFile (chart) imports fetchData and does not splice customDataFn', () => {
  const out = buildWidgetFile(
    { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', displayAs: 'area-chart', xKey: 'timeSlice', yKey: 'memoryCallsCount' },
    null, '30d'
  )
  assert.match(out, /import \{ fetchData \} from '@\/metrics\/memory-calls-trend'/)
  assert.match(out, /useWidgetData\(fetchData, \[\]\)/)
  assert.doesNotMatch(out, /const customDataFn = async/)
})

test('buildWidgetFile (kpi/table) imports fetchData and has no embedded customDataFn', () => {
  const out = buildWidgetFile(
    { name: 'job-failures', tier: 'T1', title: 'Faulted Jobs', displayAs: 'data-table',
      columns: '[{key:"processName",label:"Process"}]' },
    null, '30d'
  )
  assert.match(out, /import \{ fetchData \} from '@\/metrics\/job-failures'/)
  assert.match(out, /fetchData\(sdk, getToken\)/)
  assert.doesNotMatch(out, /const customDataFn = async/)
})

test('generateViewFile imports the metric module detail/data export', () => {
  const spec = buildViewSpec('MemoryCallsTrend',
    { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', displayAs: 'area-chart' },
    null, '30d')
  const out = generateViewFile(spec)
  assert.match(out, /import \{ (fetchData|fetchDetail) \} from '@\/metrics\/memory-calls-trend'/)
  assert.doesNotMatch(out, /const customDataFn = async/)
})

test('classifyEditIntent ADD carries metric metadata without fnBody', () => {
  const plan = classifyEditIntent({
    projectDir: '/p',
    ops: [{ op: 'ADD', metric: { name: 'agent-health', tier: 'T1', title: 'Agent Health', displayAs: 'ranked-table' } }],
  })
  assert.equal(plan.ops[0].op, 'ADD')
  assert.equal(plan.ops[0].metric.name, 'agent-health')
  assert.equal(plan.ops[0].metric.fnBody, undefined)
})

// ── Maestro Insights + SLA coverage (review items 1–4) ────────────────────────

function genWidget(name) {
  const entry = registry.t1[name]
  assert.ok(entry, `missing T1 entry ${name}`)
  const metric = { name, tier: 'T1', title: entry.defaults.title, displayAs: entry.template, ...entry.defaults }
  const content = buildWidgetFile(metric, entry, '30d')
  assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${name} leftover placeholders`)
  assert.ok(content.includes(`import { fetchData } from '@/metrics/${name}'`), `${name} missing fetchData import`)
  return { entry, content }
}

test('item 4: error-text refuse narrowed — aggregated error classes NOT refused', () => {
  for (const text of ['top errors', 'errors by type', 'agent error breakdown']) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(!refused, `"${text}" must not be hard-refused — Agents.getErrors aggregates error classes`)
  }
})

test('item 4: error-text refuse still blocks raw stack traces', () => {
  for (const text of ['show me the stack trace', 'exception text per job', 'raw error message text']) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(refused, `"${text}" should be hard-refused (no raw stack-trace aggregation)`)
  }
})

test('item 1: SLA metrics resolve T1 and are NOT refused', () => {
  for (const [text, expected] of [
    ['sla breach', 'case-sla-breaches'],
    ['cases at risk', 'case-sla-breaches'],
    ['overdue cases', 'case-sla-breaches'],
    ['sla status', 'case-sla-status'],
    ['sla breakdown', 'case-sla-status'],
    ['stage sla', 'case-stage-sla'],
  ]) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(!refused, `"${text}" must not be hard-refused — SLA summary exists`)
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('item 1: SLA T1 entries generate clean widgets', () => {
  for (const name of ['case-sla-status', 'case-sla-breaches', 'case-stage-sla']) genWidget(name)
})

test('item 2a: Maestro process Insights metrics resolve T1', () => {
  for (const [text, expected] of [
    ['busiest processes', 'top-maestro-processes-by-runs'],
    ['top failing processes', 'top-maestro-processes-by-faults'],
    ['slowest processes', 'top-maestro-processes-by-duration'],
    ['process status over time', 'maestro-process-status-timeline'],
    ['failing elements', 'top-failing-process-elements'],
  ]) {
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('item 2a: process Insights T1 entries generate clean widgets (incl. status series)', () => {
  for (const name of ['top-maestro-processes-by-runs', 'top-maestro-processes-by-faults', 'top-maestro-processes-by-duration', 'maestro-process-status-timeline', 'top-failing-process-elements']) {
    const { entry, content } = genWidget(name)
    if (entry.template === 'multi-line-chart') assert.ok(content.includes('Faulted'), `${name} missing status series`)
  }
})

test('item 2b: Maestro case Insights metrics resolve T1', () => {
  for (const [text, expected] of [
    ['busiest cases', 'top-cases-by-runs'],
    ['top failing cases', 'top-cases-by-faults'],
    ['slowest cases', 'top-cases-by-duration'],
    ['case status over time', 'case-status-timeline'],
    ['failing case elements', 'top-failing-case-elements'],
  ]) {
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('item 2b: case Insights T1 entries generate clean widgets', () => {
  for (const name of ['top-cases-by-runs', 'top-cases-by-faults', 'top-cases-by-duration', 'case-status-timeline', 'top-failing-case-elements']) genWidget(name)
})

test('item 2c: element-latency-stats resolves T2', () => {
  const r = resolveAlias('element latency stats')
  assert.ok(r, 'did not resolve')
  assert.equal(r.tier, 'T2')
  assert.equal(r.key, 'element-latency-stats')
})

test('scope: Insights RTM + PIMS present in all scope lists', () => {
  const build = readFileSync(resolve(__dirname, '../build-dashboard.mjs'), 'utf8')
  const scopesLine = build.match(/DASHBOARD_SCOPES\s*=\s*'([^']*)'/)?.[1] ?? ''
  const granted = scopesLine.split(/\s+/)
  for (const s of ['Insights', 'Insights.RealTimeData', 'OR.Folders', 'PIMS']) {
    assert.ok(granted.includes(s), `DASHBOARD_SCOPES missing ${s}`)
  }
  const impl = readFileSync(resolve(__dirname, '../../../references/dashboards/plugins/build/impl.md'), 'utf8')
  assert.ok(/--user-scope "[^"]*Insights,Insights\.RealTimeData[^"]*PIMS/.test(impl), 'full create command missing Insights RTM + PIMS')
})

// ── Robustness fixes (Agent-Ops postmortem: KPI delta, row-click, columns, OData lint) ──

test('Defect 1: KPI with previousField/deltaPolarity emits a delta badge', () => {
  const out = buildWidgetFile(
    { name: 'active-agents', tier: 'T3', title: 'Active Agents', displayAs: 'kpi-card', valueField: 'value', previousField: 'previous', deltaPolarity: 'up-good' },
    null, '30d'
  )
  assert.equal(out.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, 'leftover placeholders')
  assert.ok(out.includes('kpiDelta('), 'KPI must compute kpiDelta')
  assert.ok(out.includes('DeltaBadge'), 'KPI must render DeltaBadge')
  assert.ok(out.includes("const PREVIOUS_FIELD = 'previous'"), 'previousField not substituted')
  assert.ok(out.includes("const DELTA_POLARITY = 'up-good'"), 'deltaPolarity not substituted')
})

test('Defect 1: plain KPI (no previous) still generates and shows no badge data', () => {
  const out = buildWidgetFile(
    { name: 'running-jobs', tier: 'T3', title: 'Running Jobs', displayAs: 'kpi-card', valueField: 'count' },
    null, '30d'
  )
  assert.equal(out.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, 'leftover placeholders')
  assert.ok(out.includes("const PREVIOUS_FIELD = ''"), 'plain KPI must have empty PREVIOUS_FIELD')
})

test('Defect 1: registry active-agents-kpi defaults drive the delta badge', () => {
  const entry = registry.t1['active-agents-kpi']
  assert.equal(entry.defaults.previousField, 'previous')
  const out = buildWidgetFile({ name: 'active-agents-kpi', tier: 'T1', title: 'Active Agents', displayAs: 'kpi-card' }, entry, '30d')
  assert.ok(out.includes("const PREVIOUS_FIELD = 'previous'"), 'registry previousField default not applied')
  assert.ok(out.includes('DeltaBadge'))
})

test('Defect 2: table with rowLink emits onRowClick navigate; without rowLink it does not', () => {
  const withLink = buildWidgetFile(
    { name: 'all-agents', tier: 'T3', title: 'Agents', displayAs: 'data-table', columns: '[{key:"agentName",label:"Agent"}]', rowLink: { key: 'agentName' }, defaultSortAsc: true },
    null, '30d'
  )
  assert.equal(withLink.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, 'leftover placeholders')
  assert.ok(withLink.includes("const ROW_LINK_KEY = 'agentName'"), 'rowLink key not substituted')
  assert.ok(withLink.includes("const ROW_LINK_ROUTE = '/allagents'"), 'rowLink route not derived')
  assert.ok(withLink.includes('onRowClick'), 'rowLink table must wire onRowClick')
  assert.ok(withLink.includes('defaultSortAsc={true}'), 'defaultSortAsc not substituted')

  const noLink = buildWidgetFile(
    { name: 'plain', tier: 'T3', title: 'Plain', displayAs: 'data-table', columns: '[{key:"a",label:"A"}]' },
    null, '30d'
  )
  assert.ok(noLink.includes("const ROW_LINK_KEY = ''"), 'plain table must have empty ROW_LINK_KEY')
})

test('Defect 2: generateKeyedDetailViewFile imports fetchDetailByKey + reads route param', () => {
  const view = generateKeyedDetailViewFile({
    componentName: 'AllAgents', title: 'Agents', subtitle: 'Spans',
    moduleSpecifier: '@/metrics/all-agents', detailColumns: null,
  })
  assert.ok(view.includes("import { fetchDetailByKey } from '@/metrics/all-agents'"), 'keyed view must import fetchDetailByKey')
  assert.ok(view.includes('useParams'), 'keyed view must read the route param')
  assert.ok(view.includes('fetchDetailByKey(sdk, key, getToken)'), 'keyed view must call fetchDetailByKey with key')
  assert.ok(view.includes('export function AllAgentsDetailView()'), 'keyed view component name')
})

test('Defect 3: table with no columns auto-detects at runtime (no error, no name/value placeholder)', () => {
  // detailColumns-only (the postmortem mistake) no longer breaks — it auto-detects.
  const errs = validateIntent({
    schemaVersion: 2, dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table', detailColumns: [{ key: 'a', label: 'A' }] }],
  })
  assert.deepEqual(errs, [])
  const out = buildWidgetFile({ name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table' }, null, '30d')
  assert.equal(out.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, 'leftover placeholders')
  assert.ok(out.includes('COLUMNS.length ? COLUMNS : autoColumns(data)'), 'table must auto-detect columns when none given')
  assert.ok(out.includes('const COLUMNS: ColumnDef<Row>[] = []'), 'no explicit columns → empty COLUMNS')
  assert.ok(!out.includes('{key:"name",label:"Name"},{key:"value"'), 'must not emit static name/value placeholder')
})

test('Defect 3: explicit columns honored; T1 registry tables unaffected', () => {
  const out = buildWidgetFile({ name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table', columns: '[{key:"agentName",label:"Agent"}]' }, null, '30d')
  assert.ok(out.includes('agentName'))
  const t1ok = validateIntent({
    schemaVersion: 2, dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'job-failures', tier: 'T1', title: 'Faulted Jobs' }],
  })
  assert.deepEqual(t1ok, [])
})

test('Defect 2: invalid rowLink is rejected', () => {
  const errs = validateIntent({
    schemaVersion: 2, dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table', columns: '[{key:"a",label:"A"}]', rowLink: { foo: 'bar' } }],
  })
  assert.ok(errs.some(e => /rowLink must be an object with a string "key"/.test(e)))
})

test('multi-line series: an array in intent.json compiles to a TS literal (not [object Object])', () => {
  const out = buildWidgetFile(
    { name: 'agent-latency', tier: 'T3', title: 'Latency', displayAs: 'multi-line-chart', xKey: 'date',
      series: [{ key: 'P50', color: 'hsl(var(--chart-1))' }, { key: 'P95', color: 'hsl(var(--chart-2))', label: 'P95 (ms)' }] },
    null, '30d'
  )
  assert.ok(!out.includes('[object Object]'), 'array series must not coerce to [object Object]')
  assert.ok(out.includes('key:"P50",color:"hsl(var(--chart-1))"'), 'series key/color not compiled')
  assert.ok(out.includes('label:"P95 (ms)"'), 'optional series label not compiled')
})

test('multi-line series: a string literal (registry form) passes through unchanged', () => {
  const out = buildWidgetFile(
    { name: 'x', tier: 'T3', title: 'X', displayAs: 'multi-line-chart', xKey: 'date',
      series: '[{key:"Completed",color:"hsl(var(--chart-3))"}]' },
    null, '30d'
  )
  assert.ok(out.includes('key:"Completed"') && !out.includes('[object Object]'))
})

test('Perf: scaffold tsconfig has incremental + skipLibCheck', () => {
  const ts = JSON.parse(readFileSync(resolve(__dirname, '../../templates/dashboard/scaffold/tsconfig.json'), 'utf8'))
  assert.equal(ts.compilerOptions.incremental, true, 'incremental must be enabled')
  assert.equal(ts.compilerOptions.skipLibCheck, true, 'skipLibCheck must be enabled')
  assert.ok(ts.compilerOptions.tsBuildInfoFile, 'tsBuildInfoFile must be set (required with noEmit+incremental)')
})
