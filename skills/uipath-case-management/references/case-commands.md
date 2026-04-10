# uip case — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

---

## uip case init

Scaffold a new Case project with boilerplate files.

```bash
uip case init <name>
uip case init my-case-project
uip case init my-case-project --force
```

| Flag | Description |
|------|-------------|
| `<name>` | **(required)** Project name (letters, numbers, `_`, `-` only) |
| `--force` | Overwrite existing directory (does not clear existing files) |

Creates: `<name>/project.uiproj`, `<name>/content/operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`, and a starter `.bpmn` file.

---

## uip case pack

Pack a Case project directory into a `.nupkg` file.

```bash
uip case pack <projectPath> <outputPath>
uip case pack ./my-case-project ./dist
uip case pack ./my-case-project ./dist --name MyCase --version 2.0.0
```

| Flag | Description |
|------|-------------|
| `<projectPath>` | **(required)** Path to the Case project directory |
| `<outputPath>` | **(required)** Output directory for the `.nupkg` |
| `-n, --name <name>` | Package name (default: project folder name) |
| `-v, --version <version>` | Package version (default: `1.0.0`) |

---

## uip case debug

Debug a Case JSON file via a Studio Web debug session. **Requires `uip login`.**

```bash
uip case debug <projectDirectory>
uip case debug ./mySolution/myProject
uip case debug ./mySolution/myProject --folder-id 42 --poll-interval 3000
```

| Flag | Description |
|------|-------------|
| `<projectDirectory>` | **(required)** Path to the case project directory (must contain `project.uiproj`) |
| `--folder-id <id>` | Orchestrator folder ID (`OrganizationUnitId`). Auto-detected if omitted. |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--output <format>` | Output format: `table`, `json`, `yaml`, `plain` (default: `json`) |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

---

## uip case cases

Manage local case management definition JSON files.

```bash
# Create a new case definition file
uip case cases add --name <name> --file <output.json>
uip case cases add --name "Loan Approval" --file loan-approval.json
uip case cases add --name "Loan Approval" --file loan-approval.json \
  --case-identifier "LOAN" --identifier-type constant --case-app-enabled --description "Loan case"

# Edit an existing case definition file
uip case cases edit <file> --name <new-name>
uip case cases edit loan-approval.json --case-identifier "LA" --identifier-type external
uip case cases edit loan-approval.json --case-app-enabled
```

Options for `add`:
| Flag | Description |
|------|-------------|
| `-n, --name <name>` | **(required)** Name of the case definition |
| `-f, --file <path>` | **(required)** Output path for the new JSON file |
| `--case-identifier <string>` | Case identifier string (defaults to name) |
| `--identifier-type constant\|external` | Identifier type (default: constant) |
| `--case-app-enabled` | Enable the Case App UI |

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-n, --name <name>` | New name |
| `--case-identifier <string>` | New case identifier |
| `--identifier-type constant\|external` | New identifier type |
| `--case-app-enabled` | Enable the Case App |

---

## uip case stages

Manage stage nodes within a case definition JSON file.

```bash
# Add a stage
uip case stages add <file>
uip case stages add <file> --label "Review" --type stage --description "Review Stage"
uip case stages add <file> --label "Exception Handler" --type exception

# Edit a stage label
uip case stages edit <file> <stage-id> --label "New Label"

# Print a stage and its connected edges
uip case stages get <file> <stage-id>

# Remove a stage and its connected edges
uip case stages remove <file> <stage-id>
```

Stage types: `stage` (default), `exception`, `trigger`.

Auto-positioning: stages are placed at `x = 100 + (existingStageCount * 500), y = 200`.

Output on `add`: `{ StageId, Type, Label, Position }` — save `StageId` for tasks and edges.

---

## uip case stage-entry-conditions

Manage entry conditions on a stage within a case management definition JSON file.

