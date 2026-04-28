# Detail views — the drill-down contract

**Every widget must have a corresponding detail view.** The widget shows a summary (KPI, chart, ranked-table). Clicking anywhere that navigates (whole KPI card, `ViewAllLink` on a chart/table card, individual row in a ranked-table) MUST route to a real page that shows the underlying data — not a `#placeholder` hash.

## Why

A placeholder hash creates a false affordance. The card looks clickable, the user clicks, nothing useful happens. That's worse than a non-clickable tile — the user learns the dashboard is a dead-end. Real routes make every summary a gateway into the records behind it, which is how dashboards pay off exploration.

## The contract

For every widget `<WidgetName />` the generator produces:

1. A matching **detail view** at `src/dashboard/views/<WidgetName>View.tsx`.
2. A matching **list-style query hook** at `src/lib/queries/<kebab>-list.ts` — returns the FULL, non-aggregated rows the widget's summary is computed from.
3. A **route entry** in `src/app/App.tsx`: `<Route path="/<kebab>" element={<WidgetNameView sdk={sdk} />} />`
4. A **real href** on the widget's drill-down affordance:
   - KPI whole-card: `<a href="#/active-agents">` (HashRouter adds the `#/` prefix)
   - Chart `ViewAllLink`: `href="/active-agents"` (the component prepends `#/` via Link composition)
   - Table row onClick: `navigate('/active-agents')` via `useNavigate()`

## Relationship between widget hook and list hook

The widget hook is **aggregated** (e.g., bucketed time series, counts, rates). The list hook is **raw** (the rows themselves, same filter, no aggregation).

| Widget type | Widget hook returns | List hook returns |
|---|---|---|
| KPI (`useActiveAgents`) | a single number (distinct agent count) | full rows of each distinct agent with last-seen, first-seen, sample job |
| Bar chart (`useInvocationVolume24h`) | `{points: [{hour, invocations}]}` + headline | full `Job[]` rows in the 24h window, every field |
| Ranked table (`useTopAgents`) | top-N with aggregated metrics per row | full, unpaginated list of agents + their drill-down metrics |

The list hook **reuses the widget hook's filter** so the detail view is exactly the data behind the summary. This is the consistency invariant — a user seeing "24 active agents" and clicking expects to see those 24 rows, not 248 from some broader query.

## Filter semantics

The detail view's description (second line under the title) **states the filter in English**. Examples:

- KPI "Active agents (last 24h)" → view description: *"Agents that ran at least one job in the last 24 hours, sorted by last-seen."*
- Chart "Invocation volume — last 24 hours" → view description: *"All agent-type jobs created in the last 24 hours. 2,847 records."*
- Table "Top agents by invocation — last 7 days" → view description: *"All agents ranked by total invocations in the last 7 days. Click an agent to see its jobs."*

## Primitive used

`src/dashboard/chrome/DetailViewShell.tsx` — consistent page chrome (back link to dashboard, title, description, children). Every view wraps its content in this shell.

## Template

`assets/templates/views/detail-view.tsx.template` is the canonical shape:
- Imports the list hook.
- Renders a sortable full-width table of the raw rows.
- Wraps in `<DetailViewShell title={...} description={...}>`.

The generator specializes it per widget: column definitions match what's semantically meaningful for that data source (e.g., agent view has agent-name + invocations + errorRate + lastRun; invocation view has jobId + agent + startTime + state + duration).

## Rules for the generator

