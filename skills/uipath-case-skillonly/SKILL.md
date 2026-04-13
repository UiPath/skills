---
name: uipath-case-skillonly
description: "[PREVIEW] Case Management caseplan.json authoring — writes JSON directly (no CLI for local structure). Registry/enrich/debug→CLI. For .xaml→uipath-rpa. For .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management — Skill-Driven Authoring

Builds and edits Case Management definition files (`caseplan.json`) by writing JSON directly. Only a small set of CLI commands remain for operations that genuinely require external APIs.

## When to Use This Skill

- User wants to **create or edit a caseplan.json** — stages, tasks, edges, conditions, SLA
- User asks about the **case management JSON schema** — nodes, edges, tasks, rules, bindings
- User wants to **discover available resources** via the registry before building
- User wants to **validate, debug, or deploy** a case definition
- User wants to **manage runtime instances** — list, pause, resume, cancel

## Critical Rules

1. **Write JSON directly** — do not call `uip case cases/stages/tasks/edges/sla/conditions/var` commands. The agent writes caseplan.json using the schema in [references/case-schema-reference.md](references/case-schema-reference.md).
2. **CLI is reserved for**: `registry pull/search/get-connector/get-connection`, `tasks describe`, `triggers add-event`, `validate`, `debug`, `process/*`, `job/*`, `instance/*`.
3. **Version is always `"v16"`** — use this literal in `root.version`.
4. **Generate IDs using the prefixedId convention** — see [ID Generation](#id-generation) below.
5. **Bindings live at root level** — every process/agent/rpa/action/api-workflow/case-management task references its `name` and `folderPath` via `=bindings.<id>` pointing to entries in `root.data.uipath.bindings`.
6. **Connector tasks need CLI enrichment** — `external-agent`, `wait-for-connector`, `execute-connector-activity`, and event triggers cannot be fully built without calling `uip case tasks describe` or `triggers add-event`.
7. **`shouldRunOnlyOnce`** is the current task field (`shouldRunOnReEntry` is deprecated).
8. **Validate before debug** — run `uip case validate --file <path>` before `debug`.
9. **`debug` requires explicit user consent** — it executes the case in Orchestrator with real side effects (emails, API calls, database writes). Always ask before running.
10. **Never edit `*.bpmn` files** — they are auto-generated from caseplan.json.

## ID Generation

All IDs use alphanumeric random characters (`A-Za-z0-9`). Generate them yourself using this format:

| Element | Format | Example |
|---|---|---|
| Root | `"root"` (fixed) | `root` |
| Stage / ExceptionStage | `Stage_` + 6 chars | `Stage_zlZulP` |
| Trigger | `trigger_` + 6 chars | `trigger_aB3cD4` |
| Task | `t` + **8** chars | `t9nayawCu` |
| Edge | `edge_` + 6 chars | `edge_9bzKc2` |
| Condition (any) | `Condition_` + 6 chars | `Condition_SqgWT0` |
| Rule (any) | `Rule_` + 6 chars | `Rule_iQF8aX` |
| Escalation | `esc_` + 6 chars | `esc_FIWwCn` |
| Binding | `b` + **8** chars | `bCiT7IgAE` |
| elementId | `<stageId>-<taskId>` | `Stage_f95rff-t9nayawCu` |

## Workflow

### Phase 1 — Discovery (CLI)

```bash
uip login status --output json           # check auth
uip case registry pull                   # refresh cache
uip case registry search "<keyword>"     # find processes, agents, apps by name
```

Capture `resourceKey` values (e.g., `"Shared/MyFolder.MyProcess"`) — needed for bindings.

### Phase 2 — Plan

Before writing any JSON, produce a plan in chat covering:
- Case name, identifier, `caseIdentifierType`
- Stage names, order, whether sequential or parallel lanes per stage
- Task types per stage and their resource keys
- Entry/exit conditions for each stage and the case
- SLA requirements and escalation recipients
- Global variables (inputs/outputs passed in/out of the case)

Get user confirmation before building.

### Phase 3 — Build (write JSON directly)

Create or edit `caseplan.json` using [references/case-schema-reference.md](references/case-schema-reference.md).

Build order:
1. Root node (name, identifier, `caseExitConditions`, bindings for all tasks, global variables, SLA rules)
2. Trigger node
3. Stage nodes (each with tasks, `entryConditions`, `exitConditions`, `slaRules`)
4. Edges (trigger→stage, stage→stage)

> For connector tasks (`external-agent`, `wait-for-connector`, `execute-connector-activity`): add a placeholder task and proceed to Phase 4 to enrich it.

### Phase 4 — Enrich (CLI — connector tasks only)

Only needed when the case has connector-based tasks or event triggers:

```bash
# Get full schema for a connector task
uip case tasks describe --type <taskType> --id <connectorId> --output json

# Add an enriched event trigger (replaces manual trigger node)
uip case triggers add-event \
  --file <path/to/caseplan.json> \
  --type-id <connectorTypeId> \
  --connection-id <connectionId> \
  --output json

# Look up available connections
uip case registry get-connection --key <connectorKey> --output json
```

### Phase 5 — Validate and Deploy

```bash
# Local schema validation (no auth required)
uip case validate --file <path/to/caseplan.json> --output json

# Cloud debug (REQUIRES explicit user consent)
uip case debug --project-dir <projectDir> --output json
```

## Reference Navigation

Always start with the schema reference for structural skeleton and ID conventions, then load feature plugins on demand.

| Reference | Contents |
|---|---|
| [case-schema-reference.md](references/case-schema-reference.md) | Structural skeleton: top-level JSON, ID conventions, root/node/edge fields, plugin navigation map |
| [commands-reference.md](references/commands-reference.md) | CLI commands: registry, enrichment, validate, debug, runtime management |

### Plugins — Load On Demand

**Tasks**

| Plugin | Covers |
|---|---|
| [plugins/tasks/standard-io](references/plugins/tasks/standard-io/planning.md) | process, agent, rpa, api-workflow, case-management |
| [plugins/tasks/action](references/plugins/tasks/action/planning.md) | Human-in-the-loop action tasks |
| [plugins/tasks/timer](references/plugins/tasks/timer/planning.md) | wait-for-timer — timeDuration, timeDate, timeCycle |
| [plugins/tasks/connector-activity](references/plugins/tasks/connector-activity/planning.md) | wait-for-connector, execute-connector-activity, external-agent (CLI enrichment required) |

**Triggers**

| Plugin | Covers |
|---|---|
| [plugins/triggers/manual](references/plugins/triggers/manual/impl.md) | Manual case trigger (default) |
| [plugins/triggers/timer](references/plugins/triggers/timer/planning.md) | Scheduled timer trigger |
| [plugins/triggers/connector-trigger](references/plugins/triggers/connector-trigger/planning.md) | Connector event trigger (CLI enrichment required) |

**Stage Types**

| Plugin | Covers |
|---|---|
| [plugins/stage-types/exception-stage](references/plugins/stage-types/exception-stage/planning.md) | ExceptionStage — error handlers, return-to-origin, re-entry behaviour |

**Conditions**

| Plugin | Covers |
|---|---|
| [plugins/conditions/stage-entry](references/plugins/conditions/stage-entry/planning.md) | When a stage becomes active — all rule types |
| [plugins/conditions/stage-exit](references/plugins/conditions/stage-exit/planning.md) | When a stage completes — exit-only, wait-for-user, return-to-origin |
| [plugins/conditions/task-entry](references/plugins/conditions/task-entry/planning.md) | When a task within a stage triggers |
| [plugins/conditions/case-exit](references/plugins/conditions/case-exit/impl.md) | When the entire case ends |

**SLA**

| Plugin | Covers |
|---|---|
| [plugins/sla/setup](references/plugins/sla/setup/planning.md) | Deadlines, at-risk/sla-breached escalation, conditional rules |

**Variables**

| Plugin | Covers |
|---|---|
| [plugins/variables/bindings](references/plugins/variables/bindings/impl.md) | Root binding declarations, =bindings. references |
| [plugins/variables/global-vars](references/plugins/variables/global-vars/planning.md) | inputs/outputs/inputOutputs, =vars. references |

## Anti-patterns

- **Do not call `uip case stages add`** or any other local-JSON CLI command — the agent writes JSON directly.
- **Do not hand-write connector task schemas** — always use `tasks describe` for connector enrichment.
- **Do not reuse IDs** — every element needs a unique ID; generate fresh ones.
- **Do not omit `elementId` on tasks** — it must be `<stageId>-<taskId>` and is used for output variable binding.
- **Do not put `required-tasks-completed` on case exit conditions** — use `required-stages-completed` there; use `required-tasks-completed` only on stage exit conditions.
- **Do not omit `data: {}` for edge nodes** — TriggerEdge and Edge both need `"data": {}`.
