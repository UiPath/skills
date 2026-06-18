# Maestro Insights + SLA Dashboard Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the Maestro/process analytics blind spot in the `uipath-coded-apps` dashboard skill by cataloging the SDK's Maestro Insights RTM family (SLA, top-N, status timeline, element stats), and fix the two stale hard-refuses (`sla.*breach`, blanket error-text) that contradict the installed SDK.

**Architecture:** The skill is data + docs, not logic. Each metric is a catalog entry in `capability-registry.json` (display hints) + a row in `tier-resolution.md`; the dashboard build subagent writes the `metrics/<name>.ts` module at dashboard-build time from the SDK call documented in the entry. Correctness therefore hinges on (a) exact request/response DTOs in the registry descriptions and `sdk/maestro.md`, and (b) the resolution test suite (`resolution.test.mjs`) which mechanically verifies alias resolution, hard-refuse non-collision, and clean widget generation. Scopes are a single static broad grant (`DASHBOARD_SCOPES` in `build-dashboard.mjs`, mirrored in the external-app `--user-scope` and `oauth-scopes.md`); the new methods need `Insights Insights.RealTimeData`, already present — so scope work is documentation + a consistency guard test, not a value change.

**Tech Stack:** JSON catalog, Markdown references, Node `node:test` (`resolution.test.mjs`), `build-dashboard.mjs` (`buildWidgetFile`/`resolveAlias` exports). No app/runtime code changes.

---

## Ground-truth DTOs (verified against SDK source — do NOT deviate)

All paths are in `C:\Work\uipath-typescript`. All Maestro Insights endpoints resolve to `INSIGHTS_RTM_BASE` (`utils/constants/endpoints/maestro.ts:38-55`).

**Scopes (authoritative — from `C:\Work\uipath-typescript\docs\oauth-scopes.md:77-124`):**
- `Cases`/`MaestroProcesses` `getTopRunCount`/`getTopFaultedCount`/`getTopExecutionDuration`/`getTopElementFailedCount`/`getInstanceStatusTimeline`/`getElementStats` → **`Insights.RealTimeData Insights OR.Folders.Read`** (no PIMS).
- `CaseInstances.getSlaSummary`/`getStagesSlaSummary` → **`Insights.RealTimeData Insights OR.Folders.Read PIMS`** — the SLA methods additionally require **`PIMS`**.

`DASHBOARD_SCOPES` (build-dashboard.mjs:343) already grants `OR.Folders` (covers `OR.Folders.Read`), `Insights`, `Insights.RealTimeData` — so the Top/timeline/element metrics need **no scope change**. It does **NOT** grant `PIMS`, so the SLA metrics (and the pre-existing `cases-running-above` T2, which uses `Cases.getAll` → `PIMS`) require adding `PIMS` everywhere. Task 7 does this.

**CaseInstances** — subpath `@uipath/uipath-typescript/cases` (`services/maestro/cases/case-instances.ts`):

| Method | Signature | Returns | Row shape |
|--------|-----------|---------|-----------|
| `getSlaSummary(options?)` | options object: `{ caseInstanceId?, startTimeUtc?: Date, endTimeUtc?: Date, pageSize?, cursor?, jumpToPage? }` | `NonPaginatedResponse<SlaSummaryResponse>` (`.items`, default top 50) or `PaginatedResponse` w/ pagination opts | `{ caseInstanceId, folderKey, name, externalId, caseSummary, processKey, slaDueTime (ISO UTC), slaStatus, escalationRuleIndex, escalationRuleType, instanceStatus, lastModifiedTime (ISO UTC) }` |
| `getStagesSlaSummary(options?)` | `{ caseInstanceId? }` | **bare** `CaseInstanceStageSLAResponse[]` | `{ caseInstanceId, stages: { elementId, name, latestStatus, slaDueTime (LOCALE str e.g. "9/17/2025 8:35:38 PM"), slaStatus, escalationRuleIndex, escalationRuleType }[] }` |

`SlaSummaryStatus` string values (`models/maestro/case-instances.types.ts:103`): `'On Track'`, `'At Risk'`, `'Overdue'`, `'Completed'`, `'Unknown'`.

**Cases** (`services/maestro/cases/cases.ts`) and **MaestroProcesses** (`services/maestro/processes/processes.ts`) — **identical signatures**, subpaths `@uipath/uipath-typescript/cases` and `@uipath/uipath-typescript/maestro-processes`:

| Method | Signature | Returns (bare array) | Row shape |
|--------|-----------|----------------------|-----------|
| `getTopRunCount(start: Date, end: Date, options?: TopQueryOptions)` | `TopQueryOptions = { packageId?, processKey?, version? }` | `{packageId, processKey, runCount, name}[]` (≤5) | runCount |
| `getTopFaultedCount(start, end, options?)` | same | `{packageId, processKey, faultedCount, name}[]` (≤10) | faultedCount |
| `getTopExecutionDuration(start, end, options?)` | same | `{packageId, processKey, duration, name}[]` (≤5) | duration (ms) |
| `getTopElementFailedCount(start, end, options?)` | same | `{elementName, elementType, processKey, failedCount}[]` (≤10) | failedCount |
| `getInstanceStatusTimeline(start, end, options?: TimelineOptions)` | `TimelineOptions = { groupBy?: TimeInterval }` (`HOUR`/`DAY`/`WEEK`, default DAY) | `{startTime (LOCALE str), status, count}[]` | `status` ∈ `'Completed'`/`'Faulted'`/`'Cancelled'` |
| `getElementStats(processKey, packageId, start: Date, end: Date, packageVersion)` | all positional | `{elementId, successCount, failCount, terminatedCount, pausedCount, inProgressCount, minDurationMs, maxDurationMs, avgDurationMs, p50DurationMs, p95DurationMs, p99DurationMs}[]` | percentiles |

> For Cases, `name` is derived from `packageId` (CaseManagement prefix stripped); for MaestroProcesses, `name === packageId`. Both present on every row — safe to display `name`.

**Module rules for these methods:**
- Compare `slaStatus` / `status` as **strings** (`String(row.status) === 'Faulted'`) — do NOT import the enums (avoids unverified-export risk + TS2367 narrowing errors). The literal values above are source-verified.
- `getSlaSummary` rows are on `.items`; use `fetchAll(cursor => svc.getSlaSummary({ pageSize: 200, cursor }))`. Every other method returns a **bare array** — return as-is or reshape, never `.items`.
- All take **positional `Date`s** except `getSlaSummary` (options object with `startTimeUtc`/`endTimeUtc`).

---

## File structure

