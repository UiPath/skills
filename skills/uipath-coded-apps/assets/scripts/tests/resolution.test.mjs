import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { validateIntent, resolveMetric, buildT1WidgetSpec, buildT2WidgetSpec, compileT2ToTypeScript, buildT3WidgetFile, emit, parseEvent, classifyEditIntent } from '../build-dashboard.mjs'

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
  const result = resolveT1('agent-errors')
  assert.ok(result)
  assert.equal(result.tier, 'T1')
  assert.equal(result.entry.template, 'line-chart')
})

test('T1 exact name lookup returns null for unknown metric', () => {
  const result = resolveT1('completely-unknown-metric')
  assert.equal(result, null)
})

test('alias lookup finds agent-errors by natural language', () => {
  const result = resolveAlias('show me agent failures over time')
  assert.ok(result)
  assert.equal(result.tier, 'T1')
  assert.equal(result.key, 'agent-errors')
})

test('alias lookup finds T2 queue-failure-threshold', () => {
  const result = resolveAlias('queues where failure rate is high')
  assert.ok(result)
  assert.equal(result.tier, 'T2')
  assert.equal(result.key, 'queue-failure-threshold')
})

test('alias lookup returns null for unknown text', () => {
  const result = resolveAlias('completely unrelated nonsense xyz')
  assert.equal(result, null)
})

test('all T1 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t1)) {
    assert.ok(entry.template, `${key} missing template`)
    assert.ok(entry.namespace, `${key} missing namespace`)
    assert.ok(entry.method, `${key} missing method`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
    assert.ok(entry.defaults?.title, `${key} missing defaults.title`)
  }
})

test('all T2 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t2)) {
    assert.ok(entry.service, `${key} missing service`)
    assert.ok(entry.sdkImport, `${key} missing sdkImport`)
    assert.ok(entry.sdkService, `${key} missing sdkService`)
    assert.ok(entry.method, `${key} missing method`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
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
    metrics: [{ name: 'agent-errors', tier: 'T1' }]
  })
  assert.deepEqual(errors, [])
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

// ── resolveMetric + buildT1WidgetSpec tests ───────────────────────────────────

test('resolveMetric: T1 known name returns entry with template', () => {
  const result = resolveMetric({ name: 'agent-errors', tier: 'T1' })
  assert.equal(result.tier, 'T1')
  assert.equal(result.entry.template, 'line-chart')
})

test('resolveMetric: T2 known name returns entry with service', () => {
  const result = resolveMetric({ name: 'queue-failure-threshold', tier: 'T2', params: { threshold: 20, direction: 'gt' } })
  assert.equal(result.tier, 'T2')
  assert.ok(result.entry.service)
})

test('resolveMetric: T3 always resolves with null entry', () => {
  const result = resolveMetric({ name: 'custom-thing', tier: 'T3', fnBody: 'return []', displayAs: 'kpi-card', title: 'X' })
  assert.equal(result.tier, 'T3')
  assert.equal(result.entry, null)
})

test('resolveMetric: unknown T1 name throws with "not found in registry"', () => {
  assert.throws(() => resolveMetric({ name: 'nonexistent-metric', tier: 'T1' }), /not found in registry/)
})

test('buildT1WidgetSpec: merges registry defaults with intent overrides', () => {
  const spec = buildT1WidgetSpec(
    { name: 'agent-errors', tier: 'T1', title: 'My Error Chart' },
    registry.t1['agent-errors'],
    '30d'
  )
  assert.equal(spec.componentName, 'AgentErrors')
  assert.equal(spec.template, 'line-chart')
  assert.equal(spec.title, 'My Error Chart')
  assert.equal(spec.icon, 'AlertTriangle')
  assert.ok(spec.dataHook.includes('agents.getErrors'))
  assert.ok(spec.dataHook.includes('THIRTY_DAYS_AGO'))
})

