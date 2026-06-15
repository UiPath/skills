# Dashboard Skill — Compiler Architecture (design)

**Date:** 2026-06-15
**Skill:** `skills/uipath-coded-apps` (NLP dashboards)
**Status:** Design — awaiting review. Implementation gated behind approval.
**Origin:** Architecture review feedback (Viswanath Lekshmanan), three points.

---

## 1. Problem

Three pieces of review feedback, all pointing at one missing boundary.

1. **TypeScript code lives inside `intent.json`.** Each metric carries its SDK call as a `fnBody` **string** (`references/dashboards/primitives/tier-resolution.md:95`). The string is spliced into a `customDataFn` block inside the generated widget (`build-dashboard.mjs:761-794`), and the **only** type-check is a single whole-app `npx tsc --noEmit` at the end of the build (`build-dashboard.mjs:1082`). Which widget failed is recovered by regex over tsc output (`widgetNameFromTscErrors`). Code-as-string in JSON has no editor support, no isolated type-check, and errors surface late, mixed with app errors.
   **Ask:** put function bodies in real `.ts` files, compile them and emit errors *separately*, before hooking into the whole app.

2. **The scaffold is ~39 loose files** under `assets/templates/dashboard/scaffold/` (project skeleton) and `assets/templates/dashboard/widgets/` (6 chart templates + `t3-shell.tsx.template`), with no version identity.
   **Ask:** package templates + widgets as a zip that serves as the skill's starting fixture.

3. **No upgrade path.** `state.json` is `schemaVersion: 1`, persists each widget's full `intentMetric`, and there is a `REBUILD` op — but there is no scaffold/skill version stamp and no migration mechanism.
   **Ask:** version things so that when a new widget library lands later, existing dashboards (their `intent.json` + agent-generated files) are easy to update.

### The unifying gap

The skill is today a **generator** (prompt → files, one-shot). The three asks turn it into a **compiler**:

```
versioned-fixture  +  durable-intent  →  dashboard app
```

where an **upgrade** is just *recompile the same durable intent against a newer fixture*.

---

## 2. Core architecture — three layers

| Layer | What it is | Today | Lifecycle |
|---|---|---|---|
| **Durable source** | what the user meant — metadata + metric logic | `intent.json` with `fnBody` strings | preserved forever; survives upgrades |
| **Disposable output** | the React app | generated widgets/views/layout + scaffold libs | regenerated at will |
| **Versioned fixture** | scaffold + chart templates | ~39 loose, unversioned files | swapped as a unit when the library evolves |

**Durable set** (preserved across upgrades): `intent.json`, `src/metrics/**`, `.dashboard/state.json`, `.env.local`, `uipath.json` (deploy identity).
**Disposable set** (regenerated): everything else — `src/dashboard/widgets/**`, `views/**`, `App.tsx`, `src/lib/**`, `components/**`, `chrome/**`, config files.

Drawing this boundary is the through-line of all three phases.

---

## 3. Phase 1 — Metric code → real `.ts` modules, compiled in isolation

### 3.1 `intent.json` becomes pure metadata

`fnBody` is removed from every metric. The metric's data function lives in a real file. Module path is conventional (`metrics/<name>.ts`) with an optional explicit `module` override; the data export is always `fetchData`, the optional record-grain detail export is `fetchDetail`.

Before:
```json
{ "name": "agent-memory-timeline", "tier": "T1", "title": "Agent Memory",
  "fnBody": "const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')\nreturn await new AgentMemory(sdk as never).getTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })" }
```

After (the `intent.json` envelope — `dashboardName`, `timeRange`, `metrics[]` — is unchanged; only `schemaVersion` is added and `fnBody`/`detailFnBody` are removed from each metric):
```json
{ "schemaVersion": 2,
  "dashboardName": "Agent Operations",
  "timeRange": "30d",
  "metrics": [
    { "name": "agent-memory-timeline", "tier": "T1", "title": "Agent Memory",
      "displayAs": "area-chart", "xKey": "timeSlice", "yKey": "totalCount",
      "headlineMode": "sum", "deltaPolarity": "up-good" }
  ] }
```
The code moves to `metrics/agent-memory-timeline.ts`.

