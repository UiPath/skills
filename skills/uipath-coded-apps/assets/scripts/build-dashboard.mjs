#!/usr/bin/env node
/**
 * build-dashboard.mjs — Dashboard build pipeline
 *
 * Accepts an intent.json or edit-intent.json as a file path argument and
 * generates a complete React dashboard project.
 *
 * Input routing:
 *   intent.json      (has "metrics" field) → runDashboardBuild()
 *   edit-intent.json (has "op" field)      → runIncrementalEdit()
 *
 * Usage:
 *   node build-dashboard.mjs <path-to-json>
 *
 * Exit codes:
 *   0 — success
 *   1 — fatal error (message on stderr)
 *   2 — widget needs retry (update fnBody in intent.json and re-run)
 */

import { readFileSync, writeFileSync, copyFileSync, mkdirSync, existsSync, renameSync, unlinkSync } from 'fs'
import { createConnection } from 'net'
import { join, dirname, basename, resolve } from 'path'
import { fileURLToPath, pathToFileURL } from 'url'
import { execSync } from 'child_process'
import { createHash } from 'crypto'

// ── Path constants ─────────────────────────────────────────────────────────────

const __dirname = dirname(fileURLToPath(import.meta.url))

// Widget generator templates ship INSIDE the starter-kit zip (under _gen/widgets),
// not in the skill — the skill carries no scaffold/template source and no zip code.
// The orchestration points this at <project>/_gen/widgets after the agent extracts
// the kit; tests set it via setWidgetsDir(). null until set.
let WIDGETS_DIR = null
export function setWidgetsDir(dir) { WIDGETS_DIR = dir }
function widgetsDir() {
  if (!WIDGETS_DIR) fail('Widget templates dir not set — extract the starter kit (assertScaffoldExtracted) before generating widgets.')
  return WIDGETS_DIR
}
function t3ShellTemplatePath() { return join(widgetsDir(), 't3-shell.tsx.template') }

/** Fixed dev server port — high enough to avoid common app collisions */
const DASHBOARD_PORT = 57173

// ── Capability registry ────────────────────────────────────────────────────────

const REGISTRY = JSON.parse(readFileSync(resolve(__dirname, 'capability-registry.json'), 'utf8'))

// ── Type definitions (JSDoc only — this file is plain JavaScript) ────────────

/**
 * @typedef {'T1'|'T2'|'T3'} MetricTier
 */

/**
 * A single metric entry inside intent.json.
 * @typedef {Object} IntentMetric
 * @property {string}      name          - Kebab-case metric identifier
 * @property {MetricTier}  tier          - Resolution tier
 * @property {string}      [title]       - Display title (required for all tiers)
 * @property {string}      [subtitle]    - CardDescription line; auto-filled from time range when absent
 * @property {string}      [description] - Fallback for subtitle
 * @property {string}      [componentName] - Override PascalCase component name
 * @property {string}      [icon]        - lucide-react icon name
 * @property {string}      [detailRoute] - HashRouter path for drilldown
 * @property {Object}      [params]      - T2 filter params (validation only — agent writes fnBody)
 * @property {string}      fnBody        - Required for all tiers: async function body using SDK service classes
 * @property {string}      [displayAs]   - One of VALID_DISPLAY_TYPES
 * @property {string}      [valueField]  - kpi-card: field shown as the headline number
 * @property {string}      [valueLabel]  - kpi-card: label under the headline
 * @property {string}      [xKey]        - Chart x-axis field
 * @property {string}      [yKey]        - Chart value field
 * @property {string}      [headlineMode]   - VALID_HEADLINE_MODES — how the chart headline aggregates
 * @property {string}      [deltaPolarity]  - VALID_DELTA_POLARITIES — is an increase good?
 * @property {string}      [rateNum]     - rate-chart: numerator field per bucket
 * @property {string}      [rateDen]     - rate-chart: denominator field per bucket
 * @property {string}      [columns]     - ColumnDef array literal string (tables)
 * @property {Array<{key:string,label:string,align?:string,format?:string,color?:string}>} [columnDefs] - Structured columns; compiled to formatted/coloured cells
 * @property {string}      [detailFnBody]   - Record-grain query for the chart's detail view
 * @property {Array}       [detailColumns]  - Structured columns for the detail view
 * @property {string}      [detailSortKey]  - Raw field the detail table sorts on
 * @property {string}      [series]      - multi-line-chart series literal
 * @property {string}      [pivotExpression] - multi-line-chart pivot expression
 * @property {DetailViewSpec} [detailView]
 * @property {{key:string}} [rowLink]
 * @property {boolean} [detail]
 */

/**
 * The full intent.json structure.
 * @typedef {Object} DashboardIntent
 * @property {string}        dashboardName
 * @property {string}        [dashboardDescription] - One sentence for the dashboard header
 * @property {'1d'|'7d'|'30d'|'90d'} timeRange
 * @property {IntentMetric[]} metrics
 * @property {string}        projectDir  - Absolute path for generated project
 * @property {string}        routingName - Permanent URL slug (e.g. "agent-health-x7k2")
 * @property {string}        orgName
 * @property {string}        tenantName
 * @property {string}        cloudUrl    - e.g. https://alpha.uipath.com
 * @property {string}        apiUrl      - e.g. https://alpha.api.uipath.com
 * @property {string}        [clientId]  - External OAuth app client ID
 */

/**
 * Derived chart-widget spec — all fields resolved, ready for template substitution.
 * @typedef {Object} WidgetSpec
 * @property {string} componentName
 * @property {string} template
 * @property {string} title
 * @property {string} subtitle
 * @property {string} icon
 * @property {string} detailRoute
 * @property {string} dataHook
 * @property {string} dataSelector
 * @property {string} xKey
 * @property {string} yKey
 * @property {string} headlineMode
 * @property {string} deltaPolarity
 * @property {string} rateNum
 * @property {string} rateDen
 * @property {string} series
 * @property {string} pivotExpression
 */

/**
 * Minimal widget descriptor used for layout classification.
 * @typedef {Object} WidgetMeta
 * @property {string} componentName
 * @property {string} template
 */

/**
 * Per-widget entry persisted in state.json.
 * @typedef {Object} WidgetHashEntry
 * @property {string}     hash         - SHA-256 prefix of generated file content
 * @property {MetricTier} tier
 * @property {string}     metric       - Original metric name from intent
 * @property {string}     template     - Template used for layout classification
 * @property {IntentMetric} intentMetric - Full intent entry, persisted for CHANGE/REBUILD
 */

// ── Constants ──────────────────────────────────────────────────────────────────

const TIME_RANGE_CONSTANTS = {
  '1d':  'ONE_DAY_AGO',
  '7d':  'SEVEN_DAYS_AGO',
  '30d': 'THIRTY_DAYS_AGO',
  '90d': 'NINETY_DAYS_AGO',
}

const KNOWN_EVENTS = new Set([
  'PREWARM_START', 'PREWARM_DONE', 'PREWARM_FAILED', 'SCAFFOLD_READY', 'ENV_WRITTEN',
  'WIDGET_READY', 'METRICS_PASS', 'METRICS_RETRY', 'T3_FAILED', 'TSC_PASS', 'TSC_FAIL',
  'BUILD_RESULT', 'PARTIAL_BUILD_DETECTED', 'AUTH_MISSING',
  'HAND_EDIT_DETECTED', 'T2_SCHEMA_ERROR', 'INCREMENTAL_READY', 'UPGRADE_AVAILABLE', 'UPGRADE_DONE',
])

export const VALID_EDIT_OPS = ['ADD', 'REMOVE', 'CHANGE', 'REBUILD', 'UPGRADE']

/**
 * Display types supported for all widget tiers.
 * Table/KPI types use t3-shell.tsx.template.
 * Chart types use the standard chart templates with customDataFn injected.
 */
export const VALID_DISPLAY_TYPES = [
  'kpi-card', 'ranked-table', 'data-table',
  'area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart',
]

/** Detail-view sub-widget displayAs vocabularies (rich drill-down). */
const DETAIL_CHART_TYPES = new Set(['donut-chart', 'bar-chart', 'area-chart', 'line-chart', 'multi-line-chart'])
const DETAIL_TABLE_TYPES = new Set(['data-table', 'ranked-table'])

/**
 * @typedef {Object} DetailViewWidget
 * @property {'donut-chart'|'bar-chart'|'area-chart'|'line-chart'|'multi-line-chart'|'data-table'|'ranked-table'} displayAs
 * @property {string} title
 * @property {string} source  Key into the detail fetch's named-source map.
 * @property {string} [xKey]
 * @property {string} [yKey]
 * @property {Array<{key:string,color:string}>} [series]  Required for multi-line-chart.
 * @property {Array<object>} [columns]  Table column defs.
 */
/**
 * @typedef {Object} DetailViewSpec
 * @property {DetailViewWidget[]} widgets
 */
/** Validate a metric's optional detailView spec. Throws with a precise message. */
export function validateDetailView(metric) {
  const dv = metric.detailView
  if (dv == null) return
  if (!metric.rowLink?.key && metric.detail !== true) {
    throw new Error(`metric "${metric.name}": detailView requires the metric to have rowLink.key (table) or detail:true (chart)`)
  }
  if (!Array.isArray(dv.widgets) || dv.widgets.length === 0) {
    throw new Error(`metric "${metric.name}": detailView.widgets must be a non-empty array`)
  }
  for (const w of dv.widgets) {
    if (!w.source || typeof w.source !== 'string') throw new Error(`metric "${metric.name}": each detailView widget needs a "source" string`)
    if (!w.title) throw new Error(`metric "${metric.name}": detailView widget (source "${w.source}") needs a title`)
    const isChart = DETAIL_CHART_TYPES.has(w.displayAs)
    const isTable = DETAIL_TABLE_TYPES.has(w.displayAs)
    if (!isChart && !isTable) throw new Error(`metric "${metric.name}": detailView widget displayAs "${w.displayAs}" invalid`)
    if (w.displayAs === 'multi-line-chart') {
      if (!w.xKey || !Array.isArray(w.series) || w.series.length === 0) throw new Error(`metric "${metric.name}": detailView multi-line-chart needs xKey + series[]`)
    } else if (isChart) {
      if (!w.xKey || !w.yKey) throw new Error(`metric "${metric.name}": detailView ${w.displayAs} needs xKey and yKey`)
    }
  }
}

/** Headline aggregate modes — how a chart's big number is computed from its series. */
export const VALID_HEADLINE_MODES = ['sum', 'avg', 'latest', 'count', 'max', 'min']

/** Delta polarity — whether an increase is good, bad, or neutral (drives badge colour). */
export const VALID_DELTA_POLARITIES = ['up-good', 'up-bad', 'neutral']

/** Column value formatters supported in table column defs. */
export const VALID_COLUMN_FORMATS = ['number', 'percent', 'duration', 'timeAgo', 'text']

/**
 * Minimum SDK version the catalog metrics require — the agent-memory and
 * governance subpaths ship in 1.4.1. A stale lockfile/registry otherwise
 * surfaces as cryptic tsc "module not found" failures mid-build.
 */
export const MIN_SDK_VERSION = '1.4.1'

