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

import { readFileSync, writeFileSync, copyFileSync, mkdirSync, readdirSync, existsSync, renameSync, unlinkSync, rmSync } from 'fs'
import { createConnection } from 'net'
import { join, dirname, resolve } from 'path'
import { fileURLToPath, pathToFileURL } from 'url'
import { execSync, spawn } from 'child_process'
import { createHash } from 'crypto'

// ── Path constants ─────────────────────────────────────────────────────────────

const __dirname = dirname(fileURLToPath(import.meta.url))
const SCAFFOLD_DIR = resolve(__dirname, '../templates/dashboard/scaffold')
const WIDGETS_DIR = resolve(__dirname, '../templates/dashboard/widgets')
const T3_SHELL_TEMPLATE_PATH = resolve(__dirname, '../templates/dashboard/widgets/t3-shell.tsx.template')

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

const TIME_CONSTANTS = `const NOW = new Date()
const ONE_DAY_AGO = new Date(Date.now() - 86_400_000)
const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000)
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000)
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000)
`

const KNOWN_EVENTS = new Set([
  'PREWARM_START', 'PREWARM_DONE', 'PREWARM_FAILED', 'SCAFFOLD_READY', 'ENV_WRITTEN',
  'WIDGET_READY', 'T3_RETRY', 'T3_FAILED', 'TSC_PASS', 'TSC_FAIL',
  'SERVER_READY', 'BUILD_RESULT', 'PARTIAL_BUILD_DETECTED', 'AUTH_MISSING',
  'HAND_EDIT_DETECTED', 'T2_SCHEMA_ERROR', 'INCREMENTAL_READY',
])

const VALID_EDIT_OPS = ['ADD', 'REMOVE', 'CHANGE', 'REBUILD']

/**
 * Display types supported for all widget tiers.
 * Table/KPI types use t3-shell.tsx.template.
 * Chart types use the standard chart templates with customDataFn injected.
 */
export const VALID_DISPLAY_TYPES = [
  'kpi-card', 'ranked-table', 'data-table',
  'area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart',
]

/** Headline aggregate modes — how a chart's big number is computed from its series. */
export const VALID_HEADLINE_MODES = ['sum', 'avg', 'latest', 'count', 'max', 'min']

/** Delta polarity — whether an increase is good, bad, or neutral (drives badge colour). */
export const VALID_DELTA_POLARITIES = ['up-good', 'up-bad', 'neutral']

/** Column value formatters supported in table column defs. */
export const VALID_COLUMN_FORMATS = ['number', 'percent', 'duration', 'timeAgo', 'text']

/**
 * Minimum SDK version the catalog metrics require — the agent-memory and
 * governance subpaths ship in 1.4.0. A stale lockfile/registry otherwise
 * surfaces as cryptic tsc "module not found" failures mid-build.
 */
export const MIN_SDK_VERSION = '1.4.0'

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
const DASHBOARD_SCOPES = 'OR.Assets OR.Jobs OR.Folders OR.Buckets OR.Execution OR.Tasks OR.Queues OR.Users Insights Insights.RealTimeData'

// ── Low-level utilities ────────────────────────────────────────────────────────

function fail(msg) {
  process.stderr.write(`ERROR: ${msg}\n`)
  process.exit(1)
}

function log(msg) {
  process.stdout.write(msg + '\n')
}

