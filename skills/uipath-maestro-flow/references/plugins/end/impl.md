# End Node — Implementation

## Node Type

`core.control.end`

## Registry Validation

```bash
uip flow registry get core.control.end --output json
```

Confirm: input port `input`, no output ports.

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

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.control.end --output json \
  --label "Done" \
  --position 700,300
```

> Output mapping must be added by editing the `.flow` JSON directly — the CLI does not support `--output` for End nodes.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Missing output mapping | `out` variable not mapped on this End node | Add `outputs.{varId}.source` expression for every `out` variable |
| Output expression unresolvable | `$vars` reference points to unreachable node | Ensure the node is upstream and connected via edges |
| Runtime silent failure | Output mapping missing on one reachable End node | Check **all** End nodes, not just the primary path |
