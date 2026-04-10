---
name: uipath-case-management
description: "[PREVIEW] UiPath Case Management projects (caseplan.json files) — manage case definitions, stages, tasks, edges, entry/exit conditions. Create, edit, validate, run cases via uip CLI: stages, tasks, triggers etc."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

Comprehensive guide for creating, editing, and managing UiPath Case Management definition files using the `uip case` CLI.

## When to Use This Skill

- User wants to **create a new Case Management definition file** with `uip case cases add`
- User is **editing a case JSON file** — adding stages, tasks, edges, or properties
- User wants to **explore available resources** (processes, agents, actions) via the registry
- User wants to **manage runtime case instances** (list, pause, resume, cancel, variables)
- User wants to **view process summaries or incidents**
- User asks about the **case management JSON schema** — nodes, edges, tasks, rules, SLA
- User asks **how to wire stages**, configure task types, or set entry/exit conditions

## Critical Rules

1. **Every stage needs at least one edge** connecting it to the case or it will be orphaned
2. **Trigger node is created automatically** on `cases add` — don't add another unless it's a separate entry point (e.g. for a multi-trigger case)
3. **Tasks are 2D arrays**: `tasks[lane][index]` — use `--lane` to put tasks in parallel lanes
4. **Edge type is inferred** from the source node — don't set it manually via `edges add`
5. **Stage IDs are returned on creation** — capture them from the `StageId` field in the success output
6. **Edit `content/*.json` only** — `content/*.bpmn` is auto-generated and will be overwritten
7. **Every command must be executed in sequence. No parallel execution.**

## Quick Start

