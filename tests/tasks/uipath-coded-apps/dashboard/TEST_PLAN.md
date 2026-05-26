# Dashboard Capability — Test Plan

All tests for the `uipath-coded-apps` dashboard generation capability.
None of these exist on `main` — all are to be created as part of this feature.

Tests follow the three-tier pattern used across this repo:
- **Smoke** — PR-gate, ≤40 turns, validates basic correctness, no real API calls
- **Integration** — Daily, ≤200 turns, validates routing decisions and pattern compliance  
- **E2E** — Nightly, ≤200 turns, full lifecycle with real credentials

---

## Activation (`tests/tasks/activation/uipath-coded-apps.jsonl`)

One-shot binary classifier prompts. Run via `experiments/activation.yaml` (1 turn each).
Target: 20 prompts covering all dashboard types (agent reliability, cost, governance, ops).

| ID | Prompt |
|---|---|
| 051 | "build me an agent health dashboard" |
| 052 | "create a dashboard showing agent error rates and latency" |
| 053 | "I want to see invocation volume and success rate as a chart" |
| 054 | "generate an analytics dashboard with KPIs for my agent fleet" |
| 055 | "build a governance posture dashboard showing policy violations" |
| 056 | "show me agent metrics — active count, P95 latency, top erroring agents" |
| 057 | "I need an operations dashboard showing job completion trends" |
| 058 | "create a cost dashboard tracking AGU consumption by agent" |
| 059 | "build me a UiPath agent health dashboard: active agents, error rate trend" |
| 060 | "add a governance violations widget to my existing dashboard" |
| 061 | "I want a real-time view of how my agents are performing today" |
| 062 | "show me which agents are consuming the most resources this month" |
| 063 | "build a dashboard for the ops team to monitor agent health" |
| 064 | "I need a single view showing errors, latency, and usage for my fleet" |
| 065 | "add a memory usage chart to my existing monitoring dashboard" |

---

## Smoke Tests (`smoke/`)

PR-gate. Fast. No real API calls. Inherits experiment defaults (≤40 turns, 900s).

### `smoke/dashboard_plan_gate`
**What:** Agent shows a plan before scaffolding. npm ci must not run before the user approves.  
**Validates:** Approval gate is enforced — no code generated before confirmation.  
**Key criteria:** `command_executed npm ci` with `max_count: 0`; no package.json created before approval.

### `smoke/dashboard_scaffold`
**What:** 2-widget build produces correct structure and all 6 required env vars.  
**Validates:** Scaffold creates package.json, .env.local with VITE_UIPATH_CLOUD_URL / BASE_URL / ORG / TENANT / TENANT_ID / PAT; src/widgets/ exists; useInsights used; npm ci ran; App.tsx imports widgets.  
**Key criteria:** `file_check` for all 6 env vars; `command_executed npm ci`; `run_command` check_dashboard.py.

### `smoke/dashboard_disambiguate`
**What:** Ambiguous prompt halts and asks which mode (app or dashboard) before building.  
**Validates:** Agent asks clarifying question; no npm ci; no package.json created.  
**Key criteria:** `command_executed npm ci` with `max_count: 0`; `run_command` node check for no package.json.

### `smoke/dashboard_skill_trigger`
**What:** Correct skill fires for a dashboard-specific prompt.  
**Validates:** `uipath-coded-apps` skill activates (not another skill).  
**Key criteria:** `skill_triggered` with `expected: "yes"`.

---

## Integration Tests (`routing/`, `build/`)

Daily. Verify specific routing and pattern decisions.

### `routing/dashboard_sdk_routing`
**What:** SDK-routed metrics (queue items, running jobs, pending tasks) use SDK not Insights.  
**Validates:** QueueItems, Jobs.getAll, Tasks.getAll appear in widgets; no jobs.getCompletedTimeline used for live state.  
**Key criteria:** `run_command` python3 checks for SDK patterns and absence of Insights jobs API.

### `routing/dashboard_insights_routing`
**What:** Insights-routed metrics use the correct namespace and endpoint.  
**Validates:** agents.getErrors, agents.getLatencyTimeline, agents.getTopErroredAgents all appear; all three use useInsights.  
**Key criteria:** `run_command` python3 for specific endpoint presence; `run_command` check_dashboard.py with `--require-recipe`.

### `routing/dashboard_endtime`
**What:** Every useInsights call includes both startTime AND endTime.  
**Validates:** Missing endTime causes 500 errors from Insights API — regression test for this bug.  
**Key criteria:** `run_command` python3 that scans all widget TSX files for absence of endTime and fails if any is missing.

### `routing/dashboard_import_paths`
**What:** Generated widgets use `@/` aliases, not broken relative paths.  
**Validates:** `'../hooks/useInsights'` resolves to non-existent path from src/dashboard/widgets/ — regression test.  
**Key criteria:** `run_command` python3 that fails if any widget contains `'../hooks/` or `'../dashboard/chrome'`.

