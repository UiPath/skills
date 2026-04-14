# UiPath Skills Test Coverage Report

Analyze what a skill teaches vs what its tests verify. Produce a gap analysis with prioritized recommendations.

**Input:** `$ARGUMENTS`
- Skill name or path (e.g., `uipath-maestro-flow`) — single skill.
- Empty or `all` — every skill under `skills/`.

**Output:** Markdown report(s) in `tests/reports/<skill-name>.md` (e.g., `tests/reports/uipath-maestro-flow.md`), unless the user specifies a different path. Overwrite existing reports at the same path.

---

## Phase 1 — Discovery

1. Resolve target skill(s). Single name → `skills/<name>/`. Empty/all → glob `skills/uipath-*/`.
2. For each skill, check for `tests/tasks/<skill-name>/`.
3. Find `*.yaml` test files recursively under each test directory. Exclude `_shared/`.
4. Find `check_*.py` scripts recursively. Exclude `_shared/test_*.py` (unit tests for shared helpers).

For multi-skill runs, use parallel Explore agents — one per skill — to read skill + test content simultaneously.

## Phase 2 — Extract the skill's capability inventory

Read the skill's **SKILL.md and every file in `references/` and `assets/`**. Skills vary widely in structure — adapt extraction to what you find.

### 2a. Identify components

Components are the specific, testable units the skill teaches. What counts as a "component" depends on the skill's domain:

| Skill domain | Component examples |
|---|---|
| Flow orchestration (`uipath-maestro-flow`) | Node types: `core.action.script`, `core.logic.decision`, `uipath.connector.*`, etc. Find these in SKILL.md Plugin Index tables and `references/plugins/*/planning.md` files. |
| RPA workflows (`uipath-rpa`) | Workflow modes (Coded C#, XAML), activity types, project types. Found in section headings like "Coded Workflows Quick Reference", "XAML Workflows Quick Reference". |
| Platform operations (`uipath-platform`) | CLI command groups (`uip orchestrator`, `uip solution`, `uip is`), API domains. Found in "CLI Overview" command tables and Task Navigation. |
| Agent development (`uipath-agents`) | Lifecycle stages (Auth, Setup, Build, Bindings, Run, Deploy), framework types (LangGraph, LlamaIndex, etc.). Found in "Lifecycle Stages" section. |
| Desktop/browser automation (`uipath-servo`) | Command categories (Discover, Interact, Inspect, Manage), input methods, framework types. Found in "Commands" section hierarchy. |
| Coded apps (`uipath-coded-apps`) | Pipeline stages (Push, Pull, Pack, Publish, Deploy), app configuration concepts. Found in lifecycle and "Ship It" sections. |

Group components by category. For skills with `references/plugins/` subdirectories (like `uipath-maestro-flow`), each plugin directory is one component — use the planning.md to understand what it covers.

### 2b. Identify workflow steps

Look for these section patterns (skills use different names):
- `## Quick Start` with `### Step N — Title` subsections
- `## Lifecycle Stages` with stage names
- `## One-Prompt Flow` with numbered steps
- `## Ship It` with pipeline steps
- Numbered steps inside any major workflow section

Extract the step name and what it does. Some skills have sub-steps (e.g., `Step 2a`, `Step 2b`); count the major steps, note sub-steps.

### 2c. Extract critical rules

Look for a `## Critical Rules` section. Format varies:
- **Numbered list with bold titles** (e.g., `1. **Rule Title** — explanation`)
- **Grouped by subsection** (e.g., "Common Rules", "Coded-Specific Rules")
- **Implicit rules** scattered in other sections (mark these separately)

Record each rule's number and a short summary (under 15 words).

### 2d. Extract anti-patterns

Look for `## Anti-Patterns` or `## What NOT to Do` sections **in SKILL.md only**. Do not count items from reference files — those are implementation details, not skill-level anti-patterns. Format varies:
- **Bulleted list with bold names** (e.g., `- **Never guess node schemas** — explanation`)
- **Numbered list**
- Some skills have zero anti-patterns

Record each item with a short summary.

### 2e. Identify infrastructure dependencies

Determine what environment each skill requires to be testable:
- **Local-only** — Can run without cloud auth or special hardware (e.g., flow validate, solution bundle)
- **Cloud auth required** — Needs UiPath tenant authentication (e.g., platform ops, flow debug, deploy)
- **Platform-specific** — Needs Windows, Studio Desktop, Servo CLI, display, browser extension, etc.

Tag each skill with its dependencies. This informs which tests are feasible to write and run in CI.

## Phase 3 — Extract test coverage

### 3a. Parse each test YAML

Extract these fields:

```
task_id         — unique test identifier (e.g., "skill-flow-calculator")
description     — what the test validates
tags            — array; first element = skill name, second = test type (smoke/integration/e2e)
initial_prompt  — the prompt given to the agent
success_criteria — array of assertion objects
```

For each `success_criteria` entry, record by type:

| Type | Key fields | What it proves |
|---|---|---|
| `command_executed` | `command_pattern` (regex), `min_count`, `tool_name` | Agent ran a specific CLI command |
| `file_exists` | `path` | Agent created a specific file |
| `file_contains` | `path`, `includes` (string array) | File contains expected strings |
| `json_check` | `path`, `assertions` (array of `{expression, operator, expected}`) | JSON structure is correct |
| `run_command` | `command` (shell command), `expected_exit_code`, `timeout` | Arbitrary check passes (often a Python check script) |

### 3b. Parse check scripts

When a `run_command` criterion runs a `check_*.py` script, read it and extract:

- **Node type assertions** — calls to `assert_flow_has_node_type(["type.name"])`. This proves a specific node was used (not hardcoded).
- **Output value assertions** — calls to `assert_output_value(payload, EXPECTED)`, `assert_output_int_in_range(payload, lo, hi)`, `assert_outputs_contain(payload, needles, require_all=True|False)`.
- **Input injection** — calls to `read_flow_input_vars()` + `run_debug(inputs={...})`. This proves the flow uses input variables correctly.
- **Other checks** — any additional `sys.exit("FAIL: ...")` conditions.

Example: `check_calculator_flow.py` asserts `core.action.script` node exists, injects inputs (17, 23), and checks output equals 391. This means the test directly covers: script node, input variables, output variables, flow debug.

### 3c. Map tests to capabilities

For each test, produce a coverage list using three tiers:

- **Direct** — The test explicitly checks for this capability. Examples:
  - `command_executed` with pattern `uip\s+flow\s+validate` → directly covers "flow validate" step
  - `assert_flow_has_node_type(["core.action.http"])` → directly covers HTTP node
  - `json_check` with assertion on `validation_passed` → directly covers validation output

- **Indirect** — The test would fail without this capability, but doesn't assert it by name. Examples:
  - Every flow needs `core.control.end` and `core.trigger.manual`, but no test calls `assert_flow_has_node_type(["core.control.end"])`
  - Building any flow requires `definitions` entries (Critical Rule 7), but no test checks the definitions array
  - Decision-based flows require `=js:` expressions (Critical Rule 13), but no test checks expression syntax

- **None** — No test exercises this capability, even indirectly.

## Phase 4 — Score

### 4a. Component coverage

Count: `(Direct + Indirect) / Total`. Report Direct and Indirect separately in the table.

### 4b. Workflow step coverage

A step is "tested" if at least one test exercises the CLI commands or file operations it describes.

### 4c. Critical rule coverage

A rule is "Direct" if a test would catch its violation. A rule is "Indirect" if following the rule is necessary but not checked. Example: Rule 4 ("always use `--output json`") is directly tested by `init_validate.yaml`'s `command_pattern: 'uip\s+.*--output\s+json'`. Rule 7 ("every node needs a definitions entry") is indirect — a flow without definitions would fail validation, but no test checks the definitions array.

### 4d. Anti-pattern coverage

An anti-pattern is "tested" only if a test would catch the agent doing the wrong thing. This is rare — most test suites lack negative tests.

### 4e. Weighted overall score

| Dimension | Weight | Rationale |
|---|---|---|
| Components | 40% | Core of what the skill teaches |
| Workflow steps | 20% | Sequential correctness |
| Critical rules | 25% | Guard against expensive mistakes |
| Anti-patterns | 15% | Usually need dedicated negative tests |

Formula: `overall = 0.40 * comp% + 0.20 * step% + 0.25 * rule% + 0.15 * anti%`

For skills with **no tests**: overall = 0%.

## Phase 5 — Write reports

Create `tests/reports/` if needed. Write one report per skill at `tests/reports/<skill-name>.md` (e.g., `tests/reports/uipath-maestro-flow.md`). When more than one skill is analyzed, also write `tests/reports/summary.md` with the roll-up table comparing all skills. If the user specified a custom output path, use that instead. Overwrite any existing report at the same path.

---

## Report Template: Per-Skill (with tests)

Use this template when the skill has at least one test task.

```markdown
# Test Coverage Report: <skill-name>

*Generated: YYYY-MM-DD*

## Summary

| Metric | Value |
|--------|-------|
| Total test tasks | N |
| Smoke tests | N |
| Integration tests | N |
| E2E tests | N |
| Components covered (direct + indirect) | X / Y (Z%) |
| Components covered (direct only) | X / Y (Z%) |
| Workflow steps covered | X / Y (Z%) |
| Critical rules covered (direct) | X / Y (Z%) |
| Anti-patterns covered | X / Y (Z%) |
| **Estimated overall coverage** | **Z%** |

> **Infrastructure:** <what this skill requires to run tests — e.g., "Cloud auth required for debug/deploy tests. Local-only for validate/bundle.">

## Test Inventory

| Test ID | Type | Tags | Description | Components Exercised |
|---------|------|------|-------------|---------------------|
| skill-flow-calculator | e2e | generate, ootb | Multiply two inputs via script node | `core.action.script`, input vars, output vars, validate, debug |

## Component Coverage

### <Category> (X/Y covered)

| Component | Direct | Indirect | Test(s) |
|-----------|--------|----------|---------|
| `core.action.script` | Yes | — | skill-flow-calculator, skill-flow-dice-roller, skill-flow-bellevue-weather |
| `core.logic.loop` | — | — | — |

(One subsection per component category.)

### Workflow Steps (X/Y covered)

| # | Step | Covered | Test(s) | Notes |
|---|------|---------|---------|-------|
| 0 | Resolve uip binary | Indirect | all (implicit) | All tests require it but none assert it |
| 4 | Plan the flow | No | — | No test checks for .arch.plan.md or .impl.plan.md |

### Critical Rules (X/Y covered)

| # | Rule | Direct | Indirect | Test(s) |
|---|------|--------|----------|---------|
| 4 | Always --output json | Yes | — | skill-flow-init-validate |
| 7 | Every node needs definitions | — | Yes | all e2e (validation would fail without them) |
| 5 | Edit .flow ONLY | — | — | — |

### Anti-Patterns (X/Y covered)

| # | Anti-Pattern | Covered | Test(s) | Notes |
|---|-------------|---------|---------|-------|
| 1 | Never guess node schemas | No | — | Would need negative test |

## Untested Features

Group by theme. Include cross-cutting features (variable management, expression syntax, planning phases, publishing, editing existing artifacts, etc.) that have no coverage:

- **Control flow:** `core.logic.switch`, `core.logic.loop`, `core.logic.merge`, `core.subflow`, `core.logic.terminate`
- **Publishing:** `uip solution bundle`, `uip solution upload`, `uip flow pack`
- **Planning:** Phase 1 arch plan generation, Phase 2 impl plan resolution, mermaid diagram validation
- **Editing:** No test modifies an existing flow (all tests create from scratch)

## Coverage Gaps — Priority Ranked

### High Priority

Gaps where an agent getting it wrong would cause expensive failures or silent bugs.

1. **<Gap title>** — <What's untested, specific risk>. *Suggested test:* `<suggested-task-id>` (type) — <one sentence describing the test>.

### Medium Priority

Gaps in secondary capabilities or uncommon paths.

### Low Priority

Gaps in edge cases or features that other tests partially cover indirectly.

## Recommendations

Top 5–10 tests to write next, ordered by how much coverage they add:

1. **`<suggested-task-id>`** (e2e) — Covers: `core.logic.loop`, `core.logic.merge`, `core.action.transform`, iteration pattern. *Why:* The entire control-flow family is untested; a single test with a loop-and-merge topology covers 4 components.
```

---

## Report Template: Per-Skill (no tests)

Use this compact template when the skill has zero test tasks. Do not produce full coverage tables with all-dash rows — just list the inventory.

```markdown
# Test Coverage Report: <skill-name>

*Generated: YYYY-MM-DD*

## Summary

| Metric | Value |
|--------|-------|
| Total test tasks | 0 |
| Components inventoried | N |
| Workflow steps | N |
| Critical rules | N |
| Anti-patterns | N |
| **Estimated overall coverage** | **0%** |

> **Infrastructure:** <what this skill requires to run tests — e.g., "Requires Windows + UiPath Studio Desktop" or "Requires cloud auth" or "Local-only — no special requirements">

## Component Inventory

List all components grouped by category. Use a compact format — no Direct/Indirect/Test columns since there are no tests.

### <Category> (N components)
- Component 1
- Component 2
- ...

(Repeat per category.)

### Workflow Steps (N steps)
1. Step name — brief description
2. ...

### Critical Rules (N rules)
1. Rule summary
2. ...

### Anti-Patterns (N items)
1. Anti-pattern summary
2. ...

## Recommended Starter Tests

Recommend 2 smoke tests and 2 e2e tests to establish baseline coverage. For each:

1. **`<suggested-task-id>`** (type) — Covers: <components, rules>. *Why:* <rationale>. <Infrastructure note if needed.>
```

---

## Report Template: Summary Roll-Up

Produce this whenever more than one skill is analyzed (including `all` mode).

```markdown
# Test Coverage Summary

*Generated: YYYY-MM-DD*

## Overview

| Skill | Tests | Components (direct) | Workflow | Rules | Anti-Patterns | Overall | Infra |
|-------|-------|---------------------|----------|-------|---------------|---------|-------|
| uipath-maestro-flow | 10 | 6/24 (25%) | 6/9 (67%) | 1/16 (6%) | 0/13 (0%) | 33% | Cloud auth |
| uipath-rpa | 0 | 0/39 (0%) | 0/8 (0%) | 0/21 (0%) | 0/30 (0%) | 0% | Windows + Studio |

**Totals:** N tests across M skills. X components inventoried, Y directly tested (Z%). A workflow steps, B covered. C critical rules, D directly tested. E anti-patterns, F tested.

## Skills Without Tests

| Skill | Components | Rules | Steps | Infra Requirements | Risk Summary |
|-------|-----------|-------|-------|-------------------|--------------|
| uipath-rpa | 39 | 21 | 8 | Windows + Studio | Highest rule count; Coded C# + XAML authoring |
| uipath-agents | 46 | 10 | 9 | Cloud auth | 4 frameworks, 8 binding types, lazy LLM init |

## Cross-Skill Patterns

Observations that span multiple skills. Look for:
- Test type gaps (e.g., "no integration-tier tests exist anywhere")
- Workflow phase gaps (e.g., "no skill tests publishing or deployment")
- Negative test gaps (e.g., "no anti-pattern tests exist for any skill")
- Editing gaps (e.g., "no test modifies an existing artifact")
- Infrastructure barriers (e.g., "N skills require Windows, blocking CI coverage")

## Top 10 Recommended Tests

Across all skills, prioritized by coverage impact. Prefer tests that are feasible to implement (local-only or cloud-auth-only over platform-specific).

1. **`skill-<name>-<capability>`** (<skill>, <type>) — <what it covers and why>. <Infra note if needed.>
```

---

## Rules

1. **Read everything.** Every SKILL.md, every reference, every YAML, every check script. For skills with `references/plugins/` directories, read at least the `planning.md` for each plugin to understand what it covers — you don't need to read every `impl.md` unless the test coverage is ambiguous.
2. **Be conservative.** "Direct" requires an explicit assertion. "Indirect" requires the test would necessarily fail without it. When in doubt, "None".
3. **Read-only.** Do not modify skill or test files. Only write to `tests/reports/`.
4. **Deduplicate.** If a node type appears in both SKILL.md and a plugin reference, count it once.
5. **Be specific.** "Add more tests" is not actionable. Name the exact components, suggest a task_id, suggest what the test prompt and check script would verify.
6. **Handle no-tests gracefully.** Use the compact no-tests template. List all capabilities as inventory, recommend 2 smoke + 2 e2e starter tests.
7. **Parallelize.** For multi-skill runs, use Explore agents in parallel.
8. **Match recommendations to existing test patterns.** Look at how existing tests are structured (YAML format, check script patterns, tag conventions) and suggest new tests that follow the same patterns. Recommend realistic tests — flag infrastructure dependencies and prefer tests that can run in CI (local-only or cloud-auth-only).
9. **Anti-patterns come from SKILL.md only.** Count items in the main Anti-Patterns / What NOT to Do section. Do not trawl reference files for additional "never do X" statements — those are implementation-level guidance, not skill-level anti-patterns.
10. **Flag infrastructure requirements.** Every report should note what environment the skill needs for testing. The summary should include an Infra column so readers can quickly see which skills are CI-testable vs platform-gated.