export const SKILL_VERSION = '2.0.0'        // compiler-architecture era; bump per skill release
const FIXTURE_ZIP_PATH = resolve(__dirname, '../fixtures/governance-dashboard-starter-kit.zip')
const SCAFFOLD_VERSION_FILE = resolve(__dirname, '../fixtures/governance-dashboard-starter-kit.version')
function readScaffoldVersion() {
  try { return readFileSync(SCAFFOLD_VERSION_FILE, 'utf8').trim() || '0.0.0' } catch { return '0.0.0' }
}
export const SCAFFOLD_VERSION = readScaffoldVersion()  // published alongside the starter-kit zip by apps-dev-tools
export const INTENT_SCHEMA_VERSION = 2
export const STATE_SCHEMA_VERSION = 2

/**
 * The version block stamped into state.json so a dashboard knows what it was
 * built against (drives offer-on-detect upgrade + future migrations).
 * @param {string|null} [sdkVersion]
 */
export function buildVersions(sdkVersion = null) {
  return { skill: SKILL_VERSION, scaffold: SCAFFOLD_VERSION, intentSchema: INTENT_SCHEMA_VERSION, sdk: sdkVersion }
}

/**
 * Compare a project's stamped scaffold version to the shipped one. Returns
 * { from, to } when they differ (including a pre-versioning project with no
 * versions block), or null when current. Forward-only — any mismatch means
 * "a newer scaffold is available".
 * @param {object} state - parsed .dashboard/state.json
 */
export function scaffoldDrift(state) {
  const stamped = state?.versions?.scaffold ?? null
  return stamped === SCAFFOLD_VERSION ? null : { from: stamped, to: SCAFFOLD_VERSION }
}

/**
 * Apply intent-schema migrations in sequence from intent.schemaVersion up to target.
 * Registry: assets/scripts/migrations/intent-v<N>-to-v<N+1>.mjs (empty today — framework
 * so a future schema bump is a drop-in file, not a refactor). Pure migrate(intent) functions.
 * @param {object} intent
 * @param {string} migrationsDir
 * @param {number} [targetVersion=INTENT_SCHEMA_VERSION]
 */
export async function runIntentMigrations(intent, migrationsDir, targetVersion = INTENT_SCHEMA_VERSION) {
  let v = intent.schemaVersion ?? 1
  while (v < targetVersion) {
    const file = join(migrationsDir, `intent-v${v}-to-v${v + 1}.mjs`)
    if (!existsSync(file)) break
    const { migrate } = await import(pathToFileURL(file).href)
    intent = migrate(intent)
    v++
  }
  intent.schemaVersion = Math.max(intent.schemaVersion ?? 1, v)
  return intent
}

/**
 * Generate (or remove) a table widget's keyed row-click detail view. Writes
 * <Component>DetailView.tsx when the metric is a table with `rowLink`, and removes
 * a stale one otherwise. Shared by fresh build, ADD, CHANGE, REBUILD, and upgrade so
 * the row-click drill-down stays consistent on every path. Returns true if a keyed
 * view now exists on disk.
 * @returns {boolean}
 */
function writeKeyedViewIfRowLink(P, componentName, metric, entry, timeRange) {
  const detailPath = join(P, 'src', 'dashboard', 'views', `${componentName}DetailView.tsx`)
  const displayAs = metric.displayAs ?? entry?.template ?? ''
  // rowLink and detailView fall back to the registry entry's defaults — same as
  // title/columns — so a cataloged metric (e.g. agent-compliance-report) ships its
  // drill-down without the intent having to restate it.
  const rowLink = metric.rowLink ?? entry?.defaults?.rowLink
  const detailView = metric.detailView ?? entry?.defaults?.detailView ?? null
  if (rowLink?.key && widgetLayoutGroup(displayAs) === 'table') {
    writeAtomic(detailPath, generateKeyedDetailViewFile({
      componentName,
      title: metric.title ?? entry?.defaults?.title ?? componentName,
      subtitle: autoSubtitle(metric, entry?.defaults ?? {}, timeRange),
      moduleSpecifier: metricModuleSpecifier(metric),
      detailColumns: metric.detailColumns ? compileColumns(metric.detailColumns) : null,
      detailView,
    }))
    return true
  }
  if (existsSync(detailPath)) unlinkSync(detailPath)
  return false
}

/** Route descriptors for every widget that currently has a keyed DetailView file on disk. */
function collectKeyedViews(P, state) {
  return Object.keys(state.widgets ?? {})
    .filter(name => existsSync(join(P, 'src', 'dashboard', 'views', `${name}DetailView.tsx`)))
    .map(name => ({ componentName: name, routeBase: `/${name.toLowerCase()}` }))
}

/**
 * Regenerate every widget + chart view from each widget's persisted intentMetric
 * (metadata) against the on-disk metric modules. Used by the REBUILD op and by upgrade.
 * @param {string} P  resolved project dir
 * @param {object} state  parsed state.json (widget hashes refreshed in place)
 * @param {string} timeRange
 */
export function rebuildAllWidgets(P, state, timeRange) {
  for (const [componentName, info] of Object.entries(state.widgets ?? {})) {
    const m = info.intentMetric
    if (!m) {
      log(`⚠ Cannot rebuild "${componentName}" — built before intent persistence. Re-run a fresh build to refresh it.`)
      continue
    }
    const { entry } = resolveMetric(m)
    const content = buildWidgetFile(m, entry, timeRange)
    writeAtomic(join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`), content)
    info.hash = hashContent(content)
    const viewPath = join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`)
    if (widgetLayoutGroup(info.template ?? '') === 'chart') {
      writeAtomic(viewPath, generateViewFile(buildViewSpec(componentName, m, entry, timeRange)))
    } else if (existsSync(viewPath)) {
      unlinkSync(viewPath)
    }
    writeKeyedViewIfRowLink(P, componentName, m, entry, timeRange)
  }
}

/**
 * Upgrade an existing dashboard to the current scaffold: refresh the disposable
 * framework, migrate intent.json, regenerate widgets/views from durable intent +
 * on-disk metric modules, re-validate, and re-stamp versions. The durable set
 * (intent.json, src/metrics, .dashboard, .env.local, uipath.json's clientId) is
 * preserved. The framework refresh extracts the starter-kit archive (see lib/zip.mjs).
 * @param {string} P  resolved project dir
 * @param {object} state  parsed state.json
 * @param {string} intentPath  edit-intent path (for the migrations dir + retry signal)
 */
async function runUpgrade(P, state, intentPath) {
  // Best-effort dirty-tree warning — upgrade regenerates disposable files.
  try {
    const dirty = execSync(`git -C "${P}" status --porcelain`, { stdio: 'pipe' }).toString().trim()
    if (dirty) log('⚠ Project has uncommitted changes — upgrade regenerates disposable files (your intent.json + src/metrics are preserved).')
  } catch { /* not a git repo — nothing to check */ }

  // 1. Refresh the disposable scaffold framework: the agent re-extracts the
  //    latest starter-kit archive over the project before --upgrade (preserving
  //    src/metrics, intent.json, and the gitignored .env.local that carries the
  //    clientId). Verify the fresh kit is present and point at its templates.
  assertScaffoldExtracted(P)
  setWidgetsDir(join(P, '_gen', 'widgets'))

  // 2. Migrate intent.json if present (no-op today — empty registry).
  const intentJsonPath = join(P, 'intent.json')
  if (existsSync(intentJsonPath)) {
    const migrated = await runIntentMigrations(
      JSON.parse(readFileSync(intentJsonPath, 'utf8')),
      join(dirname(intentPath), 'migrations'),
    )
    writeAtomic(intentJsonPath, JSON.stringify(migrated, null, 2))
  }

  // 3. Ensure deps, then regenerate from durable intent + on-disk metric modules.
  const LOCK_SIGNAL = join(P, 'node_modules', '.package-lock.json')
  if (!existsSync(LOCK_SIGNAL)) { log('⚙ Installing dependencies…'); await runPrewarm(P) }
  rebuildAllWidgets(P, state, state.timeRange ?? '30d')
  const widgetMeta = Object.entries(state.widgets ?? {}).map(([name, info]) => ({ componentName: name, template: info.template ?? 'ranked-table' }))
  generateDashboardFiles(P, widgetMeta, state.app?.name ?? 'Dashboard', state.app?.description ?? '')
  injectAppRoutes(
    P,
    Object.keys(state.widgets ?? {}).filter(n => existsSync(join(P, 'src', 'dashboard', 'views', `${n}View.tsx`))),
    collectKeyedViews(P, state),
  )

  // 4. Validate: Stage A (metric modules in isolation) then the full app.
  const stageA = runMetricsTypecheck(P)
  if (!stageA.ok) { emit('METRICS_RETRY', { files: stageA.files, errors: stageA.errors, intentPath }); process.exit(2) }
  try { execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' }) }
  catch (e) { emit('TSC_FAIL', { errors: (e.stdout?.toString() || '').slice(0, 1000) }); fail('Upgrade produced TypeScript errors') }

  // 5. Re-stamp + persist.
  state.schemaVersion = STATE_SCHEMA_VERSION
  state.versions = buildVersions(checkSdkVersion(P).version)
  writeAtomic(join(P, '.dashboard', 'state.json'), JSON.stringify(state, null, 2))
  emit('UPGRADE_DONE', { to: SCAFFOLD_VERSION, widgets: Object.keys(state.widgets ?? {}) })
}

/**
 * Check the installed @uipath/uipath-typescript version in a project.
 * @param {string} projectPath
 * @returns {{ ok: boolean, version: string|null }}
 */
export function checkSdkVersion(projectPath) {
  const pkgPath = join(projectPath, 'node_modules', '@uipath', 'uipath-typescript', 'package.json')
  if (!existsSync(pkgPath)) return { ok: false, version: null }
  let version
  try { version = JSON.parse(readFileSync(pkgPath, 'utf8')).version } catch { return { ok: false, version: null } }
  const [maj = 0, min = 0, pat = 0] = String(version).split('.').map(Number)
  const [rMaj, rMin, rPat] = MIN_SDK_VERSION.split('.').map(Number)
  const ok = maj > rMaj || (maj === rMaj && (min > rMin || (min === rMin && pat >= rPat)))
  return { ok, version }
}

/** Map a time range to a human subtitle fragment. */
function timeRangeLabel(timeRange) {
  return { '1d': 'last 24 hours', '7d': 'last 7 days', '30d': 'last 30 days', '90d': 'last 90 days' }[timeRange] ?? timeRange
}

/**
 * OAuth scopes required for the dashboard.
 * These MUST match what is registered on the external OAuth app.
 * Use parent scopes only — .Read sub-scopes are not reliably registered.
 */
const DASHBOARD_SCOPES = 'OR.Assets OR.Jobs OR.Folders OR.Buckets OR.Execution OR.Tasks OR.Queues OR.Users Insights Insights.RealTimeData Traces.Api PIMS'

// ── Low-level utilities ────────────────────────────────────────────────────────

function fail(msg) {
  process.stderr.write(`ERROR: ${msg}\n`)
  process.exit(1)
}

function log(msg) {
  process.stdout.write(msg + '\n')
}

/**
 * The agent extracts the starter-kit zip into the project dir before building —
 * the skill ships no zip/unzip code. This verifies the kit landed (scaffold app +
 * the _gen/widgets generator templates) and fails loud with the OS-native extract
 * command if not. Pick the command for your platform.
 * @param {string} projectPath
 */
function assertScaffoldExtracted(projectPath) {
  const hasScaffold = existsSync(join(projectPath, 'package.json'))
  const hasTemplates = existsSync(join(projectPath, '_gen', 'widgets'))
  if (hasScaffold && hasTemplates) return
  fail([
    `Starter kit not extracted into: ${projectPath}`,
    `Extract the archive there first (choose your OS):`,
    `  Windows : powershell -NoProfile -Command "Expand-Archive -LiteralPath '${FIXTURE_ZIP_PATH}' -DestinationPath '${projectPath}' -Force"`,
    `  macOS   : unzip -o "${FIXTURE_ZIP_PATH}" -d "${projectPath}"   (or: ditto -x -k "${FIXTURE_ZIP_PATH}" "${projectPath}")`,
    `  Linux   : unzip -o "${FIXTURE_ZIP_PATH}" -d "${projectPath}"   (or: python3 -m zipfile -e "${FIXTURE_ZIP_PATH}" "${projectPath}")`,
    `Then re-run the build.`,
  ].join('\n'))
}

/** Atomic file write — write to .tmp then rename on success */
function writeAtomic(filePath, content) {
  mkdirSync(dirname(filePath), { recursive: true })
  const tmp = filePath + '.tmp'
  writeFileSync(tmp, content, 'utf8')
  renameSync(tmp, filePath)
}

function hashContent(content) {
  return createHash('sha256').update(content).digest('hex').slice(0, 16)
}

function toPascalCase(str) {
  return str.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join('')
}

// ── Pre-warm ───────────────────────────────────────────────────────────────────

/**
 * Run npm ci in the given project directory with a pre-warm lock sentinel.
 * Emits PREWARM_START, PREWARM_DONE, or PREWARM_FAILED events.
 * @param {string} projectPath - Absolute path to project directory
 * @returns {Promise<void>}
 */
export async function runPrewarm(projectPath) {
  emit('PREWARM_START')
  const prewarmLock = join(projectPath, '.prewarm.lock')
  writeAtomic(prewarmLock, String(Date.now()))
  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm'
  try {
    execSync(`${npmCmd} ci --prefer-offline`, { cwd: projectPath, stdio: 'pipe' })
  } catch {
    try {
      execSync(`${npmCmd} ci`, { cwd: projectPath, stdio: 'pipe' })
    } catch (e) {
      const stderr = (e.stderr?.toString() ?? String(e)).slice(0, 500)
      emit('PREWARM_FAILED', { exitCode: e.status ?? 1, stderr })
      try { unlinkSync(prewarmLock) } catch { /* ignore */ }
      throw new Error(`npm ci failed: ${stderr}`)
    }
  }
  try { unlinkSync(prewarmLock) } catch { /* ignore */ }
  emit('PREWARM_DONE')
}

/**
 * Block until node_modules/.package-lock.json appears (written by npm ci).
 * Used when pre-warm was started in the background during plan review.
 * Emits PREWARM_DONE or PREWARM_FAILED.
 * @param {string} projectPath
 * @param {number} [timeoutMs=300000]
 */
export function waitForPrewarm(projectPath, timeoutMs = 300_000) {
  const signal = join(projectPath, 'node_modules', '.package-lock.json')
  const deadline = Date.now() + timeoutMs
  const startedAt = Date.now()
  let lastLogAt = 0

  while (!existsSync(signal)) {
    const elapsed = Date.now() - startedAt

    if (Date.now() > deadline) {
      emit('PREWARM_FAILED', { exitCode: -1, stderr: `Timed out after ${Math.round(timeoutMs / 1000)}s` })
      throw new Error(`Pre-warm timed out after ${Math.round(timeoutMs / 1000)}s`)
    }

    // Log progress every 20 seconds so the build output shows life
    if (elapsed - lastLogAt >= 20_000) {
      log(`⏳ Installing dependencies… (${Math.round(elapsed / 1000)}s)`)
      lastLogAt = elapsed
    }

    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 500)
  }

  emit('PREWARM_DONE')
}

