# Dashboard Phase 2 — Versioning + Offer-on-Detect Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stamp every generated dashboard with the versions it was built against, detect when the shipped scaffold is newer than a dashboard's, and provide an `UPGRADE` operation that regenerates the disposable app from the durable intent + metric modules against the current scaffold — preserving the user's metrics.

**Architecture:** Add version constants + a `versions` block to `state.json` (`{ skill, scaffold, intentSchema, sdk }`, `schemaVersion` → 2). On any operation against an existing project, compare the stamped `scaffold` version to the shipped `SCAFFOLD_VERSION`; on drift emit `UPGRADE_AVAILABLE` (the skill offers it). A new `UPGRADE` edit-intent op refreshes the scaffold framework (`copyDir` for now — Phase 3 swaps in zip-extraction), runs intent-schema migrations (empty registry — framework only), REBUILDs every widget/view from `state.intentMetric` + the on-disk `src/metrics/*.ts`, re-runs Stage A + full tsc, and re-stamps the versions.

**Tech Stack:** Node ESM build script (`build-dashboard.mjs`), `node:test`, TypeScript (`tsc`), the existing Phase 1 metric-module pipeline.

**Spec:** `docs/superpowers/specs/2026-06-15-dashboard-compiler-architecture-design.md` §4. Phase 3 (zip fixture) is a separate later plan; this phase uses a `SCAFFOLD_VERSION` constant + `copyDir(SCAFFOLD_DIR)` as the interim fixture source.

**Branch:** `feat/dashboard-compiler-arch`.

---

## Interim decisions (Phase 3 supersedes)
- `SCAFFOLD_VERSION` is a constant in `build-dashboard.mjs`. Phase 3 sources it from `scaffold.manifest.json`.
- Upgrade "swaps the fixture" via `copyDir(SCAFFOLD_DIR, projectDir)` (the loose scaffold). Phase 3 swaps this for zip-extraction.
- Migration registry ships **empty** — `intentSchema` is `2` and there is no `v3` yet. The runner exists so a future schema bump is a drop-in `migrations/intent-v2-to-v3.mjs`, not a refactor.
- Drift = stamped scaffold version ≠ current (covers Phase-1 projects with no `versions` block). We only ship forward, so "different" ⇒ "offer upgrade".

---

## File Structure

**Modified:** `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` — version constants + `buildVersions`/`scaffoldDrift`/`runIntentMigrations` helpers; stamp `versions` in both build state-writes + the incremental state-write; emit `UPGRADE_AVAILABLE` on drift; `UPGRADE` op + `runUpgrade`.
**New:** `skills/uipath-coded-apps/assets/scripts/migrations/README.md` — documents the (empty) registry + the `intent-v<N>-to-v<N+1>.mjs` contract.
**Modified tests:** `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`.
**Modified docs:** `references/dashboards/primitives/state-file.md`, `references/dashboards/primitives/incremental-editor.md`, `references/dashboards/plugins/build/impl.md`.

`KNOWN_EVENTS` gains `UPGRADE_AVAILABLE`, `UPGRADE_DONE`. `VALID_EDIT_OPS` gains `UPGRADE`.

---

## Task 1: Version constants + `buildVersions` + stamp `state.json`

**Files:**
- Modify: `build-dashboard.mjs` (constants near `MIN_SDK_VERSION`; `buildVersions`; both build state-writes; incremental state-write; `KNOWN_EVENTS`; `state.schemaVersion`)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Write the failing test**

