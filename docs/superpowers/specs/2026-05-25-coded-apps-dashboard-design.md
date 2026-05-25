# Design Spec: Dashboard Generation Capability for uipath-coded-apps

**Date:** 2026-05-25
**Branch:** feat/uipath-dashboards-skill
**Status:** Approved — ready for implementation planning

---

## Overview

Extend `uipath-coded-apps` from a single-purpose skill (Coded Web Apps + Action Apps) into a
capability hub that also generates admin dashboards from natural-language prompts. The new
dashboard capability uses the TS SDK for operational data and a temporary HTTP client for the
UiPath Insights API (being onboarded to the SDK; the skill is designed for a zero-effort swap
when that lands).

---

## Background

A POC on `feat/demo-gov` (local, unpushed) validated the core concept: NLP prompt → four-axis
metric decomposition → plan approval gate → template-first scaffold → parallel widget generation.
The POC was a standalone `uipath-dashboards` skill. This spec folds that capability into
`uipath-coded-apps` using the plugin hub patterns established by `uipath-maestro-flow` (capability
hub) and `uipath-governance` (disambiguation on ambiguous intent).

---

## Goals

1. Add dashboard generation to `uipath-coded-apps` without touching the existing 17 reference files
2. Route intent via disambiguation (silent for strong signals, explicit question for ambiguous ones)
3. Keep dashboard build pipeline ≤ 20 tool calls — template-first, parallel widget writes
4. Insights API: simple HTTP client now, zero-effort SDK swap later
5. Ship 3 eval tasks covering: NLP build, disambiguation, incremental widget add

---

## Non-Goals

- No reorganization of existing flat reference files into `references/apps/`
- No persona-specific preset dashboards (fully NLP-driven)
- No auto-deploy (deploy always requires explicit user confirmation)
- No Insights SDK adapter interface — simple HTTP client only, replaced when SDK ships

---

## File Structure

```
skills/uipath-coded-apps/
├── SKILL.md                                    ← 3 surgical edits (description, disambiguation, nav)
├── references/
│   ├── [17 existing files — UNCHANGED]
│   └── dashboards/                             ← NEW
│       ├── CAPABILITY.md                       ← Dashboard hub: critical rules, plugin router
│       ├── plugins/
│       │   ├── build/impl.md                   ← Plan → Approve → Scaffold → Validate → Preview
│       │   └── deploy/impl.md                  ← Pre-flight + delegates to ../pack-publish-deploy.md
│       ├── primitives/
│       │   ├── auth-context.md                 ← Resolve org/tenant/userId from uip login session
│       │   ├── build-plan.md                   ← Plain-language plan generation + approval gate
│       │   ├── data-router.md                  ← SDK vs Insights routing per metric intent
│       │   └── insights-client.md              ← Temp HTTP client (replace when SDK ships)
│       └── insights-catalog.md                 ← Static Insights capability catalog
└── assets/
    ├── templates/
    │   ├── web-app-template.md                 ← UNCHANGED
    │   ├── action-app-template.md              ← UNCHANGED
    │   └── dashboard/                          ← NEW
    │       ├── scaffold/                       ← Complete React + Vite + shadcn + Tailwind project
    │       │   ├── package.json
    │       │   ├── vite.config.ts
    │       │   ├── tailwind.config.ts
    │       │   ├── tsconfig.json
    │       │   └── src/
    │       │       ├── App.tsx
    │       │       ├── main.tsx
    │       │       ├── hooks/
    │       │       │   ├── useAuth.ts          ← PKCE OAuth (same pattern as web-app-template.md)
    │       │       │   └── useInsights.ts      ← InsightsClient wrapper hook
    │       │       ├── lib/
    │       │       │   ├── insights-client.ts  ← HTTP client implementation
    │       │       │   └── sdk-client.ts       ← TS SDK instantiation + scope wiring
    │       │       └── components/
    │       │           ├── DashboardShell.tsx
    │       │           ├── WidgetGrid.tsx
    │       │           └── MetricCard.tsx
    │       └── widgets/                        ← 6 chart component templates
    │           ├── area-chart.tsx
    │           ├── bar-chart.tsx
    │           ├── donut-chart.tsx
    │           ├── kpi-card.tsx
    │           ├── line-chart.tsx
    │           └── data-table.tsx
    └── scripts/
        └── discover-capabilities.mjs           ← Insights catalog enrichment (live tenant entities)
tests/tasks/
    ├── uipath-coded-apps-dashboard-build.yaml
    ├── uipath-coded-apps-dashboard-disambiguate.yaml
    └── uipath-coded-apps-dashboard-incremental.yaml
```

