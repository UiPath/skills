---
confidence: high
---

# Marker Input Collection Is Null (400007)

## Context

What this looks like:
- HTTP 400, Maestro error code `400007` (`BpmnMarkerInputNullError`)
- Error message: `Input collection for the marker element must not be null`
- Sometimes seen alongside the related evaluation error `400008` (`BpmnMarkerInputEvaluationFailure`) — see [marker-invalid-cast](marker-invalid-cast.md) for the JS array cast bug

What can cause it:
- The variable referenced in the multi-instance marker's "Items" property is `null` at runtime (never assigned, or upstream task didn't produce the list)
- A `NullReferenceException` in `BpmnExecution.cs` where a marker input was assumed non-null but the underlying success value was null (known internal bug; tracked historically — fix replaces `!` null-forgiving with `?? throw`)
- User Task multi-instance "items" passed a malformed JSON array (e.g., a stringified array instead of a real array)

What to look for:
- The marker's `elementId` from the incident
- Variables API: confirm the collection variable is actually `null` (vs empty array, which behaves differently)
- Upstream element that should have produced the collection

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json`
2. Pull variables scoped to the marker element: `uip maestro <type> instance variables <instance-id> -f <folder-key> --parent-element-id <marker-element-id> --output json` — verify the "Items" variable is null
3. Walk element executions to find the upstream task that was supposed to produce the collection: `uip maestro <type> instance element-executions <instance-id> -f <folder-key> --output json`
4. Inspect the marker's "Items" expression in the BPMN: `uip maestro <type> instance asset <instance-id> -f <folder-key> --output json`

## Resolution

- **If upstream task produced nothing:** fix the upstream task or add an exclusive gateway that skips the marker when the collection is null/empty
- **If variable was renamed / unbound:** re-select the collection variable in the marker's "Items" property
- **If malformed JSON array on User Task:** ensure callers construct a real JSON array, not a stringified one
- **If you suspect the internal null-forgiving bug:** request the Maestro engine team confirm the `BpmnExecution.cs` fix is deployed in your region; in the meantime ensure the upstream activity never returns a null wrapper
- **If using JS expression and seeing `InvalidCastException`:** switch to C# expressions and see [marker-invalid-cast](marker-invalid-cast.md)

## References

- [Docs: Multi-instance markers](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/markers-implementation)
- [Docs: Markers](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/markers)
