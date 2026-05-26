# Dashboard Skill — Capability Registry Design

**Date:** 2026-05-27
**Branch:** `feat/uipath-dashboards-skill`
**Status:** Approved — ready for implementation planning

---

## Problem

The dashboard skill today has two disconnected data-path documents (`insights-catalog.md` and `data-router.md`) that are maintained independently, cover only Insights RTM, and have no principled mechanism for refusing requests the SDK cannot fulfill. When a user asks for an unmapped metric, the agent either silently approximates or invents a call to a non-existent endpoint. Both produce broken dashboards.

The skill also has a growing surface of smaller issues: time constants duplicated in three files, incremental detection buried after four doc loads, template placeholders not validated, and an Insights HTTP client that can't distinguish CORS failures from auth failures.

---

## Goal

A dashboard skill where:
- The agent knows exactly what data is available and how to access it
- Requests for unavailable metrics produce a clear, specific refusal with alternatives — never silent approximation
- The build pipeline is reliable from NLP input to running preview
- The scaffold and templates are correct, tested, and maintainable
- The architecture has a clean migration path for when Insights endpoints join the TypeScript SDK

---

## Architecture: Capability Registry

### Core concept

Replace `insights-catalog.md` and `data-router.md` with a single `sdk-capabilities.md` reference. This file is the authoritative list of every data source the skill can use, organized by domain. It is the only document the agent consults for capability decisions.

The SDK is the single intended data layer. The existing Insights RTM HTTP client (`useInsights.ts` + `insights-client.ts`) is a temporary implementation for endpoints not yet in the SDK — documented as such in the registry, with migration path explicit.

### Registry entry structure

Each capability is documented as a structured block:

```
### <domain>.<method> — Human-readable name

**Source:** SDK method OR Insights RTM HTTP client (pending SDK migration)
**Method/Endpoint:** exact call signature or endpoint path
**Parameters:** required and optional fields
**Response shape:** TypeScript interface with field names and types

**Computable metrics:**
- explicit list of what CAN be derived from this data

**Cannot compute from this data:**
- explicit list of what this data CANNOT tell you

**Widget templates:** which of the 10+ templates map to this data
**Aliases:** common NLP phrasings that map to this capability
```

### Top-level refuse table

At the start of `sdk-capabilities.md`, before any capability entries, a table of 12–15 commonly requested metrics that NO UiPath API can produce:

| Requested | Why unavailable | Suggest instead |
|---|---|---|
| Agent cost in dollars | Platform tracks AGU/PLTU, not currency | processes.getConsumption |
| Real-time CPU/memory | Not exposed via any UiPath API | — |
| Per-user job attribution | Job records don't carry end-user identity | — |
| Cross-tenant comparison | Dashboard scoped to one tenant at build time | — |

Agent checks this table first in Phase 3a before searching capability entries.

### Coverage

**Insights RTM (HTTP client — pending SDK migration):**
- `agents.getErrors` — agent error counts
- `agents.getSummary` — success/failure rates, invocation volume
- `agents.getLatency` — run duration percentiles
- `agents.getAgents` — registered agent list and metadata
- `jobs.getTimeline` — job activity over time
- `jobs.getCompletedTimeline` — completed job timeline (document actual response shape from SDK source, or mark RED until confirmed)

**Orchestrator SDK:**
- `sdk.orchestrator.getJobs()` — job counts, status, process breakdown
- `sdk.orchestrator.getQueues()` — queue depth, throughput, wait times
- `sdk.orchestrator.getProcesses()` — process list, consumption (AGU/PLTU)
- `sdk.orchestrator.getAssets()` — asset inventory

---

## Pipeline Changes

### Phase 3 — two-step (replaces current single-step)

**Phase 3a — Feasibility gate (0 tool calls, in-context)**

For each metric in the user's request:
1. Check the refuse table — if matched, add to refuse list
2. Search registry aliases — classify as GREEN, AMBER, or RED:
   - **GREEN**: capability entry exists + matching widget template → generate via template substitution
   - **AMBER**: capability entry exists, no template → generate via agent-authored SDK hook in `files{}` map
   - **RED**: not found in registry → hard refuse

RED metrics never reach the plan. Refuse is surfaced inline in the plan message, not as a separate step:

```
Here's your Agent Health Dashboard — 5 widgets.
⚠ "Cost per agent run" isn't available — UiPath tracks consumption 
in AGU units, not currency. Excluded it. Want AGU consumption instead?
```

If an alternative exists, it's offered. If not, the refusal stands.

