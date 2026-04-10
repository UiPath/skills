# Validation Report: `uipath-flow` Skill (v2)

> Date: 2026-04-10
> Branch: `tmatup/uipath_flow_skill`
> Skill: `skills/uipath-flow/` (merged from `uipath-maestro-flow` + `uipath-lattice-flow`)
> Framework: `coder_eval` at `/home/tmatup/root/coder_eval/`
> Eval commit: [`b8479c5`](https://github.com/UiPath/coder_eval/commit/b8479c53c692b4b9235b64d5232dfabb2ab1b0bb) — feat: add uipath-flow validation tasks (18 tasks, 4 tiers) (#135)

---

## Executive Summary

The unified `uipath-flow` skill passes validation across all testable phases. **16/16 new tasks pass (100%)** across JSON authoring regression, mode selection, CLI with skill injection, two-phase planning, and connector lifecycle. Both skill injection strategies (template_dir and Skill tool) produce correct agent behavior.

3 pre-existing e2e tasks from main had two issues: (1) missing `plugins` config causing "Unknown skill" errors, and (2) triple-nested validate paths. Both fixed. After fixes, all 3 produce valid flows (validate passes); their `flow debug` criterion remains failing due to a pre-existing design conflict (prompt says "don't debug" but criteria tests debug output).

---

## v2 Changes from v1

| Change | Detail |
|--------|--------|
| `=js:` prefix fix | Condition expressions (decision, switch, HTTP branch) no longer use `=js:`. Ported from maestro-flow commit `24c34d5`. |
| Dual injection strategy | JSON-only tasks use `template_dir`; CLI/mixed tasks use `Skill` tool at runtime |
| E2E tasks | 8 new e2e tasks discovered (from main), require `flow-e2e.yaml` experiment config |
| BellevueWeather | New regression test validates agent defaults to JSON authoring when no mode specified |
| Task prompt updates | CLI tasks now say "Before starting, load the uipath-flow skill" |

---

## Phase Results

### Phase 1: JSON Authoring Regression (7 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-json-add-decision | 2/2 | 1.000 | PASS |
| flow-json-remove-node | 2/2 | 1.000 | PASS |
| flow-json-dice-roller | 4/4 | 0.932 | PASS |
| flow-json-calculator | 4/4 | 0.932 | PASS |
| flow-json-loop | 3/3 | 1.000 | PASS |
| flow-json-scheduled | 3/3 | 1.000 | PASS |
| flow-json-decision | 3/3 | 1.000 | PASS |

### Phase 2: Mode Selection (3 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-mode-selection-cli | 3/3 | 1.000 | PASS |
| flow-mode-selection-json | 4/4 | 1.000 | PASS |
| flow-json-bellevue-weather | 5/5 | 1.000 | PASS |

**BellevueWeather (mode default regression):** Agent correctly defaulted to JSON authoring. Used Bash only for `ls`, `mkdir`, and `uip flow validate`. No `uip flow node add` or `uip flow edge add` used.

### Phase 3: CLI with Skill (2 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-cli-add-node | 4/4 | 1.000 | PASS |
| flow-cli-dice-roller | 4/4 | 1.000 | PASS |

### Phase 4: Planning (2 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-planning-arch | 5/5 | 1.000 | PASS |
| flow-planning-impl | 5/5 | 1.000 | PASS |

### Phase 5: Connectors (2 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-connector-discovery | 4/4 | 1.000 | PASS |
| flow-connector-configure | 4/4 | 1.000 | PASS |

### Phase 6: E2E OOTB (3 tasks — fixed and re-run)

Initial run failed 0/3 due to missing `plugins` config + triple-nested validate paths. After fixes:

| Task ID | Validate | Debug | Status |
|---------|----------|-------|--------|
| uipath-flow-bellevue-weather | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-calculator | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-dice-roller | 1.00 | 0.00 (expected) | PARTIAL PASS |

All 3 tasks now produce valid flows (criterion 1 passes). Criterion 2 (`flow debug`) fails because it requires runtime execution — a pre-existing design issue in these tasks from main, not a skill regression. The prompts say "Do NOT run flow debug" but the criteria test debug output.

---

## Root Cause Analysis: E2E Task Failures

All 3 failures share the same root cause: **missing `plugins` config**.

The e2e tasks are designed to be run with the `flow-e2e.yaml` experiment config, which provides the skill plugin:

```yaml
# experiments/flow-e2e.yaml
variants:
  - variant_id: with-skill
    agent:
      max_turns: 200
      plugins:
        - type: "local"
          path: "$UIPATH_PLUGIN_MARKETPLACE_DIR"
```

When run without the experiment config, `Skill('uipath-flow')` returns "Unknown skill: uipath-flow", causing agents to:
1. Fall back to scavenging reference files from other run directories
2. Bloat their context window with large JSON files
3. Hit max_turns or crash the Claude Code CLI

**Fixes applied:**
- Set `UIPATH_PLUGIN_MARKETPLACE_DIR=/home/tmatup/root/skills` in `.env` (repo root, not `skills/skills/` — the plugin.json at `.claude-plugin/plugin.json` resolves the `skills/` subdir)
- Fixed ALL 8 e2e validate commands: hardcoded triple-nested paths (`Name/Name/Name.flow`) → glob-based discovery (`glob.glob('**/Name*.flow')`)
- Correct invocation: `coder-eval run tasks/uipath_flow/e2e/*/*.yaml -e experiments/flow-e2e.yaml`

---

## Skill Changes Validated

### `=js:` prefix fix (7 files)

Ported from maestro-flow commit `24c34d5`. Condition expressions (decision `expression`, switch case `expression`, HTTP branch `conditionExpression`) must NOT use the `=js:` prefix — they evaluate as JS automatically. Only value expressions (output `source`, variable updates, HTTP inputs) use `=js:`.

Files updated:
- `SKILL.md` — Critical Rule 6
- `references/variables-guide.md` — expression docs, switch/HTTP examples
- `references/planning-guide.md` — decision condition example
- `references/cli/workflow-guide.md` — decision `--input` CLI example
- `references/json/authoring-guide.md` — decision expression JSON example
- `references/nodes/action-http.md` — 2 `conditionExpression` fields
- `assets/templates/http-flow-template.json` — 2 template `conditionExpression` fields

---

## Validation Matrix

| What | Tasks | Strategy | Auth | Result |
|------|-------|----------|------|--------|
| Mode selection (JSON explicit) | mode-selection-json | template_dir | No | PASS |
| Mode selection (CLI explicit) | mode-selection-cli | Skill tool | No | PASS |
| Mode default (no preference) | bellevue-weather | Skill tool | No | PASS |
| JSON: OOTB creation | json-dice-roller, json-calculator | template_dir | No | PASS |
| JSON: flow editing | json-add-decision, json-remove-node | template_dir | No | PASS |
| JSON: control flow | json-decision, json-loop, json-scheduled | template_dir | No | PASS |
| CLI: flow creation | cli-dice-roller | Skill tool | No | PASS |
| CLI: node editing | cli-add-node | Skill tool | No | PASS |
| Planning: Phase 1 | planning-arch | template_dir | No | PASS |
| Planning: Phase 2 | planning-impl | Skill tool | Yes | PASS |
| Connectors: discovery | connector-discovery | Skill tool | Yes | PASS |
| Connectors: configure | connector-configure | Skill tool | Yes | PASS |
| E2E: OOTB flows | e2e/bellevue_weather, calculator, dice_roller | Skill tool + experiment | Yes | PENDING |

---

## Not Yet Run

| Group | Tasks | Reason |
|-------|-------|--------|
| E2E: dynamic resources | e2e/api_workflow, coded_agent, lowcode_agent, rpa_project_euler | Requires auth + published resources |
| E2E: connector | e2e/slack_channel_description | Requires auth + Slack connection |
| Legacy CLI | registry, process, run_e2e, init_validate_pack | Pre-existing, picks up active plugin |
| Complexity | complexity-5/10/25/50/100 | Requires Skill plugin |
| Reference flows | devconnect-email, hr-onboarding, etc. | Requires Skill plugin |