| File | Change |
|------|--------|
| `references/sdk/maestro.md` | Add the 8 Insights/SLA methods (Cases+Processes share 6; CaseInstances adds 2) with DTOs + module patterns + scope note |
| `assets/scripts/capability-registry.json` | Remove `sla.*breach` refuse; narrow error-text refuse; add 13 T1 + 1 T2 entries |
| `references/dashboards/primitives/tier-resolution.md` | T1/T2 table rows; remove SLA T0 row; update error-text T0 row; calling conventions; read-method allowlist |
| `references/oauth-scopes.md` | New "Maestro Insights — RTM" section; update Insights bundle row |
| `references/dashboards/CAPABILITY.md` | Add SLA/insights keywords to the maestro conditional-load row |
| `references/dashboards/plugins/build/impl.md` | Document the minimal-fallback Insights caveat |
| `assets/scripts/tests/resolution.test.mjs` | Resolution + non-refuse + widget-gen + scope-consistency tests |

No change to `build-dashboard.mjs` (`DASHBOARD_SCOPES` already includes `Insights Insights.RealTimeData`) or the scaffold env writer.

---

### Task 1: Refresh `sdk/maestro.md` (source of truth for the build subagent)

**Files:**
- Modify: `skills/uipath-coded-apps/references/sdk/maestro.md`

This doc currently documents only `getAll`/`getIncidents`/instance services. The build subagent cites it to write modules, so it must carry the new methods with exact DTOs before any catalog entry references them.

- [ ] **Step 1: Append a "Maestro Insights — RTM" section** documenting all 8 methods.

Add after the existing Cases/CaseInstances content:

````markdown
## Maestro Insights — RTM (SDK ≥ 1.4.x)

> Scope: `Insights Insights.RealTimeData` (these use the Insights RTM host, NOT PIMS — contrast with `Cases.getAll`/`CaseInstances.getAll`). Surface a 403 as a permissions message (the External App may lack Insights scopes in this environment).

`Cases` (`@uipath/uipath-typescript/cases`) and `MaestroProcesses` (`@uipath/uipath-typescript/maestro-processes`) expose the **same six methods** with identical signatures. `CaseInstances` (`@uipath/uipath-typescript/cases`) adds the two SLA methods.

**Positional `Date` args** (`start, end`) for the six analytics methods; `getSlaSummary` takes an **options object**. All return a **bare array** except `getSlaSummary` (rows on `.items`).

| Method | Returns (bare array of) | Notes |
|--------|------------------------|-------|
| `getTopRunCount(start, end, options?)` | `{ packageId, processKey, runCount, name }` | ≤5, ranked. `options`: `{ packageId?, processKey?, version? }` |
| `getTopFaultedCount(start, end, options?)` | `{ packageId, processKey, faultedCount, name }` | ≤10, ranked |
| `getTopExecutionDuration(start, end, options?)` | `{ packageId, processKey, duration, name }` | ≤5, `duration` in ms |
| `getTopElementFailedCount(start, end, options?)` | `{ elementName, elementType, processKey, failedCount }` | ≤10, BPMN elements |
| `getInstanceStatusTimeline(start, end, options?)` | `{ startTime, status, count }` | `status` ∈ `Completed`/`Faulted`/`Cancelled`; `startTime` is a LOCALE string; `options`: `{ groupBy?: TimeInterval }` (HOUR/DAY/WEEK, default DAY) |
| `getElementStats(processKey, packageId, start, end, packageVersion)` | `{ elementId, successCount, failCount, terminatedCount, pausedCount, inProgressCount, minDurationMs, maxDurationMs, avgDurationMs, p50DurationMs, p95DurationMs, p99DurationMs }` | all positional args |

`CaseInstances` SLA methods:

| Method | Returns | Row shape |
|--------|---------|-----------|
| `getSlaSummary(options?)` | `{ items: SlaSummaryResponse[] }` (default top 50) or paginated | `{ caseInstanceId, folderKey, name, externalId, caseSummary, processKey, slaDueTime (ISO UTC), slaStatus, escalationRuleIndex, escalationRuleType, instanceStatus, lastModifiedTime }`. `options`: `{ caseInstanceId?, startTimeUtc?: Date, endTimeUtc?: Date }` + pagination |
| `getStagesSlaSummary(options?)` | **bare** `{ caseInstanceId, stages: Stage[] }[]` | `Stage = { elementId, name, latestStatus, slaDueTime, slaStatus, escalationRuleIndex, escalationRuleType }`. `options`: `{ caseInstanceId? }` |

`slaStatus` string values: `'On Track'`, `'At Risk'`, `'Overdue'`, `'Completed'`, `'Unknown'`. **Compare as strings — do not import the enum.**

### Module patterns

```ts
// Top processes by run count (ranked-table) — native shape, return as-is
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { MaestroProcesses } = await import('@uipath/uipath-typescript/maestro-processes')
  return await new MaestroProcesses(sdk as never).getTopRunCount(THIRTY_DAYS_AGO, NOW)
}
```

```ts
// Process instance status over time (multi-line-chart) — pivot long→wide, seed all series
export const fetchData: MetricFn = async (sdk) => {
  const { MaestroProcesses } = await import('@uipath/uipath-typescript/maestro-processes')
  const points = await new MaestroProcesses(sdk as never).getInstanceStatusTimeline(THIRTY_DAYS_AGO, NOW)
  const byDate: Record<string, Record<string, unknown>> = {}
  for (const p of points) {
    const d = String(p.startTime)
    byDate[d] = byDate[d] ?? { date: d, Completed: 0, Faulted: 0, Cancelled: 0 }
    byDate[d][String(p.status)] = p.count
  }
  return Object.values(byDate)
}
```

```ts
// SLA status breakdown (donut-chart) — group by status string
export const fetchData: MetricFn = async (sdk) => {
  const { CaseInstances } = await import('@uipath/uipath-typescript/cases')
  const { fetchAll } = await import('@/lib/paginate')
  const rows = await fetchAll(cursor => new CaseInstances(sdk as never).getSlaSummary({ pageSize: 200, cursor }))
  const by: Record<string, number> = {}
  for (const r of rows) { const k = String(r.slaStatus); by[k] = (by[k] ?? 0) + 1 }
  return Object.entries(by).map(([name, value]) => ({ name, value }))
}
```

```ts
// Cases at SLA risk (data-table) — filter At Risk / Overdue
export const fetchData: MetricFn = async (sdk) => {
  const { CaseInstances } = await import('@uipath/uipath-typescript/cases')
  const { fetchAll } = await import('@/lib/paginate')
  const rows = await fetchAll(cursor => new CaseInstances(sdk as never).getSlaSummary({ pageSize: 200, cursor }))
  return rows.filter(r => { const s = String(r.slaStatus); return s === 'At Risk' || s === 'Overdue' })
}
```

