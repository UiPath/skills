# API Workflow

*Exact signatures, fields, and defaults: `apiWorkflow()`.*

Run a deployed coded API workflow as a serverless Orchestrator job.

Signature: `apiWorkflow({ key, name, folderPath, inputs?, returns? })`, or
`apiWorkflow({ key, name, location: 'in-solution', projectId, inputs?, returns? })`
for an API workflow in the same solution (see [In the same solution](#in-the-same-solution)).

```ts
.step('age', apiWorkflow({ key: workflowKey,
  name: 'NameToAge', folderPath: 'Shared',
  inputs: { name: input('name') }, returns: { age: 'integer' } }))
```

## At a glance

Run a deployed coded API workflow and wait for its job result.

Confirm identity and exact argument casing on the tenant; `.onError(...)` is supported.

**Finding the key: [`or-processes.md`](or-processes.md)**

## Tenant contract

The workflow key, name, and folder must describe one deployed resource. Confirm
its actual input/output names and casing from the tenant. See
[Orchestrator Processes](or-processes.md) and use the `Api` process type for the
shared, pagination-safe resource-discovery procedure.

`.onError(...)` is supported on API workflow steps. Choose a handler only when
the scenario wants recovery; otherwise a faulted job may need to fault the Flow.

## In the same solution

An API workflow that is a sibling project of the Flow, in the same solution, is
not published yet, so it has no folder. Write it with `location: 'in-solution'`
and `projectId` instead of `folderPath`:

```ts
.step('notify', apiWorkflow({
  key: localResourceKey,
  name: '<ApiWorkflowProject>',
  location: 'in-solution',
  projectId: localProjectKey,
  inputs: { name: input('name') },
}))
```

- **Where the two ids come from.** The same way as for an in-solution function
  ([published-function.md](published-function.md#in-the-same-solution)), from
  `resources/solution_folder/process/api/<ApiWorkflowProject>.json`:
  `resource.key` → `key`, `resource.projectKey` → `projectId`. Never invent
  either.
- `check` refuses an in-solution step with no `projectId`
  (`APIWF_LOCAL_NO_PROJECT_ID`), a `projectId` that is not a GUID
  (`APIWF_LOCAL_PROJECT_ID_NOT_GUID`), and a `folderPath` beside
  `location: 'in-solution'` (`APIWF_LOCAL_HAS_FOLDER`): the in-solution
  binding's folder is `''`, filled in at deploy.

Needs `@uipath/maestro-builder-sdk` SDK_VERSION or later; an older SDK has no
`location` on `apiWorkflow()` and refuses the step as having no `folderPath`
(`APIWF_NO_FOLDER`).

## Evidence boundary

Replay uses the authored contract. Live evidence should identify the real job,
its input arguments, completion status, and returned output. Job completion does
not by itself prove the coded workflow's business result is correct.
