// Use-case flow: incremental EDIT — apply ADD / REMOVE / CHANGE / REBUILD / EJECT /
// UPGRADE ops to an existing project in one validated pass. Delegates project-wide
// UPGRADE to ./upgrade.mjs. Extracted from build-dashboard.mjs.

import { execSync } from 'child_process'
import { join, resolve, dirname, basename } from 'path'
import { existsSync, readFileSync, mkdirSync, copyFileSync, unlinkSync } from 'fs'
import { scaffoldDrift, readScaffoldVersion, buildVersions, checkSdkVersion } from '../lifecycle.mjs'
import { runUpgrade } from './upgrade.mjs'
import {
  log, fail, emit, writeAtomic, setWidgetsDir, assertScaffoldExtracted,
  classifyEditIntent, resolveChangeMetric, resolveMetric, buildWidgetFile, buildViewSpec,
  generateViewFile, generateDashboardFiles, injectAppRoutes, collectKeyedViews,
  writeKeyedViewIfRowLink, rebuildAllWidgets, runMetricsTypecheck,
  widgetGetsDetailView, toPascalCase, hashContent, STATE_SCHEMA_VERSION,
} from '../build-dashboard.mjs'

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
export async function runIncrementalEdit(editIntent, intentPath) {
  const { projectDir } = editIntent
  if (!projectDir) fail('edit-intent.projectDir is required')
  const P = resolve(projectDir)
  const intentDir = dirname(intentPath)
  const statePath = join(P, '.dashboard', 'state.json')
  if (!existsSync(statePath)) fail('No .dashboard/state.json found. Run a fresh build first.')
  const state = JSON.parse(readFileSync(statePath, 'utf8'))
  const { ops } = classifyEditIntent(editIntent)

  // Eject — flip to the ejected regime (one-way). No scaffold needed: this only
  // rewrites state.json. From here the dashboard is a full-source project edited
  // free-form by the agent + `npm run build`; the edit-script no longer runs on it.
  // Idempotent — re-ejecting an ejected project is a no-op write.
  if (ops.length === 1 && ops[0].op === 'EJECT') {
    state.regime = 'ejected'
    state.schemaVersion = STATE_SCHEMA_VERSION
    writeAtomic(statePath, JSON.stringify(state, null, 2))
    emit('EJECTED', {
      projectDir: P,
      note: 'Dashboard ejected → full-source, agent-edited regime. Compiler regen / UPGRADE no longer apply. Edit files under src/ directly, then run `npm run build`.',
    })
    return
  }

  // Regime gate — the structured edit-script is for compiler-managed dashboards
  // only. An ejected project (or a template) is edited free-form on its source;
  // running the script would regenerate Dashboard.tsx/widgets and clobber hand
  // work. Refuse loud (before touching the scaffold) and route to source editing.
  if (state.regime === 'ejected') {
    emit('EJECTED_PROJECT', { projectDir: P })
    fail(
      'This dashboard is ejected (full-source, agent-edited). The structured edit-script ' +
      'is disabled for ejected projects — edit the source under src/ directly per the ' +
      'request, then run `npm run build`. See references/dashboards/primitives/customization.md (Ejected regime).'
    )
  }

  // The starter kit must still be extracted in the project (the widget generator
  // templates live in <proj>/_gen/widgets). Verify + point the generator at them —
  // without this, ADD/CHANGE/REBUILD crash at widgetsDir().
  assertScaffoldExtracted(P)
  setWidgetsDir(join(P, '_gen', 'widgets'))
  const editDrift = scaffoldDrift(state, readScaffoldVersion(P))
  if (editDrift) emit('UPGRADE_AVAILABLE', editDrift)
  if (state.buildStatus === 'in-progress') {
    log('⚠ Warning: Previous build did not complete — widgets may be missing. Consider running a full build first.')
  }
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
      let addEntry = null
      try { addEntry = resolveMetric(o.metric).entry } catch (e) { violations.push(`ops[${i}] ADD "${o.metric.name}": ${e.message}`) }
      const rel = o.metric.module ?? `metrics/${o.metric.name}.ts`
      const addFrom = join(intentDir, rel)
      if (!existsSync(addFrom)) {
        violations.push(`ops[${i}] ADD "${o.metric.name}": metric module not found — write ${rel} exporting "fetchData"`)
      } else if (
        widgetGetsDetailView(o.metric.displayAs ?? addEntry?.template ?? 'data-table', o.metric, addEntry) &&
        !/export\s+const\s+fetchDetail\b/.test(readFileSync(addFrom, 'utf8'))
      ) {
        violations.push(
          `ops[${i}] ADD "${o.metric.name}": drill-down widget needs a record-grain "fetchDetail" export in ${rel}` +
          `${addEntry?.detailRecipe ? ` — ${addEntry.detailRecipe}` : ''} (or set "noDetail": true on the metric/registry entry for a chart with no record data)`,
        )
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
    // Charts (unless noDetail) and kpi-cards with detail:true get a record-grain
    // detail view so the drill-down route resolves.
    if (widgetGetsDetailView(addTemplate, metric, entry)) {
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
    // Keep the detail view in sync: regenerate when the widget drills down
    // (chart unless noDetail, or kpi-card with detail:true), drop it otherwise.
    const changeViewPath = join(P, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (widgetGetsDetailView(changeTemplate, metricRef, entry)) {
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
  state.versions = buildVersions(checkSdkVersion(P).version, readScaffoldVersion(P))
  writeAtomic(statePath, JSON.stringify(state, null, 2))
  emit('INCREMENTAL_READY', { count: applied.length, ops: applied })
}
