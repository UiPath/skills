#!/usr/bin/env node
/**
 * build-dashboard.mjs — Single-shot dashboard builder
 *
 * Reads an approved build plan from stdin (JSON), then:
 *   1. Copies scaffold to PROJECT_DIR (Node.js fs — cross-platform, no cp -r)
 *   2. Checks pre-warm; runs npm ci if not done
 *   3. Writes .env.local
 *   4. Writes all widget + view + Dashboard.tsx + index.ts files
 *   5. Updates App.tsx route markers
 *   6. Runs tsc --noEmit
 *   7. Writes .dashboard/state.json
 *   8. Starts dev server and outputs the URL
 *
 * Plan JSON supports two modes for widget content:
 *
 *   Mode A — files map (legacy / agent-authored TypeScript):
 *     "files": { "src/dashboard/widgets/Foo.tsx": "<full tsx>", ... }
 *
 *   Mode B — widgets array (template substitution — preferred):
 *     "widgets": [ { "componentName": "Foo", "template": "kpi-card", ... } ]
 *     The script loads pre-tested template files and applies <PLACEHOLDER> substitution.
 *     TypeScript is always correct because templates are pre-validated.
 *
 * Both modes may coexist: widgets[] generates widget + view files; files{} writes
 * Dashboard.tsx, index.ts, App.tsx (anything the agent still authors directly).
 *
 * Usage:
 *   node build-dashboard.mjs <plan.json>          ← recommended (cross-platform)
 *   node build-dashboard.mjs /path/to/plan.json
 *
 * Exit 0 = success, exit 1 = failure (message on stderr).
 */

import { readFileSync, writeFileSync, copyFileSync, mkdirSync, readdirSync, existsSync, renameSync, unlinkSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { execSync, spawn } from 'child_process';
import { createHash } from 'crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCAFFOLD_DIR = resolve(__dirname, '../templates/dashboard/scaffold');
const WIDGETS_DIR = resolve(__dirname, '../templates/dashboard/widgets');
const T3_SHELL_TEMPLATE_PATH = resolve(__dirname, '../templates/dashboard/widgets/t3-shell.tsx.template');

// ── Capability registry ───────────────────────────────────────────────────────

const REGISTRY = JSON.parse(readFileSync(resolve(__dirname, 'capability-registry.json'), 'utf8'));

// ── intent.json validator ─────────────────────────────────────────────────────

export function validateIntent(intent) {
  const errors = []
  if (!intent.dashboardName || typeof intent.dashboardName !== 'string') errors.push('dashboardName must be a non-empty string')
  if (!['1d','7d','30d','90d'].includes(intent.timeRange)) errors.push(`timeRange must be one of: 1d, 7d, 30d, 90d`)
  if (!Array.isArray(intent.metrics) || intent.metrics.length === 0) errors.push('metrics must be a non-empty array')
  for (const m of (intent.metrics ?? [])) {
    if (!m.name) errors.push('metric missing name')
    if (!['T1','T2','T3'].includes(m.tier)) errors.push(`metric "${m.name}" has invalid tier: ${m.tier}`)
    if (m.tier === 'T2' && !m.params) errors.push(`T2 metric "${m.name}" missing params`)
    if (m.tier === 'T3' && !m.fnBody) errors.push(`T3 metric "${m.name}" missing fnBody`)
    if (m.tier === 'T3' && !m.displayAs) errors.push(`T3 metric "${m.name}" missing displayAs`)
    if (m.tier === 'T3' && !m.title) errors.push(`T3 metric "${m.name}" missing title`)
  }
  return errors
}

// ── Resolution Engine ─────────────────────────────────────────────────────────

const TIME_RANGE_CONSTANTS = {
  '1d':  'ONE_DAY_AGO',
  '7d':  'SEVEN_DAYS_AGO',
  '30d': 'THIRTY_DAYS_AGO',
  '90d': 'NINETY_DAYS_AGO',
}

function toPascalCase(str) {
  return str.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join('')
}

export function resolveMetric(metric) {
  if (metric.tier === 'T3') return { tier: 'T3', key: metric.name, entry: null }
  const registrySection = metric.tier === 'T1' ? REGISTRY.t1 : REGISTRY.t2
  const entry = registrySection[metric.name]
  if (!entry) {
    throw new Error(`Metric "${metric.name}" (${metric.tier}) not found in registry. Available: ${Object.keys(registrySection).join(', ')}`)
  }
  return { tier: metric.tier, key: metric.name, entry }
}

export function buildT1WidgetSpec(metric, entry, timeRange) {
  const startConst = TIME_RANGE_CONSTANTS[timeRange] ?? 'THIRTY_DAYS_AGO'
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const responseType = '{ data: Array<Record<string, unknown>> }'
  const dataHook = `useInsights<${responseType}>('${entry.namespace}.${entry.method}', { startTime: ${startConst}, endTime: NOW })`
  return {
    componentName,
    template: entry.template,
    detailRoute: metric.detailRoute ?? `/${componentName.toLowerCase()}`,
    icon: metric.icon ?? entry.defaults.icon,
    title: metric.title ?? entry.defaults.title,
    description: metric.description ?? entry.defaults.description,
    dataHook,
    dataSelector: entry.defaults.dataSelector ?? '[]',
    xKey: entry.defaults.xKey ?? 'date',
    yKey: entry.defaults.yKey ?? 'value',
    valueExpression: entry.defaults.valueExpression ?? "'—'",
    columns: metric.columns ?? entry.defaults.columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]',
    deltaDir: entry.defaults.deltaDir ?? 'neutral',
    deltaText: entry.defaults.deltaText ?? '',
    series: entry.defaults.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]',
    pivotExpression: entry.defaults.pivotExpression ?? 'rawData',
  }
}

