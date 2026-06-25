// Use-case flow: fresh BUILD — the main intent.json pipeline. Scaffolds, writes
// config + state, pre-warms deps, copies + type-checks metric modules, generates
// every widget/view, injects routes, runs the full-app tsc backstop, and finalizes
// state.json. Extracted from build-dashboard.mjs.

import { execSync } from 'child_process'
import { join, resolve, dirname, basename } from 'path'
import { existsSync, readFileSync, mkdirSync, copyFileSync, unlinkSync } from 'fs'
import {
  scaffoldDrift, readScaffoldVersion, buildVersions, checkSdkVersion,
  runPrewarm, waitForPrewarm, killPreviousDevServer,
} from '../lifecycle.mjs'
import {
  log, fail, emit, writeAtomic, setWidgetsDir, assertScaffoldExtracted,
  resolveMetric, buildWidgetFile, buildViewSpec, generateViewFile, generateKeyedDetailViewFile,
  generateDashboardFiles, injectAppRoutes, runMetricsTypecheck,
  widgetGetsDetailView, widgetLayoutGroup, autoSubtitle, metricModuleSpecifier, compileColumns,
  toPascalCase, hashContent,
  DASHBOARD_PORT, DASHBOARD_SCOPES, MIN_SDK_VERSION, STATE_SCHEMA_VERSION,
} from '../build-dashboard.mjs'

/**
 * Main intent.json build pipeline.
 * @param {DashboardIntent} intent
 * @param {string} intentPath - Absolute path to intent.json on disk (for re-reads)
 * @returns {Promise<void>}
 */