```bash
# Add an entry condition to a stage
uip case stage-entry-conditions add <file> <stage-id>
uip case stage-entry-conditions add case.json <stage-id> --display-name "Pre-check"
uip case stage-entry-conditions add case.json <stage-id> --display-name "Interrupt" --is-interrupting true
uip case stage-entry-conditions add case.json <stage-id> --rule-type case-entered
uip case stage-entry-conditions add case.json <stage-id> --rule-type selected-stage-exited --selected-stage-id <id>

# Edit an entry condition
uip case stage-entry-conditions edit <file> <stage-id> <condition-id> --display-name "Updated"
uip case stage-entry-conditions edit case.json <stage-id> <condition-id> --is-interrupting false
uip case stage-entry-conditions edit case.json <stage-id> <condition-id> --rule-type wait-for-connector --condition-expression "expr"

# Get an entry condition
uip case stage-entry-conditions get <file> <stage-id> <condition-id>

# Remove an entry condition
uip case stage-entry-conditions remove <file> <stage-id> <condition-id>
```

Options for `add`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `<stage-id>` | **(required)** ID of the stage node |
| `-d, --display-name <name>` | Display name for the condition |
| `--is-interrupting <bool>` | Whether the condition is interrupting (`true` or `false`) |
| `--rule-type <type>` | Initial rule type: `case-entered`, `selected-stage-exited`, `selected-stage-completed`, `wait-for-connector` |
| `--condition-expression <expr>` | Condition expression for the initial rule |
| `--selected-stage-id <id>` | Stage ID for `selected-stage-*` initial rules |

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-d, --display-name <name>` | New display name for the condition |
| `--is-interrupting <bool>` | Set is-interrupting (`true` or `false`) |
| `--rule-type <type>` | Append a new rule with this type (same valid types as `add`) |
| `--condition-expression <expr>` | Condition expression for the new rule |
| `--selected-stage-id <id>` | Stage ID for `selected-stage-*` rules |

Output on `add`: `{ File, StageId, ConditionId, DisplayName, IsInterrupting, Rules }` — save `ConditionId` for future edits.

---

## uip case stage-exit-conditions

Manage exit conditions on a stage within a case management definition JSON file.

```bash
# Add an exit condition to a stage
uip case stage-exit-conditions add <file> <stage-id>
uip case stage-exit-conditions add case.json <stage-id> --display-name "Approved" --type exit-only
uip case stage-exit-conditions add case.json <stage-id> --display-name "Go to Review" --exit-to-stage-id <stage-id>
uip case stage-exit-conditions add case.json <stage-id> --marks-stage-complete true
uip case stage-exit-conditions add case.json <stage-id> --rule-type selected-tasks-completed --selected-tasks-ids "<task-id1>,<task-id2>"

# Edit an exit condition
uip case stage-exit-conditions edit <file> <stage-id> <condition-id> --display-name "New Name"
uip case stage-exit-conditions edit case.json <stage-id> <condition-id> --type wait-for-user --exit-to-stage-id <id>
uip case stage-exit-conditions edit case.json <stage-id> <condition-id> --rule-type wait-for-connector --condition-expression "expr"

# Get an exit condition
uip case stage-exit-conditions get <file> <stage-id> <condition-id>

# Remove an exit condition
uip case stage-exit-conditions remove <file> <stage-id> <condition-id>
```

Exit condition types: `exit-only`, `wait-for-user`, `return-to-origin`.

Options for `add`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `<stage-id>` | **(required)** ID of the stage node |
| `-d, --display-name <name>` | Display name for the condition |
| `-t, --type <type>` | Exit type: `exit-only`, `wait-for-user`, or `return-to-origin` |
| `--exit-to-stage-id <id>` | ID of the stage to transition to on exit |
| `--marks-stage-complete <bool>` | Whether this condition marks the stage complete (`true` or `false`) |
| `--rule-type <type>` | Initial rule type: `selected-tasks-completed`, `wait-for-connector` |
| `--condition-expression <expr>` | Condition expression for the initial rule |
| `--selected-tasks-ids <ids>` | Comma-separated task IDs for `selected-tasks-completed` initial rule |

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-d, --display-name <name>` | New display name for the condition |
| `-t, --type <type>` | New exit type |
| `--exit-to-stage-id <id>` | New target stage ID |
| `--marks-stage-complete <bool>` | Set marks-stage-complete (`true` or `false`) |
| `--rule-type <type>` | Append a new rule with this type (same valid types as `add`) |
| `--condition-expression <expr>` | Condition expression for the new rule |
| `--selected-tasks-ids <ids>` | Comma-separated task IDs for `selected-tasks-completed` rules |

