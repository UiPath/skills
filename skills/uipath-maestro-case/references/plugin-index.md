# JSON plugin index

Read the row matching the current SDD declaration. Read each selected file to
its `END` marker once per type, then lower every declaration of that type.

## Root and structure

| SDD declaration | JSON recipe |
|---|---|
| Case metadata and project scaffold | [plugins/case/impl-json.md](plugins/case/impl-json.md) |
| Primary or secondary stage | [plugins/stages/impl-json.md](plugins/stages/impl-json.md) |
| Case variables and In/Out arguments | [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |
| Task inputs, outputs, and cross-task references | [plugins/variables/io-binding/impl-json.md](plugins/variables/io-binding/impl-json.md) |
| Resource bindings | [plugins/variables/bindings/impl-json.md](plugins/variables/bindings/impl-json.md) |
| SLA and escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |

## Triggers

| SDD Trigger Type | JSON recipe |
|---|---|
| Manual | [plugins/triggers/manual/impl-json.md](plugins/triggers/manual/impl-json.md) |
| Timer | [plugins/triggers/timer/impl-json.md](plugins/triggers/timer/impl-json.md) |
| Event | [plugins/triggers/event/impl-json.md](plugins/triggers/event/impl-json.md) |

## Tasks

The SDD value and `caseplan.json` `type` use schema-kebab. Connector recipe
folder names and CLI describe flags are different; never copy them into JSON.

| SDD / caseplan type | Recipe | `tasks describe --type` |
|---|---|---|
| `process` | [plugins/tasks/process/impl-json.md](plugins/tasks/process/impl-json.md) | `process` |
| `agent` | [plugins/tasks/agent/impl-json.md](plugins/tasks/agent/impl-json.md) | `agent` |
| `rpa` | [plugins/tasks/rpa/impl-json.md](plugins/tasks/rpa/impl-json.md) | `rpa` |
| `action` | [plugins/tasks/action/impl-json.md](plugins/tasks/action/impl-json.md) | `action` |
| `api-workflow` | [plugins/tasks/api-workflow/impl-json.md](plugins/tasks/api-workflow/impl-json.md) | `api-workflow` |
| `case-management` | [plugins/tasks/case-management/impl-json.md](plugins/tasks/case-management/impl-json.md) | `case-management` |
| `execute-connector-activity` | [plugins/tasks/connector-activity/impl-json.md](plugins/tasks/connector-activity/impl-json.md) | `connector-activity` |
| `wait-for-connector` | [plugins/tasks/connector-trigger/impl-json.md](plugins/tasks/connector-trigger/impl-json.md) | `connector-trigger` |
| `wait-for-timer` | [plugins/tasks/wait-for-timer/impl-json.md](plugins/tasks/wait-for-timer/impl-json.md) | no describe call |

## Conditions

| SDD table | JSON recipe |
|---|---|
| Stage Entry Conditions | [plugins/conditions/stage-entry-conditions/impl-json.md](plugins/conditions/stage-entry-conditions/impl-json.md) |
| Stage Exit Conditions | [plugins/conditions/stage-exit-conditions/impl-json.md](plugins/conditions/stage-exit-conditions/impl-json.md) |
| Task Entry Condition | [plugins/conditions/task-entry-conditions/impl-json.md](plugins/conditions/task-entry-conditions/impl-json.md) |
| Case Exit Conditions | [plugins/conditions/case-exit-conditions/impl-json.md](plugins/conditions/case-exit-conditions/impl-json.md) |

Connector-bound `wait-for-connector` rules additionally require
`connector-trigger-impl.md` after their trigger spec is available.

<!-- END: plugin-index.md -->