1. **Every widget gets a view.** Not optional. Generator produces `WidgetName.tsx` and `WidgetNameView.tsx` in the same Generate step.
2. **Every widget gets a list hook.** Even if it reuses the same SDK call — just without the aggregation step.
3. **Routes are flat.** `/{kebab-slug}`, not `/widgets/{slug}` or `/details/{slug}`. One segment keeps URLs simple.
4. **HashRouter everywhere.** Coded apps serve from arbitrary sub-paths (`https://<org>.uipath.host/<routing-name>/`), and HashRouter works without server-side rewrites. BrowserRouter would require `basename={{routingName}}` which is fragile.
5. **Back link on every detail view.** Points to `/` via `<Link to="/">`. Never use `history.back()` — breaks direct-loaded URLs.
6. **The detail view's query reuses the widget's filter.** Never broadens the filter (e.g., "all jobs" instead of "last 24h") — the detail view is the widget's data, unabridged.
7. **Use the same empty state message format.** Widget: "No agent invocations in the last 24 hours." → View: "No agent invocations in the last 24 hours. Try a broader time range or different filter."
8. **Never add filter UI in v1.** The view shows the widget's pre-filtered data. Adding per-view filters (time range pickers, search) is v2.
9. **State/status/priority/severity columns render as colored badges.** Per [../sdk/service-semantics.md § Semantic column renderers](../sdk/service-semantics.md), apply `<StateBadge service={...} field={...} value={row.X} />` to any column whose key matches a registered (service, field) pair. Plain-text "Faulted" / "Successful" cells are banned — UiPath products color-code these everywhere.
10. **KPI/drilldown semantic agreement.** When a KPI does a *distinct-count* aggregation (e.g., `Active Agents = 2` = distinct `processName` count), the drilldown table MUST show one row per distinct entity (with the count as a column), NOT the raw underlying records. Example: `Active Agents (2)` drilldown shows 2 agent rows with `name | invocations | last seen | error rate`, NOT 6 job records. If you need the raw record list, give the KPI a different label (e.g., `Active Agents — 2 distinct, 6 invocations`) and route the drilldown accordingly. The label and the data behind it must agree, always.

## Anti-patterns

- **Placeholder hashes** — `href="#active-agents"` with nothing at that route. Banned.
- **Back buttons using `history.back()`** — breaks when the view was loaded directly (bookmark, shared URL). Always use `<Link to="/">`.
- **Views that re-fetch different data than the widget** — breaks the "what you see behind the summary" contract.
- **Per-view filter UIs in v1** — scope creep. Ship filterless views first.
- **Nested routes** — `/widgets/active-agents/details` is noise. `/active-agents` is fine.
- **Rendering SDK error objects directly as React children** — `{row.jobError}` crashes React with "Objects are not valid as a React child" because `jobError` is a structured `{code, title, detail, ...}` object. Always flatten: `{formatJobError(row.jobError)}` from `_shared.ts`. Same discipline for any field that might surface as an object (error payloads, trace details, bodyJson fields).

## Example — full flow for the agent-health case

```
Widget                            Detail view                       List hook
─────────────────────────────────  ──────────────────────────────   ─────────────────────────────
ActiveAgentsKPI.tsx                ActiveAgentsView.tsx              active-agents-list.ts
  useActiveAgents → 24               useActiveAgentsList             fetchAllJobs(24h agent-only)
                                                                      → group by processName
                                                                      → return Agent[] rows
  whole card: href="#/active-agents"
                                  route: /active-agents
                                  columns: agent, last seen, job count, error count, latency

InvocationVolume24h.tsx            InvocationVolumeView.tsx          invocation-volume-list.ts
  useInvocationVolume24h → {points}  useInvocationVolumeList         fetchAllJobs(24h agent-only)
                                                                      → return Job[] rows
  ViewAllLink: href="/invocation-volume"
                                  route: /invocation-volume
                                  columns: jobId, agent, startTime, state, duration

TopAgentsTable.tsx                 TopAgentsView.tsx                 top-agents-list.ts
  useTopAgents → TopAgentRow[]       useTopAgentsList                fetchAllJobs(7d agent-only)
                                                                      → group by processName
                                                                      → full unpaginated list
  row click: navigate(`/top-agents/${agent}`)   route: /top-agents/:agent (future v2 — per-agent detail)
  or: ViewAllLink → /top-agents                 route: /top-agents
                                  columns: agent, invocations, errors, errorRate, avgLatency, lastRun
```
