import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync, mkdirSync, existsSync, readFileSync } from 'node:fs'
import { join, delimiter } from 'node:path'
import { tmpdir } from 'node:os'
import { spawn } from 'node:child_process'
import {
  readScaffoldVersion, buildVersions, scaffoldDrift, runIntentMigrations,
  checkSdkVersion, runPrewarm, waitForPrewarm, killPreviousDevServer,
} from '../../skills/uipath-coded-apps/assets/scripts/dashboards/lifecycle.mjs'
import { MIN_SDK_VERSION, SKILL_VERSION, INTENT_SCHEMA_VERSION } from '../../skills/uipath-coded-apps/assets/scripts/dashboards/build-dashboard.mjs'
import { installFakeTools, readFakeLog, pathKey } from './support/coded-apps-dashboards-fake-tools.mjs'

const tmp = prefix => mkdtempSync(join(tmpdir(), prefix))

/** Run fn with process.stdout/stderr captured; returns the captured text. */
async function capture(fn) {
  const out = []
  const realOut = process.stdout.write.bind(process.stdout)
  process.stdout.write = chunk => { out.push(String(chunk)); return true }
  try { await fn() } finally { process.stdout.write = realOut }
  return out.join('')
}

/** Run fn with the fake npm first on PATH and the given env overrides. */
async function withFakeNpm(extraEnv, fn) {
  const dir = installFakeTools()
  const log = join(dir, 'calls.log')
  const saved = { path: process.env[pathKey], fail: process.env.FAKE_NPM_FAIL, log: process.env.FAKE_LOG }
  process.env[pathKey] = dir + delimiter + saved.path
  process.env.FAKE_LOG = log
  if (extraEnv.FAKE_NPM_FAIL !== undefined) process.env.FAKE_NPM_FAIL = extraEnv.FAKE_NPM_FAIL
  try {
    const stdout = await capture(() => fn(log))
    return { stdout, calls: readFakeLog(log) }
  } finally {
    process.env[pathKey] = saved.path
    for (const [k, v] of [['FAKE_NPM_FAIL', saved.fail], ['FAKE_LOG', saved.log]]) {
      if (v === undefined) delete process.env[k]; else process.env[k] = v
    }
  }
}

// ── versions ────────────────────────────────────────────────────────────────

test('buildVersions stamps skill, scaffold, intent schema and sdk', () => {
  assert.deepEqual(buildVersions('1.6.0', '2.1.0'), {
    skill: SKILL_VERSION, scaffold: '2.1.0', intentSchema: INTENT_SCHEMA_VERSION, sdk: '1.6.0',
  })
  assert.deepEqual(buildVersions(), {
    skill: SKILL_VERSION, scaffold: '0.0.0', intentSchema: INTENT_SCHEMA_VERSION, sdk: null,
  })
})

test('readScaffoldVersion falls back to 0.0.0 for unparseable or versionless markers', () => {
  const dir = tmp('lc-scaf-')
  mkdirSync(join(dir, '_gen'))
  writeFileSync(join(dir, '_gen', 'starter-kit.json'), '{ nope')
  assert.equal(readScaffoldVersion(dir), '0.0.0')
  writeFileSync(join(dir, '_gen', 'starter-kit.json'), '{"name":"kit"}')
  assert.equal(readScaffoldVersion(dir), '0.0.0')
})

test('scaffoldDrift tolerates a missing state and reports it as drift from null', () => {
  assert.deepEqual(scaffoldDrift(undefined, '2.0.0'), { from: null, to: '2.0.0' })
  assert.equal(scaffoldDrift({ versions: { scaffold: '2.0.0' } }, '2.0.0'), null)
})

// ── intent migrations ───────────────────────────────────────────────────────