### 3.2 Agent input layout

The agent authors a folder (working dir), not a lone JSON:
```
<workdir>/
  intent.json            # metadata only
  metrics/
    agent-memory-timeline.ts
    job-failures.ts
```
The build still takes the `intent.json` path as its single argument; metric modules resolve from `<intent-dir>/metrics/<name>.ts` by convention.

### 3.3 The metric module contract

New scaffold file `src/lib/metric-contract.ts`:
```ts
// The data-fetch signature every metric module exports. sdk is `any` because the
// SDK service constructors take `sdk as never`; the array return preserves the
// settled Promise<any[]> harness (SDK response interfaces are not assignable to
// Record<string, unknown>[], so any[] keeps the "must return an array" check
// without forcing casts).
export type MetricFn = (sdk: any, getToken: () => Promise<string>) => Promise<any[]>
```

A metric module (`src/metrics/agent-memory-timeline.ts`):
```ts
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { AgentMemory } = await import('@uipath/uipath-typescript/agent-memory')
  return await new AgentMemory(sdk as never).getTimeline({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
}
```

### 3.4 Time constants move out of the splice

Today `TIME_CONSTANTS` is a string injected after the last import of each widget (`build-dashboard.mjs:142, 366-374`). New scaffold module `src/lib/time.ts` exports them; metric modules import what they need:
```ts
export const NOW = new Date()
export const ONE_DAY_AGO = new Date(Date.now() - 86_400_000)
export const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000)
export const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000)
export const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000)
```
`NOW` is fixed at module load — acceptable for a dashboard session.

### 3.5 Two-stage compile

`tsconfig.metrics.json` (scaffold) — isolated, fast, no React:
```json
{ "extends": "./tsconfig.json",
  "include": ["src/metrics/**/*.ts", "src/lib/metric-contract.ts", "src/lib/paginate.ts", "src/lib/time.ts"],
  "compilerOptions": { "noEmit": true } }
```
The metric modules import only pure libs (`metric-contract`, `paginate`, `time`) + the SDK `.d.ts`. None pull React, so the metrics compile is small and fast.

Build flow:

- **Stage A (new):** after scaffold extract + pre-warmed `npm ci`, copy `metrics/*.ts` into `src/metrics/`, run `npx tsc -p tsconfig.metrics.json`. On failure → `METRICS_RETRY:{ files:[...], errors:[...] }`, exit 2. Errors map **directly** to `src/metrics/<name>.ts` (no regex guessing). Agent fixes the named files, re-runs Stage A only.
- **Stage B:** once Stage A is green, generate widgets that **import** the metric module (`import { fetchData } from '@/metrics/<name>'` → `useWidgetData(fetchData, [])`) instead of splicing a string. Generate layout/views/routes. Run the full-app `tsc` as a backstop (now rarely the failing layer; remaining failures are template/integration issues, not fnBody).

`useWidgetData` is unchanged — it already injects `sdk`/`getToken` into the supplied function; the function is now imported rather than locally declared.

### 3.6 `state.json` stores module refs, not code

`widgets.<Component>.intentMetric` keeps metadata; `fnBody` is dropped. The durable code is the `src/metrics/<name>.ts` file in the project. State references the module; the file is the source of truth.

### 3.7 Incremental editor impact

`edit-intent.json` ops act on metric files directly:
- **ADD** — write `src/metrics/<name>.ts` + metadata; Stage-A compile; generate widget.
- **CHANGE** — edit the existing `src/metrics/<name>.ts` (and/or metadata); Stage-A compile; regenerate the widget + view.
- **REMOVE** — delete the module + widget.
- **REBUILD** — regenerate every widget from durable intent + existing metric files (the seed of the upgrade flow).

