# Dashboard Skill Robustness + Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Eliminate the four defect classes from the Agent-Ops postmortem (KPI delta, table row-click drill-down, silent empty tables, non-filterable OData fields) and cut build wall-clock — without regressing existing dashboards.

**Architecture:** The skill generates a React app from a metric catalog + scaffold. Fixes split across three surfaces: (a) **scaffold** (`templates/dashboard/scaffold/`, shipped via the fixture zip — edits require re-pack), (b) **live build assets** (`templates/dashboard/widgets/*`, `assets/scripts/build-dashboard.mjs`, read at build time — no re-pack), (c) **docs/registry** (`references/`, `capability-registry.json`). Reliability comes from making the *promise surface* (plan vocabulary) equal the *build surface* (what the scaffold can emit), from **runtime auto-detection** (tables detect their own columns), and from keeping **service-specific knowledge in the SDK reference docs** (not hardcoded in the generic engine). Performance comes primarily from **fewer fix rounds** (one-shot correctness) and **incremental tsc**.

**Tech Stack:** Node `node:test` (`resolution.test.mjs`), TypeScript scaffold (React + Vite + recharts), `pack-scaffold.mjs` fixture archive.

---

## Verified ground truth (all postmortem claims confirmed against source)

| Defect | Verified fact | Source |
|--------|---------------|--------|
| 1 KPI delta | `t3-shell.tsx.template` renders only headline+label; `DeltaBadge`/`delta()` wired into chart templates only; plan vocab promises a badge | `widgets/t3-shell.tsx.template:55-66`; `impl.md:76`; `scaffold/src/lib/widget.ts:34`; `scaffold/src/lib/time.ts` (no `SIXTY_DAYS_AGO`) |
| 2 row-click | detail views chart-only (`widgetLayoutGroup`); `RecordsTable` has no `onRowClick`; `MetricFn=(sdk,getToken)=>Promise<any[]>` (no key); App.tsx has GENERATED markers | `build-dashboard.mjs:670-674,1190-1195`; `RecordsTable.tsx:12-17`; `metric-contract.ts:8`; `App.tsx:11-12,50-51` |
| 3 empty table | 3 column fields (`columns`/`columnDefs`/`detailColumns`); silent fallback to `[{name},{value}]`; no validation a table has real columns | `build-dashboard.mjs:925,820`; `validateIntent` has no table-column check |
| 4 OData filter | `releaseName→processName` is read-only mapped (not filterable); orchestrator.md documents `ProcessType` filter but has NO agent-name→jobs→trace recipe; no warning about filterability | `jobs.constants.ts:13`; `orchestrator.md:257-264`; Job has `traceId` (`jobs.types.ts:146`) |
| Perf | Long poles: `npm ci` 5-10 min (first build) + full-app `tsc --noEmit` 2-8 min, **× 3 fix rounds**. No vite build, no per-widget tsc. node_modules cached by sentinel for rebuilds | `build-dashboard.mjs:388-407,1112-1125,1215-1225` |
| Smoke | Pipeline ends at `tsc --noEmit` + state write; dev server started separately. No runtime/headless check | `build-dashboard.mjs:1215-1255` |

**Pack boundary (regression-critical):** fixture zip = `templates/dashboard/scaffold/` only (`pack-scaffold.mjs:17,45`). Edits to scaffold files require `node pack-scaffold.mjs --version <next>` + the drift-guard test. Widget templates + `build-dashboard.mjs` are read live (no re-pack).

**Reframe of "runtime smoke":** A headless browser smoke would add minutes + a heavy dependency — directly against the perf goal. Defect 3 (empty table) is fixed structurally by runtime column auto-detection (Task 3). Defect 4 (non-filterable field) is addressed by documentation in the correct layer — the Jobs reference — plus the Phase 3.5 cross-check (Task 4); service-specific filter rules are NOT hardcoded into the generic engine. A true runtime probe is an **optional, opt-in** stretch (Task 9), never default.

---

## File structure

