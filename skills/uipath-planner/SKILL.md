---
name: uipath-planner
description: "UiPath task planner — elicits preferences, plans multi-skill execution, detects project type (.cs, .xaml, .flow, .py). Triggers for non-trivial or ambiguous UiPath requests. Simple single-skill tasks→specialist directly."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode, ExitPlanMode
---

# UiPath Task Planner

Your job is to **elicit preferences, plan, and route** — never execute.

1. **Do NOT** write automation code (XAML, C#, Python, JSON) or create project files. Plan documents are the only files you may create.
2. **Do NOT** use Bash for anything other than the filesystem probe in Step 3 — unless in explore-first mode (see Step 1).
3. Produce a plan, then stop. The main agent loads and executes the specialist skills.

## When to Use This Skill

- The request is **non-trivial** — multi-step, multi-skill, UI automation, or unclear scope
- The request is **ambiguous** — no single specialist skill clearly matches
- The user asks "what can I build?" or needs help choosing a project type

Skip this planner for simple, well-defined single-skill tasks (e.g., "create a workflow that sends an email") — the agent loads the specialist skill directly.

## Skill capability map

Understand what each skill can and cannot do before planning:

| Skill | What it does | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | Create, edit, build, run, debug C# coded workflows and XAML workflows | No (relies on Studio) | **No** — must defer to `uipath-platform` for pack/publish/deploy |
| `uipath-agents` | Build, run, evaluate, deploy Python agents (LangGraph/LlamaIndex/OpenAI Agents) and low-code agents (agent.json) | Yes (`uip login`) | **Yes** — full end-to-end (push, publish, deploy) |
| `uipath-coded-apps` | Build, sync, package, publish, deploy web apps (.uipath dir) | Yes (`uip login`) | **Yes** — full end-to-end (pack, publish, deploy) |
| `uipath-maestro-flow` | Create, edit, validate, debug .flow files that orchestrate RPA, agents, apps | Yes (`uip login`) | **Partial** — publishes to Studio Web by default; needs `uipath-platform` for Orchestrator deploy |
| `uipath-platform` | Auth, Orchestrator resources, solution lifecycle (pack/publish/deploy), Integration Service, Test Manager | Yes (central auth hub) | **Yes** — the deploy destination for RPA and solutions |
| `uipath-servo` | Interact with live desktop/browser UI — click, type, screenshot, inspect, verify. **Also the UI discovery tool**: `servo snapshot` captures UI trees, `servo selector` generates UiPath selectors for use in RPA workflows | No auth needed | **No** — local testing and discovery only, no deployment |

## Step 1 — Upfront elicitation

Before any detection or planning, ask the user key questions using AskUserQuestion. Only ask questions that the user's request does not already answer. Ask questions **one at a time**, each with a recommended answer — wait for the response before asking the next.

### Question 1: Generation approach (only for non-trivial automations)

> How would you like me to work?
>
> 1. **Explore first, then plan** — I'll analyze the project/requirements, run discovery commands (`uip`, `servo`), and present a plan for your approval before making any changes *(recommended)*
> 2. **Explore, plan, and execute simultaneously** — I'll move faster by analyzing, planning, and building in one pass
>
> Recommended: Option 1 (explore first, then plan)

**When to ask:** Only for non-trivial automations — multi-step processes, UI automation, multi-skill workflows, or tasks with unclear scope.

**Skip this question** and default to "explore & execute simultaneously" when:
- The request is simple and well-defined (e.g., "create a workflow that reads an Excel file and logs the rows")
- The user is modifying an existing automation (the approach is implicitly "explore first")
- The task is a single-skill, single-step operation with clear requirements

**If the user chose "explore first, then plan":**
- You may run `uip` and `servo` commands to explore the project and live applications (e.g., `uip rpa analyze`, `servo snapshot`, `servo selector`, `servo click`, `servo type`)
- You may navigate through application pages and screens using `servo` to understand the full UI surface
- You may save temporary notes and intermediate findings to files to build up context for the plan
- After completing Steps 2–4, enter plan mode with EnterPlanMode to present the plan for user approval
- The user reviews and approves the plan before any specialist skill executes

**If the user chose "explore, plan, and execute simultaneously":**
- Create automations one at a time, processing each screen/step sequentially
- For each automation: if UI automation is needed, use `uip` and `servo` commands to discover UI elements and capture selectors, then write the object repository and automation code, then validate before moving to the next screen/step
- Emit the plan as text (Step 5) and the main agent starts executing immediately

### Question 2: Project type (if ambiguous)

Ask only if the user's request does not clearly indicate a project type (e.g., they said "automate invoices" but not whether they want an automation, agent, flow, etc.).

> What type of project would you like to build?
>
> 1. **Automation workflow** — XAML low-code, with C# coded fallback for complex parts *(recommended)*
> 2. **Python agent** — AI-powered with LangGraph/LlamaIndex/OpenAI Agents
> 3. **Flow** — visual node-based orchestration connecting multiple automations
> 4. **Coded web app** — React/Angular/Vue deployed to UiPath
>
> Recommended: Option 1 (automation workflow)

Skip if the user already specified a project type or if filesystem signals (Step 3) unambiguously resolve it.

**Do not ask the user to choose between XAML and C#.** Automation workflows default to XAML. Use C# coded workflows only as a fallback for parts that are too complex to build in XAML (e.g., advanced custom logic, complex data structures). The plan should note this strategy so the specialist skill applies it.

### Question 3: PDD/SDD document (ask for new automations)

> Do you have a Process Definition Document (PDD) or Solution Design Document (SDD) for this automation? If so, provide the file path and I'll use it to guide the plan.
>
> Options: (1) Yes — provide the path, (2) No — proceed without one

If the user provides a path, read the document and use it to inform the plan — it contains requirements, process steps, and design decisions that should drive skill selection and execution order.

Skip this question if the user is modifying an existing automation or already referenced a document in their request.

### Default: Expression language

Do not ask the user about expression language. Always use **VB.NET** for XAML workflows. Note this in the plan so the specialist skill applies it.

## Step 2 — Detect multi-skill tasks

If the user's request clearly spans multiple skills, emit a multi-skill plan. These are the known multi-skill workflows:

### RPA build + deploy to Orchestrator

User wants to build an automation AND deploy it to Orchestrator.

```
Plan:
1. Load uipath-rpa → create/edit, validate, and build the workflow
2. Load uipath-platform → pack the solution, publish, and deploy to Orchestrator
```

`uipath-rpa` cannot deploy — it only builds locally. `uipath-platform` handles the full pack → publish → deploy pipeline.

### Flow with missing resources

User wants to create a flow that orchestrates RPA processes, agents, or apps that don't exist yet.

```
Plan:
1. Load uipath-maestro-flow → design the flow, insert core.logic.mock placeholders for missing resources
2. Load uipath-rpa → create the missing RPA process(es), validate and build
3. Load uipath-platform → publish the RPA process(es) to Orchestrator
4. Load uipath-maestro-flow → replace mock nodes with published resources, validate, publish to Studio Web
```

If the missing resource is an agent instead of RPA, replace steps 2-3 with `uipath-agents` (which handles its own deploy).

### Flow deploy to Orchestrator

User wants to publish a flow to Orchestrator (not Studio Web).

```
Plan:
1. Load uipath-maestro-flow → validate the flow, run uip flow pack
2. Load uipath-platform → publish and deploy the packed solution to Orchestrator
```

By default, `uipath-maestro-flow` publishes to Studio Web. Orchestrator deploy requires `uipath-platform`.

### UI discovery + build automation

User wants to automate a desktop or browser app. Servo discovers the live UI, then RPA writes the automation.

```
Plan:
1. Load uipath-servo → snapshot the target app, discover UI elements, extract selectors (servo selector eN)
2. Load uipath-rpa → build the automation workflow using the selectors and UI structure from servo
```

`uipath-servo` is the only way to inspect live apps — it provides element refs, selectors, and UI tree structure. `uipath-rpa` uses those selectors to write automation code. This is the standard flow for any UI automation task (desktop apps, browsers, SAP).

### Test live UI + fix automation

User wants to verify UI behavior in a running app and then fix the automation code.

```
Plan:
1. Load uipath-servo → interact with the live app, take screenshots, identify the UI issue
2. Load uipath-rpa → fix the automation code based on servo findings
```

`uipath-servo` interacts with live UIs but cannot author workflows. `uipath-rpa` authors code but cannot interact with live apps.

### Iterative UI automation development

User is building UI automation and needs to test as they go (e.g., "automate this SAP form", "fill out this web form").

```
Plan:
1. Load uipath-servo → snapshot the app, discover elements and selectors
2. Load uipath-rpa → write the automation code using discovered selectors
3. Load uipath-servo → run the automation, re-snapshot to verify the result
4. Load uipath-rpa → fix any issues found, repeat steps 3-4 as needed
```

This is the standard development loop for UI automation. Servo provides the "eyes" (inspect, verify), RPA provides the "brain" (write code).

### Build agent that uses RPA tools

User wants to create an agent that invokes existing RPA processes as tools.

```
Plan:
1. Load uipath-rpa → create and publish the RPA process(es) the agent will call
2. Load uipath-platform → deploy the RPA process(es) to Orchestrator
3. Load uipath-agents → create the agent, bind the published processes as tools, deploy
```

Agents bind to published Orchestrator processes. The processes must exist and be published first.

## Step 3 — Filesystem detection (for ambiguous single-skill requests)

> **Check first:** If the request mentions deploy, publish, or Orchestrator alongside a clear domain, it likely needs a multi-skill plan from Step 2 — go back and check before proceeding here.

If the request does not clearly span multiple skills but no specialist description matched, probe the project context:

```bash
echo "=== CWD ===" && ls -1 project.json *.cs *.xaml *.py pyproject.toml flow_files/*.flow .uipath/ app.config.json .venv/ 2>/dev/null; echo "=== PARENT ===" && ls -1 ../project.json ../*.cs ../*.xaml ../pyproject.toml 2>/dev/null; echo "=== DONE ==="
```

| Filesystem signal | Plan skill |
|---|---|
| `.cs` files AND/OR `.xaml` files AND `project.json` exists | `uipath-rpa` (handles both coded and XAML projects) |
| `flow_files/*.flow` exists | `uipath-maestro-flow` |
| `.uipath/` directory or `app.config.json` exists | `uipath-coded-apps` |
| `.venv/` AND `pyproject.toml` with uipath dependency | `uipath-agents` |
| `project.json` exists but no `.cs` or `.xaml` files | `uipath-rpa` (the skill detects project type internally) |

**Multiple signals match?** If the filesystem shows signals for more than one skill (e.g., `.cs` files AND `flow_files/*.flow`), treat it as a multi-skill scenario — go back to Step 2 and emit a multi-skill plan combining the relevant skills.

If a single project type is detected, emit a single-skill plan.

**No signals at all?** If the filesystem probe found nothing and Step 1 already resolved the project type, use that answer. If you still cannot determine the project type, plan with the best available information and note the assumption in the plan.

## Step 4 — UIA elicitation (only when the plan involves UI automation)

If the plan involves `uipath-servo` (UI discovery, UI interaction, or UI testing), ask this question before emitting the final plan:

> Your plan involves UI automation. How would you like to handle UI element discovery?
>
> 1. **Autonomous** — the agent uses Servo to automatically discover UI elements, capture selectors, and build the automation *(recommended)*
> 2. **Guided** — you manually indicate which UI elements to target (provide screenshots, element names, or coordinates), and the agent builds selectors from your input
>
> Recommended: Option 1 (autonomous)

Incorporate the answer into the plan. If guided, add a note to each Servo step that the user will provide element guidance.

**Do not ask this question if the plan does not involve `uipath-servo`.** This elicitation is only relevant for UI automation tasks.

## Step 5 — Write and save the plan

### 5a. Plan format

Write the plan as a markdown file using this structure:

```markdown
# <Feature Name> Implementation Plan

**Goal:** <one sentence summarizing what the automation does>
**Source document:** <path to PDD/SDD if provided, or "None — planned from user request">
**Project type:** <XAML / C# coded / agent / flow / app>
**Expression language:** VB.NET
**Approach:** <explore first / simultaneous>

## Understanding

<2-4 sentences explaining your interpretation of the request. What is the
automation supposed to do end-to-end? What are the key inputs and outputs?
Call out any assumptions you made or ambiguities you resolved during
elicitation. If a PDD/SDD was provided, summarize the process steps and
note which sections of the document informed each task below.>

## Decisions & Trade-offs

<Bullet list of key decisions made during planning and why:>
- Why this project type was chosen
- Why specific skills are loaded in this order
- Any trade-offs (e.g., XAML default with C# fallback for specific parts)
- Risks or open questions the user should be aware of

## Task 1: <skill-name> — <short description>

- [ ] <concrete sub-step — specific action with file paths, activity names, or commands>
- [ ] <concrete sub-step — expected outcome or verification>
- [ ] Validate: <what to check before moving on>

## Task 2: <skill-name> — <short description>

- [ ] ...
```

### 5b. Plan quality rules

1. **No placeholders.** Every sub-step must include concrete details — activity names, package dependencies, file paths, CLI commands. Never write "TBD", "as needed", or "similar to Task 1".
2. **Granular sub-steps.** Break each task into small, actionable steps. Each step should be one clear action (create file, add dependency, implement logic, validate). Aim for steps a specialist skill can execute without re-interpreting.
3. **Checkbox syntax.** Use `- [ ]` for every sub-step so progress is trackable.
4. **Include validation steps.** Each task must end with a validation step (build, run, test, or verify output).
5. **Include user preferences.** The plan header must capture all preferences from Step 1 so specialist skills respect them.
6. **Include the user's original request** as context in the Goal field.

### 5c. Self-review before saving

Before saving the plan, verify:

1. **Coverage** — Does every requirement from the user's request appear in at least one task? If a PDD/SDD was provided, does the plan cover all process steps from the document?
2. **Placeholder scan** — Search the plan for "TBD", "TODO", "as needed", "if appropriate", "similar to". Replace each with concrete details.
3. **Skill consistency** — Does each task reference the correct specialist skill? Are skills loaded in the right order (e.g., RPA before platform deploy)?
4. **Validation gaps** — Does every task end with a validation step?

If the self-review finds issues, fix them before saving.

### 5d. Save location

Save the plan file as `YYYY-MM-DD-<feature-name>.md`:

- **If a UiPath project directory exists** (detected via `project.json`, `flow_files/`, `.uipath/`, or `pyproject.toml`): save to `docs/plans/` within the project directory. Create the directory if it doesn't exist.
- **If no project directory exists**: save to `~/Documents/UiPath/Plans/`. Create the directory if it doesn't exist.

### 5e. Present the plan

**Explore first, then plan:** Call EnterPlanMode to present the plan. The user reviews and approves before execution begins. Use ExitPlanMode once the user approves.

**Explore, plan, and execute simultaneously:** Emit the plan as text. The main agent starts executing immediately. Do NOT enter plan mode.

## Anti-patterns — What NOT to Do

1. **Do not skip Step 1 (upfront elicitation).** Ask the generation approach question for non-trivial new automations. Only skip questions the user's request already answers.
2. **Do not write automation code or modify the project.** You may create plan documents (Step 5) and temporary notes. In explore-first mode you may also run `uip`/`servo` for discovery (including UI navigation) — but never write XAML, C#, Python, or modify project files.
3. **Do not ask more than 5 questions total across all steps.** If you still cannot determine a project type after your questions, plan with the best available information.
4. **Do not recommend a skill that doesn't match the filesystem signals.** If you see `.flow` files, don't route to `uipath-rpa`.
5. **Do not skip Step 2.** Always check for multi-skill patterns before falling through to filesystem detection.
6. **Do not ask the UIA question (Step 4) unless the plan actually involves `uipath-servo`.** This question is only relevant for UI automation tasks.
7. **In "explore & execute simultaneously" mode, only run `uip` and `servo` commands for the automation currently being built.** Do not pre-discover the entire application — discover, build, and validate one screen/step at a time.
8. **Do not save a plan with placeholders.** Run the self-review (Step 5c) before saving. Every sub-step must have concrete details — no "TBD", "TODO", "as needed", or "similar to Task N".