test('runIntentMigrations applies each migration file in sequence and stamps the target version', async () => {
  const dir = tmp('lc-mig-')
  writeFileSync(join(dir, 'intent-v1-to-v2.mjs'), 'export const migrate = i => ({ ...i, steps: [...(i.steps ?? []), "1to2"] })\n')
  writeFileSync(join(dir, 'intent-v2-to-v3.mjs'), 'export const migrate = i => ({ ...i, steps: [...(i.steps ?? []), "2to3"] })\n')
  const out = await runIntentMigrations({ schemaVersion: 1, metrics: [] }, dir, 3)
  assert.deepEqual(out.steps, ['1to2', '2to3'])
  assert.equal(out.schemaVersion, 3)
})

test('runIntentMigrations treats a missing schemaVersion as 1 and stops at the first gap in the chain', async () => {
  const dir = tmp('lc-mig-gap-')
  writeFileSync(join(dir, 'intent-v1-to-v2.mjs'), 'export const migrate = i => ({ ...i, migrated: true })\n')
  const out = await runIntentMigrations({ metrics: [] }, dir, 4)
  assert.equal(out.migrated, true)
  assert.equal(out.schemaVersion, 2) // v2-to-v3 does not exist → stop, keep what was reached
})

test('runIntentMigrations never lowers a schemaVersion that is already ahead of the target', async () => {
  const out = await runIntentMigrations({ schemaVersion: 5 }, '/no/such/dir', 2)
  assert.equal(out.schemaVersion, 5)
})

// ── SDK version floor ───────────────────────────────────────────────────────

function projectWithSdk(version) {
  const p = tmp('lc-sdk-')
  const dir = join(p, 'node_modules', '@uipath', 'uipath-typescript')
  mkdirSync(dir, { recursive: true })
  if (version !== null) writeFileSync(join(dir, 'package.json'), typeof version === 'string' ? JSON.stringify({ version }) : '{ broken')
  return p
}

test('checkSdkVersion: not installed', () => {
  assert.deepEqual(checkSdkVersion(tmp('lc-nosdk-')), { ok: false, version: null })
})

test('checkSdkVersion: unreadable package.json counts as not installed', () => {
  assert.deepEqual(checkSdkVersion(projectWithSdk({})), { ok: false, version: null })
})

test('checkSdkVersion compares major, minor and patch against MIN_SDK_VERSION', () => {
  const [maj, min, pat] = MIN_SDK_VERSION.split('.').map(Number)
  const cases = [
    [`${maj}.${min}.${pat}`, true],
    [`${maj}.${min}.${pat + 1}`, true],
    [`${maj}.${min + 1}.0`, true],
    [`${maj + 1}.0.0`, true],
    [`${maj}.${min}.${pat - 1}`, false],
    [`${maj}.${min - 1}.99`, false],
    [`${maj - 1}.99.99`, false],
  ]
  for (const [version, ok] of cases) {
    assert.deepEqual(checkSdkVersion(projectWithSdk(version)), { ok, version }, version)
  }
})

// ── runPrewarm (fake npm) ───────────────────────────────────────────────────

test('runPrewarm: first attempt succeeds, announces start/done and leaves no lock file', async () => {
  const project = tmp('lc-pw-')
  const { stdout, calls } = await withFakeNpm({}, () => runPrewarm(project))
  assert.deepEqual(calls, ['npm ci --prefer-offline'])
  assert.match(stdout, /^PREWARM_START\nPREWARM_DONE\n$/)
  assert.ok(!existsSync(join(project, '.prewarm.lock')))
  assert.ok(existsSync(join(project, 'node_modules', '.package-lock.json')))
})

test('runPrewarm escalates ci --prefer-offline → ci → install and warns about lockfile drift', async () => {
  const project = tmp('lc-pw-esc-')
  const { stdout, calls } = await withFakeNpm({ FAKE_NPM_FAIL: 'ci-offline,ci' }, () => runPrewarm(project))
  assert.deepEqual(calls, ['npm ci --prefer-offline', 'npm ci', 'npm install'])
  assert.match(stdout, /npm ci rejected the lockfile/)
  assert.match(stdout, /PREWARM_DONE\n$/)
})

