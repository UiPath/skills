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
 *   2 — metric modules need retry (fix the named metrics/<name>.ts files and re-run)
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync, renameSync, unlinkSync } from 'fs'
import { join, dirname, resolve } from 'path'
import { fileURLToPath, pathToFileURL } from 'url'
import { execSync } from 'child_process'
import { createHash } from 'crypto'
// Project-lifecycle utilities (versioning, prewarm, sdk-check, dev-server teardown)
// live in a sibling module. Imported for internal use here; the test-facing ones are
// re-exported so `import … from build-dashboard.mjs` keeps working. (Benign runtime
// import cycle — lifecycle.mjs imports primitives/consts back, used only at call time.)
import {
  readScaffoldVersion, buildVersions, scaffoldDrift, runIntentMigrations, runPrewarm,
} from './lifecycle.mjs'
export { readScaffoldVersion, buildVersions, scaffoldDrift, runIntentMigrations }

// Use-case flow orchestrators (extracted to ./flows/*). Imported here for the
// entry-point dispatcher; packTemplate is also re-exported (tests import it from
// this module). Benign cycle: the flows import shared primitives back from here,
// referenced only inside their function bodies (call time), never at module eval.
import { runDashboardBuild } from './flows/build.mjs'
import { runIncrementalEdit } from './flows/edit.mjs'
import { packTemplate } from './flows/template.mjs'
export { packTemplate }

// ── Path constants ─────────────────────────────────────────────────────────────

const __dirname = dirname(fileURLToPath(import.meta.url))

// Widget generator templates ship INSIDE the starter-kit archive (under _gen/widgets),
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

/**
 * Fixed dev server port. Kept BELOW the ephemeral ranges (Linux 32768+, Windows/macOS
 * 49152+) so it can't land in an OS-reserved block — Windows (WinNAT/Hyper-V/WSL2)
 * carves reserved chunks out of the ephemeral range, and a dev server can't bind one
 * even when it's free (`An attempt was made to access a socket in a way forbidden by
 * its access permissions`). 25173 is high enough to dodge common dev servers yet clear
 * of every ephemeral range. Must match the scaffold's vite.config.ts `server.port`.
 */
export const DASHBOARD_PORT = 25173

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
 * @property {Object}      [params]      - T2 filter params (validation only — the filter logic lives in the metric module)
 * @property {string}      [module]      - Relative path to the metric's data-fetch module (defaults to metrics/<name>.ts)
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
 * @property {boolean}     [detail]         - kpi-card only: opt into a record-grain drill-down (module must export fetchDetail)
 * @property {Array}       [detailColumns]  - Structured columns for the detail view (falls back to registry defaults.detailColumns)
 * @property {string}      [detailSortKey]  - Raw field the detail table sorts on
 * @property {string}      [series]      - multi-line-chart series literal
 * @property {string}      [pivotExpression] - multi-line-chart pivot expression
 * @property {DetailViewSpec} [detailView]
 * @property {{key:string}} [rowLink]
 */

/**
 * The full intent.json structure.
 * @typedef {Object} DashboardIntent
 * @property {string}        dashboardName
 * @property {string}        [dashboardDescription] - One sentence for the dashboard header
 * @property {'1d'|'7d'|'30d'|'90d'} timeRange
 * @property {IntentMetric[]} metrics
 * @property {string}        projectDir  - Project dir; "." by contract (build runs from inside the pre-warmed <routingName> folder; must already exist)
 * @property {string}        routingName - Permanent URL slug (e.g. "agent-health-x7k2")
 * @property {string}        orgName
 * @property {string}        tenantName
 * @property {string}        cloudUrl    - e.g. https://cloud.uipath.com
 * @property {string}        apiUrl      - e.g. https://api.uipath.com
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
  'WIDGET_READY', 'METRICS_PASS', 'METRICS_RETRY', 'CHART_DETAIL_MISSING', 'T3_FAILED', 'TSC_PASS', 'TSC_FAIL',
  'BUILD_RESULT', 'PARTIAL_BUILD_DETECTED', 'AUTH_MISSING',
  'HAND_EDIT_DETECTED', 'T2_SCHEMA_ERROR', 'INCREMENTAL_READY', 'UPGRADE_AVAILABLE', 'UPGRADE_DONE',
  'TEMPLATE_BUILD', 'EJECTED', 'EJECTED_PROJECT', 'TEMPLATE_PACKED',
])

export const VALID_EDIT_OPS = ['ADD', 'REMOVE', 'CHANGE', 'REBUILD', 'UPGRADE', 'EJECT']

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
 * governance subpaths ship in 1.4.1; the Agents insights aggregates
 * (getSummary / getTopErrorCount / getTopConsumption / getIncidentDistribution
 * / getUnitConsumptionSummary) ship in 1.5.0. A stale lockfile/registry
 * otherwise surfaces as cryptic tsc "module not found" failures mid-build.
 */