```ts
// Stage-level SLA (data-table) — flatten stages
export const fetchData: MetricFn = async (sdk) => {
  const { CaseInstances } = await import('@uipath/uipath-typescript/cases')
  const data = await new CaseInstances(sdk as never).getStagesSlaSummary()
  return data.flatMap(d => d.stages.map(s => ({
    caseInstanceId: d.caseInstanceId, stage: s.name, slaStatus: s.slaStatus, slaDueTime: s.slaDueTime, latestStatus: s.latestStatus,
  })))
}
```

```ts
// Element latency stats (T2 — identifiers baked in at authoring time)
export const fetchData: MetricFn = async (sdk) => {
  const { MaestroProcesses } = await import('@uipath/uipath-typescript/maestro-processes')
  return await new MaestroProcesses(sdk as never).getElementStats('<processKey>', '<packageId>', THIRTY_DAYS_AGO, NOW, '<version>')
}
```
````

- [ ] **Step 2: Verify all relative links resolve and the doc has no leftover TODOs.** Run:

```bash
grep -n "TODO\|FIXME\|<PLACEHOLDER>" skills/uipath-coded-apps/references/sdk/maestro.md || echo "clean"
```
Expected: `clean`

- [ ] **Step 3: Commit.**

```bash
git -C C:/Work/skills add skills/uipath-coded-apps/references/sdk/maestro.md
git -C C:/Work/skills commit -m "docs(dashboards): document Maestro Insights RTM + SLA methods in sdk/maestro.md"
```

---

### Task 2: Narrow the stale error-text hard-refuse (review item 4)

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/capability-registry.json`
- Modify: `skills/uipath-coded-apps/references/dashboards/primitives/tier-resolution.md`
- Test: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

The `error.*message|stack.*trace|exception.*text` refuse claims "No aggregation endpoint for error text" — false: `Agents.getErrors` returns aggregated `{type, description, count}` (already T1 `agent-errors`) and `ProcessIncidents.getAll` returns `{errorMessage, count}`. Narrow it to raw RPA-job stack traces only.

- [ ] **Step 1: Write the failing test.** Add to `resolution.test.mjs` (after the existing 1.4.1 refuse tests):

```js
test('error-text refuse is narrowed: aggregated error classes are NOT refused', () => {
  for (const text of ['top errors', 'errors by type', 'agent error breakdown']) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(!refused, `"${text}" must not be hard-refused — Agents.getErrors aggregates error classes`)
  }
})

