# RPA Process Nodes

RPA resource nodes invoke published RPA workflows (XAML or coded C#) from within a flow. They appear in the registry after login.

## Implementation

### Node Type Pattern

| Node Type Pattern | Service Type | Category |
|---|---|---|
| `uipath.core.rpa-workflow.{key}` | `Orchestrator.StartJob` | `rpa-workflow` |

### Discovery

```bash
uip flow registry pull --force
uip flow registry search process --output json
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
```

The `{key}` is the resource's unique identifier from Orchestrator (typically a GUID or slug).

### When to Use RPA

Use RPA resource nodes only when the target system has no API:
- Legacy desktop applications
- Terminal-based systems
- Browser flows that cannot be done via API
- Systems requiring screen scraping or UI interaction

RPA requires robot infrastructure and is orders of magnitude slower than API-based approaches. Prefer higher tiers first:

1. Pre-built IS connector → connector node
2. HTTP Request within a connector → connector node (HTTP fallback)
3. Standalone HTTP Request → `core.action.http`
4. **RPA workflow** → `uipath.core.rpa-workflow.{key}` (last resort for API-less systems)

### Configuration

After discovering the RPA resource in the registry:

```bash
uip flow node add <file> "uipath.core.rpa-workflow.{key}" --output json \
  --input '{"documentPath": "/invoices/batch1"}' \
  --label "Process Invoices"
```

Wire edges and validate:

```bash
uip flow edge add <file> <upstreamId> <rpaNodeId> --output json
uip flow validate <file> --output json
```

### JSON Structure

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

### Ports

| Input Port | Output Port(s) |
|---|---|
| `input` | `success` |

### Output Variables

- `$vars.{nodeId}.output` — the RPA workflow's return value (structure depends on the workflow)
- `$vars.{nodeId}.error` — error details if execution fails

### Creating a New RPA Process

If the flow needs an RPA process that doesn't exist yet:

1. Add a `core.logic.mock` placeholder in the flow
2. Tell the user to use:
   - `uipath-coded-workflows` — for C# coded workflows (CLI-only)
   - `uipath-rpa-workflows` — for XAML workflows (requires Studio Desktop)
3. After publishing, refresh registry and replace the mock:

```bash
uip flow registry pull --force
uip flow registry search "<process-name>" --output json
```

## Debug

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| RPA process not found in registry | Process not published to Orchestrator | Publish the workflow, then `registry pull --force` |
| Job fails to start | No available robot or folder mismatch | Check Orchestrator folder and robot availability |
| Input schema mismatch | Flow passes inputs the RPA workflow doesn't expect | Check `inputDefinition` from `registry get` for expected input names and types |
| Process times out | RPA workflow takes too long or is stuck | Check robot logs in Orchestrator; RPA workflows can hang on UI element waits |

### Debug Tips

1. **RPA processes need robots** — unlike connector nodes that call APIs directly, RPA workflows need an available robot in Orchestrator to execute
2. **Check `inputDefinition` carefully** — RPA input/output schemas are defined by the workflow author. Mismatched field names or types are the most common error
3. **RPA is slow by design** — expect seconds to minutes per execution, not milliseconds. For batch processing, consider using queue nodes (`core.action.queue.create`) to distribute work across multiple robots
4. **Two flavors of RPA** — XAML workflows (built in Studio Desktop) and coded workflows (C#, built via CLI). Both publish to Orchestrator the same way and appear as `uipath.core.rpa-workflow.{key}` in the registry
