# Standard IO Tasks — Planning

Covers five task types that share identical JSON structure: `process`, `agent`, `rpa`, `api-workflow`, `case-management`.

## When to Use Each Type

| Situation | Task type |
|---|---|
| Run a published orchestration / agentic process | `process` |
| Run a published AI agent | `agent` |
| Run a desktop or browser RPA automation | `rpa` |
| Call a published API workflow | `api-workflow` |
| Invoke a nested case management process | `case-management` |
| Need a human to review or decide | No — use [action](../action/planning.md) |
| Wait for a timer/delay | No — use [timer](../timer/planning.md) |

## What You Need Before Building

For each task, collect from the user or registry search:

| Info | Example | Used as |
|---|---|---|
| Resource key | `"Shared/[CM] Insurance.BookAppraisal"` | `resourceKey` in binding |
| Process display name | `"BookAppraisal"` | `default` in name binding |
| Folder path | `"Shared/[CM] Insurance"` | `default` in folderPath binding |

Run `uip case registry search "<keyword>"` to find the resource key.

## Binding Resource Values

| Task type | `resource` in binding |
|---|---|
| `process`, `agent`, `rpa`, `api-workflow`, `case-management` | `"process"` |
| `action` | `"app"` — use the action plugin instead |

## Re-entry Behaviour

Set `shouldRunOnlyOnce` based on whether the task should re-run if the stage is re-entered:

| `shouldRunOnlyOnce` | Task runs on re-entry? |
|---|---|
| `true` | No — runs only on first stage entry |
| `false` or absent | Yes — runs every time stage is entered |
