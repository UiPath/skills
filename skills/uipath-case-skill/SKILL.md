---
name: uipath-case-skill
description: "[PREVIEW] UiPath Case Management projects (caseplan.json files). tasks.md→caseplan.json(JSON-direct). Registry/enrich/validate/debug→CLI. For .xaml→uipath-rpa. For .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

Write `caseplan.json` as direct JSON via [references/implementation.md](references/implementation.md). CLI is only for registry, connector enrichment, validate, debug, and instance management.

## Critical Rules

1. **Write JSON directly** — never use `uip case * add`. Only use CLI listed in [references/cli-commands.md](references/cli-commands.md).
2. **Bindings live at root level** — tasks reference `name`/`folderPath` via `=bindings.<id>` → `root.data.uipath.bindings`.
3. **One task per lane** — parallelism via entry conditions, not lane grouping. See [plugins/skeleton/task](references/plugins/skeleton/task.md).

## Quick Start

**Create from tasks.md** — run [implementation.md](references/implementation.md) directly.

**Edit existing caseplan.json** — see [Common Edits](references/implementation.md#common-edits--existing-caseplanjson), then `uip case validate` after edits.

## Reference Navigation

- [references/cli-commands.md](references/cli-commands.md) — all related CLI subcommands, binary resolution, auth
- [references/implementation.md](references/implementation.md) — tasks.md → caseplan.json (Quick Start, Common Edits, bindings, runtime ops)

### Plugins (loaded on demand)

**Skeleton** — always load for new cases or when adding new stages/tasks/edges

| Plugin | When to load |
|---|---|
| [plugins/skeleton/case](references/plugins/skeleton/case.md) | Starting any new case — project scaffold + root JSON skeleton |
| [plugins/skeleton/stage](references/plugins/skeleton/stage.md) | Adding any stage node (includes ExceptionStage) |
| [plugins/skeleton/task](references/plugins/skeleton/task.md) | Adding any task — lane convention, common fields |
| [plugins/skeleton/edge](references/plugins/skeleton/edge.md) | Adding any edge — TriggerEdge vs Edge, handle format |

**Tasks** — load individually per task type

| Plugin | Task types covered |
|---|---|
| [plugins/tasks/standard-io](references/plugins/tasks/standard-io.md) ([planning](references/plugins/tasks/standard-io-planning.md)) | `process`, `agent`, `rpa`, `api-workflow`, `case-management` |
| [plugins/tasks/action](references/plugins/tasks/action.md) | `action` (human-in-the-loop) |
| [plugins/tasks/timer](references/plugins/tasks/timer.md) | `wait-for-timer` |
| [plugins/tasks/execute-connector-activity](references/plugins/tasks/execute-connector-activity.md) | `execute-connector-activity` (requires CLI enrichment) |
| [plugins/tasks/wait-for-connector](references/plugins/tasks/wait-for-connector.md) | `wait-for-connector` (requires CLI enrichment) |
| [plugins/tasks/external-agent](references/plugins/tasks/external-agent.md) | `external-agent` (requires CLI enrichment) |

**Triggers**

| Plugin | Covers |
|---|---|
| [plugins/triggers/manual](references/plugins/triggers/manual.md) | Manual trigger (default) |
| [plugins/triggers/timer](references/plugins/triggers/timer.md) | Timer trigger |
| [plugins/triggers/connector-trigger](references/plugins/triggers/connector-trigger.md) | Connector event trigger (requires CLI enrichment) |

**Conditions**

| Plugin | Covers |
|---|---|
| [plugins/conditions/stage-entry](references/plugins/conditions/stage-entry.md) | When a stage is active |
| [plugins/conditions/stage-exit](references/plugins/conditions/stage-exit.md) | When a stage exits |
| [plugins/conditions/task-entry](references/plugins/conditions/task-entry.md) | When a task triggers |
| [plugins/conditions/case-exit](references/plugins/conditions/case-exit.md) | When the case exits |

**SLA**

| Plugin | Covers |
|---|---|
| [plugins/sla](references/plugins/sla/sla.md) | Deadlines, escalation, conditional SLA |

**Variables**
| Plugin | Covers |
| [plugins/variables/bindings](references/plugins/variables/bindings.md) | Root binding declarations |
| [plugins/variables/global-vars](references/plugins/variables/global-vars.md) | Case-level variables (inputs, outputs, inputOutputs) |

## Anti-patterns

- **Do not reuse IDs** — every element needs a unique ID.
- **Do not omit `elementId`** on tasks or task inputs/outputs — format is `<stageId>-<taskId>`.
- **Do not omit `"data": {}` on edges** — required on both TriggerEdge and Edge.