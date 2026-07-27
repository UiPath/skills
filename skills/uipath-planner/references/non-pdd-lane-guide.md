# Non-PDD Lane Guide

When the planner is invoked without an SDD (the entry guard found no `## Planner Handoff` marker, or the user picked "Other context" at the entry guard prompt), it runs Lane B — detect context, elicit preferences, write a plan, hand off to specialists. This guide covers Lane B end-to-end.

> Lane B is for non-trivial UiPath requests without a PDD: multi-project orchestration, or requests still ambiguous after detection. Single-project requests exit at Step 2 — the specialist is loaded directly, no plan is written.

Steps run in this order — **detection before elicitation** — so every skip-rule input exists before the question batch is built.

## Step 1 — Detect before asking (no prompts)

All sub-steps are non-interactive. Run them first; their outputs drive the Step 2 exit and the Step 3 skip rules.

1. **Provided context document** — if the entry guard classified a document as "Other context", read it now. Any question its content answers counts as resolved; its content feeds the plan.

2. **Filesystem detection** — use `Glob` / `Read` / `Grep` (cross-platform) in current directory, then in the parent, NEVER shell-specific pipelines (`ls` globs, `grep` over pipes, `/dev/null` fail on native PowerShell):
   - `Glob`: `project.json`, `*.xaml`, `*.cs`, `*.flow`, `flow_files/*.flow`, `*.bpmn`, `caseplan.json`, `agent.json`, `pyproject.toml`, `.uipath/*`, `app.config.json`, `*.uipx`, `element.json`, `*.py`.
   - `project.json` found → `Read` it and check `targetFramework` and dependencies structurally (no regex-over-cat).
   - `pyproject.toml` found → `Read` it and disambiguate: an agent-framework dependency (`langgraph`, `llamaindex`, `openai-agents`) or a sibling `agent.json` → **Agents**; a sibling `uipath.json` with a `functions` map (or `entry-points.json` from `uip functions init`) → **Functions**; a bare `uipath` dependency with neither → inspect further or ask (a `.venv/` directory is NOT required and proves nothing).
   - Root-level `*.json` with none of the above → `Grep` for `"document.dsl"` (API Workflow project).

   | Filesystem signal | Plan skill |
   |---|---|
   | `.xaml` and/or `.cs` files + `project.json` | `uipath-rpa` |
   | `*.flow` (usually under `flow_files/`) | `uipath-maestro-flow` |
   | `*.bpmn` (no `caseplan.json`) | `uipath-maestro-bpmn` |
   | `caseplan.json` | `uipath-maestro-case` |
   | `agent.json` | `uipath-agents` (low-code) |
   | `pyproject.toml` + agent-framework dependency (langgraph / llamaindex / openai-agents) | `uipath-agents` (coded) |
   | `pyproject.toml` + `uipath.json` with a `functions` map | `uipath-functions` |
   | JSON containing `document.dsl` | `uipath-api-workflow` |
   | `.uipath/` or `app.config.json` | `uipath-coded-apps` |
   | `element.json` (+ `element-metadata.json`) | `uipath-connector-builder` |
   | `*.uipx` | `uipath-solution` (deploy/lifecycle ops) |
   | `project.json` only (no `.cs`/`.xaml`) | `uipath-rpa` |

   Multiple signals → the request likely spans projects; classify with the multi-skill patterns below.

   No signals → greenfield request (the normal planning-phase case); project type comes from sub-step 4 inference.

3. **Multi-skill classification** — check the request against the named patterns in [multi-skill-patterns-guide.md](multi-skill-patterns-guide.md) ("build"+"deploy", "build"+"verify", one product depending on another). Record the matched pattern, if any.