```js
import { buildVersions, SCAFFOLD_VERSION, INTENT_SCHEMA_VERSION, STATE_SCHEMA_VERSION } from '../build-dashboard.mjs'

test('buildVersions stamps skill/scaffold/intentSchema/sdk', () => {
  const v = buildVersions('1.4.0')
  assert.equal(v.scaffold, SCAFFOLD_VERSION)
  assert.equal(v.intentSchema, INTENT_SCHEMA_VERSION)
  assert.equal(v.sdk, '1.4.0')
  assert.ok(typeof v.skill === 'string' && v.skill.length > 0)
})

test('buildVersions tolerates a missing sdk version', () => {
  assert.equal(buildVersions().sdk, null)
})

test('STATE_SCHEMA_VERSION is 2', () => {
  assert.equal(STATE_SCHEMA_VERSION, 2)
})
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: FAIL — exports not defined.

- [ ] **Step 3: Add constants + helper**

Near `export const MIN_SDK_VERSION = '1.4.0'` add:
```js
export const SKILL_VERSION = '2.0.0'        // compiler-architecture era; bump per skill release
export const SCAFFOLD_VERSION = '1.0.0'     // Phase 3 will source this from scaffold.manifest.json
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
```

- [ ] **Step 4: Stamp the build state-writes**

In `runDashboardBuild`, the **partial** state object (`schemaVersion: 1`, `buildStatus: 'in-progress'`): change `schemaVersion: 1` → `schemaVersion: STATE_SCHEMA_VERSION` and add `versions: buildVersions(null),` (SDK not checked yet at partial-write time).
The **final** state object (`schemaVersion: 1`, `buildStatus: 'complete'`, written after the SDK check): change `schemaVersion: 1` → `schemaVersion: STATE_SCHEMA_VERSION` and add `versions: buildVersions(sdkCheck.version),` (the `sdkCheck` from Step 3.5 is in scope).

- [ ] **Step 5: Stamp the incremental state-write**

In `runIncrementalEdit`, just before the final `writeAtomic(statePath, JSON.stringify(state, null, 2))`, add:
```js
  state.schemaVersion = STATE_SCHEMA_VERSION
  state.versions = buildVersions(checkSdkVersion(P).version)
```

- [ ] **Step 6: KNOWN_EVENTS**

Add `'UPGRADE_AVAILABLE'` and `'UPGRADE_DONE'` to the `KNOWN_EVENTS` set (used in Tasks 2 & 4).

- [ ] **Step 7: Run tests + parse check**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/` (new tests pass; suite green) and `node --check skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs`.

- [ ] **Step 8: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): stamp state.json with build versions (skill/scaffold/intentSchema/sdk)"
```

---

## Task 2: Scaffold-drift detection + `UPGRADE_AVAILABLE`

**Files:**
- Modify: `build-dashboard.mjs` (`scaffoldDrift` helper; emit in `runDashboardBuild` + `runIncrementalEdit` when an existing state is read)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Write the failing test**

```js
import { scaffoldDrift } from '../build-dashboard.mjs'

test('scaffoldDrift: none when stamped scaffold equals current', () => {
  assert.equal(scaffoldDrift({ versions: { scaffold: SCAFFOLD_VERSION } }), null)
})

test('scaffoldDrift: detected when stamped differs', () => {
  const d = scaffoldDrift({ versions: { scaffold: '0.9.0' } })
  assert.deepEqual(d, { from: '0.9.0', to: SCAFFOLD_VERSION })
})

