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
 * @property {string}      [title]       - Display title (required for T1/T2/T3)
 * @property {string}      [description] - One-line description
 * @property {string}      [componentName] - Override PascalCase component name
 * @property {string}      [icon]        - lucide-react icon name
 * @property {string}      [detailRoute] - HashRouter path for drilldown
 * @property {Object}      [params]      - T2 filter params (used for validation only — agent writes fnBody)
 * @property {number}      [params.threshold]
 * @property {string}      [params.direction] - 'gt'|'lt'|'eq'|'gte'|'lte'|'neq'
 * @property {string}      fnBody        - Required for all tiers: async function body using SDK service classes
 * @property {string}      [displayAs]   - Widget template name (kpi-card | ranked-table | data-table | *-chart)
 * @property {string}      [valueField]  - kpi-card: which field to display as the headline number
 * @property {string}      [valueLabel]  - kpi-card: label shown below the headline (e.g. "running jobs")
 * @property {string}      [dataSelector]
 * @property {string}      [dataHook]
 * @property {string}      [columns]     - ColumnDef array literal string
 * @property {string}      [xKey]
 * @property {string}      [yKey]
 * @property {string}      [deltaDir]
 * @property {string}      [deltaText]
 * @property {string}      [series]
 * @property {string}      [pivotExpression]
 */

/**
 * The full intent.json structure.
 * @typedef {Object} DashboardIntent
 * @property {string}        dashboardName
 * @property {'1d'|'7d'|'30d'|'90d'} timeRange
 * @property {IntentMetric[]} metrics
 * @property {string}        projectDir  - Absolute path for generated project
 * @property {string}        routingName - Permanent URL slug (e.g. "agent-health-x7k2")
 * @property {string}        orgName
 * @property {string}        tenantName
 * @property {string}        cloudUrl    - e.g. https://alpha.uipath.com
 * @property {string}        apiUrl      - e.g. https://alpha.api.uipath.com
 * @property {string}        tenantId    - UUID from ~/.uipath/.auth
 * @property {string}        [clientId]  - External OAuth app client ID
 */

/**
 * Derived widget specification — all fields resolved, ready for template substitution.
 * @typedef {Object} WidgetSpec
 * @property {string} componentName
 * @property {string} template
 * @property {string} title
 * @property {string} description
 * @property {string} icon
 * @property {string} detailRoute
 * @property {string} dataHook
 * @property {string} dataSelector
 * @property {string} xKey
 * @property {string} yKey
 * @property {string} valueExpression
 * @property {string} columns
 * @property {string} deltaDir
 * @property {string} deltaText
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
 * @property {string}     hash     - SHA-256 prefix of generated file content
 * @property {MetricTier} tier
 * @property {string}     metric   - Original metric name from intent
 * @property {string}     template - Template used for layout classification
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
  'area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart',
]

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
 * Columns are auto-detected from the first data row at runtime via autoColumns().
 * When the dataHook references customDataFn and fnBody is provided, injects a
 * customDataFn definition so the view file compiles without referencing an
 * undefined symbol.
 * @param {{ componentName: string, title: string, description: string, dataHook: string, dataSelector: string, fnBody?: string }} widget
 * @returns {string} Full TypeScript file content
 */
