import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { validateIntent, resolveMetric, buildWidgetFile, generateViewFile, compileColumns, emit, parseEvent, classifyEditIntent, resolveChangeMetric, widgetLayoutGroup, VALID_DISPLAY_TYPES } from '../build-dashboard.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REGISTRY_PATH = resolve(__dirname, '../capability-registry.json')

const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'))

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
    dashboardName: 'My Dashboard',
    timeRange: '30d',
    metrics: [{ name: 'agent-memory-timeline', tier: 'T1', title: 'Agent Memory', fnBody: 'return []' }]
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: rejects T1 metric without fnBody', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'agent-memory-timeline', tier: 'T1', title: 'Agent Memory' }]
  })
  assert.ok(errors.some(e => e.includes('T1') && e.includes('fnBody')))
})

test('validateIntent: rejects T1 metric without title', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'agent-memory-timeline', tier: 'T1', fnBody: 'return []' }]
  })
  assert.ok(errors.some(e => e.includes('T1') && e.includes('title')))
})

test('validateIntent: rejects T2 metric without fnBody', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'jobs-by-state', tier: 'T2', title: 'Jobs', params: { value: 'Faulted' } }]
  })
  assert.ok(errors.some(e => e.includes('T2') && e.includes('fnBody')))
})

test('validateIntent: rejects missing dashboardName', () => {
  const errors = validateIntent({ timeRange: '30d', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('dashboardName')))
})

test('validateIntent: rejects invalid timeRange', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '2w', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('timeRange')))
})

test('validateIntent: rejects T2 metric without params', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '7d', metrics: [{ name: 'queue-failure-threshold', tier: 'T2' }] })
  assert.ok(errors.some(e => e.includes('T2') && e.includes('params')))
})

test('validateIntent: rejects T3 metric without fnBody', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '7d', metrics: [{ name: 'custom', tier: 'T3', displayAs: 'ranked-table', title: 'Custom' }] })
  assert.ok(errors.some(e => e.includes('T3') && e.includes('fnBody')))
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

test('buildWidgetFile: T1 metric uses fnBody from agent (not hardcoded SDK)', () => {
  const entry = registry.t1['memory-calls-trend']
  const content = buildWidgetFile(
    {
      name: 'memory-calls-trend',
      tier: 'T1',
      title: 'Memory Calls',
      displayAs: 'area-chart',
      xKey: 'timeSlice',
      yKey: 'memoryCallsCount',
      fnBody: "const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')\nreturn await new AgentMemory(sdk as never).getCallsTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })"
    },
    entry,
    '30d'
  )
  assert.ok(content.includes('customDataFn'))
  assert.ok(content.includes('getCallsTimeline'))
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

test('buildWidgetFile: T2 metric with fnBody uses chart path', () => {
  const entry = registry.t2['jobs-duration-threshold']
  const content = buildWidgetFile(
    {
      name: 'jobs-duration-threshold',
      tier: 'T2',
      title: 'Long Running Jobs',
      displayAs: 'bar-chart',
      xKey: 'name',
      yKey: 'duration',
      fnBody: "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nconst svc = new Jobs(sdk as never)\nconst result = await svc.getAll({ filter: \"State eq 'Running'\" })\nreturn result?.items ?? []"
    },
    entry,
    '30d'
  )
  assert.ok(content.includes('customDataFn'))
  assert.ok(content.includes('Jobs'))
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

test('buildWidgetFile: throws if fnBody is missing', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', title: 'X', displayAs: 'kpi-card' }, null),
    /missing fnBody/
  )
})

test('buildWidgetFile: throws if displayAs cannot be determined', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', title: 'X', fnBody: 'return []' }, null),
    /needs displayAs/
  )
})

test('buildWidgetFile: injects fnBody into shell template for ranked-table', () => {
  const content = buildWidgetFile({
    name: 'faulted-queues', tier: 'T3', title: 'Faulted Queues', description: 'Queues with faults',
    displayAs: 'ranked-table', fnBody: "const r = await sdk.queues.getAll({})\nreturn r.items ?? []"
  }, null, '30d')
  assert.ok(content.includes('FaultedQueues'), 'component name not injected')
  assert.ok(content.includes('Faulted Queues'), 'title not injected')
  assert.ok(content.includes('sdk.queues.getAll'), 'fnBody not injected')
  assert.ok(!content.includes('<<FN_BODY>>'), 'FN_BODY placeholder not replaced')
  assert.ok(!content.includes('<<COMPONENT_NAME>>'), 'COMPONENT_NAME placeholder not replaced')
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
      dashboardName: 'x', timeRange: '7d',
      metrics: [{ name: 'custom', tier: 'T3', title: 'X', fnBody: 'return []', displayAs: chartType }]
    })
    assert.deepEqual(errors, [], `${chartType} should be valid for T3-SDK`)
  }
})

test('validateIntent: rejects T3-SDK with truly unsupported displayAs', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', title: 'X', fnBody: 'return []', displayAs: 'unknown-widget' }]
  })
  assert.ok(errors.some(e => e.includes('unsupported displayAs')))
})

test('validateIntent: accepts T3-SDK with ranked-table displayAs', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', title: 'X', fnBody: 'return []', displayAs: 'ranked-table' }]
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
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', fnBody: 'return []', headlineMode: 'median' }],
  })
  assert.ok(errors.some(e => e.includes('headlineMode')))
})