**Total: ~24 new files, 3 edits to SKILL.md, 0 changes to existing references.**

---

## SKILL.md Changes (3 edits only)

### Edit 1 — Frontmatter description

```yaml
---
name: uipath-coded-apps
description: "UiPath Coded Web Apps, Action Apps (app.config.json, action-schema.json),
  and admin dashboards. Build apps via uip codedapp + TS SDK. Generate analytics/KPI/
  observability dashboards from NLP using Insights API. For .cs/XAML→uipath-rpa,
  Python→uipath-agents, .flow→uipath-maestro-flow."
---
```

### Edit 2 — Disambiguation block (insert after Critical Rules)

```markdown
## Disambiguation — Apps vs Dashboards

**Route directly to Apps workflow** (sections below) when you see:
`web app`, `action app`, `codedapp`, `app.config.json`, `action-schema.json`,
`scaffold app`, `deploy app`, `pack`, `publish`, `push`, `pull`, `debug app`

**Route directly to [references/dashboards/CAPABILITY.md] when you see:**
`dashboard`, `analytics`, `KPI`, `metrics`, `Insights`, `observability`,
`admin console`, `report`, `chart`, `trend`, `governance report`, `agent metrics`

**When intent is ambiguous** — render this verbatim, wait for digit `1` or `2` only:

> Which fits your goal?
> 1. **Build or modify a Web App or Action App** — scaffold a UI, form, or app that deploys to Automation Cloud
> 2. **Generate a dashboard** — analytics or admin view from a natural-language description
```

### Edit 3 — Reference Navigation (append one row)

```markdown
| Dashboard generation (NLP → deployed dashboard) | [references/dashboards/CAPABILITY.md](references/dashboards/CAPABILITY.md) |
```

---

## Dashboard CAPABILITY.md

```markdown
# Dashboard Capability

## When to Use This Capability
- User wants a dashboard, analytics view, KPI summary, or metric report
- NLP prompt describes data to visualize ("agent success rates", "queue SLA", "governance violations")
- Iterating on an existing dashboard (adding widgets, changing chart types)

## Critical Rules
1. Read `primitives/auth-context.md` BEFORE any SDK or Insights API call
2. ALWAYS derive a plain-language plan before writing code — read `primitives/build-plan.md`
3. HALT at the approval gate — do not scaffold until user confirms the plan
4. Route each metric to SDK or Insights via `primitives/data-router.md` — never guess the source
5. NEVER hardcode tenant IDs, org names, or folder paths in generated code
6. NEVER auto-deploy — deploy pipeline always requires explicit user confirmation
7. Use the HTTP client from `primitives/insights-client.md` for all Insights API calls
8. All tokens flow through `useAuth()` — never store tokens in state, localStorage, or env vars at runtime
9. Run `tsc --noEmit` before claiming success
10. Every list call paginates — ≤50 rows per page, never load all

## Plugin Router

| I want to...                                  | Read                                |
|-----------------------------------------------|-------------------------------------|
| Create or edit a dashboard                    | [plugins/build/impl.md](plugins/build/impl.md) |
| Deploy a built dashboard to Automation Cloud  | [plugins/deploy/impl.md](plugins/deploy/impl.md) |

## Reference Files
- [primitives/auth-context.md](primitives/auth-context.md) — auth session resolution
- [primitives/build-plan.md](primitives/build-plan.md) — plan generation + approval gate
- [primitives/data-router.md](primitives/data-router.md) — SDK vs Insights routing
- [primitives/insights-client.md](primitives/insights-client.md) — Insights HTTP client
- [insights-catalog.md](insights-catalog.md) — Insights capability catalog
```

---

## build/impl.md — 8-Phase Pipeline

### Phase Overview