/**
 * Stage A — isolated type-check of the agent-written metric modules, before any
 * widget is generated. Fast (no React graph) and maps errors directly to the
 * offending src/metrics/<name>.ts file.
 * @param {string} projectPath
 * @returns {{ ok: true } | { ok: false, errors: string[], files: string[] }}
 */
export function runMetricsTypecheck(projectPath) {
  try {
    execSync('npx tsc -p tsconfig.metrics.json', { cwd: projectPath, stdio: 'pipe' })
    return { ok: true }
  } catch (e) {
    const out = (e.stdout?.toString() ?? '') + (e.stderr?.toString() ?? '')
    const errors = out.split('\n').filter(l => l.includes('error TS')).slice(0, 20)
    const files = [...new Set((out.match(/src[/\\]metrics[/\\][\w-]+\.ts/g) ?? []).map(p => p.replace(/\\/g, '/')))]
    return { ok: false, errors, files }
  }
}

// ── Event streaming ────────────────────────────────────────────────────────────

/**
 * Emit a structured event line to stdout (or a custom writer for testing).
 * @param {string} type  - Must be one of KNOWN_EVENTS
 * @param {object|null} [payload=null]
 * @param {{ write: (s: string) => void }} [writer=process.stdout]
 */
export function emit(type, payload = null, writer = process.stdout) {
  const line = payload != null ? `${type}:${JSON.stringify(payload)}` : type
  writer.write(line + '\n')
}

/**
 * Parse a stdout line back to a structured event, or null if not a known event.
 * @param {string} line
 * @returns {{ type: string, payload: object|null }|null}
 */
export function parseEvent(line) {
  const trimmed = line.trim()
  const colonIdx = trimmed.indexOf(':')
  if (colonIdx === -1) {
    return KNOWN_EVENTS.has(trimmed) ? { type: trimmed, payload: null } : null
  }
  const type = trimmed.slice(0, colonIdx)
  if (!KNOWN_EVENTS.has(type)) return null
  try {
    return { type, payload: JSON.parse(trimmed.slice(colonIdx + 1)) }
  } catch {
    return null
  }
}

// ── Template helpers ───────────────────────────────────────────────────────────

/**
 * Load a widget template and apply <PLACEHOLDER> substitutions.
 * Injects time constants after the last import line.
 * @param {string} templateName
 * @param {Record<string, string>} subs
 * @returns {string}
 */
function applyTemplate(templateName, subs) {
  const templatePath = join(widgetsDir(), `${templateName}.tsx`)
  if (!existsSync(templatePath)) fail(`Template not found: ${templateName}.tsx in ${widgetsDir()}`)
  let content = readFileSync(templatePath, 'utf8')

  for (const [key, value] of Object.entries(subs)) {
    content = content.split(`<${key}>`).join(value)
  }

  // Detect unresolved placeholders — a remaining <UPPER_CASE> token means a
  // placeholder was in the template but not supplied in the substitution map.
  // Fail loudly now rather than generating broken TypeScript that confuses tsc.
  const unresolved = [...new Set((content.match(/<[A-Z][A-Z_]+>/g) ?? []))]
  if (unresolved.length > 0) {
    fail(
      `Template "${templateName}.tsx" has unresolved placeholders: ${unresolved.join(', ')}. ` +
      `These must be added to the substitution map passed to applyTemplate().`
    )
  }

  return content
}

/**
 * Generate a detail view file for a widget.
 *
 * Drills to RECORD GRAIN: the view runs `detailFnBody` — the individual records
 * behind the chart (e.g. each job run), not the chart's aggregated buckets. When
 * `detailColumns` (a compiled ColumnDef literal) is supplied, it drives the table
 * (formatted/coloured cells); otherwise columns are auto-detected at runtime.
 * `defaultSortKey` keys the initial sort on the raw field (e.g. an ISO timestamp)
 * so chronological order is correct even when a column renders a friendly label.
 *
 * @param {{ componentName: string, title: string, subtitle?: string, moduleSpecifier: string, detailExport: string, detailColumns?: string|null, defaultSortKey?: string }} widget
 * @returns {string} Full TypeScript file content
 */
export function generateViewFile(widget) {
  const { componentName, title, subtitle = '', moduleSpecifier, detailExport, detailColumns, defaultSortKey, detailView = null } = widget

  const columnsExpr = detailColumns ? detailColumns : 'autoColumns(rows)'
  const sortKeyExpr = defaultSortKey ? JSON.stringify(defaultSortKey) : '(columns[0]?.key as string)'

  const compiled = detailView ? compileDetailWidgets(detailView, 'd') : null
  const extraImports = compiled ? '\n' + [...compiled.imports].filter(i => !i.includes("'@/dashboard/chrome/RecordsTable'")).join('\n') : ''

  const body = detailView
    ? `  const d = (data && !Array.isArray(data)) ? (data as Record<string, unknown[]>) : { rows: toRows(data ?? []) }

  if (loading) return (
    <DetailViewShell title="${title ?? componentName}" description="${subtitle}">
      <LoadingState height="h-96" />
    </DetailViewShell>
  )
  if (error) return (
    <DetailViewShell title="${title ?? componentName}" description="${subtitle}">
      <EmptyState message={error.message} />
    </DetailViewShell>
  )
  return (
    <DetailViewShell title="${title ?? componentName}" description="${subtitle}">
      <div className="space-y-6">
${compiled.jsx}
      </div>
    </DetailViewShell>
  )`
    : `  const rows = toRows(data ?? [])
  const columns = ${columnsExpr}

  if (loading) return (
    <DetailViewShell title="${title ?? componentName}" description="${subtitle}">
      <LoadingState height="h-96" />
    </DetailViewShell>
  )
  if (error) return (
    <DetailViewShell title="${title ?? componentName}" description="${subtitle}">
      <EmptyState message={error.message} />
    </DetailViewShell>
  )
  return (
    <DetailViewShell title="${title ?? componentName}" description="${subtitle}">
      <RecordsTable rows={rows} columns={columns} defaultSortKey={${sortKeyExpr}} />
    </DetailViewShell>
  )`

  return `import React from 'react'
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useWidgetData } from '@/hooks/useWidgetData'
import { LoadingState, EmptyState } from '@/dashboard/chrome'
import { fmtNumber, fmtPercent, fmtDuration, fmtTimeAgo } from '@/lib/format'
import { toneClass } from '@/lib/widget'
import { ${detailExport} } from '${moduleSpecifier}'${extraImports}

type Row = Record<string, unknown>

/** Auto-detect columns from the first row when explicit detailColumns aren't given. */
function autoColumns(rows: Row[]): ColumnDef<Row>[] {
  if (rows.length === 0) return [{ key: 'value', label: 'Value' }]
  return Object.entries(rows[0])
    .filter(([, v]) => v !== null && v !== undefined && typeof v !== 'object')
    .map(([k, v]) => ({
      key: k,
      label: k.replace(/([A-Z])/g, ' $1').replace(/^(.)/, (s: string) => s.toUpperCase()).trim(),
      ...(typeof v === 'number' && { align: 'right' as const }),
    }))
}

export function ${componentName}View() {
  const { data, loading, error } = useWidgetData(${detailExport}, [])

  /** Safely extract a row array from any response shape */
  function toRows(raw: unknown): Row[] {
    if (!raw) return []
    if (Array.isArray(raw)) return raw as Row[]
    if (typeof raw === 'object') {
      const obj = raw as Record<string, unknown>
      if (Array.isArray(obj.items)) return obj.items as Row[]
      if (Array.isArray(obj.data)) return obj.data as Row[]
      if (obj.data && typeof obj.data === 'object') return toRows(obj.data)
    }
    return []
  }

${body}
}
`
}

