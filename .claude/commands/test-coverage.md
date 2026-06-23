# UiPath Skills Test Coverage Report

Analyze what a skill teaches vs what its tests verify. Produce a gap analysis with prioritized recommendations.

**Input:** `$ARGUMENTS`
- Skill name or path (e.g., `uipath-maestro-flow`) — single skill.
- Empty or `all` — every skill under `skills/`.

**Output:** Markdown report(s) in `tests/reports/<skill-name>.md` (e.g., `tests/reports/uipath-maestro-flow.md`), unless the user specifies a different path. Overwrite existing reports at the same path.

**Feed-forward contract.** This report is the primary input to `/generate-task <description>`. `/generate-task` takes a free-form description and infers the target skill from it — write gap titles as self-contained descriptions that name the skill or its CLI surface, so the reader can paste a gap straight into `/generate-task` (e.g. "Brown-field editing of existing uipath-maestro-flow projects" → `/generate-task Brown-field editing of existing uipath-maestro-flow projects`).

---

## Phase 1 — Discovery

1. Resolve target skill(s):
   - Single name → `skills/<name>/`. If `skills/<name>/` does NOT exist but `<name>` is in the **Planned Skills Registry** below, treat it as a planned skill (use the planned-skill template in Phase 5). If `<name>` is in the **Cross-Cutting Capability Registry** below, treat it as a cross-cutting capability (see that section).
   - Empty/all → union of (a) glob `skills/uipath-*/`, (b) every entry in the **Planned Skills Registry** whose folder does not yet exist, and (c) every entry in the **Cross-Cutting Capability Registry**. Planned-but-missing skills MUST appear in the per-skill report set and roll-up at 0% until they ship; cross-cutting capabilities MUST appear as their own report + roll-up row (flagged cross-cutting, see §4f and §5).
