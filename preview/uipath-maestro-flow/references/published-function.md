# Published function

*Exact signatures, fields, and defaults: [`publishedFunction()`](api.md#publishedfunction-function).*

A **Function** is a small, single-purpose unit of code deployed to Orchestrator
as its own resource. `publishedFunction()` invokes one as a single step
(`uipath.core.function.<key>`, dispatched as
`Orchestrator.ExecuteFunctionAsync`).

Signature: `publishedFunction({ key, name, folderPath, inputs?, returns? })`.

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
