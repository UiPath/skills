// End-to-end tests for the three use-case flows (fresh build, incremental edit, upgrade).
// They run build-dashboard.mjs as a child process against a real starter-kit scaffold
// extracted from the committed fixture archive. `npm`/`npx` are fakes
// (see support/coded-apps-dashboards-fake-tools.mjs), so the Stage-A metric check and the
// full-app `tsc` are steered by environment variables instead of installing the real toolchain.

import { test, before } from 'node:test'
import assert from 'node:assert/strict'
import {
  mkdtempSync, writeFileSync, readFileSync, mkdirSync, existsSync, cpSync, rmSync,
} from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import { spawnSync, execFileSync } from 'node:child_process'
import { installFakeTools, fakeEnv, readFakeLog } from './support/coded-apps-dashboards-fake-tools.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SCRIPT = resolve(__dirname, '../../skills/uipath-coded-apps/assets/scripts/dashboards/build-dashboard.mjs')
const ARCHIVE = resolve(__dirname, '../../skills/uipath-coded-apps/assets/fixtures/governance-dashboard-starter-kit.tar.gz')
const TAR = process.platform === 'win32'
  ? join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe')
  : 'tar'

let fakeDir
let kitDir // pristine extracted scaffold, copied for every test
before(() => {
  fakeDir = installFakeTools()
  kitDir = mkdtempSync(join(tmpdir(), 'flows-kit-'))
  execFileSync(TAR, ['-xzf', ARCHIVE, '-C', kitDir], { stdio: 'pipe' })
})

const FETCH_DATA = 'export const fetchData = async () => []\n'
const FETCH_DETAIL = 'export const fetchDetail = async () => []\n'
const FETCH_KEYED = 'export const fetchDetailByKey = async (k: string) => [k]\n'

const ORDERS = { name: 'orders-table', tier: 'T3', title: 'Orders', displayAs: 'ranked-table', rowLink: { key: 'id' } }
const TREND = { name: 'sales-trend', tier: 'T3', title: 'Sales trend', displayAs: 'bar-chart' }
const OPEN = { name: 'open-count', tier: 'T3', title: 'Open', displayAs: 'kpi-card' }
const MODULES = {
  'orders-table': FETCH_DATA + FETCH_KEYED,
  'sales-trend': FETCH_DATA + FETCH_DETAIL,
  'open-count': FETCH_DATA,
}

/** Write <dir>/metrics/<name>.ts for each name → source. */
function writeModules(dir, modules) {
  mkdirSync(join(dir, 'metrics'), { recursive: true })
  for (const [name, src] of Object.entries(modules)) writeFileSync(join(dir, 'metrics', `${name}.ts`), src)
}

/** A fresh copy of the scaffold plus a work dir for intents + metric modules. */
function newWorkspace({ nodeModules = true, sdk = '1.5.1', scaffold = true } = {}) {
  const base = mkdtempSync(join(tmpdir(), 'flows-'))
  const project = join(base, 'proj')
  if (scaffold) cpSync(kitDir, project, { recursive: true })
  else mkdirSync(project, { recursive: true })
  if (nodeModules) {
    mkdirSync(join(project, 'node_modules', '@uipath', 'uipath-typescript'), { recursive: true })
    writeFileSync(join(project, 'node_modules', '.package-lock.json'), '{}')
    writeFileSync(join(project, 'node_modules', '@uipath', 'uipath-typescript', 'package.json'), JSON.stringify({ version: sdk }))
  }
  const work = join(base, 'work')
  mkdirSync(work)
  return { base, project, work, log: join(base, 'calls.log') }
}

function intentFor(ws, over = {}) {
  return {
    schemaVersion: 2,
    dashboardName: 'Ops Dashboard',
    dashboardDescription: 'desc',
    timeRange: '7d',
    projectDir: ws.project,
    routingName: 'ops-dashboard-ab12',
    orgName: 'acme', tenantName: 'prod',
    cloudUrl: 'https://alpha.uipath.com', apiUrl: 'https://alpha.uipath.com/acme/prod',
    clientId: 'client-1',
    metrics: [ORDERS, TREND, OPEN],
    ...over,
  }
}