function generateViewFile(widget) {
  const { componentName, title, description, dataHook, dataSelector, fnBody } = widget

  const staticColumnsDecl = ''
  const columnsExpr = 'autoColumns(rows)'

  // If dataHook references customDataFn, define it here too so the view compiles
  const needsCustomFn = dataHook && dataHook.includes('customDataFn') && fnBody
  const customFnBlock = needsCustomFn ? `
// ── Custom data function (same fnBody as parent widget) ──────────────────────
const customDataFn = async (sdk: any, getToken: () => Promise<string>): Promise<Record<string, unknown>[]> => {
${fnBody.split('\n').map(l => '  ' + l).join('\n')}
}
// ─────────────────────────────────────────────────────────────────────────────
` : ''

  return `import React from 'react'
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useInsightsSDK } from '@/hooks/useInsightsSDK'
import { LoadingState, EmptyState } from '@/dashboard/chrome'

${TIME_CONSTANTS.trimEnd()}
${staticColumnsDecl}
type Row = Record<string, unknown>

/**
 * Auto-generate column definitions from the first data row.
 * Only includes primitive fields (strings, numbers) — skips nested objects and nulls.
 * Column labels are derived by splitting camelCase into words.
 */
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
${customFnBlock}
export function ${componentName}View() {
  const { data, loading, error } = ${dataHook}

  /** Safely extract a row array from any Insights API response shape */
  function toRows(raw: unknown): Row[] {
    if (!raw) return []
    if (Array.isArray(raw)) return raw as Row[]
    if (typeof raw === 'object') {
      const obj = raw as Record<string, unknown>
      if (Array.isArray(obj.agents)) return obj.agents as Row[]
      if (Array.isArray(obj.data)) return obj.data as Row[]
      if (obj.data && typeof obj.data === 'object') return toRows(obj.data)
    }
    return []
  }

  const raw: unknown = ${dataSelector ?? '(data as any)?.data ?? []'}
  const rows = toRows(raw)
  const columns = ${columnsExpr}

  if (loading) return (
    <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}">
      <LoadingState height="h-96" />
    </DetailViewShell>
  )
  if (error) return (
    <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}">
      <EmptyState message={error.message} />
    </DetailViewShell>
  )
  return (
    <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}">
      <RecordsTable rows={rows} columns={columns} defaultSortKey={columns[0]?.key as string} />
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
function generateDashboardFiles(projectPath, widgetMeta, dashboardName) {
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
        <Header title="${dashboardName}" description="Operational metrics dashboard" />
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
function widgetLayoutGroup(template) {
  if (['kpi-card', 'kpi-with-sparkline'].includes(template)) return 'kpi'
  if (['data-table', 'ranked-table', 'progress-bar-list'].includes(template)) return 'table'
  return 'chart'
}

/**
 * Inject generated import and route blocks into App.tsx markers.
 * @param {string} projectPath
 * @param {string[]} viewWidgetNames - Widget names that have a generated view file
 */
function injectAppRoutes(projectPath, viewWidgetNames) {
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

  const CHART_TYPES = new Set(['area-chart', 'line-chart', 'bar-chart', 'donut-chart', 'multi-line-chart'])

  // ── Chart path ─────────────────────────────────────────────────────────────
  if (CHART_TYPES.has(displayAs)) {
    const indented = metric.fnBody.split('\n').map(l => '  ' + l).join('\n')
    const customFnBlock = [
      '',
      '// ── Custom data function ──────────────────────────────────────────────────────',
      'const customDataFn = async (sdk: any, getToken: () => Promise<string>): Promise<Record<string, unknown>[]> => {',
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
      description:       metric.description ?? defaults.description ?? '',
      dataHook:          'useInsightsSDK(customDataFn, [])',
      hookImport:        "import { useInsightsSDK } from '@/hooks/useInsightsSDK'",
      sdkImportLine:     '',
      responseTypeImport: '',
      dataSelector:      'data ?? []',
      xKey:              metric.xKey  ?? defaults.xKey  ?? 'date',
      yKey:              metric.yKey  ?? defaults.yKey  ?? 'value',
      valueExpression:   "'—'",
      columns:           metric.columns ?? '[{key:"name",label:"Name"}]',
      deltaDir:          metric.deltaDir ?? defaults.deltaDir ?? 'neutral',
      deltaText:         metric.deltaText ?? defaults.deltaText ?? '',
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
  const columns    = metric.columns   ?? defaults.columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]'
  const valueField = metric.valueField ?? ''
  const valueLabel = metric.valueLabel ?? ''

  let content = readFileSync(T3_SHELL_TEMPLATE_PATH, 'utf8')
  content = content
    .split('<<FN_BODY>>').join(indentedFnBody)
    .split('<<COMPONENT_NAME>>').join(componentName)
    .split('<<TITLE>>').join(metric.title ?? componentName)
    .split('<<DESCRIPTION>>').join(metric.description ?? defaults.description ?? '')
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
    DESCRIPTION: spec.description,
    DETAIL_ROUTE: spec.detailRoute,
    ICON: spec.icon,
    DATA_HOOK: spec.dataHook,
    DATA_SELECTOR: spec.dataSelector,
    X_KEY: spec.xKey,
    Y_KEY: spec.yKey,
    DATA_KEY: spec.yKey,
    NAME_KEY: spec.xKey,
    VALUE_EXPRESSION: spec.valueExpression,
    COLUMNS: spec.columns,
    DELTA_DIR: spec.deltaDir,
    DELTA_TEXT: spec.deltaText,
    SERIES: spec.series,
    PIVOT_EXPRESSION: spec.pivotExpression,
    SDK_IMPORT: '',
    SDK_SERVICE: '',
    SDK_CALL: '',
    SDK_RESULT_TYPE: '',
    SDK_IMPORT_LINE: spec.sdkImportLine ?? '',
    RESPONSE_TYPE_IMPORT: spec.responseTypeImport ?? '',
    HOOK_IMPORT: "import { useInsightsSDK } from '@/hooks/useInsightsSDK'",
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
    projectDir, orgName, tenantName, cloudUrl, apiUrl, tenantId, clientId = '',
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
    writeAtomic(join(P, '.env.local'), [
      `VITE_UIPATH_CLOUD_URL=${cloudUrl}`,
      `VITE_UIPATH_BASE_URL=${apiUrl}`,
      `VITE_UIPATH_ORG_NAME=${orgName}`,
      `VITE_UIPATH_TENANT_NAME=${tenantName}`,
      `VITE_INSIGHTS_TENANT_ID=${tenantId}`,
      `VITE_UIPATH_CLIENT_ID=${clientId}`,
      `VITE_UIPATH_SCOPE=OR.Assets.Read OR.Jobs OR.Folders.Read OR.Buckets.Read OR.Execution.Read OR.Tasks OR.Queues.Read OR.Users.Read Insights Insights.RealTimeData`,
      `VITE_DEV_PORT=${DASHBOARD_PORT}`,
    ].join('\n'))
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
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
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

    // Step 4 — Resolve + generate widgets
    const nonT3 = metrics.filter(m => m.tier !== 'T3')
    const t3Metrics = metrics.filter(m => m.tier === 'T3')
    const widgetHashes = {}
    const widgetMeta = []    // { componentName, template }
    const widgetSpecs = {}   // componentName → { componentName, title, description, dataHook, dataSelector, columns }
    let widgetIndex = 0
    const total = metrics.length

    // All non-T3 metrics use buildWidgetFile (unified path)
    await Promise.all(nonT3.map(async (metric) => {
      const { entry } = resolveMetric(metric)  // gets registry hints or null
      const widgetContent = buildWidgetFile(metric, entry, timeRange)

      const displayAs = metric.displayAs ?? entry?.template ?? 'data-table'
      const componentName = metric.componentName ?? toPascalCase(metric.name)
      const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
      writeAtomic(widgetPath, widgetContent)

      widgetHashes[componentName] = { hash: hashContent(widgetContent), tier: metric.tier, metric: metric.name, template: displayAs }
      widgetMeta.push({ componentName, template: displayAs })

      // Generate view file for T1/T2 using registry's dataSelector + display hints
      if (entry) {
        widgetSpecs[componentName] = {
          componentName,
          title: metric.title ?? entry.defaults?.title ?? componentName,
          description: metric.description ?? entry.defaults?.description ?? '',
          dataHook: 'useInsightsSDK(customDataFn, [])',
          dataSelector: metric.dataSelector ?? entry.defaults?.dataSelector ?? '[]',
          columns: metric.columns ?? entry.defaults?.columns,
          viewColumns: entry.defaults?.viewColumns,
          fnBody: metric.fnBody,
        }
      }

      widgetIndex++
      emit('WIDGET_READY', { name: componentName, index: widgetIndex, total })
    }))

    // T3 widgets — sequential with exit-2 retry signal
    for (const metric of t3Metrics) {
      const currentIntent = JSON.parse(readFileSync(intentPath, 'utf8'))
      const currentMetric = currentIntent.metrics.find(m => m.name === metric.name) ?? metric

      let widgetContent
      try {
        widgetContent = buildWidgetFile(currentMetric, null, timeRange)
      } catch (e) {
        emit('T3_FAILED', { widget: metric.name, reason: e.message })
        fail(`T3 widget "${metric.name}" could not be generated: ${e.message}`)
      }

      const componentName = toPascalCase(metric.name)
      const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
      writeAtomic(widgetPath, widgetContent)

      try {
        execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
      } catch (e) {
        const tscOut = e.stdout?.toString() ?? ''
        const errors = tscOut.split('\n').filter(l => l.includes('error TS')).slice(0, 5)
        const failingWidget = widgetNameFromTscErrors(tscOut, toPascalCase(metric.name))
        // Exit code 2 signals the agent to fix fnBody in intent.json and re-run
        emit('T3_RETRY', { widget: failingWidget, errors, intentPath })
        log(`⚠ Widget "${failingWidget}" has TypeScript errors. Fix fnBody in ${intentPath} and re-run.`)
        process.exit(2)
      }

      const t3Template = metric.displayAs ?? 'ranked-table'
      widgetHashes[componentName] = { hash: hashContent(widgetContent), tier: 'T3', metric: metric.name, template: t3Template }
      widgetMeta.push({ componentName, template: t3Template })
      // T3 widgets never get detail views — no Insights endpoint backs them
      widgetIndex++
      emit('WIDGET_READY', { name: componentName, index: widgetIndex, total })
    }

    // Step 5 — Generate Dashboard.tsx + index.ts
    generateDashboardFiles(P, widgetMeta, dashboardName)

    // Step 5a — Generate view files and track which ones were written
    const generatedViewNames = []
    for (const [componentName, spec] of Object.entries(widgetSpecs)) {
      const info = widgetHashes[componentName]
      if (info?.tier === 'T2') continue
      const viewContent = generateViewFile(spec)
      writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`), viewContent)
      generatedViewNames.push(componentName)
    }

    // Step 5b — Only inject routes for widgets that actually have view files
    injectAppRoutes(P, generatedViewNames)

    // Step 6 — Full tsc
    try {
      execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
      emit('TSC_PASS')
    } catch (e) {
      const err = e.stdout?.toString() || e.stderr?.toString() || String(e)
      emit('TSC_FAIL', { errors: err.slice(0, 1000) })
      fail(`TypeScript errors:\n${err}`)
    }

    // Step 7 — Write final state.json (upgrade partial → complete)
    const newState = {
      schemaVersion: 1,
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
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
 * Validate an edit-intent.json operation and return it unchanged.
 * Throws for unknown operation types.
 * @param {{ op: string, projectDir: string, target?: string, metric?: IntentMetric, delta?: object }} editIntent
 * @returns {typeof editIntent}
 */
export function classifyEditIntent(editIntent) {
  if (!VALID_EDIT_OPS.includes(editIntent.op)) {
    throw new Error(`classifyEditIntent: invalid op "${editIntent.op}". Must be one of: ${VALID_EDIT_OPS.join(', ')}`)
  }
  return editIntent
}

/**
 * Apply an incremental edit (ADD / REMOVE / CHANGE / REBUILD) to an existing project.
 * @param {{ op: string, projectDir: string, target?: string, metric?: IntentMetric, delta?: object }} editIntent
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
  const { op, target, metric, delta } = classifyEditIntent(editIntent)
  const timeRange = state.timeRange ?? '30d'

  if (op === 'ADD') {
    const { tier, entry } = resolveMetric(metric)
    const componentName = metric.componentName ?? toPascalCase(metric.name)
    const widgetContent = buildWidgetFile(metric, entry, timeRange)
    const addTemplate = metric.displayAs ?? entry?.template ?? 'data-table'
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
    writeAtomic(widgetPath, widgetContent)
    state.widgets = state.widgets ?? {}
    state.widgets[componentName] = { hash: hashContent(widgetContent), tier, metric: metric.name, template: addTemplate }

  } else if (op === 'REMOVE') {
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    const currentContent = existsSync(widgetPath) ? readFileSync(widgetPath, 'utf8') : null
    const stored = state.widgets?.[target]
    if (currentContent && stored && hashContent(currentContent) !== stored.hash) {
      emit('HAND_EDIT_DETECTED', { widget: target })
      fail(`Widget "${target}" has been hand-edited. Overwriting would lose your changes.`)
    }
    if (existsSync(widgetPath)) unlinkSync(widgetPath)
    const viewPath = join(P, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (existsSync(viewPath)) unlinkSync(viewPath)
    if (state.widgets) delete state.widgets[target]

  } else if (op === 'CHANGE') {
    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    const currentContent = existsSync(widgetPath) ? readFileSync(widgetPath, 'utf8') : null
    const stored = state.widgets?.[target]
    if (currentContent && stored && hashContent(currentContent) !== stored.hash) {
      emit('HAND_EDIT_DETECTED', { widget: target })
      fail(`Widget "${target}" has been hand-edited. Overwriting would lose your changes.`)
    }
    const tier = stored?.tier ?? 'T1'
    const metricRef = { name: stored?.metric ?? target.toLowerCase(), tier, ...delta }
    const { entry } = resolveMetric(metricRef)
    const widgetContent = buildWidgetFile(metricRef, entry, delta?.timeRange ?? timeRange)
    writeAtomic(widgetPath, widgetContent)
    const changeTemplate = metricRef.displayAs ?? entry?.template ?? stored?.template ?? 'data-table'
    if (state.widgets) state.widgets[target] = { hash: hashContent(widgetContent), tier, metric: metricRef.name, template: changeTemplate }

  } else if (op === 'REBUILD') {
    // Rebuild all widgets from existing state entries — requires fnBody not stored in state
    for (const [componentName, info] of Object.entries(state.widgets ?? {})) {
      // All tiers require fnBody which is not persisted in state — skip with warning
      log(`⚠ Cannot rebuild ${info.tier} widget "${componentName}" from state alone — fnBody not persisted. Re-run full build with intent.json.`)
    }
  }

  // Regenerate Dashboard.tsx + index.ts
  const widgetMeta = Object.entries(state.widgets ?? {}).map(([name, info]) => ({
    componentName: name,
    template: info.template ?? 'ranked-table',
  }))
  generateDashboardFiles(P, widgetMeta, state.app?.name ?? 'Dashboard')

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
  emit('INCREMENTAL_READY', { op, widget: target ?? toPascalCase(metric?.name ?? '') })
}

// ── Entry point ────────────────────────────────────────────────────────────────

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {

  // --prewarm <routingName> mode: copy scaffold + run npm ci, then exit
  // Takes a routing name (e.g. "agent-health-x7k2"), always creates the project
  // under ~/dashboards/<routingName> — never in cwd.
  // Path is computed by Node.js (os.homedir) so no bash path manipulation needed.
  if (process.argv[2] === '--prewarm' && process.argv[3]) {
    const { homedir } = await import('os')
    const routingName = process.argv[3]
    const prewarmDir  = join(homedir(), 'dashboards', routingName)
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
  } else if (plan.op) {
    classifyEditIntent(plan)
    await runIncrementalEdit(plan, planArg)
  } else {
    fail('Unrecognised input format. Expected intent.json (has "metrics") or edit-intent.json (has "op").')
  }

} // end entry-point guard