test('scaffoldDrift: detected for a pre-versioning project (no versions block)', () => {
  const d = scaffoldDrift({ widgets: {} })
  assert.deepEqual(d, { from: null, to: SCAFFOLD_VERSION })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/` → FAIL (`scaffoldDrift` not defined).

- [ ] **Step 3: Add the helper**

```js
/**
 * Compare a project's stamped scaffold version to the shipped one.
 * Returns { from, to } when they differ (including a pre-versioning project
 * with no versions block), or null when current. Forward-only — any mismatch
 * means "a newer scaffold is available".
 * @param {object} state - parsed .dashboard/state.json
 */
export function scaffoldDrift(state) {
  const stamped = state?.versions?.scaffold ?? null
  return stamped === SCAFFOLD_VERSION ? null : { from: stamped, to: SCAFFOLD_VERSION }
}
```

- [ ] **Step 4: Emit on detect (build path)**

In `runDashboardBuild`, right after the existing project's state is read for the partial-state merge (where `existingState` is parsed), add:
```js
    const drift = existsSync(statePath) ? scaffoldDrift(existingState) : null
    if (drift) emit('UPGRADE_AVAILABLE', drift)
```
(Informational — the build proceeds. `existingState` is the var already parsed from `statePath`.)

- [ ] **Step 5: Emit on detect (incremental path)**

In `runIncrementalEdit`, right after `const state = JSON.parse(readFileSync(statePath, 'utf8'))`, add:
```js
  const drift = scaffoldDrift(state)
  if (drift) emit('UPGRADE_AVAILABLE', drift)
```

- [ ] **Step 6: Run tests + parse check**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/` and `node --check ...build-dashboard.mjs`.

- [ ] **Step 7: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): detect scaffold drift and emit UPGRADE_AVAILABLE"
```

---

## Task 3: Intent-migration runner (empty registry) + `UPGRADE` op classification

**Files:**
- Create: `skills/uipath-coded-apps/assets/scripts/migrations/README.md`
- Modify: `build-dashboard.mjs` (`runIntentMigrations`; add `'UPGRADE'` to `VALID_EDIT_OPS`; ensure `classifyEditIntent` accepts a no-target `UPGRADE` op)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Create the registry README**

`migrations/README.md`:
```markdown
# Intent-schema migrations

Empty by design. When `intent.json`'s `schemaVersion` is bumped, add one file here:

`intent-v<N>-to-v<N+1>.mjs` exporting `export function migrate(intent) { /* return upgraded intent */ }`

`runIntentMigrations` (in build-dashboard.mjs) applies them in sequence from the
artifact's `schemaVersion` up to `INTENT_SCHEMA_VERSION`. Pure functions, no I/O.
```

- [ ] **Step 2: Write the failing tests**

```js
import { runIntentMigrations, classifyEditIntent, VALID_EDIT_OPS } from '../build-dashboard.mjs'
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'

test('runIntentMigrations: no-op when already at target', async () => {
  const out = await runIntentMigrations({ schemaVersion: 2, metrics: [] }, '/no/such/dir', 2)
  assert.equal(out.schemaVersion, 2)
})

test('runIntentMigrations: applies a sequenced migration from a dir', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'mig-'))
  writeFileSync(join(dir, 'intent-v2-to-v3.mjs'), 'export function migrate(i){ return { ...i, bumped: true } }')
  try {
    const out = await runIntentMigrations({ schemaVersion: 2, metrics: [] }, dir, 3)
    assert.equal(out.bumped, true)
    assert.equal(out.schemaVersion, 3)
  } finally { rmSync(dir, { recursive: true, force: true }) }
})

test('VALID_EDIT_OPS includes UPGRADE', () => {
  assert.ok(VALID_EDIT_OPS.includes('UPGRADE'))
})

test('classifyEditIntent accepts a no-target UPGRADE op', () => {
  const plan = classifyEditIntent({ projectDir: '/p', op: 'UPGRADE' })
  assert.equal(plan.ops[0].op, 'UPGRADE')
})
```

- [ ] **Step 3: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/` → FAIL.

- [ ] **Step 4: Add `runIntentMigrations` + `UPGRADE` to `VALID_EDIT_OPS`**

Ensure `pathToFileURL` is imported from `node:url` (it already is — used by the entry-point guard). Add:
```js
/**
 * Apply intent-schema migrations in sequence from intent.schemaVersion up to target.
 * Registry is `assets/scripts/migrations/intent-v<N>-to-v<N+1>.mjs` (empty today).
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
```
Change `const VALID_EDIT_OPS = ['ADD', 'REMOVE', 'CHANGE', 'REBUILD']` → add `'UPGRADE'`.

Confirm `classifyEditIntent` normalizes a single `{ op: 'UPGRADE' }` (no `target`/`metric`) into `ops: [{ op: 'UPGRADE' }]` without erroring — it validates `op` against `VALID_EDIT_OPS` (now includes UPGRADE) and does not require target/metric for unknown-shaped ops. If it currently demands a `target` for non-ADD ops, add an `UPGRADE` early-accept (`if (o.op === 'UPGRADE') return { op: 'UPGRADE' }`) in its per-op mapping.

- [ ] **Step 5: Run tests + parse check**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/` (all green) + `node --check ...`.

- [ ] **Step 6: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/migrations/README.md skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): intent-migration runner (empty registry) + UPGRADE op"
```

---

## Task 4: `runUpgrade` — refresh scaffold, migrate, REBUILD, re-stamp

**Files:**
- Modify: `build-dashboard.mjs` (`runUpgrade`; route a lone `UPGRADE` op in `runIncrementalEdit`; extract the existing REBUILD loop into a reusable helper)

- [ ] **Step 1: Extract the REBUILD loop into a helper**

