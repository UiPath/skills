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

`registry get` shows a Decision declaring two outputs, `matchedCase` and `matchedCaseId`, and `flow format` writes them into `variables.nodes[]`. **Ignore both. Neither is ever assigned at runtime.**

They are synthetic. The scope resolver suppresses a gateway's outputs for every reader except the gateway itself, and the flow→BPMN serializer emits no writer for them — a Decision compiles to a gateway whose branch choice lives on the outgoing sequence flows' `conditionExpression`, never in a variable. They hold real values only in the Studio Web canvas, which evaluates gateways client-side. Because the variable is *declared* but never assigned, a downstream read fails **silently**: `undefined` flows into the reader's own logic and yields a wrong result instead of a fault.

| What you write | What happens |
| --- | --- |
| `$vars.<decisionId>.matchedCaseId` or `.matchedCase` | validate passes with `[EXPRESSION_DIAGNOSTIC] Property '<decisionId>' does not exist on type '{…}'`; reads `undefined` at runtime |
| `$vars.<decisionId>.output.matchedCaseId` | validate **fails**: `node "<decisionId>" has no output named "output" — its outputs are: matchedCase, matchedCaseId` |

> That second message then recommends `$vars.<decisionId>.matchedCaseId`. Take only half of it: drop the `.output.` segment **and** stop reading the gateway. The cross-reference check reads the registry's declared outputs and does not know the scope resolver suppresses them.

To act on which branch ran, use one of:

- **Recompute the condition** from a node upstream of the Decision, which is still in scope — `$vars.getWeather.output.tempF > 60` rather than the Decision's result. Cheapest when the condition's inputs are still reachable.
- **Write an `inout` global on each branch** with [`variables.variableUpdates`](../../editing-operations-json.md#add-a-variable-update), then read `$vars.<globalId>` where the branches rejoin. Use this when the condition cannot be recomputed. Map the global on every End node or it raises `MISSING_OUTPUT_MAPPING`.

This holds whether or not the branches rejoin, and applies identically to [Switch](../switch/impl.md#outputs).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Expression does not evaluate to boolean | Expression returns non-boolean value | Ensure expression uses comparison operators (`===`, `>`, etc.) |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| `[400302] Error evaluating outgoing flow expression from gateway` | `expression` reads a node that runs *after* the Decision (typical after moving the Decision earlier in the flow) | Point `expression` at a node that still runs before the Decision (e.g. the HTTP node's `$vars.<node>.output…`), not at the node the branches lead to |
| Only one branch wired | Missing true or false edge | Add the missing edge — both branches are required |
