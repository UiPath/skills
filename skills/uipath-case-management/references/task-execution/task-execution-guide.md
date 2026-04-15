# Task Execution Guide

Translates an approved `tasks.md` into `uip case` CLI commands. This is the **Execution Phase** (Steps 6–13) of the case management workflow.

Read the approved `tasks.md` from `<project-root>/planning/tasks.md` (produced by the [planning phase](task-planning-guide.md)). Execute each task in order. Capture IDs returned by each command and use them in subsequent steps.

## Step 6 — Create Case project structure

The case file must be inside a proper solution/project structure. Create it under the same `<project-root>` used by the planning phase:
```bash
# Create the solution inside the project root
cd <project-root> && uip solution new <solutionName>

# Create the case project inside the solution
cd <solutionName> && uip case init <projectName>

# Add the project to the solution
uip solution project add \
  <projectName> \
  <solutionName>.uipx
```

This scaffolds a complete project. See [case-schema.md](../case-schema.md) for the full project structure.

```bash
uip case cases add --name <CaseName> --file <project-root>/<solutionName>/<projectName>/caseplan.json
```

This scaffolds a minimal case JSON file with a root node and a default Trigger node.

Optional flags:
- `--case-identifier <string>` — defaults to the name
- `--identifier-type constant|external` — default: `constant`
- `--case-app-enabled` — enable the Case App UI

## Step 7 — Add stages

```bash
uip case stages add <file> --label "Review Application" --output json --is-required
uip case stages add <file> --label "Exception Handler" --type exception --output json
```

Stage types: `stage` (default), `exception`, `trigger`.

Stages are auto-positioned. Each stage gets a unique ID in the output — save it for adding tasks and edges.

## Step 8 — Connect stages with edges

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

## Step 9 — Add tasks to stages and bind variables

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

## Step 10 — Add entry and exit conditions

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

## Step 11 — Add SLA and escalation rules

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

## Step 12 — Validate

```bash
uip case validate <file>
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Step 13.

On failure: the output lists each `[error]` or `[warning]` with its path and message. Fix the reported issues and re-run `validate` until it passes.

## Step 13 — Ask about debug

Once the case file passes validation, tell the user and ask:

> "Case file created and validated. Do you want to debug it? This will upload it to Studio Web and run a debug session."

Use `AskUserQuestion` with options: "Yes", "No"

If the user says yes:
```bash
uip case debug "<project-root>/<solutionName>/<projectName>" --log-level debug --output json
```

Requires `uip login`. Uploads to Studio Web, triggers a debug session in Orchestrator, and streams results.

**Do NOT run `case debug` automatically.** Debug executes the case for real — it will send emails, post Slack messages, call APIs, write to databases, etc. Only run debug when the user explicitly asks.
