# Agent Governance Traces (interim, trace-derived)

> **INTERIM capability.** There is **no OOB SDK/Insights aggregate** for runtime-governance results yet.
> We derive them by parsing the `governance.*` spans the runtime-governance feature emits into agent
> traces. Bounded + rate-limit-safe by design. When an Insights API ships, only the metric modules change
> — the typed lib, registry entries, widgets, and the per-agent drill-down stay.
>
> **HARD LIMIT — last 15 agent runs.** Because this is trace-derived (one `Traces.getById` per run), every
> runtime-compliance metric scans **only the last `MAX_RUNS = 15` agent runs** (actual job runs, newest
> first, no per-agent dedup by default). This is a hard cap, not a default:
> 1. **Default data source = actual job runs** (`Jobs` → `Traces.getById`), NOT the Insights `Agents.getAll`
>    aggregate. Repeat runs from the same agent stay visible.
> 2. **Every runtime-compliance widget must state its window in the UI** — the subtitle reads
>    `Last 15 agent runs` (use the `WINDOW_LABEL` phrase below) so the user knows exactly what slice of data
>    they are looking at. Never render a runtime-compliance widget without this label.
> 3. **If the prompt asks for MORE than the cap** — a larger window ("last 90 days", "this quarter"), a higher
>    run count ("last 100 runs", "all runs"), or tenant-wide totals — **do NOT build that widget.** Tell the
>    user plainly: runtime compliance is an interim trace-derived view bounded to the last 15 agent runs, so
>    that range isn't possible right now. Build the rest of the dashboard; skip only the over-cap widget. This
>    is enforced by the `hardRefuse` registry entry and the gate in `primitives/tier-resolution.md`.
>
> **Only build these when the prompt EXPLICITLY signals runtime compliance, a standard/pack/ISO clause, or
> a rule violation** — see `primitives/tier-resolution.md § Governance violations (gated)`. Generic
> "governance / policy / denials / enforcement" must route to the Insights-API metrics `policy-denials` /
> `governance-verdicts` (`sdk/governance.md`), NOT here — do not regress them. Never add these to a plain
> agent-ops dashboard.

```ts
// The window every runtime-compliance widget must show as its subtitle.
export const WINDOW_LABEL = 'Last 15 agent runs'
```

## The governance span contract

Each agent run = one trace (`traceId` / `jobKey`). Governance spans (within the trace) come in two kinds.
`attributes` is an **object** when the spans come from `Traces.getById` (`SpanGetResponse.attributes` is
`Record<string, unknown>`) and a **JSON string** from the AgentTraces endpoints — `@/lib/governance`
accepts both, so never `JSON.parse` by hand.

- **Per-rule** — `name` starts with `governance.rule.`. Keys: `governance.rule_id`, `governance.rule_name`,
  `governance.pack_name` (the standard, e.g. `ISO/IEC 42001:2023 Runtime`), `governance.hook`
  (`BEFORE_AGENT`/`BEFORE_MODEL`/`AFTER_MODEL`/`AFTER_AGENT`), `governance.matched` (bool),
  `governance.action` (`allow`/`audit`/`block`), `governance.status` (`PASS`/`MATCHED`),
  `governance.detail`, `agentName`/`agentVersion`. **A violation = `governance.matched === true`.**
- **Per-hook summary** — `governance.before_agent|before_model|after_model|after_agent`:
  `governance.total_rules`, `governance.matched_rules`, `governance.final_action`,
  `governance.enforcement_mode` (`audit`/`enforce`).
- Some rule spans carry only `{agentId, agentName, agentVersion}` (no rule signal) — the parser skips them.
  The integer span `status`/`Status` is NOT the governance signal; use `governance.matched`/`governance.status`.

## Violations vs evaluations (PASS vs MATCHED)

- **VIOLATION** = `governance.matched` truthy (`true` or `"true"`) — a rule fired.
- **EVALUATION** = ANY `governance.rule.*` span — every rule check, PASS or MATCHED.

