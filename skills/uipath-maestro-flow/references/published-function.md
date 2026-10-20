# Published function

*Exact signatures, fields, and defaults: `publishedFunction()`.*

A **Function** is a small, single-purpose unit of code deployed to Orchestrator
as its own resource. `publishedFunction()` invokes one as a single step
(`uipath.core.function.<key>`, dispatched as
`Orchestrator.ExecuteFunctionAsync`).

Signature: `publishedFunction({ key, name, folderPath?, location?, projectId?, inputs?, returns? })`.
`folderPath` is required for a published function; a sibling Function project of the same solution takes `location: 'in-solution'` and `projectId` instead ([below](#in-solution-sibling)).

```ts
.step('echo', publishedFunction({
  key: '7059bdb5-fdd7-4e13-9d7b-1748aaeb129d',
  name: 'acme-echo',
  folderPath: 'Shared/acme-echo',
  inputs: { message: input('message') },
  returns: { echoed: 'string' },
}))
.step('relay', script({ code: 'return $vars.echo.output.echoed;' }))
```

## At a glance

Run a deployed Orchestrator **Function** — a small unit of code published as its
own resource — as one step.

```ts
.step('echo', publishedFunction({ key: functionKey,
  name: 'acme-echo', folderPath: 'Shared/acme-echo',
  inputs: { message: input('message') }, returns: { echoed: 'string' } }))
```

A function is usually deployed into a folder of its OWN name — read `folderPath`
from the tenant rather than assuming `'Shared'`, since the binding's resourceKey
is `<folderPath>.<name>`.

## Identity

Three fields, none of them derivable:

- **`key`** — the function's GUID; it becomes the node type's suffix, so a wrong
  one emits a node the tenant cannot resolve. Find it with
  `uip maestro flow registry search "uipath.core.function"` (after
  `registry pull --force`, since registry reads are cached).
- **`name`** — the function's own name in Orchestrator.
- **`folderPath`** — the folder it is deployed in. **A function is usually
  deployed into a folder of its OWN name** (`'Shared/acme-echo'`, not
  `'Shared'`). The binding's `resourceKey` is `<folderPath>.<name>`, so
  assuming `'Shared'` points the dispatch at nothing while still validating.

Two steps on the same function share ONE binding pair, exactly as the other
published families do.

## In-solution sibling

To call a Function project that sits in the SAME solution as the Flow (not a
deployed function), set `location: 'in-solution'` and `projectId`, and omit
`folderPath`:

```ts
.step('readFile', publishedFunction({ key: localResourceKey, name: '<FunctionProject>',
  location: 'in-solution', projectId: localProjectKey,
  inputs: { file: input('documentFile') }, returns: { text: 'string' } }))
```

- **Where the two ids come from.** `uip solution projects add <FunctionProject>`
  writes `resources/solution_folder/process/function/<FunctionProject>.json`:
  `resource.key` → `key`, `resource.projectKey` → `projectId`.
  `uip maestro flow registry list --local` from the Flow project shows the same
  key as the node type's suffix. Never invent either.
- **No `folderPath`.** The sibling has no folder until the solution is deployed.
- **One function per project.** The resource is per project, and the step names
  no entry point, so give each function the Flow calls its own project.
- **Run it deployed.** `uip maestro flow debug` does not run a JS/TS Function
  sibling yet: Studio Web's import drops the project, and the step faults with
  `170007` (process not found). Pack, publish and deploy the solution, then
  `uip maestro flow process run`.

`check` refuses the wrong shapes: `FUNCTION_LOCAL_NO_PROJECT_ID` (no
`projectId`), `FUNCTION_LOCAL_PROJECT_ID_NOT_GUID` (`projectId` is not the
project GUID), `FUNCTION_LOCAL_HAS_FOLDER` (`folderPath` set as well; drop it,
or drop `location` to call the published copy). `FUNCTION_NO_FOLDER` applies to
published steps only.

## Declaring what it returns

`returns` is required if anything reads the step's output. The function's real
output arguments live on the tenant and authoring is offline, so an undeclared
read is rejected (`FUNCTION_READ_WITHOUT_RETURNS`) — nothing here could tell a
real field from a typo. `registry get uipath.core.function.<key>` shows what the
platform synthesizes for a deployed one.

## Which family to reach for

| The deployed thing | Factory |
| --- | --- |
| A Function (a unit of code, its own resource) | `publishedFunction()` |
| A coded API workflow | `apiWorkflow()` |
| An RPA process | `rpaWorkflow()` |
| A Maestro process orchestration | `agenticProcess()` |

They share one emit path and differ only in service type and binding subtype, so
picking the wrong one produces a flow that validates and dispatches nothing.
Match the family the scenario names.

## Evidence boundary

Offline `validate` proves the node type, the binding pair and the declared
output schema. That the function exists, accepts those arguments, and returns
those fields is platform evidence — `.onError(...)` is supported for the
dispatch failing.