In `runIncrementalEdit`, the `else if (op === 'REBUILD')` branch iterates `state.widgets` and regenerates each widget (+ chart view) from `info.intentMetric`. Extract that loop body into:
```js
/**
 * Regenerate every widget + chart view from each widget's persisted intentMetric
 * (metadata) against the on-disk metric modules. Used by the REBUILD op and by upgrade.
 * @param {string} P  resolved project dir
 * @param {object} state  parsed state.json (mutated: widget hashes refreshed)
 * @param {string} timeRange
 */
export function rebuildAllWidgets(P, state, timeRange) {
  for (const [componentName, info] of Object.entries(state.widgets ?? {})) {
    const m = info.intentMetric
    if (!m) { log(`⚠ Cannot rebuild "${componentName}" — built before intent persistence. Re-run a fresh build.`); continue }
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
  }
}
```
Replace the REBUILD branch body with `rebuildAllWidgets(P, state, timeRange)`.

- [ ] **Step 2: Add `runUpgrade`**

```js
/**
 * Upgrade an existing dashboard to the current scaffold: refresh the disposable
 * framework, migrate intent.json, regenerate widgets/views from durable intent +
 * on-disk metric modules, re-validate, and re-stamp versions. The durable set
 * (intent.json, src/metrics, .dashboard, .env.local, uipath.json) is preserved
 * because the scaffold template does not contain those paths.
 * @param {string} P  resolved project dir
 * @param {object} state  parsed state.json
 * @param {string} intentPath  the edit-intent path (for the migrations dir + retry signal)
 */
async function runUpgrade(P, state, intentPath) {
  // Best-effort dirty-tree warning (the upgrade regenerates disposable files).
  try {
    const dirty = execSync(`git -C "${P}" status --porcelain`, { stdio: 'pipe' }).toString().trim()
    if (dirty) log('⚠ Project has uncommitted changes — upgrade will regenerate disposable files (your intent.json + src/metrics are preserved).')
  } catch { /* not a git repo — nothing to check */ }

  // 1. Refresh the disposable scaffold framework (Phase 3: extract the zip instead).
  copyDir(SCAFFOLD_DIR, P)
  try { rmSync(join(P, 'node_modules'), { recursive: true, force: true }) } catch { /* keep deps if present */ }

  // 2. Migrate intent.json if present (no-op today).
  const intentJsonPath = join(P, 'intent.json')
  if (existsSync(intentJsonPath)) {
    const migrated = await runIntentMigrations(
      JSON.parse(readFileSync(intentJsonPath, 'utf8')),
      join(dirname(intentPath), 'migrations'),
    )
    writeAtomic(intentJsonPath, JSON.stringify(migrated, null, 2))
  }

  // 3. Ensure deps, then regenerate.
  const LOCK_SIGNAL = join(P, 'node_modules', '.package-lock.json')
  if (!existsSync(LOCK_SIGNAL)) { log('⚙ Installing dependencies…'); await runPrewarm(P) }
  rebuildAllWidgets(P, state, state.timeRange ?? '30d')
  const widgetMeta = Object.entries(state.widgets ?? {}).map(([name, info]) => ({ componentName: name, template: info.template ?? 'ranked-table' }))
  generateDashboardFiles(P, widgetMeta, state.app?.name ?? 'Dashboard', state.app?.description ?? '')
  injectAppRoutes(P, Object.keys(state.widgets ?? {}).filter(n => existsSync(join(P, 'src', 'dashboard', 'views', `${n}View.tsx`))))

  // 4. Validate (Stage A then full tsc).
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
```

- [ ] **Step 3: Route a lone UPGRADE op**

In `runIncrementalEdit`, immediately after `const { ops } = classifyEditIntent(editIntent)`, add:
```js
  if (ops.length === 1 && ops[0].op === 'UPGRADE') {
    await runUpgrade(P, state, intentPath)
    return
  }
```
(This runs the project-wide upgrade instead of the per-widget batch loop. The drift `emit('UPGRADE_AVAILABLE', …)` from Task 2 already fired above this point — harmless.)

- [ ] **Step 4: Parse check + unit suite**