### `build/dashboard_recipe_usage`
**What:** Agent uses Widget Recipes from insights-catalog.md rather than inventing custom patterns.  
**Validates:** agents.getErrors, agents.getAgents, agents.getConsumption all appear; typed response generics present.  
**Key criteria:** `run_command` python3 per endpoint; `file_check` for `useInsights<{`.

### `build/dashboard_multiwidget`
**What:** 5-widget dashboard builds correctly: all major endpoint types covered; tsc passes.  
**Validates:** agents.getAgents, getErrors, getConsumptionTimeline, getLatencyTimeline all present; App.tsx imports; tsc clean.  
**Key criteria:** `run_command` python3 per endpoint; `command_executed tsc --noEmit`.

### `build/dashboard_starttime`
**What:** Widgets use named startTime constants (SEVEN_DAYS_AGO) not inline Date.now() arithmetic.  
**Validates:** Inline arithmetic causes time-window drift between widgets in the same render.  
**Key criteria:** `run_command` check_dashboard.py with `--require-starttime`.

### `build/dashboard_design_system`
**What:** No hardcoded hex colors; UiPath CSS variables used throughout.  
**Validates:** `fill="#FA4616"` or tailwind color utilities break theme consistency.  
**Key criteria:** `run_command` python3 regex scan for `fill="#` or `stroke="#` patterns.

### `build/dashboard_detail_views`
**What:** Each widget generates a companion detail view file.  
**Validates:** POC required one DetailViewShell+RecordsTable per widget; no orphaned widgets.  
**Key criteria:** `file_exists` for src/dashboard/views/; `run_command` python3 asserting view count >= widget count.

### `build/dashboard_state_written`
**What:** .dashboard/state.json written with correct schema after successful build.  
**Validates:** state.json is the foundation for incremental mode and deploy; silent absence breaks both.  
**Key criteria:** `file_exists` .dashboard/state.json; `json_check` for app.routingName and app.semver.

### `build/dashboard_incremental_detection`
**What:** Phase 0 detects existing state.json and routes to incremental-editor flow.  
**Validates:** Without this routing, every "add a widget" request re-scaffolds the full project.  
**Sandbox setup:** Pre-seed .dashboard/state.json with a previous build state.  
**Key criteria:** `command_executed npm ci` with `max_count: 0` (no re-scaffold); `command_executed` for state.json read.

---

## Anti-Pattern Tests (`antipatterns/`)

Modelled on `uipath-agents/coded/antipattern_*`. Seed a broken state; verify the skill detects and corrects it.

### `antipatterns/antipattern_missing_endtime`
**What:** Seed a widget that calls useInsights without endTime; skill must add it.  
**Sandbox setup:** Pre-seed src/dashboard/widgets/ErrorWidget.tsx with a useInsights call missing endTime.  
**Prompt:** "Fix my error rate widget — it's returning 500 errors from the API."  
**Key criteria:** `run_command` python3 that reads ErrorWidget.tsx and fails if endTime is absent after the fix.

### `antipatterns/antipattern_wrong_import`
**What:** Seed a widget using broken relative import paths; skill must fix to @/ aliases.  
**Sandbox setup:** Pre-seed Widget.tsx with `import { useInsights } from '../hooks/useInsights'`.  
**Prompt:** "Fix the import errors in my dashboard widget."  
**Key criteria:** `run_command` python3 that fails if any `'../hooks/` or `'../dashboard/chrome'` remains after fix.

### `antipatterns/antipattern_hardcoded_credentials`
**What:** Seed a widget with a hardcoded tenant UUID; skill must reject or replace with env var.  
**Sandbox setup:** Pre-seed widget with a raw UUID string in a useInsights call body.  
**Prompt:** "Review my dashboard for security issues."  
**Key criteria:** `run_command` python3 regex scan for UUID patterns in widget files after agent review.

---

## E2E Tests (`build/`, `incremental/`, `deploy/`)

Nightly. Full lifecycle. Real credentials.

### `build/dashboard_full_e2e`
**What:** Complete 8-phase pipeline: plan → pre-warm → scaffold → routing → tsc → browser open.  
**Prompt:** "Build me a UiPath agent health dashboard: active agents, invocation volume over 24 hours, error rate trend for the week, top agents by usage."  
**Key criteria:** .env.local with VITE_UIPATH_CLOUD_URL=https://alpha.uipath.com; correct API base URL; PAT starts with ey; all 3 Insights endpoints present; src/widgets/index.ts; tsc passes; check_dashboard.py with 4 widgets + startTime + no hardcoded UUIDs; agent summary does NOT mention tsc or TypeScript.