const VALID_T2_OPS = ['gt', 'lt', 'eq', 'gte', 'lte', 'neq']
const T2_OP_TO_JS = { gt: '>', lt: '<', eq: '===', gte: '>=', lte: '<=', neq: '!==' }

export function compileT2ToTypeScript(descriptor) {
  const { sdkService, method, filterField, filterOp, filterValue, sortField, sortDir } = descriptor
  if (!VALID_T2_OPS.includes(filterOp)) {
    throw new Error(`T2 descriptor has invalid op: ${filterOp}. Must be one of: ${VALID_T2_OPS.join(', ')}`)
  }
  const jsOp = T2_OP_TO_JS[filterOp]
  const sortFn = sortDir === 'asc'
    ? `items.sort((a, b) => (a.${sortField} ?? 0) - (b.${sortField} ?? 0))`
    : `items.sort((a, b) => (b.${sortField} ?? 0) - (a.${sortField} ?? 0))`
  return `async (sdk, _getToken) => {
  const svc = new ${sdkService}(sdk as never)
  const result = await svc.${method}({})
  const items = (result?.items ?? result?.value ?? []) as Array<Record<string, number>>
  const filtered = items.filter(item => (item.${filterField} ?? 0) ${jsOp} ${filterValue})
  ${sortFn}
  return filtered
}`
}

export function buildT2WidgetSpec(metric, entry) {
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const { params } = metric
  const descriptor = {
    service: entry.service,
    sdkImport: entry.sdkImport,
    sdkService: entry.sdkService,
    method: entry.method,
    filterField: params.field ?? entry.filterField,
    filterOp: params.direction ?? 'gt',
    filterValue: params.threshold ?? params.value ?? 0,
    sortField: params.sortField ?? entry.sortField,
    sortDir: params.sortDir ?? 'desc',
  }
  const sdkHookCode = compileT2ToTypeScript(descriptor)
  return {
    componentName,
    template: metric.displayAs ?? entry.defaultDisplayAs,
    sdkImport: entry.sdkImport,
    sdkService: entry.sdkService,
    sdkHookCode,
    title: metric.title ?? entry.defaults.title,
    description: metric.description ?? entry.defaults.description,
    icon: metric.icon ?? entry.defaults.icon,
    columns: metric.columns ?? entry.defaults.columns,
    detailRoute: metric.detailRoute ?? `/${componentName.toLowerCase()}`,
    deltaDir: entry.defaults.deltaDir ?? 'neutral',
    deltaText: entry.defaults.deltaText ?? '',
    dataSelector: entry.defaults.dataSelector ?? '(data as any)?.items ?? []',
  }
}

export function buildT3WidgetFile(metric) {
  if (!metric.fnBody) throw new Error(`T3 metric "${metric.name}" missing fnBody`)
  if (!existsSync(T3_SHELL_TEMPLATE_PATH)) {
    throw new Error(`T3 shell template not found at ${T3_SHELL_TEMPLATE_PATH}`)
  }
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const iconName = metric.icon ?? 'Activity'
  const indentedFnBody = metric.fnBody.split('\n').map(l => '  ' + l).join('\n')
  let content = readFileSync(T3_SHELL_TEMPLATE_PATH, 'utf8')
  content = content
    .split('<<FN_BODY>>').join(indentedFnBody)
    .split('<<COMPONENT_NAME>>').join(componentName)
    .split('<<TITLE>>').join(metric.title ?? componentName)
    .split('<<DESCRIPTION>>').join(metric.description ?? '')
    .split('<<ICON_NAME>>').join(iconName)
  return content
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function fail(msg) {
  process.stderr.write(`ERROR: ${msg}\n`);
  process.exit(1);
}

const KNOWN_EVENTS = new Set([
  'PREWARM_START','PREWARM_DONE','PREWARM_FAILED','SCAFFOLD_READY','ENV_WRITTEN',
  'WIDGET_READY','T3_RETRY','T3_FAILED','TSC_PASS','TSC_FAIL',
  'SERVER_READY','BUILD_RESULT','PARTIAL_BUILD_DETECTED','AUTH_MISSING',
  'HAND_EDIT_DETECTED','T2_SCHEMA_ERROR','INCREMENTAL_READY'
])

export function emit(type, payload = null, writer = process.stdout) {
  const line = payload != null ? `${type}:${JSON.stringify(payload)}` : type
  writer.write(line + '\n')
}

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

function log(msg) {
  process.stdout.write(msg + '\n');
}

/** Recursive directory copy — Node.js only, no cp -r, works on Windows */
function copyDir(src, dest) {
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src, { withFileTypes: true })) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

