# Dashboard Capability — Test Plan

Complete list of tests for the `uipath-coded-apps` dashboard generation capability.
Status: ✅ exists · 🔲 to be created

Tests follow the three-tier pattern used across this repo:
- **Smoke** — PR-gate, ≤40 turns, validates basic correctness, no real API calls
- **Integration** — Daily, ≤200 turns, validates routing decisions and pattern compliance
- **E2E** — Nightly, ≤200 turns, full lifecycle with real credentials

---

## Activation (`tests/tasks/activation/uipath-coded-apps.jsonl`)

One-shot binary classifier: does the skill fire for dashboard prompts?
Run via `experiments/activation.yaml` (1 turn per prompt).

| ID | Prompt | Status |
|---|---|---|
| 051 | "build me an agent health dashboard" | ✅ |
| 052 | "create a dashboard showing agent error rates and latency" | ✅ |
| 053 | "I want to see invocation volume and success rate as a chart" | ✅ |
| 054 | "generate an analytics dashboard with KPIs for my agent fleet" | ✅ |
| 055 | "build a governance posture dashboard showing policy violations" | ✅ |
| 056 | "show me agent metrics — active count, P95 latency, top erroring agents" | ✅ |
| 057 | "I need an operations dashboard showing job completion trends" | ✅ |
| 058 | "create a cost dashboard tracking AGU consumption by agent" | ✅ |
| 059 | "build me a UiPath agent health dashboard: active agents, error rate trend" | ✅ |
| 060 | "add a governance violations widget to my existing dashboard" | ✅ |
| 061 | "I want a real-time view of how my agents are performing today" | 🔲 |
| 062 | "show me which agents are consuming the most resources this month" | 🔲 |
| 063 | "build a dashboard for the ops team to monitor agent health" | 🔲 |
| 064 | "I need a single view showing errors, latency, and usage for my fleet" | 🔲 |
| 065 | "add a memory usage chart to my existing monitoring dashboard" | 🔲 |

**Note:** Expand to 20+ prompts covering all dashboard types (agent reliability, cost/FinOps,
governance, traces/memory, jobs operations) to improve recall across diverse user language.

---

## Smoke Tests (`smoke/`)

PR-gate. Fast. No real API calls.

| File | What it tests | Status |
|---|---|---|
| `smoke/dashboard_plan_gate` | Agent shows plan before scaffolding; no npm ci before approval | ✅ |
| `smoke/dashboard_scaffold` | Scaffold produces correct structure: package.json, all 6 env vars, widgets/, useInsights in widgets | ✅ |
| `smoke/dashboard_disambiguate` | Ambiguous prompt halts and asks question; no scaffold before clarification | ✅ |
| `smoke/dashboard_skill_trigger` | `skill_triggered` criterion confirms the uipath-coded-apps skill activates (not another skill) | 🔲 |

### `dashboard_skill_trigger` (new)
**Why needed:** None of our YAML tests use the `skill_triggered` criterion. This directly
verifies the skill activates — distinct from activation prompts which only test routing.
```yaml
success_criteria:
  - type: skill_triggered
    skill_name: "uipath-coded-apps"
    expected: "yes"
    weight: 3.0
```

---

## Integration Tests (`routing/`, `build/`)

Daily. Verify specific decisions the agent must make correctly.

### Routing (`routing/`)

| File | What it tests | Status |
|---|---|---|
| `routing/dashboard_sdk_routing` | SDK-routed metrics (queue items, jobs, tasks) use SDK not Insights | ✅ |
| `routing/dashboard_insights_routing` | Insights-routed metrics use correct namespace (agents.getErrors, agents.getLatencyTimeline) | ✅ |
| `routing/dashboard_endtime` | Every useInsights call includes both startTime AND endTime (500 regression test) | 🔲 |
| `routing/dashboard_import_paths` | Generated widgets use @/ aliases (@/hooks/useInsights, @/dashboard/chrome) not relative paths | 🔲 |