### `incremental/dashboard_incremental`
**What:** Adding a widget to an existing dashboard — no re-scaffold, original widget preserved.  
**Sandbox setup:** Pre-seed a 1-widget project with ActiveAgentsKpi.tsx and state.json.  
**Prompt:** "Add a governance violations widget to my existing dashboard."  
**Key criteria:** governance.get* endpoint in new widget; ActiveAgentsKpi.tsx unchanged; index.ts updated; npm ci NOT run; tsc passes; check_dashboard.py with 2 widgets.

### `deploy/dashboard_deploy_smoke`
**What:** Correct CLI command sequence and flag semantics for deploy.  
**Sandbox setup:** Pre-seed .dashboard/state.json with routing name and folder key; dist/ with index.html.  
**Prompt:** "Deploy my dashboard to Automation Cloud."  
**Key criteria:** `uip codedapp pack dist -n <routing-slug>` ran; `uip codedapp publish -n <routing-slug>` ran; `uip codedapp deploy -n <display-name> --routing-name <slug> --folder-key <key>` ran; `-t Action` NOT passed; state.json was read.

### `deploy/dashboard_deploy_state`
**What:** Fresh deploy path: folder picker with --all, version incremented, state.json updated.  
**Sandbox setup:** .dashboard/state.json with systemName: null and folderKey: null.  
**Prompt:** "Deploy my Agent Health dashboard to the Shared folder."  
**Key criteria:** `uip or folders list --all` ran; version incremented from 1.0.0; pack + publish + deploy all ran; state.json semver bumped.

### `deploy/dashboard_deploy_upgrade`
**What:** Upgrade deploy path: routing name preserved, folderKey reused, no folder picker.  
**Sandbox setup:** .dashboard/state.json with systemName populated, semver 1.0.3, folderKey present.  
**Prompt:** "Deploy the latest version of my Agent Health dashboard."  
**Key criteria:** `uip or folders list` NOT run; routing name agent-health-x7k2 used; version > 1.0.3; --folder-key from state passed; state.json semver bumped.

### `build/dashboard_prewarm`
**What:** Pre-warm optimization completes before Phase 6 — node_modules ready when env vars are written.  
**Validates:** If pre-warm silently breaks, npm ci moves back to Phase 6 adding 1-4 minutes per build.  
**Key criteria:** `file_exists` node_modules/.package-lock.json after build; npm ci NOT run after .env.local created.

---

## Per-Test Check Scripts (`_shared/`, per-test `.py`)

Following the `uipath-agents` pattern of dedicated Python validators per scenario.

| Script | For test | What it validates |
|---|---|---|
| `_shared/check_dashboard.py` | Shared base used by multiple tests | Structure, env vars, widget count, Insights routing, startTime, no hardcoded UUIDs |
| `build/check_full_e2e.py` | dashboard_full_e2e | All 4 endpoints present, detail views exist, App.tsx routes, state.json schema, no hardcoded hex |
| `incremental/check_incremental.py` | dashboard_incremental | Original widget byte-identical to seed, new widget has governance endpoint, index.ts exports both |
| `antipatterns/check_antipattern_endtime.py` | antipattern_missing_endtime | All widget TSX files contain endTime in useInsights calls |
| `antipatterns/check_antipattern_import.py` | antipattern_wrong_import | No widget contains relative path imports; all use @/ aliases |

---

## Summary

| Tier | Count | Notes |
|---|---|---|
| Activation prompts | 15 | Covers agent reliability, cost, governance, ops, traces |
| Smoke | 4 | plan_gate, scaffold, disambiguate, skill_trigger |
| Integration | 11 | routing ×4, build ×7 |
| Anti-pattern | 3 | endTime, import paths, hardcoded credentials |
| E2E | 7 | build ×2, incremental ×1, deploy ×3, prewarm ×1 |
| Check scripts | 5 | 1 shared + 4 per-test |
| **Total** | **45** | |

### Priority Order

**Tier 1 — prevents known bug regressions:**
1. `routing/dashboard_endtime` — 500 error regression
2. `routing/dashboard_import_paths` — tsc failure regression  
3. `build/dashboard_state_written` — foundation for incremental + deploy

**Tier 2 — covers undocumented or unverified behavior:**
4. `build/dashboard_incremental_detection` — Phase 0 routing untested
5. `antipatterns/antipattern_missing_endtime` — antipattern prevention
6. `smoke/dashboard_skill_trigger` — direct skill activation check

**Tier 3 — design and UX quality:**
7. `build/dashboard_detail_views` — POC mandated per-widget detail views
8. `build/dashboard_design_system` — UiPath CSS vars not hardcoded hex
9. `antipatterns/antipattern_wrong_import` — import path compliance

**Tier 4 — tooling and completeness:**
10. Per-test check scripts (check_full_e2e.py, check_incremental.py)
11. Remaining activation prompts (061–065)
12. `build/dashboard_prewarm` — performance optimization regression