/** Atomic file write — write to .tmp then rename on success */
function writeAtomic(filePath, content) {
  mkdirSync(dirname(filePath), { recursive: true });
  const tmp = filePath + '.tmp';
  writeFileSync(tmp, content, 'utf8');
  renameSync(tmp, filePath);
}

// ── Pre-warm ──────────────────────────────────────────────────────────────────

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

export function waitForPrewarm(projectPath, timeoutMs = 60_000) {
  const signal = join(projectPath, 'node_modules', '.package-lock.json')
  const deadline = Date.now() + timeoutMs
  while (!existsSync(signal)) {
    if (Date.now() > deadline) {
      emit('PREWARM_FAILED', { exitCode: -1, stderr: 'Timed out waiting for pre-warm' })
      throw new Error('Pre-warm timed out after 60s')
    }
    execSync('node -e "setTimeout(()=>{},500)"', { stdio: 'pipe' })
  }
  emit('PREWARM_DONE')
}

// ── Content hashing ───────────────────────────────────────────────────────────

function hashContent(content) {
  return createHash('sha256').update(content).digest('hex').slice(0, 16)
}

// ── Dashboard file generation ─────────────────────────────────────────────────

function generateDashboardFiles(projectPath, widgetNames, dashboardName) {
  const imports = widgetNames.map(n => `import { ${n} } from './widgets/${n}'`).join('\n')
  const indexTs = widgetNames.map(n => `export { ${n} } from './${n}'`).join('\n') + '\n'
  const grid = widgetNames.length === 1 ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'
  const dashboardJsx = `import React from 'react'
import { Header } from '@/dashboard/chrome/Header'
${imports}

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <Header title="${dashboardName}" description="Operational metrics dashboard" />
      <div className="p-4 md:p-8">
        <div className="grid ${grid} gap-4">
          ${widgetNames.map(n => `<${n} />`).join('\n          ')}
        </div>
      </div>
    </div>
  )
}
`
  writeAtomic(join(projectPath, 'src', 'dashboard', 'Dashboard.tsx'), dashboardJsx)
  writeAtomic(join(projectPath, 'src', 'dashboard', 'widgets', 'index.ts'), indexTs)
}

// ── Template substitution ─────────────────────────────────────────────────────

const TIME_CONSTANTS = `const NOW = new Date().toISOString()
const ONE_DAY_AGO = new Date(Date.now() - 86_400_000).toISOString()
const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000).toISOString()
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000).toISOString()
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000).toISOString()
`;

/**
 * Load a widget template and apply <PLACEHOLDER> substitutions.
 * Injects time constants after the last import line.
 */
function applyTemplate(templateName, subs) {
  const templatePath = join(WIDGETS_DIR, `${templateName}.tsx`);
  if (!existsSync(templatePath)) fail(`Template not found: ${templateName}.tsx in ${WIDGETS_DIR}`);
  let content = readFileSync(templatePath, 'utf8');

  // Apply all substitutions
  for (const [key, value] of Object.entries(subs)) {
    content = content.split(`<${key}>`).join(value);
  }

  // Inject time constants after the last import line
  const lines = content.split('\n');
  let lastImportIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('import ')) lastImportIdx = i;
  }
  if (lastImportIdx >= 0) {
    lines.splice(lastImportIdx + 1, 0, '', TIME_CONSTANTS.trimEnd());
    content = lines.join('\n');
  }

  return content;
}

/**
 * Generate a detail view file (always DetailViewShell + RecordsTable).
 * This is always script-generated — agents never write view files directly.
 */
function generateViewFile(widget) {
  const { componentName, title, description, dataHook, dataSelector, columns } = widget;
  const cols = columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]';
  return `import React from 'react'
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useInsights } from '@/hooks/useInsights'
import { LoadingState, EmptyState } from '@/dashboard/chrome'

${TIME_CONSTANTS.trimEnd()}

const COLUMNS: ColumnDef<Record<string, unknown>>[] = ${cols}

export function ${componentName}View() {
  const { data, loading, error } = ${dataHook}
  const rows: Record<string, unknown>[] = ${dataSelector ?? '[]'}
  if (loading) return <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}"><LoadingState height="h-96" /></DetailViewShell>
  if (error)   return <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}"><EmptyState message={error.message} /></DetailViewShell>
  return (
    <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}">
      <RecordsTable rows={rows} columns={COLUMNS} defaultSortKey={COLUMNS[0]?.key as string} />
    </DetailViewShell>
  )
}
`;
}