export const MIN_SDK_VERSION = '1.5.1'

export const SKILL_VERSION = '2.2.0'        // 2.2 = runtime governance on AgentTraces getGovernanceDecisions/getGovernanceSummary (SDK 1.5.1)
const FIXTURE_ARCHIVE_PATH = resolve(__dirname, '../../fixtures/governance-dashboard-starter-kit.tar.gz')

export const INTENT_SCHEMA_VERSION = 2
export const STATE_SCHEMA_VERSION = 2

/**
 * Generate (or remove) a table widget's keyed row-click detail view. Writes
 * <Component>DetailView.tsx when the metric is a table with `rowLink`, and removes
 * a stale one otherwise. Shared by fresh build, ADD, CHANGE, REBUILD, and upgrade so
 * the row-click drill-down stays consistent on every path. Returns true if a keyed
 * view now exists on disk.
 * @returns {boolean}
 */
export function writeKeyedViewIfRowLink(P, componentName, metric, entry, timeRange) {
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
export function collectKeyedViews(P, state) {
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
    if (widgetGetsDetailView(info.template ?? '', m, entry)) {
      writeAtomic(viewPath, generateViewFile(buildViewSpec(componentName, m, entry, timeRange)))
    } else if (existsSync(viewPath)) {
      unlinkSync(viewPath)
    }
    writeKeyedViewIfRowLink(P, componentName, m, entry, timeRange)
  }
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
export const DASHBOARD_SCOPES = 'OR.Assets OR.Jobs OR.Folders OR.Buckets OR.Execution OR.Tasks OR.Queues OR.Users Insights Insights.RealTimeData Traces.Api PIMS'

// ── Low-level utilities ────────────────────────────────────────────────────────

export function fail(msg) {
  process.stderr.write(`ERROR: ${msg}\n`)
  process.exit(1)
}

export function log(msg) {
  process.stdout.write(msg + '\n')
}

/**
 * The agent extracts the starter-kit .tar.gz into the project dir before building,
 * using the OS `tar` (built into Windows 10+, macOS, Linux). This verifies the kit
 * landed (scaffold app + the _gen/widgets generator templates) and fails loud with
 * the extract command if not.
 * @param {string} projectPath
 */
export function assertScaffoldExtracted(projectPath) {
  const hasScaffold = existsSync(join(projectPath, 'package.json'))
  const hasTemplates = existsSync(join(projectPath, '_gen', 'widgets'))
  if (hasScaffold && hasTemplates) return
  fail([
    `Starter kit not extracted into: ${projectPath}`,
    `Extract it first with tar (built into Windows 10+, macOS, Linux).`,
    `Feed the archive on stdin (-f -) so GNU tar doesn't misread the C:\\ drive colon as a remote host:`,
    `  mkdir -p "${projectPath}" && tar -xz -C "${projectPath}" -f - < "${FIXTURE_ARCHIVE_PATH}"`,
    `Then re-run the build.`,
  ].join('\n'))
}

/**
 * Atomic file write — write to .tmp then rename on success.
 *
 * On Windows the rename can fail with EPERM/EBUSY when a watcher (e.g. the Vite
 * dev server during a REBUILD) holds the target file open. Retry the rename a
 * few times with a short backoff, then fall back to a direct overwrite so the
 * write still lands. A scoped CHANGE op touches one file and rarely races; a
 * full REBUILD rewrites every widget — prefer stopping the dev server first.
 */
export function writeAtomic(filePath, content) {
  mkdirSync(dirname(filePath), { recursive: true })
  const tmp = filePath + '.tmp'
  writeFileSync(tmp, content, 'utf8')
  const RETRYABLE = new Set(['EPERM', 'EBUSY', 'EACCES'])
  for (let attempt = 0; ; attempt++) {
    try {
      renameSync(tmp, filePath)
      return
    } catch (err) {
      if (!RETRYABLE.has(err?.code) || attempt >= 4) {
        // Out of retries (or a non-lock error): overwrite in place so the new
        // content still lands, then drop the tmp. Less atomic, but a held-open
        // widget file would otherwise block the whole build.
        try {
          writeFileSync(filePath, content, 'utf8')
          try { unlinkSync(tmp) } catch { /* ignore */ }
          return
        } catch {
          throw err
        }
      }
      // Busy-wait briefly (sync context): 50ms · 100ms · 150ms · 200ms.
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 50 * (attempt + 1))
    }
  }
}