/** Run build-dashboard.mjs on a plan object (written to <work>/<file>); returns { r, events }. */
function runPlan(ws, plan, { file = 'intent.json', env = {} } = {}) {
  const planPath = join(ws.work, file)
  writeFileSync(planPath, JSON.stringify(plan, null, 2))
  const r = spawnSync(process.execPath, [SCRIPT, planPath], {
    cwd: ws.work, encoding: 'utf8', env: fakeEnv(fakeDir, { FAKE_LOG: ws.log, ...env }),
  })
  const events = r.stdout.split('\n').filter(l => /^[A-Z0-9_]+(:|$)/.test(l)).map(l => {
    const i = l.indexOf(':')
    return i === -1 ? { type: l, payload: null } : { type: l.slice(0, i), payload: JSON.parse(l.slice(i + 1)) }
  })
  return { r, events, types: events.map(e => e.type), planPath }
}

const readJson = p => JSON.parse(readFileSync(p, 'utf8'))
const stateOf = ws => readJson(join(ws.project, '.dashboard', 'state.json'))
const at = (ws, ...parts) => join(ws.project, ...parts)

/** A project that has gone through a successful fresh build of ORDERS + TREND + OPEN. */
function builtWorkspace(over = {}) {
  const ws = newWorkspace(over)
  writeModules(ws.work, MODULES)
  const { r } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 0, r.stderr + r.stdout)
  return ws
}

const editPlan = (ws, body) => ({ projectDir: ws.project, ...body })

// ═════════════════════════════════════════════════════════════════════════════
// Fresh build
// ═════════════════════════════════════════════════════════════════════════════

test('build: generates widgets, views, routes, config and a complete state.json', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const { r, events, types } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 0, r.stderr)

  assert.deepEqual(types.filter(t => t !== 'WIDGET_READY'), [
    'SCAFFOLD_READY', 'ENV_WRITTEN', 'PREWARM_DONE', 'METRICS_PASS', 'TSC_PASS', 'BUILD_RESULT',
  ])
  assert.deepEqual(events.filter(e => e.type === 'WIDGET_READY').map(e => e.payload),
    [{ name: 'OrdersTable', index: 1, total: 3 }, { name: 'SalesTrend', index: 2, total: 3 }, { name: 'OpenCount', index: 3, total: 3 }])
  const result = events.find(e => e.type === 'BUILD_RESULT').payload
  assert.equal(result.success, true)
  assert.deepEqual(result.widgets, ['OrdersTable', 'SalesTrend', 'OpenCount'])
  assert.equal(result.previewUrl, 'http://localhost:25173')

  for (const f of ['widgets/OrdersTable.tsx', 'widgets/SalesTrend.tsx', 'widgets/OpenCount.tsx',
    'views/SalesTrendView.tsx', 'views/OrdersTableDetailView.tsx', 'Dashboard.tsx', 'widgets/index.ts']) {
    assert.ok(existsSync(at(ws, 'src', 'dashboard', f)), f)
  }
  assert.ok(!existsSync(at(ws, 'src', 'dashboard', 'views', 'OpenCountView.tsx')), 'plain KPI has no detail view')
  for (const m of ['orders-table', 'sales-trend', 'open-count']) assert.ok(existsSync(at(ws, 'src', 'metrics', `${m}.ts`)), m)

  const app = readFileSync(at(ws, 'src', 'App.tsx'), 'utf8')
  assert.match(app, /import \{ SalesTrendView \} from '@\/dashboard\/views\/SalesTrendView'/)
  assert.match(app, /<Route path="\/salestrend" element=\{<SalesTrendView \/>\} \/>/)
  assert.match(app, /<Route path="\/orderstable\/:key" element=\{<OrdersTableDetailView \/>\} \/>/)

  const cfg = readJson(at(ws, 'uipath.json'))
  assert.equal(cfg.name, 'Ops Dashboard')
  assert.equal(cfg.clientId, 'client-1')
  assert.equal(cfg.orgName, 'acme')
  assert.equal(cfg.baseUrl, 'https://alpha.uipath.com/acme/prod')
  assert.equal(cfg.redirectUri, 'http://localhost:25173')

  const state = stateOf(ws)
  assert.equal(state.buildStatus, 'complete')
  assert.equal(state.regime, 'compiler-managed')
  assert.equal(state.env, 'alpha')
  assert.equal(state.app.semver, '1.0.0')
  assert.equal(state.timeRange, '7d')
  assert.deepEqual(Object.keys(state.widgets), ['OrdersTable', 'SalesTrend', 'OpenCount'])
  assert.equal(state.widgets.SalesTrend.template, 'bar-chart')
  assert.equal(state.widgets.OrdersTable.intentMetric.rowLink.key, 'id')
  assert.equal(state.versions.sdk, '1.5.1')
  assert.equal(state.versions.scaffold, readJson(at(ws, '_gen', 'starter-kit.json')).version)
  assert.ok(!existsSync(at(ws, '.build-in-progress')), 'sentinel removed after a clean build')
})