// ── runDashboardBuild pipeline ────────────────────────────────────────────────

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
      try {
        execSync(`node -e "require('fs').rmSync(${JSON.stringify(join(P,'node_modules'))},{recursive:true,force:true})"`,
          { stdio: 'pipe' })
      } catch { /* ignore */ }
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
    ].join('\n'))
    const uipathJsonPath = join(P, 'uipath.json')
    if (existsSync(uipathJsonPath) && clientId) {
      const uj = JSON.parse(readFileSync(uipathJsonPath, 'utf8'))
      uj.clientId = clientId
      writeAtomic(uipathJsonPath, JSON.stringify(uj, null, 2))
    }
    emit('ENV_WRITTEN')

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
    const t1t2Metrics = metrics.filter(m => m.tier !== 'T3')
    const t3Metrics = metrics.filter(m => m.tier === 'T3')
    const widgetHashes = {}
    let widgetIndex = 0
    const total = metrics.length

    // T1 + T2 in parallel
    await Promise.all(t1t2Metrics.map(async (metric) => {
      const { tier, entry } = resolveMetric(metric)
      let widgetContent, componentName

      if (tier === 'T1') {
        const spec = buildT1WidgetSpec(metric, entry, timeRange)
        componentName = spec.componentName
        widgetContent = applyTemplate(spec.template, {
          COMPONENT_NAME: spec.componentName,
          TITLE: spec.title,
          DESCRIPTION: spec.description,
          DETAIL_ROUTE: spec.detailRoute,
          ICON: spec.icon,
          DATA_HOOK: spec.dataHook,
          DATA_SELECTOR: spec.dataSelector,
          X_KEY: spec.xKey,
          Y_KEY: spec.yKey,
          VALUE_EXPRESSION: spec.valueExpression,
          COLUMNS: spec.columns,
          DELTA_DIR: spec.deltaDir,
          DELTA_TEXT: spec.deltaText,
          SERIES: spec.series,
          PIVOT_EXPRESSION: spec.pivotExpression,
          SDK_IMPORT: '', SDK_SERVICE: '', SDK_CALL: '', SDK_RESULT_TYPE: '',
        })
      } else {
        // T2
        const spec = buildT2WidgetSpec(metric, entry)
        componentName = spec.componentName
        widgetContent = applyTemplate('sdk-data-table', {
          COMPONENT_NAME: spec.componentName,
          TITLE: spec.title,
          DESCRIPTION: spec.description,
          DETAIL_ROUTE: spec.detailRoute,
          ICON: spec.icon,
          SDK_IMPORT: spec.sdkImport,
          SDK_SERVICE: spec.sdkService,
          SDK_CALL: `getAll({})`,
          SDK_RESULT_TYPE: 'any',
          COLUMNS: spec.columns,
          DELTA_DIR: spec.deltaDir ?? 'neutral',
          DELTA_TEXT: spec.deltaText ?? '',
          DATA_HOOK: '', DATA_SELECTOR: spec.dataSelector.replace(/\bdata\b/g, 'result'), X_KEY: '', Y_KEY: '',
          VALUE_EXPRESSION: '', SERIES: '', PIVOT_EXPRESSION: '',
        })
      }

      const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
      writeAtomic(widgetPath, widgetContent)
      widgetHashes[componentName] = { hash: hashContent(widgetContent), tier, metric: metric.name }
      widgetIndex++
      emit('WIDGET_READY', { name: componentName, index: widgetIndex, total })
    }))

    // T3 widgets — sequential (may require agent retry)
    for (const metric of t3Metrics) {
      let attempts = 0
      let success = false
      while (attempts < 3 && !success) {
        attempts++
        const currentIntent = JSON.parse(readFileSync(intentPath, 'utf8'))
        const currentMetric = currentIntent.metrics.find(m => m.name === metric.name) ?? metric
        let widgetContent
        try {
          widgetContent = buildT3WidgetFile(currentMetric)
        } catch (e) {
          emit('T3_FAILED', { widget: metric.name, reason: e.message })
          fail(`T3 widget "${metric.name}" failed: ${e.message}`)
        }
        const componentName = toPascalCase(metric.name)
        const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
        writeAtomic(widgetPath, widgetContent)

        try {
          execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
          widgetHashes[componentName] = { hash: hashContent(widgetContent), tier: 'T3', metric: metric.name }
          widgetIndex++
          emit('WIDGET_READY', { name: componentName, index: widgetIndex, total })
          success = true
        } catch (e) {
          const errors = (e.stdout?.toString() ?? '').split('\n').filter(l => l.includes('error TS')).slice(0, 5)
          if (attempts >= 3) {
            emit('T3_FAILED', { widget: metric.name, errors, attempts })
            fail(`T3 widget "${metric.name}" failed after 3 attempts`)
          }
          emit('T3_RETRY', { widget: metric.name, errors, intentPath, retryCount: attempts })
          log(`⚠ T3 "${metric.name}" has TypeScript errors (attempt ${attempts}/3). Update fnBody in ${intentPath} and re-run.`)
          process.exit(2)
        }
      }
    }

    // Step 5 — Generate Dashboard.tsx + index.ts
    generateDashboardFiles(P, Object.keys(widgetHashes), dashboardName)

    // Step 6 — Full tsc
    try {
      execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
      emit('TSC_PASS')
    } catch (e) {
      const err = e.stdout?.toString() || e.stderr?.toString() || String(e)
      emit('TSC_FAIL', { errors: err.slice(0, 1000) })
      fail(`TypeScript errors:\n${err}`)
    }

    // Step 7 — Write state.json
    const stateDir = join(P, '.dashboard')
    mkdirSync(stateDir, { recursive: true })
    const statePath = join(stateDir, 'state.json')
    const existingState = existsSync(statePath) ? JSON.parse(readFileSync(statePath, 'utf8')) : {}
    const newState = {
      schemaVersion: 2,
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
      widgets: widgetHashes,
      deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
    }
    writeAtomic(statePath, JSON.stringify(newState, null, 2))

    // Step 8 — Start dev server
    const isWindows = process.platform === 'win32'
    const server = spawn('npm', ['run', 'dev'], {
      cwd: P, detached: true, stdio: 'pipe', shell: isWindows,
    })
    server.on('error', () => {})
    server.unref()

    let port = 5173
    const deadline = Date.now() + 8000
    while (Date.now() < deadline) {
      try {
        execSync(
          `node -e "require('http').get('http://localhost:${port}',r=>process.exit(r.statusCode<500?0:1)).on('error',()=>process.exit(1))"`,
          { stdio: 'pipe', timeout: 1000 }
        )
        break
      } catch { port++; if (port > 5183) { port = 5173; break } }
    }

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