Batch semantics (one `ops[]` run, validate-all-then-apply, single regen + single tsc) are preserved; the validation step gains the Stage-A metrics compile.

---

## 4. Phase 2 — Versioning + upgrade

### 4.1 Version stamps

`state.json` gains:
```json
"versions": { "skill": "x.y.z", "scaffold": "x.y.z", "intentSchema": 2, "sdk": "1.4.0" }
```
`skill` from the plugin manifest, `scaffold` from `scaffold.manifest.json` (Phase 3), `intentSchema` is the literal, `sdk` from the existing `checkSdkVersion`. Stamped on every build.

`intent.json` gains its own `schemaVersion` (only `state.json` had one). Both schemas start the new architecture at **version 2** (the module-based world). There is **no v1→v2 migrator** — pre-architecture dashboards are pre-production and simply rebuilt fresh (per decision).

### 4.2 Migration registry (framework, initially empty)

`assets/scripts/migrations/` with a runner that applies `intent-v<N>-to-v<N+1>.mjs` in sequence from the artifact's `schemaVersion` up to the current. Ships with **zero** migrations — it exists so future schema changes are a drop-in file, not a refactor. This is the forward mechanism Viswa asked for; YAGNI keeps us from writing migrations we do not need yet.

### 4.3 Upgrade flow — offer-on-detect

At build/edit start, compare `state.versions.scaffold` to the shipped fixture version:
- Equal → normal path.
- Older → emit `UPGRADE_AVAILABLE:{ from, to, changes }`. The skill (per `plugins/build/impl.md`) tells the user what changed and offers to upgrade — consistent with the existing plan→confirm ethos. Silent auto-upgrade is rejected (surprise regen risk); explicit-only is rejected (undiscoverable).

On confirm:
1. Require a clean git tree for the project (or take a backup) — refuse otherwise, tell the user.
2. Extract the new fixture (Phase 3) over the **disposable set** only.
3. Run schema migrations (none yet).
4. **REBUILD** all widgets/views/layout from durable intent + `src/metrics/**` against the new fixture.
5. Stage-A compile metrics against the new SDK/contract, then full-app tsc; on metric failure, the same `METRICS_RETRY` loop applies.
6. Re-stamp `state.versions`.

Because the durable set is preserved and everything else is regenerated, an upgrade is "REBUILD against a newer fixture + (future) schema migration."

---

## 5. Phase 3 — Zip fixture

### 5.1 Source of truth stays loose

