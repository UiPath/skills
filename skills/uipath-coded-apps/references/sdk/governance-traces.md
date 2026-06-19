# Agent Governance Traces (interim, trace-derived)

> **INTERIM capability.** There is **no OOB SDK/Insights aggregate** for runtime-governance results yet.
> We derive them by parsing the `governance.*` spans the runtime-governance feature emits into agent
> traces. Bounded + rate-limit-safe by design. When an Insights API ships, only the metric modules change
> — the typed lib, registry entries, widgets, and the per-agent drill-down stay.
>
> **Only build these when the prompt EXPLICITLY signals runtime compliance, a standard/pack/ISO clause, or
> a rule violation** — see `primitives/tier-resolution.md § Governance violations (gated)`. Generic
> "governance / policy / denials / enforcement" must route to the Insights-API metrics `policy-denials` /
> `governance-verdicts` (`sdk/governance.md`), NOT here — do not regress them. Never add these to a plain
> agent-ops dashboard.

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
  orderby: 'CreationTime desc' })` → match `processName` → `traceId` → `Traces.getById(traceId)`.
- **Tenant-wide aggregate (Layer 2, bounded scan):** enumerate recent agent **runs** via the same Jobs call
  (each Job carries its `traceId`), take the latest run per distinct agent capped at `MAX_AGENTS` (=10), and
  `Traces.getById` each — bounded + rate-limit-safe; surface the cap in the widget.

```ts
import type { MetricFn } from '@/lib/metric-contract'
import { parseGovernanceSpans, countBy } from '@/lib/governance'

const MAX_AGENTS = 10

// Latest run per distinct agent (capped), spans via Traces.getById → parsed violations.
async function scanViolations(sdk: any) {
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
    out.push(...parseGovernanceSpans(spans).violations)
    if (seen.size >= MAX_AGENTS) break
  }
  return out // caller groups/aggregates; widget shows EmptyState when []
}

// violations-by-standard (donut: xKey name, yKey value)
export const fetchData: MetricFn = async (sdk) => countBy(await scanViolations(sdk), v => v.standard)
```

### All-evaluations scan (PASS + MATCHED) — `scanEvaluations`

Mirrors `scanViolations` (same bounded `Jobs` → `Traces.getById` scan, `MAX_AGENTS = 10`) but pushes `...parseRuleEvaluations(spans)` — EVERY rule check, so a compliant fleet is visible.

```ts
import { parseRuleEvaluations, countBy } from '@/lib/governance'

const MAX_AGENTS = 10

async function scanEvaluations(sdk: any) {
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
    out.push(...parseRuleEvaluations(spans))
    if (seen.size >= MAX_AGENTS) break
  }
  return out
}

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

## Layer-1 per-agent compliance report (rowLink drill-down)

A `data-table` of agents with `rowLink: { key: "agentName" }`; the module also exports
`fetchDetailByKey(sdk, agentName)` → that agent's latest run's spans → `parseRuleEvaluations` (ALL checks,
PASS + MATCHED) for the row table, plus violation rollups (`byHook`, `byRule`) and an outcome split
(`byOutcome`) — mirroring the product's Trace view but with the compliant rules visible too.

```ts
import type { MetricFn, MetricDetailByKeyFn } from '@/lib/metric-contract'
import { parseGovernanceSpans, parseRuleEvaluations, countBy } from '@/lib/governance'

export const fetchData: MetricFn = async (sdk) => {
  const { Agents } = await import('@uipath/uipath-typescript/agents')
  const { THIRTY_DAYS_AGO, NOW } = await import('@/lib/time')
  return (await new Agents(sdk as never).getAll(THIRTY_DAYS_AGO, NOW))?.items ?? []
}

export const fetchDetailByKey: MetricDetailByKeyFn = async (sdk, agentName) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { Traces } = await import('@uipath/uipath-typescript/traces')
  const { parseGovernanceSpans, parseRuleEvaluations, countBy } = await import('@/lib/governance')
  const jobs = (await new Jobs(sdk as never).getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' }))?.items ?? []
  const job = jobs.find((j: { processName?: string | null; traceId?: string | null }) => j.processName === agentName)
  if (!job?.traceId) return { rows: [], byHook: [], byRule: [], byOutcome: [] }
  const spans = await new Traces(sdk as never).getById(job.traceId)
  const { violations } = parseGovernanceSpans(spans)
  const rows = parseRuleEvaluations(spans) // ALL evaluations (PASS + MATCHED, minimal-attr skipped) — each has matched/outcome
  return {
    rows,
    byHook: countBy(violations, v => v.hook),
    byRule: countBy(violations, v => v.ruleName),
    byOutcome: countBy(rows, e => e.outcome),
  }
}
```

When the metric declares `detailView`, return a **named-source map** (`{ rows, byHook, byRule, byOutcome, … }`) whose keys match each sub-widget's `source`; otherwise return a bare array (single table). Derived from ONE `Traces.getById` — no extra round-trips. See `primitives/detail-views.md § Rich detail views`.

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
