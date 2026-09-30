# Delay Node — Implementation

## Node Type

`core.logic.delay`

## Registry Validation

Run `uip maestro flow registry get core.logic.delay --output json`.

Confirm input port `input`, output port `output`, and required inputs `timerType` and `timerPreset`. Set the node instance `typeVersion` to the response `version` field; do not hardcode it.

## JSON Structure

```json
{
  "id": "<id>",
  "type": "core.logic.delay",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<label>" },
  "inputs": { "timerType": "<timerType>", "timerPreset": "<preset>" }
}
```

- Duration preset: use `timerType: "timeDuration"` and `timerPreset: "<preset>"` (for example, `"PT15M"`).
- Custom duration: use `timerPreset: "custom"` and add `timerValue` as an ISO 8601 duration (for example, `"P1DT5H30M"`).
- Wait until a date: use `timerType: "timeDate"`, `timerPreset: "custom"`, and `timerDate` as an ISO 8601 datetime or `=js:` expression (for example, `"=js:$vars.scheduledDate"`).

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). BPMN type and event definition come from `definitions[]`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 string | Check format: `P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S` |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 duration |
| Missing `timerDate` | `timerType: "timeDate"` but no `timerDate` | Add `timerDate` with ISO 8601 datetime or `=js:` expression |
| BPMN timer event not emitted | Wrong `core.logic.delay` definition in `definitions[]` | Re-copy from `uip maestro flow registry get core.logic.delay --output json` — the definition carries `model.eventDefinition: "bpmn:TimerEventDefinition"` |