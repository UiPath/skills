---
name: uipath-case-management
description: "[PREVIEW] Case Management authoring (sdd.md → tasks.md → caseplan.json). Resolves registry taskTypeIds, generates task plans, executes uip case CLI. For .xaml→uipath-rpa, for .flow→uipath-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

End-to-end guide for creating UiPath Case Management definitions. Takes a design document (sdd.md), generates a reviewable task plan (tasks.md), and executes the plan via the `uip case` CLI.

## When to Use This Skill

- User asks to create a case management project or definition
- User asks to generate implementation tasks from an sdd.md
- User asks to break down a case spec into tasks or plan case tasks from sdd
- User asks to create a tasks.md from spec or interpret case spec
- User asks to convert a spec to an implementation plan
- User provides an sdd.md and wants a case built from it
- User is editing an existing case JSON file — adding stages, tasks, edges, or properties
- User wants to manage runtime case instances (list, pause, resume, cancel)
- User asks about the case management JSON schema — nodes, edges, tasks, rules, SLA

## Critical Rules

1. **Always regenerate tasks.md from scratch** — never do incremental updates to an existing tasks.md. This avoids stale state from previous runs.
2. **Run `uip case registry pull` before any interpretation** — pulling the registry cache upfront avoids network failures partway through.
3. **tasks.md entries are declarative specifications** — no `uip` CLI commands in tasks.md. Each task entry contains parameters, IDs, and metadata only. The execution phase translates specs into CLI calls.
4. **Follow every step as written — do not skip or shortcut** — the procedures exist because previous shortcuts caused failures. Do not skip registry lookups based on assumptions.
5. **Best effort on registry failures** — if a lookup fails, mark it as `[REGISTRY LOOKUP FAILED: <keywords>]` and continue. Do not abort the entire run.
6. **One task per T-number** — do not group multiple sdd.md tasks under a single T-number.
7. **Max 2 registry refresh retries** — if `registry pull --force` still yields no match after 2 retries, mark the lookup as failed and move on.
8. **Ask the user when login fails** — if `uip login status` shows not logged in, prompt the user to run `uip login` and stop until they confirm.
9. **Every stage needs at least one edge** connecting it to the case or it will be orphaned.
10. **Trigger node is created automatically** on `cases add` — don't add another unless it's a separate entry point (e.g. for a multi-trigger case).
11. **Tasks are 2D arrays**: `tasks[lane][index]` — use `--lane` to put tasks in parallel lanes.
12. **Edit `content/*.json` only** — `content/*.bpmn` is auto-generated and will be overwritten.
13. **Execute all commands in sequence. No parallel execution.**

## Workflow

This skill has two phases: **Planning** (Steps 0–4) generates a reviewable tasks.md from the sdd.md. **Execution** (Steps 6–13) translates tasks.md into CLI commands. Step 5 is the hard stop between them — do not proceed to execution without explicit user approval.

---

### Planning Phase

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

### Step 1 — Check login and pull registry

Registry discovery happens during interpretation, so login is required before starting.

```bash
uip login status --output json
uip case registry pull
```

If not logged in, prompt the user to log in first. The registry pull caches all resources locally at `~/.uip/case-resources/` so that subsequent searches are local disk lookups with no network failures mid-interpretation.

### Step 2 — Locate and parse the design document

Accept the sdd.md file path from the user, or ask if not provided.

- **sdd.md** — the semantic design document. This is the sole input: it describes stages, tasks, edges, rules, SLA, component types, persona information, and provides the search keywords for registry lookups.

Parse sdd.md as the single source of truth for the case design.

### Step 3 — Resolve task types via registry

For each task in the sdd.md, determine the correct `taskTypeId` by reading the local registry cache files directly. After `registry pull` (Step 1), all resources are cached at `~/.uip/case-resources/`. Search these files instead of using CLI search commands — it is more reliable and faster.

#### Component type mapping

This table maps sdd.md component types to the primary cache file to search and the CLI `--type` flag:

| component_type | Primary cache file | CLI tasks add --type |
|---|---|---|
| API_WORKFLOW | `api-index.json` | api-workflow |
| AGENTIC_PROCESS | `processOrchestration-index.json` | process |
| HITL | `action-apps-index.json` | action |
| RPA | `process-index.json` | rpa |
| AGENT | `agent-index.json` | agent |
| CASE_MANAGEMENT | `caseManagement-index.json` | case-management |
| CONNECTOR_ACTIVITY | `typecache-activities-index.json` | execute-connector-activity |
| CONNECTOR_TRIGGER | `typecache-triggers-index.json` | wait-for-connector |
| EXTERNAL_AGENT | *(not in cache)* | external-agent |
| TIMER | *(not in cache)* | wait-for-timer |
| PROCESS | `process-index.json` | process |

For types marked "not in cache" (`EXTERNAL_AGENT`, `TIMER`), use the `--type` value directly without searching.

For all other types, follow the procedure in the [registry-discovery reference](references/registry-discovery.md):

1. **Search the primary cache file** by matching the task name and folder path from the sdd.md.
2. **If no match in the primary file**, search all other cache files — the sdd.md component type label may not match the actual registry type (e.g., an "RPA" task may be registered as `process`).
3. **Pick the best match** using exact name + folder path from sdd.md Process References.
4. **Force-refresh and retry** (`uip case registry pull --force`) only if no match is found across all cache files.
5. **Extract the correct identifier field** per cache file type (`entityKey`, `id`, or `uiPathActivityTypeId`).
6. For **connector tasks** (typecache-activities, typecache-triggers), also run `get-connector` and `get-connection` CLI commands to collect full details.

Collect all registry results for the debug output in Step 4.

### Step 4 — Generate tasks.md and registry-resolved.json

Create a `tasks/` folder in the same directory as the sdd.md file. Generate `tasks.md` using the structure below. Each section is a numbered task (T01, T02, ...) that maps to one or more CLI commands.

Read the [CLI command reference](references/case-commands.md) and the [case JSON schema reference](references/case-schema.md) to understand the available flags and data structures as you generate each task.

Also write a `registry-resolved.json` file in the `tasks/` folder containing all registry lookup results keyed by task ID. This serves as a debugging and audit trail. Include:
- The search query used
- All matched results
- Which result was selected and why

#### Task structure

The task ordering follows the execution phase steps: stages → edges → tasks → conditions → SLA. The task title IS the action description — do not add a redundant `what` or `type` field. Absorb type into the title (e.g., "Add api-workflow task" not "Add task" + "type: api-workflow").

##### 1. Create case file (T01)

Title format: `Create case file "<name>"`

Set up the case definition with name, description, key prefix.

##### 2. Configure trigger (T02)

Title format: `Configure wait-for-connector trigger "<name>"`

For connector triggers, resolve via registry using `typecache-triggers` and include connection details from `get-connection` if applicable.

##### 3. Create stages (one per stage)

Title format: `Create stage "<name>"` or `Create exception stage "<name>"`

Each stage is its own task. Basic properties only — SLA and escalation come later (section 7). Each stage specifies:

- **isRequired** — whether this stage must complete for the case to be considered complete (true/false). Determines which stages are tracked by `required-stages-completed` case exit conditions. Determine from the sdd.md using these criteria:
  - `true` — **Default for regular stages.** The stage is part of the main case flow and must complete before the case can close. Look for: stages on the happy path, stages described as mandatory, stages without "optional" or "exception" qualifiers.
  - `false` — Use for exception stages, optional review stages, or rework loops that the case can complete without entering. Look for: stages labeled as "exception", "optional", "fallback", "on-error", or stages that are only reached via conditional/interrupting entry conditions.

Example:
```markdown
## T05: Create stage "PO Receipt & Triage"
- isRequired: true
- order: after T04
- verify: Confirm Result: Success, capture StageId

## T06: Create exception stage "Exception Handling"
- isRequired: false
- order: after T05
- verify: Confirm Result: Success, capture StageId
```

##### 4. Setup edges (one per edge)

Title format: `Add edge "<source>" → "<target>"`

One task per edge with human-readable condition labels.

##### 5. Add tasks (one per task)

Title format: `Add <type> task "<name>" to "<stage>"`

Each task from the sdd.md becomes its own numbered task. Do NOT group multiple tasks under a single T-number. Each task specifies:

- **taskTypeId** — resolved from the registry in Step 3.
- **inputs** — what data this task consumes. Each input uses one of two formats:
  - **Literal or expression**: `input_name = "<value>"` — a static value or expression prefix (`=metadata.`, `=js:`, `=vars.`, `=datafabric.`, `=bindings.`).
  - **Cross-task reference**: `input_name <- "Stage Name"."Task Name".output_name` — wires another task's output into this input. The execution phase translates this into a `uip case var bind --source-stage --source-task --source-output` command.
- **outputs** — what data this task produces, listed as named output fields. Downstream tasks reference these via the cross-task input format above. To discover available output names, run `uip case tasks describe --type <type> --id <taskTypeId>` during planning.
- **runOnlyOnce** — whether the task should execute only once per case instance (true/false). Sourced from the sdd.md. Maps to CLI flag `--should-run-only-once`. Defaults to true if not specified in sdd.md.
- **isRequired** — whether the task is required for stage completion (true/false). Sourced from the sdd.md. Maps to CLI flag `--is-required`. Defaults to true if not specified in sdd.md.
- **order** — which task(s) must complete before this one runs (expressed as a dependency, e.g., "after T05").
- **verify** — what the execution phase should check after executing this task to confirm success.
- **recipient** — for `action` tasks only: the email address of the assigned user, sourced from sdd.md. Omit if the sdd.md does not specify an assignee.
- **priority** — for `action` tasks only: `Low`, `Medium`, `High`, or `Critical`, sourced from sdd.md (default: `Medium` if not specified).

> **No uip commands in task entries.** Each task is a declarative specification — parameters, IDs, and metadata only. Never write `uip case tasks add ...` or any shell command inside a task body. The execution phase translates these specs into CLI commands.

> Ignore lane concept in creating the task. It is no longer feasible for managing the parallelism.

Example (task with outputs and literal inputs):
```markdown
## T25: Add api-workflow task "Monitor Order Inbox" to "PO Receipt & Triage"
- taskTypeId: abc-123-def
- inputs:
  - inbox_config = "=vars.inbox_config"
  - po_patterns = "=vars.po_patterns"
- outputs: email_id, sender_email, po_document
- runOnlyOnce: true
- isRequired: true
- order: after T24
- verify: Confirm Result: Success, capture TaskId from output
```