Output on `add`: `{ File, StageId, ConditionId, DisplayName, Type, ExitToStageId, MarksStageComplete, Rules }` — save `ConditionId` for future edits.

---

## uip case validate

Validate a case management JSON file against case management rules.

```bash
uip case validate <file>
uip case validate case.json
```

| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |

Output: `{ File, Status: "Valid" }` on success. Errors and warnings are reported inline.

---

## uip case triggers

Manage triggers in a case management definition JSON file. Also updates `entry-points.json` in the same directory.

```bash
# Add a manual trigger
uip case triggers add-manual <file>
uip case triggers add-manual case.json --display-name "Start Manually"
uip case triggers add-manual case.json --position "-100,340"

# Add a timer trigger
uip case triggers add-timer <file> --every <duration>
uip case triggers add-timer case.json --every 1h
uip case triggers add-timer case.json --every 2d --at 2026-04-26T10:40:00.000-07:00 --repeat 5
uip case triggers add-timer case.json --time-cycle "R/PT1H"  # raw ISO 8601

# Add a connector event trigger (requires uip login)
uip case triggers add-event <file> --type-id <id> --connection-id <id>
uip case triggers add-event case.json --type-id <uiPathActivityTypeId> --connection-id <uuid>
uip case triggers add-event case.json --type-id <id> --connection-id <id> \
  --event-params '{"project":"PROJ"}' --filter '((fields.status=`Open`))'
```

Options for `add-manual`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `-d, --display-name <name>` | Display name (auto: `Trigger N`) |
| `--position <x,y>` | Explicit position (default: auto-stacked left of stages) |

Options for `add-timer`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--every <duration>` | Repeat interval: `10s`, `5m`, `1h`, `2d`, `1w`, `3mo` or ISO 8601 like `PT10S` (required unless `--time-cycle` is set) |
| `--at <datetime>` | Start time as ISO 8601 datetime |
| `--repeat <count>` | Number of repetitions (omit for infinite) |
| `--time-cycle <expr>` | Raw ISO 8601 repeating interval (overrides `--every`/`--at`/`--repeat`) |
| `-d, --display-name <name>` | Display name (auto: `Trigger N`) |
| `--position <x,y>` | Explicit position |

Options for `add-event`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--type-id <id>` | **(required)** `uiPathActivityTypeId` from TypeCache triggers |
| `--connection-id <id>` | **(required)** Connection UUID to bind to the trigger |
| `--event-params <json>` | JSON object of event parameter key/value pairs |
| `--filter <expression>` | Filter expression, e.g. `((fields.progress<\`222\`))` |
| `-d, --display-name <name>` | Display name (auto: `Trigger N`) |
| `--position <x,y>` | Explicit position |

Output on add: `{ File, TriggerId, Type, DisplayName, [TimeCycle] }` — save `TriggerId` for edges.

---

## uip case var

Manage variable bindings in a case management definition.

```bash
# Bind a task input to a literal or expression value
uip case var bind <file> <stage-id> <task-id> <input-name> --value "hello"
uip case var bind case.json <stage-id> <task-id> Amount --value "=metadata.amount"
uip case var bind case.json <stage-id> <task-id> Code --value "=js:Math.random()"

# Bind a task input to another task's output
uip case var bind <file> <stage-id> <task-id> <input-name> \
  --source-stage <src-stage-id> --source-task <src-task-id> --source-output <output-name>
```

Options for `bind`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `<stage-id>` | **(required)** ID of the stage containing the target task |
| `<task-id>` | **(required)** ID of the target task |
| `<input-name>` | **(required)** Name of the input to bind |
| `--value <value>` | Raw value or expression (`=metadata.X`, `=js:X`, `=vars.X`, `=bindings.X`, etc.) |
| `--source-stage <id>` | Source stage ID (requires `--source-task` and `--source-output`) |
| `--source-task <id>` | Source task ID (requires `--source-stage` and `--source-output`) |
| `--source-output <name>` | Source output name (requires `--source-stage` and `--source-task`) |