/**
 * Generate a KEYED detail view for a table widget with `rowLink` — reads the
 * route param and calls the module's `fetchDetailByKey(sdk, key, getToken)`.
 * @param {{componentName:string,title?:string,subtitle?:string,moduleSpecifier:string,detailColumns?:string|null}} widget
 * @returns {string}
 */
export function generateKeyedDetailViewFile(widget) {
  const { componentName, title, subtitle = '', moduleSpecifier, detailColumns, detailView = null } = widget
  const columnsExpr = detailColumns ? detailColumns : 'autoColumns(rows)'

  const compiled = detailView ? compileDetailWidgets(detailView, 'd') : null
  const extraImports = compiled ? '\n' + [...compiled.imports].filter(i => !i.includes("'@/dashboard/chrome/RecordsTable'")).join('\n') : ''

  // Body branches: rich detailView renders compiled sub-widgets over a normalized
  // source map; otherwise today's single RecordsTable (backward-compat, unchanged).
  const stateInit = detailView ? `const [data, setData] = useState<unknown>(null)` : `const [data, setData] = useState<Row[]>([])`
  const fetchThen = detailView
    ? `.then((res: unknown) => { setData(res); setLoading(false) })`
    : `.then((rows: Row[]) => { setData(rows); setLoading(false) })`

  const body = detailView
    ? `  const d = (data && !Array.isArray(data)) ? (data as Record<string, unknown[]>) : { rows: toRows(data as unknown) }
  const heading = key ? \`${title ?? componentName}: \${decodeURIComponent(key)}\` : '${title ?? componentName}'

  if (loading) return (
    <DetailViewShell title={heading} description="${subtitle}">
      <LoadingState height="h-96" />
    </DetailViewShell>
  )
  if (error) return (
    <DetailViewShell title={heading} description="${subtitle}">
      <EmptyState message={error.message} />
    </DetailViewShell>
  )
  return (
    <DetailViewShell title={heading} description="${subtitle}">
      <div className="space-y-6">
${compiled.jsx}
      </div>
    </DetailViewShell>
  )`
    : `  const rows = data
  const columns = ${columnsExpr}
  const heading = key ? \`${title ?? componentName}: \${decodeURIComponent(key)}\` : '${title ?? componentName}'

  if (loading) return (
    <DetailViewShell title={heading} description="${subtitle}">
      <LoadingState height="h-96" />
    </DetailViewShell>
  )
  if (error) return (
    <DetailViewShell title={heading} description="${subtitle}">
      <EmptyState message={error.message} />
    </DetailViewShell>
  )
  return (
    <DetailViewShell title={heading} description="${subtitle}">
      <RecordsTable rows={rows} columns={columns} />
    </DetailViewShell>
  )`

  return `import React from 'react'
import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useAuth } from '@/hooks/useAuth'
import { LoadingState, EmptyState } from '@/dashboard/chrome'
import { fmtNumber, fmtPercent, fmtDuration, fmtTimeAgo } from '@/lib/format'
import { toneClass } from '@/lib/widget'
import { fetchDetailByKey } from '${moduleSpecifier}'${extraImports}

type Row = Record<string, unknown>

/** Auto-detect columns from the first row when explicit detailColumns aren't given. */
function autoColumns(rows: Row[]): ColumnDef<Row>[] {
  if (rows.length === 0) return [{ key: 'value', label: 'Value' }]
  return Object.entries(rows[0])
    .filter(([, v]) => v !== null && v !== undefined && typeof v !== 'object')
    .map(([k, v]) => ({
      key: k,
      label: k.replace(/([A-Z])/g, ' $1').replace(/^(.)/, (s: string) => s.toUpperCase()).trim(),
      ...(typeof v === 'number' && { align: 'right' as const }),
    }))
}
${detailView ? `
/** Safely extract a row array from any response shape (legacy fallback / bare arrays). */
function toRows(raw: unknown): Row[] {
  if (!raw) return []
  if (Array.isArray(raw)) return raw as Row[]
  if (typeof raw === 'object') {
    const obj = raw as Record<string, unknown>
    if (Array.isArray(obj.items)) return obj.items as Row[]
    if (Array.isArray(obj.data)) return obj.data as Row[]
    if (obj.data && typeof obj.data === 'object') return toRows(obj.data)
  }
  return []
}
` : ''}
export function ${componentName}DetailView() {
  const { key } = useParams<{ key: string }>()
  const { sdk, getToken } = useAuth()
  ${stateInit}
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!sdk || !key) return
    setLoading(true)
    fetchDetailByKey(sdk, key, getToken)
      ${fetchThen}
      .catch((err: unknown) => { setError(err instanceof Error ? err : new Error(String(err))); setLoading(false) })
  }, [sdk, key])

${body}
}
`
}

/**
 * Generate Dashboard.tsx and widgets/index.ts from resolved widget metadata.
 * @param {string} projectPath
 * @param {WidgetMeta[]} widgetMeta
 * @param {string} dashboardName
 */
export function generateDashboardFiles(projectPath, widgetMeta, dashboardName, dashboardDescription = '') {
  const widgetNames = widgetMeta.map(w => w.componentName)

  const kpis   = widgetMeta.filter(w => widgetLayoutGroup(w.template) === 'kpi')
  const charts = widgetMeta.filter(w => widgetLayoutGroup(w.template) === 'chart')
  const tables = widgetMeta.filter(w => widgetLayoutGroup(w.template) === 'table')

  const kpiCols = Math.min(kpis.length, 4)
  const kpiGrid = kpiCols === 1 ? 'grid-cols-1'
    : kpiCols === 2 ? 'grid-cols-1 sm:grid-cols-2'
    : kpiCols === 3 ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
    : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'

  const imports = widgetNames.map(n => `import { ${n} } from './widgets/${n}'`).join('\n')
  const indexTs = widgetNames.map(n => `export { ${n} } from './${n}'`).join('\n') + '\n'

  const kpiSection = kpis.length ? `
          {/* KPI row */}
          <div className="grid ${kpiGrid} gap-6">
            ${kpis.map(w => `<${w.componentName} />`).join('\n            ')}
          </div>` : ''

  const chartSection = charts.length ? `
          {/* Charts */}
          <div className="grid grid-cols-1 ${charts.length > 1 ? 'lg:grid-cols-2' : ''} gap-6 mt-10">
            ${charts.map(w => `<${w.componentName} />`).join('\n            ')}
          </div>` : ''

  const tableSection = tables.length ? `
          {/* Tables */}
          <div className="space-y-6 mt-10">
            ${tables.map(w => `<${w.componentName} />`).join('\n            ')}
          </div>` : ''

  const dashboardJsx = `import React from 'react'
import { Header } from '@/dashboard/chrome/Header'
${imports}

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-screen-2xl px-4 py-8 md:px-8 md:py-10">
        <Header title="${dashboardName}" description="${dashboardDescription || 'Operational metrics dashboard'}" />
${kpiSection}${chartSection}${tableSection}
      </div>
    </div>
  )
}
`
  writeAtomic(join(projectPath, 'src', 'dashboard', 'Dashboard.tsx'), dashboardJsx)
  writeAtomic(join(projectPath, 'src', 'dashboard', 'widgets', 'index.ts'), indexTs)
}

/**
 * Classify a widget template into its layout group for Dashboard.tsx grid placement.
 * @param {string} template
 * @returns {'kpi'|'table'|'chart'}
 */
export function widgetLayoutGroup(template) {
  if (template === 'kpi-card') return 'kpi'
  if (['data-table', 'ranked-table'].includes(template)) return 'table'
  return 'chart'
}

/**
 * Inject generated import and route blocks into App.tsx markers.
 * @param {string} projectPath
 * @param {string[]} viewWidgetNames - Widget names that have a generated view file
 */
export function injectAppRoutes(projectPath, viewWidgetNames, keyedViews = []) {
  const appPath = join(projectPath, 'src', 'App.tsx')
  if (!existsSync(appPath)) {
    emit('PARTIAL_BUILD_DETECTED', { message: 'App.tsx not found — scaffold may not be copied yet' })
    return
  }
  let content = readFileSync(appPath, 'utf8')

  const viewNames = viewWidgetNames

  const imports = [
    `import { Dashboard } from '@/dashboard/Dashboard'`,
    ...viewNames.map(n => `import { ${n}View } from '@/dashboard/views/${n}View'`),
    ...keyedViews.map(k => `import { ${k.componentName}DetailView } from '@/dashboard/views/${k.componentName}DetailView'`),
  ].join('\n')

  const routes = [
    `        <Route path="/" element={<Dashboard />} />`,
    ...viewNames.map(n => `        <Route path="/${n.toLowerCase()}" element={<${n}View />} />`),
    ...keyedViews.map(k => `        <Route path="${k.routeBase}/:key" element={<${k.componentName}DetailView />} />`),
  ].join('\n')

  content = content.replace(
    /\/\/ GENERATED_IMPORTS_START[\s\S]*?\/\/ GENERATED_IMPORTS_END/,
    `// GENERATED_IMPORTS_START\n${imports}\n// GENERATED_IMPORTS_END`
  )
  content = content.replace(
    /\{\/\* GENERATED_ROUTES_START \*\/\}[\s\S]*?\{\/\* GENERATED_ROUTES_END \*\/\}/,
    `{/* GENERATED_ROUTES_START */}\n${routes}\n        {/* GENERATED_ROUTES_END */}`
  )

  writeAtomic(appPath, content)
}

// ── Resolution Engine ──────────────────────────────────────────────────────────

/**
 * Validate a DashboardIntent object and return an array of error messages.
 * Returns an empty array when the intent is valid.
 * @param {DashboardIntent} intent
 * @returns {string[]}
 */