| Phase | Description | Tool-use cost |
|-------|-------------|---------------|
| 1 Boot | Parallel read: all 4 primitives + insights-catalog | 1 block |
| 2 Preflight | `uip login status --output json`, resolve org/tenant | 1 Bash |
| 3 Metric derivation | Four-axis decomposition in-context (no tools) | 0 |
| 4 Plan | Render markdown plan in chat (no code) | 0 |
| 5 Approval gate | HALT — wait for user | 0 |
| 6 Scaffold | One-shot Bash: copy template, npm install, shadcn init | 1 Bash |
| 7 Widget generation | Parallel Write: all widget files in one message | 1 block (N writes) |
| 8 Validate + summary | `tsc --noEmit`, smoke-test dev server, ready message | 2 Bash |

**Total: ≤ 14 tool calls for a 6-widget dashboard. Typical wall-clock: ~15s.**

### Four-Axis Metric Decomposition

For each metric in the NLP prompt, derive:

- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95 | p99`
- **Service**: `SDK` or `Insights` (via data-router.md)

### Plan Format

```
Here's what I'll build. Confirm to proceed, or tell me what to change.

1. Agent Success Rate (last 7 days)      [Insights] — area chart, daily % success
2. Active Queue Items by folder          [SDK]      — bar chart, snapshot count
3. P95 Process Execution Time            [Insights] — KPI card, weekly avg ms
4. Pending Action Center Tasks           [SDK]      — KPI card, live count
5. Governance Violations (last 30 days)  [Insights] — line chart, daily count
6. Maestro Flow Runs by status           [SDK]      — donut chart, snapshot
```

### Approval Gate Rules

- Any positive response → proceed
- Widget edit → update that line only, re-show changed lines only, re-ask
- Rejection without edit → ask "What would you like to change?"
- Never re-show full plan after partial edit
- Never start scaffolding before explicit approval

### Scaffold Phase (Phase 6)

Single Bash call — copies template, installs deps, inits shadcn:

```bash
cp -r assets/templates/dashboard/scaffold/. <PROJECT_DIR>/ && \
cd <PROJECT_DIR> && \
npm install && \
npx shadcn@latest init --defaults
```

This replaces ~30 individual Write calls. Scaffold provides:
`package.json`, `vite.config.ts`, `tailwind.config.ts`, `tsconfig.json`,
`src/App.tsx`, `src/main.tsx`, `src/hooks/useAuth.ts`, `src/hooks/useInsights.ts`,
`src/lib/insights-client.ts`, `src/lib/sdk-client.ts`,
`src/components/DashboardShell.tsx`, `src/components/WidgetGrid.tsx`,
`src/components/MetricCard.tsx`

### Widget Generation Phase (Phase 7)

- Read relevant widget templates (area-chart.tsx, kpi-card.tsx, etc.)
- Write all widget files in one parallel message block
- Each widget: fill exactly 4 placeholders: `<COMPONENT_NAME>`, `<DATA_HOOK>`, `<TITLE>`, `<X_KEY>/<Y_KEY>` or `<COLUMNS>`
- 6 widgets = 6 Write calls in 1 message = 1 round trip

### Validation Phase (Phase 8)

```bash
# In project dir
tsc --noEmit
npm run dev &
sleep 3 && curl -s http://localhost:5173 | grep -q "root" && echo "OK" || echo "FAIL"
kill %1
```

If `tsc --noEmit` fails → fix type errors before reporting success. Never skip.

---

## deploy/impl.md

```markdown
# Dashboard Deploy

## Pre-flight
1. Run: `npm run build` — fix errors before proceeding
2. Bump version in `package.json` (required for re-publish)

## Deploy Pipeline
Dashboard projects are standard Coded Web Apps.

→ Read [../../pack-publish-deploy.md](../../pack-publish-deploy.md) for all steps.

## Dashboard-specific Notes
- App type is always Web — never pass `-t Action` to `uip codedapp publish`
- Deployed app name should match the dashboard title from the build plan
- Verify the live URL loads without auth errors before reporting success
```

---

## primitives/auth-context.md

```markdown
# Auth Context Resolution

## Step 1 — Verify login
```bash
uip login status --output json
```
If `isLoggedIn` is false → stop, tell user to run `uip login`.

