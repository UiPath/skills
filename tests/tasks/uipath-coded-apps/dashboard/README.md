# Dashboard Capability — Test Suite

Tests for the `uipath-coded-apps` dashboard generation capability. The skill generates
production-ready React dashboards from natural-language prompts using the UiPath Insights
RTM API and TypeScript SDK.

## How to Run

```bash
cd tests

# All dashboard tests (default experiment — dev/local)
make test-uipath-coded-apps

# By tier
make tags TAGS="uipath-coded-apps smoke"        # PR-gate (fast, ~40 turns)
make tags TAGS="uipath-coded-apps integration"  # Daily
make tags TAGS="uipath-coded-apps e2e"          # Nightly (full lifecycle)

# Single test
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run tasks/uipath-coded-apps/dashboard/smoke/dashboard_scaffold.yaml \
  -e experiments/default.yaml
```

## Test Architecture

### Shared validator: `_shared/check_dashboard.py`

A reusable Python script called via `run_command` criteria. Validates project structure,
env vars, widget count, Insights routing, startTime constants, and absence of hardcoded
UUIDs — without running tsc (use `--no-tsc` for integration tests).

```
--min-widgets N        At least N .tsx files in src/widgets/
--require-insights     At least one widget imports useInsights
--require-sdk          At least one widget uses SDK (QueueItems, Jobs.getAll, etc.)
--require-recipe ENDPOINT  At least one widget references this endpoint string
--require-starttime    Widgets use named constants (SEVEN_DAYS_AGO) not inline Date.now()
--no-tsc               Skip tsc --noEmit (used when node_modules may not be present)
```

### Incremental test template: `incremental/templates/existing_dashboard/`

A pre-built 1-widget scaffold used as `sandbox.template_sources` for the incremental test.
Contains a working `ActiveAgentsKpi.tsx` widget and `index.ts` export so the incremental
test starts from a known state.

---

## Activation Prompts

Defined in `tests/tasks/activation/uipath-coded-apps.jsonl` (rows 051–060).

These measure whether the skill fires correctly on dashboard-related prompts.
Run with `tests/experiments/activation.yaml` (1-turn binary classifier).

| Prompt | Expected |
|--------|----------|
| "build me an agent health dashboard" | `uipath-coded-apps` |
| "create a dashboard showing agent error rates and latency" | `uipath-coded-apps` |
| "show me agent metrics — active count, P95 latency, top erroring agents" | `uipath-coded-apps` |
| "generate an analytics dashboard with KPIs for my agent fleet" | `uipath-coded-apps` |
| "build a governance posture dashboard showing policy violations" | `uipath-coded-apps` |
| "I want to see invocation volume and success rate as a chart" | `uipath-coded-apps` |
| "I need an operations dashboard showing job completion trends" | `uipath-coded-apps` |
| "create a cost dashboard tracking AGU consumption by agent" | `uipath-coded-apps` |
| "build me a UiPath agent health dashboard: active agents, error rate trend" | `uipath-coded-apps` |
| "add a governance violations widget to my existing dashboard" | `uipath-coded-apps` |

---

## Smoke Tests (`smoke/`)

Run on every PR. Fast (≤40 turns, 900s). No real API calls — validates structure and
agent behavior only.

### `dashboard_plan_gate`
**What it tests:** The approval gate — agent must show a plan before building anything.

**What passes:**
- `npm ci` was NOT run before the user approved (max_count: 0)
- Agent produces no scaffold files before approval

**Why it matters:** Without this, agents scaffold immediately on any dashboard-related
prompt, ignoring the plan→approve workflow that prevents misbuilt dashboards.

---

### `dashboard_scaffold`
**What it tests:** Core scaffold correctness — all required files and env vars are written.