| File | Surface | Change |
|------|---------|--------|
| `scaffold/src/lib/time.ts` | scaffold (re-pack) | add `SIXTY_DAYS_AGO` + prior-window helper |
| `scaffold/src/lib/widget.ts` | scaffold (re-pack) | add `kpiDelta(value, previous, polarity)` |
| `scaffold/src/dashboard/chrome/RecordsTable.tsx` | scaffold (re-pack) | add `onRowClick?`, `defaultSortAsc?` |
| `scaffold/src/lib/metric-contract.ts` | scaffold (re-pack) | add `MetricDetailByKeyFn` type |
| `scaffold/src/App.tsx` | scaffold (re-pack) | (markers already support injection — no structural change) |
| `scaffold/tsconfig*.json` | scaffold (re-pack) | `incremental: true` + `tsBuildInfoFile`; confirm `skipLibCheck` |
| `widgets/t3-shell.tsx.template` | live | KPI delta branch; table `onRowClick`/`rowLink` wiring |
| `assets/scripts/build-dashboard.mjs` | live | KPI delta subs; table-column validation; keyed-route gen; OData-filter lint; incremental tsc; `kpiDelta` plumbing |
| `capability-registry.json` | data | KPI entries return `{value,previous}`; agent-spans drill-down recipe |
| `references/sdk/orchestrator.md` | docs | filterable-vs-read-only Job fields; agent→jobs→trace recipe |
| `references/dashboards/plugins/build/impl.md` | docs | Phase 2 capability cross-check; KPI/row-link vocabulary truthful |
| `references/dashboards/primitives/{detail-views,tier-resolution}.md` | docs | one column field for tables; row-link drill-down pattern |
| `assets/scripts/tests/resolution.test.mjs` | tests | validation, substitution, route-gen, lint, column-key checks |
| `assets/fixtures/governance-dashboard-starter-kit.{zip,manifest.json}` | artifact | re-pack after all scaffold edits |

---

### Task 1: KPI cards become delta-capable (Defect 1)

Make the *capability* real so the plan vocabulary stops lying. Backward-compatible: a KPI with no `previous` still renders value+label.

**Files:** `scaffold/src/lib/time.ts`, `scaffold/src/lib/widget.ts`, `widgets/t3-shell.tsx.template`, `build-dashboard.mjs`, `capability-registry.json`, `impl.md`, `tier-resolution.md`, `resolution.test.mjs`

- [ ] **Step 1 — time.ts:** add `export const SIXTY_DAYS_AGO = new Date(Date.now() - 5_184_000_000)` (and keep existing). This gives KPIs a prior 30-day window (60→30 days ago).
- [ ] **Step 2 — widget.ts:** add
  ```ts
  export function kpiDelta(value: number, previous: number, polarity: DeltaPolarity = 'neutral'): { text: string; direction: DeltaDirection } {
    if (!isFinite(value) || !isFinite(previous) || previous === 0) return { text: '', direction: 'neutral' }
    const pct = Math.round(((value - previous) / Math.abs(previous)) * 100)
    const up = pct > 0
    const direction = pct === 0 ? 'neutral' : polarity === 'up-bad' ? (up ? 'bad' : 'good') : polarity === 'up-good' ? (up ? 'good' : 'bad') : 'neutral'
    return { text: `${up ? '+' : ''}${pct}%`, direction }
  }
  ```
  (Reuse existing `DeltaPolarity`/`DeltaDirection` types from this file.)
- [ ] **Step 3 — t3-shell.tsx.template KPI branch:** after computing `headline`, read optional `previous` + `<<DELTA_POLARITY>>` and render a `DeltaBadge` when present:
  ```tsx
  const prevRaw = (data[0] as Record<string, unknown>)?.['<<PREVIOUS_FIELD>>']
  const cur = Number(VALUE_FIELD ? (data[0] as Record<string, unknown>)?.[VALUE_FIELD] : data.length)
  const d = (prevRaw !== undefined && prevRaw !== null) ? kpiDelta(cur, Number(prevRaw), '<<DELTA_POLARITY>>' as DeltaPolarity) : null
  // ...render: {d && d.text && <DeltaBadge direction={d.direction} text={d.text} />}
  ```
  Add the `DeltaBadge` + `kpiDelta` imports to the template header. `<<PREVIOUS_FIELD>>` defaults to `previous`.
- [ ] **Step 4 — build-dashboard.mjs:** in the KPI/table shell path (~line 921-942) add substitutions `PREVIOUS_FIELD` (`metric.previousField ?? 'previous'`) and `DELTA_POLARITY` (`metric.deltaPolarity ?? defaults.deltaPolarity ?? 'neutral'`).
- [ ] **Step 5 — registry:** update `active-agents-kpi` (and document the pattern) so the metric returns `[{ value, previous }]` — current window count + prior-window count via `SIXTY_DAYS_AGO`/`THIRTY_DAYS_AGO`. Add `valueField: "value"` and a `deltaPolarity` default. Keep it OPTIONAL for other KPIs (perf: a delta = 2 SDK calls).
- [ ] **Step 6 — impl.md Phase 2 (line 76):** keep the change-badge vocabulary but make it conditional + truthful: *"as a single headline number — add a vs-previous-period change badge ONLY when the metric module returns `{ value, previous }` (two windows). Plain KPIs return `{ value }` and render no badge."*
- [ ] **Step 7 — tests:** add a `buildWidgetFile` test that a KPI metric with `previousField`/`deltaPolarity` emits `DeltaBadge` + `kpiDelta(` and no leftover placeholders; and that a plain KPI (no previous) still generates and does NOT hard-require a badge. Run `node --test`.

