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

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow "uipath.core.rpa-workflow.{key}" --output json \
  --input '{"documentPath": "/invoices/batch1"}' \
  --label "Process Invoices" \
  --position 400,200
```

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

```bash
uip flow node add <Project>.flow core.logic.mock --output json \
  --label "Process Invoices [TODO: RPA]" \
  --position 400,200
```

Tell the user to create the RPA process with `uipath-rpa`, then replace the mock after publishing:

```bash
uip flow registry pull --force
uip flow registry search "<process-name>" --output json
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
```

1. Remove the mock node from `nodes`
2. Add the real resource node (with correct `type`, `inputs`, `model`)
3. Update all edges that referenced the mock node's ID
4. Add node variables to `variables.nodes`
5. Validate: `uip flow validate`

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
