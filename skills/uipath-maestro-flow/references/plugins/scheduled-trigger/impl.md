# Scheduled Trigger — Implementation

## Node Type

`core.trigger.scheduled`

## Registry Validation

```bash
uip flow registry get core.trigger.scheduled --output json
```

Confirm: no input port, output port `output`, required inputs `timerType` and `timerPreset`.

## JSON Structure

### Preset Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0.0",
  "display": { "label": "Every Hour" },
  "inputs": {
    "timerType": "timeCycle",
    "timerPreset": "R/PT1H"
  },
  "model": {
    "type": "bpmn:StartEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Custom Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0.0",
  "display": { "label": "Every 45 Minutes" },
  "inputs": {
    "timerType": "timeCycle",
    "timerPreset": "custom",
    "timerValue": "R/PT45M"
  },
  "model": {
    "type": "bpmn:StartEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

## Replacing Manual Trigger with Scheduled

1. Change the start node's `type` to `core.trigger.scheduled`
2. Add timer inputs: `timerType: "timeCycle"`, `timerPreset: "R/PT1H"` (or custom)
3. Add the `eventDefinition` to `model`: `"eventDefinition": "bpmn:TimerEventDefinition"`
4. Update the definition in the `definitions` array (get from `registry get`)
5. Validate: `uip flow validate`

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 repeating interval | Check format: `R/P[duration]` (e.g., `R/PT1H`) |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 repeating interval |
| Missing `eventDefinition` in model | Forgot to add timer event definition | Add `"eventDefinition": "bpmn:TimerEventDefinition"` to `model` |
| Two triggers in flow | Both manual and scheduled triggers exist | Remove one — flows must have exactly one trigger |