## Step 2 — Extract fields
```json
{
  "isLoggedIn": true,
  "accountName": "<ORG_NAME>",
  "tenantName": "<TENANT_NAME>",
  "userId": "<USER_UUID>"
}
```

## Step 3 — Construct base URLs
```
SDK base:      https://cloud.uipath.com/<ORG_NAME>/<TENANT_NAME>
Insights base: https://cloud.uipath.com/<ORG_NAME>/<TENANT_NAME>/insights_/api
```
Never hardcode these. Pass as constructor args to InsightsClient and TS SDK instance.

## Error handling
- 401 → token expired → re-run `uip login`, retry once
- Missing accountName/tenantName → tell user: "Run `uip login` and try again"
```

---

## primitives/data-router.md

```markdown
# Data Router — SDK vs Insights

Rule: SDK for operational state (current counts, list views, snapshots).
      Insights for analytics (historical trends, aggregations, percentiles, derived metrics).

## Routing Table

| Intent signals                                           | Route    | SDK method / Insights endpoint               |
|----------------------------------------------------------|----------|----------------------------------------------|
| job count, job status, running jobs, failed jobs         | SDK      | orchestrator/jobs → Jobs.getAll()            |
| queue items, queue depth, transaction throughput         | SDK      | orchestrator/queues → QueueItems.getAll()    |
| process list, automation inventory                       | SDK      | orchestrator/processes → Processes.getAll()  |
| maestro instances, flow runs, active flows               | SDK      | maestro/processes → ProcessInstances.getAll()|
| case status, case backlog                                | SDK      | maestro/cases → CaseInstances.getAll()       |
| case SLA, SLA compliance                                 | SDK      | maestro/cases → CaseInstances.getSlaSummary()|
| action center tasks, pending approvals                   | SDK      | action-center/tasks → Tasks.getAll()         |
| DataFabric entity records                                | SDK      | data-fabric/entities → Entities.getAll()     |
| agent success rate, agent failure rate                   | Insights | /agent-metrics                               |
| token consumption, LLM usage, cost per agent             | Insights | /agent-traces                                |
| tool usage, tool guardrails, tool violations             | Insights | /governance-metrics                          |
| P50 / P95 / P99 latency, percentile execution time       | Insights | /latency-analytics                           |
| job execution trend (historical), process duration trend | Insights | /job-analytics                               |
| governance violations, policy compliance                 | Insights | /governance-metrics                          |
| trace spans, distributed tracing                         | Insights | /traces                                      |

## Tie-breaking Rules
- "job count today" → SDK (current state); "job count over 30 days" → Insights (historical)
- "queue depth" → SDK (snapshot); "queue throughput trend" → Insights
- Any metric requiring P50/P95/P99 → always Insights

## SDK Import Pattern
```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
import { Jobs } from '@uipath/uipath-typescript/jobs';
// Never root imports — always subpath
```

## Insights Hook Pattern
```typescript
import { useInsights } from '../hooks/useInsights';
const { data } = useInsights('agent-metrics', { timeRange: '7d' });
```
```

---

## primitives/insights-client.md

```markdown
# Insights HTTP Client

Temporary HTTP client until Insights lands in @uipath/uipath-typescript.
When SDK ships: replace InsightsClient with the SDK class in sdk-client.ts.
No widget files, no hook call sites change on migration.

## Client Implementation

```typescript
// src/lib/insights-client.ts

interface InsightsRequestOptions {
  timeRange?: '1h' | '24h' | '7d' | '30d' | '90d';
  folderId?: string;
  [key: string]: string | undefined;
}

export class InsightsClient {
  constructor(
    private baseUrl: string,
    private getToken: () => Promise<string>
  ) {}

  private async request<T>(path: string, params: InsightsRequestOptions = {}): Promise<T> {
    const token = await this.getToken();
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null))
    );
    const res = await fetch(`${this.baseUrl}/${path}?${query}`, {
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    });
    if (res.status === 401) throw new Error('INSIGHTS_AUTH_EXPIRED');
    if (!res.ok) throw new Error(`Insights API error: ${res.status} on /${path}`);
    return res.json();
  }

  getAgentMetrics(opts: InsightsRequestOptions)     { return this.request('agent-metrics', opts); }
  getJobAnalytics(opts: InsightsRequestOptions)     { return this.request('job-analytics', opts); }
  getGovernanceMetrics(opts: InsightsRequestOptions){ return this.request('governance-metrics', opts); }
  getTraces(opts: InsightsRequestOptions)           { return this.request('traces', opts); }
  getLatencyAnalytics(opts: InsightsRequestOptions) { return this.request('latency-analytics', opts); }
}
```