Exactly one of `--value` or all three `--source-*` options must be provided.

Valid expression prefixes: `=vars.`, `=bindings.`, `=js:`, `=metadata.`, `=datafabric.`, `=orchestrator.JobAttachments`, `=response`, `=result`, `=Error`, `=jsonString:`.

Output: `{ File, StageId, TaskId, InputName, Value, [SourceStage, SourceTask, SourceOutput] }`.

---

## uip case tasks

Manage tasks within a stage node.

```bash
# Add a task to a stage (lane 0 by default)
uip case tasks add <file> <stage-id> --type process --display-name "Run KYC" --name "KYC" --folder-path "Shared"
uip case tasks add <file> <stage-id> --type action --display-name "Human Review" --task-title "Review" --priority High
uip case tasks add <file> <stage-id> --type agent --display-name "AI Scoring" --should-run-only-once
uip case tasks add <file> <stage-id> --type wait-for-timer
uip case tasks add <file> <stage-id> --type process --lane 1  # parallel lane

# Add a task and inline-enrich with API bindings (process/agent/rpa/action/api-workflow/case-management)
uip case tasks add <file> <stage-id> --type process --task-type-id <entityKey> --display-name "KYC"

# Add a connector activity or trigger task with full enrichment (requires uip login)
uip case tasks add-connector <file> <stage-id> --type activity --type-id <id> --connection-id <id>
uip case tasks add-connector <file> <stage-id> --type trigger --type-id <id> --connection-id <id>
uip case tasks add-connector <file> <stage-id> --type activity --type-id <id> --connection-id <id> \
  --input-values '{"body":{"comment":"Hello"},"queryParameters":{"issueIdOrKey":"PROJ-1"}}'
uip case tasks add-connector <file> <stage-id> --type trigger --type-id <id> --connection-id <id> \
  --input-values '{"body":{"project":"PROJ"}}' --filter '((fields.status=`Open`))'

# Edit a task
uip case tasks edit <file> <stage-id> <task-id> --display-name "Updated Name"
uip case tasks edit <file> <stage-id> <task-id> --name "NewProcess" --folder-path "Finance"
uip case tasks edit <file> <stage-id> <task-id> --should-run-only-once --is-required

# Get a task
uip case tasks get <file> <stage-id> <task-id>

# Remove a task
uip case tasks remove <file> <stage-id> <task-id>

# Enrich a task with input/output schemas from the API
uip case tasks enrich --type <type> --id <id>
uip case tasks enrich --type process --id <entityKey>
uip case tasks enrich --type agent --id <entityKey> --element-id <elementId>

# Describe a task type's input/output metadata (for binding discovery)
uip case tasks describe --type <type> --id <id>
uip case tasks describe --type process --id <entityKey>
uip case tasks describe --type connector-activity --id <typeId> --connection-id <uuid>
uip case tasks describe --type connector-trigger --id <typeId> --connection-id <uuid>
```

Valid task types:
| Type | Description |
|------|-------------|
| `process` | Run a UiPath RPA process |
| `action` | Human-in-the-loop action task |
| `agent` | AI agent task |
| `api-workflow` | API workflow |
| `rpa` | RPA robot task |
| `external-agent` | External AI agent (with connector) |
| `wait-for-timer` | Suspend until a timer fires |
| `wait-for-connector` | Suspend waiting for a connector event |
| `execute-connector-activity` | Execute a connector action |
| `case-management` | Sub-case process |

Tasks are stored as a 2D array: `tasks[lane][index]`. Use `--lane <n>` to place tasks in parallel execution lanes.

Options for `add`:
| Flag | Description |
|------|-------------|
| `-t, --type <type>` | **(required)** Task type (see table above) |
| `-d, --display-name <name>` | Display name for the task |
| `-n, --name <name>` | Process or workflow name |
| `--folder-path <path>` | Folder path for the process or workflow |
| `--lane <n>` | Parallel lane index (default: `0`) |
| `--task-type-id <id>` | Entity key / action-app ID to auto-enrich with bindings, inputs, and outputs (enrichable types only) |
| `--should-run-only-once` | Whether the task should run only once |
| `--description <text>` | Description of the task |
| `--is-required` | Whether the task is required |
| `--task-title <title>` | Title for the action task (`action` type only) |
| `--priority <level>` | Priority for the action task: `Low`, `Medium`, `High`, `Critical` (`action` type only, default: `Medium`) |