### `dashboard_endtime` (new)
**Why needed:** Missing endTime causes 500 errors from Insights API. We fixed this bug but
have no regression test. Must verify generated widget code includes `endTime: NOW`.
```yaml
success_criteria:
  - type: run_command
    command: >
      python3 -c "import os,sys; d='src/widgets';
      files=[f for f in os.listdir(d) if f.endswith('.tsx')];
      fails=[f for f in files if 'endTime' not in open(os.path.join(d,f)).read()];
      sys.exit(1 if fails else 0)"
```

### `dashboard_import_paths` (new)
**Why needed:** `'../hooks/useInsights'` from `src/dashboard/widgets/` resolves to
non-existent `src/dashboard/hooks/`. This was a real bug that caused tsc failures on every
build. Prevents regression.
```yaml
success_criteria:
  - type: run_command
    command: >
      python3 -c "import os,sys; d='src/widgets';
      files=[f for f in os.listdir(d) if f.endswith('.tsx')];
      # Bad pattern: relative path that resolves wrong
      bad=[f for f in files if \"'../hooks/\" in open(os.path.join(d,f)).read() or \"'../dashboard/chrome'\" in open(os.path.join(d,f)).read()];
      sys.exit(1 if bad else 0)"
```

### Build (`build/`)

| File | What it tests | Status |
|---|---|---|
| `build/dashboard_recipe_usage` | Correct endpoints from catalog recipes, typed response interfaces | ✅ |
| `build/dashboard_multiwidget` | 5-widget build: all endpoints present, App.tsx imports, tsc passes | ✅ |
| `build/dashboard_starttime` | Named constants (SEVEN_DAYS_AGO) used, not inline Date.now() arithmetic | ✅ |
| `build/dashboard_design_system` | No hardcoded hex colors; UiPath CSS vars used (hsl(var(--chart-1)) etc.) | 🔲 |
| `build/dashboard_detail_views` | Each widget generates a companion detail view with DetailViewShell + RecordsTable | 🔲 |
| `build/dashboard_state_written` | .dashboard/state.json written with correct schema after successful build | 🔲 |
| `build/dashboard_incremental_detection` | Phase 0 detects existing state.json and routes to incremental-editor flow | 🔲 |