export function validateIntent(intent) {
  const errors = []
  if (intent.schemaVersion !== 2) errors.push('intent.json must have "schemaVersion": 2')
  if (!intent.dashboardName || typeof intent.dashboardName !== 'string') errors.push('dashboardName must be a non-empty string')
  if (!['1d', '7d', '30d', '90d'].includes(intent.timeRange)) errors.push(`timeRange must be one of: 1d, 7d, 30d, 90d`)
  if (!Array.isArray(intent.metrics) || intent.metrics.length === 0) errors.push('metrics must be a non-empty array')
  for (const m of (intent.metrics ?? [])) {
    if (!m.name) errors.push(`metric ${JSON.stringify(m.title ?? m)} missing name (needed to resolve its metrics/<name>.ts module)`)
    if (!['T1', 'T2', 'T3'].includes(m.tier)) errors.push(`metric "${m.name}" has invalid tier: ${m.tier}`)
    if (m.tier === 'T1' || m.tier === 'T2') {
      if (!m.title)  errors.push(`${m.tier} metric "${m.name}" missing title`)
    }
    if (m.tier === 'T2') {
      if (!m.params) {
        errors.push(`T2 metric "${m.name}" missing params`)
      }
    }
    if (m.tier === 'T3') {
      if (!m.title) errors.push(`T3 metric "${m.name}" missing title`)
      if (!m.displayAs) errors.push(`T3 metric "${m.name}" needs displayAs — valid values: ${VALID_DISPLAY_TYPES.join(', ')}`)
      else if (!VALID_DISPLAY_TYPES.includes(m.displayAs)) {
        errors.push(`T3 metric "${m.name}" has unsupported displayAs "${m.displayAs}". Valid: ${VALID_DISPLAY_TYPES.join(', ')}`)
      }
    }
    // Presentation hints (all tiers, all optional) — validate enums when present
    if (m.headlineMode && !VALID_HEADLINE_MODES.includes(m.headlineMode)) {
      errors.push(`metric "${m.name}" has invalid headlineMode "${m.headlineMode}". Valid: ${VALID_HEADLINE_MODES.join(', ')}`)
    }
    if (m.deltaPolarity && !VALID_DELTA_POLARITIES.includes(m.deltaPolarity)) {
      errors.push(`metric "${m.name}" has invalid deltaPolarity "${m.deltaPolarity}". Valid: ${VALID_DELTA_POLARITIES.join(', ')}`)
    }
    if (m.displayAs === 'rate-chart' && (!m.rateNum || !m.rateDen)) {
      errors.push(`rate-chart metric "${m.name}" needs rateNum and rateDen (the numerator/denominator field names its fnBody returns per bucket)`)
    }
    if (Array.isArray(m.detailColumns)) {
      for (const c of m.detailColumns) {
        if (!c.key || !c.label) errors.push(`metric "${m.name}" detailColumns entry missing key/label`)
        if (c.format && !VALID_COLUMN_FORMATS.includes(c.format)) {
          errors.push(`metric "${m.name}" detailColumns "${c.key}" has invalid format "${c.format}". Valid: ${VALID_COLUMN_FORMATS.join(', ')}`)
        }
      }
    }
    // Row-click drill-down config
    if (m.rowLink !== undefined && (typeof m.rowLink !== 'object' || !m.rowLink.key || typeof m.rowLink.key !== 'string')) {
      errors.push(`metric "${m.name}" rowLink must be an object with a string "key" (the row field used as the drill-down route param). The module must export fetchDetailByKey.`)
    }
    // Rich detail-view spec — throws with a precise message on any violation.
    validateDetailView(m)
  }
  return errors
}

/**
 * The module specifier a generated widget imports its data function from.
 * Default convention: metrics/<metric-name>.ts → '@/metrics/<metric-name>'.
 * An explicit `module` field (e.g. "metrics/custom.ts") overrides; the .ts is stripped.
 * @param {{ name: string, module?: string }} metric
 * @returns {string}
 */
export function metricModuleSpecifier(metric) {
  const rel = metric.module ?? `metrics/${metric.name}.ts`
  return '@/' + rel.replace(/\.ts$/, '')
}

/**
 * Look up a metric in the capability registry.
 * T3 metrics always resolve (they carry their own generation logic).
 * Returns null entry for unknown T1/T2 metrics (agent provides fnBody, registry lookup is for display hints only).
 * @param {IntentMetric} metric
 * @returns {{ tier: MetricTier, key: string, entry: object|null }}
 */
export function resolveMetric(metric) {
  if (metric.tier === 'T3') return { tier: 'T3', key: metric.name, entry: null }
  const registrySection = metric.tier === 'T1' ? REGISTRY.t1 : REGISTRY.t2
  const entry = registrySection[metric.name]
  if (!entry) {
    throw new Error(`Metric "${metric.name}" (${metric.tier}) not found in registry. Available: ${Object.keys(registrySection).join(', ')}`)
  }
  return { tier: metric.tier, key: metric.name, entry }
}

/**
 * Resolve a widget subtitle (CardDescription). Falls back to a window label.
 * @param {IntentMetric} metric
 * @param {object} defaults - registry entry defaults
 * @param {string} timeRange
 * @returns {string}
 */
function autoSubtitle(metric, defaults, timeRange) {
  const explicit = metric.subtitle ?? defaults.subtitle ?? metric.description ?? defaults.description
  if (explicit) return explicit
  const label = timeRangeLabel(timeRange)
  return label.charAt(0).toUpperCase() + label.slice(1)
}

/**
 * Compile a column spec into a TS array literal for RecordsTable.
 * Accepts either a ready literal string (passed through) or an array of
 * { key, label, align?, format?, color? } objects, for which it emits `render`
 * functions that format (number/percent/duration/timeAgo) and optionally colour cells.
 * @param {string|Array<object>} input
 * @returns {string}
 */
export function compileColumns(input) {
  if (typeof input === 'string') return input
  if (!Array.isArray(input) || input.length === 0) return '[{key:"name",label:"Name"}]'
  const cols = input.map((c) => {
    const parts = [`key:${JSON.stringify(c.key)}`, `label:${JSON.stringify(c.label)}`]
    if (c.align) parts.push(`align:${JSON.stringify(c.align)} as const`)
    const render = columnRender(c)
    if (render) parts.push(`render:${render}`)
    return `{${parts.join(',')}}`
  })
  return `[${cols.join(',')}]`
}

/**
 * Compile a metric's `detailView` spec into the imports + JSX for a rich
 * drill-down view. Chart sub-widgets render the matching primitive from
 * `@/dashboard/charts`; table sub-widgets render a titled Card wrapping a
 * RecordsTable. Each sub-widget reads its named source off `dataVar`
 * (the normalized `{ rows, byHook, ... }` map).
 * @param {{ widgets: Array<object> }} detailView
 * @param {string} [dataVar='d']
 * @returns {{ imports: Set<string>, jsx: string }}
 */
export function compileDetailWidgets(detailView, dataVar = 'd') {
  const imports = new Set()
  const blocks = []
  const CHART_IMPORT = {
    'donut-chart': 'Donut',
    'bar-chart': 'Bars',
    'area-chart': 'TrendArea',
    'line-chart': 'TrendArea',
    'multi-line-chart': 'MultiLine',
  }
  for (const w of (detailView.widgets ?? [])) {
    const srcExpr = `(${dataVar}[${JSON.stringify(w.source)}] ?? []) as Record<string, unknown>[]`
    if (DETAIL_CHART_TYPES.has(w.displayAs)) {
      const comp = CHART_IMPORT[w.displayAs]
      imports.add(`import { ${comp} } from '@/dashboard/charts'`)
      imports.add(`import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'`)
      const emptyProp = typeof w.emptyMessage === 'string' ? ` emptyMessage={${JSON.stringify(w.emptyMessage)}}` : ''
      let chartEl
      if (w.displayAs === 'multi-line-chart') {
        chartEl = `<MultiLine data={${srcExpr}} xKey={${JSON.stringify(w.xKey)}} series={${compileSeries(w.series)}}${emptyProp} />`
      } else if (w.displayAs === 'donut-chart') {
        chartEl = `<Donut data={${srcExpr}} nameKey={${JSON.stringify(w.xKey)}} valueKey={${JSON.stringify(w.yKey)}}${emptyProp} />`
      } else if (w.displayAs === 'bar-chart') {
        chartEl = `<Bars data={${srcExpr}} nameKey={${JSON.stringify(w.xKey)}} valueKey={${JSON.stringify(w.yKey)}}${emptyProp} />`
      } else if (w.displayAs === 'area-chart') {
        chartEl = `<TrendArea data={${srcExpr}} xKey={${JSON.stringify(w.xKey)}} yKey={${JSON.stringify(w.yKey)}}${emptyProp} />`
      } else { // line-chart
        chartEl = `<TrendArea data={${srcExpr}} xKey={${JSON.stringify(w.xKey)}} yKey={${JSON.stringify(w.yKey)}} area={false}${emptyProp} />`
      }
      blocks.push(`        <Card>
          <CardHeader><CardTitle>{${JSON.stringify(w.title)}}</CardTitle></CardHeader>
          <CardContent>
            ${chartEl}
          </CardContent>
        </Card>`)
    } else {
      // table sub-widget
      imports.add(`import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'`)
      imports.add(`import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'`)
      const colsExpr = w.columns ? compileColumns(w.columns) : `autoColumns(${srcExpr})`
      blocks.push(`        <Card>
          <CardHeader><CardTitle>{${JSON.stringify(w.title)}}</CardTitle></CardHeader>
          <CardContent>
            <RecordsTable rows={${srcExpr}} columns={${colsExpr}} />
          </CardContent>
        </Card>`)
    }
  }
  return { imports, jsx: blocks.join('\n') }
}

/**
 * Compile a multi-line-chart `series` spec into a TS array literal.
 * Accepts either a ready literal string (passed through) or an array of
 * `{ key, color, label? }` objects — the natural form an author writes in
 * intent.json. Without this, naive string coercion of the array writes the JS
 * default `[object Object],[object Object]` into the SERIES constant and tsc fails.
 * @param {string|Array<{key:string,color:string,label?:string}>} input
 * @returns {string}
 */
export function compileSeries(input) {
  if (typeof input === 'string') return input
  if (!Array.isArray(input) || input.length === 0) return '[{key:"value",color:"hsl(var(--chart-1))"}]'
  const items = input.map((s) => {
    const parts = [`key:${JSON.stringify(s.key)}`, `color:${JSON.stringify(s.color)}`]
    if (s.label) parts.push(`label:${JSON.stringify(s.label)}`)
    return `{${parts.join(',')}}`
  })
  return `[${items.join(',')}]`
}

/** Build a `render` function body for a column with `format` and/or `color`. Returns null if neither. */
function columnRender(c) {
  if (!c.format && !c.color) return null
  let valExpr
  switch (c.format) {
    case 'number':   valExpr = 'fmtNumber(Number(v))'; break
    case 'percent':  valExpr = 'fmtPercent(Number(v))'; break
    case 'duration': valExpr = 'fmtDuration(Number(v))'; break
    case 'timeAgo':  valExpr = 'fmtTimeAgo(String(v))'; break
    default:         valExpr = 'String(v ?? "—")'
  }
  if (c.color) {
    // color: 'goodHigh' (higher is better) | 'goodLow' (lower is better)
    return `(v:unknown)=>React.createElement('span',{className:toneClass(Number(v),${JSON.stringify(c.color)})},${valExpr})`
  }
  return `(v:unknown)=>${valExpr}`
}

/**
 * Build the spec passed to generateViewFile for a chart widget's detail view.
 * Shared by the fresh build and incremental ADD/CHANGE so detail views stay
 * consistent. Prefers a record-grain detailFnBody; falls back to the chart fnBody.
 * @param {string} componentName
 * @param {IntentMetric} metric
 * @param {object|null} entry - registry entry (for defaults)
 * @param {string} timeRange
 */
export function buildViewSpec(componentName, metric, entry, timeRange) {
  return {
    componentName,
    title: metric.title ?? entry?.defaults?.title ?? componentName,
    subtitle: autoSubtitle(metric, entry?.defaults ?? {}, timeRange),
    moduleSpecifier: metricModuleSpecifier(metric),
    detailExport: metric.detail === true ? 'fetchDetail' : 'fetchData',
    detailColumns: metric.detailColumns ? compileColumns(metric.detailColumns) : null,
    defaultSortKey: metric.detailSortKey,
    detailView: metric.detailView ?? entry?.defaults?.detailView ?? null,
  }
}