---

### Task 2: First-class row-click → parameterized detail drill-down (Defect 2)

The biggest gap (~60% of rework). Add a keyed drill-down pattern: a table row links to `/<widget>/:key`, a generated view reads the key and calls a keyed fetch.

**Files:** `RecordsTable.tsx`, `metric-contract.ts`, `build-dashboard.mjs` (route + view gen), `t3-shell.tsx.template`, `tier-resolution.md`, `detail-views.md`, `resolution.test.mjs`

- [ ] **Step 1 — RecordsTable.tsx:** add optional props `onRowClick?: (row: T) => void` and `defaultSortAsc?: boolean`; when `onRowClick` is set, add `cursor-pointer` + `onClick` to `<tr>` and an `aria-role`. No behavior change when absent (backward-compatible).
- [ ] **Step 2 — metric-contract.ts:** add `export type MetricDetailByKeyFn = (sdk: any, key: string, getToken: () => Promise<string>) => Promise<any[]>` (keep `MetricFn` unchanged).
- [ ] **Step 3 — intent schema:** a `data-table`/`ranked-table` metric may declare `rowLink: { key: string }` (the row field used as the route param, e.g. `agentName`). Document it; validate in `validateIntent` (key must be a non-empty string).
- [ ] **Step 4 — build-dashboard.mjs view+route gen:** when a table metric has `rowLink`, generate (a) a keyed detail view `views/<Component>DetailView.tsx` that reads `useParams()` and calls the module's `fetchDetailByKey`, rendering `RecordsTable` (autoColumns or `detailColumns`); (b) a `/<widgetlower>/:key` route inside the GENERATED markers; (c) wire the table widget's `onRowClick` to `navigate(\`/<widget>/\${encodeURIComponent(row[key])}\`)`. Reuse the existing marker-injection regex (App.tsx:696-708) — keyed routes go INSIDE markers (regenerated), matching the established pattern; the postmortem's hand-written `/agent/:agentId` outside markers becomes unnecessary.
- [ ] **Step 5 — t3-shell.tsx.template:** add an `<<ON_ROW_CLICK>>` slot in the table branch (empty string when no rowLink; `useNavigate` + handler when present).
- [ ] **Step 6 — detail-views.md / tier-resolution.md:** document the row-link drill-down: tables with `rowLink` get a keyed detail view + route; the module exports `fetchDetailByKey(sdk, key, getToken)`. Update the "tables link nowhere" rule to "tables link nowhere unless `rowLink` is set."
- [ ] **Step 7 — tests:** `buildWidgetFile`/`generateViewFile` tests — a table metric with `rowLink:{key:'agentName'}` emits an `onRowClick` navigate, a `:key` route, and a detail view importing `fetchDetailByKey`; a table WITHOUT `rowLink` emits none of these (no regression). Run `node --test`.

---

### Task 3: Auto-detect table columns at runtime (Defect 3)

The robust, generic fix (no fail-loud error, no hardcoding): a table widget that resolves to no explicit columns **auto-detects them from the actual row data** — the same `autoColumns` the chart detail view already uses — instead of a static `name/value` placeholder that renders empty `—` cells. Even the postmortem's mistake (`detailColumns` on a table) now self-heals: the widget shows the real row keys.

**Files:** `widgets/t3-shell.tsx.template`, `build-dashboard.mjs`, `tier-resolution.md`, `detail-views.md`, `resolution.test.mjs`

- [ ] **Step 1 — build default:** change the KPI/table `columns` default from the static `name/value` literal to `'[]'` so "no explicit columns" is detectable.
- [ ] **Step 2 — t3-shell template:** add an `autoColumns(rows)` helper and render the table with `const cols = COLUMNS.length ? COLUMNS : autoColumns(data)` — explicit columns win; otherwise detect real keys.
- [ ] **Step 3 — docs:** in `tier-resolution.md` + `detail-views.md`, state the rule: table display uses `columns`/`columnDefs`; `detailColumns` is only for chart drill-down views; omitting columns auto-detects (no empty placeholder). Update Phase 3.5 cross-check item to compare table column keys against the documented return shape (general teaching, not engine-hardcoded).
- [ ] **Step 4 — tests:** `buildWidgetFile` for a table with no columns emits `COLUMNS = []` + `COLUMNS.length ? COLUMNS : autoColumns(data)` and NO static `name/value` placeholder; `validateIntent` does NOT reject a no-columns table; explicit columns are honored; T1 tables unaffected. Run `node --test`.

