import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, mkdtempSync, writeFileSync, rmSync, mkdirSync, existsSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import { execSync } from 'node:child_process'
import { validateIntent, resolveMetric, buildWidgetFile, generateViewFile, generateKeyedDetailViewFile, buildViewSpec, compileColumns, compileDetailWidgets, emit, parseEvent, classifyEditIntent, resolveChangeMetric, widgetLayoutGroup, widgetGetsDetailView, setWidgetsDir, VALID_DISPLAY_TYPES, metricModuleSpecifier, buildVersions, readScaffoldVersion, INTENT_SCHEMA_VERSION, STATE_SCHEMA_VERSION, scaffoldDrift, runIntentMigrations, VALID_EDIT_OPS, MIN_SDK_VERSION } from '../build-dashboard.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REGISTRY_PATH = resolve(__dirname, '../capability-registry.json')

const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'))

// Widget generator templates ship inside the committed starter-kit zip (the skill
// carries no template source). For generation tests, extract that zip with whatever
// OS tool is available — self-contained (no sibling-repo dependency) and it tests the
// ACTUAL shipped templates. Falls back to the apps-dev-tools sibling source if present.
function locateWidgetTemplates() {
  const zip = resolve(__dirname, '../../fixtures/governance-dashboard-starter-kit.zip')
  if (existsSync(zip)) {
    const dest = mkdtempSync(join(tmpdir(), 'kit-test-'))
    // execSync with a shell string is fine here: `zip`/`dest` are internal paths
    // (resolve(__dirname,…) / mkdtempSync), never user input — no injection surface.
    for (const cmd of [
      `unzip -o "${zip}" -d "${dest}"`,
      `python3 -m zipfile -e "${zip}" "${dest}"`,
      `python -m zipfile -e "${zip}" "${dest}"`,
      `powershell -NoProfile -Command "Expand-Archive -LiteralPath '${zip}' -DestinationPath '${dest}' -Force"`,
    ]) {
      try { execSync(cmd, { stdio: 'pipe' }); break } catch { /* try next extractor */ }
    }
    const w = join(dest, '_gen', 'widgets')
    if (existsSync(w)) return w
  }
  const sibling = resolve(__dirname, '../../../../../../apps-dev-tools/uipath-dashboard-starter-kit/widgets')
  return existsSync(sibling) ? sibling : null
}
const WIDGETS_DIR_FOR_TESTS = locateWidgetTemplates()
if (WIDGETS_DIR_FOR_TESTS) setWidgetsDir(WIDGETS_DIR_FOR_TESTS)