Example (task consuming another task's outputs via cross-task reference):
```markdown
## T26: Add agent task "Classify Purchase Order" to "PO Receipt & Triage"
- taskTypeId: def-456-ghi
- inputs:
  - po_document <- "PO Receipt & Triage"."Monitor Order Inbox".po_document
  - sender_email <- "PO Receipt & Triage"."Monitor Order Inbox".sender_email
- outputs: po_category, urgency_score, extracted_line_items
- runOnlyOnce: true
- isRequired: true
- order: after T25
- verify: Confirm Result: Success, capture TaskId from output
```

Example (HITL/action with mixed input types):
```markdown
## T30: Add action task "Review Purchase Order" to "PO Receipt & Triage"
- taskTypeId: xyz-456-abc
- recipient: approver@corp.com
- priority: High
- inputs:
  - po_document <- "PO Receipt & Triage"."Monitor Order Inbox".po_document
  - po_category <- "PO Receipt & Triage"."Classify Purchase Order".po_category
  - review_deadline = "=js:new Date(Date.now() + 86400000).toISOString()"
- outputs: review_decision, reviewer_comments
- isRequired: true
- order: after T26
- verify: Confirm Result: Success, capture TaskId from output
```

##### 6. Configure conditions (one per condition)

Title format: `Add <scope> <event> condition for "<target>"` (e.g., `Add stage entry condition for "PO Receipt & Triage"`)

Each condition is its own numbered task. Process conditions in this order: stage entry conditions, stage exit conditions, case exit conditions, then task entry conditions.

**Stage entry conditions** — control when a stage is entered:

- **rule-type** — `case-entered`, `selected-stage-completed`, `selected-stage-exited`, or `wait-for-connector`
- **selected-stage-id** — the stage this rule references (required when rule-type is `selected-stage-completed` or `selected-stage-exited`)
- **order** — which task(s) must complete before this one
- **verify** — what to check after execution

**Stage exit conditions** — control when/how a stage exits:

- **rule-type** — depends on the exit behavior:
  - `required-tasks-completed` — use when `marks-stage-complete: true`. All tasks in the stage must complete; no task ID list needed.
  - `selected-tasks-completed` — use when `marks-stage-complete: false` (exit-only conditions). Requires explicit task IDs.
  - `wait-for-connector` — wait for an external connector event.
- **selected-tasks-ids** — comma-separated task names that must complete (required only when rule-type is `selected-tasks-completed`)
- **type** — exit routing type. Determine from the sdd.md using these criteria:
  - `exit-only` — **Default.** Use when the stage exits normally and the case continues forward along the configured edges.
  - `wait-for-user` — Use when the sdd.md indicates the exit requires a manual user decision or approval before proceeding.
  - `return-to-origin` — Use when the sdd.md describes a rework or exception loop that sends the case back to the stage it came from.
- **exit-to-stage-id** — the target stage name when the exit routes to a specific stage. Required when the sdd.md names an explicit destination stage for this exit. Omit when the routing follows the default edge configuration or uses `return-to-origin`.
- **marks-stage-complete** — whether this exit counts as stage completion (true/false)
- **order** — which task(s) must complete before this one
- **verify** — what to check after execution

**Case exit conditions** — control when the entire case completes:

Use `required-stages-completed` as the primary rule-type. This mirrors how stage exit conditions use `required-tasks-completed` — the case completes when all stages marked `isRequired: true` (set in section 3) have completed.

- **rule-type** — determines completion logic:
  - `required-stages-completed` — **Preferred.** Use when `marks-case-complete: true`. The case completes when every stage with `isRequired: true` has completed. No stage ID list needed.
  - `selected-stage-completed` — Use only when a non-completion exit depends on a specific stage. Requires `selected-stage-id`.
  - `selected-stage-exited` — Use only when an exit depends on a stage being exited (not necessarily completed). Requires `selected-stage-id`.
  - `wait-for-connector` — wait for an external connector event.
- **selected-stage-id** — the stage this rule references (required only for `selected-stage-completed` or `selected-stage-exited`)
- **marks-case-complete** — whether this exit counts as case completion (true/false)
- **order** — which task(s) must complete before this one
- **verify** — what to check after execution

Example:
```markdown
## T100: Add case exit condition — case resolved
- rule-type: required-stages-completed
- marks-case-complete: true
- order: after T99
- verify: Confirm Result: Success
```

**Task entry conditions** — control when a task within a stage starts:

- **rule-type** — `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, or `adhoc`
- **selected-tasks-ids** — comma-separated task names that must complete (required when rule-type is `selected-tasks-completed`)
- **condition-expression** — expression for the rule (required when rule-type is `adhoc`)
- **order** — which task(s) must complete before this one
- **verify** — what to check after execution

**Stage exit condition examples:**

```markdown
## T80: Add stage exit condition for "PO Receipt & Triage" — all tasks done
- rule-type: required-tasks-completed
- type: exit-only
- marks-stage-complete: true
- order: after T79
- verify: Confirm Result: Success

## T81: Add stage exit condition for "Manager Review" — user picks next step
- rule-type: required-tasks-completed
- type: wait-for-user
- marks-stage-complete: true
- order: after T80
- verify: Confirm Result: Success

## T82: Add stage exit condition for "Exception Handling" — return to origin
- rule-type: required-tasks-completed
- type: return-to-origin
- marks-stage-complete: false
- order: after T81
- verify: Confirm Result: Success

## T83: Add stage exit condition for "Initial Review" — route to Escalation
- rule-type: selected-tasks-completed
- selected-tasks-ids: "Flag for Escalation"
- type: exit-only
- exit-to-stage-id: "Escalation"
- marks-stage-complete: false
- order: after T82
- verify: Confirm Result: Success
```

##### 7. Set SLA and escalation rules

SLA and escalation come last. They are broken into individual tasks, ordered as follows for each target (root first, then each stage):

1. **Set default SLA** — the time-based catch-all SLA. Always last in the slaRules array. Title format: `Set default SLA for "<target>" to <duration>`
2. **Add conditional SLA rules** (if any) — condition-based SLA overrides evaluated before the default. Describe the condition in natural language from the sdd.md. Do NOT fabricate expression syntax. **Order matters:** rules are evaluated in the order they are added; the first rule whose expression evaluates to true becomes the active SLA. Title format: `Add conditional SLA rule for "<target>" — <condition summary>`
3. **Add escalation rules** — one task per escalation rule. Each rule specifies a trigger type (`at-risk` with percentage threshold, or `sla-breached`) and one or more recipients. Each recipient has a scope (`User` or `UserGroup`), a target, and a display value. Title format: `Add escalation rule for "<target>" — <trigger summary>`

Example:
```markdown
## T150: Set default SLA for "PO Receipt & Triage" to 15 minutes
- count: 15
- unit: m
- order: after T149
- verify: Confirm Result: Success

## T151: Add conditional SLA rule for root case — when priority is Urgent
- condition: Priority = Urgent
- count: 30
- unit: m
- order: after T150
- verify: Confirm Result: Success

## T152: Add escalation rule for "PO Receipt & Triage" — At-Risk 80%
- trigger-type: at-risk
- at-risk-percentage: 80
- recipients:
  - User: manager@corp.com
  - UserGroup: Order Management Team
- order: after T151
- verify: Confirm Result: Success and capture the EscalationRuleId
```

##### Not Covered section

Add a brief section at the end of tasks.md listing things referenced in the sdd.md but outside the scope of the `uip case` CLI:
- **Data Fabric entity schemas and global variables** — referenced in task mappings but must be configured separately in Data Fabric.

---

### Step 5 — HARD STOP: User reviews and approves tasks.md

Present the generated tasks.md to the user and ask for explicit approval before proceeding to execution.

Use `AskUserQuestion` with options: "Approve and proceed", "Request changes"

If the user requests changes, update tasks.md and re-present for approval. Do NOT proceed to Step 6 until the user explicitly approves.

**After the user approves:** run `/compact` to free context, then re-read `tasks.md` before proceeding to Step 6. The tasks.md file is the complete handoff artifact between the planning and execution phases.

---

### Execution Phase

Execute each task from the approved tasks.md in order, translating declarative specifications into `uip case` CLI commands. Capture IDs returned by each command and use them in subsequent steps.

### Step 6 — Create Case project structure

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
uip case cases add --name <CaseName> --file <directory>/<solutionName>/<projectName>/caseplan.json
```

> **`caseplan.json` is the literal filename — do not substitute the case name or project name here.**

This scaffolds a minimal case JSON file with a root node and a default Trigger node.

Optional flags:
- `--case-identifier <string>` — defaults to the name
- `--identifier-type constant|external` — default: `constant`
- `--case-app-enabled` — enable the Case App UI

### Step 7 — Add stages

```bash
uip case stages add <file> --label "Review Application" --output json --is-required
uip case stages add <file> --label "Exception Handler" --type exception --output json
```

Stage types: `stage` (default), `exception`, `trigger`.

Stages are auto-positioned. Each stage gets a unique ID in the output — save it for adding tasks and edges.

### Step 8 — Connect stages with edges

The default trigger ID is `trigger_1`. Connect it to the first stage, then connect stages in sequence. Add edge labels for conditions if needed.

```bash
uip case edges add <file> --source <trigger-id> --target <first-stage-id> --output json
uip case edges add <file> --source <stage-id> --target <next-stage-id> --label "Approved" --output json
```

Edge type is inferred automatically: Trigger → `TriggerEdge`, Stage → `Edge`.

Source/target handle directions default to `right`/`left` for stage edges and trigger edges.

For multi-trigger cases, add extra triggers:

```bash
uip case triggers add-timer <file> --every 1h --output json
uip case triggers add-timer <file> --every 2d --at 2026-04-26T10:00:00.000Z --output json
uip case triggers add-timer <file> --time-cycle "R/PT1H" --output json
```

Capture the returned trigger ID, then connect it to its target stage with an edge.

### Step 9 — Add tasks to stages and bind variables

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

Use `--lane <index>` for parallel execution (lane 0, 1, 2, etc.).

**Bind task inputs and wire outputs** after adding each task. For each task in tasks.md, translate its `inputs` specification into `uip case var bind` commands.

**Discover available inputs and outputs** — after adding a task with `--task-type-id`, the task is auto-enriched with input/output schemas. To inspect what inputs and outputs are available:

```bash
uip case tasks describe --type <type> --id <taskTypeId> --output json
```

Use the output to confirm that the input and output names in tasks.md match the actual schema.

**Bind literal or expression values** — for each input specified as `input_name = "<value>"` in tasks.md:

```bash
uip case var bind <file> <stage-id> <task-id> <input-name> --value "<value>" --output json
```

Valid expression prefixes: `=metadata.<field>`, `=js:<expression>`, `=vars.<varId>`, `=datafabric.<entity>`, `=bindings.<name>`, `=orchestrator.JobAttachments`.

**Wire cross-task references** — for each input specified as `input_name <- "Stage Name"."Task Name".output_name` in tasks.md:

1. Look up the source stage ID and source task ID from the IDs captured when those tasks were added in earlier steps.
2. Run the bind command:

```bash
uip case var bind <file> <target-stage-id> <target-task-id> <input-name> \
  --source-stage <source-stage-id> \
  --source-task <source-task-id> \
  --source-output <output-name> \
  --output json
```

**Binding order** — process bindings in task order as listed in tasks.md. Since tasks are ordered by dependency (`order: after T24`), binding each task's inputs immediately after adding it ensures all source tasks already exist. If a cross-task reference points to a task not yet added, defer that binding until the source task is created.

### Step 10 — Add entry and exit conditions

Only add conditions specified in tasks.md.

**Stage entry conditions:**
```bash
uip case stage-entry-conditions add <file> <stage-id> --display-name "<name>" \
  --rule-type selected-stage-completed --selected-stage-id <id>
```

**Stage exit conditions:**
```bash
uip case stage-exit-conditions add <file> <stage-id> --display-name "<name>" \
  --rule-type selected-tasks-completed --selected-tasks-ids "<task-id1>,<task-id2>" \
  --marks-stage-complete true
```

**Case exit conditions:**
```bash
uip case case-exit-conditions add <file> --display-name "<name>" \
  --rule-type required-stages-completed --marks-case-complete true
```

**Task entry conditions:**
```bash
uip case task-entry-conditions add <file> <stage-id> <task-id> \
  --display-name "<name>" \
  --rule-type selected-tasks-completed --selected-tasks-ids "<id>"
```

Rule types:
- Stage entry: `case-entered`, `selected-stage-exited`, `selected-stage-completed`, `wait-for-connector`, `adhoc`
- Stage exit: `selected-tasks-completed`, `wait-for-connector`, `required-tasks-completed`
- Case exit: `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`, `required-stages-completed`
- Task entry: `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, `adhoc`

### Step 11 — Add SLA and escalation rules

Set SLA duration on the root case or on individual stages. Only configure SLA if specified in tasks.md.

```bash
# Root-level SLA
uip case sla set <file> --count 5 --unit d

# Per-stage SLA
uip case sla set <file> --count 2 --unit w --stage-id <stage-id>

# Escalation rule
uip case sla escalation add <file> \
  --trigger-type at-risk --at-risk-percentage 80 \
  --recipient-scope User --recipient-target <target> --recipient-value <value>

# Conditional SLA rule
uip case sla rules add <file> --expression "=js:someCondition" --count 3 --unit d
```

SLA units: `h` (hours), `d` (days), `w` (weeks), `m` (months).

### Step 12 — Validate

```bash
uip case validate <file>
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Step 13.

On failure: the output lists each `[error]` or `[warning]` with its path and message. Fix the reported issues and re-run `validate` until it passes.

### Step 13 — Ask about debug

Once the case file passes validation, tell the user and ask:

> "Case file created and validated. Do you want to debug it? This will upload it to Studio Web and run a debug session."

Use `AskUserQuestion` with options: "Yes", "No"

If the user says yes:
```bash
uip case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json
```

Requires `uip login`. Uploads to Studio Web, triggers a debug session in Orchestrator, and streams results.

**Do NOT run `case debug` automatically.** Debug executes the case for real — it will send emails, post Slack messages, call APIs, write to databases, etc. Only run debug when the user explicitly asks.
Debug is for **testing that the case runs correctly** — not for publishing or viewing. To publish, use Step 14 instead.

### Step 14 — Publish to Studio Web

**This is the default publish target.** When the user wants to publish, view, or share the case, upload it to Studio Web using `solution bundle` + `solution upload`:

Always ask user:

> "Do you want to publish it to Studio Web? This will upload it and make it available for visualization and editing."

Use `AskUserQuestion` with options: "Yes", "No"

If the user says yes:
```bash
# Bundle the solution directory into a .uis file
uip solution bundle "<SolutionDir>" --output .

# Upload the .uis to Studio Web
uip solution upload "<SolutionName>.uis" --output json
```

The `bundle` command requires a solution directory containing a `.uipx` file. If the project was created with `uip case init`, it lives inside a solution directory already. The `upload` command pushes it to Studio Web where the user can visualize, inspect, edit, and publish from the browser. Share the Studio Web URL with the user.

**Do NOT run `uip case pack` + `uip solution publish` unless the user explicitly asks to deploy to Orchestrator.** That path puts the case directly into Orchestrator as a process, bypassing Studio Web — the user cannot visualize or edit it there. If the user asks to "publish" without specifying where, always default to the Studio Web path (`solution bundle` + `solution upload`).

For Orchestrator deployment when explicitly requested, see [references/case-commands.md](references/case-commands.md) for `uip case pack` and the [/uipath:uipath-platform](/uipath:uipath-platform) skill for `uip solution publish`.

## Anti-patterns — What NOT to Do

- Do NOT put `uip case ...` CLI commands in tasks.md — causes double-execution or mis-parsing. tasks.md is declarative only.
- Do NOT incrementally update an existing tasks.md — always regenerate from scratch to avoid stale state.
- Do NOT skip registry lookups based on assumptions like "this type is not discoverable." Always search the cache files first.
- Do NOT group multiple sdd.md tasks under one T-number — each task in the sdd.md gets its own numbered entry.
- Do NOT fabricate expression syntax for conditional SLA rules — describe the condition in natural language; the execution phase determines the correct expression format.
- Do NOT add interactive checkpoints during tasks.md generation — run silently and let the user review the output after completion.
- Do NOT include parameters the CLI does not support — only include what `uip case` can act on (see [CLI command reference](references/case-commands.md)).
- Do NOT use lane assignments in tasks.md — the lane concept is no longer used for managing parallelism in the planning phase.
- Do NOT edit `.bpmn` files — they are auto-generated and will be overwritten.
- Do NOT run debug automatically — it has real side effects (sends emails, calls APIs, writes to databases).
- Do NOT execute commands in parallel — run all CLI commands sequentially.
- Do NOT fabricate input or output names in cross-task references — run `uip case tasks describe` to discover actual input/output names from the task's schema.

## Reference Navigation

| I need to... | Read these |
|---|---|
| **Understand the case JSON schema** | [references/case-schema.md](references/case-schema.md) |
| **Know all CLI commands** | [references/case-commands.md](references/case-commands.md) |
| **Resolve task types from registry** | [references/registry-discovery.md](references/registry-discovery.md) |
| **Connect stages** | Step 8 above + [references/case-schema.md — Edges](references/case-schema.md) |
| **Add a task to a stage** | Step 9 above + [references/case-commands.md](references/case-commands.md) |
| **Find available processes/agents** | Run `uip case registry pull` then `uip case registry list` |

## Key Concepts

### Local vs cloud commands

| Commands | What they do | Auth needed |
|---------|-------------|-------------|
| `uip case cases`, `stages`, `tasks`, `edges` | Edit local JSON definition files | No |
| `uip case instance`, `processes`, `incidents` | Query/manage live Orchestrator data | Yes |

### CLI output format

All `uip case` commands return structured JSON:
```json
{ "Result": "Success", "Code": "StageAdded", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Use `--output json` for programmatic use.
