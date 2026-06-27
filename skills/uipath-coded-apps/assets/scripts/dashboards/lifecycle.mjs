// Project-lifecycle utilities for the dashboard build pipeline — versioning,
// dependency pre-warm, SDK-version check, and dev-server teardown. Extracted from
// build-dashboard.mjs to keep that file focused on generation + orchestration.
//
// These functions depend only on small primitives (emit/log/writeAtomic) and a few
// constants from build-dashboard.mjs; they never call the widget/view generators, so
// there is no tight coupling. (The import from build-dashboard.mjs forms a benign
// runtime cycle — every cross-reference is used inside a function body, never at
// module-evaluation time, so the live bindings are resolved by call time.)

import { readFileSync, existsSync, unlinkSync } from 'fs'
import { join } from 'path'
import { pathToFileURL } from 'url'
import { execSync } from 'child_process'
import { createConnection } from 'net'
import { emit, log, writeAtomic, SKILL_VERSION, INTENT_SCHEMA_VERSION, MIN_SDK_VERSION, DASHBOARD_PORT } from './build-dashboard.mjs'

/**
 * Read the scaffold version from the EXTRACTED starter kit — `_gen/starter-kit.json`
 * inside the project. The version ships INSIDE the archive (single fixture artifact);
 * there is no separate `.version` file. Returns '0.0.0' if the marker is absent.
 * @param {string} projectDir
 */
export function readScaffoldVersion(projectDir) {
  try {
    return JSON.parse(readFileSync(join(projectDir, '_gen', 'starter-kit.json'), 'utf8')).version || '0.0.0'
  } catch { return '0.0.0' }
}

/**
 * The version block stamped into state.json so a dashboard knows what it was
 * built against (drives offer-on-detect upgrade + future migrations).
 * @param {string|null} [sdkVersion]
 * @param {string} [scaffoldVersion] - the extracted scaffold's version (readScaffoldVersion(projectDir))
 */
export function buildVersions(sdkVersion = null, scaffoldVersion = '0.0.0') {
  return { skill: SKILL_VERSION, scaffold: scaffoldVersion, intentSchema: INTENT_SCHEMA_VERSION, sdk: sdkVersion }
}

/**
 * Compare a project's stamped scaffold version to the shipped one. Returns
 * { from, to } when they differ (including a pre-versioning project with no
 * versions block), or null when current. Forward-only — any mismatch means
 * "a newer scaffold is available".
 * @param {object} state - parsed .dashboard/state.json
 * @param {string} scaffoldVersion - current shipped scaffold version (from the extracted kit)
 */
export function scaffoldDrift(state, scaffoldVersion) {
  const stamped = state?.versions?.scaffold ?? null
  return stamped === scaffoldVersion ? null : { from: stamped, to: scaffoldVersion }
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

/**
 * Install dependencies in a project (npm ci). Emits PREWARM_START/DONE/FAILED.
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
 * Kill a previously-started dev server using the PID stored in a file.
 * Cross-platform: taskkill /T on Windows (kills process tree), SIGTERM on Unix.
 * Waits up to 1500ms for the port to become free after killing.
 * @param {string} pidFile - Absolute path to the .pid file
 * @returns {Promise<void>}
 */
export async function killPreviousDevServer(pidFile) {
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