### `dashboard_design_system` (new)
**Why needed:** Agents may use hardcoded hex (#FA4616) or Tailwind colors (orange-500)
instead of UiPath CSS variables. This breaks theme consistency and dark mode readiness.
```yaml
success_criteria:
  - type: run_command
    command: >
      python3 -c "import os,re,sys; d='src/widgets';
      files=[open(os.path.join(d,f)).read() for f in os.listdir(d) if f.endswith('.tsx')];
      # Reject any hardcoded hex or tailwind color class in chart fills
      bad=[c for c in files if re.search(r'fill=\"#[0-9a-fA-F]{3,6}\"', c)];
      sys.exit(1 if bad else 0)"
```

### `dashboard_detail_views` (new)
**Why needed:** The POC had mandatory detail views per widget (click tile → DrilldownShell +
RecordsTable). We document this in Phase 7 but have no test that verifies generation.
```yaml
success_criteria:
  - type: file_exists
    path: "src/dashboard/views"
  - type: run_command
    command: >
      python3 -c "import os,sys;
      widgets=len([f for f in os.listdir('src/dashboard/widgets') if f.endswith('.tsx')]);
      views=len([f for f in os.listdir('src/dashboard/views') if f.endswith('.tsx')]);
      sys.exit(0 if views >= widgets else 1)"
```

### `dashboard_state_written` (new)
**Why needed:** state.json is the foundation for incremental mode and deploy — if it's not
written after build, both downstream capabilities break silently.
```yaml
success_criteria:
  - type: file_exists
    path: ".dashboard/state.json"
    weight: 3.0
  - type: json_check
    path: ".dashboard/state.json"
    assertions:
      - expression: "app.routingName"
        operator: "contains"
        expected: "-"     # has the suffix added by routing name derivation
      - expression: "app.semver"
        operator: "equals"
        expected: "1.0.0"
```

### `dashboard_incremental_detection` (new)
**Why needed:** Phase 0 checks for `.dashboard/state.json` and routes to incremental mode.
Without a test, this routing could silently break — every subsequent build would treat an
existing dashboard as fresh, re-scaffolding the whole project.
```yaml
sandbox:
  setup: |
    mkdir -p .dashboard
    echo '{"app":{"name":"X","routingName":"x-abc1","semver":"1.0.0"},"widgets":["ActiveAgentsKPI"],"deployment":{"systemName":null}}' > .dashboard/state.json
initial_prompt: "Add a P95 latency widget to my dashboard."
success_criteria:
  # Agent must NOT run full scaffold (no npm ci for incremental)
  - type: command_executed
    command_pattern: 'npm\s+ci'
    min_count: 0
    max_count: 0
    weight: 3.0
  # Agent must read state.json
  - type: command_executed
    command_pattern: 'state\.json'
    min_count: 1
    weight: 2.0
```

---

## Anti-Pattern Tests (`antipatterns/`)

Modeled after `uipath-agents/coded/antipattern_*`. Seed a broken state; verify the skill
detects and fixes it.

| File | What it tests | Status |
|---|---|---|
| `antipatterns/antipattern_missing_endtime` | Seed widget without endTime; skill must add it before claiming success | 🔲 |
| `antipatterns/antipattern_wrong_import` | Seed widget with `'../hooks/useInsights'`; skill must fix to `'@/hooks/useInsights'` | 🔲 |
| `antipatterns/antipattern_hardcoded_credentials` | Seed widget with hardcoded tenant UUID; skill must reject or replace with env var | 🔲 |

### `antipattern_missing_endtime` (new)
```yaml
sandbox:
  setup: |
    # Pre-seed a widget that calls useInsights without endTime
    mkdir -p src/dashboard/widgets
    cat > src/dashboard/widgets/ErrorWidget.tsx << 'EOF'
    import { useInsights } from '@/hooks/useInsights'
    export function ErrorWidget() {
      const { data } = useInsights('agents.getErrors', { startTime: SEVEN_DAYS_AGO })
      return <div>{JSON.stringify(data)}</div>
    }
    EOF
initial_prompt: "Fix my error rate widget — it's returning 500 errors from the API."
success_criteria:
  - type: run_command
    command: >
      python3 -c "import sys; c=open('src/dashboard/widgets/ErrorWidget.tsx').read();
      sys.exit(0 if 'endTime' in c else 1)"
    weight: 4.0
```

### `antipattern_wrong_import` (new)
```yaml
sandbox:
  setup: |
    mkdir -p src/dashboard/widgets
    cat > src/dashboard/widgets/Widget.tsx << 'EOF'
    import { useInsights } from '../hooks/useInsights'  // WRONG: relative path
    import { DeltaBadge } from '../dashboard/chrome'     // WRONG: double-nested
    export function Widget() { return <div /> }
    EOF
initial_prompt: "Fix the import errors in my dashboard widget."
success_criteria:
  - type: run_command
    command: >
      python3 -c "import sys; c=open('src/dashboard/widgets/Widget.tsx').read();
      bad=\"'../hooks/\" in c or \"'../dashboard/chrome'\" in c;
      sys.exit(1 if bad else 0)"
    weight: 5.0
```

---

## E2E Tests (`build/`, `incremental/`, `deploy/`)

Nightly. Full lifecycle. Real credentials.

| File | What it tests | Status |
|---|---|---|
| `build/dashboard_full_e2e` | Complete 8-phase pipeline: plan→scaffold→routing→tsc→browser open | ✅ |
| `incremental/dashboard_incremental` | Add widget to existing dashboard; no re-scaffold; original widget preserved | ✅ |
| `deploy/dashboard_deploy_smoke` | Pack→publish→deploy CLI command sequence; correct -n flag semantics; no -t Action | ✅ |
| `deploy/dashboard_deploy_state` | Fresh deploy: folder picker with --all, version bump, state.json written | ✅ |
| `deploy/dashboard_deploy_upgrade` | Upgrade: routing name preserved, folderKey from state, semver incremented | ✅ |
| `build/dashboard_prewarm` | Pre-warm completes before Phase 6: node_modules present before .env.local write | 🔲 |
| `build/dashboard_no_code_in_chat` | Agent produces zero text output between plan approval and final summary | 🔲 |

### `dashboard_prewarm` (new)
**Why needed:** The pre-warm optimization (Phase 3.5) is the biggest performance lever.
If it silently stops working, npm ci moves back to Phase 6 adding 1-4 minutes.
```yaml
success_criteria:
  # node_modules must exist by the time .env.local is written
  - type: run_command
    command: >
      node -e "const fs=require('fs');
      const nm=fs.existsSync('node_modules/.package-lock.json');
      const env=fs.existsSync('.env.local');
      process.exit(nm && env ? 0 : 1)"
    weight: 3.0
  # npm ci must NOT have run after .env.local was written (pre-warm already did it)
  # (verified by checking timestamps, or by the fact that it ran in background)
  - type: file_exists
    path: "node_modules/.package-lock.json"
    weight: 2.0
```

### `dashboard_no_code_in_chat` (new)
**Why needed:** The Blackout Rule requires zero text output between approval and summary.
Agents sometimes narrate ("I'm now writing the widgets...") despite the rule. This tests
compliance.
```yaml
success_criteria:
  # Agent response between approval and summary must not mention technical terms
  - type: run_command
    command: >
      node -e "process.exit(0)"  # placeholder — actual check via transcript analysis
    weight: 2.0
  # Final summary must not contain TypeScript, tsc, package.json, or file paths
  - type: run_command
    command: >
      node -e "process.exit(0)"  # placeholder — actual check via transcript analysis
    weight: 2.0
```
> **Note:** Implementing this requires transcript access. Use `llm_judge` criterion once
> the transcript capture feature is stable in coder-eval.

---

## Per-Test Check Scripts

Following the `uipath-agents` pattern of per-test `.py` validators (not just a shared
validator). Each E2E test should have its own check script that validates the specific
scenario's artifacts in depth.

| Script | For test | Status |
|---|---|---|
| `_shared/check_dashboard.py` | Shared base: structure, env vars, widget count, routing, startTime | ✅ |
| `build/check_full_e2e.py` | Deep validation: all 4 widget endpoints, detail views, App.tsx routes, state.json schema | 🔲 |
| `incremental/check_incremental.py` | Existing widget preserved verbatim, new widget has correct endpoint, index.ts updated | 🔲 |
| `antipatterns/check_antipattern_endtime.py` | All widgets have endTime in API calls | 🔲 |
| `antipatterns/check_antipattern_import.py` | All imports use @/ alias, no relative paths | 🔲 |

---

## Summary

### By Status

| Tier | Existing | To Create | Total |
|---|---|---|---|
| Activation prompts | 10 | 5 | 15 |
| Smoke | 3 | 1 | 4 |
| Integration | 5 | 6 | 11 |
| Anti-pattern | 0 | 3 | 3 |
| E2E (build) | 1 | 2 | 3 |
| E2E (incremental) | 1 | 0 | 1 |
| E2E (deploy) | 3 | 0 | 3 |
| Check scripts | 1 | 5 | 6 |
| **Total** | **24** | **22** | **46** |

### By Priority

**High (prevents regressions of known bugs):**
1. `routing/dashboard_endtime` — 500 error regression test (fixed but untested)
2. `routing/dashboard_import_paths` — import path regression (was causing tsc failure on every build)
3. `build/dashboard_state_written` — state.json is foundation for incremental + deploy

**High (covers undocumented behavior):**
4. `build/dashboard_incremental_detection` — Phase 0 routing untested
5. `antipatterns/antipattern_missing_endtime` — antipattern prevention
6. `smoke/dashboard_skill_trigger` — direct skill activation verification

**Medium (design quality):**
7. `build/dashboard_detail_views` — POC had mandatory detail views per widget
8. `build/dashboard_design_system` — UiPath CSS vars not hardcoded hex
9. `antipatterns/antipattern_wrong_import` — import path antipattern

**Medium (tooling quality):**
10. `build/check_full_e2e.py` — per-test deep validator
11. `incremental/check_incremental.py` — per-test deep validator
12. Remaining activation prompts (11–15)

**Low (nice-to-have):**
13. `build/dashboard_prewarm` — performance optimization test
14. `build/dashboard_no_code_in_chat` — UX compliance test (needs transcript access)
15. `antipatterns/antipattern_hardcoded_credentials` — security antipattern
