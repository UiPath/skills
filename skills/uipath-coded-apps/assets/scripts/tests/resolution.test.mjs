import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { validateIntent, resolveMetric, buildWidgetFile, generateViewFile, buildViewSpec, compileColumns, emit, parseEvent, classifyEditIntent, resolveChangeMetric, widgetLayoutGroup, VALID_DISPLAY_TYPES, metricModuleSpecifier, buildVersions, SCAFFOLD_VERSION, INTENT_SCHEMA_VERSION, STATE_SCHEMA_VERSION, scaffoldDrift } from '../build-dashboard.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REGISTRY_PATH = resolve(__dirname, '../capability-registry.json')

const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'))

// ── Phase 2: version stamps ───────────────────────────────────────────────────
test('buildVersions stamps skill/scaffold/intentSchema/sdk', () => {
  const v = buildVersions('1.4.0')
  assert.equal(v.scaffold, SCAFFOLD_VERSION)
  assert.equal(v.intentSchema, INTENT_SCHEMA_VERSION)
  assert.equal(v.sdk, '1.4.0')
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

// ── SDK 1.4.0: agent / memory / governance metrics ────────────────────────────

test('1.4.0: previously-refused agent metrics now resolve as T1', () => {
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

test('1.4.0: timeline metrics the SDK lacks are still hard-refused', () => {
  for (const text of ['invocation volume over time', 'consumption timeline', 'agent latency p95', 'agent error rate trend']) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(refused, `"${text}" should be hard-refused (no SDK 1.4.0 endpoint)`)
    assert.equal(resolveAlias(text)?.key?.startsWith('agent-memory') ?? false, false)
  }
})

test('1.4.0: t1_unavailable section is gone (stale PR #438 entries removed)', () => {
  assert.equal(registry.t1_unavailable, undefined)
})

test('1.4.0: agent-health shell build compiles formatted/colored columnDefs', () => {
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

test('1.4.0: governance-verdicts donut uses name/value keys from defaults', () => {
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
