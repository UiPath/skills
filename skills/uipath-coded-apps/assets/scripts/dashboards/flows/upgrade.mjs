// Use-case flow: project-wide UPGRADE — refresh the disposable scaffold framework
// over a project, migrate intent, regenerate every widget from durable state, and
// re-validate. Extracted from build-dashboard.mjs; shared primitives are imported
// back from it (benign cycle — used only at call time).

import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { existsSync, readFileSync } from 'fs'
import { runIntentMigrations, runPrewarm, buildVersions, checkSdkVersion, readScaffoldVersion } from '../lifecycle.mjs'
import {
  log, fail, emit, writeAtomic, setWidgetsDir, assertScaffoldExtracted,
  rebuildAllWidgets, generateDashboardFiles, injectAppRoutes, collectKeyedViews,
  runMetricsTypecheck, STATE_SCHEMA_VERSION,
} from '../build-dashboard.mjs'

/**
 * Upgrade an existing dashboard to the current scaffold: refresh the disposable
 * framework, migrate intent.json, regenerate widgets/views from durable intent +
 * on-disk metric modules, re-validate, and re-stamp versions. The durable set
 * (intent.json, src/metrics, .dashboard, and uipath.json — the SDK config) is
 * preserved. The framework refresh extracts the starter-kit archive with the OS tar (see CAPABILITY.md).
 * @param {string} P  resolved project dir
 * @param {object} state  parsed state.json
 * @param {string} intentPath  edit-intent path (for the migrations dir + retry signal)
 */
export async function runUpgrade(P, state, intentPath) {
  // Best-effort dirty-tree warning — upgrade regenerates disposable files.
  try {
    const dirty = execSync(`git -C "${P}" status --porcelain`, { stdio: 'pipe' }).toString().trim()
    if (dirty) log('⚠ Project has uncommitted changes — upgrade regenerates disposable files (your intent.json + src/metrics are preserved).')
  } catch { /* not a git repo — nothing to check */ }

  // 1. Refresh the disposable scaffold framework: the agent re-extracts the
  //    latest starter-kit archive over the project before --upgrade (preserving
  //    src/metrics, intent.json, and uipath.json — the SDK config the plugin
  //    injects). Verify the fresh kit is present and point at its templates.
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
  state.versions = buildVersions(checkSdkVersion(P).version, readScaffoldVersion(P))
  writeAtomic(join(P, '.dashboard', 'state.json'), JSON.stringify(state, null, 2))
  emit('UPGRADE_DONE', { to: readScaffoldVersion(P), widgets: Object.keys(state.widgets ?? {}) })
}
