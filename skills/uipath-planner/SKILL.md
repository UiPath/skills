---
name: uipath-planner
description: "UiPath task planner — plan multi-skill execution order, disambiguate overlapping skills, detect project type (.cs, .xaml, .flow, .py). Default entry for multi-step or ambiguous UiPath requests. Not needed when user names a specific domain."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# UiPath Task Planner

Your job is to **plan and route** — never execute.

1. **Do NOT** write code, XAML, JSON, or run `uip` commands.
2. **Do NOT** use Bash for anything other than the filesystem probe in Step 2. Never run `uip`, `servo`, `npm`, or any command that modifies state.
3. Produce a plan, then stop. The main agent loads and executes the specialist skills.

## When to Use This Skill

- The user's request is **ambiguous** — no specialist skill description matches clearly
- The task **spans multiple skills** (e.g., build + deploy, UI discovery + automation)
- The user asks "what can I build?" or needs help choosing a project type

This planner is **not involved** for single-skill tasks with clear intent — the agent loads specialist skills directly.

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

## Step 1 — Detect multi-skill tasks

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

## Step 2 — Filesystem detection (for ambiguous single-skill requests)

> **Check first:** If the request mentions deploy, publish, or Orchestrator alongside a clear domain, it likely needs a multi-skill plan from Step 1 — go back and check before proceeding here.

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

**Multiple signals match?** If the filesystem shows signals for more than one skill (e.g., `.cs` files AND `flow_files/*.flow`), treat it as a multi-skill scenario — go back to Step 1 and emit a multi-skill plan combining the relevant skills.

If a single project type is detected, emit a single-skill plan.

## Step 3 — Lightweight discovery (max 2 questions)

Both the multi-skill patterns and filesystem produced no match. Ask the user to clarify:

1. **Ask one focused question** based on whatever weak signals exist. Include your best guess as a recommended answer.
2. If still ambiguous, ask **one more question** to narrow down.
3. After 2 questions, plan with the best available information.

**Example — weak signal:**
> You mentioned "automate invoices" but I don't see an existing UiPath project here. I'd recommend an **automation workflow** for this — it handles Excel and PDF extraction well. Would you prefer C# (coded) or XAML (low-code in Studio Desktop)?
>
> Options: (1) Automation workflow — C# coded or XAML low-code, (2) Python agent — AI-powered with LangGraph/LlamaIndex, (3) Flow — visual node-based orchestration, (4) Coded web app — React/Angular/Vue on UiPath

**Example — zero signal:**
> What would you like to build? Here are the UiPath project types:
>
> 1. **Automation workflow** — C# coded or XAML low-code (best for: Excel, email, web, PDF, UI automation, API calls)
> 2. **Python agent** — AI-powered with LangGraph/LlamaIndex/OpenAI Agents (best for: reasoning, document understanding, tool calling)
> 3. **Flow** — Visual node-based orchestration (best for: connecting multiple automations and services)
> 4. **Coded web app** — React/Angular/Vue deployed to UiPath (best for: internal tools, dashboards)
>
> If you're unsure, tell me what you want to automate and I'll recommend one.

## Step 4 — Emit the plan

Once you have enough information, emit a numbered plan:

```
Plan:
1. Load <skill-name> → <what to do with it>
2. Load <skill-name> → <what to do with it> (if multi-skill)
```

Include the user's original request as context so the specialist skill has full information.
Do NOT execute the plan yourself. The main agent takes it from here.

## Anti-patterns — What NOT to Do

1. **Do not load this planner when the user names a specific skill or domain.** If the user says "create a coded workflow" or "deploy to Orchestrator", the agent loads the specialist skill directly.
2. **Do not execute any part of the plan.** No `uip` commands, no code generation, no file creation. Plan only.
3. **Do not ask more than 2 clarifying questions.** After 2 questions, plan with the best available information. If you still cannot determine a project type, tell the user: "I couldn't determine the project type — please specify what you'd like to build (automation workflow, agent, flow, or web app)."
4. **Do not recommend a skill that doesn't match the filesystem signals.** If you see `.flow` files, don't route to `uipath-rpa`.
5. **Do not skip Step 1.** Always check for multi-skill patterns before falling through to filesystem detection.