test('build: env is derived from the cloud URL (staging / prod) and a missing clientId raises AUTH_MISSING', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const { r, types } = runPlan(ws, intentFor(ws, { cloudUrl: 'https://staging.uipath.com', clientId: undefined }))
  assert.equal(r.status, 0, r.stderr)
  assert.ok(types.includes('AUTH_MISSING'))
  assert.match(r.stdout, /clientId is empty — local dashboard auth will not work/)
  assert.equal(stateOf(ws).env, 'staging')

  const ws2 = newWorkspace()
  writeModules(ws2.work, MODULES)
  assert.equal(runPlan(ws2, intentFor(ws2, { cloudUrl: 'https://cloud.uipath.com' })).r.status, 0)
  assert.equal(stateOf(ws2).env, 'prod')
})

test('build: a template build is tenant-neutral and starts in the ejected regime', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const { r, events, types } = runPlan(ws, intentFor(ws, { template: true, clientId: undefined }))
  assert.equal(r.status, 0, r.stderr)
  assert.ok(types.includes('TEMPLATE_BUILD'))
  assert.ok(!types.includes('AUTH_MISSING'), 'a template needs no client id')
  assert.equal(events.find(e => e.type === 'TEMPLATE_BUILD').payload.regime, 'ejected')
  const cfg = readJson(at(ws, 'uipath.json'))
  assert.equal(cfg.name, 'Ops Dashboard')
  assert.equal(cfg.redirectUri, 'http://localhost:25173')
  assert.equal(cfg.orgName, '') // the scaffold's neutral placeholders are untouched
  assert.equal(cfg.clientId, '')
  assert.equal(stateOf(ws).regime, 'ejected')
})

test('build: a rebuild keeps an ejected regime, the semver and the deployment record, and flags scaffold drift', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  mkdirSync(at(ws, '.dashboard'), { recursive: true })
  const deployment = { systemName: 'sys', folderKey: 'fk', appUrl: 'https://app', lastDeployedAt: '2026-01-01' }
  writeFileSync(at(ws, '.dashboard', 'state.json'), JSON.stringify({
    regime: 'ejected', versions: { scaffold: '0.0.1' }, app: { semver: '3.4.5' }, deployment, widgets: {},
  }))
  const { r, events } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 0, r.stderr)
  assert.deepEqual(events.find(e => e.type === 'UPGRADE_AVAILABLE').payload.from, '0.0.1')
  const state = stateOf(ws)
  assert.equal(state.regime, 'ejected')
  assert.equal(state.app.semver, '3.4.5')
  assert.deepEqual(state.deployment, deployment)
})

test('build: a leftover sentinel from an interrupted build is reported and then cleaned up', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  writeFileSync(at(ws, '.build-in-progress'), '1')
  const { r, types } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 0, r.stderr)
  assert.ok(types.includes('PARTIAL_BUILD_DETECTED'))
  assert.ok(!existsSync(at(ws, '.build-in-progress')))
})

test('build: a legacy dev-server pid file is cleaned up', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  mkdirSync(at(ws, '.dashboard'), { recursive: true })
  writeFileSync(at(ws, '.dashboard', 'server.pid'), '2147483646')
  const { r } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 0, r.stderr)
  assert.ok(!existsSync(at(ws, '.dashboard', 'server.pid')))
})

test('build: installs dependencies through npm when they are missing', () => {
  const ws = newWorkspace({ nodeModules: false })
  writeModules(ws.work, MODULES)
  const { r, types } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /⚙ Installing dependencies…/)
  assert.deepEqual(types.slice(types.indexOf('ENV_WRITTEN'), types.indexOf('METRICS_PASS')), ['ENV_WRITTEN', 'PREWARM_START', 'PREWARM_DONE'])
  assert.ok(readFakeLog(ws.log).some(l => l === 'npm ci --prefer-offline'))
})

