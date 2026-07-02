# Agent Governance Decisions (Insights RTM)

> Requires `@uipath/uipath-typescript` **≥ 1.5.1**. Scopes: `Insights Insights.RealTimeData OR.Folders.Read` (all in `DASHBOARD_SCOPES`). Subpath: `@uipath/uipath-typescript/traces` (the `AgentTraces` service).
> **Org-admin required.** Both methods 403 for non-admin callers (SDK throws `AuthorizationError`). On 403: tell the user their account lacks governance access, render the widget's EmptyState, build the rest of the dashboard. Do not retry.

First-class Insights endpoints for **agentic runtime governance** — every policy check an agent run went through (allow/deny per hook) plus an aggregated posture summary. These widgets honor the dashboard time range like any other metric.

> **GATE — propose these ONLY on an EXPLICIT runtime-compliance signal:** a standard/pack reference
> ("standard(s)", "pack", `ISO` + clause e.g. `ISO 42001` / `A.8.4`, or a named pack), an explicit **rule/policy
> violation** ask ("rule(s) violated/fired", "runtime violations"), or runtime-governance terms ("runtime
> compliance/governance", hook names, `enforce`/`audit` mode). Generic "governance / policy / denials / blocked
> actions / allow-deny / enforcement" routes to `policy-denials` / `governance-verdicts` (`sdk/governance.md`) —
> a different domain (platform policy enforcement). When unsure which the user means, ASK. Never add these
> widgets to a plain agent-health/ops dashboard.

```typescript
import { AgentTraces, AgentGovernanceVerdict, AgentGovernanceSection } from '@uipath/uipath-typescript/traces'
const svc = new AgentTraces(sdk)
```

Both methods take a **required positional `startTime: Date`** first (same convention as `Governance.getPolicyTraces`); everything else lives in options.

## getGovernanceSummary(startTime, options?) — breakdowns in ONE call

Returns a **single object — not an array**. Options: `{ endTime?, topN?, packName?, sections? }`.

**Example response** (grounded in SDK test fixtures):

```json
{
  "total": 26, "violations": 3,
  "byHook":   [{ "key": "BEFORE_MODEL", "name": null, "count": 12, "violationCount": 2 }],
  "byAgent":  [{ "key": "af12…", "name": "customer-care-assistant-for-acmecare", "count": 20, "violationCount": 1 }],
  "byPolicy": [{ "key": "ISO42001-guardrail-prompt-injection", "name": "AI system impact assessment", "count": 2, "violationCount": 0 }],
  "byPack":   [{ "key": "ISO/IEC 42001:2023 Runtime", "name": null, "count": 26, "violationCount": 3 }],
  "byAction": [], "byMode": []
}
```

Semantics:
- `violations` / `violationCount` = **Deny verdicts**; `count`/`total` = all checks. Violation widgets read `violationCount`; all-checks widgets read `count`.
- **`byAction` and `byMode` are EMPTY unless opted in** via `sections: [AgentGovernanceSection.Action]` / `[…Mode]`. Forgetting `sections` is the compiles-green-renders-empty trap here.
- `name` is populated for `byPolicy`/`byAgent`; render `name ?? key`.
- `topN` caps each breakdown; `packName` scopes totals + breakdowns to one pack.

## getGovernanceDecisions(startTime, options?) — the record grain

One row per policy check. Paginated; rows on `.items`. Options: `{ endTime?, hook?, evaluatorResult?, policyId?, agentId?, violationsOnly?, pageSize?, cursor? }`.

**Example response** (`.items` — grounded in SDK test fixtures):

```json
{
  "items": [{
    "startTime": "2026-06-28T14:03:22Z", "endTime": "2026-06-28T14:03:24Z",
    "traceId": "3f9c…", "jobKey": "8a1d…", "folderKey": "f-1001", "source": "10",
    "policyId": "ISO42001-guardrail-prompt-injection", "policyName": "AI system impact assessment",
    "packName": "ISO/IEC 42001:2023 Runtime", "hook": "BEFORE_MODEL",
    "mode": "ENFORCE", "actionApplied": "BLOCK", "evaluatorResult": "DENY",
    "reason": "Prompt injection was detected with a probability of 0.97.",
    "agentId": "af12…", "agentName": "customer-care-assistant-for-acmecare"
  }]
}
```

Semantics — the traps:
- **`evaluatorResult === AgentGovernanceVerdict.Deny` IS the violation.** `mode` (`AUDIT`/`ENFORCE`) says whether it was enforced; `actionApplied` is the enforcement action string (`null` in audit mode). Compare enum fields with the imported enums — `d.evaluatorResult === 'DENY'` is a tsc error.
- **No server-side `traceId` filter.** Per-run views fetch the window and filter client-side on the row's `traceId`. `agentId` (agent project key) IS a server-side filter.
- `violationsOnly: true` → Deny rows only. Use for violation tables and violation drill-downs.
- One agent run = one `traceId` (with its `jobKey`); group rows by `traceId` for run-level rollups.
- Rows are TS interfaces — project with `.map(x => ({ ...x }))`, never `as` casts.
- User vocabulary maps onto the response fields: "rule" → **policy** (`policyId`/`policyName`), "standard" → **pack** (`packName`), "violation" → **Deny verdict**, "enforcement action" → **actionApplied**, "audit vs enforce" → **mode**.

## Module patterns

```typescript
// agent-governance-violations (kpi-card with delta): summary twice — window + prior window
import type { MetricFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW, priorWindow } from '@/lib/time'

export const fetchData: MetricFn = async (sdk) => {
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const svc = new AgentTraces(sdk)
  const [prevStart, prevEnd] = priorWindow(THIRTY_DAYS_AGO, NOW)
  const [cur, prev] = await Promise.all([
    svc.getGovernanceSummary(THIRTY_DAYS_AGO, { endTime: NOW }),
    svc.getGovernanceSummary(prevStart, { endTime: prevEnd }),
  ])
  return [{ value: cur.violations, previous: prev.violations }]
}

// fetchDetail — the Deny decisions behind the count (record-grain drill-down)
export const fetchDetail: MetricFn = async (sdk) => {
  const { AgentTraces } = await import('@uipath/uipath-typescript/traces')
  const page = await new AgentTraces(sdk).getGovernanceDecisions(THIRTY_DAYS_AGO, { endTime: NOW, violationsOnly: true })
  return (page?.items ?? []).map(x => ({ ...x }))
}
```

```typescript
// Breakdown donuts / ranked tables: ONE summary call, pick the section
// violations-by-standard → byPack · violations-by-rule → byPolicy · violations-by-hook → byHook
// agents-by-violations → byAgent · matched-rules-by-action → byAction (sections opt-in!)
const { AgentTraces, AgentGovernanceSection } = await import('@uipath/uipath-typescript/traces')
const s = await new AgentTraces(sdk).getGovernanceSummary(THIRTY_DAYS_AGO, {
  endTime: NOW,
  sections: [AgentGovernanceSection.Action],   // ONLY when reading byAction/byMode
})
return s.byPack.map(p => ({ name: p.name ?? p.key ?? 'Unknown', value: p.violationCount }))
```

```typescript
// rule-evaluations-by-outcome (donut): Allow vs Deny across all checks
const s = await new AgentTraces(sdk).getGovernanceSummary(THIRTY_DAYS_AGO, { endTime: NOW })
return [
  { name: 'Allow', value: s.total - s.violations },
  { name: 'Deny', value: s.violations },
]
```

```typescript
// recent-violations (data-table): the raw Deny rows
const page = await new AgentTraces(sdk).getGovernanceDecisions(THIRTY_DAYS_AGO, { endTime: NOW, violationsOnly: true })
return (page?.items ?? []).map(x => ({ ...x }))
```

## `agent-compliance-report` — one row per run + rowLink drill-down

Group decisions by `traceId` (one run = one trace). Keep the row keys the registry columns expect: `runKey`, `agentName`, `startTime`, `evaluated`, `matched`, `finalAction`.

```typescript
import type { MetricFn, MetricDetailByKeyFn } from '@/lib/metric-contract'
import { THIRTY_DAYS_AGO, NOW } from '@/lib/time'

type RunRow = { runKey: string; agentName: string; startTime: string; evaluated: number; matched: number; finalAction: string }

export const fetchData: MetricFn = async (sdk) => {
  const { AgentTraces, AgentGovernanceVerdict, AgentGovernanceMode } = await import('@uipath/uipath-typescript/traces')
  const rows = (await new AgentTraces(sdk).getGovernanceDecisions(THIRTY_DAYS_AGO, { endTime: NOW }))?.items ?? []
  const byRun = new Map<string, RunRow>()
  for (const d of rows) {
    if (!d.traceId) continue
    const run = byRun.get(d.traceId) ?? { runKey: d.traceId, agentName: d.agentName ?? '—', startTime: d.startTime, evaluated: 0, matched: 0, finalAction: 'allow' }
    run.evaluated += 1
    if (d.evaluatorResult === AgentGovernanceVerdict.Deny) {
      run.matched += 1
      run.finalAction = d.mode === AgentGovernanceMode.Enforce ? (d.actionApplied ?? 'enforced') : 'audit'
    }
    byRun.set(d.traceId, run)
  }
  return [...byRun.values()].sort((a, b) => b.startTime.localeCompare(a.startTime)).map(r => ({ ...r }))
}

// Drill-down: same window, filtered client-side to the clicked run (no server traceId filter).
// Returns the named-source map the registry detailView expects.
export const fetchDetailByKey: MetricDetailByKeyFn = async (sdk, key) => {
  const { AgentTraces, AgentGovernanceVerdict } = await import('@uipath/uipath-typescript/traces')
  const all = (await new AgentTraces(sdk).getGovernanceDecisions(THIRTY_DAYS_AGO, { endTime: NOW }))?.items ?? []
  const rows = all.filter(d => d.traceId === key).map(x => ({ ...x }))
  const denies = rows.filter(d => d.evaluatorResult === AgentGovernanceVerdict.Deny)
  const count = (list: typeof rows, pick: (d: (typeof rows)[number]) => string) => {
    const acc: Record<string, number> = {}
    for (const d of list) { const k = pick(d); acc[k] = (acc[k] ?? 0) + 1 }
    return Object.entries(acc).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)
  }
  const hooks = [...new Set(rows.map(d => String(d.hook ?? 'UNKNOWN')))]
  return {
    rows,
    byOutcomeByHook: hooks.map(h => ({
      hook: h,
      Allow: rows.filter(d => String(d.hook ?? 'UNKNOWN') === h && d.evaluatorResult !== AgentGovernanceVerdict.Deny).length,
      Deny: rows.filter(d => String(d.hook ?? 'UNKNOWN') === h && d.evaluatorResult === AgentGovernanceVerdict.Deny).length,
    })),
    byAction: count(denies, d => String(d.actionApplied ?? 'none')),
    byPolicy: count(denies, d => String(d.policyName ?? d.policyId ?? 'Unknown')),
  }
}
```

When the metric declares `detailView`, the detail fetch returns a **named-source map** (`{ rows, byOutcomeByHook, byAction, byPolicy }`) whose keys match each sub-widget's `source`. See `primitives/detail-views.md § Rich detail views`.

## Robustness

- Violation widgets on a passing fleet render an EmptyState ("No violations in this window — checks are passing"). For runtime-compliance requests ALSO offer an all-checks widget (`rule-evaluations-by-outcome`, `rule-evaluations-by-hook`, `rule-compliance`) so a compliant fleet is visible — an empty violations donut is indistinguishable from "no governance data".
- UiPath currently ships ONE governance pack — `violations-by-standard` (byPack) is usually a single slice. Prefer by-hook / by-action / by-policy / by-agent groupings; propose by-standard only when >1 pack exists.
- 403 → org-admin missing (see the header note). Never fabricate data — surface the access gap and build the rest.
