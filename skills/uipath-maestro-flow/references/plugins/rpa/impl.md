# RPA Node — Implementation

RPA nodes invoke published RPA processes. Pattern: `uipath.core.rpa-workflow.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.rpa-workflow" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Orchestrator.StartJob`
- `model.bindings.resourceSubType` — `Process`
- `inputDefinition` — may contain typed input fields (check `properties`)
- `outputDefinition.output` — process return value
- `outputDefinition.error` — error schema

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "processInvoices",
  "type": "uipath.core.rpa-workflow.invoice-process-abc123",
  "typeVersion": "1.0.0",
  "ui": { "position": { "x": 400, "y": 200 } },
  "display": { "label": "Process Invoices" },
  "inputs": {
    "documentPath": "=js:$vars.fileLocation",
    "batchSize": 50
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the RPA process",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the RPA process fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartJob",
    "version": "v2",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Process",
      "resourceKey": "invoice-process-abc123",
      "orchestratorType": "process",
      "values": {
        "name": "Invoice Processor",
        "folderPath": "Finance/Automation"
      }
    }
  }
}
```

## Mock Placeholder (If Not Yet Published)

If the RPA process is not yet published, add a `core.logic.mock` placeholder and tell the user to create it with `uipath-rpa`. After publishing, follow the [mock replacement procedure](../../flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) to swap the mock for the real resource node.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
