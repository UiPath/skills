# Agentic Process

*Behavior and worked examples. Exact signatures, fields, and defaults: [`agenticProcess()`](api.md#agenticprocess-function).*

Invoke a deployed Maestro agentic process.

Signature: `agenticProcess({ key, name, folderPath, inputs?, returns? })`

```ts
.step('intake',
  agenticProcess({
    key: 'BAADF00D-BAAD-F00D-BAAD-F00DBAADF00D',
    name: 'ProcurementProcess',
    folderPath: 'Shared',
    inputs: { productId: 1 },
    returns: { status: 'boolean' }
  }))
```

See [Orchestrator Processes](or-processes.md) and use the `ProcessOrchestration`, `CaseManagement`, and/or `Flow` process types to locate an agentic process and determine its contract.

## General

- Declared outputs can be returned as `null`