/**
 * Generate the TypeScript source for any widget file.
 * All tiers (T1, T2, T3) use fnBody — the agent writes the SDK call.
 * Registry provides display hints; agent provides the data fetching logic.
 * @param {IntentMetric} metric - Must have fnBody, displayAs (or registry template), title
 * @param {object|null} registryEntry - Registry entry for display hints (null for T3)
 * @param {'1d'|'7d'|'30d'|'90d'} [timeRange='30d']
 * @returns {string} Full TypeScript file content
 */
export function buildWidgetFile(metric, registryEntry = null, timeRange = '30d') {
  if (!metric.title)   throw new Error(`metric "${metric.name}" missing title`)

  const defaults    = registryEntry?.defaults ?? {}
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const displayAs   = metric.displayAs ?? registryEntry?.template
  const iconName    = metric.icon ?? defaults.icon ?? 'Activity'

  if (!displayAs) throw new Error(`metric "${metric.name}" needs displayAs`)

  const CHART_TYPES = new Set(['area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart'])

  // ── Chart path ─────────────────────────────────────────────────────────────
  if (CHART_TYPES.has(displayAs)) {
    const moduleSpecifier = metricModuleSpecifier(metric)
    const spec = {
      componentName,
      template:          displayAs,
      detailRoute:       metric.detailRoute ?? `/${componentName.toLowerCase()}`,
      icon:              iconName,
      title:             metric.title,
      subtitle:          autoSubtitle(metric, defaults, timeRange),
      dataHook:          'useWidgetData(fetchData, [])',
      hookImport:        [
                           "import { useWidgetData } from '@/hooks/useWidgetData'",
                           `import { fetchData } from '${moduleSpecifier}'`,
                         ].join('\n'),
      sdkImportLine:     '',
      responseTypeImport: '',
      dataSelector:      'data ?? []',
      xKey:              metric.xKey  ?? defaults.xKey  ?? 'date',
      yKey:              metric.yKey  ?? defaults.yKey  ?? 'value',
      headlineMode:      metric.headlineMode  ?? defaults.headlineMode  ?? 'sum',
      deltaPolarity:     metric.deltaPolarity ?? defaults.deltaPolarity ?? 'neutral',
      rateNum:           metric.rateNum ?? defaults.rateNum ?? 'num',
      rateDen:           metric.rateDen ?? defaults.rateDen ?? 'den',
      series:            compileSeries(metric.series ?? defaults.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]'),
      pivotExpression:   metric.pivotExpression ?? defaults.pivotExpression ?? 'rawData',
      emptyMessage:      metric.emptyMessage ?? defaults.emptyMessage ?? 'No data',
    }
    return applyTemplate(spec.template, specToSubs(spec))
  }

  // ── KPI / table path (shell template) ──────────────────────────────────────
  const t3ShellPath = t3ShellTemplatePath()
  if (!existsSync(t3ShellPath)) {
    throw new Error(`T3 shell template not found at ${t3ShellPath}`)
  }
  // No explicit columns → emit an empty literal; the widget auto-detects columns
  // from the actual row data at runtime (real keys + labels), instead of a static
  // name/value placeholder that renders every cell as "—".
  const columns      = compileColumns(metric.columnDefs ?? metric.columns ?? defaults.columnDefs ?? defaults.columns ?? '[]')
  const valueField   = metric.valueField ?? defaults.valueField ?? ''
  const valueLabel   = metric.valueLabel ?? defaults.valueLabel ?? ''
  const previousField = metric.previousField ?? defaults.previousField ?? ''
  const deltaPolarity = metric.deltaPolarity ?? defaults.deltaPolarity ?? 'neutral'
  const rowLinkKey   = metric.rowLink?.key ?? defaults.rowLink?.key ?? ''
  const rowLinkRoute = rowLinkKey ? `/${componentName.toLowerCase()}` : ''
  const defaultSortAsc = metric.defaultSortAsc === true ? 'true' : 'false'
  const emptyMessage = metric.emptyMessage ?? defaults.emptyMessage ?? 'No data'
  const subtitle     = autoSubtitle(metric, defaults, timeRange)

  let content = readFileSync(t3ShellPath, 'utf8')
  content = content
    .split('<<METRIC_IMPORT>>').join(`import { fetchData } from '${metricModuleSpecifier(metric)}'`)
    .split('<<COMPONENT_NAME>>').join(componentName)
    .split('<<TITLE>>').join(metric.title ?? componentName)
    .split('<<DESCRIPTION>>').join(subtitle)
    .split('<<ICON_NAME>>').join(iconName)
    .split('<<DISPLAY_AS>>').join(displayAs ?? 'ranked-table')
    .split('<<COLUMNS>>').join(columns)
    .split('<<VALUE_FIELD>>').join(valueField)
    .split('<<VALUE_LABEL>>').join(valueLabel)
    .split('<<PREVIOUS_FIELD>>').join(previousField)
    .split('<<DELTA_POLARITY>>').join(deltaPolarity)
    .split('<<ROW_LINK_KEY>>').join(rowLinkKey)
    .split('<<ROW_LINK_ROUTE>>').join(rowLinkRoute)
    .split('<<DEFAULT_SORT_ASC>>').join(defaultSortAsc)
    .split('<<EMPTY_MESSAGE>>').join(emptyMessage)
  return content
}

/**
 * Convert a WidgetSpec to the substitution map used by applyTemplate.
 * @param {WidgetSpec} spec
 * @returns {Record<string, string>}
 */
function specToSubs(spec) {
  return {
    COMPONENT_NAME: spec.componentName,
    TITLE: spec.title,
    SUBTITLE: spec.subtitle,
    DETAIL_ROUTE: spec.detailRoute,
    ICON: spec.icon,
    DATA_HOOK: spec.dataHook,
    DATA_SELECTOR: spec.dataSelector,
    X_KEY: spec.xKey,
    Y_KEY: spec.yKey,
    DATA_KEY: spec.yKey,
    NAME_KEY: spec.xKey,
    HEADLINE_MODE: spec.headlineMode,
    DELTA_POLARITY: spec.deltaPolarity,
    RATE_NUM: spec.rateNum,
    RATE_DEN: spec.rateDen,
    SERIES: spec.series,
    PIVOT_EXPRESSION: spec.pivotExpression,
    EMPTY_MESSAGE: spec.emptyMessage ?? 'No data',
    SDK_IMPORT_LINE: spec.sdkImportLine ?? '',
    RESPONSE_TYPE_IMPORT: spec.responseTypeImport ?? '',
    HOOK_IMPORT: spec.hookImport ?? "import { useWidgetData } from '@/hooks/useWidgetData'",
  }
}

// ── Build pipelines ────────────────────────────────────────────────────────────

/**
 * Parse tsc error output to find which widget file caused the error.
 * Falls back to defaultName if the path can't be extracted.
 * @param {string} tscOutput
 * @param {string} defaultName
 * @returns {string}
 */
function widgetNameFromTscErrors(tscOutput, defaultName) {
  const match = tscOutput.match(/widgets[/\\](\w+)\.tsx\(\d+/)
  return match?.[1] ?? defaultName
}

/**
 * Kill a previously-started dev server using the PID stored in a file.
 * Cross-platform: taskkill /T on Windows (kills process tree), SIGTERM on Unix.
 * Waits up to 1500ms for the port to become free after killing.
 * @param {string} pidFile - Absolute path to the .pid file
 * @returns {Promise<void>}
 */
async function killPreviousDevServer(pidFile) {
  if (!existsSync(pidFile)) return

  let pid
  try {
    pid = parseInt(readFileSync(pidFile, 'utf8').trim(), 10)
  } catch { return }

  if (!pid || isNaN(pid)) return

  try {
    if (process.platform === 'win32') {
      // /T kills the entire process tree (npm → node → Vite); /F forces termination
      execSync(`taskkill /PID ${pid} /T /F`, { stdio: 'pipe' })
    } else {
      process.kill(pid, 'SIGTERM')
    }
  } catch { /* process already dead — ignore */ }

  // Wait for port to become free (up to 1500ms)
  const deadline = Date.now() + 1500
  while (Date.now() < deadline) {
    const stillOpen = await new Promise(resolve => {
      const socket = createConnection({ port: DASHBOARD_PORT, host: 'localhost' })
      socket.once('connect', () => { socket.destroy(); resolve(true) })
      socket.once('error', () => resolve(false))
      socket.setTimeout(300, () => { socket.destroy(); resolve(false) })
    })
    if (!stillOpen) break
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 200)
  }

  try { unlinkSync(pidFile) } catch { /* ignore */ }
}

/**
 * Main intent.json build pipeline.
 * @param {DashboardIntent} intent
 * @param {string} intentPath - Absolute path to intent.json on disk (for re-reads)
 * @returns {Promise<void>}
 */