These steps are for **creating a new case definition from scratch**. For existing files, skip to the relevant step. For small targeted edits (renaming a stage, changing a task's display name), skip straight to Step 4.

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

### Step 1 — Check login status

`uip case tasks`, `instance`, `processes`, `incidents`, and `registry` (for tenant resources) require authentication. `uip case cases`, `stages` and `edges` work on local files without login.

```bash
uip login status --output json
```

If not logged in and you need cloud features:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Create a new Case project and add a case definition file

The case file must be inside a proper solution/project structure:
```bash
mkdir -p <directory>

# Create the solution
cd <directory> && uip solution new <solutionName>

# Create the case project inside the solution
cd <solutionName> && uip case init <projectName>

# Add the project to the solution
uip solution project add \
  <projectName> \
  <solutionName>.uipx
```

This scaffolds a complete project. See [references/case-schema.md](references/case-schema.md) for the full project structure.

```bash
uip case cases add --name <CaseName> --file <directory>/<solutionName>/<projectName>/case.stage.json
```

This scaffolds a minimal case JSON file with a root node and a default Trigger node.

Optional flags:
- `--case-identifier <string>` — defaults to the name
- `--identifier-type constant|external` — default: `constant`
- `--case-app-enabled` — enable the Case App UI

### Step 3 — Plan the case definition

**Only for new definitions or major restructuring**. Skip for small targeted edits.

Before editing, create a plan based on the given input file and get user approval:

1. **Output the plan directly in chat** with:
   - **Goal** — one-line summary of what the case process does
   - **Stages** — numbered list of each stage, its type (stage/exception), and purpose
   - **Tasks per stage** — task type and what each task does
   - **Connections** — how stages connect (source → target, edge labels)
   - **Missing information** — anything unspecified, marked as `[REQUIRED: description]`

2. **Ask the user to review the plan before proceeding.** Do NOT move to Step 5 until the user confirms.

### Step 4 — Add stages

```bash
uip case stages add <file> --label "Review Application" --output json
uip case stages add <file> --label "Exception Handler" --type exception --output json
```

Stage types: `stage` (default), `exception`, `trigger`.

Stages are auto-positioned. Each stage gets a unique ID in the output — save it for adding tasks and edges.

### Step 5 — Connect stages with edges
The default trigger Id is `trigger_1`. Connect it to the first stage, then connect stages in sequence. Add edge labels for conditions if needed.

```bash
uip case edges add <file> --source <trigger-id> --target <first-stage-id> --output json
uip case edges add <file> --source <stage-id> --target <next-stage-id> --label "Approved" --output json
```

Edge type is inferred automatically: Trigger → `TriggerEdge`, Stage → `Edge` (carries transition rules).

Source/target handle directions default to `right`/`left` for stage edges and trigger edges.

### Step 5b — Add extra triggers (multi-trigger cases only)

Skip this step for single-trigger cases. Add additional triggers when the case needs to start from multiple entry points.

A default `trigger_1` (manual trigger) is created automatically. Add timer triggers for time-based automation:

```bash
# Timer trigger — fires on a schedule
uip case triggers add-timer <file> --every 1h --output json
uip case triggers add-timer <file> --every 2d --at 2026-04-26T10:00:00.000Z --output json
uip case triggers add-timer <file> --time-cycle "R/PT1H" --output json   # raw ISO 8601
```

Capture the returned trigger ID, then connect it to its target stage with an edge (same as Step 5).

**Positioning:** Triggers stack vertically to the left of the stages. Each additional trigger is placed ~150px below the previous one. The default `trigger_1` is at y=200; a second trigger sits at y=350, a third at y=500, etc.

Full trigger options: see [references/case-commands.md — uip case triggers](references/case-commands.md).

### Step 6 — Add tasks to stages

```bash
uip case tasks add <file> <stage-id> --type process --display-name "Run Background Check" --name "BackgroundCheck" --folder-path "Shared" --task-type-id <taskTypeId> --output json
uip case tasks add <file> <stage-id> --type agent --display-name "AI Analysis" --task-type-id <taskTypeId> --output json
uip case tasks add <file> <stage-id> --type action --display-name "Human Review" \
  --task-title "Please review this application" \
  --priority Medium \
  --recipient reviewer@example.com \
  --task-type-id <taskTypeId> --output json
```

Valid task types: `process`, `agent`, `api-workflow`, `rpa`, `external-agent`, `case-management`.

Use `--lane <index>` and index should increase by 1 for each task starting with 0. For parallel execution task, their lane index should be identical.

### Step 6b — Bind task inputs and wire outputs

After adding tasks, set input values and connect task outputs to downstream inputs.

**Bind a literal value to a task input:**
```bash
uip case var bind <file> <stage-id> <task-id> <input-name> --value "<value>" --output json
```

Value can be a plain string, a number, or an expression:
- `=metadata.<field>` — reference case metadata (e.g. `=metadata.caseId`)
- `=js:<expression>` — JavaScript expression (e.g. `=js:Math.random()`)
- `=vars.<varId>` — reference a variable by ID

**Wire a task output to a downstream task's input:**
```bash
uip case var bind <file> <target-stage-id> <target-task-id> <input-name> \
  --source-stage <source-stage-id> \
  --source-task <source-task-id> \
  --source-output <output-name> \
  --output json
```

This resolves the source output's variable ID and sets `input.value = "=vars.<varId>"` on the target task.

Run bindings in order — they execute sequentially and depend on previously added tasks and outputs.

### Step 7 — Add entry and exit conditions

Only add conditions that the user has explicitly specified or that are required by the design plan.

**Stage entry conditions** — when a stage should be triggered:
```bash
uip case stage-entry-conditions add <file> <stage-id> --display-name "<name>" \
  --rule-type selected-stage-completed --selected-stage-id <id>
```

**Stage exit conditions** — when a stage should complete and transition:
```bash
uip case stage-exit-conditions add <file> <stage-id> --display-name "<name>" \
  --rule-type selected-tasks-completed --selected-tasks-ids "<task-id1>,<task-id2>" \
  --marks-stage-complete true
```

**Case exit conditions** — when the whole case should close:
```bash
uip case case-exit-conditions add <file> --display-name "<name>" \
  --rule-type selected-stage-completed --selected-stage-id <id> \
  --marks-case-complete true
```

**Task entry conditions** — when a specific task should start:
```bash
uip case task-entry-conditions add <file> <stage-id> <task-id> \
  --display-name "<name>" \
  --rule-type selected-tasks-completed --selected-tasks-ids "<id>"
```

Rule types:
- Stage entry: `case-entered`, `selected-stage-exited`, `selected-stage-completed`, `wait-for-connector`, `adhoc`
- Stage exit: `selected-tasks-completed`, `wait-for-connector`
- Case exit: `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`
- Task entry: `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, `adhoc`

Each command outputs `{ ConditionId, ... }` on success — save the ID if you need to edit the condition later.

### Step 8 — Add SLA rules

Set SLA duration on the root case or on individual stages. Optionally add escalation rules and conditional SLA overrides. Only configure SLA if the user has specified timing requirements.

**Set root-level SLA** (applies to the whole case):
```bash
uip case sla set <file> --count 5 --unit d
```

**Set per-stage SLA**:
```bash
uip case sla set <file> --count 2 --unit w --stage-id <stage-id>
```

SLA units: `h` (hours), `d` (days), `w` (weeks), `m` (months).

**Add an escalation rule** (notify someone when at-risk or breached):
```bash
uip case sla escalation add <file> \
  --trigger-type at-risk --at-risk-percentage 80 \
  --recipient-scope User --recipient-target <target> --recipient-value <value>

uip case sla escalation add <file> \
  --trigger-type sla-breached \
  --recipient-scope UserGroup --recipient-target <target> --recipient-value <value> \
  --display-name "Notify Manager" --stage-id <stage-id>
```

**Add a conditional SLA rule** (expression-based override, root level only):
```bash
uip case sla rules add <file> --expression "=js:someCondition" --count 3 --unit d
```

Condition rules are evaluated in order before the default rule (`=js:true`).

### Step 9 — Validate the case file

Run validation before asking to debug. This catches structural errors locally without uploading anything.

```bash
uip case validate <file>
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Step 10.

On failure: the output lists each `[error]` or `[warning]` with its path and message. Fix the reported issues and re-run `validate` until it passes before proceeding.

### Step 10 — Ask About Debug

Once the case file passes validation, tell the user and ask:

> "Case file created and validated. Do you want to debug it? This will upload it to Studio Web and run a debug session."

Use AskUserQuestion with options: "Yes", "No"


### Step 11 — Debug (cloud) — only when explicitly requested

If the user says yes, run the debug command with the **project directory path**:

```bash
uip case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json
```

Requires `uip login`. Uploads to Studio Web, triggers a debug session in Orchestrator, and streams results.

**Do NOT run `case debug` automatically.** Debug executes the case for real — it will send emails, post Slack messages, call APIs, write to databases, etc. Only run debug when the user explicitly asks to debug or test the case. After validation succeeds, tell the user the case is ready and ask if they want to debug it.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Understand the case JSON schema** | [references/case-schema.md](references/case-schema.md) |
| **Know all CLI commands** | [references/case-commands.md](references/case-commands.md) |
| **Connect stages** | Step 5 above + [references/case-schema.md - Edges](references/case-schema.md) |
| **Add a task to a stage** | Step 6 above + [references/case-commands.md](references/case-commands.md) |
| **Manage runtime instances** | [references/case-commands.md - instances](references/case-commands.md) |
| **Find available processes/agents** | Run `uip case registry pull` then `uip case registry list` |
| **Add extra triggers (timer)** | Step 5b above + [references/case-commands.md — triggers](references/case-commands.md) |
| **Bind task inputs / wire outputs** | Step 6b above + [references/case-commands.md — var bind](references/case-commands.md) |

## Key Concepts

### Local vs cloud commands

| Commands | What they do | Auth needed |
|---------|-------------|-------------|
| `uip case cases`, `stages`, `tasks`, `edges` | Edit local JSON definition files | No |
| `uip case instance`, `processes`, `incidents` | Query/manage live Orchestrator data | Yes |

Always edit the local JSON file first, then push/deploy via the platform skill when ready.

### CLI output format

All `uip case` commands return structured JSON:
```json
{ "Result": "Success", "Code": "StageAdded", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Use `--output json` for programmatic use.

## References

- **[Case JSON Schema](references/case-schema.md)** — Full schema reference: root, nodes, edges, tasks, rules, SLA
- **[CLI Command Reference](references/case-commands.md)** — All `uip case` subcommands with parameters