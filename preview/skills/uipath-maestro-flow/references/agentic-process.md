# Agentic Process

*Exact signatures, fields, and defaults: [`agenticProcess()`](api.md#agenticprocess-function).*

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

## Forms and fire-and-forget completion

One `agenticProcess()` covers all three published forms; `form` selects the
wire identity: `'bpmn'` (default — Maestro BPMN process orchestration),
`'flow'` (published Maestro Flow), `'case'` (Case Management process).

`completion: 'fire-and-forget'` dispatches the process and continues
immediately: `returns` is forbidden, the step publishes no output (reading
`$vars.<step>.output` is a check error), and only dispatch failures route
through `.onError(...)`. Local replay treats it as dispatch-only.

```ts
.step('launchReview', agenticProcess({ key: reviewKey, name: 'ClaimsReview',
  folderPath: 'Shared', form: 'flow', completion: 'fire-and-forget',
  inputs: { claimId: input('claimId') } }))
```