---

### Task 4: Document Job query constraints + agent→trace recipe (Defect 4)

**Files:** `references/sdk/orchestrator.md`, `capability-registry.json`, `references/sdk/traces.md`

- [ ] **Step 1 — orchestrator.md filterability note:** add a short subsection: *"Filterable vs read-only Job fields. Mapped response fields (`processName`←`releaseName`, `createdTime`←`creationTime`, `folderId`←`organizationUnitId`, `packageType`←`ProcessType`) are READ-ONLY — they exist in the response but are NOT valid in an OData `$filter` and throw `Invalid OData query options`. Filter only on raw API fields: `ProcessType`, `State`, `CreationTime`, `StartTime`. To find a specific agent's jobs, filter `ProcessType eq 'Agent'` and match `processName` CLIENT-SIDE."* Fix the misleading line 264 ("cross-check filter against the example response") — clarify that appearing in the response does **not** make a field filterable.
- [ ] **Step 2 — orchestrator.md recipe:** add the canonical end-to-end snippet:
  ```ts
  // Jobs for a named agent → most-recent trace's spans
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const jobs = (await new Jobs(sdk as never).getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' }))?.items ?? []
  const job = jobs.find(j => j.processName === agentName)   // client-side match (processName is read-only)
  if (!job?.traceId) return []
  return await new AgentTraces(sdk as never).getSpansByTraceId(job.traceId)
  ```
- [ ] **Step 3 — registry recipe:** wire the snippet as a `fetchDetailByKey(sdk, agentName)` example — the keyed detail for Task 2.
- [ ] **Step 4 — traces.md:** add a one-line pointer to the orchestrator recipe for the job→trace bridge (Job carries `traceId`).
- [ ] No test (doc-only) — verified by Phase 3.5 cross-check and the self-test build.

---

### Task 5: (removed) — keep service knowledge in the docs, not the engine

The earlier draft proposed a static OData-filter lint with a hardcoded denylist of Job field names in `build-dashboard.mjs`. **Rejected:** service-specific facts (which Job fields are filterable) must NOT be baked into the generic build engine — that band-aids one service's quirk into a generic skill. Defect 4 is instead addressed entirely by **documentation + the existing static cross-check**: the `orchestrator.md` "Filterable vs read-only Job fields" table (Task 4, the correct layer — the Jobs reference) and the Phase 3.5 item "appearing in the response does NOT make a field filterable" (Task 3, general for any service). A deterministic guard, if ever wanted, is the optional runtime probe (Task 9) — which catches *any* failing query generically, not a hardcoded field list.

---

### Task 6: Performance — incremental tsc + round reduction

The 15 min = `npm ci` (5-10) + full-app `tsc` (2-8) **× 3 fix rounds**. Tasks 1-5 remove the rounds (the dominant lever). This task attacks the per-round tsc cost.

**Files:** `scaffold/tsconfig.json` (+ `tsconfig.metrics.json`), `build-dashboard.mjs`, `scaffold/.gitignore`, `resolution.test.mjs`

- [ ] **Step 1 — incremental tsc:** in the scaffold `tsconfig.json` set `"incremental": true` and `"tsBuildInfoFile": "node_modules/.cache/dash.tsbuildinfo"`; confirm `"skipLibCheck": true` (add if missing — large SDK type graph). Same for `tsconfig.metrics.json` (separate buildinfo). This makes Stage B reruns (CHANGE ops + fix rounds) incremental.
- [ ] **Step 2 — build-dashboard.mjs:** keep `tsc --noEmit` but ensure it does NOT pass a flag that disables incremental; verify the buildinfo path is under `node_modules` (survives rebuilds, ignored by git).
- [ ] **Step 3 — prewarm timing:** confirm/strengthen that `runPrewarm()` is kicked off at plan-presentation time (impl.md) so `npm ci` overlaps user approval; document it explicitly in impl.md.
- [ ] **Step 4 — measure:** add a self-test note: build once (cold), CHANGE one widget, rebuild — assert the second tsc is materially faster (manual/observational; not a unit test).
- [ ] **Step 5 — guard:** add a test asserting the scaffold tsconfig has `incremental` + `skipLibCheck` true (parse the file) so it can't silently regress.

---

### Task 7: Planner cross-checks scaffold capability, not just SDK feasibility