Options for `add-connector`:
| Flag | Description |
|------|-------------|
| `-t, --type <type>` | **(required)** Connector type: `activity` or `trigger` |
| `--type-id <id>` | **(required)** `uiPathActivityTypeId` UUID from the TypeCache |
| `--connection-id <id>` | **(required)** Connection UUID to bind to the task |
| `-d, --display-name <name>` | Override display name for the task |
| `--lane <n>` | Parallel lane index (default: `0`) |
| `--input-values <json>` | JSON object of input values keyed by input name (use `tasks describe` to discover names) |
| `--filter <expression>` | Filter expression for trigger type |

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-d, --display-name <name>` | New display name |
| `-n, --name <name>` | New process or workflow name |
| `--folder-path <path>` | New folder path |
| `--should-run-only-once` | Set should-run-only-once |
| `--description <text>` | New description |
| `--is-required` | Set is-required |

Options for `enrich`:
| Flag | Description |
|------|-------------|
| `--type <type>` | **(required)** Enrichable task type |
| `--id <id>` | **(required)** Unique ID of the task (entityKey or action-app id) |
| `--element-id <elementId>` | Element ID for variable binding |

Options for `describe`:
| Flag | Description |
|------|-------------|
| `--type <type>` | **(required)** Task type: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `connector-activity`, `connector-trigger` |
| `--id <id>` | **(required)** Unique ID of the task (entityKey or action-app id) |
| `--connection-id <id>` | Connection UUID (required for `connector-activity` and `connector-trigger` types) |

Enrichable types: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`.

---

## uip case edges

Manage edges (connections) between stage nodes.

```bash
# Add an edge (type inferred: TriggerEdge if source is Trigger, Edge otherwise)
uip case edges add <file> --source <trigger-id> --target <stage-id>
uip case edges add <file> --source <stage-id> --target <next-stage-id> --label "Approved"
uip case edges add <file> --source <stage-id> --target <exception-stage-id> \
  --label "Rejected" --source-handle bottom --target-handle top
uip case edges add <file> --source <stage-id> --target <next-stage-id> --z-index 10

# Edit an edge
uip case edges edit <file> <edge-id> --label "New Label"
uip case edges edit <file> <edge-id> --z-index 10
uip case edges edit <file> <edge-id> --source-handle right --target-handle left

# Get an edge
uip case edges get <file> <edge-id>

# Remove an edge
uip case edges remove <file> <edge-id>
```

Handle directions: `right` (default source), `left` (default target), `top`, `bottom`.

Handle values are formatted automatically as `<nodeId>____source____<direction>`.

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-l, --label <label>` | New display label |
| `--source-handle <direction>` | New source handle direction |
| `--target-handle <direction>` | New target handle direction |
| `--z-index <number>` | New z-index for rendering order |

---

## uip case case-exit-conditions

Manage exit conditions on a case within a case management definition JSON file.

```bash
# Add an exit condition
uip case case-exit-conditions add <file>
uip case case-exit-conditions add case.json --display-name "Approved"
uip case case-exit-conditions add case.json --display-name "Closed" --marks-case-complete true
uip case case-exit-conditions add case.json --rule-type selected-stage-completed --selected-stage-id <id>

# Edit an exit condition
uip case case-exit-conditions edit <file> <condition-id> --display-name "New Name"
uip case case-exit-conditions edit case.json <condition-id> --marks-case-complete false
uip case case-exit-conditions edit case.json <condition-id> --rule-type wait-for-connector --condition-expression "expr"

# Get an exit condition
uip case case-exit-conditions get <file> <condition-id>