**Phase 3b — Widget configuration derivation (unchanged)**
Apply four-axis decomposition for GREEN and AMBER metrics only. Use registry response shapes (not guessed types) for `dataHook` and `dataSelector` fields. AMBER metrics use documented SDK method signatures directly.

### CAPABILITY.md — early incremental check

Move the state.json check to `CAPABILITY.md` before any plugin loads:

```
1. Check: ls .dashboard/state.json
2. EXISTS → load incremental-editor.md directly (skip build plugin)
3. MISSING → load build/impl.md
```

Prevents loading 4+ build documents when user is only adding a widget.

### `build-plan.md` — approval gate clarification

The plan shows widget list AND client ID question together. User's single response must address both. If widgets are approved but client ID question unanswered, agent re-asks specifically before proceeding to Phase 6.

---

## Template Evolution

### New SDK templates (4)

| Template | SDK method | Covers |
|---|---|---|
| `sdk-kpi-card` | `sdk.orchestrator.getJobs()` | Jobs completed, active robots, counts |
| `sdk-data-table` | `sdk.orchestrator.getQueues()` | Queue status overview |
| `sdk-bar-chart` | `sdk.orchestrator.getProcesses()` | Top processes by run count |
| `sdk-ranked-table` | `sdk.orchestrator.getJobs()` with groupBy | Agents by job volume |

These use `const { sdk } = useAuth()` directly. Placeholder syntax (`<COMPONENT_NAME>`, `<TITLE>`, etc.) is identical to existing templates. `build-dashboard.mjs` handles them the same way.

### AMBER path (agent-authored SDK hooks)

For AMBER metrics, agent writes a typed custom hook in the `files{}` map of `plan.json`. The capability registry entry provides the exact method signature and response shape — agent does not guess types. The script writes the file as-is; `tsc --noEmit` validates it.

Three-tier safety:
1. Template substitution for GREEN (known patterns, pre-tested)
2. Typed SDK call for AMBER (novel but documented)
3. Hard refuse for RED (unavailable)

### Existing templates unchanged

The 10 existing Insights RTM templates stay as-is. When Insights joins the SDK, those entries in the registry update their method references — templates and generation logic don't change. The registry is the seam.

---

## Bug Fixes

### Documentation

| Issue | Fix |
|---|---|
| Time constants in 3 places | Canonical definition stays in `build-plan.md`; other locations reference it |
| `data-router.md` | Retired — content migrates to `sdk-capabilities.md` |
| `insights-catalog.md` | Retired — content migrates to `sdk-capabilities.md` |
| `jobs.getCompletedTimeline` undocumented | Document actual response shape from SDK source, or mark RED in refuse table |
| `auth-context.md` `/dev/stdin` remnant | Replace with `os.tmpdir()` + temp file pattern |

### Scaffold code

| File | Fix |
|---|---|
| `useInsights.ts` | Add `cloudUrl`, `apiUrl`, `orgName`, `tenantName` to `useMemo` dependency array |
| `insights-client.ts` | Distinguish CORS/network failure vs server 4xx/5xx vs auth 401 — three distinct error messages |

### Out of scope

- Polling / live-refresh patterns (separate design needed)
- Multi-tenancy (separate design needed)
- `sdk.logout()` cleanup behavior (confirmed correct by user testing)
- Widget timezone handling (informational note only)

---

## Files Changed

### New
- `skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md`
- `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-kpi-card.tsx`
- `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-data-table.tsx`
- `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-bar-chart.tsx`
- `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-ranked-table.tsx`

### Modified
- `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md` — early incremental check
- `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md` — Phase 3 split, retire data-router/catalog references
- `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md` — approval gate clarification, time constants as canonical source
- `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/useInsights.ts` — cache key fix
- `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/insights-client.ts` — error distinction

### Retired (content migrated to sdk-capabilities.md)
- `skills/uipath-coded-apps/references/dashboards/insights-catalog.md`
- `skills/uipath-coded-apps/references/dashboards/primitives/data-router.md`

---

## Success Criteria

1. Agent hard-refuses unmapped metrics with specific reason before plan is shown
2. All 10+ Insights RTM capabilities documented with complete response shapes in `sdk-capabilities.md`
3. 4 new Orchestrator SDK templates generate valid TypeScript on first build
4. Early incremental check in `CAPABILITY.md` prevents loading build docs for edit-only requests
5. `useInsights.ts` cache key includes all env var deps
6. `insights-client.ts` surfaces distinct error messages for CORS vs server vs auth failures
7. No `data-router.md` or `insights-catalog.md` references remaining in any skill file