Violation-only widgets show coverage gaps, but a healthy fleet (rules passing) renders empty — indistinguishable from "no governance data". So when the user asks for **runtime compliance** (not just violations), ALSO propose an all-evaluations widget: `rule-evaluations-by-outcome` (Pass vs Matched), `rule-evaluations-by-hook`, or `rule-compliance`. Back those with `parseRuleEvaluations`; keep the violation widgets on `parseGovernanceSpans().violations`.

```ts
import { parseGovernanceSpans, parseRuleEvaluations, countBy } from '@/lib/governance'
import type { GovernanceRuleEvaluation } from '@/lib/governance'

const evals = parseRuleEvaluations(spans)            // EVERY rule check (PASS + MATCHED); each has matched/outcome
const violations = parseGovernanceSpans(spans).violations // matched only
```

`GovernanceRuleEvaluation = GovernanceViolation + { matched: boolean, outcome: 'Matched' | 'Pass' }`.

## Use the shipped lib — never hand-roll parsing

`@/lib/governance` (typed, hardened, never throws) is the only sanctioned parser:

```ts
import { parseGovernanceSpans, countBy } from '@/lib/governance'
import type { GovernanceViolation, GovernanceHookSummary, GovernanceHook } from '@/lib/governance'

const { violations, hookSummaries } = parseGovernanceSpans(spans) // violations = one row per FIRED rule
// countBy(violations, v => v.standard) → chart-ready [{name,value}] (descending)
```

`GovernanceViolation = { agentName, agentVersion, ruleId, ruleName, standard, hook, action, status, detail, time, jobKey, traceId }`.

## SDK fetch paths — use `Traces.getById(traceId)`

Spans come from **`new Traces(sdk).getById(traceId)`** → bare `SpanGetResponse[]` (up to `pageSize`, default
1000, single fetch — no cursor). The Insights/AgentTraces span endpoints do not reliably return the
governance spans; `Traces.getById` does. Get the `traceId` from the agent's Job. Subpath:
`@uipath/uipath-typescript/traces`.

- **Per-agent / per-run (Layer 1, cheap):** find the run via `Jobs.getAll({ filter: "ProcessType eq 'Agent'",
  orderby: 'CreationTime desc' })` → match `processName` (or `traceId`) → `Traces.getById(traceId)`.
- **Recent-runs scan (Layer 2, bounded, DEFAULT):** enumerate the **last `MAX_RUNS` (=15) agent runs** via the
  same Jobs call (each Job carries its `traceId`), newest first, **no per-agent dedup** — so repeat runs from
  the same agent stay visible — and `Traces.getById` each. Bounded + rate-limit-safe. Surface the
  `WINDOW_LABEL` in the widget.
- **Latest-per-agent scan (opt-in):** the deduped variant (one row per distinct agent). Use ONLY when the user
  explicitly wants per-agent rollup, not recent runs. Same 15-run bound.