# Remove an exit condition
uip case case-exit-conditions remove <file> <condition-id>
```

Options for `add`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `-d, --display-name <name>` | Display name for the condition |
| `--marks-case-complete <bool>` | Whether this condition marks the case complete (`true` or `false`) |
| `--rule-type <type>` | Initial rule type: `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector` |
| `--condition-expression <expr>` | Condition expression for the initial rule |
| `--selected-stage-id <id>` | Stage ID for `selected-stage-*` initial rules |

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-d, --display-name <name>` | New display name for the condition |
| `--marks-case-complete <bool>` | Set marks-case-complete (`true` or `false`) |
| `--rule-type <type>` | Append a new rule with this type (same valid types as `add`) |
| `--condition-expression <expr>` | Condition expression for the new rule |
| `--selected-stage-id <id>` | Stage ID for `selected-stage-*` rules |

Output on `add`: `{ File, ConditionId, DisplayName, MarksCaseComplete, Rules }` — save `ConditionId` for future edits.

---

## uip case task-entry-conditions

Manage entry conditions on a task within a case management definition JSON file.

```bash
# Add an entry condition to a task
uip case task-entry-conditions add <file> <stage-id> <task-id>
uip case task-entry-conditions add case.json <stage-id> <task-id> --display-name "Pre-check"
uip case task-entry-conditions add case.json <stage-id> <task-id> --rule-type current-stage-entered
uip case task-entry-conditions add case.json <stage-id> <task-id> --rule-type selected-tasks-completed --selected-tasks-ids "<id1>,<id2>"

# Edit an entry condition
uip case task-entry-conditions edit <file> <stage-id> <task-id> <condition-id> --display-name "Updated"
uip case task-entry-conditions edit case.json <stage-id> <task-id> <condition-id> --rule-type adhoc --condition-expression "expr"

# Get an entry condition
uip case task-entry-conditions get <file> <stage-id> <task-id> <condition-id>

# Remove an entry condition
uip case task-entry-conditions remove <file> <stage-id> <task-id> <condition-id>
```

Options for `add`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `<stage-id>` | **(required)** ID of the stage node |
| `<task-id>` | **(required)** ID of the task |
| `-d, --display-name <name>` | Display name for the condition |
| `--rule-type <type>` | Initial rule type: `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, `adhoc` |
| `--condition-expression <expr>` | Condition expression for the initial rule |
| `--selected-tasks-ids <ids>` | Comma-separated task IDs for `selected-tasks-completed` initial rule |

Options for `edit` (at least one required):
| Flag | Description |
|------|-------------|
| `-d, --display-name <name>` | New display name for the condition |
| `--rule-type <type>` | Append a new rule with this type (same valid types as `add`) |
| `--condition-expression <expr>` | Condition expression for the new rule |
| `--selected-tasks-ids <ids>` | Comma-separated task IDs for `selected-tasks-completed` rules |

Output on `add`: `{ File, StageId, TaskId, ConditionId, DisplayName, Rules }` — save `ConditionId` for future edits.

---

## uip case registry

Manage the local resource cache. Requires `uip login` for tenant-specific resources.

```bash
# Refresh cache from all resource types
uip case registry pull
uip case registry pull --force             # ignore 30-min TTL and force refresh
uip case registry pull --solutionId <id>  # include a specific solution's resources

# List all cached resources
uip case registry list --output json

# Search for resources by keyword and/or field filters
uip case registry search <keyword>
uip case registry search <keyword> --type process
uip case registry search --filter "name:contains=Apple,category=Pipelines"
uip case registry search <keyword> --filter "name:contains=Foo" --type agent
```

Resource types: `agent`, `process`, `api`, `processOrchestration`, `caseManagement`, `typecache`, `action-apps`, `solution`.

Options for `search`:
| Flag | Description |
|------|-------------|
| `[keyword]` | Optional keyword to search by |
| `-t, --type <type>` | Limit search to a specific resource type |
| `-f, --filter <filter>` | Field filters, e.g. `name:contains=Apple,category=Pipelines` |

Filter format: `field=value` or `field:operator=value`. Supported fields: `name`, `description`, `category`, `tags`. Supported operators: `equals`, `contains`, `in`, `startsWith`, `endsWith`. At least one of keyword or `--filter` is required.

Cache lives at `~/.uipcli/case-resources/` and expires after 30 minutes.

---

## uip case process

Manage and run Case processes. **Requires `uip login`.**

```bash
# List available Case processes
uip case process list
uip case process list --folder-key <guid>
uip case process list --filter "Name eq 'MyCase'"