test('error-text refuse still blocks raw stack traces', () => {
  for (const text of ['show me the stack trace', 'exception text per job', 'raw error message text']) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(refused, `"${text}" should be hard-refused (no raw stack-trace aggregation)`)
  }
})
```

- [ ] **Step 2: Run to verify the first test fails** (current pattern is fine; this guards the change):

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | grep -E "error-text|# (pass|fail)"
```
Expected: the "narrowed" test passes already (current pattern doesn't match those), the "raw stack traces" test FAILS on `'raw error message text'` (current pattern needs `error.*message` which matches — verify; if both pass, the change is purely a reason/alternative correction and you note that).

- [ ] **Step 3: Edit the refuse entry** in `capability-registry.json` — replace the `error.*message|stack.*trace|exception.*text` entry with:

```json
    { "pattern": "stack.*trace|exception.*text|raw error (message|text)", "reason": "No endpoint returns raw RPA-job stack traces / exception text. (Aggregated error CLASSES are available: Agents.getErrors → {type, description, count} (agent-errors T1); Maestro process errors via ProcessIncidents.getAll → {errorMessage, count}.)", "alternative": "agent-errors (T1) for agent error classes; T3 ProcessIncidents.getAll for Maestro process error messages; or faulted-jobs data-table (errorCode/jobError per row) for RPA." },
```

- [ ] **Step 4: Update the matching T0 row** in `tier-resolution.md` (the "Error text / stack traces" row):

```markdown
| Raw RPA stack traces / exception text | No endpoint aggregates raw RPA-job error text | `agent-errors` (T1) for agent error classes; T3 `ProcessIncidents.getAll` for Maestro process error messages; faulted-jobs data-table (`errorCode`/`jobError`) for RPA |
```

- [ ] **Step 5: Run tests to verify both pass.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -8
```
Expected: all pass (no fails).

- [ ] **Step 6: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "fix(dashboards): narrow error-text hard-refuse to raw RPA stack traces"
```

---

### Task 3: SLA metrics — remove the wrong refuse, add 3 T1 metrics (review item 1)

**Files:**
- Modify: `capability-registry.json`, `tier-resolution.md`, `resolution.test.mjs`

`CaseInstances.getSlaSummary`/`getStagesSlaSummary` exist with `slaStatus` ∈ On Track/At Risk/Overdue/Completed. The `sla.*breach` refuse ("No SLA metadata in any API") is factually wrong.

- [ ] **Step 1: Write the failing test.** Add to `resolution.test.mjs`:

```js
test('SLA metrics resolve T1 and are NOT refused', () => {
  for (const [text, expected] of [
    ['sla breach', 'case-sla-breaches'],
    ['cases at risk', 'case-sla-breaches'],
    ['overdue cases', 'case-sla-breaches'],
    ['sla status', 'case-sla-status'],
    ['sla breakdown', 'case-sla-status'],
    ['stage sla', 'case-stage-sla'],
  ]) {
    const refused = registry.hardRefuse.some(e => new RegExp(e.pattern).test(text))
    assert.ok(!refused, `"${text}" must not be hard-refused — SLA summary exists`)
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('new SLA T1 entries generate clean widgets', () => {
  for (const name of ['case-sla-status', 'case-sla-breaches', 'case-stage-sla']) {
    const entry = registry.t1[name]
    assert.ok(entry, `missing ${name}`)
    const metric = { name, tier: 'T1', title: entry.defaults.title, displayAs: entry.template, ...entry.defaults }
    const content = buildWidgetFile(metric, entry, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${name} leftover placeholders`)
    assert.ok(content.includes(`import { fetchData } from '@/metrics/${name}'`), `${name} missing fetchData import`)
  }
})
```

- [ ] **Step 2: Run to verify it fails.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | grep -E "SLA|# fail"
```
Expected: FAIL (`sla breach` is currently refused; entries don't exist).

- [ ] **Step 3: Remove the `sla.*breach` refuse** from `capability-registry.json` (delete the entry):

```json
    { "pattern": "sla.*breach|breach.*sla", "reason": "Raw counts only — no SLA metadata in any API.", "alternative": "T3-SDK: new Jobs(sdk as never).getAll({ filter: \"State eq 'Faulted'\" }) to compute failure rate" },
```

- [ ] **Step 4: Add the 3 SLA T1 entries** to the `"t1"` object in `capability-registry.json`:

```json
    "case-sla-status": {
      "aliases": ["sla status", "sla breakdown", "sla overview", "cases by sla", "sla health"],
      "template": "donut-chart",
      "description": "Case-instance SLA status breakdown. SDK: page `new CaseInstances(sdk as never).getSlaSummary({ pageSize: 200, cursor })` via fetchAll → rows on `.items`, each `{ slaStatus, ... }`. Module groups by `String(slaStatus)` ('On Track'|'At Risk'|'Overdue'|'Completed'|'Unknown') → `[{ name, value }]`. Subpath @uipath/uipath-typescript/cases. Scope: Insights Insights.RealTimeData OR.Folders.Read PIMS (SLA needs PIMS). 403 ⇒ permissions message.",
      "defaults": { "title": "Case SLA Status", "description": "Case instances by SLA status", "icon": "ShieldCheck", "xKey": "name", "yKey": "value" }
    },
    "case-sla-breaches": {
      "aliases": ["sla breach", "sla breaches", "cases at risk", "at risk cases", "overdue cases", "breached sla", "sla violations"],
      "template": "data-table",
      "description": "Case instances at SLA risk. SDK: fetchAll over `new CaseInstances(sdk as never).getSlaSummary({ pageSize: 200, cursor })` (rows on `.items`), filter `String(slaStatus) === 'At Risk' || === 'Overdue'`. Each row: `{ name, externalId, slaStatus, slaDueTime, instanceStatus, processKey }`. Subpath @uipath/uipath-typescript/cases.",
      "defaults": { "title": "Cases at SLA Risk", "description": "Case instances at risk or overdue on SLA", "icon": "ShieldAlert",
        "columnDefs": [
          { "key": "name", "label": "SLA Rule" },
          { "key": "externalId", "label": "Case" },
          { "key": "slaStatus", "label": "Status" },
          { "key": "slaDueTime", "label": "Due", "format": "timeAgo" },
          { "key": "instanceStatus", "label": "Instance" }
        ] }
    },
    "case-stage-sla": {
      "aliases": ["stage sla", "stage level sla", "case stage sla", "sla by stage"],
      "template": "data-table",
      "description": "Stage-level SLA per case instance. SDK: `new CaseInstances(sdk as never).getStagesSlaSummary()` → BARE `[{ caseInstanceId, stages: [{ name, slaStatus, slaDueTime, latestStatus }] }]`. Module flattens: `data.flatMap(d => d.stages.map(s => ({ caseInstanceId: d.caseInstanceId, stage: s.name, slaStatus: s.slaStatus, slaDueTime: s.slaDueTime, latestStatus: s.latestStatus })))`.",
      "defaults": { "title": "Stage SLA", "description": "SLA status by case stage", "icon": "ListChecks",
        "columnDefs": [
          { "key": "stage", "label": "Stage" },
          { "key": "slaStatus", "label": "SLA" },
          { "key": "slaDueTime", "label": "Due" },
          { "key": "latestStatus", "label": "Stage Status" },
          { "key": "caseInstanceId", "label": "Case Instance" }
        ] }
    },
```

- [ ] **Step 5: Add T1 rows** to the T1 catalog table in `tier-resolution.md`:

```markdown
| `case-sla-status` | Case SLA status split | `donut-chart` | `CaseInstances.getSlaSummary()` → `.items` `{slaStatus}`; group by status → `[{name,value}]` |
| `case-sla-breaches` | Cases at SLA risk/overdue | `data-table` | `CaseInstances.getSlaSummary()` → filter `slaStatus` At Risk/Overdue |
| `case-stage-sla` | Stage-level SLA | `data-table` | `CaseInstances.getStagesSlaSummary()` → BARE; flatten `stages` |
```

- [ ] **Step 6: Remove the SLA T0 refuse row** in `tier-resolution.md` (the "SLA breach %" row) — delete it.

- [ ] **Step 7: Run tests.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -8
```
Expected: all pass.

- [ ] **Step 8: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "feat(dashboards): add case SLA T1 metrics; drop stale sla-breach refuse"
```

---

### Task 4: Maestro Process Insights — 5 T1 metrics (review item 2a)

**Files:**
- Modify: `capability-registry.json`, `tier-resolution.md`, `resolution.test.mjs`

- [ ] **Step 1: Write the failing test.** Add to `resolution.test.mjs`:

```js
test('Maestro process Insights metrics resolve T1', () => {
  for (const [text, expected] of [
    ['busiest processes', 'top-maestro-processes-by-runs'],
    ['top failing processes', 'top-maestro-processes-by-faults'],
    ['slowest processes', 'top-maestro-processes-by-duration'],
    ['process status over time', 'maestro-process-status-timeline'],
    ['failing elements', 'top-failing-process-elements'],
  ]) {
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('process Insights T1 entries generate clean widgets (incl. status series)', () => {
  for (const name of ['top-maestro-processes-by-runs', 'top-maestro-processes-by-faults', 'top-maestro-processes-by-duration', 'maestro-process-status-timeline', 'top-failing-process-elements']) {
    const entry = registry.t1[name]
    assert.ok(entry, `missing ${name}`)
    const metric = { name, tier: 'T1', title: entry.defaults.title, displayAs: entry.template, ...entry.defaults }
    const content = buildWidgetFile(metric, entry, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${name} leftover placeholders`)
    if (entry.template === 'multi-line-chart') assert.ok(content.includes('Faulted'), `${name} missing status series`)
  }
})
```

- [ ] **Step 2: Run to verify it fails.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | grep -E "process Insights|# fail"
```
Expected: FAIL (entries don't exist).

- [ ] **Step 3: Add the 5 T1 entries** to `capability-registry.json`:

```json
    "top-maestro-processes-by-runs": {
      "aliases": ["busiest processes", "most active processes", "top processes by runs", "most run processes", "top maestro processes"],
      "template": "ranked-table",
      "description": "Top Maestro processes by run count (≤5). SDK: `new MaestroProcesses(sdk as never).getTopRunCount(THIRTY_DAYS_AGO, NOW)` (positional Dates) → BARE `[{ packageId, processKey, runCount, name }]` (return as-is). Subpath @uipath/uipath-typescript/maestro-processes. Scope: Insights Insights.RealTimeData.",
      "defaults": { "title": "Busiest Processes", "description": "Maestro processes ranked by run count", "icon": "Activity",
        "columnDefs": [ { "key": "name", "label": "Process" }, { "key": "runCount", "label": "Runs", "align": "right", "format": "number" } ] }
    },
    "top-maestro-processes-by-faults": {
      "aliases": ["top failing processes", "most faulted processes", "processes by failure", "worst processes", "top faulted processes"],
      "template": "ranked-table",
      "description": "Top Maestro processes by faulted count (≤10). SDK: `new MaestroProcesses(sdk as never).getTopFaultedCount(THIRTY_DAYS_AGO, NOW)` → BARE `[{ packageId, processKey, faultedCount, name }]`.",
      "defaults": { "title": "Top Failing Processes", "description": "Maestro processes ranked by faults", "icon": "TriangleAlert",
        "columnDefs": [ { "key": "name", "label": "Process" }, { "key": "faultedCount", "label": "Faults", "align": "right", "format": "number" } ] }
    },
    "top-maestro-processes-by-duration": {
      "aliases": ["slowest processes", "longest running processes", "top processes by duration", "processes by duration"],
      "template": "ranked-table",
      "description": "Top Maestro processes by total execution duration (≤5). SDK: `new MaestroProcesses(sdk as never).getTopExecutionDuration(THIRTY_DAYS_AGO, NOW)` → BARE `[{ packageId, processKey, duration, name }]` (`duration` ms).",
      "defaults": { "title": "Slowest Processes", "description": "Maestro processes ranked by total duration", "icon": "Clock",
        "columnDefs": [ { "key": "name", "label": "Process" }, { "key": "duration", "label": "Total ms", "align": "right", "format": "number" } ] }
    },
    "maestro-process-status-timeline": {
      "aliases": ["process status over time", "process instance status", "process status timeline", "completed vs faulted processes"],
      "template": "multi-line-chart",
      "description": "Maestro process instance status over time. SDK: `new MaestroProcesses(sdk as never).getInstanceStatusTimeline(THIRTY_DAYS_AGO, NOW)` → BARE `[{ startTime, status, count }]` (`status` Completed/Faulted/Cancelled). Module pivots per `startTime`, seeding all 3 series to 0 → `[{ date, Completed, Faulted, Cancelled }]`. xKey: date.",
      "defaults": { "title": "Process Status Over Time", "description": "Completed / Faulted / Cancelled instances", "icon": "GitBranch", "xKey": "date",
        "series": "[{key:\"Completed\",color:\"hsl(var(--chart-3))\"},{key:\"Faulted\",color:\"hsl(var(--chart-5))\"},{key:\"Cancelled\",color:\"hsl(var(--chart-4))\"}]",
        "headlineMode": "latest", "deltaPolarity": "neutral" }
    },
    "top-failing-process-elements": {
      "aliases": ["failing elements", "top failing elements", "error prone activities", "bpmn element failures", "failing activities"],
      "template": "ranked-table",
      "description": "Top failing BPMN elements across Maestro processes (≤10). SDK: `new MaestroProcesses(sdk as never).getTopElementFailedCount(THIRTY_DAYS_AGO, NOW)` → BARE `[{ elementName, elementType, processKey, failedCount }]`.",
      "defaults": { "title": "Top Failing Elements", "description": "BPMN elements ranked by failures", "icon": "TriangleAlert",
        "columnDefs": [ { "key": "elementName", "label": "Element" }, { "key": "elementType", "label": "Type" }, { "key": "failedCount", "label": "Failures", "align": "right", "format": "number" } ] }
    },
```

- [ ] **Step 4: Add the 5 rows** to the T1 catalog table in `tier-resolution.md`:

```markdown
| `top-maestro-processes-by-runs` | Busiest processes | `ranked-table` | `MaestroProcesses.getTopRunCount(start,end)` → BARE `[{name,runCount,...}]` |
| `top-maestro-processes-by-faults` | Top failing processes | `ranked-table` | `MaestroProcesses.getTopFaultedCount(start,end)` → BARE `[{name,faultedCount,...}]` |
| `top-maestro-processes-by-duration` | Slowest processes | `ranked-table` | `MaestroProcesses.getTopExecutionDuration(start,end)` → BARE `[{name,duration,...}]` |
| `maestro-process-status-timeline` | Process status over time | `multi-line-chart` | `MaestroProcesses.getInstanceStatusTimeline(start,end)` → pivot to `[{date,Completed,Faulted,Cancelled}]` |
| `top-failing-process-elements` | Top failing BPMN elements | `ranked-table` | `MaestroProcesses.getTopElementFailedCount(start,end)` → BARE `[{elementName,failedCount,...}]` |
```

- [ ] **Step 5: Run tests.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -8
```
Expected: all pass.

- [ ] **Step 6: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "feat(dashboards): add Maestro process Insights T1 metrics (top/status/elements)"
```

---

### Task 5: Maestro Case Insights — 5 T1 metrics (review item 2b)

**Files:**
- Modify: `capability-registry.json`, `tier-resolution.md`, `resolution.test.mjs`

Mirror of Task 4 on the `Cases` service (subpath `@uipath/uipath-typescript/cases`). Identical method signatures and response shapes; only the service class and subpath differ.

- [ ] **Step 1: Write the failing test.** Add to `resolution.test.mjs`:

```js
test('Maestro case Insights metrics resolve T1', () => {
  for (const [text, expected] of [
    ['busiest cases', 'top-cases-by-runs'],
    ['top failing cases', 'top-cases-by-faults'],
    ['slowest cases', 'top-cases-by-duration'],
    ['case status over time', 'case-status-timeline'],
    ['failing case elements', 'top-failing-case-elements'],
  ]) {
    const r = resolveAlias(text)
    assert.ok(r, `"${text}" did not resolve`)
    assert.equal(r.key, expected, `"${text}" → ${r?.key}, expected ${expected}`)
  }
})

test('case Insights T1 entries generate clean widgets', () => {
  for (const name of ['top-cases-by-runs', 'top-cases-by-faults', 'top-cases-by-duration', 'case-status-timeline', 'top-failing-case-elements']) {
    const entry = registry.t1[name]
    assert.ok(entry, `missing ${name}`)
    const metric = { name, tier: 'T1', title: entry.defaults.title, displayAs: entry.template, ...entry.defaults }
    const content = buildWidgetFile(metric, entry, '30d')
    assert.equal(content.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g), null, `${name} leftover placeholders`)
  }
})
```

- [ ] **Step 2: Run to verify it fails.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | grep -E "case Insights|# fail"
```
Expected: FAIL.

- [ ] **Step 3: Add the 5 T1 entries** to `capability-registry.json` (note `Cases` + `/cases`; `name` is the readable case name):

```json
    "top-cases-by-runs": {
      "aliases": ["busiest cases", "most active cases", "top cases by runs", "most run cases", "top cases"],
      "template": "ranked-table",
      "description": "Top case processes by run count (≤5). SDK: `new Cases(sdk as never).getTopRunCount(THIRTY_DAYS_AGO, NOW)` (positional Dates) → BARE `[{ packageId, processKey, runCount, name }]`. Subpath @uipath/uipath-typescript/cases. Scope: Insights Insights.RealTimeData.",
      "defaults": { "title": "Busiest Cases", "description": "Case processes ranked by run count", "icon": "Activity",
        "columnDefs": [ { "key": "name", "label": "Case" }, { "key": "runCount", "label": "Runs", "align": "right", "format": "number" } ] }
    },
    "top-cases-by-faults": {
      "aliases": ["top failing cases", "most faulted cases", "cases by failure", "worst cases", "faulted cases"],
      "template": "ranked-table",
      "description": "Top case processes by faulted count (≤10). SDK: `new Cases(sdk as never).getTopFaultedCount(THIRTY_DAYS_AGO, NOW)` → BARE `[{ packageId, processKey, faultedCount, name }]`.",
      "defaults": { "title": "Top Failing Cases", "description": "Case processes ranked by faults", "icon": "TriangleAlert",
        "columnDefs": [ { "key": "name", "label": "Case" }, { "key": "faultedCount", "label": "Faults", "align": "right", "format": "number" } ] }
    },
    "top-cases-by-duration": {
      "aliases": ["slowest cases", "longest running cases", "top cases by duration", "cases by duration"],
      "template": "ranked-table",
      "description": "Top case processes by total duration (≤5). SDK: `new Cases(sdk as never).getTopExecutionDuration(THIRTY_DAYS_AGO, NOW)` → BARE `[{ packageId, processKey, duration, name }]` (`duration` ms).",
      "defaults": { "title": "Slowest Cases", "description": "Case processes ranked by total duration", "icon": "Clock",
        "columnDefs": [ { "key": "name", "label": "Case" }, { "key": "duration", "label": "Total ms", "align": "right", "format": "number" } ] }
    },
    "case-status-timeline": {
      "aliases": ["case status over time", "case instance status", "case status timeline", "completed vs faulted cases"],
      "template": "multi-line-chart",
      "description": "Case instance status over time. SDK: `new Cases(sdk as never).getInstanceStatusTimeline(THIRTY_DAYS_AGO, NOW)` → BARE `[{ startTime, status, count }]` (Completed/Faulted/Cancelled). Module pivots per `startTime`, seeding all 3 series to 0 → `[{ date, Completed, Faulted, Cancelled }]`. xKey: date.",
      "defaults": { "title": "Case Status Over Time", "description": "Completed / Faulted / Cancelled case instances", "icon": "GitBranch", "xKey": "date",
        "series": "[{key:\"Completed\",color:\"hsl(var(--chart-3))\"},{key:\"Faulted\",color:\"hsl(var(--chart-5))\"},{key:\"Cancelled\",color:\"hsl(var(--chart-4))\"}]",
        "headlineMode": "latest", "deltaPolarity": "neutral" }
    },
    "top-failing-case-elements": {
      "aliases": ["failing case elements", "top failing case activities", "case bpmn failures"],
      "template": "ranked-table",
      "description": "Top failing BPMN elements across case processes (≤10). SDK: `new Cases(sdk as never).getTopElementFailedCount(THIRTY_DAYS_AGO, NOW)` → BARE `[{ elementName, elementType, processKey, failedCount }]`.",
      "defaults": { "title": "Top Failing Case Elements", "description": "Case BPMN elements ranked by failures", "icon": "TriangleAlert",
        "columnDefs": [ { "key": "elementName", "label": "Element" }, { "key": "elementType", "label": "Type" }, { "key": "failedCount", "label": "Failures", "align": "right", "format": "number" } ] }
    },
```

- [ ] **Step 4: Add the 5 rows** to the T1 catalog table in `tier-resolution.md` (Cases variants, mirroring Task 4 with `Cases.` + `/cases`).

- [ ] **Step 5: Run tests.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -8
```
Expected: all pass.

- [ ] **Step 6: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "feat(dashboards): add Maestro case Insights T1 metrics"
```

---

### Task 6: Element latency stats — T2 parametric metric (review item 2c)

**Files:**
- Modify: `capability-registry.json`, `tier-resolution.md`, `resolution.test.mjs`

`getElementStats(processKey, packageId, start, end, packageVersion)` needs user-supplied identifiers → T2 (the agent bakes them into the module at authoring time, like `jobs-by-state`).

- [ ] **Step 1: Write the failing test.** Add to `resolution.test.mjs`:

```js
test('element-latency-stats resolves T2', () => {
  const r = resolveAlias('element latency stats')
  assert.ok(r, 'did not resolve')
  assert.equal(r.tier, 'T2')
  assert.equal(r.key, 'element-latency-stats')
})
```

- [ ] **Step 2: Run to verify it fails.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | grep -E "element-latency|# fail"
```
Expected: FAIL.

- [ ] **Step 3: Add the T2 entry** to the `"t2"` object in `capability-registry.json`:

```json
    "element-latency-stats": {
      "aliases": ["element latency", "element latency stats", "element duration stats", "activity latency", "element performance", "slow elements", "element percentiles"],
      "description": "Per-BPMN-element execution + duration percentiles for one process/case. SDK: `new MaestroProcesses(sdk as never).getElementStats('<processKey>', '<packageId>', THIRTY_DAYS_AGO, NOW, '<version>')` → BARE `[{ elementId, successCount, failCount, terminatedCount, pausedCount, inProgressCount, minDurationMs, maxDurationMs, avgDurationMs, p50DurationMs, p95DurationMs, p99DurationMs }]`. Identifiers baked in from params at authoring time. For case management use `new Cases(...)` (same signature). Scope: Insights Insights.RealTimeData.",
      "defaults": {
        "title": "Element Latency",
        "description": "Per-element duration percentiles",
        "icon": "Gauge",
        "columns": "[{key:\"elementId\",label:\"Element\"},{key:\"successCount\",label:\"OK\",align:\"right\" as const},{key:\"failCount\",label:\"Fail\",align:\"right\" as const},{key:\"avgDurationMs\",label:\"Avg ms\",align:\"right\" as const},{key:\"p95DurationMs\",label:\"P95 ms\",align:\"right\" as const}]",
        "deltaDir": "neutral",
        "deltaText": "",
        "dataSelector": "(data as any) ?? []"
      }
    },
```

- [ ] **Step 4: Add a T2 row** to the T2 table in `tier-resolution.md`:

```markdown
| `element-latency-stats` | Per-element duration percentiles | `{ processKey, packageId, version }` |
```

- [ ] **Step 5: Run tests.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -8
```
Expected: all pass.

- [ ] **Step 6: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "feat(dashboards): add element-latency-stats T2 metric"
```

---

### Task 7: Scope list everywhere — verify, document, guard (user follow-up)

**Files:**
- Modify: `references/oauth-scopes.md`, `references/dashboards/CAPABILITY.md`, `references/dashboards/plugins/build/impl.md`, `resolution.test.mjs`

Per the authoritative SDK doc (`C:\Work\uipath-typescript\docs\oauth-scopes.md:77-124`): the Top/timeline/element methods need `Insights.RealTimeData Insights OR.Folders.Read` — all already granted by `DASHBOARD_SCOPES`. The **SLA methods additionally require `PIMS`**, which is **NOT** in `DASHBOARD_SCOPES` (`build-dashboard.mjs:343`). So `PIMS` must be added to the scope constant, the external-app `--user-scope` (full + minimal), and `oauth-scopes.md`. (This also repairs the pre-existing `cases-running-above` T2, which uses `Cases.getAll` → `PIMS` and is currently broken under the default scopes.) The scaffold `.env` (`VITE_UIPATH_SCOPE`) is written from the constant, so it updates automatically.

- [ ] **Step 1: Write the guard test.** Add to `resolution.test.mjs` (top, near the other `readFileSync` setup):

```js
import { readFileSync as _rf } from 'node:fs'
test('Insights RTM + PIMS scopes are present in all scope lists', () => {
  const build = _rf(new URL('../build-dashboard.mjs', import.meta.url), 'utf8')
  const scopesLine = build.match(/DASHBOARD_SCOPES\s*=\s*'([^']*)'/)?.[1] ?? ''
  for (const s of ['Insights', 'Insights.RealTimeData', 'OR.Folders', 'PIMS']) {
    assert.ok(scopesLine.split(/\s+/).includes(s), `DASHBOARD_SCOPES missing ${s}`)
  }
  const impl = _rf(new URL('../../../references/dashboards/plugins/build/impl.md', import.meta.url), 'utf8')
  assert.ok(/--user-scope "[^"]*Insights,Insights\.RealTimeData[^"]*PIMS/.test(impl)
    || /--user-scope "[^"]*PIMS[^"]*Insights,Insights\.RealTimeData/.test(impl), 'create command missing Insights RTM + PIMS')
})
```

> Adjust the relative paths to match the test file's location (`assets/scripts/tests/resolution.test.mjs` → `../build-dashboard.mjs`, `../../../references/...`). Verify with a one-off `node -e` before relying on it.

- [ ] **Step 2: Run to verify it FAILS** (PIMS is currently absent):

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | grep -E "Insights RTM \+ PIMS|# fail"
```
Expected: FAIL (`DASHBOARD_SCOPES missing PIMS`).

- [ ] **Step 3: Add `PIMS` to `DASHBOARD_SCOPES`** in `build-dashboard.mjs:343`:

```js
const DASHBOARD_SCOPES = 'OR.Assets OR.Jobs OR.Folders OR.Buckets OR.Execution OR.Tasks OR.Queues OR.Users Insights Insights.RealTimeData PIMS'
```

- [ ] **Step 4: Add `PIMS` to both `--user-scope` commands** in `build/impl.md` (full + minimal):

```
... ,Insights,Insights.RealTimeData,PIMS"   # full
... ,OR.Queues,OR.Users,PIMS"               # minimal (PIMS so Maestro getAll + SLA work even when Insights is rejected)
```

- [ ] **Step 5: Add a "Maestro Insights — RTM" section** to `oauth-scopes.md` (after the Governance Insights section), with the EXACT scopes from the SDK doc:

```markdown
## Maestro Insights — RTM (SDK ≥ 1.4.x)

These use the Insights RTM host (`INSIGHTS_RTM_BASE`). The SLA methods also touch PIMS-backed case data and require `PIMS` on top of the Insights scopes.

| Method | Required Scope |
|--------|----------------|
| `Cases` / `MaestroProcesses` `.getTopRunCount()` / `getTopFaultedCount()` / `getTopExecutionDuration()` / `getTopElementFailedCount()` / `getInstanceStatusTimeline()` / `getElementStats()` | `Insights` · `Insights.RealTimeData` · `OR.Folders.Read` |
| `CaseInstances.getSlaSummary()` / `getStagesSlaSummary()` | `Insights` · `Insights.RealTimeData` · `OR.Folders.Read` · **`PIMS`** |

> The Insights agent/trace/memory/governance methods also require `OR.Folders.Read` (covered by the granted `OR.Folders`). Update the corresponding sections above to list `OR.Folders.Read` alongside `Insights` / `Insights.RealTimeData` for accuracy.
```

- [ ] **Step 6: Update the Insights bundle row** at the bottom of `oauth-scopes.md`:

```markdown
| Insights RTM (Agents, Agent Traces, Agent Memory, Governance, Maestro Insights) | `Insights Insights.RealTimeData OR.Folders.Read` |
| Maestro SLA (CaseInstances SLA summary) | `Insights Insights.RealTimeData OR.Folders.Read PIMS` |
```

- [ ] **Step 7: Extend the maestro conditional-load row** in `CAPABILITY.md`:

```markdown
| cases, process instances, Maestro, SLA, top/slowest/failing processes or cases, element stats | `references/sdk/maestro.md` *(from skill root)* |
```

- [ ] **Step 8: Add the minimal-fallback caveat** in `build/impl.md` after the minimal `--user-scope` command:

```markdown
> **Insights metrics need the Insights scopes.** The minimal fallback drops `Insights,Insights.RealTimeData` — every agent **and** Maestro Insights/SLA metric (agent-*, trace-*, case-sla-*, top-*, *-status-timeline, element-latency-stats) returns 403 under it. `PIMS` is retained in the minimal set so plain Maestro `getAll` metrics (e.g. `cases-running-above`) still work. Use the minimal set only when the environment rejects the Insights scopes; the Insights-based metrics will be unavailable.
```

- [ ] **Step 9: Run full tests.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -8
```
Expected: all pass (incl. the renamed "Insights RTM + PIMS scopes" guard).

- [ ] **Step 10: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "fix(dashboards): grant + document PIMS for Maestro SLA; OR.Folders.Read for Insights"
```

---

### Task 8: Final validation

**Files:**
- Test: `resolution.test.mjs` (read-method allowlist + full run)

- [ ] **Step 1: Add the new read methods to the allowlist** in `tier-resolution.md` (the "Read methods ONLY. Allowed:" line) — append: `getSlaSummary`, `getStagesSlaSummary`, `getTopRunCount`, `getTopFaultedCount`, `getTopExecutionDuration`, `getTopElementFailedCount`, `getInstanceStatusTimeline`, `getElementStats`.

- [ ] **Step 2: Add the Maestro Insights calling-convention note** to `tier-resolution.md` (the "Calling conventions" list):

```markdown
- `Cases` / `MaestroProcesses.getTopRunCount / getTopFaultedCount / getTopExecutionDuration / getTopElementFailedCount / getInstanceStatusTimeline(start, end, options?)` — positional `Date`s, **bare array**; `getElementStats(processKey, packageId, start, end, version)` all positional, bare array (see `sdk/maestro.md`)
- `CaseInstances.getSlaSummary({ startTimeUtc?, endTimeUtc?, ... })` — options object, rows on `.items`; `getStagesSlaSummary(options?)` — bare array
```

- [ ] **Step 3: Run the full suite.**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs 2>&1 | tail -10
```
Expected: `# fail 0`, all new tests counted.

- [ ] **Step 4: Run the widget-generation smoke for ALL 14 new entries** (catches template/series/placeholder issues against the real registry):

```bash
cd skills/uipath-coded-apps/assets/scripts && node --input-type=module -e '
import { buildWidgetFile } from "./build-dashboard.mjs"
import { readFileSync } from "node:fs"
const reg = JSON.parse(readFileSync("./capability-registry.json","utf8"))
const t1 = ["case-sla-status","case-sla-breaches","case-stage-sla","top-maestro-processes-by-runs","top-maestro-processes-by-faults","top-maestro-processes-by-duration","maestro-process-status-timeline","top-failing-process-elements","top-cases-by-runs","top-cases-by-faults","top-cases-by-duration","case-status-timeline","top-failing-case-elements"]
let ok = true
for (const name of t1) {
  const e = reg.t1[name]; if (!e) { console.log("MISSING", name); ok=false; continue }
  const m = { name, tier:"T1", title:e.defaults.title, displayAs:e.template, ...e.defaults }
  let c; try { c = buildWidgetFile(m, e, "30d") } catch(err){ console.log("THROW",name,err.message); ok=false; continue }
  const lo = c.match(/<[A-Z][A-Z_]*>|<<[A-Z_]+>>/g); if (lo){console.log("LEFTOVER",name,lo);ok=false}
  if (!c.includes(`import { fetchData } from \x27@/metrics/${name}\x27`)){console.log("NO IMPORT",name);ok=false}
}
const t2 = reg.t2["element-latency-stats"]; if(!t2){console.log("MISSING element-latency-stats");ok=false}
console.log(ok ? "ALL GOOD" : "FAILURES ABOVE")
'
```
Expected: `ALL GOOD`.

- [ ] **Step 5: Verify `capability-registry.json` is valid JSON** (the collision + structure tests already load it, but confirm explicitly):

```bash
node -e "JSON.parse(require('fs').readFileSync('skills/uipath-coded-apps/assets/scripts/capability-registry.json','utf8')); console.log('valid json')"
```
Expected: `valid json`.

- [ ] **Step 6: Commit.**

```bash
git -C C:/Work/skills add -A && git -C C:/Work/skills commit -m "chore(dashboards): read-method allowlist + calling conventions for Maestro Insights"
```

---

## Notes on intentional design decisions

1. **Modules compare status as strings, not enums.** `SlaSummaryStatus` / `InstanceFinalStatus` are real exports, but importing them invites TS2367 ("no overlap") narrowing errors and an unverified-export risk. The literal values (`'At Risk'`, `'Overdue'`, `'Faulted'`, …) are source-verified and stable. Keeps modules enum-free and seamless.
2. **Cases and Processes are separate catalog entries**, not one parametric metric — the registry has no domain switch, and a user asking for "cases" vs "processes" should resolve unambiguously. The 10 entries are near-identical but cheap; the cost is catalog size, the benefit is zero-ambiguity resolution.
3. **`element-latency-stats` is T2, not T1** — it requires `processKey`+`packageId`+`version`, which only the user can supply. Modeled exactly like `jobs-by-state` (identifiers baked into the module at authoring time).
4. **Scope change IS required — add `PIMS`.** Verified against the SDK's authoritative `docs/oauth-scopes.md`: Top/timeline/element methods need `Insights Insights.RealTimeData OR.Folders.Read` (all granted), but the SLA methods additionally need **`PIMS`**, which is absent from `DASHBOARD_SCOPES`. Task 7 adds `PIMS` to the constant + both `--user-scope` commands and documents `OR.Folders.Read`. The guard test fails until `PIMS` is present. (This also fixes the pre-existing `cases-running-above` PIMS gap.)
5. **`getInstanceStatusTimeline.startTime` is a locale string** (e.g. `"5/8/2026 12:00:00 AM"`), not ISO — the multi-line chart's `tickFormatter` (`new Date(String(v))`) parses it. The module passes it through as `date`; no reformatting needed.

## Self-review (run against the review's items 1–4)

- **Item 1 (SLA refuse → metrics):** Task 3 removes `sla.*breach` and adds `case-sla-status`/`case-sla-breaches`/`case-stage-sla`. ✓
- **Item 2 (Maestro Insights family T1):** Tasks 4–6 add 10 T1 (process+case top/status/elements) + `element-latency-stats` T2. ✓
- **Item 3 (refresh `maestro.md`):** Task 1, with exact DTOs + module patterns. ✓
- **Item 4 (narrow error-text refuse):** Task 2. ✓
- **Scope follow-up:** Task 7 adds `PIMS` to `DASHBOARD_SCOPES` + both `--user-scope` commands (SLA methods require it per the SDK scope doc), documents `OR.Folders.Read` + `PIMS` in oauth-scopes.md, updates CAPABILITY.md, adds the create-command/scaffold guard test, and the minimal-fallback caveat. ✓
- **Type consistency:** every registry `description` and module pattern uses the source-verified field names (`runCount`/`faultedCount`/`duration`/`failedCount`/`elementName`/`slaStatus`/`slaDueTime`/`avgDurationMs`/`p95DurationMs`) and call conventions (positional Dates; `getSlaSummary` options object + `.items`; all others bare arrays). No placeholder code.
- **Alias collisions:** new aliases avoid every remaining hard-refuse pattern and the existing T1 alias `process failures` (job-failures) / `maestro cases` (cases-running-above); the `hardRefuse does not collide` test + per-task resolution tests enforce this mechanically.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-18-maestro-insights-sla-coverage.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session with checkpoints for review.

Which approach?