# API Workflow

*Exact signatures, fields, and defaults: `apiWorkflow()`.*

Run a coded API workflow, deployed or a sibling in the same solution, as a
serverless Orchestrator job.

Signature: `apiWorkflow({ key, name, folderPath, inputs?, returns? })`, or
`apiWorkflow({ key, name, location: 'in-solution', projectId, inputs?, returns? })`
for an API workflow in the same solution (see [In the same solution](#in-the-same-solution)).

```ts
.step('age', apiWorkflow({ key: workflowKey,
  name: 'NameToAge', folderPath: 'Shared',
  inputs: { name: input('name') }, returns: { age: 'integer' } }))
```

## At a glance

Run a coded API workflow and wait for its job result.

Published workflow: confirm identity and exact argument casing on the tenant.
In-solution sibling: read them from the sibling project
([In the same solution](#in-the-same-solution)). `.onError(...)` is supported.

**Finding the key: [`or-processes.md`](or-processes.md)**

## Tenant contract

For a published workflow, the key, name, and folder must describe one deployed
resource. Confirm its actual input/output names and casing from the tenant. See
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

- **Or name the sibling by project:** `apiWorkflow({ location: 'in-solution', project: '<ApiWorkflowProject>', inputs, returns })`. See
  [agent.md](agent.md#name-an-in-solution-sibling-by-project) for what it
  fills in, what it refuses, and when to fall back to the ids below.
- **Where the two ids come from.** Same recipe as an in-solution function
  ([published-function.md](published-function.md#in-the-same-solution)), with
  `process/api/` in place of `process/function/`:
  `resources/solution_folder/process/api/<ApiWorkflowProject>.json`,
  `resource.key` → `key`, `resource.projectKey` → `projectId`. Never invent
  either.
- **`inputs` and `returns`** come from the sibling's `Workflow.json`:
  `input.schema.document.properties` and `output.schema.document.properties`,
  each field's `type`. Its `entry-points.json` `input`/`output` may be `null`,
  so do not read them there. The sibling is not on the tenant yet; do not look
  it up there.
- `check` warns on an in-solution step with no `projectId`
  (`APIWF_LOCAL_NO_PROJECT_ID`; the call resolves by `key`, so a decompiled
  step without one is fine as is), and refuses a `projectId` that is not a GUID
  (`APIWF_LOCAL_PROJECT_ID_NOT_GUID`) and a `folderPath` beside
  `location: 'in-solution'` (`APIWF_LOCAL_HAS_FOLDER`): the in-solution
  binding's folder is `''`, filled in at deploy.
  If `check` reports `APIWF_LOCAL_NO_PROJECT_ID` as an error (an older SDK),
  add `projectId` from `resource.projectKey`.
  Still set `projectId` on a step you author: Studio Web's Run node reads it
  to deploy the sibling first.
- A decompiled in-solution step (folder `''`) comes back as
  `location: 'in-solution'`. Keep it that way when editing; never add a
  `folderPath`.

Needs `@uipath/maestro-builder-sdk` 6.71.1 or later: check that
`dist/nodes/process/flow/spec.d.ts` of the SDK copy in use declares `projectId`
on `ApiWorkflowInputs`. An older SDK has no `location` on `apiWorkflow()`:
`check` reports `APIWF_NO_FOLDER`, but `compile` alone (6.64.0 on, it no longer
runs `check`) exits 0 and writes a binding keyed `undefined.<name>`. On an older
SDK, report the version instead of compiling the in-solution form.

## Evidence boundary

Replay uses the authored contract. Live evidence should identify the real job,
its input arguments, completion status, and returned output. Job completion does
not by itself prove the coded workflow's business result is correct.