test('build: refuses a plan without projectDir or routingName', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  let { r } = runPlan(ws, intentFor(ws, { projectDir: undefined }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /intent\.projectDir is required/)
  ;({ r } = runPlan(ws, intentFor(ws, { routingName: undefined })))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /intent\.routingName is required/)
})

test('build: a projectDir that does not exist is refused instead of being created', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const ghost = join(ws.base, 'not-there')
  const { r } = runPlan(ws, intentFor(ws, { projectDir: ghost }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /projectDir does not exist/)
  assert.ok(!existsSync(ghost))
})

test('build: an unextracted scaffold fails with the tar command to run', () => {
  const ws = newWorkspace({ scaffold: false })
  writeModules(ws.work, MODULES)
  const { r } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Starter kit not extracted into: /)
  assert.match(r.stderr, /tar --no-same-owner/)
})

test('build: an SDK older than the floor stops the build with a fix hint', () => {
  const ws = newWorkspace({ sdk: '1.0.0' })
  writeModules(ws.work, MODULES)
  const { r, types } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Installed @uipath\/uipath-typescript 1\.0\.0 is below the required 1\.5\.1/)
  assert.ok(!types.includes('METRICS_PASS'))
  assert.equal(stateOf(ws).buildStatus, 'in-progress', 'the partial state is left for deploy diagnostics')
})

test('build: a missing metric module names the file to write', () => {
  const ws = newWorkspace()
  writeModules(ws.work, { 'orders-table': MODULES['orders-table'] })
  const { r } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Metric module not found: .*sales-trend\.ts/)
})

test('build: Stage-A metric type errors exit 2 with METRICS_RETRY naming the files', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const { r, events } = runPlan(ws, intentFor(ws), { env: { FAKE_METRICS_FAIL: '1' } })
  assert.equal(r.status, 2)
  const retry = events.find(e => e.type === 'METRICS_RETRY').payload
  assert.deepEqual(retry.files, ['src/metrics/orders-table.ts'])
  assert.match(retry.errors[0], /error TS2322/)
  assert.match(r.stdout, /Metric modules have TypeScript errors/)
  assert.ok(!existsSync(at(ws, 'src', 'dashboard', 'widgets', 'OrdersTable.tsx')), 'nothing generated before Stage A passes')
})

test('build: a drill-down widget without fetchDetail exits 2 with CHART_DETAIL_MISSING', () => {
  const ws = newWorkspace()
  writeModules(ws.work, { ...MODULES, 'sales-trend': FETCH_DATA })
  const { r, events } = runPlan(ws, intentFor(ws))
  assert.equal(r.status, 2)
  const missing = events.find(e => e.type === 'CHART_DETAIL_MISSING').payload
  assert.deepEqual(missing.metrics.map(m => m.metric), ['sales-trend'])
  assert.match(r.stdout, /sales-trend \(metrics\/sales-trend\.ts\)/)
})

test('build: registry (T1) metrics resolve their template and show the registry detailRecipe when fetchDetail is missing', () => {
  const ws = newWorkspace()
  const t1 = { name: 'agent-error-timeline', tier: 'T1', title: 'Errors over time' }
  writeModules(ws.work, { 'agent-error-timeline': FETCH_DATA })
  const { r, events } = runPlan(ws, intentFor(ws, { metrics: [t1] }))
  assert.equal(r.status, 2)
  assert.equal(events.find(e => e.type === 'CHART_DETAIL_MISSING').payload.metrics[0].metric, 'agent-error-timeline')

  writeModules(ws.work, { 'agent-error-timeline': FETCH_DATA + FETCH_DETAIL })
  const ok = runPlan(ws, intentFor(ws, { metrics: [t1] }))
  assert.equal(ok.r.status, 0, ok.r.stderr)
  assert.equal(stateOf(ws).widgets.AgentErrorTimeline.tier, 'T1')
  assert.equal(stateOf(ws).widgets.AgentErrorTimeline.template, 'area-chart')
})