// ── Phase 2: version stamps ───────────────────────────────────────────────────
// The scaffold version is read from the extracted kit (_gen/starter-kit.json) and
// passed in — there is no module-level SCAFFOLD_VERSION const anymore.
test('buildVersions stamps skill/scaffold/intentSchema/sdk', () => {
  const v = buildVersions('1.4.1', '2.7.0')
  assert.equal(v.scaffold, '2.7.0')
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

// ── Phase 2: scaffold drift (current version supplied by the caller) ──────────
test('scaffoldDrift: none when stamped scaffold equals current', () => {
  assert.equal(scaffoldDrift({ versions: { scaffold: '2.7.0' } }, '2.7.0'), null)
})

test('scaffoldDrift: detected when stamped differs', () => {
  assert.deepEqual(scaffoldDrift({ versions: { scaffold: '0.9.0' } }, '2.7.0'), { from: '0.9.0', to: '2.7.0' })
})

test('scaffoldDrift: detected for a pre-versioning project (no versions block)', () => {
  assert.deepEqual(scaffoldDrift({ widgets: {} }, '2.7.0'), { from: null, to: '2.7.0' })
})

test('readScaffoldVersion reads the version from the extracted _gen/starter-kit.json', () => {
  const dir = mkdtempSync(join(tmpdir(), 'scaffver-'))
  mkdirSync(join(dir, '_gen'), { recursive: true })
  writeFileSync(join(dir, '_gen', 'starter-kit.json'), JSON.stringify({ name: 'x', version: '9.9.9' }))
  assert.equal(readScaffoldVersion(dir), '9.9.9')
  assert.equal(readScaffoldVersion(join(dir, 'nope')), '0.0.0') // missing → safe default
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
// NOTE: zip/unzip + contentHash + zip-slip tests moved to apps-dev-tools
// (uipath-dashboard-starter-kit/tests/zip.test.mjs) along with zip.mjs — the
// skill no longer ships any zip code or scaffold source.

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

test('chart widgets: card chrome always renders; loading shows a chart-sized skeleton (not a full-card block)', () => {
  const cases = [
    { displayAs: 'area-chart', xKey: 'date', yKey: 'value', h: 'h-[180px]' },
    { displayAs: 'bar-chart', xKey: 'name', yKey: 'value', h: 'h-[180px]' },
    { displayAs: 'line-chart', xKey: 'date', yKey: 'value', h: 'h-[180px]' },
    { displayAs: 'donut-chart', xKey: 'name', yKey: 'value', h: 'h-[180px]' },
    { displayAs: 'multi-line-chart', xKey: 'date', series: [{ key: 'Pass', color: 'hsl(var(--chart-2))' }, { key: 'Matched', color: 'hsl(var(--chart-1))' }], h: 'h-[200px]' },
    { displayAs: 'rate-chart', xKey: 'date', rateNum: 'num', rateDen: 'den', h: 'h-[180px]' },
  ]
  for (const c of cases) {
    const content = buildWidgetFile({ name: `w-${c.displayAs}`, tier: 'T3', title: 'W', ...c }, null, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${c.displayAs}: leftover placeholders`)
    assert.ok(content.includes('<CardHeader'), `${c.displayAs}: CardHeader missing`)
    // The regressed pattern was an early `if (loading) return <LoadingState ...` BEFORE the card.
    assert.ok(!/if \(loading\)\s*return\s*<LoadingState/.test(content), `${c.displayAs}: still bails to a full-card skeleton`)
    // Body skeleton must be chart-sized, never the oversized default h-64 / bare <LoadingState />.
    assert.ok(content.includes(`<LoadingState height="${c.h}"`), `${c.displayAs}: loading skeleton not sized ${c.h}`)
    assert.ok(!content.includes('<LoadingState />'), `${c.displayAs}: bare unsized LoadingState present`)
  }
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

// ── SDK 1.5.0: Agents insights aggregate metrics ──────────────────────────────

test('1.5.0: new Agents insights metrics resolve as T1', () => {
  for (const [text, expected] of [
    ['agents by error count', 'agents-by-errors'],
    ['noisiest agents', 'agents-by-errors'],
    ['incident distribution', 'agent-incident-distribution'],
    ['errors vs escalations vs policy', 'agent-incident-distribution'],
    ['agent success rate', 'agent-success-rate'],
    ['job success rate', 'agent-success-rate'],
    ['total agent units', 'agent-unit-consumption-summary'],
  ]) {
    const result = resolveAlias(text)
    assert.ok(result, `"${text}" did not resolve`)
    assert.equal(result.key, expected, `"${text}" resolved to ${result.key}, expected ${expected}`)
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern, 'i').test(text))
    assert.ok(!refused, `"${text}" should NOT be hard-refused — SDK 1.5.0 supports it`)
  }
})

test('1.5.0: insights metrics generate clean widgets (no leftover placeholders; KPIs default value/previous)', () => {
  for (const name of ['agents-by-errors', 'agent-incident-distribution', 'agent-success-rate', 'agent-unit-consumption-summary', 'agent-consumption']) {
    const entry = registry.t1[name]
    assert.ok(entry, `missing ${name}`)
    const content = buildWidgetFile({ name, tier: 'T1', title: entry.defaults.title, displayAs: entry.template, ...entry.defaults }, entry, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${name}: leftover placeholders`)
    assert.ok(content.includes(`import { fetchData } from '@/metrics/${name}'`), `${name}: missing fetchData import`)
  }
  // The two summary KPIs must carry the conventional value/previous delta fields.
  for (const name of ['agent-success-rate', 'agent-unit-consumption-summary']) {
    const entry = registry.t1[name]
    const content = buildWidgetFile({ name, tier: 'T1', title: entry.defaults.title, displayAs: 'kpi-card', ...entry.defaults }, entry, '30d')
    assert.ok(content.includes("const VALUE_FIELD = 'value'"), `${name}: VALUE_FIELD must be 'value'`)
    assert.ok(content.includes("const PREVIOUS_FIELD = 'previous'"), `${name}: PREVIOUS_FIELD must be 'previous' for the lookback delta`)
  }
})

test('1.5.0: MIN_SDK_VERSION floor is 1.5.0 (insights aggregates ship in 1.5.0)', () => {
  assert.equal(MIN_SDK_VERSION, '1.5.0')
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

test('Defect 1: kpi-card with no valueField defaults to value/previous (no "headline 1" count)', () => {
  const out = buildWidgetFile(
    { name: 'gov-violations', tier: 'T3', title: 'Governance Violations', displayAs: 'kpi-card' },
    null, '30d'
  )
  assert.equal(out.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, 'leftover placeholders')
  assert.ok(out.includes("const VALUE_FIELD = 'value'"), 'kpi-card must default VALUE_FIELD to "value", not render data.length')
  assert.ok(out.includes("const PREVIOUS_FIELD = 'previous'"), 'conventional kpi-card must default PREVIOUS_FIELD to "previous"')
})

test('Defect 1: kpi-card with explicitly empty valueField fails loud', () => {
  assert.throws(
    () => buildWidgetFile(
      { name: 'broken-kpi', tier: 'T3', title: 'Broken', displayAs: 'kpi-card', valueField: '' },
      null, '30d'
    ),
    /no valueField/,
    'kpi-card with empty valueField must throw rather than silently render the row count'
  )
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

// NOTE: scaffold tsconfig (incremental/skipLibCheck) is now validated in
// apps-dev-tools (it owns the scaffold source) — not a skill concern.

// ── Governance violations (gated, trace-derived, interim) ─────────────────────

const TRACE_GOV_KEYS = new Set(['agent-governance-violations', 'violations-by-standard', 'violations-by-rule', 'violations-by-hook', 'agents-by-violations', 'recent-violations', 'agent-compliance-report'])

test('governance: trace metrics resolve T1 only on explicit runtime/standard/rule aliases', () => {
  for (const [text, expected] of [
    ['rule violations', 'agent-governance-violations'],
    ['runtime compliance violations', 'agent-governance-violations'],
    ['violations by standard', 'violations-by-standard'],
    ['iso violations', 'violations-by-standard'],
    ['violations by rule', 'violations-by-rule'],
    ['violations by hook', 'violations-by-hook'],
    ['agents with most violations', 'agents-by-violations'],
    ['rule violation log', 'recent-violations'],
    ['agent compliance report', 'agent-compliance-report'],
  ]) {
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('governance gate: plain agent-ops phrases do NOT pull in a trace-governance metric', () => {
  for (const text of ['active agents', 'agent health', 'agent latency p95', 'memory calls over time', 'faulted jobs', 'busiest processes']) {
    const r = resolveAlias(text)
    assert.ok(!r || !TRACE_GOV_KEYS.has(r.key), `"${text}" must not resolve to a trace-governance metric (got ${r?.key})`)
  }
})

test('governance no-regression: generic governance/policy phrases route to Insights-API metrics, not trace scan', () => {
  // The existing Governance SDK metrics must keep winning generic intent — the
  // trace-derived widgets are reserved for EXPLICIT runtime/standard/rule asks.
  for (const [text, expected] of [
    ['policy denials', 'policy-denials'],
    ['denied actions', 'policy-denials'],
    ['blocked actions', 'policy-denials'],
    ['policy violations', 'policy-denials'],
    ['governance denials', 'policy-denials'],
    ['governance summary', 'governance-verdicts'],
    ['allow deny breakdown', 'governance-verdicts'],
    ['enforcement summary', 'governance-verdicts'],
    ['governance overview', 'governance-verdicts'],
  ]) {
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.ok(!TRACE_GOV_KEYS.has(r.key), `"${text}" must NOT route to a trace-governance metric (got ${r?.key})`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('governance: matched-rules-by-action resolves and is an enforcement-action donut', () => {
  const r = resolveAlias('matched rules by action')
  assert.ok(r && r.key === 'matched-rules-by-action', `"matched rules by action" → ${r?.key}`)
  const entry = registry.t1['matched-rules-by-action']
  assert.equal(entry.template, 'donut-chart')
  assert.match(entry.description, /block.*audit.*allow|action/i)
})

test('governance: agent-compliance-report detailView leads with multi-line + by-action, keyed on runKey', () => {
  const entry = registry.t1['agent-compliance-report']
  assert.equal(entry.defaults.rowLink.key, 'runKey', 'compliance report must key rowLink on the run (runKey)')
  const widgets = entry.defaults.detailView.widgets
  assert.equal(widgets[0].displayAs, 'multi-line-chart', 'first detail sub-widget must be the Pass-vs-Matched multi-line')
  assert.equal(widgets[0].source, 'byOutcomeByHook')
  assert.ok(Array.isArray(widgets[0].series) && widgets[0].series.length === 2, 'multi-line must declare Pass/Matched series')
  assert.equal(widgets[1].displayAs, 'donut-chart', 'second detail sub-widget must be the by-action donut')
  assert.equal(widgets[1].source, 'byAction')
  // The whole detail view must compile (multi-line series wired, no leftover placeholders).
  const view = buildViewSpec('AgentComplianceReport', { name: 'agent-compliance-report', title: 'Agent Compliance' }, entry, '30d')
  assert.ok(view.detailView, 'detailView must resolve from registry defaults')
})

test('governance: all violation entries generate clean widgets (rowLink wired where set)', () => {
  for (const name of ['agent-governance-violations', 'violations-by-standard', 'violations-by-rule', 'violations-by-hook', 'matched-rules-by-action', 'agents-by-violations', 'recent-violations', 'agent-compliance-report']) {
    const entry = registry.t1[name]
    assert.ok(entry, `missing ${name}`)
    const metric = { name, tier: 'T1', title: entry.defaults.title, displayAs: entry.template, ...entry.defaults }
    const content = buildWidgetFile(metric, entry, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${name} leftover placeholders`)
    assert.ok(content.includes(`import { fetchData } from '@/metrics/${name}'`), `${name} missing fetchData import`)
    if (entry.defaults.rowLink) assert.ok(content.includes('onRowClick'), `${name} rowLink not wired`)
  }
})

// ── Regression guards: every build path must be kept in lockstep ──────────────
// (Caught the externalization bug where incremental edits never set the widgets
// dir and the row-click drill-down was wired only into the fresh build.)

test('regression: widgets dir is set + extraction asserted on every widget-generating path', () => {
  const src = readFileSync(resolve(__dirname, '../build-dashboard.mjs'), 'utf8')
  const setCalls = (src.match(/setWidgetsDir\(join\(P, '_gen', 'widgets'\)\)/g) || []).length
  assert.ok(setCalls >= 3, `setWidgetsDir(<proj>/_gen/widgets) must run on fresh build, upgrade, AND incremental edit; found ${setCalls}`)
  const assertCalls = (src.match(/assertScaffoldExtracted\(/g) || []).length
  // definition + fresh + upgrade + incremental + prewarm = 5
  assert.ok(assertCalls >= 5, `assertScaffoldExtracted must guard every build entry path; found ${assertCalls}`)
})

test('regression: row-click keyed views are wired on fresh + incremental + upgrade', () => {
  const src = readFileSync(resolve(__dirname, '../build-dashboard.mjs'), 'utf8')
  assert.ok(src.includes('injectAppRoutes(P, generatedViewNames, keyedViewWidgets)'), 'fresh build must inject keyed routes')
  assert.ok((src.match(/collectKeyedViews\(P, state\)/g) || []).length >= 2, 'incremental + upgrade must inject keyed routes via collectKeyedViews')
  assert.ok((src.match(/writeKeyedViewIfRowLink\(/g) || []).length >= 3, 'keyed detail view must be (re)written on ADD, CHANGE, and REBUILD')
  // no bare 2-arg injectAppRoutes call survives (the old broken incremental path)
  assert.ok(!/injectAppRoutes\(P, viewNames\)(?!,)/.test(src), 'no injectAppRoutes call may omit keyed views')
})

// ── Rich detail views (detailView spec) ───────────────────────────────────────

/** Minimal valid schemaVersion-2 intent with one overridable metric. */
function baseIntent(overrides = {}) {
  const { metrics, ...rest } = overrides
  return {
    schemaVersion: 2,
    dashboardName: 'D',
    timeRange: '30d',
    metrics: metrics ?? [{ name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table' }],
    ...rest,
  }
}

// TASK 2 — schema validation -----------------------------------------------------

test('detailView: valid spec on a rowLink table passes validateIntent', () => {
  const errs = validateIntent(baseIntent({ metrics: [{
    name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table',
    rowLink: { key: 'name' },
    detailView: { widgets: [
      { displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
      { displayAs: 'data-table', title: 'All', source: 'rows' },
    ] },
  }] }))
  assert.deepEqual(errs, [])
})

test('detailView: chart sub-widget missing xKey/yKey throws', () => {
  assert.throws(() => validateIntent(baseIntent({ metrics: [{
    name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table',
    rowLink: { key: 'name' },
    detailView: { widgets: [{ displayAs: 'donut-chart', title: 'By Hook', source: 'byHook' }] },
  }] })), /xKey|yKey/i)
})

test('detailView: bad displayAs throws', () => {
  assert.throws(() => validateIntent(baseIntent({ metrics: [{
    name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table',
    rowLink: { key: 'name' },
    detailView: { widgets: [{ displayAs: 'pie', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' }] },
  }] })), /displayAs/i)
})

test('detailView: requires rowLink.key or detail:true', () => {
  assert.throws(() => validateIntent(baseIntent({ metrics: [{
    name: 'agents', tier: 'T3', title: 'Agents', displayAs: 'data-table',
    detailView: { widgets: [{ displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' }] },
  }] })), /detailView requires/i)
})

// TASK 3 — compileDetailWidgets + keyed view -------------------------------------

test('compileDetailWidgets: emits primitive imports + JSX per sub-widget', () => {
  const { imports, jsx } = compileDetailWidgets({ widgets: [
    { displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
    { displayAs: 'ranked-table', title: 'Rules', source: 'byRule', columns: [{ key: 'name', label: 'Rule' }] },
    { displayAs: 'data-table', title: 'All', source: 'rows' },
  ]}, 'd')
  assert.ok([...imports].some(i => i.includes('Donut')), 'Donut import missing')
  assert.ok(jsx.includes('d["byHook"]') || jsx.includes('d.byHook'), 'byHook source not referenced')
  assert.ok(jsx.includes('RecordsTable'), 'table sub-widget not via RecordsTable')
})

test('detailView falls back to registry entry defaults (buildViewSpec)', () => {
  // A cataloged metric ships its detailView via registry defaults — the intent
  // metric need not restate it. Guards the fresh-build + view-spec fallback.
  const entry = { defaults: { detailView: { widgets: [
    { displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
  ] } } }
  const spec = buildViewSpec('AgentComplianceReport', { name: 'agent-compliance-report', title: 'Agent Compliance' }, entry, '30d')
  assert.ok(spec.detailView, 'detailView should fall back to entry.defaults.detailView')
  assert.equal(spec.detailView.widgets[0].source, 'byHook')
})

test('generateKeyedDetailViewFile: with detailView imports charts + references source map', () => {
  const view = generateKeyedDetailViewFile({
    componentName: 'AllAgents', title: 'Agents', subtitle: 'Spans',
    moduleSpecifier: '@/metrics/all-agents', detailColumns: null,
    detailView: { widgets: [
      { displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
    ] },
  })
  assert.ok(view.includes("@/dashboard/charts"), 'keyed detailView must import chart primitives')
  assert.ok(view.includes('d["byHook"]') || view.includes('d.byHook'), 'keyed detailView must reference source map')
  assert.ok(view.includes('fetchDetailByKey(sdk, key, getToken)'), 'keyed view must still call fetchDetailByKey')
})

test('generateKeyedDetailViewFile: without detailView still renders a single RecordsTable (backward-compat)', () => {
  const view = generateKeyedDetailViewFile({
    componentName: 'AllAgents', title: 'Agents', subtitle: 'Spans',
    moduleSpecifier: '@/metrics/all-agents', detailColumns: null,
  })
  assert.ok(view.includes('<RecordsTable'), 'no-detailView keyed view must render a single RecordsTable')
  assert.ok(!view.includes("@/dashboard/charts"), 'no-detailView keyed view must not import charts')
})

// TASK 4 — chart record-grain view (generateViewFile) ----------------------------

test('generateViewFile: with detailView imports charts + references source map', () => {
  const view = generateViewFile({
    componentName: 'Errors', title: 'Errors', subtitle: 'Last 30d',
    moduleSpecifier: '@/metrics/errors', detailExport: 'fetchDetail', detailColumns: null,
    detailView: { widgets: [
      { displayAs: 'bar-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
    ] },
  })
  assert.ok(view.includes("@/dashboard/charts"), 'detailView view must import chart primitives')
  assert.ok(view.includes('d["byHook"]') || view.includes('d.byHook'), 'detailView view must reference source map')
})

test('generateViewFile: without detailView still renders a single RecordsTable (backward-compat)', () => {
  const view = generateViewFile({
    componentName: 'Errors', title: 'Errors', subtitle: 'Last 30d',
    moduleSpecifier: '@/metrics/errors', detailExport: 'fetchData', detailColumns: null,
  })
  assert.ok(view.includes('<RecordsTable'), 'no-detailView view must render a single RecordsTable')
  assert.ok(!view.includes("@/dashboard/charts"), 'no-detailView view must not import charts')
})

// ── Issue 1: rowLink falls back to registry defaults ──────────────────────────

test('rowLink: a cataloged table whose rowLink lives in registry defaults renders clickable', () => {
  const content = buildWidgetFile(
    { name: 'x', tier: 'T1', title: 'X', displayAs: 'data-table' },
    { template: 'data-table', defaults: { rowLink: { key: 'agentName' } } },
    '30d'
  )
  assert.ok(content.includes('onRowClick'), 'rowLink from registry defaults must wire onRowClick')
  assert.ok(content.includes("const ROW_LINK_KEY = 'agentName'"), 'ROW_LINK_KEY must come from registry defaults.rowLink.key')
})

// ── Issue 2: per-metric explanatory empty states (emptyMessage) ────────────────
// These exercise the <<EMPTY_MESSAGE>> / <EMPTY_MESSAGE> placeholders added to the
// widget templates. The placeholders live in the apps-dev-tools sibling source
// (the orchestrator rebuilds the fixture zip from it during the self-test build);
// run against that source when present so the assertions track the edited templates.
const SIBLING_WIDGETS = resolve(__dirname, '../../../../../../apps-dev-tools/uipath-dashboard-starter-kit/widgets')
function withSiblingTemplates(fn) {
  if (!existsSync(SIBLING_WIDGETS)) return // sibling source unavailable — skip
  const prev = WIDGETS_DIR_FOR_TESTS
  setWidgetsDir(SIBLING_WIDGETS)
  try { fn() } finally { if (prev) setWidgetsDir(prev) }
}

test('emptyMessage: table metric emits the per-metric empty message (not bare "No data")', () => {
  withSiblingTemplates(() => {
    const content = buildWidgetFile(
      { name: 'gov', tier: 'T3', title: 'Violations', displayAs: 'data-table', emptyMessage: 'Rules are passing' },
      null, '30d'
    )
    assert.ok(content.includes('Rules are passing'), 'table empty message not substituted')
    assert.ok(!content.includes('message="No data"'), 'bare "No data" must be replaced')
  })
})

test('emptyMessage: chart metric emits the per-metric empty message', () => {
  withSiblingTemplates(() => {
    const content = buildWidgetFile(
      { name: 'gov-trend', tier: 'T3', title: 'Violations Trend', displayAs: 'area-chart', xKey: 'date', yKey: 'value', emptyMessage: 'Rules are passing' },
      null, '30d'
    )
    assert.ok(content.includes('Rules are passing'), 'chart empty message not substituted')
  })
})

test('emptyMessage: falls back to registry defaults.emptyMessage', () => {
  withSiblingTemplates(() => {
    const content = buildWidgetFile(
      { name: 'x', tier: 'T1', title: 'X', displayAs: 'data-table' },
      { template: 'data-table', defaults: { emptyMessage: 'Nothing to report' } },
      '30d'
    )
    assert.ok(content.includes('Nothing to report'), 'emptyMessage must fall back to registry defaults')
  })
})

// ── Record-grain detail views: noDetail opt-out, KPI drill-down, contract ──────

test('widgetGetsDetailView: chart gets a view; noDetail chart does not', () => {
  assert.equal(widgetGetsDetailView('area-chart', { name: 'm' }, null), true, 'plain chart drills down')
  assert.equal(widgetGetsDetailView('donut-chart', { name: 'm' }, { noDetail: true }), false, 'noDetail chart does not')
})

test('widgetGetsDetailView: kpi-card drills down on metric or registry-default detail', () => {
  assert.equal(widgetGetsDetailView('kpi-card', { name: 'm' }, null), false, 'plain KPI links nowhere')
  assert.equal(widgetGetsDetailView('kpi-card', { name: 'm', detail: true }, null), true, 'metric detail:true drills down')
  // Cataloged KPI defaults the drill-down on via the registry entry.
  assert.equal(widgetGetsDetailView('kpi-card', { name: 'm' }, { defaults: { detail: true } }), true, 'registry defaults.detail drills down')
  // Metric override wins — suppress a defaulted-on KPI.
  assert.equal(widgetGetsDetailView('kpi-card', { name: 'm', detail: false }, { defaults: { detail: true } }), false, 'metric detail:false suppresses')
})

test('registry contract: every default-on KPI ships a detailRecipe + detailColumns', () => {
  for (const [name, entry] of Object.entries(registry.t1)) {
    if (entry.template !== 'kpi-card' || entry.defaults?.detail !== true) continue
    assert.ok(entry.detailRecipe, `${name}: default-drill-down KPI needs a detailRecipe`)
    assert.ok(entry.defaults?.detailColumns, `${name}: default-drill-down KPI needs defaults.detailColumns`)
  }
})

test('buildWidgetFile: cataloged default-on KPI renders a clickable card', () => {
  withSiblingTemplates(() => {
    const content = buildWidgetFile(
      { name: 'active-agents-kpi', tier: 'T1', title: 'Active Agents', displayAs: 'kpi-card' },
      registry.t1['active-agents-kpi'], '30d'
    )
    assert.ok(content.includes("const KPI_DETAIL_ROUTE = '/activeagentskpi'"), 'registry default-on KPI must get a detail route')
    assert.ok(content.includes('KPI_DETAIL_ROUTE ? () => navigate(KPI_DETAIL_ROUTE)'), 'KPI card must be clickable')
  })
})

test('widgetGetsDetailView: tables never get a chart-style view', () => {
  assert.equal(widgetGetsDetailView('data-table', { name: 'm' }, null), false)
  assert.equal(widgetGetsDetailView('ranked-table', { name: 'm' }, null), false)
})

test('widgetGetsDetailView: T3 chart opts out via metric-level noDetail (no registry entry)', () => {
  // A T3 custom chart on an aggregate-only endpoint sets "noDetail": true in
  // intent.json — there is no registry entry to carry the flag.
  assert.equal(widgetGetsDetailView('area-chart', { name: 'm', tier: 'T3', noDetail: true }, null), false)
  // Without the flag, a T3 chart still requires a drill-down (fetchDetail enforced).
  assert.equal(widgetGetsDetailView('area-chart', { name: 'm', tier: 'T3' }, null), true)
})

test('registry contract: every T1 chart is either noDetail or has detailRecipe + detailColumns', () => {
  const CHARTS = new Set(['area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart'])
  for (const [name, entry] of Object.entries(registry.t1)) {
    if (!CHARTS.has(entry.template)) continue
    if (entry.noDetail === true) {
      assert.ok(!entry.detailRecipe, `${name}: noDetail chart must not also carry a detailRecipe`)
      continue
    }
    assert.ok(entry.detailRecipe, `${name}: detail-capable chart needs a detailRecipe`)
    assert.ok(entry.defaults?.detailColumns, `${name}: detail-capable chart needs defaults.detailColumns`)
  }
})

test('buildWidgetFile: noDetail chart renders a non-clickable card (empty detailRoute, no ViewAllLink)', () => {
  withSiblingTemplates(() => {
    const content = buildWidgetFile(
      { name: 'agent-memory-timeline', tier: 'T1', title: 'Agent Memory', displayAs: 'area-chart', xKey: 'timeSlice', yKey: 'totalCount' },
      registry.t1['agent-memory-timeline'], '30d'
    )
    assert.ok(content.includes("const detailRoute = ''"), 'noDetail chart must have an empty detailRoute')
    // The ViewAllLink + card click are runtime-guarded on detailRoute, so an empty
    // route renders them inert (no navigation, no cursor-pointer) without a separate template.
    assert.ok(content.includes('detailRoute ? <ViewAllLink'), 'ViewAllLink must be guarded on detailRoute')
    assert.ok(content.includes('detailRoute ? () => navigate(detailRoute)'), 'card click must be guarded on detailRoute')
  })
})

test('buildWidgetFile: detail-capable chart renders a clickable card with a route', () => {
  withSiblingTemplates(() => {
    const content = buildWidgetFile(
      { name: 'agent-error-timeline', tier: 'T1', title: 'Agent Errors', displayAs: 'area-chart', xKey: 'date', yKey: 'value' },
      registry.t1['agent-error-timeline'], '30d'
    )
    assert.ok(content.includes("const detailRoute = '/agenterrortimeline'") ||
              content.includes("const detailRoute = '/agenterrors'"), 'capable chart must have a non-empty detailRoute')
    assert.ok(content.includes('detailRoute ? () => navigate(detailRoute)'), 'card click must be guarded on detailRoute')
  })
})

test('buildWidgetFile: kpi-card with detail:true is clickable; plain KPI is not', () => {
  withSiblingTemplates(() => {
    const withDetail = buildWidgetFile(
      { name: 'failure-rate', tier: 'T3', title: 'Failure Rate', displayAs: 'kpi-card', valueField: 'value', detail: true },
      null, '30d'
    )
    assert.ok(withDetail.includes("const KPI_DETAIL_ROUTE = '/failurerate'"), 'KPI detail route must be set')
    assert.ok(withDetail.includes('KPI_DETAIL_ROUTE ? () => navigate(KPI_DETAIL_ROUTE)'), 'KPI card must be clickable')

    const plain = buildWidgetFile(
      { name: 'active-agents', tier: 'T3', title: 'Active Agents', displayAs: 'kpi-card', valueField: 'value' },
      null, '30d'
    )
    assert.ok(plain.includes("const KPI_DETAIL_ROUTE = ''"), 'plain KPI must have an empty detail route')
  })
})

test('buildViewSpec: detailColumns + detailSortKey fall back to registry defaults; export is fetchDetail', () => {
  const entry = registry.t1['violations-by-standard']
  const spec = buildViewSpec('ViolationsByStandard', { name: 'violations-by-standard', title: 'Violations by Standard' }, entry, '30d')
  assert.equal(spec.detailExport, 'fetchDetail', 'detail view runs the record-grain fetchDetail export')
  assert.ok(spec.detailColumns, 'detailColumns must come from registry defaults when intent omits them')
  assert.ok(spec.detailColumns.includes('agentName'), 'compiled detailColumns should carry the registry keys')
})