**What passes:**
- `package.json` and `.env.local` exist
- All 6 env vars present: `VITE_UIPATH_CLOUD_URL`, `VITE_UIPATH_BASE_URL`, `VITE_UIPATH_ORG_NAME`, `VITE_UIPATH_TENANT_NAME`, `VITE_INSIGHTS_TENANT_ID`, `VITE_UIPATH_PAT`
- `src/widgets/` directory and `index.ts` exist
- At least one widget uses `useInsights`
- `npm ci` ran (scaffold executed)
- `App.tsx` imports from widgets

**Why it matters:** Catches regressions in scaffold creation, missing env vars, or broken
PAT auth — all of which produce broken dashboards at runtime.

---

### `dashboard_disambiguate`
**What it tests:** Ambiguous prompts halt before building and ask a clarifying question.

**What passes:**
- `npm ci` NOT run (no scaffold before disambiguation)
- `package.json` NOT created

**Why it matters:** Without disambiguation, a prompt like "I need something to track
performance" scaffolds arbitrarily. The approval gate depends on the agent asking first.

---

## Integration Tests (`routing/`, `build/`)

Run daily. Verify correct routing decisions and widget generation patterns.

### `dashboard_sdk_routing`
**What it tests:** SDK-routed metrics use SDK, not Insights.

**Prompt:** Queue items, running jobs, pending Action Center tasks

**What passes:**
- Queue widget: `QueueItems` present in widgets
- Jobs widget: `Jobs.getAll` or `jobs.getAll` pattern
- Tasks widget: `Tasks.getAll` or `tasks.getAll` pattern
- No widget uses `jobs.getCompletedTimeline`, `jobs.getSummary`, or similar Insights jobs endpoints for these operational metrics

**Why it matters:** Routing operational state (live counts, current status) to Insights
instead of SDK produces wrong data — Insights is for historical aggregates, not live state.

---

### `dashboard_insights_routing`
**What it tests:** Insights-routed metrics use the correct namespace and endpoint.

**Prompt:** Agent error trend, P95 latency per agent, top agents by error count

**What passes:**
- Error trend widget: `agents.getErrors` endpoint
- Latency widget: `agents.getLatencyTimeline` endpoint
- Top agents widget: `agents.getTopErroredAgents` endpoint
- All three use `useInsights` (not raw fetch)
- check_dashboard.py validates structure + Insights routing

**Why it matters:** Wrong endpoint (e.g., `traceview.getLatencyTimeline` instead of
`agents.getLatencyTimeline`) returns different data shapes and causes runtime errors.

---

### `dashboard_recipe_usage`
**What it tests:** The agent uses Widget Recipes from `insights-catalog.md` rather
than inventing custom patterns.

**Prompt:** Error trend (7 days), active agent count (KPI), top agents by AGU consumption (bar)

**What passes:**
- Error trend: `agents.getErrors` endpoint (Recipe 1)
- Active agents KPI: `agents.getAgents` endpoint (Recipe 3)
- Consumption bar: `agents.getConsumption` endpoint (Recipe 10)
- Widgets include TypeScript response type annotations (`useInsights<{...}>` generic)

**Why it matters:** Without recipes, agents invent arbitrary data shapes that produce
`(data as any)?.data?.wrong?.path ?? []` — silently empty charts at runtime.

---

### `dashboard_multiwidget`
**What it tests:** A 5-widget dashboard builds correctly end-to-end with all major
endpoint types covered.

**Prompt:** Active agents (KPI), error trend (line), invocation activity (area),
P95 latency (line), top agents (table)

**What passes:**
- 5 widget files in `src/widgets/`
- `agents.getAgents`, `agents.getErrors`, `agents.getConsumptionTimeline`, `agents.getLatencyTimeline` all present
- `App.tsx` imports from widgets
- `tsc --noEmit` passes

**Why it matters:** Per-widget correctness doesn't guarantee the full project compiles.
This test catches type errors that emerge only when all widgets are combined.

---

### `dashboard_starttime`
**What it tests:** Widgets use named `startTime` constants, not inline `Date.now()` arithmetic.