# Get process schema and entry point details
uip case process get <process-key> <feed-id>
uip case process get <process-key> <feed-id> --folder-key <guid>

# Run a Case process
uip case process run <process-key> <folder-key>
uip case process run <process-key> <folder-key> --inputs '{"key":"value"}'
uip case process run <process-key> <folder-key> --inputs @inputs.json --validate
```

Options for `list`:
| Flag | Description |
|------|-------------|
| `-t, --tenant <name>` | Tenant name (defaults to authenticated tenant) |
| `-f, --folder-key <key>` | Filter by folder key (GUID) |
| `--filter <odata>` | Additional OData filter expression |
| `--folder-id <id>` | Folder ID (`OrganizationUnitId`, required for client credentials auth) |
| `--login-validity <minutes>` | Minimum minutes before token expiration triggers refresh (default: `10`) |

Options for `get`:
| Flag | Description |
|------|-------------|
| `<process-key>` | **(required)** Process key (from `list`) |
| `<feed-id>` | **(required)** Feed ID (from `list`) |
| `-t, --tenant <name>` | Tenant name |
| `-f, --folder-key <key>` | Folder key (GUID) |
| `--folder-id <id>` | Folder ID |
| `--login-validity <minutes>` | Min minutes before token refresh |

Options for `run`:
| Flag | Description |
|------|-------------|
| `<process-key>` | **(required)** Process key |
| `<folder-key>` | **(required)** Folder key (GUID) |
| `-i, --inputs <json>` | Input parameters as JSON string or `@file.json` (also reads from stdin) |
| `-t, --tenant <name>` | Tenant name |
| `--release-key <key>` | Release key (GUID, from `list`) |
| `--folder-id <id>` | Folder ID |
| `--feed-id <id>` | Feed ID for package lookup |
| `--robot-ids <ids>` | Comma-separated robot IDs |
| `--validate` | Validate inputs against process schema before running |
| `--login-validity <minutes>` | Min minutes before token refresh |

Output on `run`: `{ jobKey, state, traceId }` — use `jobKey` with `uip case job traces`.

---

## uip case job

Monitor Case jobs. **Requires `uip login`.**

```bash
# Stream traces for a running job
uip case job traces <job-key>
uip case job traces <job-key> --pretty
uip case job traces <job-key> --poll-interval 5000

# Get job status
uip case job status <job-key>
uip case job status <job-key> --detailed
```

Options for `traces`:
| Flag | Description |
|------|-------------|
| `<job-key>` | **(required)** Job key (GUID from `process run`) |
| `-t, --tenant <name>` | Tenant name |
| `--poll-interval <ms>` | Polling interval in milliseconds (default: `2000`) |
| `--traces-service <name>` | Traces service name (default: `llmopstenant_`) |
| `--pretty` | Human-readable trace output instead of raw JSON |
| `--login-validity <minutes>` | Min minutes before token refresh |

Options for `status`:
| Flag | Description |
|------|-------------|
| `<job-key>` | **(required)** Job key (GUID from `process run`) |
| `-t, --tenant <name>` | Tenant name |
| `--folder-id <id>` | Folder ID |
| `--detailed` | Show full response with all fields |
| `--login-validity <minutes>` | Min minutes before token refresh |

---

## uip case instance

Manage live Case process instances. **Requires `uip login`.**

```bash
# List instances
uip case instance list
uip case instance list --limit 20 --offset 0
uip case instance list --process-key <key> --folder-key <key>
uip case instance list --package-id <id> --error-code <code>

# Get a specific instance
uip case instance get <instance-id>
uip case instance get <instance-id> --folder-key <key>

# Lifecycle operations (all accept --folder-key and --comment)
uip case instance pause <instance-id>
uip case instance resume <instance-id>
uip case instance cancel <instance-id>
uip case instance retry <instance-id>

# Variables
uip case instance variables <instance-id>
uip case instance variables <instance-id> --parent-element-id <id>

# Incidents for a specific instance
uip case instance incidents <instance-id>

