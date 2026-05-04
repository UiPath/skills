# Non-PDD Lane Guide

When the planner is invoked without an SDD (the entry guard found no `## Planner Handoff` marker, or the user picked "Other context" at the entry guard prompt), it runs Lane B — elicit preferences, detect project type, write a plan, hand off to specialists. This guide covers Lane B end-to-end.

> Lane B is appropriate for non-trivial UiPath requests without a PDD: ambiguous tasks, multi-skill orchestration, project-type detection from the filesystem. For trivial single-skill tasks, the main agent should load the specialist directly without the planner.

## Step 1 — Upfront elicitation

Ask only the questions the user's request does not already answer. **One at a time** — wait for each response before asking the next.

### Question 1 — Generation approach

> How would you like me to work?
>
> 1. **Explore first, then plan** — analyze the project and requirements, run non-mutating discovery, then present a plan for approval before any project changes *(recommended for non-trivial requests)*
> 2. **Explore, plan, and execute simultaneously** — emit the plan as text and the main agent starts executing right away

**Skip this question** when the request is simple and well-defined, the user is modifying an existing automation, or the task is single-skill single-step.

**If "explore first, then plan":**
- You may run non-mutating discovery: `uip rpa analyze`, `uip rpa get-errors`, reading `project.json`.
- Do NOT run commands that mutate the project (create files, register targets, install packages) — those belong to execution.
- After Steps 2–4, call `EnterPlanMode` with the plan. User approves → `ExitPlanMode`.

**If "explore, plan, and execute simultaneously":**
- Emit the plan as text in Step 5. The main agent loads the first specialist skill immediately and follows that skill's own workflow.
- Do NOT call `EnterPlanMode`.

### Question 2 — Execution autonomy

> Once execution starts, how should I handle ambiguity or scope concerns?
>
> 1. **Autonomous to completion** *(recommended)* — follow the plan end-to-end without stopping for confirmation. Specialist skills handle their own pause points (auth failure, UI capture limits, etc.).
> 2. **Interactive** — pause and confirm on structural decisions, scope concerns, or side-effect actions during execution.

Record the answer in the plan header as `Execution autonomy: autonomous | interactive`. Specialist skills read this field at runtime — in autonomous mode they do NOT re-ask decisions the plan already makes.

**Skip this question** only in explore-first mode — the approval gate at plan time already scopes autonomy. Default to `autonomous` for simultaneous mode when the user does not specify.

### Project type — infer first, ask only if vague

Resolve project type without asking when possible. Stop at the first match:

1. **User explicitly named a mode** ("xaml workflow", "coded workflow", "C# workflow", ".cs file", "low-code") → honor it. Record `Project type: XAML` or `Project type: C# coded` in the plan header.
2. **Keyword signals** (look for these in the user's request, but do not echo them as labels) →
   - "agent", "AI agent", "agentic", "LLM", "LangGraph", "LlamaIndex", "OpenAI Agents" → **AI Agent**
   - "flow", "orchestrate multiple automations", `.flow` → **Flow**
   - "web app", "app", "React", "Angular", "Vue", `.uipath/` → **Application**
3. **Filesystem signals** (Step 3) → route per the Step 3 table.
4. **Default** → **RPA workflow (XAML)**. Covers ~95% of UiPath work — UI automation, form-fill, Excel / email / file ops.

Only ask if the request is genuinely vague ("I want to build something with UiPath") AND no keyword or filesystem signals apply:

> What kind of project should I scaffold?
>
> 1. **RPA workflow** — UI automation, Excel / email / file work *(recommended — covers ~95% of UiPath work)*
> 2. **AI Agent** — autonomous agent that reasons with an LLM and calls tools
> 3. **Flow** — visual node-based orchestration connecting multiple automations
> 4. **Application** — custom UI deployed as a UiPath App

If the user picks **RPA workflow**, record `Project type: XAML` and move on. **Never follow up with "XAML or C#?"** — that authoring-mode decision belongs to `uipath-rpa`, not the planner. Coded mode is set only when the user independently says "coded workflow" or ".cs file" (which rule 1 above already honors); never as a follow-up.

### Default — Expression language

Always use **VB.NET** for XAML workflows. Note this in the plan. Do not ask.

## Step 2 — Detect multi-skill requests

Before filesystem detection (Step 3), check whether the request matches a multi-skill pattern. Multi-skill requests usually combine "build" + "deploy", "build" + "verify", or one product depending on another.

See [multi-skill-patterns-guide.md](multi-skill-patterns-guide.md) for the 6 named patterns. If the request matches one, emit a multi-skill plan in that pattern's order. Otherwise, treat it as single-skill and proceed to Step 3.

## Step 3 — Filesystem detection (single-skill requests)

> **Check first:** if the request mentions deploy / publish / Orchestrator alongside a clear domain, it likely needs a multi-skill plan from Step 2.

Probe the project context:

```bash
echo "=== CWD ===" && ls -1 project.json *.cs *.xaml *.py pyproject.toml flow_files/*.flow .uipath/ app.config.json .venv/ 2>/dev/null; \
echo "=== PARENT ===" && ls -1 ../project.json ../*.cs ../*.xaml ../pyproject.toml 2>/dev/null; \
echo "=== FRAMEWORK ===" && cat project.json 2>/dev/null | grep -o '"targetFramework"[^,}]*' || echo "targetFramework: not found"; \
echo "=== DONE ==="
```

| Filesystem signal | Plan skill |
|---|---|
| `.xaml` files + `project.json` with `targetFramework: "Legacy"` or absent | `uipath-rpa-legacy` |
| `.xaml` AND/OR `.cs` files + `project.json` with any other `targetFramework` | `uipath-rpa` |
| `flow_files/*.flow` | `uipath-maestro-flow` |
| `.uipath/` or `app.config.json` | `uipath-coded-apps` |
| `.venv/` AND `pyproject.toml` with uipath dependency | `uipath-agents` |
| `project.json` only (no `.cs`/`.xaml`) | Check `targetFramework` — `"Legacy"` or absent → `uipath-rpa-legacy`; otherwise → `uipath-rpa` |

**Multiple signals?** Go back to Step 2 and emit a multi-skill plan.

**No signals?** Use Step 1 answers. If still undetermined, plan with best available info and note the assumption.

## Step 4 — UI element targeting (only when the plan includes UI automation)

If the plan loads `uipath-rpa` for a workflow that clicks, types into, or reads elements in a desktop or browser app, ask the three UI questions in **one batched** `AskUserQuestion` call (see [pdd-driven-lane-guide.md → Step 5](pdd-driven-lane-guide.md#step-5--ui-element-targeting-only-when-9-contains-ui-applications) for the exact wording — same questions, same skip rules apply). Skip any question already resolved from the user's request.

Skip the entire batch for non-UI plans (pure data processing, API calls, agent-only, flow-only).

Record the answers in the plan header. The handoff is informational — `uipath-rpa` does not read the plan file; it runs its own target-configuration flow when invoked. The plan-header fields exist so the human reviewer and the main agent retain the decisions in context.

## Step 5 — Write the plan

Compose `<feature>.md` per the schema in [plan-and-tasks-format.md → Non-PDD lane](plan-and-tasks-format.md#non-pdd-lane-featuremd). Plan body holds the task list with the same task row schema as Lane A.

### Self-review before saving

1. **Coverage** — every requirement appears in at least one task.
2. **Placeholder scan** — no "TBD", "TODO", "as needed", "if appropriate", "similar to".
3. **Skill order** — correct specialist per task; skills load in the right order (e.g., RPA before platform deploy; testing before deploy).
4. **Validation gaps** — every generation task ends with a `Validate:` compile / build / lint check.
5. **Testing task present** — a dedicated `Testing (MANDATORY)` task exists for every generation skill in the plan. Routes to the specialist's testing references — does not describe the procedure.
6. **No internal-flow leakage** — the plan does not duplicate steps from any specialist's own references.
7. **Anti-hallucination rule** appended to every Skill prompt.

Fix issues before saving.

### Save location

Save as `YYYY-MM-DD-<feature-name>.md`:

- **Project directory exists** (`project.json`, `flow_files/`, `.uipath/`, or `pyproject.toml`) → save to `docs/plans/` within the project. Create the directory if needed.
- **No project directory** → save to `~/Documents/UiPath/Plans/`. Create the directory if needed.

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

| Scenario | `AskUserQuestion` calls |
|---|---|
| Simple single-skill, simultaneous, all signals clear | **1** (autonomy only) |
| Non-trivial, explore-first, all project-type signals clear | **2** (approach + autonomy) |
| Non-trivial, with UI automation | **3** (approach + autonomy + UI batch) |
| Vague request, with UI automation | **4** (approach + autonomy + project-type fallback + UI batch) |
| Resume scenario | **+1** (continue/regenerate) |
| Maximum | **5** |

This is the hard cap defined in the planner's Critical Rules. If you cannot fit the elicitation in 5 calls, plan with best available info and note the assumption in Decisions & Trade-offs.