## Initialization (in sdk-client.ts)

```typescript
import { InsightsClient } from './insights-client';
export const insightsClient = new InsightsClient(
  `https://cloud.uipath.com/${orgName}/${tenantName}/insights_/api`,
  getToken
);
```

## useInsights Hook (in hooks/useInsights.ts)

```typescript
export function useInsights<T>(
  endpoint: keyof Pick<InsightsClient, 'getAgentMetrics' | 'getJobAnalytics' | 'getGovernanceMetrics' | 'getTraces' | 'getLatencyAnalytics'>,
  opts: InsightsRequestOptions,
  deps: unknown[] = []
) {
  const { getToken } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const client = new InsightsClient(
      import.meta.env.VITE_INSIGHTS_BASE_URL,
      getToken
    );
    (client[endpoint] as (o: InsightsRequestOptions) => Promise<T>)(opts)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, deps);

  return { data, error, loading };
}
```

## SDK Migration Steps
1. In `sdk-client.ts`: replace `new InsightsClient(...)` with `new Insights(sdk)`
2. Delete `src/lib/insights-client.ts`
3. Update `useInsights.ts` import to use SDK class
4. Update `insights-catalog.md`: remove "HTTP client" note
```

---

## insights-catalog.md

```markdown
# Insights Capability Catalog

Static catalog of available Insights API endpoints.
Enriched at build time by `assets/scripts/discover-capabilities.mjs`
(adds live DataFabric custom entities if the tenant has them).

## Agent Observability — /agent-metrics
| Metric               | Shape options   | Time frames      |
|----------------------|-----------------|------------------|
| Success rate         | area, line, kpi | 1h, 24h, 7d, 30d |
| Failure rate         | area, line, kpi | 1h, 24h, 7d, 30d |
| Invocation count     | bar, line       | 24h, 7d, 30d     |
| Avg execution time   | line, kpi       | 7d, 30d, 90d     |

## Latency Analytics — /latency-analytics
| Metric               | Shape options   | Notes             |
|----------------------|-----------------|-------------------|
| P50 execution time   | kpi, line       | Per process/agent |
| P95 execution time   | kpi, line       | Per process/agent |
| P99 execution time   | kpi, line       | Per process/agent |

## Job Analytics — /job-analytics
| Metric               | Shape options   | Time frames   |
|----------------------|-----------------|---------------|
| Job duration trend   | area, line      | 7d, 30d, 90d  |
| Success/failure rate | bar             | 7d, 30d       |

## Governance Metrics — /governance-metrics
| Metric               | Shape options   | Time frames   |
|----------------------|-----------------|---------------|
| Policy violations    | line, bar       | 7d, 30d, 90d  |
| Tool guardrail hits  | bar, kpi        | 24h, 7d, 30d  |
| Compliance score     | kpi             | snapshot      |

## Distributed Traces — /traces
| Metric               | Shape options   | Notes                     |
|----------------------|-----------------|---------------------------|
| Span count by service| bar, donut      | Requires tracing enabled  |
| Token consumption    | area, kpi       | LLM calls only            |
| Tool call distribution| donut          | Per agent                 |

## Not in Insights — use SDK instead
Operational counts (live job/queue/task state), process inventory,
case SLA summaries, DataFabric entity records, Maestro instance lists.
```

---

## Widget Templates — Placeholder Convention

Each widget template uses exactly these placeholders:

| Placeholder       | Replaced with                                   |
|-------------------|-------------------------------------------------|
| `<COMPONENT_NAME>`| PascalCase component name (e.g., `AgentSuccessRate`) |
| `<DATA_HOOK>`     | Full hook call (e.g., `useInsights('agent-metrics', { timeRange: '7d' })`) |
| `<TITLE>`         | Human-readable widget title                     |
| `<X_KEY>`         | Data field for x-axis / row label               |
| `<Y_KEY>` / `<COLUMNS>` | Data field for y-axis value, or column defs for tables |

Example (area-chart.tsx template):

```tsx
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../hooks/useAuth';
// IMPORT: <DATA_HOOK_IMPORT>

export function <COMPONENT_NAME>() {
  const { getToken } = useAuth();
  const { data, loading, error } = <DATA_HOOK>;

  if (loading) return <div className="animate-pulse h-64 rounded-lg bg-muted" />;
  if (error) return <div className="text-destructive text-sm">Failed to load</div>;

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="text-sm font-medium text-muted-foreground mb-3"><TITLE></h3>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data}>
          <XAxis dataKey="<X_KEY>" />
          <YAxis />
          <Tooltip />
          <Area dataKey="<Y_KEY>" fill="hsl(var(--primary))" stroke="hsl(var(--primary))" fillOpacity={0.2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

## Eval Tasks

### Task 1 — NLP Build with Correct SDK/Insights Routing

```yaml
id: uipath-coded-apps-dashboard-build
skill: uipath-coded-apps
prompt: |
  Create a dashboard for my team showing:
  - Agent success rate over the last 7 days
  - Current active queue items by folder
  - P95 process execution time

success_criteria:
  - Plan shown before any files written (contains [Insights] and [SDK] labels)
  - Approval gate present (does not scaffold before user confirms)
  - After approval: scaffold directory created with package.json and vite.config.ts
  - area-chart widget uses useInsights hook for agent success rate
  - bar-chart widget uses SDK QueueItems (not Insights) for queue items
  - kpi-card widget uses useInsights for P95 latency
  - tsc --noEmit passes
  - No hardcoded tenant IDs or org names in generated files

sandbox:
  node: {}
```

### Task 2 — Ambiguous Intent Triggers Disambiguation

```yaml
id: uipath-coded-apps-dashboard-disambiguate
skill: uipath-coded-apps
prompt: |
  I need to create something to track my automation performance.

success_criteria:
  - Agent asks disambiguation question before taking any action
  - Question offers exactly two numbered options (App or Dashboard)
  - No files written, no npm commands run before user answers

sandbox:
  node: {}
```

### Task 3 — Incremental Widget Add

```yaml
id: uipath-coded-apps-dashboard-incremental
skill: uipath-coded-apps
prompt: |
  Add a widget to my existing dashboard showing governance violations
  over the last 30 days. The dashboard is at ./my-dashboard/

success_criteria:
  - Agent reads existing widget files before writing (detects hand edits)
  - Only new widget file written (existing widgets untouched)
  - New widget uses useInsights with governance-metrics endpoint
  - tsc --noEmit passes after addition
  - No re-scaffold of the entire project

sandbox:
  node: {}
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Tool calls for 6-widget build | ≤ 14 |
| Tool calls for incremental widget add | ≤ 8 |
| Wall-clock time (scaffold + 6 widgets) | ~15s |
| SKILL.md size increase | ~30 lines |
| dashboard/CAPABILITY.md lines | ~40 lines |

---

## Insights SDK Migration Checklist (when @uipath/uipath-typescript/insights ships)

- [ ] Replace `InsightsClient` in `sdk-client.ts` with SDK import
- [ ] Delete `src/lib/insights-client.ts` from scaffold template
- [ ] Update `useInsights.ts` import
- [ ] Update `primitives/insights-client.md`: mark as superseded, link to SDK docs
- [ ] Update `insights-catalog.md`: remove "HTTP client" note
- [ ] No widget files, no hook call sites change

---

## Open Questions (resolved during design)

| Question | Decision |
|----------|----------|
| Reorganize existing 17 refs into `references/apps/`? | No — keep flat, add `dashboards/` alongside |
| Insights adapter: interface or simple client? | Simple HTTP client (replace when SDK ships) |
| Disambiguation: always ask or smart-route? | Smart route (silent for strong signals, explicit question for ambiguous) |
| Persona presets? | No — fully NLP-driven |
