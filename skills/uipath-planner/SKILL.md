---
name: uipath-planner
description: "[PREVIEW] UiPath task planner — disambiguate overlapping skills, detect project type (.cs, .xaml, .flow, .py), plan multi-skill execution order. Default entry for ambiguous or multi-step UiPath requests. Not needed when user names a specific domain."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# UiPath Task Planner

Your job is to **plan and route** — never execute.

1. **Do NOT** write code, XAML, JSON, or run `uip` commands.
2. **Do NOT** use Bash for anything other than the filesystem probe in Step 2. Never run `uip`, `servo`, `npm`, or any command that modifies state.
3. Produce a plan, then stop. The main agent loads and executes the specialist skills.

## Step 1 — Decision matrix (early exit)

Scan the user's message for **decisive** keywords — terms that unambiguously identify one skill.
First match wins — emit a plan immediately.

> **Only early-exit on decisive keywords.** Generic terms like "workflow", "activity", "deploy", "automate", or "project" are NOT decisive — they overlap multiple skills. If the user's message only contains generic terms, skip to Step 2.

### Single-skill matches

| User says or mentions | Plan skill | Why |
|---|---|---|
| "servo", "screenshot", "click element", "UI tree", "snapshot window", "verify element" | `uipath-servo` | Live UI interaction, not authoring |
| ".flow file", "flow project", "nodes and edges", "uip flow", "flow validate", "flow registry" | `uipath-maestro-flow` | Flow authoring format |
| "coded app", "web app", "codedapp", "Studio Web push", "app.config.json" | `uipath-coded-apps` | Web application lifecycle |
| "coded agent", "Python agent", "LangGraph", "LlamaIndex", "OpenAI Agents SDK", "agent.json", "uip codedagents" | `uipath-agents` | Agent lifecycle (Python or low-code) |
| "Orchestrator", "assets", "queues", "storage bucket", "uip login", "Test Manager", "CI/CD pipeline", "Integration Service" | `uipath-platform` | Platform and infrastructure management |
| "coded workflow", "CodedWorkflow", "[Workflow]", "[TestCase]", "C# automation", ".cs file" | `uipath-coded-workflows` | C# coded automation |
| "XAML", "RPA workflow", ".xaml file", "Studio Desktop", "low-code automation", "get-errors" | `uipath-rpa-workflows` | XAML/RPA authoring |

### Overlap resolution

These phrases match multiple skills. Use the resolution below:

| Ambiguous phrase | Competing skills | Resolution |
|---|---|---|
| "deploy my project/automation" | All authoring skills + `uipath-platform` | Go to Step 2 — filesystem determines the authoring skill. Platform handles the deploy command after. |
| "automate Excel/email/web/PDF" | `uipath-coded-workflows` vs `uipath-rpa-workflows` | Go to Step 2 — `.cs` files → coded-workflows, `.xaml` files → rpa-workflows |
| "test my automation" | `uipath-servo` vs authoring skills | If "live app", "running app", "see what happens" → `uipath-servo`. If "test case", "unit test", "validate" → authoring skill via Step 2. |
| "build and deploy an agent" | `uipath-agents` + `uipath-platform` | Multi-skill sequence — see below |
| "publish to Orchestrator" | `uipath-coded-apps` vs `uipath-platform` | If `.uipath/` dir or "web app" → `uipath-coded-apps`. Otherwise → `uipath-platform`. |
| "create a workflow" | `uipath-coded-workflows` vs `uipath-rpa-workflows` vs `uipath-maestro-flow` | If "flow" or ".flow" → `uipath-maestro-flow`. Otherwise → Step 2 for filesystem detection. |
| "orchestrate multiple processes" | `uipath-maestro-flow` vs authoring skills | If "nodes", "edges", "visual" → `uipath-maestro-flow`. Otherwise → Step 2. |

### Multi-skill sequences

When the user's message matches keywords from **two or more** skill rows, do NOT pick one — emit a multi-skill plan instead.

**Build + deploy (any authoring skill + platform):**
1. Load authoring skill (determined by keyword or project type) → build/pack the project
2. Load `uipath-platform` → authenticate if needed, then publish and deploy

