# API Workflow

*Behavior and worked examples. Exact signatures, fields, and defaults: [`apiWorkflow()`](api.md#apiworkflow-function).*

Run a deployed coded API workflow as a serverless Orchestrator job.

Signature: `apiWorkflow({ key, name, folderPath, inputs?, returns? })`.

```ts
.step('age', apiWorkflow({ key: workflowKey,
  name: 'NameToAge', folderPath: 'Shared',
  inputs: { name: input('name') }, returns: { age: 'integer' } }))
```

## Tenant contract

The workflow key, name, and folder must describe one deployed resource. Confirm
its actual input/output names and casing from the tenant. See
[Orchestrator Processes](or-processes.md) and use the `Api` process type for the
shared, pagination-safe resource-discovery procedure.

`.onError(...)` is supported on API workflow steps. Choose a handler only when
the scenario wants recovery; otherwise a faulted job may need to fault the Flow.

## Evidence boundary

Replay uses the authored contract. Live evidence should identify the real job,
its input arguments, completion status, and returned output. Job completion does
not by itself prove the coded workflow's business result is correct.