`templates/dashboard/scaffold/**` and `templates/dashboard/widgets/**` remain loose files — diffable, greppable, **PR-reviewable** (the repo's quality model; `content-quality.md` bans binaries). They are the editable truth.

### 5.2 Pack step

`assets/scripts/pack-scaffold.mjs` zips both dirs into a committed, versioned artifact:
```
assets/fixtures/scaffold-v<semver>.zip
assets/fixtures/scaffold.manifest.json   # { version, sha256, builtFrom, files }
```
The zip is committed so the shipped skill has a ready fixture (no pack step at user-build time). Reviewers read the loose-source diff and ignore the regenerated binary; CI/pre-commit can verify the zip matches source via the manifest checksum.

### 5.3 Build consumes the fixture

The build extracts `scaffold-v<semver>.zip` into the project instead of `cp -r`. The fixture version flows into `state.versions.scaffold` (Phase 2).

### 5.4 Cross-platform extraction

`.zip` extraction is **not** uniformly available: GNU `tar` (Linux/CI) cannot extract zip, and `unzip` is not guaranteed on Windows. So extraction uses a **dependency-free Node helper** `assets/scripts/lib/unzip.mjs` (parse the zip central directory + `zlib.inflateRawSync` per entry — ~100 lines, no npm dependency, works wherever Node runs). *Alternative if preferred during implementation:* ship `.tgz` instead — `zlib.gunzipSync` + a minimal tar reader is even simpler in pure Node and `tar` extracts it everywhere. Default is `.zip` per decision.

---

## 6. Data flow (target)

```
FRESH BUILD
  agent → intent.json (metadata) + metrics/*.ts
        → build: extract fixture@vY  →  npm ci (pre-warmed)
        → Stage A: tsc -p tsconfig.metrics.json   ──fail──▶ METRICS_RETRY (fix metrics/*.ts) ─┐
        → Stage B: generate widgets (import metric modules) + layout + views                  │
        → full-app tsc (backstop)                                                             │
        → stamp state.versions → BUILD_RESULT                                                 │
                                                                                              ▼
                                                                                    agent edits metric file, re-runs

UPGRADE (offer-on-detect)
  build start → scaffold drift? → UPGRADE_AVAILABLE → user confirms
             → preserve durable set → extract fixture@vZ over disposable set
             → migrate intent (none yet) → REBUILD from durable intent + metrics/*.ts
             → Stage A + full tsc → re-stamp versions
```

---

## 7. Testing

**Unit** (`assets/scripts/tests/*.test.mjs`, `node --test`):
- intent schema v2 validation (rejects `fnBody`; resolves `metrics/<name>.ts`; module convention + override).
- metric-contract type presence; widget wiring emits an `import` not a splice.
- Stage-A isolated-compile: success path; failure maps to the exact `.ts` file in `METRICS_RETRY`.
- version stamping writes all four fields.
- migration runner: no-op chain passes; a synthetic v2→v3 proves sequencing.
- `unzip.mjs` round-trip: pack → unzip → byte/checksum equality vs source.
- upgrade flow: drift detection; durable set preserved; disposable set regenerated.

**Smoke** (coder-eval tasks under `tests/tasks/uipath-coded-apps/dashboard/`):
- fresh build with metric modules → app compiles, widgets present.
- deliberately broken metric `.ts` → `METRICS_RETRY` fires on the right file → fix → pass.
- upgrade-on-detect → build at fixture vA, bump shipped version, next build offers + regenerates.

The existing dashboard coder-eval suite is already stale (flagged earlier; references old `useInsights`/PAT/`src-widgets`). This work is the moment to refresh it to the module architecture.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Cross-platform `.zip` extraction | Dependency-free `unzip.mjs` (no system tool); `.tgz` fallback documented |
| Isolated `tsconfig.metrics` accidentally pulls React (slow / wrong errors) | Keep `metric-contract`/`paginate`/`time` pure; assert in a unit test that the metrics compile resolves no React types |
| Two scaffold representations (loose + zip) drift | Manifest sha256 + CI/pre-commit check that the zip matches loose source |
| `useWidgetData` signature mismatch with imported `MetricFn` | Contract type is the single source; widget template + hook both reference it |
| `NOW` fixed at module load | Acceptable for a session; documented |

---

## 9. Non-goals (YAGNI)

- No v1→v2 backfill migrator (new skill; pre-prod dashboards rebuild fresh).
- No actual migration scripts yet — registry framework only.
- Look-and-feel customization stays doc-level (`customization.md`) — unchanged.
- No change to OAuth, deploy, or the dev-server-as-background-job lifecycle.

---

## 10. Phasing

1. **Phase 1 — metric modules + two-stage compile.** Independently shippable; immediately cuts the retry cost and makes `intent.json` pure metadata. Foundation for the durable/disposable split.
2. **Phase 2 — versioning + offer-on-detect upgrade.** Needs Phase 1's durable split. (Needs a *versioned* fixture, which the Phase 3 manifest supplies — but the version *stamp* can land here even before zipping.)
3. **Phase 3 — zip fixture.** Pack step + `unzip.mjs` + build consumes the fixture. Last and most self-contained.
