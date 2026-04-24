# UiPath Skills Test Coverage Report

Analyze what a skill teaches vs what its tests verify. Produce a gap analysis with prioritized recommendations.

**Input:** `$ARGUMENTS`
- Skill name or path (e.g., `uipath-maestro-flow`) — single skill.
- Empty or `all` — every skill under `skills/`.

**Output:** Markdown report(s) in `tests/reports/<skill-name>.md` (e.g., `tests/reports/uipath-maestro-flow.md`), unless the user specifies a different path. Overwrite existing reports at the same path.

**Feed-forward contract.** This report is the primary input to `/generate-tasks <skill> [focus]`. Write gap titles as short noun phrases and suggested task IDs the way you'd want them typed back as a focus string (e.g. "Brown-field editing of existing flows" → `generate-tasks uipath-maestro-flow Brown-field editing of existing flows`).

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

Determine what environment each skill requires to be testable. Use the same phrasing as existing task prompts and `/skill-compare` so readers can grep across docs:

- **Local-only** — no cloud auth or special hardware (e.g., flow validate, solution pack)
- **Requires cloud auth** — needs UiPath tenant authentication (e.g., platform ops, flow debug, deploy)
- **Requires Windows + Studio Desktop** — needs Studio installed (task prompts typically note "Studio Desktop is NOT available" when skipping these)
- **Requires browser extension / Servo CLI / display** — desktop/browser automation skills

Tag each skill with its dependencies. This informs which tests are feasible to write and run in CI.

## Phase 3 — Extract test coverage

### 3a. Parse each test YAML

Extract these fields:

```
task_id         — unique test identifier (e.g., "skill-flow-calculator")
description     — what the test validates
tags            — array carrying values from the five Tag Taxonomy dimensions
                  documented in tests/README.md. Position convention:
                  [skill, tier, lifecycle, scenario, ...features]
                    skill     — uipath-<name>                                 (required)
                    tier      — smoke | integration | e2e                      (required)
                    lifecycle — activate | generate | edit | validate | execute | deploy
                    scenario  — green-field | brown-field | fixture
                    features  — hitl, approval-gate, write-back, escalation, registry,
                                connector-feature, connections, activities, records,
                                entities, api-workflow, compliance, test-case, hooks,
                                transform, http (0..n)
                  Record every dimension; Phase 4f keys off all of them, not just tier.
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

### 4d. Path coverage (when applicable)

Some skills teach ≥2 implementation **paths** — alternate ways to accomplish the same task. Regressions in real projects frequently live in one path while the other keeps passing, so path coverage is its own axis.

Identify paths from SKILL.md and references. Common examples:

| Skill | Paths |
|---|---|
| `uipath-rpa` | Coded (C#), XAML |
| `uipath-rpa-legacy` | Cross-platform Legacy, Windows-only Legacy |
| `uipath-agents` | LangGraph, LlamaIndex, OpenAI Agents, Simple Function, low-code |
| `uipath-maestro-flow` (agents) | low-code, inline-flow |
| `uipath-coded-apps` | Coded Web App, Coded Action App |
| `uipath-human-in-the-loop` | greenfield HITL in `.flow`, brownfield HITL in `.flow`, HITL in coded agents |

A path is "covered" if at least one test exercises it (look at the `authoring`, `lifecycle`, `scenario`, or skill-specific tags on each task, plus the prompt content). For single-path skills, this dimension is **N/A**.

### 4e. Anti-patterns (diagnostic, not scored)

Report anti-patterns covered in a per-skill table, but do **NOT** include them in the weighted overall score. Across the repo, anti-pattern coverage is effectively 0% everywhere — keeping it at 15% weight was deadweight that compressed scores without adding signal. The "Negative-test gap" signal in Phase 4g already surfaces skills with ≥3 anti-patterns and zero negative tests, which is the actionable version.

### 4f. Weighted overall score

Weights reflect what tests actually catch:

| Dimension | Weight | Rationale |
|---|---|---|
| Components | 55% | Core of what the skill teaches; where regressions actually land |
| Workflow steps | 30% | Sequential correctness across the lifecycle |
| Critical rules | 15% | Guard against expensive mistakes (low because most rules are Indirect in practice) |
| Path coverage | — / 15% | N/A for single-path skills; 15% when applicable |

**N/A handling.** When a skill is missing a dimension (common cases documented below), mark it **N/A** in the Summary table and **renormalize** the remaining weights proportionally — do NOT score it as 0%. Example: a catalog skill (`uipath-platform`) with no Critical Rules section and a single path has weights renormalized to Components 65% / Steps 35%.

| Skill shape | Typical N/A dimensions | Effective weights |
|---|---|---|
| Workflow-heavy, multi-path (e.g. `uipath-rpa`, `uipath-agents`, `uipath-maestro-flow`) | — | Comp 45% / Steps 25% / Rules 15% / Path 15% |
| Workflow-heavy, single-path (e.g. `uipath-case-management`, `uipath-human-in-the-loop`) | Path | Comp 55% / Steps 30% / Rules 15% |
| Command-catalog skills (e.g. `uipath-platform`, `uipath-servo`, `uipath-test`, `uipath-feedback`, `uipath-data-fabric`) | Rules, Path, Steps (often) | Comp 100% (or Comp 65% / Steps 35% if the skill has explicit workflow steps) |
| Planning skills (e.g. `uipath-planner`, `uipath-solution-design`) | Components (often), Rules (sometimes), Path | Steps 70% / Rules 30% (or Steps 100% if no rules section) |
| Agent-orchestration skills (e.g. `uipath-diagnostics`) | Path, sometimes Components | Components 55% (sub-agents + phases) / Steps 30% / Rules 15% |

Formula: `overall = sum(applicable_weight_i * dimension_pct_i) / sum(applicable_weight_i)`

For skills with **no tests**: overall = 0%.

### 4h. Test-density diagnostics (sidecar, not scored)

Report these alongside the Summary table to flag structural fragility that a high coverage score might hide. None of these feed the weighted score — they're red-flag indicators for readers.

- **Total tests** — already in Summary.
- **Tests per component (median)** — if `0`, most components are untested even when the coverage score looks OK.
- **Tests per component (max)** — if one component has >50% of the tests, coverage is concentrated and fragile.
- **Single-test-dominance flag** — emit a warning bullet if any one test task accounts for more than 1/3 of all Direct component hits. That test becomes a single point of failure for the coverage number.

### 4i. Tag-dimension coverage (sidecar diagnostic)

For each skill that has at least one test, compute which values from the Tag Taxonomy are exercised. Report the three variable dimensions (the `skill` dimension is trivially covered and `tier` is already reported in the Summary table):

- **Lifecycle** — tick each of `activate`, `generate`, `edit`, `validate`, `execute`, `deploy` if any test carries that tag.
- **Scenario** — tick each of `green-field`, `brown-field`, `fixture`.
- **Feature** — list the feature tags present vs a reasonable "expected" set for this skill (derived from the skill's SKILL.md — e.g. `uipath-human-in-the-loop` should exercise `hitl`, `approval-gate`, `write-back`, `escalation`; `uipath-maestro-flow` should exercise `registry`, `connector-feature`, `transform`, `http`, …). If the skill's vocabulary is open, just list what's present without the ✗ column.

This is structured data for the per-skill report (see template below). It is NOT folded into the weighted overall score — adding it on top of Components/Steps would double-count (a missing `edit` lifecycle already shows up as a workflow-step gap).

### 4j. Automatic gap signals

Run these checks and emit findings into the "Coverage Gaps — Priority Ranked" section with the specified priority. The goal is consistent, data-driven flagging across skills rather than ad-hoc prose:

| Signal | Condition | Priority | Gap title template |
|---|---|---|---|
| **Lifecycle gap (edit)** | The skill teaches an edit workflow (it documents modifying an existing artifact — common for `uipath-maestro-flow`, `uipath-rpa`, `uipath-agents`) but no test carries the `edit` lifecycle tag. | **High** | "Editing existing `<artifact>`" |
| **Scenario gap (brown-field)** | All tests carry `green-field` (or no scenario tag), and the skill explicitly supports modifying existing projects. | **Medium** | "Brown-field modification of existing `<artifact>`" |
| **Negative-test gap** | The skill's SKILL.md lists ≥3 anti-patterns and zero tests assert on any of them. | **High** | "Negative tests for anti-patterns" |
| **Tier gap** | The skill has tests but is missing a tier (smoke-only, integration-only, or e2e-only). | **High** (if smoke or e2e is missing — those are the minimum bar), **Medium** (integration missing) | "Missing `<tier>` tier" |

Whenever a signal fires, the corresponding recommendation in Phase 5's Recommendations section must include the tag list that would address it (e.g. a "Brown-field modification" recommendation ships with `(e2e, edit, brown-field, …)`).

## Phase 5 — Write reports

Create `tests/reports/` if needed.

**Output rules:**

| Invocation | Files written |
|---|---|
| Single skill (e.g. `uipath-maestro-flow`) | `tests/reports/<skill-name>.md` only. |
| `all` (or empty) | One per-skill report **and** the roll-up: `tests/reports/<skill-name>.md` for every skill plus `tests/reports/SUMMARY.md`. |
| User-specified custom path | Use that path instead. |

Overwrite any existing report at the same path. The summary file name is `SUMMARY.md` (uppercase), matching the directory structure documented in `tests/README.md`.

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
| Critical rules covered (direct) | X / Y (Z%) *or* N/A (no Critical Rules section) |
| Path coverage | X / Y (Z%) *or* N/A (single-path skill) |
| **Estimated overall coverage** | **Z%** (weights: Comp W1% / Steps W2% / Rules W3% / Path W4% — renormalized over applicable dimensions) |

Anti-patterns are inventoried in the Anti-Patterns section below but are **not** part of the overall score (see Phase 4e).

### Test-density diagnostics

- Total test tasks: N
- Median tests per component: X
- Max tests per component: X (on `<component>`)
- ⚠ *single-test-dominance:* emit this bullet only when one test accounts for >1/3 of Direct component hits — name the test.

> **Infrastructure:** <what this skill requires to run tests — e.g., "Requires cloud auth for debug/deploy tests. Local-only for validate/bundle.">

## Test Inventory

| Test ID | Type | Tags | Description | Components Exercised |
|---------|------|------|-------------|---------------------|
| skill-flow-calculator | e2e | generate, green-field, transform | Multiply two inputs via script node | `core.action.script`, input vars, output vars, validate, debug |

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

### Path Coverage (X/Y paths exercised)

Applicable only when the skill documents ≥2 implementation paths. Otherwise write "N/A — single-path skill" and skip the table.

| Path | Exercised | Test(s) |
|------|-----------|---------|
| Coded (C#) | Yes | skill-rpa-coded-test-case |
| XAML | No | — |

### Anti-Patterns (X/Y covered — diagnostic only, NOT in overall score)

| # | Anti-Pattern | Covered | Test(s) | Notes |
|---|-------------|---------|---------|-------|
| 1 | Never guess node schemas | No | — | Would need negative test |

### Tag-Dimension Coverage

Sidecar diagnostic — see Phase 4i. Not part of the weighted overall score.

**Lifecycle**

| Value | Tests | Status |
|---|---|---|
| `activate` | skill-flow-registry-discovery | ✓ |
| `generate` | skill-flow-calculator, skill-flow-reading-list, … | ✓ |
| `edit` | — | ✗ |
| `validate` | skill-flow-init-validate | ✓ |
| `execute` | skill-flow-calculator, skill-flow-dice-roller | ✓ |
| `deploy` | — | ✗ |

**Scenario**

| Value | Tests | Status |
|---|---|---|
| `green-field` | all | ✓ |
| `brown-field` | — | ✗ |
| `fixture` | — | ✗ |

**Feature tags in use**

`registry` (2), `transform` (3), `http` (1), `connector-feature` (18), …

(For skills with a clear "expected" feature set — e.g., HITL should exercise `hitl`, `approval-gate`, `write-back`, `escalation` — use the same Status column with ✓/✗. For skills with an open feature vocabulary, just list counts.)

## Untested Features

Group by theme. Include cross-cutting features (variable management, expression syntax, planning phases, publishing, editing existing artifacts, etc.) that have no coverage:

- **Control flow:** `core.logic.switch`, `core.logic.loop`, `core.logic.merge`, `core.subflow`, `core.logic.terminate`
- **Publishing:** `uip solution upload`, `uip flow pack`
- **Planning:** Phase 1 arch plan generation, Phase 2 impl plan resolution, mermaid diagram validation
- **Editing:** No test modifies an existing flow (all tests create from scratch)

## Coverage Gaps — Priority Ranked

Gap titles are short noun phrases — the exact string a reader would paste into `/generate-tasks <skill> <focus>`. Include entries emitted by the Phase 4g automatic signals (lifecycle gap, scenario gap, negative-test gap, tier gap) alongside skill-specific gaps.

### High Priority

Gaps where an agent getting it wrong would cause expensive failures or silent bugs.

1. **<Gap title — noun phrase>** — <What's untested, specific risk>. *Suggested test:* `<suggested-task-id>` (tier, lifecycle, scenario, …features) — <one sentence describing the test>.

### Medium Priority

Gaps in secondary capabilities or uncommon paths.

### Low Priority

Gaps in edge cases or features that other tests partially cover indirectly.

## Recommendations

Top 5–10 tests to write next, ordered by how much coverage they add. Each recommendation carries the full proposed tag list so `/generate-tasks` can consume it verbatim.

1. **`<suggested-task-id>`** (e2e, generate, green-field, transform) — Covers: `core.logic.loop`, `core.logic.merge`, `core.action.transform`, iteration pattern. *Why:* The entire control-flow family is untested; a single test with a loop-and-merge topology covers 4 components.
2. **`skill-flow-edit-loop`** (e2e, edit, brown-field, registry) — Covers: editing an existing flow, adding a loop node to an existing topology. *Why:* No test carries the `edit` lifecycle or `brown-field` scenario — modifying existing flows is a first-class workflow in this skill.
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

Recommend 2 smoke tests and 2 e2e tests to establish baseline coverage (per CONTRIBUTING.md minimum bar: 1 smoke + 1 e2e). For each, include the full proposed tag list so `/generate-tasks` can consume the recommendation verbatim:

1. **`<suggested-task-id>`** (smoke, generate, green-field) — Covers: <components, rules>. *Why:* <rationale>. <Infrastructure note if needed.>
2. **`<suggested-task-id>`** (e2e, generate, green-field, <feature>) — Covers: <…>. *Why:* <…>.
```