2. For a normal skill, check for `tests/tasks/<skill-name>/`. For a cross-cutting capability, there is **no dedicated dir** — discover its tests by **tag** (step 3).
3. Find `*.yaml` test files. Normal skill: recursively under `tests/tasks/<skill-name>/`, exclude `_shared/`. Cross-cutting capability: `grep -rl '<tag>' tests/tasks --include='*.yaml' | grep -v _shared` across the **whole** `tests/tasks/` tree (its tasks live inside other skills' dirs).
4. Find `check_*.py` scripts recursively. Exclude `_shared/test_*.py` (unit tests for shared helpers).

For multi-skill runs, use parallel Explore agents — one per skill — to read skill + test content simultaneously. Skip Phase 2 entirely for planned-but-missing skills (no SKILL.md to read).

### Cross-Cutting Capability Registry

Some capabilities are taught and tested across **multiple** skills with no folder of their own, yet are first-class products on the org scorecard (e.g. ECS / Context Grounding). Analyze each as its own unit: a dedicated `references/` doc is the capability inventory source, and its tests are selected by **tag** (they physically live inside other skills' `tests/tasks/` dirs). Because those tasks are **also** counted under their host skills, a cross-cutting unit is an **additive overlay, not a partition** — flag it and **exclude it from the repo-wide Totals sums** (Phase 5) so tasks/components are not double-counted.

| Capability (report key) | Tag | Inventory source(s) | Host skills | Scorecard row |
|---|---|---|---|---|
| `uipath-context-grounding` | `context-grounding` | `skills/uipath-agents/references/context-grounding-patterns.md` (decision logic) + `skills/uipath-agents/references/coded/capabilities/context-grounding.md` + `.../lowcode/capabilities/context/context.md` + the BatchTransform/DeepRAG `planning.md` files those link to | `uipath-agents`, `uipath-maestro-flow` | ECS (uip context-grounding) |

Add a row when a capability (a) is documented in a shared `references/` doc, (b) is exercised by tasks tagged with a single stable tag that span ≥2 skill dirs, and (c) maps to a standalone scorecard product row. Remove it only if the capability gets its own `skills/uipath-<name>/` folder (then it becomes a normal skill).

### Planned Skills Registry

These skills are expected to ship but have no folder under `skills/` yet. Treat them as 0% coverage and surface them in every `all`-mode run so the gap stays visible. When a folder appears under `skills/<name>/`, normal Phase 2 extraction takes over automatically — do not remove entries from this list when that happens; the existence check in step 1 handles the transition. Remove an entry only when the skill is intentionally cancelled.

| Planned skill | Domain (one-line hint for the stub report) |
|---|---|
| `uipath-automation-suite` | On-prem Automation Suite platform operations |
| `uipath-communications-mining` | Communications Mining (email/text intent + sentiment) |
| `uipath-document-understanding` | Document Understanding (extraction, classification, validation) |
| `uipath-governance` | Tenant governance, policies, audit (umbrella over `uipath-gov-*`) |
| `uipath-insights` | Insights dashboards, KPIs, scheduled reports |
| `uipath-marketplace` | UiPath Marketplace component publish/consume |
| `uipath-process-mining` | Process Mining (event logs, conformance, dashboards) |
| `uipath-task-mining` | Task Mining (recordings, task analysis) |
| `uipath-agenthub` | Agent Hub (build, publish, and manage UiPath agents) |

## Phase 2 — Extract the skill's capability inventory

Read the skill's **SKILL.md and every file in `references/` and `assets/`**. Skills vary widely in structure — adapt extraction to what you find.

### 2a. Identify components

Components are the specific, testable units the skill teaches. What counts as a "component" depends on the skill's domain:

| Skill domain | Component examples |
|---|---|
| Flow orchestration (`uipath-maestro-flow`) | Node types: `core.action.script`, `core.logic.decision`, `uipath.connector.*`, etc. Find these in SKILL.md Plugin Index tables and `references/plugins/*/planning.md` files. |
| RPA workflows (`uipath-rpa`) | Workflow modes (Coded C#, XAML), activity types, project types. Found in section headings like "Coded Workflows Quick Reference", "XAML Workflows Quick Reference". |
| Platform operations (`uipath-platform`) | CLI command groups (`uip orchestrator`, `uip is`), API domains. Found in "CLI Overview" command tables and Task Navigation. |
| Solution lifecycle (`uipath-solution`) | `uip solution` lifecycle (init, pack, publish, deploy, activate). Found in the CLI Surface Probe, Critical Rules, and Workflow sections of the SKILL.md. |
| Solution design + planning (`uipath-planner`) | PDD → SDD design (Phase D: PDD analysis, architecture review, SDD generation, product/scope selection, SDD templates) plus multi-skill task derivation (Lane A/B). Found in the Critical Rules, Entry Guard, Phase D, lane summaries, and Reference Navigation sections. |
| Agent development (`uipath-agents`) | Lifecycle stages (Auth, Setup, Build, Bindings, Run, Deploy), framework types (LangGraph, LlamaIndex, etc.). Found in "Lifecycle Stages" section. |
| Coded apps (`uipath-coded-apps`) | Pipeline stages (Push, Pull, Pack, Publish, Deploy), app configuration concepts. Found in lifecycle and "Ship It" sections. |
| Cross-cutting capability (`uipath-context-grounding`) | The **modes × surfaces** matrix from the inventory doc: BatchTransform (coded, low-code), DeepRAG (coded, low-code), Index search (coded, low-code) — 6 components from `context-grounding-patterns.md` §The Three Modes + §Surface Selection. Found in the registered inventory source(s), NOT a SKILL.md. |

Group components by category. For skills with `references/plugins/` subdirectories (like `uipath-maestro-flow`), each plugin directory is one component — use the planning.md to understand what it covers. **Cross-cutting capability:** there is no SKILL.md — read the registered inventory source doc(s) instead. Components = the capability's modes/surfaces matrix; critical rules = its invariants (e.g. `context-grounding-patterns.md` §Cross-Surface Invariants is 6 numbered rules; the file-type routing rule — CSV→BatchTransform, PDF/TXT→DeepRAG — is a 7th). Workflow steps usually N/A (Steps weight redistributes to Components/Rules).

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
- **Requires browser extension / display** — desktop/browser automation skills

Tag each skill with its dependencies. This informs which tests are feasible to write and run in CI.

### 2f. Classify each capability by mode (Coding Agents Scorecard)

Label every component, workflow step, and critical rule with the mode(s) it serves. Multi-label allowed — a `validate` step is both `build` and `diagnose`.

- **build** — creating, designing, editing, deploying (init, scaffold, pack, edit, validate-during-build, deploy)
- **operate** — running, triggering, managing live instances/connectors/integrations (run, trigger, invoke, manage connections)
- **diagnose** — investigating faults, inspecting traces, debugging (get-errors, logs, trace inspect, debug)

These labels define each mode's denominator in Phase 4f-mode. Most build-heavy skills come out build-dominant — expected. A skill that clearly teaches an `operate` or `diagnose` surface but has zero capabilities labeled that mode is itself a finding (surface it in the gaps).

**Labeling subtlety — `validate` and `list`/`get` are mode-dependent.** A capability's mode follows the *intent the skill teaches*, not the verb:
- `validate` / `build` run on a **fresh artifact during authoring** → `build`. The same command run on a **pre-broken artifact to surface and fix errors** (the autonomous validate→read-errors→fix loop) → also `diagnose`. Tag both; a build-only test does NOT cover the diagnose loop.
- `list` / `get` / `status` as a **happy-path step** → the mode of the step it serves. The same read used to **triage a fault** ("list jobs `--state Faulted`", "get incidents before deciding") → `diagnose`.
- `run` / `invoke` / `deploy` of a **deployed, live artifact** → `operate`, even when the build skill owns the command.

#### 2f-i. Operate & diagnose surface checklist (apply to EVERY skill)

Build coverage is almost always the strong mode; `operate` and `diagnose` are where real gaps hide and where a skill's SKILL.md mentions a surface that no test touches. The archetypes below recur across ≥2 skills. For each skill, walk both lists: if the SKILL.md / references teach the surface (even in a reference, not just the main body), it is a labeled capability for that mode — and if no test exercises it, it is a `None` that feeds the Phase 4f-mode denominator and the Phase 4i mode gap. Cite the specific archetype in the gap title (e.g. "Missing `operate` coverage in uipath-rpa — run/invoke + deploy-activate untested").

**Operate archetypes — does any test exercise…**

| # | Archetype | Surface pattern (skill-agnostic) |
|---|---|---|
| O1 | **Run / invoke a deployed artifact** | start a job/process/agent/flow/test-case by key → returns execution id (`jobs start`, `tm testcases run`, `flow debug`, `api-workflow run`, `codedagent deploy`+invoke) |
| O2 | **Deploy + activate as separate steps** | `deploy run` then stand-alone `deploy activate` / `deploy status` poll (esp. after `--skip-activate`); `deploy config link/unlink`; `deploy uninstall` |
| O3 | **File sync push / pull** | `codedagent`/`codedapp push` + `pull` roundtrip; `solution upload` to Studio Web / workspace |
| O4 | **Instance lifecycle** | pause / resume / cancel / retry a *running* instance (`maestro flow|case instance …`, BPMN job lifecycle beyond start+stop, `jobs stop`+retry) |
| O5 | **Queue operations** | add items, requeue / review failed items, set deadline / SLA on a live queue |
| O6 | **Trigger create + fire (non-cron)** | create a **queue** or **API** trigger and verify it fires — not just time-based cron |
| O7 | **Connection create + test** | create an IS OAuth connection (`is connections create <key>`) + `ping`/test on a live tenant |
| O8 | **Enable / disable a live resource** | toggle tenant service, webhook, IP-restriction enforcement, or BYO-LLM config on/off and verify state change |
| O9 | **Publish / register a live version** | publish IXP model version, BYO-LLM config, or `packages upload` so it becomes the live version |
| O10 | **License / seat assignment** | assign user/group license bundles, set tenant allocation, read consumables |
| O11 | **Eval run + poll + fetch results** | start a Studio Web eval against a deployed flow/agent, poll to done, fetch scored results |

**Diagnose archetypes — does any test exercise…**

| # | Archetype | Surface pattern (skill-agnostic) |
|---|---|---|
| D1 | **Validate → read errors → fix loop on a PRE-BROKEN artifact** | feed a deliberately broken file, assert the agent reads structured errors and fixes the root cause, then re-validates clean (NOT happy-path validate) |
| D2 | **Incident / fault read on a failed runtime instance** | `instance incidents` / `instance variables` / job faults after a failed run, without rerunning |
| D3 | **Job / execution log retrieval** | `jobs logs <id> --output json`, `tm executions get` / step-log drill-down on a faulted run |
| D4 | **Trace / span inspection** | `traces spans get <trace-id>` as a standalone diagnostic (LLM/tool calls, token counts), not a build/operate side effect |
| D5 | **Audit query filtered for triage** | `audit … events --status Failure` / by user / by time window to answer "who did X / what changed" |
| D6 | **Effective-access / authorization check** | folder-scoped `authorization check-access <user>`, `deployed-policy get --user-id` — "why can't user X do Y" |
| D7 | **Connectivity / health check** | BYO-LLM `--force-refresh` / reprobe, `is connections list --all-folders`, dead-connection audit |
| D8 | **Failure-mode / error-code classification** | match an error code / exception (e.g. `MST-9107`, `CS0103`, exit codes) to a known catalog and recommend the fix branch |
| D9 | **Model / metric quality inspection** | `get-metrics` + `list-models`, per-field F1 / precision / recall to explain bad extraction |
| D10 | **Schema / contract-drift detection** | out-of-sync `bindings_v2.json`, `entry-points` drift, camelCase/naming mismatch surfaced by validate |
| D11 | **Read-only discovery for triage** | `login status`, `list --state Faulted`, `get` before mutating — inspecting state to scope a fault |

**Two recurring meta-findings to always check (emit as gaps when present):**
- **Tag-drift on operate/diagnose:** a skill's only operate/diagnose tests are tagged `mode:build` (or carry no `mode:*` at all) — fires the Phase 4f-mode tag cross-check. Common on catalog skills (`uipath-tasks`, `uipath-data-fabric`, `uipath-ixp`) where every task inherited `mode:build`.
- **Surface-without-test:** SKILL.md/references document an operate/diagnose command (e.g. `maestro case instance`, `rpa debug start`, `solution deploy activate`) that has zero covering tests — the most common source of `operate`/`diagnose` `None`s.

## Phase 3 — Extract test coverage

### 3a. Parse each test YAML

Extract these fields:

```
task_id         — unique test identifier (e.g., "skill-flow-calculator")
description     — what the test validates
tags            — array carrying values from the Tag Taxonomy dimensions
                  documented in tests/README.md. Form:
                  [skill, tier, mode:X, shape:X, node:..., resource, connector, windows, feature:...]
                    skill      — uipath-<name>                                (required, flat)
                    tier       — smoke | integration | e2e                    (required, flat)
                    mode       — mode:{build|operate|diagnose}                  (required; see Phase 2f for mode definitions)
                    shape      — shape:{single-node|multi-node}              (flow-building tests)
                    node       — node:{decision|switch|subflow|terminate|loop|transform|hitl} (0..n)
                    resource   — flat boolean marker (present iff task uses a resource node) (0..1)
                    connector  — flat boolean marker (present iff task uses any connector)   (0..1)
                    windows    — flat boolean marker (present iff task requires a Windows host) (0..1)
                    feature    — feature:{http|trigger|registry|transform|approval-gate|
                                 write-back|escalation|…}                     (0..n)
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

**Canonical figure for scoring: direct-only.** Report both Direct and Direct+Indirect, but the **overall score and the Score Contribution table use the direct-only % `Direct / Total`** (this is what the SUMMARY's `Components (direct)` column shows). Direct+Indirect is informational context, never the scored number. Use the same direct-only % everywhere it feeds a calculation so the Score Contribution total reconciles to the Overall.

**Top untested buckets (roll-up signal).** After scoring components, record the **2–3 categories with the most `None` components** as a compact, comma-separated string — this is what makes the penalty legible from the SUMMARY without opening the per-skill file. Format each as `<category> <none>/<total>`, e.g. `triggers 0/3, IS connectors 0/2, run/publish 2/8`. Pick the categories that drag the score most (largest absolute `None` count; break ties by lowest coverage %). Rules:
- Derive these from the **same `None` rows** already in the Component Coverage tables — do not invent new groupings.
- **Planning skills (Components N/A)** and **catalog skills with no categories**: fall back to the largest-gap **workflow-step groups** or **rule groups** instead (e.g. `Lane A 0/10, entry-guard 0/1, rules 0/5`), so the column is never empty for a scored skill.
- **Skills with no tests / planned skills:** use `all (no tests)` / `— (planned)` respectively.
- Keep it under ~60 chars; it rides in one Overview cell. The full enumeration stays in the per-skill report's **Untested Features** section — this is just the headline.

### 4b. Workflow step coverage

A step is "tested" if at least one test exercises the CLI commands or file operations it describes.

### 4c. Critical rule coverage

A rule is "Direct" if a test would catch its violation. A rule is "Indirect" if following the rule is necessary but not checked. Example: Rule 4 ("always use `--output json`") is directly tested by `init_validate.yaml`'s `command_pattern: 'uip\s+.*--output\s+json'`. Rule 7 ("every node needs a definitions entry") is indirect — a flow without definitions would fail validation, but no test checks the definitions array.

### 4d. Path coverage (when applicable)

Some skills teach ≥2 implementation **paths** — alternate ways to accomplish the same task. Regressions in real projects frequently live in one path while the other keeps passing, so path coverage is its own axis.

Identify paths from SKILL.md and references. Common examples:

| Skill | Paths |
|---|---|
| `uipath-rpa` | Coded (C#), XAML, Legacy (.NET 4.6.1) |
| `uipath-agents` | LangGraph, LlamaIndex, OpenAI Agents, Simple Function, low-code |
| `uipath-maestro-flow` (agents) | low-code, inline-flow |
| `uipath-coded-apps` | Coded Web App, Coded Action App |
| `uipath-human-in-the-loop` | greenfield HITL in `.flow`, brownfield HITL in `.flow`, HITL in coded agents |

A path is "covered" if at least one test exercises it (look at the `mode:*`, `node:*`, `feature:*`, or skill-specific tags on each task, plus the prompt content). For single-path skills, this dimension is **N/A**.

### 4e. Anti-patterns (troubleshooting, not scored)

Report anti-patterns covered in a per-skill table, but do **NOT** include them in the weighted overall score. Across the repo, anti-pattern coverage is effectively 0% everywhere — keeping it at 15% weight was deadweight that compressed scores without adding signal. The "Negative-test gap" signal in Phase 4i already surfaces skills with ≥3 anti-patterns and zero negative tests, which is the actionable version.

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
| Workflow-heavy, single-path (e.g. `uipath-maestro-case`, `uipath-human-in-the-loop`) | Path | Comp 55% / Steps 30% / Rules 15% |
| Command-catalog skills (e.g. `uipath-platform`, `uipath-servo`, `uipath-test`, `uipath-feedback`, `uipath-data-fabric`) | Rules, Path, Steps (often) | Comp 100% (or Comp 65% / Steps 35% if the skill has explicit workflow steps) |
| Planning skills (e.g. `uipath-planner`) | Components (often), Rules (sometimes), Path | Steps 70% / Rules 30% (or Steps 100% if no rules section) |
| Agent-orchestration skills (e.g. `uipath-troubleshoot`) | Path, sometimes Components | Components 55% (sub-agents + phases) / Steps 30% / Rules 15% |
| Cross-cutting capability (e.g. `uipath-context-grounding`) | Path, Steps (usually) | Comp 70% (modes×surfaces) / Rules 30% (invariants) |

Formula: `overall = sum(applicable_weight_i * dimension_pct_i) / sum(applicable_weight_i)`

**Per-dimension contribution.** Define `renorm_weight_i = applicable_weight_i / sum(applicable_weight_i)` (so the renormalized weights sum to 1) and `contribution_i = renorm_weight_i * dimension_pct_i`. By construction `sum(contribution_i) = overall`. Render this decomposition in each per-skill report's **Score Contribution** table (see the with-tests template) so the headline number is traceable to the dimensions that earned or forfeited it. Also report `lost_i = renorm_weight_i*100 − contribution_i` — the largest `lost_i` is the highest-leverage dimension to test next, and should align with that skill's top-ranked gaps.

For skills with **no tests**: overall = 0% (skip the Score Contribution table — every dimension contributes 0).

### 4f-mode. Per-mode coverage (scored slices, reported beside Overall)

Report a coverage score for **each** Coding Agents Scorecard mode (`build`, `operate`, `diagnose`) alongside the Overall. Mode is orthogonal to the scored dimensions — do NOT add it as a weighted dimension (that double-counts against Workflow steps; see Phase 4h). Instead **re-slice the same capability inventory by the Phase 2f mode labels** and re-run the Phase 4f weighted formula per slice:

1. For mode `m`, take only the components / workflow steps / critical rules labeled `m`.
2. Compute each dimension's direct-only coverage within that slice; renormalize the applicable weights over the dimensions present in the slice (same N/A handling as Phase 4f).
3. `mode_pct(m)` = that weighted number.

Cases:
- Mode has labeled capabilities, zero covering tests → **0%**.
- Mode has no labeled capabilities in this skill → **N/A** (e.g. a pure-build catalog skill with no diagnose surface). N/A modes do not fire the Phase 4i mode gap.
- Overall (Phase 4f) is unchanged — it is **NOT** the mean of the three modes (slices differ in size). Report both; they will not match, by design.

**Tag cross-check.** A capability counts toward `mode_pct(m)` from its Phase 2f label, regardless of which test covers it. But if a mode-`m` capability is covered *only* by tests not tagged `mode:m`, the test's mode tag is wrong — emit a consistency flag (name the test). This keeps the coverage slices aligned with the `mode:*` tags that `/generate-confluence-scorecard` slices eval by, so per-mode coverage and per-mode eval pair correctly.

**Mode-balanced & mode-floor headlines (report beside the capability Overall).** The capability Overall is build-dominated by construction — the inventory is mostly build capabilities, so a skill can read "healthy" (e.g. 79%) while `operate`/`diagnose` sit near 0%, because those modes are a small slice of each dimension's denominator. To make that blindness legible without changing the Overall, compute and report two derived figures from the per-mode slices:
- **Mode-balanced** = arithmetic mean of `mode_pct(m)` over the modes that are **not N/A** (i.e. modes the skill actually has a surface for). A skill with `diagnose` N/A averages only `build` + `operate`.
- **Mode-floor** = `min` of `mode_pct(m)` over the not-N/A modes — the worst-covered real mode. This is the single number that exposes a 0% mode.

Report both beside the Overall in the per-skill Summary, the SUMMARY Overview, and `coverage.json` (`mode_balanced`, `mode_floor`). They are **descriptive, not a new weighted score** — the Overall is still the Phase 4f capability number. Rule of thumb for readers: a high Overall with a low Mode-floor = build-solid but mode-blind; that gap is the action item, and the Phase 4i mode gap already names which archetype to test. Skills with no tests → `0`/`0`; planned skills → `—`.

### 4g. Test-density troubleshooting (sidecar, not scored)

Report these alongside the Summary table to flag structural fragility that a high coverage score might hide. None of these feed the weighted score — they're red-flag indicators for readers.

- **Total tests** — already in Summary.
- **Tests per component (median)** — if `0`, most components are untested even when the coverage score looks OK.
- **Tests per component (max)** — if one component has >50% of the tests, coverage is concentrated and fragile.
- **Single-test-dominance flag** — emit a warning bullet if any one test task accounts for more than 1/3 of all Direct component hits. That test becomes a single point of failure for the coverage number.

### 4h. Tag-dimension coverage (sidecar troubleshooting)

For each skill that has at least one test, compute which values from the Tag Taxonomy are exercised. Report the variable dimensions (the `skill` dimension is trivially covered and `tier` is already reported in the Summary table):

- **Mode** — now a **scored slice** (Phase 4f-mode), not a sidecar tick. Report it in the Per-Mode Coverage table, not here.
- **Shape** — tick each of `shape:single-node`, `shape:multi-node` (applies to flow-building skills only).
- **Node** — list values present under `node:*` for skills where that axis applies.
- **Resource / Connector / Windows** — flat boolean markers; report count of tasks carrying each (`resource`, `connector`, `windows`) for skills where they apply.
- **Feature** — list `feature:*` tags present vs a reasonable "expected" set for this skill (derived from SKILL.md — e.g. `uipath-human-in-the-loop` should exercise `feature:approval-gate`, `feature:write-back`, `feature:escalation`; `uipath-maestro-flow` should exercise `feature:registry`, `feature:transform`, `feature:http`, …). If the skill's vocabulary is open, list what's present without the ✗ column.

This is structured data for the per-skill report (see template below). It is NOT folded into the weighted overall score — adding it on top of Components/Steps would double-count (a missing edit-scenario test already shows up as a workflow-step gap).

### 4i. Automatic gap signals

Run these checks and emit findings into the "Coverage Gaps — Priority Ranked" section with the specified priority. The goal is consistent, data-driven flagging across skills rather than ad-hoc prose:

| Signal | Condition | Priority | Gap title template |
|---|---|---|---|
| **Edit-scenario gap** | The skill teaches an edit workflow (it documents modifying an existing artifact — common for `uipath-maestro-flow`, `uipath-rpa`, `uipath-agents`) but no test exercises that scenario (no task under `tests/tasks/<skill>/edit/` and no `initial_prompt` describes modifying an existing artifact). | **High** | "Editing existing `<artifact>`" |
| **Mode gap** | A mode with a non-trivial labeled capability surface (Phase 2f) is below threshold coverage (Phase 4f-mode). N/A modes (no surface) do not fire — a catalog skill with no `diagnose` surface is not penalized. **Name the specific Phase 2f-i archetype(s) untested** (e.g. O4 instance lifecycle, D1 validate→fix loop). | **High** if a mode with a real surface sits at 0%; **Medium** otherwise | "Missing `<mode>` coverage — `<archetype>` untested" |
| **Mode tag-drift** | A skill's operate/diagnose capability is covered *only* by tests tagged `mode:build` or carrying no `mode:*` (Phase 4f-mode cross-check / Phase 2f-i meta-finding). | **Medium** | "Re-tag `<test>` as `mode:<operate\|diagnose>`" |
| **Negative-test gap** | The skill's SKILL.md lists ≥3 anti-patterns and zero tests assert on any of them. | **High** | "Negative tests for anti-patterns" |
| **Tier gap** | The skill has tests but is missing a tier (smoke-only, integration-only, or e2e-only). | **High** (if smoke or e2e is missing — those are the minimum bar), **Medium** (integration missing) | "Missing `<tier>` tier" |

Whenever a signal fires, the corresponding recommendation in the Recommendations section of the per-skill report must include the tag list that would address it (e.g. a "Brown-field modification" recommendation ships with `(e2e, mode:build, …)`).

## Phase 5 — Write reports

Create `tests/reports/` if needed.

**Pre-write consistency check (run before writing each per-skill report).** The same numbers now appear in several places; verify they agree, then fix the source of any mismatch before writing — never publish inconsistent figures:
1. **Score Contribution total == Summary Overall %.** `Σ contribution_i` must equal the Overall (within rounding). If not, the weights and dimension %s disagree — recheck which figures feed the overall (components = direct-only, Phase 4a).
2. **Header weights == Score Contribution weights.** The `W% weight` in each scored section header is the renormalized weight from the contribution table; N/A dimensions carry no weight in either place, and the weights sum to 100%.
3. **Top untested buckets are real `None` groups.** Every bucket in the SUMMARY row traces to actual `None` rows / category gaps in this report's Component Coverage (or step/rule groups for planning skills) — no invented groupings.
4. **Largest `Lost` aligns with the top gap.** The dimension with the biggest `Lost (pts)` should be the one the #1 High-priority gap / top Recommendation addresses; if they diverge, re-rank or explain why.

**Emit the machine-readable sidecar.** In `all` mode, also write `tests/reports/coverage.json` — a structured mirror of the Overview so downstream consumers (e.g. `/generate-confluence-scorecard`) read data instead of scraping markdown. One object per skill keyed by skill name:

```json
{
  "generated": "YYYY-MM-DD",
  "skills": {
    "uipath-rpa": {
      "overall_pct": 42, "planned": false, "tests": {"smoke": 4, "integration": 1, "e2e": 1},
      "components": {"direct": 11, "direct_indirect": 17, "total": 39, "direct_pct": 28},
      "workflow": {"covered": 4, "total": 6, "pct": 67},
      "rules": {"covered": 6, "total": 28, "pct": 21},
      "paths": {"covered": 3, "total": 3, "pct": 100},
      "weights": {"components": 45, "workflow": 25, "rules": 15, "paths": 15},
      "contribution": {"components": 12.6, "workflow": 16.8, "rules": 3.2, "paths": 15.0},
      "mode_coverage": {"build": {"pct": 31, "covered": 8, "total": 26}, "operate": {"pct": 0, "covered": 0, "total": 4}, "diagnose": null},
      "mode_balanced": 16, "mode_floor": 0,
      "top_untested": ["triggers 0/3", "IS connectors 0/2", "run/publish 2/8"],
      "infra": "Requires Windows + Studio"
    },
    "uipath-document-understanding": {"overall_pct": 0, "planned": true}
  }
}
```

Use `null` for N/A dimensions (e.g. `"rules": null` for a catalog skill, `"paths": null` for single-path). The `contribution` values must match the per-skill Score Contribution tables and sum to `overall_pct`. `mode_coverage` carries one object per mode (`{pct, covered, total}`) or `null` for a mode with no capability surface (Phase 4f-mode) — this is the per-mode coverage `/generate-confluence-scorecard` pairs with its per-mode eval. `mode_balanced` (mean of non-N/A mode pcts) and `mode_floor` (min of non-N/A mode pcts) are the descriptive headlines from Phase 4f-mode — integers, or omitted/`null` for planned skills. Single-skill runs may write/refresh just that skill's entry; do not blank the others.

**Cross-cutting capability entries** carry the same shape plus `"cross_cutting": true`, `"tag": "<tag>"`, and `"host_skills": [...]` so consumers (e.g. `/generate-confluence-scorecard`'s ECS row) can read them and know NOT to add their tests/components into repo-wide totals:
```json
"uipath-context-grounding": {
  "overall_pct": 0, "cross_cutting": true, "tag": "context-grounding",
  "host_skills": ["uipath-agents", "uipath-maestro-flow"],
  "tests": {"smoke": 0, "integration": 0, "e2e": 0},
  "components": {"direct": 0, "direct_indirect": 0, "total": 6, "direct_pct": 0},
  "rules": {"covered": 0, "total": 7, "pct": 0}, "workflow": null, "paths": null,
  "weights": {"components": 70, "rules": 30}, "contribution": {"components": 0, "rules": 0},
  "top_untested": [...], "infra": "Local-only (validate); cloud auth for index/run"
}
```
(Fill the real numbers — components from the modes×surfaces matrix, tests by tag, etc. Coverage shape is **Components + Rules** with Path and usually Workflow N/A, so renormalize to ~Comp 70% / Rules 30% per Phase 4f. A cross-cutting entry also carries `mode_coverage`/`mode_balanced`/`mode_floor` like any skill — context-grounding is build-dominant, so its operate/diagnose slices are typically N/A and Mode-floor ≈ the build slice.)

**Roll-up reconciliation (run AFTER all reports + SUMMARY + coverage.json are written, before reporting done).** The three artifacts are produced separately — in `all` mode often by parallel sub-agents — so they can drift. `coverage.json` is the contract `/generate-confluence-scorecard` consumes, so a mismatch silently corrupts the scorecard. Verify and fix before finishing:
1. **coverage.json ↔ per-skill report.** For each skill, `overall_pct`, the tier counts, and the dimension %s in `coverage.json` equal the headline figures in `tests/reports/<skill>.md`. 
2. **coverage.json ↔ SUMMARY Overview.** Every skill row in `SUMMARY.md`'s Overview table matches its `coverage.json` entry (Overall %, tests, top-untested buckets).
3. **Roster completeness.** The set of keys in `coverage.json` == existing `skills/uipath-*/` folders ∪ planned-registry entries ∪ cross-cutting-registry entries; no skill missing, none stale. Planned-but-missing skills are `{"overall_pct":0,"planned":true}`; cross-cutting entries carry `"cross_cutting":true`. The repo-wide **Totals** in SUMMARY must **exclude** `cross_cutting` entries (their tests/components are already counted in the host skills) — verify the Totals math sums only normal skills.
4. **Cross-agent sanity (parallel `all` runs).** Spot-check that independent sub-agents applied the weights consistently for same-shape skills (e.g. all catalog skills use Comp 65/Steps 35 or Comp 100); reconcile any outlier interpretation. A quick `python3 -c "import json; ..."` over `coverage.json` is the cheapest way to run checks 1–3.

**Output rules:**

| Invocation | Files written |
|---|---|
| Single skill (e.g. `uipath-maestro-flow`) | `tests/reports/<skill-name>.md` only. |
| Single planned skill (folder missing, name in registry) | `tests/reports/<skill-name>.md` using the **planned-skill template** below. |
| `all` (or empty) | One per-skill report **and** the roll-up: `tests/reports/<skill-name>.md` for every existing skill, `tests/reports/<skill-name>.md` for every planned-but-missing skill (planned template), `tests/reports/<capability>.md` for every cross-cutting registry entry (with-tests template, sourced from its inventory doc + tag-selected tasks), `tests/reports/SUMMARY.md`, **and** `tests/reports/coverage.json`. |
| Single cross-cutting capability (e.g. `uipath-context-grounding`) | `tests/reports/<capability>.md` (with-tests template); refresh just its `coverage.json` entry. |
| User-specified custom path | Use that path instead. |

Overwrite any existing report at the same path. The summary file name is `SUMMARY.md` (uppercase), matching the directory structure documented in `tests/README.md`.

Choose the per-skill template by state:

| Skill state | Template |
|---|---|
| Folder exists, has ≥1 test | **Per-Skill (with tests)** |
| Folder exists, zero tests | **Per-Skill (no tests)** |
| Folder does NOT exist, name in Planned Skills Registry | **Per-Skill (planned, not yet created)** |
| Cross-cutting registry entry | **Per-Skill (with tests)** if tag matches ≥1 task, else (no tests). Header it "Cross-cutting capability" and add a note: tests are tag-selected and counted under host skills (non-additive); coverage source is the inventory doc, not a SKILL.md. |

---

## Report Template: Per-Skill (with tests)

Use this template when the skill has at least one test task.

```markdown
# Test Coverage Report: <skill-name>

*Generated: YYYY-MM-DD*

> **How to read this report.** Coverage counts `Direct + Indirect` as covered; only `None` rows (`—/—/—`) forfeit score points. **Direct** = a test asserts this by name. **Indirect** = a test would fail without it but never asserts it (not a gap). **None** = untested even indirectly — this is what the score penalizes and what the gaps/recommendations target. The headline **Overall %** uses **direct-only** component coverage; each scored section header shows its renormalized weight, and the Score Contribution table decomposes the Overall into per-dimension points. Test Coverage is *capability* coverage, **not** a pass-rate.

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
| Per-mode coverage (B/O/D) | 31% / 0% / N/A *(scored slices — see Per-Mode Coverage; reported beside Overall, not folded in)* |
| Mode-balanced / floor | 16% / 0% *(mean & min of non-N/A mode slices — exposes mode blindness the Overall dilutes; descriptive, not scored)* |
| **Estimated overall coverage** | **Z%** (weights: Comp W1% / Steps W2% / Rules W3% / Path W4% — renormalized over applicable dimensions) |

Anti-patterns are inventoried in the Anti-Patterns section below but are **not** part of the overall score (see Phase 4e).

### Score Contribution

Decomposes the overall % into per-dimension points so the penalty is legible — each row is `renormalized weight × that dimension's coverage %`, and the **Contribution column sums to the Overall %**. "Lost" = the points that dimension forfeits vs a perfect 100% (`weight − contribution`); the biggest "Lost" value is where adding tests moves the number most. Use the **same dimension % that feeds the overall** (per Phase 4f) — for Components that is the direct-only %.

| Dimension | Coverage % | Weight (renorm.) | Contribution (pts) | Lost (pts) |
|-----------|-----------|------------------|--------------------|------------|
| Components | 28% | 45% | 12.6 | 32.4 |
| Workflow steps | 67% | 25% | 16.8 | 8.2 |
| Critical rules | 21% | 15% | 3.2 | 11.8 |
| Path | 100% | 15% | 15.0 | 0.0 |
| **Overall** | — | **100%** | **≈48%** | **52** |

(Example is illustrative — use the skill's real numbers; N/A dimensions are dropped and their weight redistributed before computing, so the weight column always sums to 100%. The Contribution total MUST equal the Overall % in the Summary table — if it doesn't, the Summary weights and the dimension %s are inconsistent; fix that before publishing.)

### Test-density troubleshooting

- Total test tasks: N
- Median tests per component: X
- Max tests per component: X (on `<component>`)
- ⚠ *single-test-dominance:* emit this bullet only when one test accounts for >1/3 of Direct component hits — name the test.

> **Infrastructure:** <what this skill requires to run tests — e.g., "Requires cloud auth for debug/deploy tests. Local-only for validate/bundle.">

## Test Inventory

| Test ID | Type | Tags | Description | Components Exercised |
|---------|------|------|-------------|---------------------|
| skill-flow-calculator | e2e | mode:build, shape:multi-node | Multiply two inputs via script node | `core.action.script`, input vars, output vars, validate, debug |

## Component Coverage (X/Y direct, W% weight)

Each scored dimension's header carries its **renormalized weight** (the same one in the Score Contribution table) so readers see each section's contribution in place — e.g. `## Component Coverage (11/39 direct, 45% weight)`, `### Workflow Steps (3/7 covered, 25% weight)`. The weight is the *effective* weight after N/A dimensions are dropped; it must match the Score Contribution table. The per-category sub-headers below stay weightless (the weight applies to the Components dimension as a whole).

### <Category> (X/Y covered)

| Component | Direct | Indirect | Test(s) |
|-----------|--------|----------|---------|
| `core.action.script` | Yes | — | skill-flow-calculator, skill-flow-dice-roller, skill-flow-bellevue-weather |
| `core.logic.loop` | — | — | — |

(One subsection per component category.)

### Workflow Steps (X/Y covered, W% weight)

| # | Step | Covered | Test(s) | Notes |
|---|------|---------|---------|-------|
| 0 | Resolve uip binary | Indirect | all (implicit) | All tests require it but none assert it |
| 4 | Plan the flow | No | — | No test checks for .uipath.flow.arch.plan.md or .uipath.flow.impl.plan.md |

### Critical Rules (X/Y covered, W% weight)

| # | Rule | Direct | Indirect | Test(s) |
|---|------|--------|----------|---------|
| 4 | Always --output json | Yes | — | skill-flow-init-validate |
| 7 | Every node needs definitions | — | Yes | all e2e (validation would fail without them) |
| 5 | Edit .flow ONLY | — | — | — |

### Path Coverage (X/Y paths exercised, W% weight)

Applicable only when the skill documents ≥2 implementation paths. Otherwise write "N/A — single-path skill" and skip the table (drop its weight from the header — it is not a scored dimension for this skill).

| Path | Exercised | Test(s) |
|------|-----------|---------|
| Coded (C#) | Yes | skill-rpa-coded-test-case |
| XAML | No | — |

### Per-Mode Coverage (scored slices)

Re-slices the capability inventory by the Phase 2f mode labels and re-runs the weighted formula per slice (Phase 4f-mode). Reported beside — never folded into — the Overall. `N/A` = the skill has no capability surface for that mode.

| Mode | Capabilities (covered/total) | Coverage % | Covering tests |
|------|------------------------------|-----------|----------------|
| `build` | 8/26 | 31% | skill-flow-calculator, skill-flow-init-validate, … |
| `operate` | 0/4 | 0% | — |
| `diagnose` | — | N/A | — |

⚠ *tag mismatch:* emit a bullet when a capability's only covering test carries the wrong `mode:*` tag (Phase 4f-mode cross-check) — name the test and the expected mode.

### Anti-Patterns (X/Y covered — troubleshooting only, NOT in overall score)

| # | Anti-Pattern | Covered | Test(s) | Notes |
|---|-------------|---------|---------|-------|
| 1 | Never guess node schemas | No | — | Would need negative test |

### Tag-Dimension Coverage

Sidecar troubleshooting — see Phase 4h. Not part of the weighted overall score.

**Mode** — scored separately in the **Per-Mode Coverage** section above; not repeated as a sidecar tick.

**Shape** (flow-building tests only)

| Value | Tests | Status |
|---|---|---|
| `shape:single-node` | skill-flow-decision, skill-flow-rpa, … | ✓ |
| `shape:multi-node` | skill-flow-calculator, skill-flow-customer-escalation, … | ✓ |

**Node**

`node:decision` (3), `node:switch` (2), `node:hitl` (1), …

**Resource / Connector**

`resource` (4 tasks), `connector` (22 tasks).

**Feature tags in use**

`feature:registry` (1), `feature:transform` (2), `feature:http` (4), …

(For skills with a clear "expected" feature set — e.g., HITL should exercise `feature:approval-gate`, `feature:write-back`, `feature:escalation` — use the Status column with ✓/✗. For skills with open vocabulary, list counts.)

## Untested Features

Group by theme. Include cross-cutting features (variable management, expression syntax, planning phases, publishing, editing existing artifacts, etc.) that have no coverage:

- **Control flow:** `core.logic.switch`, `core.logic.loop`, `core.logic.merge`, `core.subflow`, `core.logic.terminate`
- **Publishing:** `uip solution upload`, `uip flow pack`
- **Planning:** Phase 1 arch plan generation, Phase 2 impl plan resolution, mermaid diagram validation
- **Editing:** No test modifies an existing flow (all tests create from scratch)

## Coverage Gaps — Priority Ranked

Gap titles are short descriptions — the exact string a reader would paste into `/generate-task <description>`. Each title must be self-contained enough that `/generate-task` can infer the target skill from it (mention the skill name or its CLI surface). Include entries emitted by the Phase 4i automatic signals (edit-scenario gap, mode gap, negative-test gap, tier gap) alongside skill-specific gaps.

### High Priority

Gaps where an agent getting it wrong would cause expensive failures or silent bugs.

1. **<Gap title — noun phrase>** — <What's untested, specific risk>. *Suggested test:* `<suggested-task-id>` (tier, mode:X, shape:X, node:X, …features) — <one sentence describing the test>.

### Medium Priority

Gaps in secondary capabilities or uncommon paths.

### Low Priority

Gaps in edge cases or features that other tests partially cover indirectly.

## Recommendations

Top 5–10 tests to write next, ordered by how much coverage they add. Each recommendation carries the full proposed tag list so `/generate-task` can consume it verbatim.

1. **`<suggested-task-id>`** (e2e, mode:build, shape:multi-node, node:loop, node:transform) — Covers: `core.logic.loop`, `core.logic.merge`, `core.action.transform`, iteration pattern. *Why:* The entire control-flow family is untested; a single test with a loop-and-merge topology covers 4 components.
2. **`skill-flow-edit-loop`** (e2e, mode:build, shape:multi-node, node:loop) — Covers: editing an existing flow, adding a loop node to an existing topology. *Why:* No test exercises brown-field modification — modifying existing flows is a first-class workflow in this skill.
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

Recommend 2 smoke tests and 2 e2e tests to establish baseline coverage (per CONTRIBUTING.md minimum bar: 1 smoke + 1 e2e). For each, include the full proposed tag list so `/generate-task` can consume the recommendation verbatim:

1. **`<suggested-task-id>`** (smoke, mode:build) — Covers: <components, rules>. *Why:* <rationale>. <Infrastructure note if needed.>
2. **`<suggested-task-id>`** (e2e, mode:build, shape:multi-node, feature:<X>) — Covers: <…>. *Why:* <…>.
```

---

## Report Template: Per-Skill (planned, not yet created)

Use this stub when the skill is in the **Planned Skills Registry** but `skills/<name>/` does not exist yet. Do not attempt component/rule/step extraction — there is no source. Keep the file short; its job is to keep the gap visible in the summary.

```markdown
# Test Coverage Report: <skill-name>

*Generated: YYYY-MM-DD*

> **Status:** Planned — skill folder `skills/<skill-name>/` does not exist yet. Coverage is 0% by definition. This report will be regenerated automatically once the folder lands and tests are added; no manual cleanup needed.

## Summary

| Metric | Value |
|--------|-------|
| Total test tasks | 0 |
| Components inventoried | — (skill not yet authored) |
| Workflow steps | — |
| Critical rules | — |
| Anti-patterns | — |
| **Estimated overall coverage** | **0%** |

**Domain hint:** <one-line hint from the Planned Skills Registry — e.g., "Document Understanding (extraction, classification, validation)">

## Next Steps

1. Author `skills/<skill-name>/SKILL.md` per the repo's skill-structure rules.
2. Add `tests/tasks/<skill-name>/` with at minimum 1 smoke + 1 e2e test (the repo's minimum bar).
3. Re-run `/test-coverage <skill-name>` (or `/test-coverage all`) — this stub is overwritten with a full report once the folder exists.
```

---

## Report Template: Summary Roll-Up

Produce this whenever more than one skill is analyzed (including `all` mode).

```markdown
# Test Coverage Summary

*Generated: YYYY-MM-DD*

## Overview

| Skill | Tests | Components (direct) | Workflow | Rules | Paths | Overall | Mode B/O/D | Bal/Floor | Tests/Comp (med) | Top untested buckets | Infra |
|-------|-------|---------------------|----------|-------|-------|---------|------------|-----------|------------------|----------------------|-------|
| uipath-maestro-flow | 49 | 6/24 (25%) | 6/9 (67%) | 1/16 (6%) | 1/2 (50%) | 33% | 33/0/— | 17/0 | 2 | control-flow 5/7, queue 0/2, resource 0/3 | Requires cloud auth |
| uipath-rpa | 2 | 0/39 (0%) | 0/8 (0%) | 0/21 (0%) | 1/2 (50%) | 8% | 8/0/— | 4/0 | 0 | triggers 0/3, IS connectors 0/2, run/publish 2/8 | Requires Windows + Studio |
| uipath-platform | 5 | 2/12 (17%) | N/A | N/A | N/A | 17% | 17/17/— | 17/17 | 0 | orchestrator-admin 7/15, jobs-adv 0/4 | Requires cloud auth |
| uipath-document-understanding | 0 | — / — (0%) | — | — | — | **0%** (planned) | — | — | — | — (planned) | Skill folder not yet created |
| uipath-context-grounding ⁺ | 10 | 4/6 (67%) | N/A | 3/7 (43%) | N/A | 60% | 67/—/— | 67/67 | — | index-search 0/2, low-code DeepRAG 1/2 | Cross-cutting (agents+flow); local validate / cloud run |

Overall is weighted and renormalized across applicable dimensions (see Phase 4e). N/A cells mean the skill is missing that dimension (e.g. no Critical Rules section, single-path skill, catalog skill with no workflow steps) — weights redistribute proportionally. Planned-but-missing skills (no `skills/<name>/` folder yet) are scored at 0% and tagged "(planned)" in the Overall column; they appear in the same table — do not split them out, so the gap is impossible to overlook. **Cross-cutting capabilities** (⁺, e.g. `uipath-context-grounding`) appear as their own row but are **additive overlays** — their tests/components are already counted in the host skills, so they are EXCLUDED from the Totals line below. **Mode B/O/D** is the compact per-mode coverage (`build`/`operate`/`diagnose`, Phase 4f-mode) — `—` marks an N/A mode (no capability surface); these are scored beside Overall, never folded into it. **Bal/Floor** is Mode-balanced (mean of non-N/A mode slices) / Mode-floor (min of them, Phase 4f-mode): a high Overall with a low Floor flags a build-solid but mode-blind skill. **Top untested buckets** (Phase 4a) names the 2–3 largest `None` groups dragging each skill's score; full detail lives in each report's Untested Features section.

**Totals (normal skills only — excludes planned stubs and cross-cutting ⁺ overlays to avoid double-counting):** N tests across M skills (P planned, not yet authored; Q cross-cutting capabilities reported separately). X components inventoried, Y directly tested (Z%). A workflow steps, B covered. C critical rules, D directly tested. E multi-path skills, F with full path coverage. Anti-patterns are inventoried per skill but intentionally excluded from the overall score.

## Planned Skills (folder not yet created)

List every entry from the Planned Skills Registry whose folder is still missing. Once a folder lands, it falls out of this section and into the regular roll-up rows automatically.

| Skill | Domain hint | Stub report |
|---|---|---|
| uipath-document-understanding | Document Understanding (extraction, classification, validation) | [uipath-document-understanding.md](uipath-document-understanding.md) |

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

The table also surfaces the **tier gap** signal from Phase 4i: a skill with tests but missing a tier (smoke-only, e2e-only) is flagged even if it technically meets the smoke+e2e minimum.

| Skill | Smoke | Integration | E2E | Status |
|-------|-------|-------------|-----|--------|
| uipath-maestro-flow | 2 | 5 | 8 | Meets minimum |
| uipath-rpa | 0 | 0 | 0 | Below minimum (missing smoke + e2e) |
| uipath-data-fabric | 2 | 0 | 1 | Tier gap (no integration tier) |

## Top 10 Recommended Tests

Across all skills, prioritized by coverage impact. Prefer tests that are feasible to implement (local-only or cloud-auth-only over platform-specific). Each recommendation carries the full proposed tag list so `/generate-task` can lift it verbatim.

1. **`skill-<name>-<capability>`** (<skill>, tier, mode:X, shape:X, node:X, …features) — <what it covers and why>. <Infra note if needed.>
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
11. **Tag every recommendation.** Suggested tests in the Gaps and Recommendations sections must carry the proposed tag list (tier, mode, shape, node, features) from the Tag Taxonomy. These recommendations feed `/generate-task` — the validated tag set must travel with them so no inference is required downstream.
12. **Minimum bar lives in the summary.** The smoke+e2e minimum-bar check lives in the summary's Minimum Bar Check section and nowhere else. Per-skill reports may note the status but must not restate the rule — link back to the summary instead.
13. **Planned skills count as 0%.** Every entry in the Planned Skills Registry (Phase 1) whose folder is missing produces a stub report via the planned-skill template AND a row in the summary roll-up at 0% coverage. Do not silently drop them just because there is no SKILL.md to extract from — that is the entire point of the registry. Once `skills/<name>/` exists, the existence check in Phase 1 step 1 routes the skill into the normal templates automatically, with no edit to this command file required. Only edit the registry to add a new planned skill or remove a cancelled one.