test('build: a widget that cannot be generated reports T3_FAILED and fails', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const bad = { name: 'open-count', tier: 'T3', title: 'Open', displayAs: 'kpi-card', valueField: '' }
  const { r, types } = runPlan(ws, intentFor(ws, { metrics: [bad] }))
  assert.equal(r.status, 1)
  assert.ok(types.includes('T3_FAILED'))
  assert.match(r.stderr, /Widget "open-count" could not be generated: kpi-card metric "open-count" has no valueField/)
})

test('build: a full-app tsc failure emits TSC_FAIL and exits 1 without completing state', () => {
  const ws = newWorkspace()
  writeModules(ws.work, MODULES)
  const { r, events } = runPlan(ws, intentFor(ws), { env: { FAKE_TSC_FAIL: '1' } })
  assert.equal(r.status, 1)
  assert.match(events.find(e => e.type === 'TSC_FAIL').payload.errors, /error TS2304: boom/)
  assert.match(r.stderr, /TypeScript errors:/)
  assert.equal(stateOf(ws).buildStatus, 'in-progress')
})

// ═════════════════════════════════════════════════════════════════════════════
// Incremental edit
// ═════════════════════════════════════════════════════════════════════════════

test('edit: refuses an edit without projectDir or on a project that was never built', () => {
  const ws = newWorkspace()
  let { r } = runPlan(ws, { op: 'REBUILD' }, { file: 'edit-intent.json' })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /edit-intent\.projectDir is required/)
  ;({ r } = runPlan(ws, editPlan(ws, { op: 'REBUILD' }), { file: 'edit-intent.json' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /No \.dashboard\/state\.json found\. Run a fresh build first\./)
})

test('edit: EJECT flips the regime and then the structured edit-script refuses the project', () => {
  const ws = builtWorkspace()
  const eject = runPlan(ws, editPlan(ws, { op: 'EJECT' }), { file: 'edit-intent.json' })
  assert.equal(eject.r.status, 0, eject.r.stderr)
  assert.deepEqual(eject.types, ['EJECTED'])
  assert.equal(stateOf(ws).regime, 'ejected')

  const again = runPlan(ws, editPlan(ws, { op: 'REBUILD' }), { file: 'edit-intent.json' })
  assert.equal(again.r.status, 1)
  assert.deepEqual(again.types, ['EJECTED_PROJECT'])
  assert.match(again.r.stderr, /This dashboard is ejected/)
})

test('edit: ADD creates the widget, its detail view and route, and records it in state', () => {
  const ws = builtWorkspace()
  writeModules(ws.work, { 'error-rate': FETCH_DATA + FETCH_DETAIL })
  const metric = { name: 'error-rate', tier: 'T3', title: 'Error rate', displayAs: 'area-chart' }
  const { r, events } = runPlan(ws, editPlan(ws, { op: 'ADD', metric }), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.deepEqual(events.at(-1), { type: 'INCREMENTAL_READY', payload: { count: 1, ops: [{ op: 'ADD', widget: 'ErrorRate' }] } })
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'widgets', 'ErrorRate.tsx')))
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'views', 'ErrorRateView.tsx')))
  assert.ok(existsSync(at(ws, 'src', 'metrics', 'error-rate.ts')))
  assert.match(readFileSync(at(ws, 'src', 'dashboard', 'Dashboard.tsx'), 'utf8'), /<ErrorRate \/>/)
  assert.match(readFileSync(at(ws, 'src', 'App.tsx'), 'utf8'), /path="\/errorrate"/)
  const state = stateOf(ws)
  assert.equal(state.widgets.ErrorRate.template, 'area-chart')
  assert.equal(state.widgets.ErrorRate.module, 'metrics/error-rate.ts')
  assert.deepEqual(Object.keys(state.widgets), ['OrdersTable', 'SalesTrend', 'OpenCount', 'ErrorRate'])
})