**Prompt:** Agent error trend (7 days) and agent success rate (30 days)

**What passes:**
- At least one widget uses `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, or a clearly named `const *Ago` variable
- No widget passes `Date.now()` subtraction directly into `useInsights`
- check_dashboard.py `--require-starttime` passes

**Why it matters:** Inline `Date.now() - 604800000` in each widget causes time windows
to drift by seconds between widget renders. Named constants ensure all widgets share
the same query window.

---

## E2E Tests (`build/`, `incremental/`)

Run nightly. Full lifecycle, real credentials, complete pipeline.

### `dashboard_full_e2e`
**What it tests:** The complete 8-phase build pipeline — plan → scaffold → routing →
widget generation → tsc → browser open.

**Prompt:** "Build me a UiPath agent health dashboard: active agents, invocation volume
over 24 hours, error rate trend for the week, and top agents by usage with health scores."

**What passes:**
- `package.json` created
- `.env.local` with correct `VITE_UIPATH_CLOUD_URL` (alpha.uipath.com, not api.uipath.com)
- `.env.local` with `VITE_UIPATH_BASE_URL` matching `.*api\.uipath\.com`
- `VITE_UIPATH_PAT` starts with `ey` (valid JWT token from uip login)
- `agents.getAgents`, `agents.getConsumptionTimeline`, `agents.getErrors` all in widgets
- `src/widgets/index.ts` exports present
- `App.tsx` includes `DashboardShell`
- `tsc --noEmit` passes
- check_dashboard.py: 4 widgets, Insights routing, startTime constants, no hardcoded UUIDs
- Agent final summary does NOT mention `tsc`, `TypeScript`, or `package.json`

**Why it matters:** This is the primary regression gate for the full dashboard capability.
Any breakage in auth, scaffold, routing, or TypeScript compilation is caught here.

---

### `dashboard_incremental`
**What it tests:** Adding a widget to an existing dashboard only writes the new widget —
no re-scaffolding, no overwriting existing widgets.

**Setup:** Pre-seeded project with one existing widget (`ActiveAgentsKpi.tsx`) via
`sandbox.template_sources`.

**Prompt:** "Add a widget to my existing dashboard showing governance violations
over the last 30 days."

**What passes:**
- New governance widget created in `src/widgets/`
- New widget uses `governance.get*` endpoint
- `ActiveAgentsKpi.tsx` still exists and still contains `agents.getAgents`
- `index.ts` still exports `ActiveAgentsKpi`
- `npm ci` NOT run again (no full re-scaffold)
- `tsc --noEmit` passes
- check_dashboard.py: 2 widgets, Insights routing, no hardcoded UUIDs

**Why it matters:** Without incremental mode, every "add a widget" request re-scaffolds
the entire project, wiping user customizations and taking 2-5 minutes unnecessarily.

---

## Test Coverage Map

| Capability | Test | Tier |
|---|---|---|
| Plan shown before scaffold | `dashboard_plan_gate` | smoke |
| Plan rendered before confirmation question | `dashboard_plan_before_question` | smoke |
| Scaffold creates correct structure | `dashboard_scaffold` | smoke |
| Ambiguous prompt asks question | `dashboard_disambiguate` | smoke |
| SDK signals → SDK endpoints | `dashboard_sdk_routing` | integration |
| Insights signals → correct namespace | `dashboard_insights_routing` | integration |
| Widget recipes used correctly | `dashboard_recipe_usage` | integration |
| 5-widget build compiles cleanly | `dashboard_multiwidget` | integration |
| startTime constants not inline math | `dashboard_starttime` | integration |
| Full 8-phase pipeline end-to-end | `dashboard_full_e2e` | e2e |
| Incremental widget add | `dashboard_incremental` | e2e |
| Deploy CLI commands in correct order | `dashboard_deploy_smoke` | smoke |
| Fresh deploy: folder picker + state write | `dashboard_deploy_state` | integration |
| Upgrade deploy: routing name preserved + version bump | `dashboard_deploy_upgrade` | integration |
| Skill triggers on dashboard prompts | activation prompts 051–060 | activation |

---

## Deploy Tests (`deploy/`)

These tests validate the deploy pipeline documented in `plugins/deploy/impl.md`.
Commands are run against the real CLI but will fail with auth errors in CI — what's
tested is that the agent runs the **correct commands with the correct flags**.

### `dashboard_deploy_smoke`
**What it tests:** Correct CLI command sequence and flag usage for deploy.

**Setup:** Pre-seeded `state.json` with routing name and folder key already resolved.

**What passes:**
- `uip codedapp pack dist -n <routing-slug> -v <semver>` ran
- `uip codedapp publish -n <routing-slug> -v <semver>` ran
- `uip codedapp deploy -n <display-name> --routing-name <slug> --folder-key <key>` ran
- `-t Action` was NOT passed (dashboards are Web apps)
- state.json was read before deploying

**Why it matters:** The `-n` flag means different things on pack/publish (routing slug)
vs deploy (display name). Using it wrong deploys under the wrong name or fails silently.
`-t Action` is a governance-portal specific flag that breaks Web app deploys.

---

### `dashboard_deploy_state`
**What it tests:** Fresh deploy path — folder picker runs when `folderKey` is null,
version is incremented from state.json, and state.json is updated after deploy.

**Setup:** `state.json` with `systemName: null` and `folderKey: null` (never deployed).

**What passes:**
- `uip or folders list --all` ran (required for folder resolution, `--all` bypasses 50-item cap)
- Version incremented from `1.0.0` to `1.0.1` or higher
- pack → publish → deploy all ran
- `state.json.app.semver` bumped after deploy

**Why it matters:** `--all` is required for folder list — without it the 50-item default
cap may hide the target folder. Version must be bumped to avoid publish 409 conflicts.

---

### `dashboard_deploy_upgrade`
**What it tests:** Upgrade deploy path — existing `systemName` means no folder picker,
existing `routingName` is preserved, existing `folderKey` is reused.

**Setup:** `state.json` with `systemName: "govdash-agent-health-x7k2"`, `semver: "1.0.3"`,
`folderKey: "abc123-folder-key"` (previously deployed).

**What passes:**
- `uip or folders list` NOT run (folderKey already known)
- Existing routing name `agent-health-x7k2` used throughout
- Version incremented past `1.0.3`
- `--folder-key abc123-folder-key` passed to deploy
- `state.json.app.semver` bumped after deploy

**Why it matters:** On upgrades, re-running folder picker is unnecessary and confusing.
Reusing the routing name ensures the update lands on the correct existing deployment.

---

## Validating interaction-flow changes (required before shipping)

Any change to the skill's **interaction flow** — question wording/structure, plan
format, approval gates, event-to-output mapping — must be validated BEFORE it ships:

1. Add or update a smoke task in `smoke/` that pins the interaction invariant
   (e.g. `dashboard_plan_before_question` pins "structured question asked, nothing
   built before approval"). If the invariant is about assistant text ordering
   (criteria can't assert that), state it in the task description so the LLM
   reviewer checks the transcript for it.
2. Run the smoke tier locally: `make tags TAGS="uipath-coded-apps smoke"`.
3. Only then merge the doc/script change.

This exists because a question-tool change shipped without a flow test and the
confirmation question fired before the plan was rendered — the user was asked to
approve a dashboard they had never seen.

## Known Limitations

- Tests do not make live Insights API or Automation Cloud deploy calls — correctness
  is verified through command invocations, flag usage, and state.json mutations
- The incremental test uses a pre-seeded template, not a real previously-built dashboard
- Routing-name collision retry and publish transient-error retry logic are not directly
  testable in CI (requires a real conflicting deployment to trigger)