```ts
import type { MetricFn } from '@/lib/metric-contract'
import { parseGovernanceSpans, parseRuleEvaluations, countBy } from '@/lib/governance'

const MAX_RUNS = 15 // hard cap — see the INTERIM callout above

// DEFAULT scanner: last MAX_RUNS agent runs, NO dedup. `parse` is
// `s => parseGovernanceSpans(s).violations` (violations) or `parseRuleEvaluations` (all checks).
// pageSize > MAX_RUNS so we still reach 15 *traced* runs if some jobs lack a traceId.
async function scanRecentRuns(sdk: any, parse: (spans: any) => any[]) {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { Traces } = await import('@uipath/uipath-typescript/traces')
  const jobs = (await new Jobs(sdk as never).getAll(
    { filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc', pageSize: 50 }))?.items ?? []
  const out: any[] = []
  let scanned = 0
  for (const j of jobs as Array<{ traceId?: string | null }>) {
    if (!j.traceId) continue
    const spans = await new Traces(sdk as never).getById(j.traceId)
    out.push(...parse(spans))
    if (++scanned >= MAX_RUNS) break
  }
  return out // caller groups/aggregates; widget shows EmptyState when []
}

// OPT-IN: latest run per distinct agent (dedup). Same 15-run bound.
async function scanLatestPerAgent(sdk: any, parse: (spans: any) => any[]) {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { Traces } = await import('@uipath/uipath-typescript/traces')
  const jobs = (await new Jobs(sdk as never).getAll(
    { filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc', pageSize: 100 }))?.items ?? []
  const seen = new Set<string>()
  const out: any[] = []
  for (const j of jobs as Array<{ processName?: string | null; traceId?: string | null }>) {
    const agent = j.processName ?? ''
    if (!j.traceId || (agent && seen.has(agent))) continue
    seen.add(agent)
    const spans = await new Traces(sdk as never).getById(j.traceId)
    out.push(...parse(spans))
    if (seen.size >= MAX_RUNS) break
  }
  return out
}

// Public scanners — DEFAULT to recent-runs (no dedup). Swap to scanLatestPerAgent only on explicit request.
const scanViolations  = (sdk: any) => scanRecentRuns(sdk, s => parseGovernanceSpans(s).violations)
const scanEvaluations = (sdk: any) => scanRecentRuns(sdk, parseRuleEvaluations)

// violations-by-standard (donut: xKey name, yKey value) — subtitle = WINDOW_LABEL.
export const fetchData: MetricFn = async (sdk) => countBy(await scanViolations(sdk), v => v.standard)
```

### All-evaluations scan (PASS + MATCHED) — `scanEvaluations`

`scanEvaluations` (above) is `scanRecentRuns` with `parseRuleEvaluations` — EVERY rule check, so a compliant
fleet is visible (not just violations). Same last-15-runs bound.

```ts
import { countBy } from '@/lib/governance'

// rule-evaluations-by-hook (donut)
const byHook = countBy(await scanEvaluations(sdk), e => e.hook)
// rule-evaluations-by-outcome (donut → Pass vs Matched)
const byOutcome = countBy(await scanEvaluations(sdk), e => e.outcome)

// rule-compliance (ranked-table): group by ruleName → evaluated vs matched counts
const evals = await scanEvaluations(sdk)
const m = new Map<string, { name: string; standard: string; hook: string; evaluated: number; matched: number }>()
for (const e of evals) {
  const cur = m.get(e.ruleName) ?? { name: e.ruleName, standard: e.standard, hook: e.hook, evaluated: 0, matched: 0 }
  cur.evaluated += 1
  if (e.matched) cur.matched += 1
  m.set(e.ruleName, cur)
}
const ruleCompliance = [...m.values()].sort((a, b) => b.evaluated - a.evaluated)
```

> `Traces.getById(traceId, { agentId?, pageSize?, includeExpiredSpans? })` returns the trace's full span set
> (governance rule + hook spans included); `parseGovernanceSpans` filters to the governance ones. Generic
> alternative if needed: `Traces.getSpansByIds(traceId, spanIds)`.

## `agent-compliance-report` — actual job runs + rowLink drill-down

A `data-table` of the **last 15 agent job runs** (NOT a deduped agent list, NOT the Insights `Agents.getAll`
aggregate). Each row is one run summarized from its trace: agent, start time, rules evaluated, rules matched
(violations), final action. `rowLink: { key: "runKey" }` keys on the run's `traceId`, so the drill-down opens
the exact run. The subtitle is `WINDOW_LABEL` (`Last 15 agent runs`).

`fetchData` fetches one trace per run (bounded at 15 — rate-limit-safe). `fetchDetailByKey(sdk, runKey)`
re-reads that one trace and returns a named-source map for the rich `detailView`:
- `rows` — every rule check (PASS + MATCHED) for the run.
- `byOutcomeByHook` — Pass vs Matched per hook (multi-line series; keys `Pass`/`Matched`).
- `byAction` — matched rules by enforcement action (`block`/`audit`/`allow`) donut.
- `byRule`, `byHook`, `byOutcome` — violation rollups.