/** Recursive directory copy — Node.js only, no cp -r, works on Windows */
function copyDir(src, dest) {
  mkdirSync(dest, { recursive: true })
  for (const entry of readdirSync(src, { withFileTypes: true })) {
    const srcPath = join(src, entry.name)
    const destPath = join(dest, entry.name)
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath)
    } else {
      copyFileSync(srcPath, destPath)
    }
  }
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
  const templatePath = join(WIDGETS_DIR, `${templateName}.tsx`)
  if (!existsSync(templatePath)) fail(`Template not found: ${templateName}.tsx in ${WIDGETS_DIR}`)
  let content = readFileSync(templatePath, 'utf8')

  for (const [key, value] of Object.entries(subs)) {
    content = content.split(`<${key}>`).join(value)
  }

  // Inject time constants after the last import line
  const lines = content.split('\n')
  let lastImportIdx = -1
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('import ')) lastImportIdx = i
  }
  if (lastImportIdx >= 0) {
    lines.splice(lastImportIdx + 1, 0, '', TIME_CONSTANTS.trimEnd())
    content = lines.join('\n')
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
 * @param {{ componentName: string, title: string, subtitle?: string, detailFnBody: string, detailColumns?: string|null, defaultSortKey?: string }} widget
 * @returns {string} Full TypeScript file content
 */
export function generateViewFile(widget) {
  const { componentName, title, subtitle = '', detailFnBody, detailColumns, defaultSortKey } = widget

  const indentedFn = detailFnBody.split('\n').map(l => '  ' + l).join('\n')
  const columnsExpr = detailColumns ? detailColumns : 'autoColumns(rows)'
  const sortKeyExpr = defaultSortKey ? JSON.stringify(defaultSortKey) : '(columns[0]?.key as string)'

  return `import React from 'react'
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useWidgetData } from '@/hooks/useWidgetData'
import { LoadingState, EmptyState } from '@/dashboard/chrome'
import { fmtNumber, fmtPercent, fmtDuration, fmtTimeAgo } from '@/lib/format'
import { toneClass } from '@/lib/widget'

${TIME_CONSTANTS.trimEnd()}

type Row = Record<string, unknown>

// ── Detail data function (record grain — individual records behind the chart) ──
// Promise<any[]>: SDK response interfaces lack index signatures — see widget shell.
const customDataFn = async (sdk: any, getToken: () => Promise<string>): Promise<any[]> => {
${indentedFn}
}
// ─────────────────────────────────────────────────────────────────────────────

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
  const { data, loading, error } = useWidgetData(customDataFn, [])

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

  const rows = toRows(data ?? [])
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
  )
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
export function injectAppRoutes(projectPath, viewWidgetNames) {
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
  ].join('\n')

  const routes = [
    `        <Route path="/" element={<Dashboard />} />`,
    ...viewNames.map(n => `        <Route path="/${n.toLowerCase()}" element={<${n}View />} />`),
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
  if (!intent.dashboardName || typeof intent.dashboardName !== 'string') errors.push('dashboardName must be a non-empty string')
  if (!['1d', '7d', '30d', '90d'].includes(intent.timeRange)) errors.push(`timeRange must be one of: 1d, 7d, 30d, 90d`)
  if (!Array.isArray(intent.metrics) || intent.metrics.length === 0) errors.push('metrics must be a non-empty array')
  for (const m of (intent.metrics ?? [])) {
    if (!m.name) errors.push('metric missing name')
    if (!['T1', 'T2', 'T3'].includes(m.tier)) errors.push(`metric "${m.name}" has invalid tier: ${m.tier}`)
    if (m.tier === 'T1' || m.tier === 'T2') {
      if (!m.fnBody) errors.push(`${m.tier} metric "${m.name}" missing fnBody — agent must write the SDK call from documentation`)
      if (!m.title)  errors.push(`${m.tier} metric "${m.name}" missing title`)
    }
    if (m.tier === 'T2') {
      if (!m.params) {
        errors.push(`T2 metric "${m.name}" missing params`)
      }
    }
    if (m.tier === 'T3') {
      if (!m.title) errors.push(`T3 metric "${m.name}" missing title`)
      if (!m.fnBody) errors.push(`T3 metric "${m.name}" missing fnBody — write an async function body using SDK service classes`)
      if (!m.displayAs) errors.push(`T3 metric "${m.name}" with fnBody needs displayAs — valid values: ${VALID_DISPLAY_TYPES.join(', ')}`)
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
  }
  return errors
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
    detailFnBody: metric.detailFnBody ?? metric.fnBody,
    detailColumns: metric.detailColumns ? compileColumns(metric.detailColumns) : null,
    defaultSortKey: metric.detailSortKey,
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
  if (!metric.fnBody)  throw new Error(`metric "${metric.name}" missing fnBody — agent must provide the SDK call`)

  const defaults    = registryEntry?.defaults ?? {}
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const displayAs   = metric.displayAs ?? registryEntry?.template
  const iconName    = metric.icon ?? defaults.icon ?? 'Activity'

  if (!displayAs) throw new Error(`metric "${metric.name}" needs displayAs`)

  const CHART_TYPES = new Set(['area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart', 'rate-chart'])

  // ── Chart path ─────────────────────────────────────────────────────────────
  if (CHART_TYPES.has(displayAs)) {
    const indented = metric.fnBody.split('\n').map(l => '  ' + l).join('\n')
    // Promise<any[]> (not Record<string, unknown>[]): SDK response types are
    // interfaces, which lack implicit index signatures — they are NOT assignable
    // to Record<string, unknown>. any[] keeps the "must return an array" check
    // while letting fnBody return SDK-typed arrays directly, no casts.
    const customFnBlock = [
      '',
      '// ── Custom data function ──────────────────────────────────────────────────────',
      'const customDataFn = async (sdk: any, getToken: () => Promise<string>): Promise<any[]> => {',
      indented,
      '}',
      '// ────────────────────────────────────────────────────────────────────────────',
      '',
    ].join('\n')

    const spec = {
      componentName,
      template:          displayAs,
      detailRoute:       metric.detailRoute ?? `/${componentName.toLowerCase()}`,
      icon:              iconName,
      title:             metric.title,
      subtitle:          autoSubtitle(metric, defaults, timeRange),
      dataHook:          'useWidgetData(customDataFn, [])',
      hookImport:        "import { useWidgetData } from '@/hooks/useWidgetData'",
      sdkImportLine:     '',
      responseTypeImport: '',
      dataSelector:      'data ?? []',
      xKey:              metric.xKey  ?? defaults.xKey  ?? 'date',
      yKey:              metric.yKey  ?? defaults.yKey  ?? 'value',
      headlineMode:      metric.headlineMode  ?? defaults.headlineMode  ?? 'sum',
      deltaPolarity:     metric.deltaPolarity ?? defaults.deltaPolarity ?? 'neutral',
      rateNum:           metric.rateNum ?? defaults.rateNum ?? 'num',
      rateDen:           metric.rateDen ?? defaults.rateDen ?? 'den',
      series:            metric.series ?? defaults.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]',
      pivotExpression:   metric.pivotExpression ?? defaults.pivotExpression ?? 'rawData',
    }

    let content = applyTemplate(spec.template, specToSubs(spec))
    content = content.replace(/\nexport function /, customFnBlock + '\nexport function ')
    return content
  }

  // ── KPI / table path (shell template) ──────────────────────────────────────
  if (!existsSync(T3_SHELL_TEMPLATE_PATH)) {
    throw new Error(`T3 shell template not found at ${T3_SHELL_TEMPLATE_PATH}`)
  }
  const indentedFnBody = metric.fnBody.split('\n').map(l => '  ' + l).join('\n')
  const columns    = compileColumns(metric.columnDefs ?? metric.columns ?? defaults.columnDefs ?? defaults.columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]')
  const valueField = metric.valueField ?? ''
  const valueLabel = metric.valueLabel ?? ''
  const subtitle   = autoSubtitle(metric, defaults, timeRange)

  let content = readFileSync(T3_SHELL_TEMPLATE_PATH, 'utf8')
  content = content
    .split('<<FN_BODY>>').join(indentedFnBody)
    .split('<<COMPONENT_NAME>>').join(componentName)
    .split('<<TITLE>>').join(metric.title ?? componentName)
    .split('<<DESCRIPTION>>').join(subtitle)
    .split('<<ICON_NAME>>').join(iconName)
    .split('<<DISPLAY_AS>>').join(displayAs ?? 'ranked-table')
    .split('<<COLUMNS>>').join(columns)
    .split('<<VALUE_FIELD>>').join(valueField)
    .split('<<VALUE_LABEL>>').join(valueLabel)

  const lines = content.split('\n')
  let lastImportIdx = -1
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('import ')) lastImportIdx = i
  }
  if (lastImportIdx >= 0) {
    lines.splice(lastImportIdx + 1, 0, '', TIME_CONSTANTS.trimEnd())
    content = lines.join('\n')
  }
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
    SDK_IMPORT_LINE: spec.sdkImportLine ?? '',
    RESPONSE_TYPE_IMPORT: spec.responseTypeImport ?? '',
    HOOK_IMPORT: "import { useWidgetData } from '@/hooks/useWidgetData'",
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
 * Poll until a TCP port accepts connections or the deadline passes.
 * Returns the port that responded, or the starting port if none responded.
 * @param {number} startPort
 * @param {number} timeoutMs
 * @returns {Promise<number>}
 */
async function detectDevServerPort(startPort, timeoutMs) {
  const deadline = Date.now() + timeoutMs
  let port = startPort
  while (Date.now() < deadline) {
    const open = await new Promise(resolve => {
      const socket = createConnection({ port, host: 'localhost' })
      socket.once('connect', () => { socket.destroy(); resolve(true) })
      socket.once('error', () => resolve(false))
      socket.setTimeout(500, () => { socket.destroy(); resolve(false) })
    })
    if (open) return port
    port++
    if (port > startPort + 10) port = startPort
  }
  return startPort
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
    // Step 1 — Scaffold (skip if already exists)
    if (!existsSync(join(P, 'package.json'))) {
      if (!existsSync(SCAFFOLD_DIR)) fail(`Scaffold not found at ${SCAFFOLD_DIR}`)
      copyDir(SCAFFOLD_DIR, P)
      try { rmSync(join(P, 'node_modules'), { recursive: true, force: true }) } catch { /* ignore */ }
    }
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
    const partialState = {
      schemaVersion: 1,
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

    // Step 4 — Resolve + generate widgets
    const t3Metrics = metrics.filter(m => m.tier === 'T3')
    const widgetHashes = {}
    const widgetMeta = []    // { componentName, template }
    const widgetSpecs = {}   // componentName → view spec (see buildViewSpec); chart widgets only
    let widgetIndex = 0
    const total = metrics.length

    // All widgets generated together — T1, T2, T3 in one pass (no per-widget tsc)
    // T3 errors are caught by the single tsc in step 6 below.
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
      widgetHashes[componentName] = { hash: hashContent(widgetContent), tier: metric.tier, metric: metric.name, template: displayAs, intentMetric: metric }
      widgetMeta.push({ componentName, template: displayAs })

      // Detail views: only chart widgets emit navigate/ViewAllLink (the shell
      // template for KPI/table links nowhere), so only charts need a generated
      // view + route — any tier. Columns are auto-detected at runtime in the view.
      if (widgetLayoutGroup(displayAs) === 'chart') {
        widgetSpecs[componentName] = buildViewSpec(componentName, metric, entry, timeRange)
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

    // Step 5b — Only inject routes for widgets that actually have view files
    injectAppRoutes(P, generatedViewNames)

    // Step 6 — Full tsc (catches errors for all tiers including T3)
    try {
      execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
      emit('TSC_PASS')
    } catch (e) {
      const tscOut = e.stdout?.toString() ?? ''

      // If T3 widgets are present, identify all that failed and signal the agent to fix them
      if (t3Metrics.length > 0) {
        const failingWidgets = t3Metrics
          .map(m => ({ name: m.name, componentName: toPascalCase(m.name) }))
          .filter(({ componentName }) => tscOut.includes(componentName))
        if (failingWidgets.length > 0) {
          const errors = tscOut.split('\n').filter(l => l.includes('error TS')).slice(0, 10)
          emit('T3_RETRY', { widgets: failingWidgets.map(w => w.name), errors, intentPath })
          log(`⚠ ${failingWidgets.length} T3 widget(s) have TypeScript errors. Fix fnBody in ${intentPath} and re-run.`)
          process.exit(2)
        }
      }

      const err = tscOut || e.stderr?.toString() || String(e)
      emit('TSC_FAIL', { errors: err.slice(0, 1000) })
      fail(`TypeScript errors:\n${err}`)
    }

    // Step 7 — Write final state.json (upgrade partial → complete)
    const newState = {
      schemaVersion: 1,
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0', description: dashboardDescription },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
      timeRange,
      widgets: widgetHashes,
      deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
      buildStatus: 'complete',
    }
    writeAtomic(statePath, JSON.stringify(newState, null, 2))

    // Step 8 — Start dev server (kill previous one first to guarantee port 57173)
    const serverPidFile = join(P, '.dashboard', 'server.pid')
    await killPreviousDevServer(serverPidFile)

    const isWindows = process.platform === 'win32'
    const server = spawn(
      'npm',
      ['run', 'dev', '--', '--port', String(DASHBOARD_PORT)],
      { cwd: P, detached: true, stdio: 'ignore', shell: isWindows }
    )
    server.on('error', () => {})
    server.unref()

    // Persist PID so future builds can kill this server before starting their own
    if (server.pid) {
      writeAtomic(serverPidFile, String(server.pid))
    }

    const port = await detectDevServerPort(DASHBOARD_PORT, 8000)

    emit('SERVER_READY', { port, url: `http://localhost:${port}` })
    emit('BUILD_RESULT', {
      success: true, projectDir: P, port,
      previewUrl: `http://localhost:${port}`,
      widgets: Object.keys(widgetHashes),
      dashboardName,
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
 * Starts from the persisted intentMetric (full fnBody/title/hints) and merges
 * the delta on top. Falls back to a minimal ref for legacy state files that
 * predate intentMetric persistence — then the delta itself must carry fnBody + title.
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
  const statePath = join(P, '.dashboard', 'state.json')
  if (!existsSync(statePath)) fail('No .dashboard/state.json found. Run a fresh build first.')
  const state = JSON.parse(readFileSync(statePath, 'utf8'))
  if (state.buildStatus === 'in-progress') {
    log('⚠ Warning: Previous build did not complete — widgets may be missing. Consider running a full build first.')
  }
  const { ops } = classifyEditIntent(editIntent)
  const timeRange = state.timeRange ?? '30d'

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
        if (!metricRef.fnBody) {
          violations.push(`ops[${i}] CHANGE "${o.target}": no fnBody available — include the full metric (fnBody, title) in the delta, or re-run a fresh build`)
        }
      }
    }
    if (o.op === 'ADD') {
      if (!o.metric?.name) { violations.push(`ops[${i}] ADD: missing metric`); continue }
      try { resolveMetric(o.metric) } catch (e) { violations.push(`ops[${i}] ADD "${o.metric.name}": ${e.message}`) }
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
    const widgetContent = buildWidgetFile(metric, entry, timeRange)
    const addTemplate = metric.displayAs ?? entry?.template ?? 'data-table'
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
    writeAtomic(widgetPath, widgetContent)
    state.widgets = state.widgets ?? {}
    state.widgets[componentName] = { hash: hashContent(widgetContent), tier, metric: metric.name, template: addTemplate, intentMetric: metric }
    // Chart widgets emit a drill-down link — generate the detail view so the route resolves
    if (widgetLayoutGroup(addTemplate) === 'chart') {
      const viewContent = generateViewFile(buildViewSpec(componentName, metric, entry, timeRange))
      writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`), viewContent)
    }

  } else if (op === 'REMOVE') {
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    if (existsSync(widgetPath)) unlinkSync(widgetPath)
    const viewPath = join(P, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (existsSync(viewPath)) unlinkSync(viewPath)
    if (state.widgets) delete state.widgets[target]

  } else if (op === 'CHANGE') {
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    const stored = state.widgets?.[target]
    const metricRef = resolveChangeMetric(stored, target, delta)
    const tier = metricRef.tier ?? stored?.tier ?? 'T1'
    const { entry } = resolveMetric(metricRef)
    const widgetContent = buildWidgetFile(metricRef, entry, delta?.timeRange ?? timeRange)
    writeAtomic(widgetPath, widgetContent)
    const changeTemplate = metricRef.displayAs ?? entry?.template ?? stored?.template ?? 'data-table'
    if (state.widgets) state.widgets[target] = { hash: hashContent(widgetContent), tier, metric: metricRef.name, template: changeTemplate, intentMetric: metricRef }
    // Keep the detail view in sync: regenerate for charts, drop it if no longer a chart
    const changeViewPath = join(P, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (widgetLayoutGroup(changeTemplate) === 'chart') {
      const viewContent = generateViewFile(buildViewSpec(target, metricRef, entry, delta?.timeRange ?? timeRange))
      writeAtomic(changeViewPath, viewContent)
    } else if (existsSync(changeViewPath)) {
      unlinkSync(changeViewPath)
    }

  } else if (op === 'REBUILD') {
    // Regenerate every widget (and chart detail view) from the persisted intentMetric.
    // Useful after scaffold/template updates. Legacy entries without intentMetric are skipped.
    for (const [componentName, info] of Object.entries(state.widgets ?? {})) {
      const m = info.intentMetric
      if (!m?.fnBody) {
        log(`⚠ Cannot rebuild "${componentName}" — built before intent persistence. Re-run a fresh build to refresh it.`)
        continue
      }
      const { entry } = resolveMetric(m)
      const content = buildWidgetFile(m, entry, timeRange)
      writeAtomic(join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`), content)
      info.hash = hashContent(content)
      const rebuildViewPath = join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`)
      if (widgetLayoutGroup(info.template ?? '') === 'chart') {
        writeAtomic(rebuildViewPath, generateViewFile(buildViewSpec(componentName, m, entry, timeRange)))
      } else if (existsSync(rebuildViewPath)) {
        unlinkSync(rebuildViewPath)
      }
    }
  }

  applied.push({ op, widget: target ?? (metric ? (metric.componentName ?? toPascalCase(metric.name)) : undefined) })
  } // end apply loop

  // Regenerate Dashboard.tsx + index.ts — ONCE for the whole batch
  const widgetMeta = Object.entries(state.widgets ?? {}).map(([name, info]) => ({
    componentName: name,
    template: info.template ?? 'ranked-table',
  }))
  generateDashboardFiles(P, widgetMeta, state.app?.name ?? 'Dashboard', state.app?.description ?? '')

  // Re-inject App.tsx routes — only for widgets that have an actual view file on disk
  const viewNames = Object.keys(state.widgets ?? {}).filter(name =>
    existsSync(join(P, 'src', 'dashboard', 'views', `${name}View.tsx`))
  )
  injectAppRoutes(P, viewNames)

  // tsc validate
  try {
    execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
    emit('TSC_PASS')
  } catch (e) {
    const err = e.stdout?.toString() || ''
    emit('TSC_FAIL', { errors: err.slice(0, 500) })
    fail(`TypeScript errors after edit:\n${err}`)
  }

  writeAtomic(statePath, JSON.stringify(state, null, 2))
  emit('INCREMENTAL_READY', { count: applied.length, ops: applied })
}

// ── Entry point ────────────────────────────────────────────────────────────────

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {

  // --prewarm <routingName> mode: copy scaffold + run npm ci, then exit
  // Creates the project under <cwd>/<routingName>.
  if (process.argv[2] === '--prewarm' && process.argv[3]) {
    const routingName = process.argv[3]
    const prewarmDir  = join(process.cwd(), routingName)
    if (!existsSync(join(prewarmDir, 'package.json'))) {
      if (!existsSync(SCAFFOLD_DIR)) {
        process.stderr.write(`ERROR: Scaffold not found at ${SCAFFOLD_DIR}\n`)
        process.exit(1)
      }
      mkdirSync(prewarmDir, { recursive: true })
      copyDir(SCAFFOLD_DIR, prewarmDir)
      try { rmSync(join(prewarmDir, 'node_modules'), { recursive: true, force: true }) } catch { /* ignore */ }
    }
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