// ── Incremental editing ───────────────────────────────────────────────────────

const VALID_EDIT_OPS = ['ADD', 'REMOVE', 'CHANGE', 'REBUILD']

export function classifyEditIntent(editIntent) {
  if (!VALID_EDIT_OPS.includes(editIntent.op)) {
    throw new Error(`classifyEditIntent: invalid op "${editIntent.op}". Must be one of: ${VALID_EDIT_OPS.join(', ')}`)
  }
  return editIntent
}

async function runIncrementalEdit(editIntent, intentPath) {
  const { projectDir } = editIntent
  if (!projectDir) fail('edit-intent.projectDir is required')
  const P = resolve(projectDir)
  const statePath = join(P, '.dashboard', 'state.json')
  if (!existsSync(statePath)) fail('No .dashboard/state.json found. Run a fresh build first.')
  const state = JSON.parse(readFileSync(statePath, 'utf8'))
  const { op, target, metric, delta } = classifyEditIntent(editIntent)
  const timeRange = state.timeRange ?? '30d'

  if (op === 'ADD') {
    const { tier, entry } = resolveMetric(metric)
    let widgetContent, componentName

    if (tier === 'T1') {
      const spec = buildT1WidgetSpec(metric, entry, timeRange)
      componentName = spec.componentName
      widgetContent = applyTemplate(spec.template, {
        COMPONENT_NAME: spec.componentName, TITLE: spec.title, DESCRIPTION: spec.description,
        DETAIL_ROUTE: spec.detailRoute, ICON: spec.icon, DATA_HOOK: spec.dataHook,
        DATA_SELECTOR: spec.dataSelector, X_KEY: spec.xKey, Y_KEY: spec.yKey,
        VALUE_EXPRESSION: spec.valueExpression, COLUMNS: spec.columns,
        DELTA_DIR: spec.deltaDir, DELTA_TEXT: spec.deltaText,
        SERIES: spec.series, PIVOT_EXPRESSION: spec.pivotExpression,
        SDK_IMPORT: '', SDK_SERVICE: '', SDK_CALL: '', SDK_RESULT_TYPE: '',
      })
    } else if (tier === 'T3') {
      componentName = toPascalCase(metric.name)
      widgetContent = buildT3WidgetFile(metric)
    } else {
      const spec = buildT2WidgetSpec(metric, entry)
      componentName = spec.componentName
      widgetContent = applyTemplate('sdk-data-table', {
        COMPONENT_NAME: componentName, TITLE: spec.title, DESCRIPTION: spec.description,
        DETAIL_ROUTE: spec.detailRoute, ICON: spec.icon, SDK_IMPORT: spec.sdkImport,
        SDK_SERVICE: spec.sdkService, SDK_CALL: 'getAll({})',
        SDK_RESULT_TYPE: 'any',
        COLUMNS: spec.columns, DELTA_DIR: spec.deltaDir ?? 'neutral', DELTA_TEXT: spec.deltaText ?? '',
        DATA_HOOK: '', DATA_SELECTOR: spec.dataSelector.replace(/\bdata\b/g, 'result'), X_KEY: '', Y_KEY: '', VALUE_EXPRESSION: '', SERIES: '', PIVOT_EXPRESSION: '',
      })
    }

    const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
    writeAtomic(widgetPath, widgetContent)
    state.widgets = state.widgets ?? {}
    state.widgets[componentName] = { hash: hashContent(widgetContent), tier, metric: metric.name }

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
    if (tier === 'T1') {
      const { entry } = resolveMetric(metricRef)
      const spec = buildT1WidgetSpec(metricRef, entry, delta?.timeRange ?? timeRange)
      const widgetContent = applyTemplate(spec.template, {
        COMPONENT_NAME: spec.componentName, TITLE: spec.title, DESCRIPTION: spec.description,
        DETAIL_ROUTE: spec.detailRoute, ICON: spec.icon, DATA_HOOK: spec.dataHook,
        DATA_SELECTOR: spec.dataSelector, X_KEY: spec.xKey, Y_KEY: spec.yKey,
        VALUE_EXPRESSION: spec.valueExpression, COLUMNS: spec.columns,
        DELTA_DIR: spec.deltaDir, DELTA_TEXT: spec.deltaText,
        SERIES: spec.series, PIVOT_EXPRESSION: spec.pivotExpression,
        SDK_IMPORT: '', SDK_SERVICE: '', SDK_CALL: '', SDK_RESULT_TYPE: '',
      })
      writeAtomic(widgetPath, widgetContent)
      if (state.widgets) state.widgets[target] = { hash: hashContent(widgetContent), tier, metric: metricRef.name }
    }
  }

  // Regenerate Dashboard.tsx + index.ts
  const widgetNames = Object.keys(state.widgets ?? {})
  generateDashboardFiles(P, widgetNames, state.app?.name ?? 'Dashboard')

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

// ── Main ──────────────────────────────────────────────────────────────────────

if (import.meta.url === pathToFileURL(process.argv[1]).href) {

// Accept plan as file path argument — cross-platform, no /dev/stdin issues on Windows
const planArg = process.argv[2];
if (!planArg) fail('Usage: node build-dashboard.mjs <plan.json>');

let plan;
try {
  plan = JSON.parse(readFileSync(planArg, 'utf8'));
} catch (e) {
  fail(`Could not read plan JSON from ${planArg}: ${e.message}`);
}

// Route based on input type
if (plan.metrics) {
  // New intent.json path
  const intentErrors = validateIntent(plan)
  if (intentErrors.length > 0) fail(`Invalid intent.json:\n${intentErrors.map(e => '  • ' + e).join('\n')}`)
  await runDashboardBuild(plan, planArg)
} else if (plan.op) {
  const { op } = classifyEditIntent(plan)
  await runIncrementalEdit(plan, planArg)
} else {
  // Legacy plan.json path — unchanged
  const {
    projectDir,
    dashboardName,
    routingName,
    orgName,
    tenantName,
    cloudUrl,
    apiUrl,
    tenantId,
    clientId = '',               // external OAuth app client ID
    files = {},                  // { 'relative/path': 'file content' } — agent-authored files
    widgets: planWidgets = [],   // widget config array — script generates TypeScript via templates
    appTsxImports,
    appTsxRoutes,
  } = plan;

  if (!projectDir) fail('plan.projectDir is required');
  if (!routingName) fail('plan.routingName is required');

  const P = resolve(projectDir);

  // Step 1 — Copy scaffold (cross-platform Node.js, no cp -r)
  log('⚙ Copying scaffold…');
  if (!existsSync(SCAFFOLD_DIR)) fail(`Scaffold not found at ${SCAFFOLD_DIR}`);
  copyDir(SCAFFOLD_DIR, P);

  // Remove stale node_modules if present in scaffold (prevents npm ci ENOTEMPTY)
  try {
    execSync(`node -e "require('fs').rmSync(${JSON.stringify(join(P, 'node_modules'))},{recursive:true,force:true})"`,
      { stdio: 'pipe' });
  } catch { /* ignore */ }

  // Step 2 — Write .env.local
  log('⚙ Writing environment config…');
  writeAtomic(join(P, '.env.local'), [
    `VITE_UIPATH_CLOUD_URL=${cloudUrl}`,
    `VITE_UIPATH_BASE_URL=${apiUrl}`,
    `VITE_UIPATH_ORG_NAME=${orgName}`,
    `VITE_UIPATH_TENANT_NAME=${tenantName}`,
    `VITE_INSIGHTS_TENANT_ID=${tenantId}`,
    `VITE_UIPATH_CLIENT_ID=${clientId}`,
  ].join('\n'));

  // Update uipath.json with clientId from plan
  const uipathJsonPath = join(P, 'uipath.json');
  if (existsSync(uipathJsonPath) && clientId) {
    const uj = JSON.parse(readFileSync(uipathJsonPath, 'utf8'));
    uj.clientId = clientId;
    writeAtomic(uipathJsonPath, JSON.stringify(uj, null, 2));
  }

  // Step 3 — Pre-warm guarantee: ensure dependencies installed before any code gen
  const LOCK_SIGNAL = join(P, 'node_modules', '.package-lock.json');
  const PREWARM_LOCK = join(P, '.prewarm.lock');
  if (!existsSync(LOCK_SIGNAL)) {
    if (existsSync(PREWARM_LOCK)) {
      log('⏳ Waiting for pre-warm to complete…')
      waitForPrewarm(P)
    } else {
      log('⚙ Installing dependencies…')
      await runPrewarm(P)
    }
  } else {
    emit('PREWARM_DONE')
    log('✓ Dependencies ready (pre-warm)')
  }

  // Step 4 — Write agent-authored files (files map — Dashboard.tsx, index.ts, etc.)
  log('⚙ Writing dashboard files…');
  for (const [relativePath, content] of Object.entries(files)) {
    writeAtomic(join(P, relativePath), content);
  }

  // Step 4b — Process widgets array via template substitution
  const generatedWidgetNames = [];

  if (planWidgets.length > 0) {
    log(`⚙ Generating ${planWidgets.length} widget(s) from templates…`);
  }

  for (const widget of planWidgets) {
    const { componentName, template } = widget;
    if (!componentName) fail(`Widget entry missing required field: componentName`);
    if (!template) fail(`Widget "${componentName}" missing required field: template`);

    // Build substitution map — all known placeholders with defaults
    const subs = {
      COMPONENT_NAME: componentName,
      TITLE: widget.title ?? componentName,
      DESCRIPTION: widget.description ?? '',
      DETAIL_ROUTE: widget.detailRoute ?? `/${componentName.toLowerCase()}`,
      ICON: widget.icon ?? 'Activity',
      DATA_HOOK: widget.dataHook ?? `useInsights('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })`,
      DATA_SELECTOR: widget.dataSelector ?? '[]',
      X_KEY: widget.xKey ?? 'date',
      Y_KEY: widget.yKey ?? 'value',
      VALUE_EXPRESSION: widget.valueExpression ?? "'—'",
      COLUMNS: widget.columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]',
      DATA_KEY: widget.dataKey ?? 'value',
      NAME_KEY: widget.nameKey ?? 'name',
      DELTA_DIR: widget.deltaDir ?? 'neutral',
      DELTA_TEXT: widget.deltaText ?? '',
      SERIES: widget.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]',
      PIVOT_EXPRESSION: widget.pivotExpression ?? 'rawData',
      SDK_IMPORT: widget.sdkImport ?? '',
      SDK_SERVICE: widget.sdkService ?? '',
      SDK_CALL: widget.sdkCall ?? '',
      SDK_RESULT_TYPE: widget.sdkResultType ?? '{ items?: Array<Record<string, unknown>> }',
    };

    // Generate widget file from template
    const widgetContent = applyTemplate(template, subs);
    writeAtomic(join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`), widgetContent);

    // Generate view file (always DetailViewShell + RecordsTable)
    const viewContent = generateViewFile(widget);
    writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`), viewContent);

    generatedWidgetNames.push(componentName);
  }

  // Step 5 — Update App.tsx route markers
  if (appTsxImports || appTsxRoutes) {
    const appPath = join(P, 'src', 'app', 'App.tsx');
    // Fall back to src/App.tsx if src/app/App.tsx doesn't exist
    const appFile = existsSync(appPath) ? appPath : join(P, 'src', 'App.tsx');
    let appContent = readFileSync(appFile, 'utf8');

    if (appTsxImports) {
      appContent = appContent.replace(
        /\/\/ GENERATED_IMPORTS_START[\s\S]*?\/\/ GENERATED_IMPORTS_END/,
        `// GENERATED_IMPORTS_START\n${appTsxImports}// GENERATED_IMPORTS_END`
      );
    }
    if (appTsxRoutes) {
      appContent = appContent.replace(
        /\{\/\* GENERATED_ROUTES_START \*\/\}[\s\S]*?\{\/\* GENERATED_ROUTES_END \*\/\}/,
        `{/* GENERATED_ROUTES_START */}\n${appTsxRoutes}{/* GENERATED_ROUTES_END */}`
      );
    }
    writeFileSync(appFile, appContent, 'utf8');
  }

  // Step 6 — tsc --noEmit
  log('⚙ Validating TypeScript…');
  try {
    execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' });
    log('✓ TypeScript clean');
  } catch (e) {
    const err = e.stdout?.toString() || e.stderr?.toString() || String(e);
    fail(`TypeScript errors:\n${err}`);
  }

  // Step 7 — Write state.json
  const stateDir = join(P, '.dashboard');
  mkdirSync(stateDir, { recursive: true });
  const statePath = join(stateDir, 'state.json');
  const existingState = existsSync(statePath)
    ? JSON.parse(readFileSync(statePath, 'utf8'))
    : {};

  // Collect widget names from both modes
  const filesWidgetNames = Object.keys(files)
    .filter(p => p.startsWith('src/dashboard/widgets/') && p.endsWith('.tsx'))
    .map(p => p.replace('src/dashboard/widgets/', '').replace('.tsx', ''));
  const allWidgetNames = [...new Set([...filesWidgetNames, ...generatedWidgetNames])];

  const newState = {
    ...existingState,
    app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
    env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
    org: orgName,
    tenant: tenantName,
    cloudUrl,
    widgets: allWidgetNames,
    deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
  };
  writeAtomic(statePath, JSON.stringify(newState, null, 2));

  // Step 8 — Start dev server
  // Use shell:true so npm resolves correctly on Windows (npm.cmd vs npm)
  log('⚙ Starting preview server…');
  const isWindows = process.platform === 'win32';
  const server = spawn('npm', ['run', 'dev'], {
    cwd: P,
    detached: true,
    stdio: 'pipe',
    shell: isWindows,   // required on Windows — npm is npm.cmd
  });
  server.on('error', () => {});  // suppress unhandled error if server fails to start
  server.unref();

  // Give server 5s to bind, then output result regardless
  // (user runs `npm run dev` themselves if this poll times out)
  let port = 5173;
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    try {
      execSync(
        `node -e "require('http').get('http://localhost:${port}',r=>process.exit(r.statusCode<500?0:1)).on('error',()=>process.exit(1))"`,
        { stdio: 'pipe', timeout: 1000 }
      );
      break;
    } catch {
      port++;
      if (port > 5180) { port = 5173; break; }
    }
  }

  // Output structured result — always exit 0 after this point (server runs independently)
  const result = {
    success: true,
    projectDir: P,
    port,
    previewUrl: `http://localhost:${port}`,
    widgets: allWidgetNames,
    dashboardName,
  };
  log('\nBUILD_RESULT:' + JSON.stringify(result));
  process.exit(0);  // exit before server's detached process can throw
}

} // end entry-point guard