# Get the Case definition (JSON) for a process instance
uip case instance asset <instance-id>

# Migration: migrate instance to a different package version
uip case instance migrate <instance-id> <new-version>

# Go-to: move execution cursor from one element to another
uip case instance goto <instance-id> '[{"sourceElementId":"A","targetElementId":"B"}]'
uip case instance cursors <instance-id>
uip case instance element-executions <instance-id>
```

---

## uip case processes

View Case process summaries. **Requires `uip login`.**

```bash
# List all Case process summaries
uip case processes list

# Get incidents for a specific process
uip case processes incidents <process-key>
uip case processes incidents <process-key> --folder-key <key>
```

---

## uip case incidents

View Case incident summaries across all processes. **Requires `uip login`.**

```bash
uip case incidents list
```

---

## uip case sla

Manage SLA settings and escalation rules for case definitions (root level or per stage).

```bash
# Set SLA on root or a stage
uip case sla set <file> --count <n> --unit <u>
uip case sla set case.json --count 5 --unit d
uip case sla set case.json --count 2 --unit w --stage-id <stage-id>

# Get SLA from root or a stage
uip case sla get <file>
uip case sla get case.json --stage-id <stage-id>

# Remove SLA from root or a stage
uip case sla remove <file>
uip case sla remove case.json --stage-id <stage-id>

# Add an escalation rule to an SLA
uip case sla escalation add <file> --trigger-type at-risk --at-risk-percentage 80 \
  --recipient-scope User --recipient-target <target> --recipient-value <value>
uip case sla escalation add case.json --trigger-type sla-breached \
  --recipient-scope UserGroup --recipient-target <target> --recipient-value <value> \
  --display-name "Notify Manager" --stage-id <stage-id>

# List escalation rules on an SLA
uip case sla escalation list <file>
uip case sla escalation list case.json --stage-id <stage-id>

# Remove an escalation rule by ID
uip case sla escalation remove <file> <escalation-id>
uip case sla escalation remove case.json <escalation-id> --stage-id <stage-id>

# Add a conditional SLA rule (expression-based, root level only)
uip case sla rules add <file> --expression "=js:someCondition" --count 3 --unit d

# List all conditional SLA rules at root level
uip case sla rules list <file>

# Remove a conditional SLA rule by index (0-based)
uip case sla rules remove <file> <index>
```

SLA units: `h` (hours), `d` (days), `w` (weeks), `m` (months).

Options for `sla set`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--count <count>` | **(required)** SLA duration count (positive integer) |
| `--unit <unit>` | **(required)** SLA duration unit: `h`, `d`, `w`, `m` |
| `--stage-id <id>` | Stage ID to set the SLA on (omit for root-level) |

Options for `sla get` / `sla remove`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--stage-id <id>` | Stage ID (omit for root-level) |

Options for `sla escalation add`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--trigger-type <type>` | **(required)** `at-risk` or `sla-breached` |
| `--recipient-scope <scope>` | **(required)** `User` or `UserGroup` |
| `--recipient-target <target>` | **(required)** Recipient target identifier |
| `--recipient-value <value>` | **(required)** Recipient display value |
| `--display-name <name>` | Display name for the escalation rule |
| `--at-risk-percentage <n>` | At-risk threshold (required when `trigger-type` is `at-risk`) |
| `--stage-id <id>` | Stage ID (omit for root-level) |

Options for `sla rules add`:
| Flag | Description |
|------|-------------|
| `<file>` | **(required)** Path to the case management JSON file |
| `--expression <expr>` | **(required)** Condition expression for the SLA rule |
| `--count <count>` | **(required)** SLA duration count (positive integer) |
| `--unit <unit>` | **(required)** SLA duration unit: `h`, `d`, `w`, `m` |

Condition rules are prepended before the default rule (`=js:true`) so they are evaluated first. Output codes: `SlaSet`, `SlaFound`, `SlaRemoved`, `EscalationRuleAdded`, `EscalationRulesList`, `EscalationRuleRemoved`, `SlaRuleAdded`, `SlaRulesList`, `SlaRuleRemoved`.

---

## Global options (all commands)

| Option | Description |
|--------|-------------|
| `--output json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |