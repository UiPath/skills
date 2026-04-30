# Decision Node — Implementation

## Node Type

`core.logic.decision`

## Registry Validation

```bash
uip maestro flow registry get core.logic.decision --output json
```

Confirm: input port `input`, output ports `true` and `false`, required input `expression`.

## JSON Structure

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "typeVersion": "1.0.0",
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

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Expression does not evaluate to boolean | Expression returns non-boolean value | Ensure expression uses comparison operators (`===`, `>`, etc.) |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Only one branch wired | Missing true or false edge | Add the missing edge — both branches are required |