export async function runDashboardBuild(intent, intentPath) {
  const {
    dashboardName, timeRange, metrics,
    projectDir, orgName, tenantName, cloudUrl, apiUrl, clientId = '', dashboardDescription = '',
    routingName, template = false,
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
    // Step 1 — Scaffold (the agent extracts the starter-kit archive into the project
    // before building; the skill ships no zip code). Verify it's present, then
    // point widget generation at the kit's _gen/widgets templates.
    assertScaffoldExtracted(P)
    setWidgetsDir(join(P, '_gen', 'widgets'))
    emit('SCAFFOLD_READY')

    // Step 2 — Config (uipath.json)
    // All SPA config lives in uipath.json. The `uipathCodedApps()` Vite plugin reads
    // it and injects <meta name="uipath:*"> tags into index.html (dev serve AND
    // production build); the SDK (new UiPath()) reads its config from those tags. No
    // VITE_* / .env files. A TEMPLATE build writes a TENANT-NEUTRAL uipath.json
    // (scope + redirectUri only — no org/tenant/baseUrl/clientId), so the shared
    // bundle bakes no tenant identity and the Apps host injects it at runtime. A
    // normal dashboard writes the full tenant config (baked into its own deploy).
    const uipathJsonPath = join(P, 'uipath.json')
    const baseConfig = existsSync(uipathJsonPath)
      ? JSON.parse(readFileSync(uipathJsonPath, 'utf8'))
      : {}
    const uipathConfig = template
      ? { name: dashboardName, scope: DASHBOARD_SCOPES, redirectUri: `http://localhost:${DASHBOARD_PORT}` }
      : {
          name: dashboardName,
          scope: DASHBOARD_SCOPES,
          clientId,
          orgName,
          tenantName,
          baseUrl: apiUrl,
          redirectUri: `http://localhost:${DASHBOARD_PORT}`,
        }
    writeAtomic(uipathJsonPath, JSON.stringify({ ...baseConfig, ...uipathConfig }, null, 2) + '\n')
    emit('ENV_WRITTEN')

    // Warn if clientId is missing — local-dev / standalone OAuth will fail without it
    // (a hosted/embedded deploy gets its client-id from the host instead).
    if (!template && !clientId) {
      emit('AUTH_MISSING', { var: 'clientId', message: 'No external OAuth app client ID in uipath.json. Local preview / standalone OAuth will fail. Run Phase 4.5 to provision one.' })
      log('⚠ Warning: clientId is empty — local dashboard auth will not work. See Phase 4.5 in build plugin docs.')
    }

    // Write partial state.json early so deploy can find app metadata even if build fails
    const stateDir = join(P, '.dashboard')
    mkdirSync(stateDir, { recursive: true })
    const statePath = join(stateDir, 'state.json')
    const existingState = existsSync(statePath) ? JSON.parse(readFileSync(statePath, 'utf8')) : {}
    const buildDrift = existsSync(statePath) ? scaffoldDrift(existingState, readScaffoldVersion(P)) : null
    if (buildDrift) emit('UPGRADE_AVAILABLE', buildDrift)
    // Regime: a template builds straight to the ejected regime (full-source,
    // agent-edited, no compiler regen); a fresh dashboard is compiler-managed.
    // Once ejected, always ejected (one-way — never silently re-adopt the script).
    const regime = template ? 'ejected' : (existingState.regime ?? 'compiler-managed')
    if (template) {
      emit('TEMPLATE_BUILD', {
        regime,
        note: 'Template build → ejected regime + tenant-neutral bundle (no org/tenant/baseUrl/clientId baked). The scaffold useAuth resolves host-injected <meta name="uipath:*"> config at runtime (new UiPath()), so the artifact is portable across tenants. Pack source with: node build-dashboard.mjs --pack-template <projectDir>',
      })
    }
    const partialState = {
      schemaVersion: STATE_SCHEMA_VERSION,
      versions: buildVersions(null, readScaffoldVersion(P)),
      regime,
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

    // Step 3.6 — Enforce record-grain detail. Every widget that exposes a
    // drill-down (a chart not opted out via registry `noDetail`, or a kpi-card
    // with `detail: true`) MUST export `fetchDetail` — the record-grain query
    // behind the aggregate. Without it the detail view would re-table the chart's
    // own buckets and add no information. This is the chart analogue of the
    // existing T3-table-without-columns hard-fail.
    const missingDetail = []
    for (const metric of metrics) {
      const isT3 = metric.tier === 'T3'
      const { entry } = isT3 ? { entry: null } : resolveMetric(metric)
      const displayAs = metric.displayAs ?? entry?.template ?? 'data-table'
      if (!widgetGetsDetailView(displayAs, metric, entry)) continue
      const rel = metric.module ?? `metrics/${metric.name}.ts`
      const moduleSrc = readFileSync(join(metricsDestDir, basename(rel)), 'utf8')
      if (!/export\s+const\s+fetchDetail\b/.test(moduleSrc)) {
        missingDetail.push({ metric: metric.name, module: rel, recipe: entry?.detailRecipe })
      }
    }
    if (missingDetail.length > 0) {
      emit('CHART_DETAIL_MISSING', { metrics: missingDetail, intentPath })
      log(
        `⚠ These widgets expose a drill-down but their modules don't export "fetchDetail" ` +
        `(the record-grain query behind the chart). Add it to each module (see the metric's ` +
        `detailRecipe), or — for a chart that genuinely has no record data — set "noDetail": true ` +
        `(on the registry entry for a catalog metric, or on the metric in intent.json for a T3 custom chart):\n` +
        missingDetail.map(m => `  • ${m.metric} (${m.module})${m.recipe ? `\n      ${m.recipe}` : ''}`).join('\n'),
      )
      process.exit(2)
    }

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

      // Detail views: charts (unless registry `noDetail`) and kpi-cards with
      // `detail: true` get a generated record-grain view + route — any tier. The
      // view runs `fetchDetail`; columns come from detailColumns (intent or
      // registry defaults), else auto-detected at runtime.
      if (widgetGetsDetailView(displayAs, metric, entry)) {
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
      versions: buildVersions(sdkCheck.version, readScaffoldVersion(P)),
      regime,
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
