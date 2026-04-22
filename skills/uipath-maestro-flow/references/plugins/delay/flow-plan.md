# Delay Node

## Node Type

`core.logic.delay`

## When to Use

Use a Delay node to pause execution for a duration or until a specific date.

### Selection Heuristics

| Situation | Use Delay? |
| --- | --- |
| Fixed duration pause (wait 15 minutes, wait 1 day) | Yes |
| Wait until a specific date/time | Yes |
| Wait for external work to complete | No — use [Queue](../queue/planning.md) (`create-and-wait`) |
| Wait for human input | No — use [HITL](../hitl/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `timerType` | Yes | `timeDuration` or `timeDate` |
| `timerPreset` | Yes | Preset value or `custom` |
| `timerValue` | Conditional | Required when `timerPreset: "custom"` (ISO 8601 duration) |
| `timerDate` | Conditional | Required when `timerType: "timeDate"` (ISO 8601 datetime or `=js:` expression) |

## Duration Presets

| Preset Value | Duration |
| --- | --- |
| `PT5M` | 5 minutes |
| `PT15M` | 15 minutes |
| `PT30M` | 30 minutes |
| `PT1H` | 1 hour |
| `PT6H` | 6 hours |
| `PT12H` | 12 hours |
| `P1D` | 1 day |
| `P1W` | 1 week |
| `custom` | Use `timerValue` for custom ISO 8601 duration |

## ISO 8601 Duration Format

`P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S`

Examples: `PT30S` (30 seconds), `PT2H30M` (2.5 hours), `P3DT12H` (3 days 12 hours)

## Registry Validation

```bash
uip maestro flow registry get core.logic.delay --output json
```

Confirm: input port `input`, output port `output`, required inputs `timerType` and `timerPreset`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

### Duration-Based (Preset)

```json
{
  "id": "wait15min",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "display": { "label": "Wait 15 Minutes" },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "PT15M"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Duration-Based (Custom ISO 8601)

```json
{
  "id": "waitCustom",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "display": { "label": "Wait 1 Day 5 Hours" },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "custom",
    "timerValue": "P1DT5H30M"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Date-Based (Wait Until)

```json
{
  "id": "waitUntil",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "display": { "label": "Wait Until April 15" },
  "inputs": {
    "timerType": "timeDate",
    "timerPreset": "custom",
    "timerDate": "=js:$vars.scheduledDate"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 string | Check format: `P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S` |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 duration |
| Missing `timerDate` | `timerType: "timeDate"` but no `timerDate` | Add `timerDate` with ISO 8601 datetime or `=js:` expression |
| Missing `eventDefinition` in model | Copied from wrong template | Add `"eventDefinition": "bpmn:TimerEventDefinition"` to `model` |
