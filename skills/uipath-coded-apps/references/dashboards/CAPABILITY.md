---
name: uipath-coded-apps/dashboards
---

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

| I want to...                                  | Read                                           |
|-----------------------------------------------|------------------------------------------------|
| Create or edit a dashboard                    | [plugins/build/impl.md](plugins/build/impl.md) |
| Deploy a built dashboard to Automation Cloud  | [plugins/deploy/impl.md](plugins/deploy/impl.md) |

## Reference Files
- [primitives/auth-context.md](primitives/auth-context.md) — auth session resolution
- [primitives/build-plan.md](primitives/build-plan.md) — plan generation + approval gate
- [primitives/data-router.md](primitives/data-router.md) — SDK vs Insights routing
- [primitives/insights-client.md](primitives/insights-client.md) — Insights HTTP client
- [primitives/state-file.md](primitives/state-file.md) — per-project state.json (routing name, version, deployment metadata)
- [primitives/incremental-editor.md](primitives/incremental-editor.md) — editing existing dashboards (add/remove/change widgets)
- [insights-catalog.md](insights-catalog.md) — Insights capability catalog + widget recipes
- [aesthetic/layout-patterns.md](aesthetic/layout-patterns.md) — Dashboard layout rules (10 rules, widget row ordering)
- [aesthetic/charting.md](aesthetic/charting.md) — Chart type selection, colors, DeltaBadge direction guide