test('runPrewarm: when every install attempt fails it emits PREWARM_FAILED, removes the lock and throws', async () => {
  const project = tmp('lc-pw-fail-')
  let thrown
  const { stdout, calls } = await withFakeNpm({ FAKE_NPM_FAIL: 'ci-offline,ci,install' }, async () => {
    try { await runPrewarm(project) } catch (e) { thrown = e }
  })
  assert.equal(calls.length, 3)
  assert.match(thrown.message, /^dependency install failed: .*npm ERR! install failed/s)
  assert.match(stdout, /PREWARM_FAILED:\{"exitCode":1,"stderr":"[^"]*npm ERR! install failed/)
  assert.ok(!stdout.includes('PREWARM_DONE'))
  assert.ok(!existsSync(join(project, '.prewarm.lock')))
})

// ── waitForPrewarm ──────────────────────────────────────────────────────────

test('waitForPrewarm returns immediately once node_modules/.package-lock.json exists', async () => {
  const project = tmp('lc-wait-')
  mkdirSync(join(project, 'node_modules'))
  writeFileSync(join(project, 'node_modules', '.package-lock.json'), '{}')
  const stdout = await capture(() => waitForPrewarm(project, 1000))
  assert.equal(stdout, 'PREWARM_DONE\n')
})

test('waitForPrewarm times out with PREWARM_FAILED and a descriptive error', async () => {
  const project = tmp('lc-wait-to-')
  let thrown
  const stdout = await capture(() => {
    try { waitForPrewarm(project, 1) } catch (e) { thrown = e }
  })
  assert.match(thrown.message, /^Pre-warm timed out after 0s$/)
  assert.match(stdout, /PREWARM_FAILED:\{"exitCode":-1,"stderr":"Timed out after 0s"\}/)
})

test('waitForPrewarm logs progress every 20 seconds while it waits', async () => {
  const project = tmp('lc-wait-log-')
  const realNow = Date.now
  let clock = realNow.call(Date)
  Date.now = () => (clock += 9000) // each poll "takes" 9s of wall time
  let thrown
  let stdout
  try {
    stdout = await capture(() => {
      try { waitForPrewarm(project, 60_000) } catch (e) { thrown = e }
    })
  } finally { Date.now = realNow }
  assert.match(thrown.message, /timed out after 60s/)
  assert.match(stdout, /⏳ Installing dependencies… \(\d+s\)/)
})

// ── killPreviousDevServer ───────────────────────────────────────────────────

test('killPreviousDevServer is a no-op without a pid file', async () => {
  await killPreviousDevServer(join(tmp('lc-kill-none-'), 'server.pid'))
})

test('killPreviousDevServer leaves an unparseable pid file alone', async () => {
  const pidFile = join(tmp('lc-kill-bad-'), 'server.pid')
  writeFileSync(pidFile, 'not-a-pid')
  await killPreviousDevServer(pidFile)
  assert.equal(readFileSync(pidFile, 'utf8'), 'not-a-pid')
})

test('killPreviousDevServer terminates the recorded process and deletes the pid file', async () => {
  const child = spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], { stdio: 'ignore' })
  const exited = new Promise(resolve => child.once('exit', (code, signal) => resolve({ code, signal })))
  const pidFile = join(tmp('lc-kill-live-'), 'server.pid')
  writeFileSync(pidFile, `${child.pid}\n`)
  await killPreviousDevServer(pidFile)
  const result = await Promise.race([exited, new Promise(r => setTimeout(() => r('still running'), 5000))])
  if (result === 'still running') child.kill('SIGKILL')
  assert.notEqual(result, 'still running')
  assert.ok(!existsSync(pidFile))
})

test('killPreviousDevServer tolerates a pid whose process is already gone', async () => {
  const pidFile = join(tmp('lc-kill-dead-'), 'server.pid')
  writeFileSync(pidFile, '2147483646')
  await killPreviousDevServer(pidFile)
  assert.ok(!existsSync(pidFile))
})
