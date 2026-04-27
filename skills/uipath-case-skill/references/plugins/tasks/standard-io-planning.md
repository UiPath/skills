# Standard-IO Tasks — Planning

Covers five task types that share the same binding structure (`resource: "process"`, `name` + `folderPath`) and JSON skeleton. They differ only in the `type` field and registry filter.

## Type Reference

| `type` value | What it runs | Registry `resourceSubType` filter |
|---|---|---|
| `process` | Published agentic or orchestration process | `ProcessOrchestration` |
| `agent` | Published AI/LLM-based agent | `Agent` |
| `rpa` | Published RPA automation (desktop/browser) | *(absent — RPA processes have no subtype)* |
| `api-workflow` | Published API workflow (backend REST) | `Api` |
| `case-management` | Nested child case | `CaseManagement` |

## When NOT to Use a Standard-IO Task

| Situation | Use instead |
|---|---|
| Human needs to approve, review, or decide | [action](action.md) |
| Timed delay / wait | [timer](timer.md) |
| Synchronous connector call | [execute-connector-activity](execute-connector-activity.md) |
| Wait for an external event | [wait-for-connector](wait-for-connector.md) |
| External (non-UiPath) agent | [external-agent](external-agent.md) |

## What You Need

- Process/agent/workflow name and folder path from registry search
- Input variable names and types (if any)
- Output variable names to capture (if any)

## Discovery

```bash
uip case registry search "<name>" --output json
```

Filter results by `resource: "process"` and the `resourceSubType` from the table above. For RPA processes, `resourceSubType` is absent — match on `resource: "process"` with no subtype.