test('validateIntent: rejects invalid deltaPolarity', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', fnBody: 'return []', deltaPolarity: 'sideways' }],
  })
  assert.ok(errors.some(e => e.includes('deltaPolarity')))
})

test('validateIntent: rate-chart requires rateNum + rateDen', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'rate-chart', fnBody: 'return []' }],
  })
  assert.ok(errors.some(e => e.includes('rateNum')))
})

test('validateIntent: accepts valid presentation hints', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', fnBody: 'return []', headlineMode: 'avg', deltaPolarity: 'up-bad' }],
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: rejects detailColumns entry with bad format', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', fnBody: 'return []', detailColumns: [{ key: 'd', label: 'D', format: 'bogus' }] }],
  })
  assert.ok(errors.some(e => e.includes('invalid format')))
})

test('buildWidgetFile: every chart type generates with no leftover placeholders', () => {
  for (const displayAs of ['line-chart', 'area-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart']) {
    const metric = {
      name: 'm', tier: 'T3', title: 'M', displayAs,
      xKey: 'date', yKey: 'value', rateNum: 'num', rateDen: 'den', fnBody: 'return []',
    }
    const content = buildWidgetFile(metric, null, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${displayAs} has leftover placeholders`)
    assert.ok(content.includes('customDataFn'), `${displayAs} missing customDataFn`)
  }
})

test('generateViewFile: uses record-grain detailFnBody + compiled detailColumns', () => {
  const view = generateViewFile({
    componentName: 'FaultedJobs',
    title: 'Faulted Jobs',
    subtitle: 'Last 30 days',
    detailFnBody: "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nreturn (await new Jobs(sdk as never).getAll({ filter: \"State eq 'Faulted'\" }))?.items ?? []",
    detailColumns: compileColumns([
      { key: 'processName', label: 'Process' },
      { key: 'startTime', label: 'Started', format: 'timeAgo' },
    ]),
    defaultSortKey: 'startTime',
  })
  assert.ok(view.includes('FaultedJobsView'))
  assert.ok(view.includes('getAll'), 'record-grain fnBody not embedded')
  assert.ok(view.includes('fmtTimeAgo(String(v))'), 'formatted column not embedded')
  assert.ok(view.includes('defaultSortKey={"startTime"}'), 'explicit sort key not used')
  assert.ok(!view.includes('autoColumns(rows)') || view.includes('function autoColumns'), 'autoColumns only as fallback definition')
})

test('generateViewFile: falls back to autoColumns when no detailColumns', () => {
  const view = generateViewFile({
    componentName: 'Trend', title: 'Trend', subtitle: '',
    detailFnBody: 'return []', detailColumns: null,
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

test('harness: chart customDataFn signature accepts SDK-typed arrays (Promise<any[]>)', () => {
  const content = buildWidgetFile(
    { name: 'm', tier: 'T3', title: 'M', displayAs: 'line-chart', yKey: 'v', fnBody: 'return []' },
    null, '7d'
  )
  assert.ok(content.includes('Promise<any[]>'), 'chart wrapper must be Promise<any[]>')
  assert.ok(!content.includes('Promise<Record<string, unknown>[]>'), 'old index-signature-demanding wrapper must be gone')
})

test('harness: shell customDataFn signature accepts SDK-typed arrays', () => {
  const content = buildWidgetFile(
    { name: 'm', tier: 'T3', title: 'M', displayAs: 'data-table', fnBody: 'return []' },
    null, '7d'
  )
  assert.ok(content.includes('customDataFn = async (sdk: any, getToken: () => Promise<string>): Promise<any[]>'))
})

test('harness: detail view customDataFn signature accepts SDK-typed arrays', () => {
  const view = generateViewFile({
    componentName: 'X', title: 'X', subtitle: '',
    detailFnBody: 'return []', detailColumns: null,
  })
  assert.ok(view.includes('Promise<any[]>'))
  assert.ok(!view.includes('Promise<Row[]>'))
})

// ── Incremental edit: change-merge + layout grouping ──────────────────────────

test('resolveChangeMetric: timeRange-only delta keeps persisted fnBody/title', () => {
  const stored = {
    tier: 'T1', metric: 'memory-calls-trend', template: 'area-chart',
    intentMetric: { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', fnBody: 'return await x()' },
  }
  const merged = resolveChangeMetric(stored, 'MemoryCallsTrend', { timeRange: '7d' })
  assert.equal(merged.fnBody, 'return await x()')
  assert.equal(merged.title, 'Memory Calls')
  assert.equal(merged.timeRange, '7d')
})

test('resolveChangeMetric: delta fields override persisted intentMetric', () => {
  const stored = { intentMetric: { name: 'm', tier: 'T3', title: 'Old', displayAs: 'area-chart', fnBody: 'old' } }
  const merged = resolveChangeMetric(stored, 'M', { fnBody: 'new', displayAs: 'data-table' })
  assert.equal(merged.fnBody, 'new')
  assert.equal(merged.displayAs, 'data-table')
  assert.equal(merged.title, 'Old')
})

test('resolveChangeMetric: legacy state without intentMetric yields no fnBody', () => {
  const merged = resolveChangeMetric({ tier: 'T1', metric: 'job-failures' }, 'JobFailures', { timeRange: '7d' })
  assert.equal(merged.fnBody, undefined)
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
