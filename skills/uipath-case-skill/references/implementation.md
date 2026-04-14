# Implementation: tasks.md → caseplan.json

Build (or edit) a `caseplan.json` from a `tasks.md` planning document by writing JSON directly. This phase produces a complete, validated case definition ready for `uip case validate` and (with consent) `uip case debug`.

---

## When to Load This Reference

- Create or edit `caseplan.json` (stages, tasks, edges, entry/exit conditions, SLA, bindings, variables)
- Convert **tasks.md** → caseplan.json — load [references/implementation.md](references/implementation.md)
- Discover resources via registry
- Validate, debug, or deploy a case definition

---

## Quick Start — New Case from tasks.md

### Step 0 — Resolve `uip` and check login

See [cli-commands.md → Binary Resolution](cli-commands.md#binary-resolution).

### Step 1 — Check login status

See [Authentication](cli-commands.md#authentication)

### Step 2 — Create a new Case project and add a case definition file

**The case file must be inside a proper solution/project structure**

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

> **Naming convention:** Use the same name for solution and project unless user specifies, always use `caseplan.json` as the file name.

### Step 3 — Refresh the registry

Skip this step if `taskTypeId` in `tasks.md` are all resolved, unless:
- User need to validate the taskTypeId is valid in the registry
- Some task references a connector or app whose `resourceKey`/`folderPath` is missing from tasks.md

```bash
uip case registry pull
uip case registry search "<task display name>" --output json    # capture resourceKey + folderPath
```

### Step 4 — Read the tasks.md

Parse the `tasks.md` end-to-end before writing JSON. The planning format groups work by concern and by numbered task (`T01`, `T02`, …):

| Planning group | What to build |
|---|---|
| `Create case file "<name>"` | Root node — name, caseIdentifier, caseIdentifierType, description |
| `Configure <type> trigger "<name>"` | Trigger node (manual is implicit; timer / connector explicit) |
| `Create stage "<name>"` / `Create exception stage "<name>"` | Stage / ExceptionStage node — label, isRequired, description |
| `Add edge "<A>" → "<B>"` | TriggerEdge or Edge depending on source type |
| `Add <type> task "<name>" to "<stage>"` | Task in that stage — declare bindings, write task |
| `Add stage entry condition for "<stage>"` | `stage.data.entryConditions[]` |
| `Add stage exit condition for "<stage>"` | `stage.data.exitConditions[]` |
| `Add task entry condition for "<task>" in "<stage>"` | `task.entryConditions[]` |
| `Add case exit condition` | `root.caseExitConditions[]` |
| `Set default SLA for <scope> to N <unit>` | `slaRules[].count` / `unit` on root or stage |
| `Add conditional SLA rule for <scope>` | Additional `slaRules[]` entry with `expression` |
| `Add escalation rule for <scope>` | `slaRules[].escalationRule[]` entry |

Capture every name → ID assignment as you build (StageId, TaskId, ConditionId, …) so later sections can reference them.

### Step 5 — Build caseplan.json in one pass

First load [plugins/skeleton/case](plugins/skeleton/case.md) for the case JSON skeleton, then load other plugins on demand. See [SKILL.md → Plugin Navigation](../SKILL.md#reference-navigation) for the full plugin catalog.

**Build order (do not interleave):**

1. **Root** — name, identifier, identifierType, description, empty `bindings`/`variables`/`slaRules`/`caseExitConditions`. See [plugins/skeleton/case](plugins/skeleton/case.md).
2. **Trigger nodes** — manual is created by default. Add timer or connector triggers if tasks.md declares them. See [plugins/triggers/](plugins/triggers/).
3. **Stage nodes** (and ExceptionStages) — empty tasks/conditions arrays. See [plugins/skeleton/stage](plugins/skeleton/stage.md).
4. **Edges** — Trigger → first stage (TriggerEdge), then Stage → Stage (Edge). Vertical branches for ExceptionStages. See [plugins/skeleton/edge](plugins/skeleton/edge.md).
5. **Tasks per stage** — for each task in tasks.md, look up the right plugin, declare its bindings at the root, and write the task into the stage's `tasks[]`. See [Plugin dispatch](#plugin-dispatch) below.
6. **Conditions** — fill `entryConditions` / `exitConditions` on each stage and task; fill `caseExitConditions` on root. See [Plugin dispatch](#plugin-dispatch) below.
7. **Variable bindings** — wire literal values and cross-task data flow into task inputs. See [plugins/variables/bindings](plugins/variables/bindings.md) and [plugins/variables/global-vars](plugins/variables/global-vars.md).
8. **SLA + escalation** — set `slaRules` on root and per-stage; add escalation entries. See [plugins/sla](plugins/sla/sla.md).

> **For connector tasks** (`execute-connector-activity`, `wait-for-connector`, connector triggers, `external-agent`): write a placeholder task and proceed. These cannot be fully hand-written — Step 5 enriches them via CLI.

### Step 6 — Enrich connector tasks (CLI)

Connector tasks and event triggers require additional metadata that only the CLI can produce. Run these *after* the rest of the JSON is in place:
**Connector tasks need CLI enrichment** — `external-agent`, `wait-for-connector`, `execute-connector-activity`, event triggers require `tasks describe`/`add-connector`/`triggers add-event`.

```bash
uip case tasks add-connector <file> <stage-id> --type activity \
  --type-id <typeId> --connection-id <connectionId> --output json

uip case tasks add-connector <file> <stage-id> --type trigger \
  --type-id <typeId> --connection-id <connectionId> --output json

uip case triggers add-event <file> \
  --type-id <typeId> --connection-id <connectionId> --output json
```

`<typeId>` is the `uiPathActivityTypeId` from tasks.md. `<connectionId>` comes from `uip case registry get-connection`. See [plugins/tasks/execute-connector-activity](plugins/tasks/execute-connector-activity.md), [plugins/tasks/wait-for-connector](plugins/tasks/wait-for-connector.md), [plugins/tasks/external-agent](plugins/tasks/external-agent.md).

### Step 7 — Validate

Run validation before asking to debug. This catches structural errors locally without uploading anything.

```bash
uip case validate <path/to/caseplan.json> --output json
```

On success:`Result: Success` and `Status: Valid` → proceed to Step 8.
On failure, the output lists each `[error]` / `[warning]` with its path and message. Fix the reported issues and re-run `validate` until it passes before proceeding or failed for 5 attempts.

### Step 8 — Ask about debug

Once validation passes, tell the user and ask:

> "Case file built and validated. Do you want to debug it? Debug uploads to Studio Web and runs the case in Orchestrator with real side effects — emails, API calls, database writes."

Use `AskUserQuestion` with options "Yes" / "No". Do **not** run debug without explicit consent (Critical Rule #9 in SKILL.md).

### Step 9 — Debug (only on consent)

```bash
uip case debug --project-dir "<directory>/<solutionName>/<projectName>" --output json
```

The argument is the project directory containing `project.uiproj`. Requires `uip login`. See [cli-commands.md → Debug](cli-commands.md#debug-phase-5--requires-explicit-user-consent) for flags.

---

## Common Edits — Existing caseplan.json

Use these recipes for targeted changes without rebuilding the whole file. Run `uip case validate` once after each batch of edits.

### Rename a stage or task

Edit the `data.label` (stage) or `displayName` (task) field. **Do not change the `id`** — every reference (edges, conditions, elementId) depends on it.

### Add a task to an existing stage

1. Generate a new task ID (`t` + 8 chars) and `elementId` (`<stageId>-<taskId>`).
2. Look up the resource via `uip case registry search "<name>" --output json` to get `resourceKey`, `name`, `folderPath`.
3. Declare the binding pair at `root.data.uipath.bindings`. See [plugins/variables/bindings](plugins/variables/bindings.md).
4. Build the task body using the task-type plugin's `impl.md`.
5. Append the task as its own lane entry in `stage.data.tasks[]` (one task per lane — never group).
6. If outputs are declared, add the global variable to `root.data.uipath.variables.inputOutputs`.

### Remove a task from a stage

1. Delete the task entry from `stage.data.tasks[]`.
2. Delete its bindings from `root.data.uipath.bindings` (only if no other task uses the same `id`).
3. Delete its global outputs from `root.data.uipath.variables.inputOutputs`.
4. Scan all conditions for `selectedTasksIds` references and remove the task ID from those arrays.
5. If the array becomes empty, the condition is no longer satisfiable — replace with `required-tasks-completed` or remove the condition.

### Insert a stage between two existing stages

1. Add the new stage node (see [plugins/skeleton/stage](plugins/skeleton/stage.md)). Set `position.x` halfway between the neighboring stages.
2. Find the existing edge from `<source>` → `<originalTarget>` and update its `target` + `targetHandle` to the new stage.
3. Add a new edge from the new stage to `<originalTarget>` with `data: {}` and `type: "case-management:Edge"`.
4. If conditions reference the old transition (e.g., `selected-stage-completed` with `selectedStageId: <originalTarget>`), update the relevant `selectedStageId` to the new stage.

### Rewire an edge

Edit `source` / `target` / `sourceHandle` / `targetHandle` directly. The handle format is `<nodeId>____source____<direction>` (4 underscores each side). See [plugins/skeleton/edge](plugins/skeleton/edge.md).

### Add a stage entry/exit condition to an existing stage

Append to `stage.data.entryConditions[]` or `stage.data.exitConditions[]` using the appropriate plugin: [plugins/conditions/stage-entry](plugins/conditions/stage-entry.md), [plugins/conditions/stage-exit](plugins/conditions/stage-exit.md). Generate fresh `Condition_` and `Rule_` IDs.

### Add a task entry condition

Append to `task.entryConditions[]`. Default rule for parallel-on-stage-entry is `current-stage-entered`. For sequential ordering inside a stage, use `selected-tasks-completed` with the upstream task's ID. See [plugins/conditions/task-entry](plugins/conditions/task-entry.md).

### Add or change a case exit condition

Append to `root.caseExitConditions[]`. Standard pattern is `required-stages-completed` with `marksCaseComplete: true`. **Never use `required-tasks-completed` here** — that rule is stage-scoped only. See [plugins/conditions/case-exit](plugins/conditions/case-exit.md).

### Add an SLA or escalation to root or a stage

Add to `root.data.slaRules[]` or `stage.data.slaRules[]`. Conditional rules go *before* the default `=js:true` rule (evaluation is ordered). Each rule has its own `escalationRule[]` array. See [plugins/sla](plugins/sla/sla.md).

### Add a workflow-level variable

Add to `root.data.uipath.variables.inputs` (input from caller), `outputs` (returned to caller), or `inputOutputs` (case-internal). Reference with `=vars.<id>` from task inputs or condition expressions. See [plugins/variables/global-vars](plugins/variables/global-vars.md).

### Add a multi-trigger entry point

A default manual trigger is created automatically. To add another entry point (typically a timer or connector trigger):

1. Add a new trigger node with a unique ID. Stack vertically — first trigger at `y: 0`, additional triggers at `y: 150`, `y: 300`, etc.
2. Add a `TriggerEdge` from the new trigger to the stage that should activate first when it fires.
3. For timer triggers, see [plugins/triggers/timer](plugins/triggers/timer.md). For connector triggers, see [plugins/triggers/connector-trigger](plugins/triggers/connector-trigger.md) (requires Step 5 enrichment).

---

## Expression Forms Quick Reference

Every task input or expression in the case file uses one of these forms. This is the authoritative cheat sheet — for worked examples and wiring procedures, see [plugins/variables/bindings](plugins/variables/bindings.md) and [plugins/variables/global-vars](plugins/variables/global-vars.md).

| Form | Purpose | Where used |
|---|---|---|
| `=vars.<varId>` | Read a global variable | task `input.value` |
| `=bindings.<bindingId>` | Reference a root binding (name, folderPath) | task `data.name`, `data.folderPath` |
| `=js:<expression>` | JavaScript expression (`vars.x` inside, no `$`) | `conditionExpression`, SLA `expression` |
| `=metadata.<field>` | Case-instance metadata (InstanceId, FolderKey, ProcessKey, etc.) | task inputs, conditions |
| `=datafabric.<entity.field>` | Data Fabric entity field | task `input.value`, output `target` |
| `=orchestrator.JobAttachments` | Job-attachment storage handle | task output `target` for files |
| `=response.<field>` | Task's own response object field | task output `source` only |
| `=string.Format("<fmt>", arg, ...)` | C#-style string template (`{0}`, `{1}`) | `taskTitle`, `caseAppConfig.caseSummary` |
| `<plain text>` | Literal value | task `input.value` for static strings |

**`=` vs `=js:` rule:**
- Just reading a variable → `=vars.x`
- Any expression / comparison → `=js:vars.x === 'foo'`
- Inside `conditionExpression` → always `=js:`
- String template → `=string.Format(...)`

> Variable accessor is `vars.x` (no `$`). The `$vars.x` syntax does not exist.

---

## Plugin Dispatch

Load plugins on demand from [SKILL.md → Plugin Navigation](../SKILL.md#reference-navigation). Key dispatch rules:

**Tasks:** For `process`, `agent`, `rpa`, `api-workflow`, `case-management` → load [plugins/tasks/standard-io](plugins/tasks/standard-io.md). For other types, load the type-specific plugin.

**Conditions:** All four scopes share the `rules: [[{ rule, id, ... }]]` shape (outer array = OR groups, inner array = AND group). Load the scope-specific plugin for JSON patterns and rule-type reference.

**SLA:** Rules evaluate top-down — first matching `expression` wins. Fallback is always `"=js:true"`. Load [plugins/sla](plugins/sla/sla.md) for patterns.

---

## Runtime Operations

After deployment, manage live instances via CLI. See [cli-commands.md → Runtime Management](cli-commands.md#runtime-management) for the full command set.

---

## Completion Output

When you finish building or editing, report:

1. **File path** of the caseplan.json
2. **What was built** — number of stages, tasks per stage, edges, conditions, SLA rules
3. **Validation status** — `Status: Valid` or the remaining errors
4. **Connector enrichment** — list any connector tasks / event triggers that ran through Step 5 (or still need it)
5. **Missing connections** — connectors with no available connection in Integration Service
6. **Next step** — ask if the user wants to debug (do not run automatically)
