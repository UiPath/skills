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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the trigger.",
      "source": "=result.response",
      "var": "output"
    }
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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the trigger.",
      "source": "=result.response",
      "var": "output"
    }
  },
  "model": {
    "type": "bpmn:StartEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

## Replacing Manual Trigger with Scheduled

For the step-by-step procedure, see [CLI: Replace manual trigger with scheduled trigger](../../flow-editing-operations-cli.md#replace-manual-trigger-with-scheduled-trigger) or [JSON: Replace manual trigger with scheduled trigger](../../flow-editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger). Use the JSON structures above for the node-specific `inputs` and `model` fields.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 repeating interval | Check format: `R/P[duration]` (e.g., `R/PT1H`) |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 repeating interval |
| Missing `eventDefinition` in model | Forgot to add timer event definition | Add `"eventDefinition": "bpmn:TimerEventDefinition"` to `model` |
| Two triggers in flow | Both manual and scheduled triggers exist | Remove one — flows must have exactly one trigger |
