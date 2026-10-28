# Published function

*Exact signatures, fields, and defaults: `publishedFunction()`.*

A **Function** is a small, single-purpose unit of code deployed to Orchestrator
as its own resource. `publishedFunction()` invokes one as a single step
(`uipath.core.function.<key>`, dispatched as
`Orchestrator.ExecuteFunctionAsync`).

Signature: `publishedFunction({ key, name, folderPath, inputs?, returns? })`, or
`publishedFunction({ key, name, location: 'in-solution', projectId, inputs?, returns? })`
for a coded function in the same solution (see [In the same solution](#in-the-same-solution)).

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

## In the same solution

A coded function that is a sibling project of the Flow, in the same solution,
is not published yet, so it has no folder. Write it with
`location: 'in-solution'` and `projectId` instead of `folderPath`:

```ts
.step('math', publishedFunction({
  key: '247b5eeb-ae51-4ab5-a5b2-c9ca64db3971',       // resource.key
  name: 'InvoiceMath',
  location: 'in-solution',
  projectId: '21c9a46f-dfd1-4a17-89e3-e86d315ea0fe', // resource.projectKey
  inputs: { invoice_amount: input('invoice_amount') },
  returns: { variance_pct: 'number', summary: 'string' },
}))
```

- **`key`** and **`projectId`** both come from the sibling's resource file,
  `resources/solution_folder/process/function/<project>.json`: `key` is
  `resource.key`, `projectId` is `resource.projectKey`. The same key is the
  suffix `uip maestro flow registry list --local` shows.
- **`returns`** comes from the sibling project's own `entry-points.json`:
  `entryPoints[0].output.properties`, each field's `type` (for example
  `InvoiceMath/entry-points.json`). The resource file's `spec.entryPoints`
  holds the same schema as a JSON string. The rule in
  [Declaring what it returns](#declaring-what-it-returns) still applies.
- `check` refuses an in-solution step with no `projectId`
  (`FUNCTION_LOCAL_NO_PROJECT_ID`), a `projectId` that is not a GUID
  (`FUNCTION_LOCAL_PROJECT_ID_NOT_GUID`), and a `folderPath` beside
  `location: 'in-solution'` (`FUNCTION_LOCAL_HAS_FOLDER`): the in-solution
  binding's folder is `''`, filled in at deploy.

Needs `@uipath/maestro-builder-sdk` 6.59.0 or later; an older SDK
has no `location` on `publishedFunction()` and refuses the step as having no
`folderPath` (`FUNCTION_NO_FOLDER`).

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