async function runDashboardBuild(intent, intentPath) {
  const {
    dashboardName, timeRange, metrics,
    projectDir, orgName, tenantName, cloudUrl, apiUrl, clientId = '', dashboardDescription = '',
    routingName,
  } = intent

  if (!projectDir) fail('intent.projectDir is required')
  if (!routingName) fail('intent.routingName is required')

  const P = resolve(projectDir)
  const BUILD_SENTINEL = join(P, '.build-in-progress')

  if (existsSync(BUILD_SENTINEL)) {
    emit('PARTIAL_BUILD_DETECTED', { projectDir: P })
  }
  writeAtomic(BUILD_SENTINEL, String(Date.now()))

  try {
    // Step 1 — Scaffold (the agent extracts the starter-kit zip into the project
    // before building; the skill ships no zip code). Verify it's present, then
    // point widget generation at the kit's _gen/widgets templates.
    assertScaffoldExtracted(P)
    setWidgetsDir(join(P, '_gen', 'widgets'))
    emit('SCAFFOLD_READY')

    // Step 2 — Env
    // Public, non-secret SPA config (auth is OAuth PKCE — non-confidential client ID,
    // never a PAT/secret). Written to BOTH .env.local (dev) and .env.production so that
    // `vite build` still has the SDK config even though the deploy flow renames
    // .env.local away to strip any dev PAT. Without .env.production the deployed bundle
    // has no config and throws "UiPath SDK configuration not found" at runtime.
    const publicEnv = [
      `VITE_UIPATH_CLOUD_URL=${cloudUrl}`,
      `VITE_UIPATH_BASE_URL=${apiUrl}`,
      `VITE_UIPATH_ORG_NAME=${orgName}`,
      `VITE_UIPATH_TENANT_NAME=${tenantName}`,
      `VITE_UIPATH_CLIENT_ID=${clientId}`,
      `VITE_UIPATH_SCOPE=${DASHBOARD_SCOPES}`,
    ]
    writeAtomic(join(P, '.env.local'), [...publicEnv, `VITE_DEV_PORT=${DASHBOARD_PORT}`].join('\n'))
    writeAtomic(join(P, '.env.production'), publicEnv.join('\n') + '\n')
    const uipathJsonPath = join(P, 'uipath.json')
    if (existsSync(uipathJsonPath) && clientId) {
      const uj = JSON.parse(readFileSync(uipathJsonPath, 'utf8'))
      uj.clientId = clientId
      writeAtomic(uipathJsonPath, JSON.stringify(uj, null, 2))
    }
    emit('ENV_WRITTEN')

    // Warn if clientId is missing — dashboard auth will fail at runtime without it
    if (!clientId) {
      emit('AUTH_MISSING', { var: 'clientId', message: 'No external OAuth app client ID provided. Dashboard will fail to authenticate in the browser. Run Phase 4.5 to provision one.' })
      log('⚠ Warning: clientId is empty — dashboard auth will not work. See Phase 4.5 in build plugin docs.')
    }

    // Write partial state.json early so deploy can find app metadata even if build fails
    const stateDir = join(P, '.dashboard')
    mkdirSync(stateDir, { recursive: true })
    const statePath = join(stateDir, 'state.json')
    const existingState = existsSync(statePath) ? JSON.parse(readFileSync(statePath, 'utf8')) : {}
    const buildDrift = existsSync(statePath) ? scaffoldDrift(existingState) : null
    if (buildDrift) emit('UPGRADE_AVAILABLE', buildDrift)
    const partialState = {
      schemaVersion: STATE_SCHEMA_VERSION,
      versions: buildVersions(null),
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0', description: dashboardDescription },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
      timeRange,
      widgets: existingState.widgets ?? {},
      deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
      buildStatus: 'in-progress',
    }
    writeAtomic(statePath, JSON.stringify(partialState, null, 2))

    // Step 3 — Pre-warm guarantee
    const LOCK_SIGNAL = join(P, 'node_modules', '.package-lock.json')
    const PREWARM_LOCK_PATH = join(P, '.prewarm.lock')
    if (!existsSync(LOCK_SIGNAL)) {
      if (existsSync(PREWARM_LOCK_PATH)) {
        log('⏳ Waiting for pre-warm…')
        waitForPrewarm(P)
      } else {
        log('⚙ Installing dependencies…')
        await runPrewarm(P)
      }
    } else {
      emit('PREWARM_DONE')
    }

    // Step 3.5 — SDK version floor (agent-memory/governance subpaths need ≥ MIN_SDK_VERSION)
    const sdkCheck = checkSdkVersion(P)
    if (!sdkCheck.ok) {
      fail(
        `Installed @uipath/uipath-typescript ${sdkCheck.version ?? '(not found)'} is below the required ${MIN_SDK_VERSION} ` +
        `(agent/governance metrics need the agent-memory and governance subpaths). ` +
        `Fix: delete ${join(P, 'package-lock.json')} and ${join(P, 'node_modules')}, then re-run the pre-warm.`
      )
    }

    // Step 3.6 — Copy agent-authored metric modules into the project and
    // type-check them in isolation (Stage A) before generating any widget.
    // A failure here maps directly to a metrics/<name>.ts file — fast, no React.
    const intentDir = dirname(intentPath)
    const metricsDestDir = join(P, 'src', 'metrics')
    mkdirSync(metricsDestDir, { recursive: true })
    for (const metric of metrics) {
      const rel = metric.module ?? `metrics/${metric.name}.ts`
      const fromPath = join(intentDir, rel)
      if (!existsSync(fromPath)) {
        fail(`Metric module not found: ${fromPath} — write the data function as metrics/${metric.name}.ts exporting "fetchData"`)
      }
      copyFileSync(fromPath, join(metricsDestDir, basename(rel)))
    }
    const stageA = runMetricsTypecheck(P)
    if (!stageA.ok) {
      emit('METRICS_RETRY', { files: stageA.files, errors: stageA.errors, intentPath })
      log(`⚠ Metric modules have TypeScript errors. Fix the named files in ${metricsDestDir} and re-run.`)
      process.exit(2)
    }
    emit('METRICS_PASS')

    // Step 4 — Resolve + generate widgets
    const widgetHashes = {}
    const widgetMeta = []    // { componentName, template }
    const widgetSpecs = {}   // componentName → view spec (see buildViewSpec); chart widgets only
    const keyedSpecs = {}    // componentName → keyed detail spec; table widgets with rowLink
    let widgetIndex = 0
    const total = metrics.length

    // All widgets generated together — T1, T2, T3 in one pass (no per-widget tsc)
    // Metric-level errors were already caught by Stage A above; Step 6 is the integration backstop.
    for (const metric of metrics) {
      const isT3 = metric.tier === 'T3'
      const { entry } = isT3 ? { entry: null } : resolveMetric(metric)

      let widgetContent
      try {
        widgetContent = buildWidgetFile(metric, entry, timeRange)
      } catch (e) {
        if (isT3) emit('T3_FAILED', { widget: metric.name, reason: e.message })
        fail(`Widget "${metric.name}" could not be generated: ${e.message}`)
      }

      const displayAs = metric.displayAs ?? entry?.template ?? 'data-table'
      const componentName = metric.componentName ?? toPascalCase(metric.name)
      const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
      writeAtomic(widgetPath, widgetContent)

      // intentMetric is persisted so incremental CHANGE/REBUILD can regenerate
      // the widget without the original intent.json (fnBody, title, hints).
      widgetHashes[componentName] = { hash: hashContent(widgetContent), tier: metric.tier, metric: metric.name, template: displayAs, module: metric.module ?? `metrics/${metric.name}.ts`, intentMetric: metric }
      widgetMeta.push({ componentName, template: displayAs })

      // Detail views: only chart widgets emit navigate/ViewAllLink (the shell
      // template for KPI/table links nowhere), so only charts need a generated
      // view + route — any tier. Columns are auto-detected at runtime in the view.
      if (widgetLayoutGroup(displayAs) === 'chart') {
        widgetSpecs[componentName] = buildViewSpec(componentName, metric, entry, timeRange)
      }

      // Row-click drill-down: a table widget with `rowLink` gets a keyed detail
      // view at /<widget>/:key that calls the module's fetchDetailByKey.
      // rowLink + detailView fall back to the registry entry's defaults (same as
      // title/columns), so a cataloged metric ships its drill-down + rich charts
      // without the intent restating them.
      const keyedRowLink = metric.rowLink ?? entry?.defaults?.rowLink
      if (keyedRowLink?.key && widgetLayoutGroup(displayAs) === 'table') {
        keyedSpecs[componentName] = {
          componentName,
          title: metric.title ?? entry?.defaults?.title ?? componentName,
          subtitle: autoSubtitle(metric, entry?.defaults ?? {}, timeRange),
          moduleSpecifier: metricModuleSpecifier(metric),
          detailColumns: metric.detailColumns ? compileColumns(metric.detailColumns) : null,
          detailView: metric.detailView ?? entry?.defaults?.detailView ?? null,
          routeBase: `/${componentName.toLowerCase()}`,
        }
      }

      widgetIndex++
      emit('WIDGET_READY', { name: componentName, index: widgetIndex, total })
    }

    // Step 5 — Generate Dashboard.tsx + index.ts
    generateDashboardFiles(P, widgetMeta, dashboardName, dashboardDescription)

    // Step 5a — Generate view files (widgetSpecs is chart-only; every chart links to its view)
    const generatedViewNames = []
    for (const [componentName, spec] of Object.entries(widgetSpecs)) {
      const viewContent = generateViewFile(spec)
      writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`), viewContent)
      generatedViewNames.push(componentName)
    }

    // Step 5a.2 — Generate keyed detail views for tables with rowLink
    const keyedViewWidgets = []
    for (const [componentName, spec] of Object.entries(keyedSpecs)) {
      const viewContent = generateKeyedDetailViewFile(spec)
      writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}DetailView.tsx`), viewContent)
      keyedViewWidgets.push({ componentName, routeBase: spec.routeBase })
    }

    // Step 5b — Only inject routes for widgets that actually have view files
    injectAppRoutes(P, generatedViewNames, keyedViewWidgets)

    // Step 6 — Full-app tsc backstop. Metric-level errors were already caught by
    // Stage A; a failure here is an integration/template error, not a metric bug.
    try {
      execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
      emit('TSC_PASS')
    } catch (e) {
      const tscOut = e.stdout?.toString() ?? ''
      const err = tscOut || e.stderr?.toString() || String(e)
      emit('TSC_FAIL', { errors: err.slice(0, 1000) })
      fail(`TypeScript errors:\n${err}`)
    }

    // Step 7 — Write final state.json (upgrade partial → complete)
    const newState = {
      schemaVersion: STATE_SCHEMA_VERSION,
      versions: buildVersions(sdkCheck.version),
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0', description: dashboardDescription },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
      timeRange,
      widgets: widgetHashes,
      deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
      buildStatus: 'complete',
    }
    writeAtomic(statePath, JSON.stringify(newState, null, 2))

    // Step 8 — Clean up any server a PREVIOUS script version spawned (legacy
    // pid file). The script itself no longer starts the dev server: a detached
    // child here outlives the session and leaks. The calling agent starts
    // `npm run dev` as a tracked background job instead (see build impl.md).
    const serverPidFile = join(P, '.dashboard', 'server.pid')
    await killPreviousDevServer(serverPidFile)
    try { unlinkSync(serverPidFile) } catch { /* ignore */ }

    emit('BUILD_RESULT', {
      success: true, projectDir: P, port: DASHBOARD_PORT,
      previewUrl: `http://localhost:${DASHBOARD_PORT}`,
      widgets: Object.keys(widgetHashes),
      dashboardName,
      serverStart: `npm run dev -- --port ${DASHBOARD_PORT}`,
    })

  } finally {
    try { unlinkSync(BUILD_SENTINEL) } catch { /* ignore */ }
  }
}

/**
 * Validate an edit-intent.json and normalize it to a batch.
 * Accepts either a single operation ({ op, ... } — legacy shape) or a batch
 * ({ ops: [{ op, ... }, ...] }). Throws for unknown operation types.
 * @param {{ projectDir: string, op?: string, ops?: Array<object>, target?: string, metric?: IntentMetric, delta?: object }} editIntent
 * @returns {{ projectDir: string, ops: Array<{ op: string, target?: string, metric?: IntentMetric, delta?: object }> }}
 */
export function classifyEditIntent(editIntent) {
  const ops = Array.isArray(editIntent.ops)
    ? editIntent.ops
    : [{ op: editIntent.op, target: editIntent.target, metric: editIntent.metric, delta: editIntent.delta }]
  if (ops.length === 0) throw new Error('classifyEditIntent: ops array is empty')
  ops.forEach((o, i) => {
    if (!VALID_EDIT_OPS.includes(o.op)) {
      throw new Error(`classifyEditIntent: invalid op "${o.op}" (ops[${i}]). Must be one of: ${VALID_EDIT_OPS.join(', ')}`)
    }
  })
  return { projectDir: editIntent.projectDir, ops }
}

/**
 * Build the metric used to regenerate a widget for a CHANGE op.
 * Starts from the persisted intentMetric (full metadata: title/displayAs/hints) and merges
 * the delta on top. Falls back to a minimal ref for legacy state files that
 * predate intentMetric persistence — then the delta itself must carry title + displayAs.
 * The data-fetch code lives in the metric module on disk (resolved by name); it is not part of this ref.
 * @param {object|undefined} stored - state.widgets[target]
 * @param {string} target - widget component name
 * @param {object|undefined} delta - fields to change
 * @returns {IntentMetric}
 */
export function resolveChangeMetric(stored, target, delta) {
  const base = stored?.intentMetric ?? { name: stored?.metric ?? target.toLowerCase(), tier: stored?.tier ?? 'T1' }
  return { ...base, ...(delta ?? {}) }
}