test('edit: a batch applies ADD of a keyed table and REMOVE together, regenerating the dashboard once', () => {
  const ws = builtWorkspace()
  writeModules(ws.work, { 'refunds': FETCH_DATA + FETCH_KEYED })
  const metric = { name: 'refunds', tier: 'T3', title: 'Refunds', displayAs: 'data-table', rowLink: { key: 'id' } }
  const { r, events } = runPlan(ws, editPlan(ws, { ops: [{ op: 'ADD', metric }, { op: 'REMOVE', target: 'SalesTrend' }] }), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.equal(events.at(-1).payload.count, 2)
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'views', 'RefundsDetailView.tsx')))
  for (const gone of [['widgets', 'SalesTrend.tsx'], ['views', 'SalesTrendView.tsx']]) {
    assert.ok(!existsSync(at(ws, 'src', 'dashboard', ...gone)), gone.join('/'))
  }
  assert.ok(!existsSync(at(ws, 'src', 'metrics', 'sales-trend.ts')))
  const state = stateOf(ws)
  assert.ok(!('SalesTrend' in state.widgets))
  assert.ok('Refunds' in state.widgets)
  assert.doesNotMatch(readFileSync(at(ws, 'src', 'dashboard', 'Dashboard.tsx'), 'utf8'), /SalesTrend/)
  assert.doesNotMatch(readFileSync(at(ws, 'src', 'App.tsx'), 'utf8'), /SalesTrendView/)
})

test('edit: the whole batch is validated first — every violation is listed and nothing is written', () => {
  const ws = builtWorkspace()
  const before = readFileSync(at(ws, '.dashboard', 'state.json'), 'utf8')
  const { r } = runPlan(ws, editPlan(ws, { ops: [
    { op: 'ADD' },
    { op: 'ADD', metric: { name: 'ghost', tier: 'T3', title: 'Ghost', displayAs: 'bar-chart' } },
    { op: 'ADD', metric: { name: 'bad-chart', tier: 'T3', title: 'Bad', displayAs: 'bar-chart' } },
    { op: 'ADD', metric: { name: 'not-in-registry', tier: 'T1', title: 'Nope' } },
    { op: 'REMOVE' },
    { op: 'CHANGE' },
    { op: 'CHANGE', target: 'NeverBuilt' },
  ] }), { file: 'edit-intent.json' })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Batch rejected — nothing was changed:/)
  assert.match(r.stderr, /ops\[0\] ADD: missing metric/)
  assert.match(r.stderr, /ops\[1\] ADD "ghost": metric module not found — write metrics\/ghost\.ts exporting "fetchData"/)
  assert.match(r.stderr, /ops\[3\] ADD "not-in-registry": Metric "not-in-registry" \(T1\) not found in registry/)
  assert.match(r.stderr, /ops\[4\] REMOVE: missing target/)
  assert.match(r.stderr, /ops\[5\] CHANGE: missing target/)
  assert.match(r.stderr, /ops\[6\] CHANGE "NeverBuilt": no metric module found/)
  assert.equal(readFileSync(at(ws, '.dashboard', 'state.json'), 'utf8'), before)
})

test('edit: ADD of a drill-down chart whose module lacks fetchDetail is rejected', () => {
  const ws = builtWorkspace()
  writeModules(ws.work, { 'bad-chart': FETCH_DATA })
  const { r } = runPlan(ws, editPlan(ws, { op: 'ADD', metric: { name: 'bad-chart', tier: 'T3', title: 'Bad', displayAs: 'bar-chart' } }), { file: 'edit-intent.json' })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /ops\[0\] ADD "bad-chart": drill-down widget needs a record-grain "fetchDetail" export in metrics\/bad-chart\.ts/)
})

test('edit: a hand-edited widget cannot be removed or changed (HAND_EDIT_DETECTED)', () => {
  const ws = builtWorkspace()
  writeFileSync(at(ws, 'src', 'dashboard', 'widgets', 'OpenCount.tsx'), '// my own tweak\n', { flag: 'a' })
  const { r, events } = runPlan(ws, editPlan(ws, { op: 'REMOVE', target: 'OpenCount' }), { file: 'edit-intent.json' })
  assert.equal(r.status, 1)
  assert.deepEqual(events.find(e => e.type === 'HAND_EDIT_DETECTED').payload, { widget: 'OpenCount' })
  assert.match(r.stderr, /"OpenCount": hand-edited — overwriting would lose changes/)
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'widgets', 'OpenCount.tsx')))
})

test('edit: CHANGE retitles a widget using its persisted metadata, with no new module supplied', () => {
  const ws = builtWorkspace()
  const { r } = runPlan(ws, editPlan(ws, { op: 'CHANGE', target: 'OpenCount', delta: { title: 'Open tickets' } }), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  const widget = readFileSync(at(ws, 'src', 'dashboard', 'widgets', 'OpenCount.tsx'), 'utf8')
  assert.match(widget, /Open tickets/)
  assert.equal(stateOf(ws).widgets.OpenCount.intentMetric.title, 'Open tickets')
})

test('edit: CHANGE from a chart to a keyed table drops the chart view and adds the row-click view', () => {
  const ws = builtWorkspace()
  const delta = { displayAs: 'ranked-table', rowLink: { key: 'id' } }
  const { r } = runPlan(ws, editPlan(ws, { op: 'CHANGE', target: 'SalesTrend', delta }), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.ok(!existsSync(at(ws, 'src', 'dashboard', 'views', 'SalesTrendView.tsx')))
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'views', 'SalesTrendDetailView.tsx')))
  assert.equal(stateOf(ws).widgets.SalesTrend.template, 'ranked-table')
  assert.match(readFileSync(at(ws, 'src', 'App.tsx'), 'utf8'), /path="\/salestrend\/:key"/)
})

test('edit: CHANGE with a replacement module and time range copies the module and regenerates the view', () => {
  const ws = builtWorkspace()
  writeModules(ws.work, { 'sales-trend': FETCH_DATA + FETCH_DETAIL + '// v2\n' })
  const { r } = runPlan(ws, editPlan(ws, { op: 'CHANGE', target: 'SalesTrend', delta: { timeRange: '90d' } }), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.match(readFileSync(at(ws, 'src', 'metrics', 'sales-trend.ts'), 'utf8'), /\/\/ v2/)
  assert.match(readFileSync(at(ws, 'src', 'dashboard', 'views', 'SalesTrendView.tsx'), 'utf8'), /Last 90 days/)
})

test('edit: REBUILD regenerates every widget and skips legacy entries that have no persisted intent', () => {
  const ws = builtWorkspace()
  const state = stateOf(ws)
  delete state.widgets.OpenCount.intentMetric
  writeFileSync(at(ws, '.dashboard', 'state.json'), JSON.stringify({ ...state, buildStatus: 'in-progress', versions: { scaffold: '0.0.1' } }))
  rmSync(at(ws, 'src', 'dashboard', 'widgets', 'OrdersTable.tsx'))
  const { r, types } = runPlan(ws, editPlan(ws, { op: 'REBUILD' }), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'widgets', 'OrdersTable.tsx')), 'regenerated')
  assert.match(r.stdout, /Cannot rebuild "OpenCount" — built before intent persistence/)
  assert.match(r.stdout, /Previous build did not complete/)
  assert.ok(types.includes('UPGRADE_AVAILABLE'))
  assert.equal(stateOf(ws).buildStatus, 'in-progress', 'state keeps its status; only versions are re-stamped')
  assert.notEqual(stateOf(ws).versions.scaffold, '0.0.1')
})

test('edit: Stage-A failure after the batch exits 2 with METRICS_RETRY', () => {
  const ws = builtWorkspace()
  const { r, types } = runPlan(ws, editPlan(ws, { op: 'REBUILD' }), { file: 'edit-intent.json', env: { FAKE_METRICS_FAIL: '1' } })
  assert.equal(r.status, 2)
  assert.ok(types.includes('METRICS_RETRY'))
  assert.match(r.stdout, /Metric modules have TypeScript errors/)
})

test('edit: a tsc failure after the batch emits TSC_FAIL and exits 1', () => {
  const ws = builtWorkspace()
  const { r, events } = runPlan(ws, editPlan(ws, { op: 'REBUILD' }), { file: 'edit-intent.json', env: { FAKE_TSC_FAIL: '1' } })
  assert.equal(r.status, 1)
  assert.match(events.find(e => e.type === 'TSC_FAIL').payload.errors, /boom/)
  assert.match(r.stderr, /TypeScript errors after edit:/)
})

test('edit: an unknown op is rejected by the dispatcher', () => {
  const ws = builtWorkspace()
  const { r } = runPlan(ws, editPlan(ws, { op: 'EXPLODE' }), { file: 'edit-intent.json' })
  assert.notEqual(r.status, 0)
  assert.match(r.stderr, /invalid op "EXPLODE"/)
})