```ts
import type { MetricFn, MetricDetailByKeyFn } from '@/lib/metric-contract'
import { parseGovernanceSpans, parseRuleEvaluations, countBy } from '@/lib/governance'

const MAX_RUNS = 15
const HOOKS = ['BEFORE_AGENT', 'BEFORE_MODEL', 'AFTER_MODEL', 'AFTER_AGENT'] as const

// Main table = last 15 agent RUNS (job runs), each summarized from its trace.
export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { Traces } = await import('@uipath/uipath-typescript/traces')
  const jobs = (await new Jobs(sdk as never).getAll(
    { filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc', pageSize: 50 }))?.items ?? []
  const rows: any[] = []
  for (const j of jobs as Array<{ processName?: string | null; traceId?: string | null; startTime?: string | null }>) {
    if (!j.traceId) continue
    const spans = await new Traces(sdk as never).getById(j.traceId)
    const evals = parseRuleEvaluations(spans)
    const { violations } = parseGovernanceSpans(spans)
    rows.push({
      runKey: j.traceId,                       // rowLink key → drills into THIS run
      agentName: j.processName ?? '—',
      startTime: j.startTime ?? '',
      evaluated: evals.length,
      matched: violations.length,
      finalAction: violations.some(v => v.action === 'block') ? 'block'
        : violations.some(v => v.action === 'audit') ? 'audit' : 'allow',
    })
    if (rows.length >= MAX_RUNS) break
  }
  return rows
}

// Drill-down: re-read the run's trace (runKey IS the traceId) — one round-trip.
export const fetchDetailByKey: MetricDetailByKeyFn = async (sdk, runKey) => {
  const { Traces } = await import('@uipath/uipath-typescript/traces')
  const { parseGovernanceSpans, parseRuleEvaluations, countBy } = await import('@/lib/governance')
  const spans = await new Traces(sdk as never).getById(runKey)
  const rows = parseRuleEvaluations(spans)             // ALL checks (PASS + MATCHED)
  const { violations } = parseGovernanceSpans(spans)
  return {
    rows,
    byOutcomeByHook: HOOKS.map(h => ({
      hook: h,
      Pass:    rows.filter(e => e.hook === h && !e.matched).length,
      Matched: rows.filter(e => e.hook === h &&  e.matched).length,
    })),
    byAction:  countBy(violations, v => v.action),     // block/audit/allow
    byRule:    countBy(violations, v => v.ruleName),
    byHook:    countBy(violations, v => v.hook),
    byOutcome: countBy(rows,       e => e.outcome),
  }
}
```

When the metric declares `detailView`, return a **named-source map** (`{ rows, byOutcomeByHook, byAction, byRule, byHook, byOutcome }`) whose keys match each sub-widget's `source`; otherwise return a bare array (single table). All derived from ONE `Traces.getById` — no extra round-trips. See `primitives/detail-views.md § Rich detail views`.

> **Per-agent rollup instead of recent runs?** Only on explicit request — swap `fetchData` to `scanLatestPerAgent` (dedup by agent name, same 15-run bound) and key `rowLink` on `agentName`. Recent-runs (above) is the default.

## Scope

`OR.Jobs.Read` (enumerate agent runs → `traceId`, both layers) and `Traces.Api` + `Insights
Insights.RealTimeData OR.Folders.Read` (`Traces.getById` spans). All in `DASHBOARD_SCOPES`. **`Traces.Api`
is required** — `Traces.getById` 403s without it; it is registered on the external OAuth app at create time
(see `plugins/build/impl.md` Phase 3) and listed in the scaffold `uipath.json` + `useAuth` defaults.

## Robustness (hard requirement)

`parseGovernanceSpans` never throws — malformed JSON, minimal spans, and nulls are all skipped, and it
accepts `attributes` as either the object `Traces.getById` returns or a JSON string. Every governance widget
must render an EmptyState ("No governance data in the last N days") when the scan returns no violations / the
agents aren't governance-instrumented — never crash the dashboard.