test('buildT1WidgetSpec: uses 7d time range constant', () => {
  const spec = buildT1WidgetSpec({ name: 'agent-errors', tier: 'T1' }, registry.t1['agent-errors'], '7d')
  assert.ok(spec.dataHook.includes('SEVEN_DAYS_AGO'))
})

// ── buildT2WidgetSpec + compileT2ToTypeScript tests ───────────────────────────

test('buildT2WidgetSpec: returns correct spec for queue-failure-threshold', () => {
  const metric = { name: 'queue-failure-threshold', tier: 'T2', params: { threshold: 20, direction: 'gt' } }
  const spec = buildT2WidgetSpec(metric, registry.t2['queue-failure-threshold'])
  assert.equal(spec.componentName, 'QueueFailureThreshold')
  assert.equal(spec.template, 'ranked-table')
  assert.ok(spec.sdkHookCode)
  assert.ok(spec.sdkImport)
})

test('compileT2ToTypeScript: generates valid async function for gt filter', () => {
  const code = compileT2ToTypeScript({
    service: 'queues', sdkImport: '@uipath/uipath-typescript/queues', sdkService: 'Queues',
    method: 'getAll', filterField: 'failureCount', filterOp: 'gt', filterValue: 20,
    sortField: 'failureCount', sortDir: 'desc'
  })
  assert.ok(code.includes('Queues'))
  assert.ok(code.includes('getAll'))
  assert.ok(code.includes('failureCount'))
  assert.ok(code.startsWith('async (sdk'))
})

test('compileT2ToTypeScript: throws for invalid op', () => {
  assert.throws(() => compileT2ToTypeScript({
    service: 'queues', sdkImport: 'x', sdkService: 'Queues',
    method: 'getAll', filterField: 'x', filterOp: 'INVALID', filterValue: 1,
    sortField: 'x', sortDir: 'desc'
  }), /invalid op/)
})

// ── buildT3WidgetFile tests ───────────────────────────────────────────────────

test('buildT3WidgetFile: injects fnBody into shell template', () => {
  const content = buildT3WidgetFile({
    name: 'faulted-queues', tier: 'T3', title: 'Faulted Queues', description: 'Queues with faults',
    displayAs: 'ranked-table', fnBody: "const r = await sdk.queues.getAll({})\nreturn r.items ?? []"
  })
  assert.ok(content.includes('FaultedQueues'), 'component name not injected')
  assert.ok(content.includes('Faulted Queues'), 'title not injected')
  assert.ok(content.includes('sdk.queues.getAll'), 'fnBody not injected')
  assert.ok(!content.includes('<<FN_BODY>>'), 'FN_BODY placeholder not replaced')
  assert.ok(!content.includes('<<COMPONENT_NAME>>'), 'COMPONENT_NAME placeholder not replaced')
})

test('buildT3WidgetFile: throws if fnBody is missing', () => {
  assert.throws(
    () => buildT3WidgetFile({ name: 'x', tier: 'T3', title: 'X', displayAs: 'kpi-card' }),
    /fnBody/
  )
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

test('classifyEditIntent: identifies ADD', () => {
  const result = classifyEditIntent({ op: 'ADD', projectDir: '/tmp/x', metric: { name: 'agent-errors', tier: 'T1' } })
  assert.equal(result.op, 'ADD')
})

test('classifyEditIntent: identifies REMOVE', () => {
  const result = classifyEditIntent({ op: 'REMOVE', projectDir: '/tmp/x', target: 'ErrorRateTrend' })
  assert.equal(result.op, 'REMOVE')
  assert.equal(result.target, 'ErrorRateTrend')
})

test('classifyEditIntent: throws on invalid op', () => {
  assert.throws(() => classifyEditIntent({ op: 'DELETE', projectDir: '/tmp/x' }), /invalid op/)
})

test('parseEvent: recognizes AUTH_MISSING event', () => {
  const result = parseEvent('AUTH_MISSING:{"var":"clientId","message":"No client ID"}')
  assert.equal(result.type, 'AUTH_MISSING')
  assert.equal(result.payload.var, 'clientId')
})