export function hashContent(content) {
  return createHash('sha256').update(content).digest('hex').slice(0, 16)
}

export function toPascalCase(str) {
  return str.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join('')
}

// ── Pre-warm ───────────────────────────────────────────────────────────────────

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
 * Drills to RECORD GRAIN: the view runs the module's `fetchDetail` export — the
 * individual records behind the chart (e.g. each job run), not the aggregate. When
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
 * Decide whether a widget gets a generated record-grain detail view (+ route).
 * Single source of truth for fresh build, incremental ADD/CHANGE, rebuild, and
 * upgrade — keeps the "is this card clickable / does a view file exist" decision
 * consistent everywhere.
 *
 * - Chart widgets get a detail view UNLESS opted out with `noDetail: true` — set
 *   on the registry entry (T1/T2 catalog) OR on the metric in intent.json (T3,
 *   which has no registry entry). Used when the endpoint returns only
 *   pre-aggregated data, so a record drill-down would be fake. Opted-out charts
 *   render non-clickable.
 * - KPI cards get a detail view when `detail` is true — either set on the metric
 *   (`detail: true` in intent.json) or defaulted on by the registry entry
 *   (`defaults.detail: true`, for cataloged KPIs that have a feasible record-grain
 *   query). A metric can force it off with `detail: false`. The module must export
 *   `fetchDetail`. A KPI with no `detail` signal links nowhere.
 * - Tables never get a chart-style view here (they use `rowLink` keyed views).
 *
 * @param {string} template  displayAs / registry template
 * @param {object} [metric]  intent metric (KPI `detail`, T3 `noDetail`)
 * @param {object|null} [entry]  registry entry (catalog `noDetail` / `defaults.detail`)
 * @returns {boolean}
 */
