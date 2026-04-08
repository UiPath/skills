# Decision Node — Implementation

## Node Type

`core.logic.decision`

## Registry Validation

```bash
uip flow registry get core.logic.decision --output json
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
    "expression": "=js:$vars.fetchData.output.statusCode === 200"
  },
  "model": { "type": "bpmn:ExclusiveGateway" }
}
```

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.logic.decision --output json \
  --input '{"expression": "=js:$vars.fetchData.output.statusCode === 200"}' \
  --label "Check Status" \
  --position 400,300
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

## Wiring Example

```bash
# True branch
uip flow edge add <ProjectName>.flow checkStatus processOrder --output json \
  --source-port true --target-port input

# False branch
uip flow edge add <ProjectName>.flow checkStatus logSkip --output json \
  --source-port false --target-port input
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Expression does not evaluate to boolean | Expression returns non-boolean value | Ensure expression uses comparison operators (`===`, `>`, etc.) |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Only one branch wired | Missing true or false edge | Add the missing edge — both branches are required |
