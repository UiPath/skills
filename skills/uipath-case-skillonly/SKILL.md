---
name: uipath-case-skillonly
description: "[PREVIEW] UiPath Case Management caseplan.json authoring. Two phases: spec.md→tasks.md (planning), tasks.md→caseplan.json (impl, JSON-direct). Registry/enrich/validate/debug→CLI. For .xaml→uipath-rpa. For .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management — Skill-Driven Authoring

Builds and edits Case Management definition files (`caseplan.json`) by writing JSON directly. The skill is split into two phases:

| Phase | Input | Output | Reference |
|---|---|---|---|
| **Planning** | `spec.md` (case design document) | `tasks.md` + `registry-resolved.json` | [references/planning.md](references/planning.md) |
| **Implementation** | `tasks.md` | `caseplan.json` (validated) | [references/impl.md](references/impl.md) |

A small set of CLI commands handles operations that genuinely require external APIs (registry pull, connector enrichment, validate, debug, runtime instance management). Everything else is direct JSON.

## When to Use This Skill

- User wants to **create or edit a caseplan.json** (stages, tasks, edges, conditions, SLA, bindings)
- User provides a **spec.md** (case design document) — load [planning.md](references/planning.md)
- User provides a **tasks.md** — load [references/impl.md](references/impl.md)
- User wants to **discover available resources** via the registry before building
- User wants to **validate, debug, or deploy** a case definition
- User wants to **manage runtime instances** — list, pause, resume, cancel
- User asks about the **case management JSON schema** — nodes, edges, tasks, rules, bindings

For CLI-driven editing (`uip case stages add`, `tasks add`, `edges add`, etc.), use the `uipath-case-management` skill instead.

## Routing — Which Phase to Run

Decide based on what files the user provides:

| Inputs present | Run |
|---|---|
| Only `spec.md` (no `tasks.md`) | [planning.md](references/planning.md) → produces tasks.md → then [impl.md](references/impl.md) |
| Only `tasks.md` (no `spec.md`) | [impl.md](references/impl.md) directly |
| Both `spec.md` and `tasks.md` | If user wants to **rebuild the plan**, run planning. Otherwise jump to [impl.md](references/impl.md). Ask if unclear. |
| Neither — just an existing `caseplan.json` to edit | [impl.md → Common Edits](references/impl.md#common-edits--existing-caseplanjson) |
| Neither — fresh case described inline in chat | Treat the chat as the spec; ask whether to write a spec.md first or jump straight to tasks.md |

**Do not skip the planning phase** when only a spec.md exists. Without tasks.md, the implementation phase has no resolved registry IDs and would have to re-do discovery mid-build.

## Critical Rules

1. **Write JSON directly** — do not call `uip case cases/stages/tasks/edges/sla/conditions/var add` commands. The agent writes caseplan.json using the schema in [references/case-schema-reference.md](references/case-schema-reference.md). CLI is reserved for: `registry pull/search`, `tasks describe`, `tasks add-connector`, `triggers add-event`, `registry get-connector/get-connection`, `validate`, `debug`, `process/*`, `job/*`, `instance/*`.
2. **Version is always `"v16"`** — use this literal in `root.version`.
3. **Generate IDs using the prefixedId convention** — see [ID Generation](#id-generation) below.
4. **Bindings live at root level** — every process/agent/rpa/action/api-workflow/case-management task references its `name` and `folderPath` via `=bindings.<id>` pointing to entries in `root.data.uipath.bindings`.
5. **Connector tasks need CLI enrichment** — `external-agent`, `wait-for-connector`, `execute-connector-activity`, and event triggers cannot be fully built without calling `uip case tasks describe` / `add-connector` or `triggers add-event`.
6. **`shouldRunOnlyOnce`** is the current task field (`shouldRunOnReEntry` is deprecated).
7. **One task per lane** — each task occupies its own lane (index increments by 1). Never group multiple tasks in the same lane. Parallelism is controlled by entry conditions, not lane grouping. See [plugins/setup/task](references/plugins/setup/task/impl.md).
8. **Validate before debug** — run `uip case validate <path>` before `debug`.
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

## Quick Workflow Summary

For the full procedure, see the phase-specific reference. This is just a high-level overview.

### If starting from spec.md

1. Run [planning.md](references/planning.md) — pulls registry, resolves task types, emits `tasks/tasks.md` + `tasks/registry-resolved.json`
2. Run [impl.md](references/impl.md) — scaffolds project, writes caseplan.json, enriches connector tasks, validates

### If starting from tasks.md

1. Run [impl.md](references/impl.md) directly

### If editing an existing caseplan.json

1. Go to [impl.md → Common Edits](references/impl.md#common-edits--existing-caseplanjson) for targeted recipes (rename, insert, rewire, add condition, etc.)
2. Run `uip case validate` once after the batch of edits

## Reference Navigation

### Phase guides

| Reference | Covers |
|---|---|
| [references/planning.md](references/planning.md) | Phase 1 — spec.md → tasks.md (registry discovery, task-type resolution, tasks.md format) |
| [references/impl.md](references/impl.md) | Phase 2 — tasks.md → caseplan.json (Quick Start, Common Edits, variable binding, runtime ops) |

### Schema and CLI reference

| Reference | Covers |
|---|---|
| [references/case-schema-reference.md](references/case-schema-reference.md) | Full caseplan.json JSON schema |
| [references/commands-reference.md](references/commands-reference.md) | All `uip case` CLI subcommands |

### Plugins (loaded on demand from impl.md)

**Setup** — load first when building

| Plugin | When to load |
|---|---|
| [plugins/setup/case-skeleton](references/plugins/setup/case-skeleton/impl.md) | Starting any new case — project scaffold + root JSON skeleton |
| [plugins/setup/stage](references/plugins/setup/stage/impl.md) | Adding any stage node |
| [plugins/setup/task](references/plugins/setup/task/impl.md) | Adding any task — lane convention, common fields |
| [plugins/setup/edge](references/plugins/setup/edge/impl.md) | Adding any edge — TriggerEdge vs Edge, handle format |

**Tasks** — one plugin per task `type`

| Plugin | Task type |
|---|---|
| [plugins/tasks/process](references/plugins/tasks/process/planning.md) | `process` |
| [plugins/tasks/agent](references/plugins/tasks/agent/planning.md) | `agent` |
| [plugins/tasks/rpa](references/plugins/tasks/rpa/planning.md) | `rpa` |
| [plugins/tasks/api-workflow](references/plugins/tasks/api-workflow/planning.md) | `api-workflow` |
| [plugins/tasks/case-management](references/plugins/tasks/case-management/planning.md) | `case-management` |
| [plugins/tasks/action](references/plugins/tasks/action/planning.md) | `action` |
| [plugins/tasks/timer](references/plugins/tasks/timer/planning.md) | `wait-for-timer` |
| [plugins/tasks/execute-connector-activity](references/plugins/tasks/execute-connector-activity/planning.md) | `execute-connector-activity` |
| [plugins/tasks/wait-for-connector](references/plugins/tasks/wait-for-connector/planning.md) | `wait-for-connector` |
| [plugins/tasks/external-agent](references/plugins/tasks/external-agent/planning.md) | `external-agent` |

**Triggers**

| Plugin | Covers |
|---|---|
| [plugins/triggers/manual](references/plugins/triggers/manual/impl.md) | Manual trigger (default) |
| [plugins/triggers/timer](references/plugins/triggers/timer/planning.md) | Timer trigger |
| [plugins/triggers/connector-trigger](references/plugins/triggers/connector-trigger/planning.md) | Connector event trigger |

**Stage Types**

| Plugin | Covers |
|---|---|
| [plugins/stage-types/exception-stage](references/plugins/stage-types/exception-stage/planning.md) | ExceptionStage — error handlers, return-to-origin |

**Conditions**

| Plugin | Covers |
|---|---|
| [plugins/conditions/stage-entry](references/plugins/conditions/stage-entry/planning.md) | When a stage becomes active |
| [plugins/conditions/stage-exit](references/plugins/conditions/stage-exit/planning.md) | When a stage completes |
| [plugins/conditions/task-entry](references/plugins/conditions/task-entry/planning.md) | When a task within a stage triggers |
| [plugins/conditions/case-exit](references/plugins/conditions/case-exit/impl.md) | When the case ends |
| [plugins/conditions/wait-for-connector](references/plugins/conditions/wait-for-connector/planning.md) | Wait for Integration Service connector event |

**SLA and Variables**

| Plugin | Covers |
|---|---|
| [plugins/sla/setup](references/plugins/sla/setup/planning.md) | Deadlines, escalation, conditional SLA |
| [plugins/variables/bindings](references/plugins/variables/bindings/impl.md) | Root binding declarations |
| [plugins/variables/global-vars](references/plugins/variables/global-vars/planning.md) | Case-level variables (inputs, outputs, inputOutputs) |

## Anti-patterns

- **Do not call `uip case stages/tasks/edges/sla/conditions/var add` commands** — write JSON directly. For CLI-driven editing, use the `uipath-case-management` skill.
- **Do not group tasks in the same lane** — one task per lane; parallelism via entry conditions.
- **Do not hand-write connector task schemas** — use `tasks add-connector` or `tasks describe`.
- **Do not reuse IDs** — every element needs a unique ID.
- **Do not omit `elementId` on tasks** — format is `<stageId>-<taskId>`.
- **Do not use `required-tasks-completed` on case exit conditions** — use `required-stages-completed`.
- **Do not omit `"data": {}` on edges** — required on both TriggerEdge and Edge.
- **Do not skip planning when only a spec.md is provided** — without tasks.md, the implementation phase has no resolved registry IDs.
