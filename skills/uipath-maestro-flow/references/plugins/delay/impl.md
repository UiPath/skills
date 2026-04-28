# Delay Node — Implementation

## Node Type

`core.logic.delay`

## Registry Validation

```bash
uip maestro flow registry get core.logic.delay --output json
```

Confirm: input port `input`, output port `output`, required inputs `timerType` and `timerPreset`.

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
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure above for the node-specific `inputs`. BPMN type and event definition come from the definition in `definitions[]`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 string | Check format: `P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S` |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 duration |
| Missing `timerDate` | `timerType: "timeDate"` but no `timerDate` | Add `timerDate` with ISO 8601 datetime or `=js:` expression |
| BPMN timer event not emitted | Wrong `core.logic.delay` definition in `definitions[]` | Re-copy from `uip maestro flow registry get core.logic.delay --output json` — the definition carries `model.eventDefinition: "bpmn:TimerEventDefinition"` |