4. **Product/project-type inference — need-driven, not keyword.** When no filesystem signal or explicit naming decides it, type the request with the [Product Selection Guide → Level 1](product-selection-guide.md#level-1--primary-scope-selection) need bullets, not surface keywords:
   - Explicit naming still wins ("xaml workflow", "coded workflow", ".cs file", "low-code") → record `Project type: XAML` or `Project type: C# coded`.
   - "AI"/"agent" wording does NOT force an Agent — apply the **determinism gate**: rule-expressible decisions → RPA/API; genuine judgment → Agent.
   - "flow"/"process"/"orchestrate" resolves via the [Maestro disambiguation](product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case) (Flow vs BPMN vs Case) — never assume Flow from the word alone.
   - Headless system-to-system → API Workflow; document extraction → IXP; user-facing screen → Coded Apps; reusable component → RPA Library; regression pack → Test Automation; tenant/resource ops only → `uipath-platform`.
   - Default when nothing contradicts it → **RPA workflow (XAML)** — the most common case for UI / Excel / email / file work.

5. **Delivery-model resolution** — explicit signals ("Automation Suite", "on-prem", "self-hosted", "air-gapped") → record `Delivery model: <value>`. Otherwise run the best-effort `uip login status` preflight and map the host per [sdd-generation-guide.md → Step 0](sdd-generation-guide.md#step-0-determine-execution-mode--delivery-model). Still unresolved AND any candidate product is delivery-gated (anything beyond core RPA + Orchestrator: Maestro, Agents, Coded Apps, API Workflows, Solutions `.uipx`) → add the delivery-model question to the Step 3 batch. If the user answers "not sure" (or cannot be asked), record `Delivery model: unspecified — assumed cloud [ASSUMPTION]` in the plan header plus which products the assumption gates — never omit the field when a gated product is in play. Apply the [Constraint Gate](product-selection-guide.md#constraint-gate) against [platform-availability-guide.md](platform-availability-guide.md) before recommending any product.

## Step 2 — Single-skill exit (stop Lane B)

If Step 1 resolves the request to **one project owned end-to-end by one specialist** — even when it bundles inline HITL / script / connector nodes or its own solution wrapper (author sub-steps, per the Skip paragraph in SKILL.md) — **stop Lane B**:

1. Do NOT write a plan file. Do NOT emit `TaskCreate` calls. Do NOT ask the Step 3 batch.
2. Say which specialist owns it and why ("Single-project `.flow` build — loading `uipath-maestro-flow` directly").
3. Hand off the Step 1 context (detected paths, delivery model, any resolved answers) so the specialist does not re-discover it.

Lane B continues past this step ONLY for multi-project requests (a matched multi-skill pattern, multiple filesystem signals, or separate buildable projects) or requests still genuinely ambiguous after Step 1 inference and the Q3 fallback.

## Step 3 — Upfront elicitation (batched)

Bundle every unresolved question from the table below into **one** `AskUserQuestion` call. Do not ask one at a time; do not split across turns. If a question is already resolved (user's request, context doc, Step 1 detection), omit it from the batch. If **all** are resolved, do not call `AskUserQuestion` at all and record the inferred values in the plan header with a one-line note in Decisions & Trade-offs.

Question phrasing follows the rules in [pdd-driven-lane-guide.md → Step 5](pdd-driven-lane-guide.md#step-5--ui-element-targeting-only-when-9-contains-ui-applications): no internal jargon, no domain or app names in question text.

### Skip-rules table (apply before building the batch)

All inputs below are known by the end of Step 1/2 — no skip rule depends on a later step.

| Question | Skip when | Default if skipped |
|---|---|---|
| Q1 Generation approach | Request is simple and well-defined; the user is modifying an existing automation. | `simultaneous` |
| Q2 Execution autonomy | The user already stated it ("autonomous", "check with me"). Never inferred from Q1 — planning approach and execution autonomy are separate decisions. | `autonomous` |
| Q3 Project type fallback | Step 1 resolved the type (explicit naming, need-driven inference, or filesystem). | `RPA workflow (XAML)` |
| Delivery model | Resolved at Step 1.5 (explicit, preflight); or no delivery-gated product is a candidate. | `unspecified — assumed cloud [ASSUMPTION]` + affected products note |

### Question 1 — Generation approach

> How would you like me to work?
>
> 1. **Explore first, then plan** — analyze the project and requirements, run non-mutating discovery, then present a plan for approval before any project changes *(recommended for non-trivial requests)*
> 2. **Explore, plan, and execute simultaneously** — emit the plan as text and the main agent starts executing right away

**If "explore first, then plan":**
- You may run non-mutating discovery: `uip rpa analyze`, `uip rpa get-errors`, reading `project.json`.
- Do NOT run commands that mutate the project (create files, register targets, install packages) — those belong to execution.
- After Steps 4–5, call `EnterPlanMode` with the plan. User approves → `ExitPlanMode`.

**If "explore, plan, and execute simultaneously":**
- Emit the plan as text in Step 5. The main agent loads the first specialist skill immediately and follows that skill's own workflow.
- Do NOT call `EnterPlanMode`.

### Question 2 — Execution autonomy

Asked in the same batch as Q1 — choosing explore-first does NOT imply autonomous execution afterwards; they are independent decisions.

> Once execution starts, how should I handle ambiguity or scope concerns?
>
> 1. **Autonomous to completion** *(recommended)* — follow the plan end-to-end without stopping for confirmation. Specialist skills handle their own pause points (auth failure, UI capture limits, etc.).
> 2. **Interactive** — pause and confirm on structural decisions, scope concerns, or side-effect actions during execution.

Record the answer in the plan header as `Execution autonomy: autonomous | interactive`. Task prompts carry the plan path (Step 5), so specialists can recover this and other decisions at runtime — in autonomous mode they do NOT re-ask decisions the plan already makes.

### Question 3 — Project type fallback (only when Step 1 could not infer)

> Q3 — What kind of project should I scaffold?
>
> 1. **RPA workflow** — UI automation, Excel / email / file work *(recommended default)*
> 2. **AI Agent** — genuine judgment/reasoning over ambiguous input, LLM tool use
> 3. **Orchestration** — coordinate multiple automations (Maestro Flow / BPMN / Case — disambiguated by the need)
> 4. **Headless / other** — API Workflow, custom web app, document extraction (IXP), reusable Library, Test Automation — say which

(The question UI always offers free-text "Other" — a specific answer there overrides the options.) If the user picks **RPA workflow**, record `Project type: XAML` and move on. **Never follow up with "XAML or C#?"** — that authoring-mode decision belongs to `uipath-rpa`, not the planner. Coded mode is set only when the user independently says "coded workflow" or ".cs file"; never as a follow-up, and never surface C# coded as a top-level recommendation for routine UI automation.

### Authoring surface — never a planner concern

Studio, Studio Web, VS Code — presentation layers over the same artifacts. The planner never asks about, derives, records, or conditions on them; each specialist owns its own surface. User words mentioning a surface travel as ordinary requirement prose in the task prompt, like any other stated preference. Invariant: in explore-first mode, nothing syncs to the tenant before plan approval. The only environment input the planner models is the **delivery model** (Automation Cloud / cloud variant / Automation Suite / standalone).

### Packaging (derived — no standing question)

For every plan with a generation skill, record `Packaging: standalone | solution` in the plan header per [Product Selection Guide → layer 4](product-selection-guide.md#how-selection-works--four-layers): single project → `standalone` (default); multi-project / cross-product / team standardization → `solution` (`.uipx` via `uipath-solution`). This is the deploy-skill decision — `uipath-solution` for `solution`, `uipath-platform` for `standalone` non-solution publishes. Ask only if the user's own words conflict with the derivation.

### Default — Expression language

Always use **VB.NET** for XAML workflows. Note this in the plan. Do not ask.

## Step 4 — UI element targeting (only when the plan includes UI automation)

If the plan loads `uipath-rpa` for a workflow that clicks, types into, or reads elements in a desktop or browser app, ask the three UI questions in **one batched** `AskUserQuestion` call (see [pdd-driven-lane-guide.md → Step 5](pdd-driven-lane-guide.md#step-5--ui-element-targeting-only-when-9-contains-ui-applications) for the exact wording — same questions, same skip rules apply). Skip any question already resolved from the user's request.

Skip the entire batch for non-UI plans (pure data processing, API calls, agent-only, flow-only).

Record the answers in the plan header AND summarize them in the relevant task's Skill prompt. The task prompt also carries the plan path (Step 5), so a resumed or separately-executed task can recover the full decision set from the file.

## Step 5 — Write the plan

Compose `<feature>.md` per the schema in [plan-and-tasks-format.md → Non-PDD lane](plan-and-tasks-format.md#non-pdd-lane-featuremd). Plan body holds the task list with the same task row schema as Lane A.

**Every task's Skill prompt embeds the plan path** — the exact relative or absolute path of the file written below (mirroring Lane A's embedded SDD path). `TaskCreate` copies prompts verbatim; a bare "this plan" leaves a resumed task with no way to find its values.

### Self-review before saving

1. **Coverage** — every requirement appears in at least one task.
2. **Placeholder scan** — no "TBD", "TODO", "as needed", "if appropriate", "similar to".
3. **Skill order** — correct specialist per task; skills load in the right order (e.g., RPA before platform deploy; testing before deploy).
4. **Validation gaps** — every generation task ends with a `Validate:` compile / build / lint check.
5. **Testing task present** — a dedicated `Testing (MANDATORY)` task exists for every generation skill in the plan. Routes to the specialist's testing references — does not describe the procedure.
6. **Plan path present** — every Skill prompt names the plan file path (not "this plan").
7. **No internal-flow leakage** — the plan does not duplicate steps from any specialist's own references.
8. **Anti-hallucination rule** appended to every Skill prompt.

Fix issues before saving.

### Save location

Save as `YYYY-MM-DD-<feature-name>.md`:

- **Project directory exists** (`project.json`, `flow_files/`, `.uipath/`, or `pyproject.toml`) → save to `docs/plans/` within the project. Create the directory if needed.
- **No project directory** → save to `./plans/` (relative to the current working directory). Create the directory if needed.

### Resume handling

If a plan file already exists at the target path, ask the user via `AskUserQuestion`:

> A plan file already exists at `<path>`. How should I proceed?
>
> 1. **Continue with the current plan** *(recommended)* — pick up where you left off; checkbox state preserved
> 2. **Regenerate from the current request** — discard the current plan and rebuild

Option 1: read existing plan → recreate live `TaskCreate` calls with status preserved → done.
Option 2: parse the request fresh, run identity-matching against the old file (preserve completed work), write the new plan, emit live tasks. Same regenerate algorithm as Lane A — see [plan-and-tasks-format.md → Regenerate logic](plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).

## Step 6 — Present the plan

- **Explore first, then plan:** call `EnterPlanMode` with the plan content. User approves → `ExitPlanMode` → emit live `TaskCreate` calls.
- **Explore, plan, and execute simultaneously:** emit the plan as text. Then immediately emit live `TaskCreate` calls. Main agent starts executing.

## Lane B budget

Step 3 is **always one batched call** (Q1 + Q2 + optional Q3/delivery in a single `AskUserQuestion` — at most 4 question objects per call, comfortably within the cap); Step 4 is one batched call when the plan has UI automation; resume adds one. The realistic floor is 0 calls and the realistic ceiling is 3.

| Scenario | `AskUserQuestion` calls |
|---|---|
| Single-skill exit at Step 2 | **0** (no plan, no batch — specialist loaded directly) |
| Simple multi-skill, simultaneous, all signals clear, no UI | **0** (Step 3 fully resolved from context, no UI batch) |
| Non-trivial, no UI automation | **1** (Step 3 batched) |
| Non-trivial, with UI automation | **2** (Step 3 batched + Step 4 UI batch) |
| Vague request, with UI automation | **2** (Step 3 batched — Q3 is part of the same batch — + Step 4 UI batch) |
| Resume scenario | **+1** (continue/regenerate) |
| Realistic maximum | **3** |
| Hard cap (per-phase prompt budget, Critical Rules) | **5** |

The 5-call hard cap is defined in the planner's Critical Rules. If batching collapses the elicitation correctly, you should never approach it.
