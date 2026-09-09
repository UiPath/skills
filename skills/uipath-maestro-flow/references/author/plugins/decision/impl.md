# Decision Node — Implementation

## Node Type

`core.logic.decision`

## Registry Validation

```bash
uip maestro flow registry get core.logic.decision --output json
```

Confirm: input port `input`, output ports `true` and `false`, required input `expression`. Set the node instance `typeVersion` to the `version` field from this response — do not hardcode it.

## JSON Structure

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Check Status" },
  "inputs": {
    "expression": "$vars.fetchData.output.statusCode === 200"
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`.

## Expression Examples

```javascript
// Simple comparison
$vars.fetchData.output.statusCode === 200

// Boolean field
$vars.processData.output.isValid

// Compound condition
$vars.httpCall.output.statusCode === 200 && $vars.httpCall.output.body.count > 0

// String check
$vars.classify.output.category === "urgent"

// Null check
$vars.lookupUser.output.user !== null
```

## Wiring

Output ports: `true` and `false`. Both branches must be wired. See [editing-operations.md](../../editing-operations.md) for edge add procedures.

## Outputs

A Decision is **not readable from downstream at all**. It never enters a downstream node's expression scope, so every form — `$vars.<decisionId>.matchedCaseId`, `.matchedCase`, `.output.matchedCaseId` — resolves to `undefined`. This holds whether or not the branches rejoin. `flow validate` reports it as `[EXPRESSION_DIAGNOSTIC] Property '<decisionId>' does not exist on type '{…}'`, listing a scope the Decision is absent from; the flow still validates, then reads `undefined` at runtime and silently takes the wrong branch of the reader's own logic.

To act on which branch ran, use one of:

- **Recompute the condition** from a node that is upstream of the Decision and therefore still in scope — `$vars.getWeather.output.tempF > 60` rather than the Decision's result. Cheapest when the condition's inputs are still reachable.
- **Write an `inout` global on each branch** with [`variables.variableUpdates`](../../editing-operations-json.md#add-a-variable-update), then read `$vars.<globalId>` at the node the branches rejoin. Use this when the condition cannot be recomputed. Map the global on every End node or it raises `MISSING_OUTPUT_MAPPING`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Expression does not evaluate to boolean | Expression returns non-boolean value | Ensure expression uses comparison operators (`===`, `>`, etc.) |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| `[400302] Error evaluating outgoing flow expression from gateway` | `expression` reads a node that runs *after* the Decision (typical after moving the Decision earlier in the flow) | Point `expression` at a node that still runs before the Decision (e.g. the HTTP node's `$vars.<node>.output…`), not at the node the branches lead to |
| Only one branch wired | Missing true or false edge | Add the missing edge — both branches are required |