// ═════════════════════════════════════════════════════════════════════════════
// Upgrade
// ═════════════════════════════════════════════════════════════════════════════

const upgradePlan = ws => editPlan(ws, { op: 'UPGRADE' })

test('upgrade: regenerates every widget, migrates intent.json and re-stamps the versions', () => {
  const ws = builtWorkspace()
  const migrations = join(ws.work, 'migrations')
  mkdirSync(migrations)
  writeFileSync(join(migrations, 'intent-v1-to-v2.mjs'), 'export const migrate = i => ({ ...i, migratedBy: "test" })\n')
  writeFileSync(at(ws, 'intent.json'), JSON.stringify({ schemaVersion: 1, metrics: [] }))
  // Age the project: stale versions, a broken generated widget, and no regenerated hash
  const state = stateOf(ws)
  state.versions = { scaffold: '0.0.1', skill: '0.0.1' }
  writeFileSync(at(ws, '.dashboard', 'state.json'), JSON.stringify(state))
  writeFileSync(at(ws, 'src', 'dashboard', 'widgets', 'SalesTrend.tsx'), '// stale\n')

  const { r, events } = runPlan(ws, upgradePlan(ws), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  const done = events.find(e => e.type === 'UPGRADE_DONE').payload
  assert.deepEqual(done.widgets, ['OrdersTable', 'SalesTrend', 'OpenCount'])
  assert.equal(done.to, readJson(at(ws, '_gen', 'starter-kit.json')).version)
  assert.ok(events.some(e => e.type === 'UPGRADE_AVAILABLE'))

  assert.notEqual(readFileSync(at(ws, 'src', 'dashboard', 'widgets', 'SalesTrend.tsx'), 'utf8'), '// stale\n')
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'views', 'SalesTrendView.tsx')))
  assert.ok(existsSync(at(ws, 'src', 'dashboard', 'views', 'OrdersTableDetailView.tsx')))
  assert.match(readFileSync(at(ws, 'src', 'App.tsx'), 'utf8'), /OrdersTableDetailView/)
  const migrated = readJson(at(ws, 'intent.json'))
  assert.equal(migrated.migratedBy, 'test')
  assert.equal(migrated.schemaVersion, 2)
  const after = stateOf(ws)
  assert.equal(after.versions.scaffold, done.to)
  assert.equal(after.versions.sdk, '1.5.1')
})

test('upgrade: installs dependencies first when node_modules is missing', () => {
  const ws = builtWorkspace()
  rmSync(at(ws, 'node_modules'), { recursive: true })
  const { r, types } = runPlan(ws, upgradePlan(ws), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /⚙ Installing dependencies…/)
  assert.ok(types.includes('PREWARM_START') && types.includes('PREWARM_DONE'))
  assert.ok(types.includes('UPGRADE_DONE'))
})

test('upgrade: warns that a dirty git tree will have disposable files regenerated', () => {
  const ws = builtWorkspace()
  execFileSync('git', ['init', '-q'], { cwd: ws.project })
  const { r } = runPlan(ws, upgradePlan(ws), { file: 'edit-intent.json' })
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /Project has uncommitted changes — upgrade regenerates disposable files/)
})

test('upgrade: Stage-A failure exits 2, a tsc failure exits 1, and neither re-stamps the state', () => {
  const ws = builtWorkspace()
  const stale = { ...stateOf(ws), versions: { scaffold: '0.0.1' } }
  writeFileSync(at(ws, '.dashboard', 'state.json'), JSON.stringify(stale))

  const a = runPlan(ws, upgradePlan(ws), { file: 'edit-intent.json', env: { FAKE_METRICS_FAIL: '1' } })
  assert.equal(a.r.status, 2)
  assert.ok(a.types.includes('METRICS_RETRY'))

  const b = runPlan(ws, upgradePlan(ws), { file: 'edit-intent.json', env: { FAKE_TSC_FAIL: '1' } })
  assert.equal(b.r.status, 1)
  assert.ok(b.types.includes('TSC_FAIL'))
  assert.match(b.r.stderr, /Upgrade produced TypeScript errors/)

  assert.deepEqual(stateOf(ws).versions, { scaffold: '0.0.1' })
})
