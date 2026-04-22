# End Node

## Node Type

`core.control.end`

## When to Use

Use an End node for graceful workflow completion. Each terminal path in the flow needs its own End node.

### Selection Heuristics

| Situation | Use End? |
| --- | --- |
| Normal completion of an execution path | Yes |
| Fatal error — abort everything immediately | No — use [Terminate](../terminate/flow-plan.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | — (none) |

## Key Rules

- A flow can have multiple End nodes (one per terminal path)
- Every `out` variable in `variables.globals` **must** be mapped on **every** reachable End node via `outputs`
- End nodes only terminate their own path — other parallel branches continue

## Registry Validation

```bash
uip flow registry get core.control.end --output json
```

Confirm: input port `input`, no output ports.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

Output mapping must be added by editing the `.flow` JSON directly — see [JSON: Add output mapping](../../flow-editing-operations-json.md#add-output-mapping-on-an-end-node).

## JSON Structure

### Without Output Mapping

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "display": { "label": "Done" },
  "inputs": {},
  "model": { "type": "bpmn:EndEvent" }
}
```

### With Output Mapping

When the workflow declares `out` variables, every End node must map all of them:

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "display": { "label": "Done" },
  "inputs": {},
  "outputs": {
    "processedCount": {
      "source": "=js:$vars.processData.output.count"
    },
    "resultSummary": {
      "source": "=js:$vars.formatOutput.output.summary"
    }
  },
  "model": { "type": "bpmn:EndEvent" }
}
```

Each key in `outputs` must match a variable `id` from `variables.globals` where `direction: "out"`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Missing output mapping | `out` variable not mapped on this End node | Add `outputs.{varId}.source` expression for every `out` variable |
| Output expression unresolvable | `$vars` reference points to unreachable node | Ensure the node is upstream and connected via edges |
| Runtime silent failure | Output mapping missing on one reachable End node | Check **all** End nodes, not just the primary path |