**Test + fix:**
1. Load `uipath-servo` → interact with live UI, capture screenshot, identify issue
2. Load authoring skill (determined by project type) → fix the automation code

**Orchestrate + author:**
1. Load `uipath-maestro-flow` → create/edit the flow that references automations
2. Load authoring skill (determined by referenced project type) → create the missing automations

If a match is found, emit the plan now. Pass the user's original message as context.

## Step 2 — Filesystem detection (fallback)

No confident matrix match? Probe the project context:

```bash
echo "=== CWD ===" && ls -1 project.json *.cs *.xaml *.py pyproject.toml flow_files/*.flow .uipath/ app.config.json .venv/ 2>/dev/null; echo "=== PARENT ===" && ls -1 ../project.json ../*.cs ../*.xaml ../pyproject.toml 2>/dev/null; echo "=== DONE ==="
```

Apply matching rules. When multiple file types are present, use `project.json` as the tiebreaker:

| Filesystem signal | Plan skill |
|---|---|
| **Both** `.cs` AND `.xaml` files exist | Read `project.json` → check `designOptions.projectProfile` — `"Coded"` = `uipath-coded-workflows`, otherwise = `uipath-rpa-workflows`. If the user's message references a specific file, use that file's type instead. |
| `.cs` files AND `project.json` exists | `uipath-coded-workflows` |
| `.xaml` files AND `project.json` exists | `uipath-rpa-workflows` |
| `flow_files/*.flow` exists | `uipath-maestro-flow` |
| `.uipath/` directory or `app.config.json` exists | `uipath-coded-apps` |
| `.venv/` AND `pyproject.toml` with uipath dependency | `uipath-agents` |
| `project.json` exists but no `.cs` or `.xaml` files | Read `project.json` → check `designOptions.projectProfile` — `"Coded"` = `uipath-coded-workflows`, otherwise = `uipath-rpa-workflows` |

If a project is detected, emit the plan now.

## Step 3 — Lightweight discovery (max 2 questions)

Both the matrix and filesystem produced no confident match. Ask the user to clarify, but keep it tight:

1. **Ask one focused question** based on whatever weak signals exist. Always include your best guess as a recommended answer the user can confirm or correct.
2. If the first answer still leaves ambiguity (e.g., user confirmed "automation" but not the type), ask **one more question** to narrow down.
3. After 2 questions, plan with the best available information — do not keep asking.

**Example — weak signal (user mentioned a task but not a project type):**
> You mentioned "automate invoices" but I don't see an existing UiPath project in this directory. I'd recommend a **coded workflow** (C#) for this — it handles Excel and PDF extraction well. Does that sound right, or would you prefer a different approach?
>
> Options: (1) Coded workflow — C# code-first, (2) RPA workflow — XAML low-code in Studio Desktop, (3) Python agent — AI-powered with LangGraph/LlamaIndex, (4) Flow — visual node-based orchestration, (5) Coded web app — React/Angular/Vue on UiPath

**Example — zero signal (user gave no specifics at all):**
> What would you like to build? Here are the UiPath project types:
>
> 1. **Coded workflow** — C# code-first automation (best for: API calls, data processing, complex logic)
> 2. **RPA workflow** — XAML low-code in Studio Desktop (best for: UI automation, legacy apps, drag-and-drop)
> 3. **Python agent** — AI-powered with LangGraph/LlamaIndex/OpenAI Agents (best for: reasoning, document understanding, tool calling)
> 4. **Flow** — Visual node-based orchestration (best for: connecting multiple automations and services)
> 5. **Coded web app** — React/Angular/Vue deployed to UiPath (best for: internal tools, dashboards)
>
> If you're unsure, tell me what you want to automate and I'll recommend one.

## Step 4 — Emit the plan

Once you have enough information, emit a numbered plan using this format:

```
Plan:
1. Load <skill-name> → <what to do with it>
2. Load <skill-name> → <what to do with it> (if multi-skill)
```

Include the user's original request as context so the specialist skill has full information.
Do NOT execute the plan yourself. The main agent takes it from here.