**Files:** `references/dashboards/plugins/build/impl.md`

- [ ] **Step 1 — Phase 2 rule:** add a planning rule: *"Before promising a feature in the plan, confirm the scaffold can render it. KPI change badge → only if the metric returns `{value, previous}`. Table row drill-down → only via `rowLink`. If the prompt needs a capability the scaffold lacks, say so in the plan ('needs a template extension') rather than silently working around it during the build."* Reference the now-truthful KPI + rowLink capabilities from Tasks 1-2.
- [ ] **Step 2:** ensure the widget-vocabulary list (impl.md) matches exactly the set the build can emit (no orphan promises). Doc-only; no test.

---

### Task 8: Re-pack scaffold + drift guard + full validation (regression gate)

Run AFTER all scaffold edits (Tasks 1,2,6). Single re-pack.

**Files:** `assets/fixtures/governance-dashboard-starter-kit.{zip,manifest.json}`, `resolution.test.mjs`

- [ ] **Step 1 — scaffold typechecks standalone:** `cd templates/dashboard/scaffold && npx tsc --noEmit` — the edited scaffold (RecordsTable, widget.ts, time.ts, metric-contract.ts) must compile clean before packing.
- [ ] **Step 2 — re-pack:** `node assets/scripts/pack-scaffold.mjs --version <next>` (bump `SCAFFOLD_VERSION`). Confirm zip + manifest updated, `.gitattributes` keeps zip binary.
- [ ] **Step 3 — drift guard:** run the existing drift test (`contentHash(scaffold) === manifest.sha256`) — must pass. Run full `node --test`.
- [ ] **Step 4 — self-test real build:** in a temp dir, run a real build of a dashboard exercising every new path: a delta KPI (`{value,previous}`), a `rowLink` table with `fetchDetailByKey`, a chart, and an agent→trace drill-down. Assert `TSC_PASS`, routes generated, no leftover placeholders, lint clean. Recreate + clean the temp dir.
- [ ] **Step 5 — widget-gen smoke:** run the registry-wide `buildWidgetFile` smoke (all entries) — no leftover placeholders, correct imports. Confirm no regression to the 106 existing tests.

---

### Task 9 (OPTIONAL / stretch): lightweight runtime data-probe

Only if a token is available; NOT default (preserves perf). NO headless browser.

- [ ] Investigate whether the prior "SDK data probe" infra exists on this branch; if so, extend it. Otherwise: an opt-in Node script that, given a dev token, calls each metric module's `fetchData` and reports throws (catches Defect 4 live) + empty results (flags possible Defect-3-style mismatches). Surface findings to the user; never block the build. Document as opt-in in impl.md.

---

## Regression safeguards (apply throughout)

1. **Every scaffold edit is backward-compatible** — new props/fields optional; absent → current behavior. No existing dashboard regenerates differently unless its intent opts in.
2. **Re-pack is mandatory** after scaffold edits (Task 8) — the #1 trap; the drift-guard test enforces it.
3. **The 106 existing tests must stay green**; new tests are additive.
4. **Widget-gen smoke + self-test real build** are the integration gate (React render isn't unit-tested; tsc + real build cover it).
5. **No new heavy dependency** (no playwright/puppeteer in the default path) — protects the perf goal.

## Self-review vs postmortem

- Defect 1 → Task 1 (capability real + vocab truthful). ✓
- Defect 2 → Task 2 (rowLink + keyed fetch + route). ✓
- Defect 3 → Task 3 (runtime column auto-detection — no empty tables, no hardcoding). ✓
- Defect 4 → Task 4 (docs + recipe) + Task 5 (static filter lint). ✓
- "tsc==done" / no smoke → Task 3 fixes the empty-table class structurally; Defect 4 via docs (Task 4) + Phase 3.5; Task 9 (optional live probe) for deterministic runtime coverage. ✓
- Plan-vocab vs capability → Task 7. ✓
- 15-min build → Task 6 (incremental tsc) + fewer rounds from Tasks 1-5 (dominant lever). ✓

## Priority

1. Task 4 (docs, cheap, unblocks recipe) → 2. Task 1 (KPI delta, guaranteed mismatch) → 3. Task 2 (row-click, biggest rework) → 4. Task 3 (column auto-detect) → 5. Task 6 (perf) → 6. Task 7 (planner) → 7. Task 8 (re-pack + validate). Task 5 removed; Task 9 optional.

---

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-06-18-dashboard-robustness-perf.md`. Two options:
1. **Subagent-Driven (recommended)** — fresh subagent per task, review between, two-stage review.
2. **Inline** — execute in this session with checkpoints.

Which approach?
