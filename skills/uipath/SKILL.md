---
name: uipath
description: >
  Route any UiPath task to the right skill. Detects project type from filesystem context,
  disambiguates overlapping domains, and loads the correct specialist skill. TRIGGER on any
  UiPath-related request: automation, agents, apps, platform ops, UI testing, flows, or
  general UiPath questions. Use this skill for ANY UiPath-related task when the correct
  specialist skill is not obvious — it is the default UiPath entry point. Catches: "automate X",
  "create a UiPath project", "deploy my automation", "work with UiPath", or any ambiguous
  UiPath intent. NOT needed when user explicitly names a domain (e.g., "edit my coded workflow",
  "run servo snapshot") — those go direct to the specialist skill.
allowed-tools: Bash, Glob, Grep
user-invocable: true
---

# UiPath Task Router

Your ONLY job is to detect what the user needs and invoke the right specialist skill.
Do NOT attempt the task yourself. Do NOT write code, XAML, or run uip commands.
Dispatch, then stop.

## Step 1 — Match explicit signals

Scan the user's message for decisive keywords. First match wins — invoke immediately.

| User says or mentions | Invoke skill | Why |
|---|---|---|
| "servo", "screenshot", "click element", "UI tree", "snapshot window" | `uipath-servo` | Live UI interaction, not authoring |
| ".flow file", "flow project", "nodes and edges", "uip flow", "flow validate" | `uipath-flow` | Flow authoring format |
| "coded app", "web app", "codedapp", ".nupkg", "Studio Web push" | `uipath-coded-apps` | Web application lifecycle |
| "coded agent", "Python agent", "LangGraph", "LlamaIndex", "OpenAI Agents SDK", "uip codedagents" | `uipath-coded-agents` | Python agent lifecycle |
| "Orchestrator", "assets", "queues", "storage bucket", "uip login", "Test Manager", "deploy solution", "CI/CD pipeline" | `uipath-platform` | Platform management |
| "coded workflow", "CodedWorkflow", "[Workflow]", "[TestCase]", "C# automation" | `uipath-coded-workflows` | C# coded automation |
| "XAML", "RPA workflow", ".xaml file", "Studio Desktop", "activity", "get-errors" | `uipath-rpa-workflows` | XAML/RPA authoring |

If a match is found, invoke that skill now. Pass the user's original message as args.

## Step 2 — Detect from filesystem

No clear keyword match? Probe the project context:

```bash
# Check current directory and one level up for project signals
echo "=== CWD ===" && ls -1 project.json *.cs *.xaml *.py pyproject.toml flow_files/*.flow .uipath/ app.config.json .venv/ 2>/dev/null; echo "=== PARENT ===" && ls -1 ../project.json ../*.cs ../*.xaml ../pyproject.toml 2>/dev/null; echo "=== DONE ==="
```

Read the output and apply the FIRST matching rule:

| Filesystem signal | Invoke skill |
|---|---|
| `.cs` files AND `project.json` exists | `uipath-coded-workflows` |
| `.xaml` files AND `project.json` exists | `uipath-rpa-workflows` |
| `flow_files/*.flow` exists | `uipath-flow` |
| `.uipath/` directory or `app.config.json` exists | `uipath-coded-apps` |
| `.venv/` AND `pyproject.toml` with uipath dependency | `uipath-coded-agents` |
| `project.json` exists but no .cs or .xaml files | Read `project.json` to check `designOptions.projectProfile` — "Coded" = `uipath-coded-workflows`, otherwise = `uipath-rpa-workflows` |

If a project is detected, invoke that skill now.

## Step 3 — Classify by intent

No project found. Classify the user's intent:

| Intent pattern | Invoke skill |
|---|---|
| Wants to manage Orchestrator resources, authenticate, deploy a solution, or ask about the UiPath platform | `uipath-platform` |
| Wants to interact with live UI (test, click, verify, screenshot) | `uipath-servo` |
| Wants to create a NEW automation project but hasn't specified type | Go to Step 4 |
| General UiPath question (not about building something) | `uipath-platform` |

## Step 4 — Ask the user

The task requires a new project but the type is ambiguous. Ask:

> What type of UiPath project do you want to create?
>
> 1. **Coded workflow** — C# code-first automation (.cs files)
> 2. **RPA workflow** — XAML low-code automation (Studio Desktop, .xaml files)
> 3. **Python agent** — AI agent with LangGraph/LlamaIndex/OpenAI Agents
> 4. **Flow** — Node-based visual automation (.flow files)
> 5. **Coded web app** — React/Angular/Vue web application deployed to UiPath

Then invoke the matching skill.

## Step 5 — Handle cross-cutting auth

If the detected task will need Orchestrator access (deploy, publish, manage resources, run evals)
AND the user hasn't authenticated yet, note this in your dispatch:

Invoke `uipath-platform` first with args: `"authenticate only — then continue with <domain-skill> for: <user's original request>"`

The platform skill handles auth. After auth completes, invoke the domain skill.

---

## Progressive Loading Examples

These show the full chain from router dispatch to reference loading for common tasks.

### Example A: "Automate Excel processing"

```
Router (this skill):
  Step 2 detects: project.json + .cs files exist
  → Invoke: uipath-coded-workflows

Coded workflows skill loads (~7K tokens):
  Step 0 resolves PROJECT_DIR
  Skill body says: "Perform API Discovery — Search for existing .cs files"
  Skill body says: "Add using statements based on packages in project.json"
  → Reads: project.json to find UiPath.Excel.Activities version
  → Reads: {projectRoot}/.local/docs/packages/UiPath.Excel.Activities/ (if exists)
  → Falls back to: ../../references/activity-docs/UiPath.Excel.Activities/3.5/coded/api.md
  → Falls back to: ../../references/activity-docs/UiPath.Excel.Activities/3.5/coded/examples.md

Activity reference loads (~2K tokens):
  Exact method signatures: ExcelFile.ReadRange(), WriteRange(), etc.
  → Model writes the workflow code using correct APIs
```

### Example B: "Build an RPA workflow that sends Outlook emails with attachments"

```
Router (this skill):
  Step 2 detects: project.json + .xaml files exist
  → Invoke: uipath-rpa-workflows

RPA workflows skill loads (~10K tokens):
  Resolving packages: checks UiPath.Mail.Activities in project.json
  Skill body says: "Check {projectRoot}/.local/docs/packages/ first"
  → Reads: .local/docs/packages/UiPath.Mail.Activities/ (if exists)
  → Falls back to: ../../references/activity-docs/UiPath.Mail.Activities/2.8/activities/overview.md
  → For specific activity: ../../references/activity-docs/UiPath.Mail.Activities/2.8/activities/SendOutlookMail.md
  Skill body says: "Use get-default-activity-xaml for XAML scaffolding"
  → Runs: uip rpa get-default-activity-xaml --activity-name SendOutlookMail ...

Activity reference loads (~1K tokens):
  XAML snippet for SendOutlookMail activity with correct properties
  → Model generates validated XAML workflow
```

### Example C: "Create a Python agent that uses LangGraph"

```
Router (this skill):
  Step 1 matches: "Python agent" + "LangGraph"
  → Invoke: uipath-coded-agents

Coded agents skill loads (~3K tokens):
  Framework selection: LangGraph (from explicit mention)
  Lifecycle stage: Setup → Build
  Skill body says: "Read only the relevant reference when you reach that stage"
  → Reads: references/lifecycle/setup.md (for scaffolding)
  → Reads: references/frameworks/langgraph-integration.md (for LangGraph patterns)
  → Does NOT read: llamaindex-integration.md, openai-agents-integration.md, etc.

Framework reference loads (~2K tokens):
  LangGraph StateGraph patterns, tool binding, UiPath SDK integration
  → Model builds the agent with correct patterns
```

### Example D: "Deploy my automation to Orchestrator" (no project context)

```
Router (this skill):
  Step 1 matches: "deploy" + "Orchestrator"
  → Invoke: uipath-platform

Platform skill loads (~3K tokens):
  Skill body says: "Check login status first"
  → Runs: uip login status --format json
  Task is "deploy" → reads: references/solution-guide.md (pack → publish → deploy pipeline)

Solution guide loads (~2K tokens):
  Complete pack/publish/deploy commands
  → Model runs the deployment pipeline
```

### Example E: "I want to automate something with UiPath" (maximally ambiguous)

```
Router (this skill):
  Step 1: No keyword match
  Step 2: No project files found
  Step 3: "create a NEW automation" → Step 4
  Step 4: Asks user which project type
  User replies: "RPA workflow"
  → Invoke: uipath-rpa-workflows

RPA workflows skill loads (~10K tokens):
  Creates new project with uip rpa create-project
  → Proceeds with normal workflow
```

### Example F: "Create a Flow that listens for Jira events and posts to Slack"

```
Router (this skill):
  Step 1 matches: "Flow"
  → Invoke: uipath-flow

Flow skill loads (~7K tokens):
  Skill body says: "ALWAYS query the registry before building"
  Skill body says: "ALWAYS discover connector capabilities via IS before planning"
  → Reads: references/flow-planning-guide.md (node catalog, expression system)
  → Runs: uip is activities list jira --format json
  → Runs: uip is activities list slack --format json
  → Runs: uip is connections list jira --format json
  → Reads: references/flow-file-format.md (JSON schema for .flow files)

References load progressively:
  Planning guide first (which nodes to use) → File format (how to write them)
  → Model generates validated .flow JSON
```
