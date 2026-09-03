# Scheduled Trigger — Implementation

## Node Type

`core.trigger.scheduled`

## Registry Validation

Run `uip maestro flow registry get core.trigger.scheduled --output json`.

Confirm that the definition has no input port, output port `output`, and required inputs `timerType` and `timerPreset`. Set the node instance `typeVersion` to the response `version` field; do not hardcode it because this node has advanced past `1.0`.

## JSON Structure

### Preset Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Every Hour" },
  "inputs": {
    "entryPointId": "<uuid>",
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
  }
}
```

### Custom Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Every 45 Minutes" },
  "inputs": {
    "entryPointId": "<uuid>",
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
  }
}
```

Do not add BPMN type (`bpmn:StartEvent`) or event definition (`bpmn:TimerEventDefinition`) to the instance; they come from the `core.trigger.scheduled` entry in `definitions[]`.

## Replacing Manual Trigger with Scheduled

Use [Edit/Write: Replace manual trigger with scheduled trigger](../../editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) for the step-by-step procedure, supplying the node-specific `inputs` above.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 repeating interval | Check format: `R/P[duration]` (e.g., `R/PT1H`) |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with an ISO 8601 repeating interval |
| BPMN timer event not emitted | `core.trigger.scheduled` definition wrong or missing | Re-copy from `uip maestro flow registry get core.trigger.scheduled --output json` — the definition carries `model.eventDefinition: "bpmn:TimerEventDefinition"` |
| Two triggers in flow | Both manual and scheduled triggers exist | Remove one — flows must have exactly one trigger |