export function widgetGetsDetailView(template, metric = {}, entry = null) {
  if (entry?.noDetail === true || metric?.noDetail === true) return false
  if (widgetLayoutGroup(template) === 'chart') return true
  if (template === 'kpi-card') {
    // Metric override wins; otherwise the registry entry may default it on for a
    // cataloged KPI whose drill-down records are queryable.
    return (metric?.detail ?? entry?.defaults?.detail ?? false) === true
  }
  return false
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
export function autoSubtitle(metric, defaults, timeRange) {
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
 * Build the spec passed to generateViewFile for a widget's detail view.
 * Shared by the fresh build and incremental ADD/CHANGE so detail views stay
 * consistent. The view always runs the module's record-grain `fetchDetail` export.
 * @param {string} componentName
 * @param {IntentMetric} metric
 * @param {object|null} entry - registry entry (for defaults)
 * @param {string} timeRange
 */
export function buildViewSpec(componentName, metric, entry, timeRange) {
  // Detail views show RECORD GRAIN: a chart/KPI exports `fetchData` (the
  // aggregate the widget renders) AND `fetchDetail` (the individual records
  // behind it). The view always runs `fetchDetail` — every chart metric is
  // required to export it (enforced by the CHART_DETAIL_MISSING gate), and a
  // KPI reaches this path only with `detail: true`. detailColumns fall back to
  // the registry defaults so a cataloged metric's drill-down is styled with no
  // intent.json config.
  const detailColumns = metric.detailColumns ?? entry?.defaults?.detailColumns
  return {
    componentName,
    title: metric.title ?? entry?.defaults?.title ?? componentName,
    subtitle: autoSubtitle(metric, entry?.defaults ?? {}, timeRange),
    moduleSpecifier: metricModuleSpecifier(metric),
    detailExport: 'fetchDetail',
    detailColumns: detailColumns ? compileColumns(detailColumns) : null,
    defaultSortKey: metric.detailSortKey ?? entry?.defaults?.detailSortKey,
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
    // noDetail charts (Insights endpoints with only pre-aggregated data) get NO
    // drill-down: an empty DETAIL_ROUTE makes the template render a non-clickable
    // card (no cursor-pointer, no ViewAllLink). Step 5a then skips the view file.
    const hasDetail = widgetGetsDetailView(displayAs, metric, registryEntry)
    const spec = {
      componentName,
      template:          displayAs,
      detailRoute:       hasDetail ? (metric.detailRoute ?? `/${componentName.toLowerCase()}`) : '',
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
  // kpi-card defaults to the conventional { value, previous } shape. Without a
  // valueField the shell renders data.length (the "headline 1" bug) — invisible
  // until you look at live data. Default it; if a metric explicitly clears it,
  // fail loud rather than silently show the row count.
  const isKpiCard    = displayAs === 'kpi-card'
  const valueField   = metric.valueField ?? defaults.valueField ?? (isKpiCard ? 'value' : '')
  const valueLabel   = metric.valueLabel ?? defaults.valueLabel ?? ''
  // previousField defaults only for the conventional { value, previous } shape;
  // a custom valueField (e.g. "count") gets no unsolicited badge field. The
  // badge still renders only when the module actually returns a previous value.
  const previousField = metric.previousField ?? defaults.previousField
    ?? (isKpiCard && valueField === 'value' ? 'previous' : '')
  if (isKpiCard && !valueField) {
    throw new Error(
      `kpi-card metric "${metric.name}" has no valueField — it would silently render the ` +
      `row count instead of the metric. Set valueField (e.g. "value") in the metric or ` +
      `registry defaults, and have the module return [{ value, previous? }].`,
    )
  }
  const deltaPolarity = metric.deltaPolarity ?? defaults.deltaPolarity ?? 'neutral'
  const rowLinkKey   = metric.rowLink?.key ?? defaults.rowLink?.key ?? ''
  const rowLinkRoute = rowLinkKey ? `/${componentName.toLowerCase()}` : ''
  // KPI drill-down: a kpi-card with `detail: true` (module exports fetchDetail)
  // becomes a clickable card that navigates to its record-grain view. Empty for
  // a plain KPI or any table (tables drill via ROW_LINK, not the card). Step 5a
  // generates the matching view + route when this is set.
  const kpiDetailRoute = widgetGetsDetailView(displayAs, metric, registryEntry)
    ? (metric.detailRoute ?? `/${componentName.toLowerCase()}`) : ''
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
    .split('<<KPI_DETAIL_ROUTE>>').join(kpiDetailRoute)
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




// ── Entry point ────────────────────────────────────────────────────────────────

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {

  // --prewarm <routingName|projectDir> mode: run npm ci in an already-extracted
  // project, then exit. The agent extracts the starter-kit archive into
  // <cwd>/<routingName> first. resolve() (not join()) so an ABSOLUTE path is
  // honored as-is — join(cwd, '/abs/path') concatenates into a broken path on
  // Windows (C:\cwd\C:\abs\path) and npm ci runs in the wrong place.
  if (process.argv[2] === '--prewarm' && process.argv[3]) {
    const routingName = process.argv[3]
    const prewarmDir  = resolve(process.cwd(), routingName)
    assertScaffoldExtracted(prewarmDir)
    await runPrewarm(prewarmDir)
    process.exit(0)
  }

  // --pack-template <projectDir> mode: stage modify-face source + template.json
  // into dist/_source for a one-artifact template package (run after `npm run build`).
  if (process.argv[2] === '--pack-template' && process.argv[3]) {
    packTemplate(process.argv[3])
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