/**
 * Copy a metric's module file from the edit's sibling `metrics/` dir into the
 * project's `src/metrics/`. Returns true if a file was copied, false if the edit
 * supplied none (CHANGE may legitimately supply none — the existing module stays).
 * @param {string} intentDir - directory containing the edit-intent.json
 * @param {string} projectPath
 * @param {{ name: string, module?: string }} metric
 * @returns {boolean}
 */
function copyMetricModule(intentDir, projectPath, metric) {
  const rel = metric.module ?? `metrics/${metric.name}.ts`
  const fromPath = join(intentDir, rel)
  if (!existsSync(fromPath)) return false
  const destDir = join(projectPath, 'src', 'metrics')
  mkdirSync(destDir, { recursive: true })
  copyFileSync(fromPath, join(destDir, basename(rel)))
  return true
}

/**
 * Apply one or more incremental edits (ADD / REMOVE / CHANGE / REBUILD) to an
 * existing project in a single pass: every op is validated up front (nothing is
 * written if any op would fail), then all ops apply, then Dashboard.tsx/index.ts
 * regenerate ONCE and tsc runs ONCE.
 * @param {{ projectDir: string, op?: string, ops?: Array<object> }} editIntent
 * @param {string} intentPath
 * @returns {Promise<void>}
 */
async function runIncrementalEdit(editIntent, intentPath) {
  const { projectDir } = editIntent
  if (!projectDir) fail('edit-intent.projectDir is required')
  const P = resolve(projectDir)
  const intentDir = dirname(intentPath)
  const statePath = join(P, '.dashboard', 'state.json')
  if (!existsSync(statePath)) fail('No .dashboard/state.json found. Run a fresh build first.')
  // The starter kit must still be extracted in the project (the widget generator
  // templates live in <proj>/_gen/widgets). Verify + point the generator at them —
  // without this, ADD/CHANGE/REBUILD crash at widgetsDir().
  assertScaffoldExtracted(P)
  setWidgetsDir(join(P, '_gen', 'widgets'))
  const state = JSON.parse(readFileSync(statePath, 'utf8'))
  const editDrift = scaffoldDrift(state)
  if (editDrift) emit('UPGRADE_AVAILABLE', editDrift)
  if (state.buildStatus === 'in-progress') {
    log('⚠ Warning: Previous build did not complete — widgets may be missing. Consider running a full build first.')
  }
  const { ops } = classifyEditIntent(editIntent)
  const timeRange = state.timeRange ?? '30d'

  // Project-wide upgrade — runs instead of the per-widget batch loop.
  if (ops.length === 1 && ops[0].op === 'UPGRADE') {
    await runUpgrade(P, state, intentPath)
    return
  }

  // ── Pre-validate the whole batch — fail BEFORE any write ────────────────────
  const violations = []
  for (const [i, o] of ops.entries()) {
    if (o.op === 'REMOVE' || o.op === 'CHANGE') {
      if (!o.target) { violations.push(`ops[${i}] ${o.op}: missing target`); continue }
      const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${o.target}.tsx`)
      const currentContent = existsSync(widgetPath) ? readFileSync(widgetPath, 'utf8') : null
      const stored = state.widgets?.[o.target]
      if (currentContent && stored && hashContent(currentContent) !== stored.hash) {
        emit('HAND_EDIT_DETECTED', { widget: o.target })
        violations.push(`ops[${i}] ${o.op} "${o.target}": hand-edited — overwriting would lose changes`)
      }
      if (o.op === 'CHANGE') {
        const metricRef = resolveChangeMetric(stored, o.target, o.delta)
        const rel = metricRef.module ?? `metrics/${metricRef.name}.ts`
        const provided = existsSync(join(intentDir, rel))
        const existing = existsSync(join(P, 'src', 'metrics', basename(rel)))
        if (!provided && !existing) {
          violations.push(`ops[${i}] CHANGE "${o.target}": no metric module found — provide metrics/${metricRef.name}.ts in the edit, or re-run a fresh build`)
        }
      }
    }
    if (o.op === 'ADD') {
      if (!o.metric?.name) { violations.push(`ops[${i}] ADD: missing metric`); continue }
      try { resolveMetric(o.metric) } catch (e) { violations.push(`ops[${i}] ADD "${o.metric.name}": ${e.message}`) }
      const rel = o.metric.module ?? `metrics/${o.metric.name}.ts`
      if (!existsSync(join(intentDir, rel))) {
        violations.push(`ops[${i}] ADD "${o.metric.name}": metric module not found — write ${rel} exporting "fetchData"`)
      }
    }
  }
  if (violations.length > 0) {
    fail(`Batch rejected — nothing was changed:\n${violations.map(v => '  • ' + v).join('\n')}`)
  }

  // ── Apply every op ───────────────────────────────────────────────────────────
  const applied = []
  for (const { op, target, metric, delta } of ops) {

  if (op === 'ADD') {
    const { tier, entry } = resolveMetric(metric)
    const componentName = metric.componentName ?? toPascalCase(metric.name)
    copyMetricModule(intentDir, P, metric)
    const widgetContent = buildWidgetFile(metric, entry, timeRange)
    const addTemplate = metric.displayAs ?? entry?.template ?? 'data-table'
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
    writeAtomic(widgetPath, widgetContent)
    state.widgets = state.widgets ?? {}
    state.widgets[componentName] = { hash: hashContent(widgetContent), tier, metric: metric.name, template: addTemplate, module: metric.module ?? `metrics/${metric.name}.ts`, intentMetric: metric }
    // Chart widgets emit a drill-down link — generate the detail view so the route resolves
    if (widgetLayoutGroup(addTemplate) === 'chart') {
      const viewContent = generateViewFile(buildViewSpec(componentName, metric, entry, timeRange))
      writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`), viewContent)
    }
    // Table with rowLink → generate its keyed row-click detail view
    writeKeyedViewIfRowLink(P, componentName, metric, entry, timeRange)

  } else if (op === 'REMOVE') {
    const stored = state.widgets?.[target]
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    if (existsSync(widgetPath)) unlinkSync(widgetPath)
    const viewPath = join(P, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (existsSync(viewPath)) unlinkSync(viewPath)
    const moduleRel = stored?.module ?? `metrics/${stored?.metric ?? target.toLowerCase()}.ts`
    const modulePath = join(P, 'src', 'metrics', basename(moduleRel))
    if (existsSync(modulePath)) unlinkSync(modulePath)
    if (state.widgets) delete state.widgets[target]

  } else if (op === 'CHANGE') {
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    const stored = state.widgets?.[target]
    const metricRef = resolveChangeMetric(stored, target, delta)
    copyMetricModule(intentDir, P, metricRef)
    const tier = metricRef.tier ?? stored?.tier ?? 'T1'
    const { entry } = resolveMetric(metricRef)
    const widgetContent = buildWidgetFile(metricRef, entry, delta?.timeRange ?? timeRange)
    writeAtomic(widgetPath, widgetContent)
    const changeTemplate = metricRef.displayAs ?? entry?.template ?? stored?.template ?? 'data-table'
    if (state.widgets) state.widgets[target] = { hash: hashContent(widgetContent), tier, metric: metricRef.name, template: changeTemplate, module: metricRef.module ?? `metrics/${metricRef.name}.ts`, intentMetric: metricRef }
    // Keep the detail view in sync: regenerate for charts, drop it if no longer a chart
    const changeViewPath = join(P, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (widgetLayoutGroup(changeTemplate) === 'chart') {
      const viewContent = generateViewFile(buildViewSpec(target, metricRef, entry, delta?.timeRange ?? timeRange))
      writeAtomic(changeViewPath, viewContent)
    } else if (existsSync(changeViewPath)) {
      unlinkSync(changeViewPath)
    }
    // Sync the keyed row-click detail view (adds it if rowLink was set, removes a stale one)
    writeKeyedViewIfRowLink(P, target, metricRef, entry, delta?.timeRange ?? timeRange)

  } else if (op === 'REBUILD') {
    // Regenerate every widget (and chart detail view) from the persisted intentMetric.
    // Useful after scaffold/template updates. Legacy entries without intentMetric are skipped.
    rebuildAllWidgets(P, state, timeRange)
  }

  applied.push({ op, widget: target ?? (metric ? (metric.componentName ?? toPascalCase(metric.name)) : undefined) })
  } // end apply loop

  // Regenerate Dashboard.tsx + index.ts — ONCE for the whole batch
  const widgetMeta = Object.entries(state.widgets ?? {}).map(([name, info]) => ({
    componentName: name,
    template: info.template ?? 'ranked-table',
  }))
  generateDashboardFiles(P, widgetMeta, state.app?.name ?? 'Dashboard', state.app?.description ?? '')

  // Re-inject App.tsx routes — chart views + keyed row-click detail views on disk
  const viewNames = Object.keys(state.widgets ?? {}).filter(name =>
    existsSync(join(P, 'src', 'dashboard', 'views', `${name}View.tsx`))
  )
  injectAppRoutes(P, viewNames, collectKeyedViews(P, state))

  // Stage A — re-type-check metric modules in isolation after the batch.
  const stageA = runMetricsTypecheck(P)
  if (!stageA.ok) {
    emit('METRICS_RETRY', { files: stageA.files, errors: stageA.errors, intentPath })
    log(`⚠ Metric modules have TypeScript errors. Fix the named files in ${join(P, 'src', 'metrics')} and re-run.`)
    process.exit(2)
  }

  // tsc validate
  try {
    execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
    emit('TSC_PASS')
  } catch (e) {
    const err = e.stdout?.toString() || ''
    emit('TSC_FAIL', { errors: err.slice(0, 500) })
    fail(`TypeScript errors after edit:\n${err}`)
  }

  state.schemaVersion = STATE_SCHEMA_VERSION
  state.versions = buildVersions(checkSdkVersion(P).version)
  writeAtomic(statePath, JSON.stringify(state, null, 2))
  emit('INCREMENTAL_READY', { count: applied.length, ops: applied })
}

// ── Entry point ────────────────────────────────────────────────────────────────

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {

  // --prewarm <routingName> mode: run npm ci in an already-extracted project, then exit.
  // The agent extracts the starter-kit zip into <cwd>/<routingName> first.
  if (process.argv[2] === '--prewarm' && process.argv[3]) {
    const routingName = process.argv[3]
    const prewarmDir  = join(process.cwd(), routingName)
    assertScaffoldExtracted(prewarmDir)
    await runPrewarm(prewarmDir)
    process.exit(0)
  }

  const planArg = process.argv[2]
  if (!planArg) fail('Usage: node build-dashboard.mjs <intent.json|edit-intent.json>')

  let plan
  try {
    plan = JSON.parse(readFileSync(planArg, 'utf8'))
  } catch (e) {
    fail(`Could not read plan JSON from ${planArg}: ${e.message}`)
  }

  if (plan.metrics) {
    const intentErrors = validateIntent(plan)
    if (intentErrors.length > 0) fail(`Invalid intent.json:\n${intentErrors.map(e => '  • ' + e).join('\n')}`)
    await runDashboardBuild(plan, planArg)
  } else if (plan.op || plan.ops) {
    classifyEditIntent(plan)
    await runIncrementalEdit(plan, planArg)
  } else {
    fail('Unrecognised input format. Expected intent.json (has "metrics") or edit-intent.json (has "op").')
  }

} // end entry-point guard
