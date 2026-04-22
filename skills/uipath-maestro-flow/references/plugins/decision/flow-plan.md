# Decision Node

## Node Type

`core.logic.decision`

## When to Use

Use a Decision node for binary branching (if/else) based on a boolean condition.

### Selection Heuristics

| Situation | Use Decision? |
| --- | --- |
| Two-path branch based on a boolean condition | Yes |
| Three or more paths | No — use [Switch](../switch/flow-plan.md) |
| Branch on HTTP response status codes | No — use [HTTP](../http/flow-plan.md) built-in branches |
| Branch requires reasoning on ambiguous input | No — use [Agent](../agent/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `true`, `false` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `expression` | Yes | Boolean JavaScript expression (e.g., `$vars.fetchData.output.statusCode === 200`) |
| `trueLabel` | No | Custom label for the true branch |
| `falseLabel` | No | Custom label for the false branch |

## Wiring Rules

- Decision nodes produce exactly **two** outgoing edges: one from `true`, one from `false`
- Both branches must lead to a downstream node (no dangling branches)
- Each branch typically ends at its own End node or merges back into a shared path

## Registry Validation

```bash
uip flow registry get core.logic.decision --output json
```

Confirm: input port `input`, output ports `true` and `false`, required input `expression`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "typeVersion": "1.0.0",
  "display": { "label": "Check Status" },
  "inputs": {
    "expression": "$vars.fetchData.output.statusCode === 200"
  },
  "model": { "type": "bpmn:ExclusiveGateway" }
}
```

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

Output ports: `true` and `false`. Both branches must be wired. See [flow-editing-operations.md](../../flow-editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Expression does not evaluate to boolean | Expression returns non-boolean value | Ensure expression uses comparison operators (`===`, `>`, etc.) |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Only one branch wired | Missing true or false edge | Add the missing edge — both branches are required |
