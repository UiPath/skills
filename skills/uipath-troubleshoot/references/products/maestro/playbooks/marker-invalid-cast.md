---
confidence: high
---

# Multi-Instance Marker InvalidCastException (400008)

## Context

What this looks like:
- HTTP 400, Maestro error code `400008` (`BpmnMarkerInputEvaluationFailure`)
- Error message: `Failed to evaluate the input collection variable for the marker element`
- Inner exception: `InvalidCastException: System.Object[] to ExpressionList`
- Sibling: see [marker-input-null](marker-input-null.md) when the collection is null (error `400007`)

What can cause it:
- Bug in `JavaScriptEvaluator.cs` — JS expression returns `Object[]` which cannot be cast to the internal `ExpressionList` type the BPMN engine expects on a multi-instance marker

What to look for:
- Whether the marker's "Items" expression uses `=js:` (JavaScript) — that's the trigger
- Whether the same logic written as C# works

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json` — confirm `InvalidCastException` and `ExpressionList`
2. Check the marker's "Items" expression language in the BPMN: `uip maestro <type> instance asset <instance-id> -f <folder-key> --output json`

## Resolution

- Switch the marker's "Items" expression from JavaScript to a C# expression that returns a typed list/array
- Re-publish and re-run; the parallel marker should iterate all items
- If switching to C# is not feasible, work around by materializing the JS array into a typed collection variable in a preceding Script task

## References

- [Docs: Multi-instance markers](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/markers-implementation)