/**
 * PLAN JSON SCHEMA
 * ─────────────────
 * {
 *   "projectDir":    string  — absolute path where dashboard will be created
 *   "dashboardName": string  — human display name (e.g. "Agent Health Dashboard")
 *   "routingName":   string  — URL slug (e.g. "agent-health-x7k2")
 *   "orgName":       string  — from uip login (Data.Organization)
 *   "tenantName":    string  — from uip login (Data.Tenant)
 *   "cloudUrl":      string  — from uip login (Data.BaseUrl)
 *   "apiUrl":        string  — derived ("alpha" → https://alpha.api.uipath.com etc.)
 *   "tenantId":      string  — UUID from ~/.uipath/.auth UIPATH_TENANT_ID
 *   "clientId":      string  — external OAuth app client ID (from uip admin external-apps create)
 *
 *   "widgets": [            — PREFERRED: agent provides config, script generates TypeScript
 *     {
 *       "componentName": string   — PascalCase; used as filename and export name
 *       "template":      string   — one of: line-chart | area-chart | bar-chart | donut-chart |
 *                                           kpi-card | kpi-with-sparkline | data-table |
 *                                           ranked-table | progress-bar-list | multi-line-chart
 *       "detailRoute":   string   — HashRouter path, e.g. "/error-rate"
 *       "icon":          string   — any lucide-react icon name
 *       "title":         string   — human label shown in CardTitle
 *       "description":   string   — one line in CardDescription
 *       "dataHook":      string   — full useInsights<ResponseType>(...) call expression
 *       "dataSelector":  string   — expression extracting array/value from response data
 *       "xKey":          string   — (line/area/bar) X-axis field name
 *       "yKey":          string   — (line/area/bar) Y-axis field name
 *       "valueExpression": string — (kpi-card/kpi-with-sparkline) expression evaluating to string
 *       "columns":       string   — (data-table/ranked-table) ColumnDef array literal
 *       "deltaDir":      string   — up-good | up-bad | down-good | down-bad | neutral
 *       "deltaText":     string   — text shown in DeltaBadge
 *       "series":        string   — (multi-line-chart) series array literal
 *       "pivotExpression": string — (multi-line-chart) expression pivoting flat array to series map
 *       "sdkImport":     string   — (sdk-* templates) npm subpath, e.g. "@uipath/uipath-typescript/jobs"
 *       "sdkService":    string   — (sdk-* templates) class name, e.g. "Jobs"
 *       "sdkCall":       string   — (sdk-* templates) method call expression, e.g. "getAll({ state: 'Running' })"
 *       "sdkResultType": string   — (sdk-* templates) TypeScript type literal, e.g. "{ items?: Array<{ state: string }> }"
 *     }
 *   ],
 *
 *   "files": {              — agent-authored files (Dashboard.tsx, index.ts, App.tsx)
 *     "src/dashboard/Dashboard.tsx": "...",
 *     "src/dashboard/widgets/index.ts": "..."
 *   },
 *   "appTsxImports": string  — lines to inject between GENERATED_IMPORTS markers
 *   "appTsxRoutes":  string  — JSX to inject between GENERATED_ROUTES markers
 * }
 */