Run: `node --check ...build-dashboard.mjs` and `node --test skills/uipath-coded-apps/assets/scripts/tests/` (no unit regressions — `runUpgrade` is integration-tested in Task 6).

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
git commit -m "feat(dashboards): UPGRADE op — refresh scaffold, migrate, rebuild, re-stamp"
```

---

## Task 5: Docs — versions, offer-on-detect, UPGRADE op

**Files:**
- Modify: `references/dashboards/primitives/state-file.md`, `references/dashboards/primitives/incremental-editor.md`, `references/dashboards/plugins/build/impl.md`

- [ ] **Step 1: `state-file.md`** — bump the schema example to `schemaVersion: 2` and add a `versions` block (`skill`, `scaffold`, `intentSchema`, `sdk`). Add a rule: "`versions` records what the dashboard was built against; `scaffold` drift drives the upgrade offer."

- [ ] **Step 2: `incremental-editor.md`** — document the `UPGRADE` op: `{ "projectDir": "...", "op": "UPGRADE" }` (no target/metric). It refreshes the scaffold framework, migrates intent, regenerates all widgets/views from persisted metadata + on-disk modules, re-validates, re-stamps versions. Preserves `intent.json` + `src/metrics`. Watch events: `UPGRADE_DONE` (success), `METRICS_RETRY`/`TSC_FAIL` (regeneration failed).

- [ ] **Step 3: `impl.md`** — add an "Offer-on-detect upgrade" note: when the build/edit emits `UPGRADE_AVAILABLE:{from,to}`, tell the user a newer dashboard scaffold is available and offer to upgrade (same plan→confirm ethos — a short structured question or plain offer). On confirm, run an `UPGRADE` edit-intent via the build subagent. Never auto-upgrade.

- [ ] **Step 4: Commit**

```bash
git add skills/uipath-coded-apps/references/
git commit -m "docs(dashboards): version stamps, offer-on-detect upgrade, UPGRADE op"
```

---

## Task 6: Self-test + full validation

**Files:** none committed beyond what Tasks 1-5 produced (this task runs real builds).

- [ ] **Step 1: Full unit suite** — `node --test skills/uipath-coded-apps/assets/scripts/tests/` → all green.

- [ ] **Step 2: Real build stamps versions** — build a fixture dashboard (reuse the Phase-1 self-test shape: an `intent.json` with `projectDir`, `routingName`, 2-3 T1 metrics + `metrics/*.ts`). Run `node ...build-dashboard.mjs <fixture>/intent.json`. Confirm `<project>/.dashboard/state.json` has `schemaVersion: 2` and a `versions` block with `scaffold` = `SCAFFOLD_VERSION` and `sdk` populated.

- [ ] **Step 3: Drift + UPGRADE** — temporarily bump `SCAFFOLD_VERSION` to `'1.1.0'` in the script; re-run the build (or an incremental edit) and confirm `UPGRADE_AVAILABLE:{from:"1.0.0",to:"1.1.0"}` is emitted. Then run an `UPGRADE` edit-intent (`{ projectDir, op: "UPGRADE" }`) and confirm `UPGRADE_DONE`, the app still `TSC_PASS`-clean, and `state.versions.scaffold` is now `1.1.0`. Revert the `SCAFFOLD_VERSION` bump.

- [ ] **Step 4: Clean up** the temp project dir.

- [ ] **Step 5: Commit** (only if Step 3 required a committed test fixture/task; otherwise nothing to commit).

---

## Self-Review (completed by plan author)

- **Spec §4 coverage:** (a) version stamps → Task 1. (b) `state.schemaVersion`→2 → Task 1. (c) migration registry → Task 3. (d) offer-on-detect + upgrade flow → Tasks 2 (detect) + 4 (UPGRADE) + 5 (offer). (e) durable/disposable preservation → Task 4 (`copyDir` doesn't touch intent.json/src/metrics/.dashboard/.env).
- **Placeholders:** new helpers (`buildVersions`, `scaffoldDrift`, `runIntentMigrations`, `rebuildAllWidgets`, `runUpgrade`) have complete code; doc tasks describe concrete edits.
- **Type consistency:** `buildVersions(sdkVersion)` shape `{ skill, scaffold, intentSchema, sdk }` used identically in Tasks 1/4; `scaffoldDrift → {from,to}` matches the `UPGRADE_AVAILABLE` payload (Task 2) and the self-test assertion (Task 6); `rebuildAllWidgets(P, state, timeRange)` defined in Task 4 Step 1, called in Task 4 Step 2.
- **Interim/Phase-3 seam:** `SCAFFOLD_VERSION` constant + `copyDir` are explicitly flagged as Phase-3-superseded — no hidden coupling.

---

## Execution Handoff

Phase 2 only. Phase 3 (zip fixture) is the final, separate plan — it will replace the `SCAFFOLD_VERSION` constant with `scaffold.manifest.json` and the `copyDir` upgrade-refresh with zip-extraction.
