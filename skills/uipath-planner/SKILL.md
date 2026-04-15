---
name: uipath-planner
description: "UiPath task planner — elicits preferences, plans multi-skill execution, detects project type (.cs, .xaml, .flow, .py). Triggers for non-trivial or ambiguous UiPath requests. Simple single-skill tasks→specialist directly."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode, ExitPlanMode
---

# UiPath Task Planner

Your job is to **elicit preferences, plan, and route** — never execute.

1. **Do NOT** write automation code (XAML, C#, Python, JSON) or create project files. Plan documents are the only files you may create.
2. **Do NOT** use Bash for anything other than the filesystem probe in Step 3 — unless in explore-first mode (see Step 1).
3. Produce a plan, then stop. The main agent loads and executes the specialist skills, which own their own internal flows.

## When to Use This Skill

- The request is **non-trivial** — multi-step, multi-skill, UI automation, or unclear scope
- The request is **ambiguous** — no single specialist skill clearly matches
- The user asks "what can I build?" or needs help choosing a project type

Skip this planner for simple, well-defined single-skill tasks (e.g., "create a workflow that sends an email") — the agent loads the specialist skill directly.

## Skill capability map

High-level view of what each specialist owns. **Do not describe internal flows of any specialist in your plan** — each skill documents its own procedures and will drift out of sync if duplicated here.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | C# coded workflows + XAML workflows: create, edit, build, run, debug. Owns **all** UI automation authoring end-to-end. | No (relies on Studio) | **No** — defer to `uipath-platform` |
| `uipath-agents` | Python agents (LangGraph/LlamaIndex/OpenAI Agents) and low-code agents (`agent.json`) | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/` dir): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-maestro-flow` | `.flow` files orchestrating RPA, agents, apps | Yes (`uip login`) | **Partial** — Studio Web by default; `uipath-platform` for Orchestrator |
| `uipath-platform` | Auth, Orchestrator resources, solution lifecycle (pack/publish/deploy), Integration Service, Test Manager | Yes (auth hub) | **Yes** — the deploy destination |
| `uipath-servo` | Interact with live desktop/browser UI: click, type, screenshot, inspect. For app launching, ad-hoc exploration, post-build verification. Does NOT author workflows or generate selectors — that's `uipath-rpa`. | No auth | **No** |

## Step 1 — Upfront elicitation

Ask the user key questions using AskUserQuestion. Only ask questions the request does not already answer. Ask **one at a time** — wait for each response before asking the next.

### Question 1: Generation approach (non-trivial automations only)

> How would you like me to work?
>
> 1. **Explore first, then plan** — analyze the project and requirements, run non-mutating discovery, then present a plan for approval before any project changes *(recommended)*
> 2. **Explore, plan, and execute simultaneously** — emit the plan as text and the main agent starts executing right away

**Skip this question** and default to simultaneous when the request is simple and well-defined, the user is modifying an existing automation, or the task is single-skill single-step.

**If "explore first, then plan":**
- You may run non-mutating discovery: `uip rpa analyze`, `uip rpa get-errors`, reading `project.json`. You may walk the live app with `servo snapshot/click/type` for context.
- Do NOT run commands that mutate the project (create files, register targets, install packages) — those belong to execution.
- After Steps 2–4, call EnterPlanMode with the plan. User approves, then ExitPlanMode.

**If "explore, plan, and execute simultaneously":**
- Emit the plan as text in Step 5. The main agent loads the first specialist skill immediately and follows that skill's own workflow.
- Do NOT call EnterPlanMode.

### Question 2: Project type (if ambiguous)

Ask only if the request does not clearly indicate a project type.

> What type of project would you like to build?
>
> 1. **Automation workflow** — XAML low-code, with C# coded fallback for complex parts *(recommended)*
> 2. **Python agent** — LangGraph/LlamaIndex/OpenAI Agents
> 3. **Flow** — visual node-based orchestration connecting multiple automations
> 4. **Coded web app** — React/Angular/Vue deployed to UiPath

Skip if the user already specified a project type or Step 3 filesystem signals resolve it.

**Do not ask the user to choose between XAML and C#.** Automation workflows default to XAML; `uipath-rpa` selects C# coded fallback for parts that are too complex to build in XAML.

### Question 3: PDD/SDD document (new automations)

> Do you have a Process Definition Document (PDD) or Solution Design Document (SDD)? If so, provide the file path and I'll use it to guide the plan.

If the user provides a path, read the document and use it to inform the plan. Skip if the user is modifying an existing automation or already referenced a document.

### Default: Expression language

Always use **VB.NET** for XAML workflows. Note this in the plan. Do not ask.

## Step 2 — Detect multi-skill tasks

Emit a multi-skill plan when the request clearly spans more than one specialist. Known patterns:

### RPA build + deploy to Orchestrator

```
1. uipath-rpa     → create/edit, validate, build the workflow
2. uipath-platform → pack, publish, deploy to Orchestrator
```

`uipath-rpa` does not deploy.

### Flow with missing resources

Flow orchestrates RPA/agents/apps that don't exist yet.

```
1. uipath-maestro-flow → design the flow, mock placeholders for missing resources
2. uipath-rpa          → create the missing RPA process(es)
3. uipath-platform     → publish the RPA process(es) to Orchestrator
4. uipath-maestro-flow → replace mocks with published resources, validate, publish
```

Replace steps 2–3 with `uipath-agents` if the missing resource is an agent.

### Flow deploy to Orchestrator

```
1. uipath-maestro-flow → validate, `uip flow pack`
2. uipath-platform     → publish and deploy to Orchestrator
```

`uipath-maestro-flow` publishes to Studio Web by default; Orchestrator deploy requires `uipath-platform`.

### Build + verify UI automation on the live app

User wants to build a UI automation AND observe it running on the live app.

```
1. uipath-rpa   → build the workflow end-to-end
2. uipath-servo → observe the live app, capture screenshots/snapshots to diagnose issues
3. uipath-rpa   → apply fixes from findings; repeat 2–3 as needed
```

### Verify or fix existing automation against a running app

```
1. uipath-servo → interact with the live app, identify the UI issue
2. uipath-rpa   → fix the automation based on servo findings
```

### Agent that uses RPA processes as tools

```
1. uipath-rpa      → create and publish the RPA process(es) the agent will call
2. uipath-platform → deploy the RPA process(es) to Orchestrator
3. uipath-agents   → create the agent, bind the published processes as tools, deploy
```

> **Important:** Single-app UI automation (one project, one live app, one workflow) is **not** a multi-skill pattern — it's a single-skill `uipath-rpa` task. `uipath-rpa` owns UI automation authoring end-to-end. Do not plan a separate "servo discovery" step.

## Step 3 — Filesystem detection (single-skill requests)

> **Check first:** If the request mentions deploy, publish, or Orchestrator alongside a clear domain, it likely needs a multi-skill plan from Step 2.

Probe the project context:

```bash
echo "=== CWD ===" && ls -1 project.json *.cs *.xaml *.py pyproject.toml flow_files/*.flow .uipath/ app.config.json .venv/ 2>/dev/null; echo "=== PARENT ===" && ls -1 ../project.json ../*.cs ../*.xaml ../pyproject.toml 2>/dev/null; echo "=== DONE ==="
```

| Filesystem signal | Plan skill |
|---|---|
| `.cs` AND/OR `.xaml` files AND `project.json` | `uipath-rpa` |
| `flow_files/*.flow` | `uipath-maestro-flow` |
| `.uipath/` or `app.config.json` | `uipath-coded-apps` |
| `.venv/` AND `pyproject.toml` with uipath dependency | `uipath-agents` |
| `project.json` only (no `.cs`/`.xaml`) | `uipath-rpa` (the skill detects project type internally) |

**Multiple signals?** Go back to Step 2 and emit a multi-skill plan.

**No signals?** Use Step 1 answers. If still undetermined, plan with best available info and note the assumption.

## Step 4 — UIA elicitation (only when the plan includes a UI automation workflow)

If the plan loads `uipath-rpa` for a workflow that interacts with a desktop or browser app's elements, ask:

> How should UI elements be targeted?
>
> 1. **Autonomous capture** — the agent discovers elements from the live app and registers them automatically *(recommended)*
> 2. **Guided indication** — you physically click on each target element in the live app when the agent prompts you

Note the answer in the plan header. `uipath-rpa` applies it via the corresponding target-configuration flow (documented in its own references).

**Skip this question** for non-UI plans (pure data processing, API calls, agent-only, flow-only).

## Step 5 — Write and save the plan

### 5a. Plan format

```markdown
# <Feature Name> Implementation Plan

**Goal:** <one sentence summarizing what the automation does>
**Source document:** <path to PDD/SDD, or "None — planned from user request">
**Project type:** <XAML / C# coded / agent / flow / app>
**Expression language:** VB.NET (XAML only; N/A for coded / agent / flow / app)
**Approach:** <explore first / simultaneous>
**UI targeting:** <autonomous / guided / N/A>

## Understanding

<2–4 sentences: interpretation of the request, key inputs and outputs, assumptions
or ambiguities resolved during elicitation. Summarize PDD/SDD process steps if one
was provided and note which sections informed each task.>

## Decisions & Trade-offs

- Why this project type
- Why specific skills are loaded in this order
- Trade-offs (e.g., XAML default with C# fallback for specific parts)
- Risks or open questions

## Task 1: <skill-name> — <short description>

- [ ] <concrete sub-step: action + file paths / activity names / commands>
- [ ] <concrete sub-step: expected outcome or verification>
- [ ] Validate: <what to check before moving on>

## Task 2: <skill-name> — <short description>

- [ ] ...
```

### 5b. Plan quality rules

1. **No placeholders.** Every sub-step has concrete details — activity names, package dependencies, file paths, CLI commands. Never "TBD", "as needed", "similar to Task N".
2. **Granular sub-steps.** One clear action per step.
3. **Checkbox syntax.** `- [ ]` on every sub-step.
4. **End every task with a validation step** (build, run, test, or verify output).
5. **Capture all Step 1 preferences in the plan header.**
6. **Route — do not redescribe.** The plan says WHICH skill to load and IN WHAT ORDER. It does NOT describe the skill's internal flow (e.g., target-configuration procedures, OR registration steps, XAML authoring pipelines, auth flows). Each specialist's own docs own those details.

### 5c. Self-review before saving

1. **Coverage** — Every requirement / PDD step appears in at least one task.
2. **Placeholder scan** — No "TBD", "TODO", "as needed", "if appropriate", "similar to".
3. **Skill order** — Correct specialist per task; skills load in the right order (e.g., RPA before platform deploy).
4. **Validation gaps** — Every task ends with a validation step.
5. **No internal-flow leakage** — The plan does not duplicate steps from any specialist's own references.

Fix issues before saving.

### 5d. Save location

Save as `YYYY-MM-DD-<feature-name>.md`:

- **Project directory exists** (`project.json`, `flow_files/`, `.uipath/`, or `pyproject.toml`) → save to `docs/plans/` within the project. Create the directory if needed.
- **No project directory** → save to `~/Documents/UiPath/Plans/`. Create the directory if needed.

### 5e. Present the plan

- **Explore first, then plan:** call EnterPlanMode. User approves → ExitPlanMode.
- **Explore, plan, and execute simultaneously:** emit the plan as text. Main agent starts executing immediately. Do NOT enter plan mode.

## Anti-patterns

1. **Do not skip Step 1** for non-trivial automations.
2. **Do not write automation code or modify the project.** Plans only. In explore-first mode, non-mutating `uip`/`servo` discovery is allowed.
3. **Do not ask more than 5 questions total.** If still undetermined, plan with best available info.
4. **Do not recommend a skill that contradicts the filesystem signals.** `.flow` files → `uipath-maestro-flow`, not `uipath-rpa`.
5. **Do not skip Step 2.** Check multi-skill patterns before filesystem detection.
6. **Do not ask the UIA question (Step 4) unless the plan includes a UI automation workflow.** Gate on the presence of UI element targeting, NOT on whether `uipath-servo` is loaded — most UI plans are single-skill `uipath-rpa`.
7. **Do not route UI automation through `uipath-servo` for element discovery or selector work.** `uipath-rpa` is the sole workflow authoring skill. Servo is only for live-app interaction and post-build verification.
8. **Do not describe specialist-internal flows in the plan** (target-configuration procedures, OR registration, scaffolding/write-agent pipelines, auth steps, pack/publish details). Route to the skill and let it follow its own documentation — inlining those flows creates drift.
9. **Do not save a plan with placeholders** (TBD, TODO, as needed, similar to Task N).