---

## Report Template: Summary Roll-Up

Produce this whenever more than one skill is analyzed (including `all` mode).

```markdown
# Test Coverage Summary

*Generated: YYYY-MM-DD*

## Overview

| Skill | Tests | Components (direct) | Workflow | Rules | Paths | Overall | Tests/Comp (med) | Infra |
|-------|-------|---------------------|----------|-------|-------|---------|------------------|-------|
| uipath-maestro-flow | 49 | 6/24 (25%) | 6/9 (67%) | 1/16 (6%) | 1/2 (50%) | 33% | 2 | Requires cloud auth |
| uipath-rpa | 2 | 0/39 (0%) | 0/8 (0%) | 0/21 (0%) | 1/2 (50%) | 8% | 0 | Requires Windows + Studio |
| uipath-platform | 5 | 2/12 (17%) | N/A | N/A | N/A | 17% | 0 | Requires cloud auth |

Overall is weighted and renormalized across applicable dimensions (see Phase 4e). N/A cells mean the skill is missing that dimension (e.g. no Critical Rules section, single-path skill, catalog skill with no workflow steps) — weights redistribute proportionally.

**Totals:** N tests across M skills. X components inventoried, Y directly tested (Z%). A workflow steps, B covered. C critical rules, D directly tested. E multi-path skills, F with full path coverage. Anti-patterns are inventoried per skill but intentionally excluded from the overall score.

## Skills Without Tests

| Skill | Components | Rules | Steps | Infra Requirements | Risk Summary |
|-------|-----------|-------|-------|-------------------|--------------|
| uipath-rpa | 39 | 21 | 8 | Windows + Studio | Highest rule count; Coded C# + XAML authoring |
| uipath-agents | 46 | 10 | 9 | Cloud auth | 4 frameworks, 8 binding types, lazy LLM init |

## All Coverage Gaps

Combine every gap from every per-skill report into one table, sorted by priority (High first, then Medium, then Low). This gives a single view of everything that needs testing across the repo.

| # | Skill | Priority | Gap | Risk | Suggested Test | Infra |
|---|-------|----------|-----|------|---------------|-------|
| 1 | uipath-maestro-flow | High | Control flow nodes untested | Silent data loss from misbuilt loops | `skill-flow-loop-sum` (e2e) | Cloud auth |
| 2 | uipath-agents | High | No Simple Function agent test | Wrong pyproject.toml or missing @traced | `skill-agent-simple-echo` (e2e) | Cloud auth |
| ... | ... | ... | ... | ... | ... | ... |

## Cross-Skill Patterns

Observations that span multiple skills. Look for:
- Test type gaps (e.g., "no integration-tier tests exist anywhere")
- Workflow phase gaps (e.g., "no skill tests publishing or deployment")
- Negative test gaps (e.g., "no anti-pattern tests exist for any skill")
- Editing gaps (e.g., "no test modifies an existing artifact")
- Infrastructure barriers (e.g., "N skills require Windows, blocking CI coverage")

## Minimum Bar Check

> Every skill must have at least 1 smoke test and 1 e2e test (per CONTRIBUTING.md). This is the **only** place the minimum-bar check lives — per-skill Recommendations sections link back here rather than restating the rule.

The table also surfaces the **tier gap** signal from Phase 4g: a skill with tests but missing a tier (smoke-only, e2e-only) is flagged even if it technically meets the smoke+e2e minimum.

| Skill | Smoke | Integration | E2E | Status |
|-------|-------|-------------|-----|--------|
| uipath-maestro-flow | 2 | 5 | 8 | Meets minimum |
| uipath-rpa | 0 | 0 | 0 | Below minimum (missing smoke + e2e) |
| uipath-data-fabric | 2 | 0 | 1 | Tier gap (no integration tier) |

## Top 10 Recommended Tests

Across all skills, prioritized by coverage impact. Prefer tests that are feasible to implement (local-only or cloud-auth-only over platform-specific). Each recommendation carries the full proposed tag list so `/generate-tasks` can lift it verbatim.

1. **`skill-<name>-<capability>`** (<skill>, tier, lifecycle, scenario, …features) — <what it covers and why>. <Infra note if needed.>
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
11. **Tag every recommendation.** Suggested tests in the Gaps and Recommendations sections must carry the proposed tag list (tier, lifecycle, scenario, features) from the Tag Taxonomy. These recommendations feed `/generate-tasks` — the validated tag set must travel with them so no inference is required downstream.
12. **Minimum bar lives in the summary.** The smoke+e2e minimum-bar check lives in the summary's Minimum Bar Check section and nowhere else. Per-skill reports may note the status but must not restate the rule — link back to the summary instead.
