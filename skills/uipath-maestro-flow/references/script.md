# Script

*Exact signatures, fields, and defaults: `script()`.*

`script` runs inline JavaScript for computation without a first-class Flow node. Read upstream data through `$vars`; read results with `out(step, path?)`. Flow inputs are `$vars.start.output.<name>` (the lowering of `input('<name>')`); `.var()` values are `$vars.<name>`.

Use the named first-class node when the scenario needs a connector or HTTP for external data/API calls, Transform, Delay, or another product capability, whether or not requested. Use script for local calculation, arbitrary-code reshaping, or computing a value before passing a bare reference to another node. Return an object for named fields (`out('parse', 'tag')`) or a scalar (`out('parse')`). Use `script({ code: string })`, or `script(fn, { returns })` for [a function](#writing-the-script-as-a-function).

## What the step publishes

A node TYPE cannot know a particular body’s output: its generic output is `object` on 1.0.0 and `any` on 1.1. The compiler reads the body and declares what it plainly returns. Object returns remain open objects, not field lists, and nothing is declared unless every `return` agrees. Runtime reads and calls declare nothing, so use `returns` when needed.

`returns` overrides the body and accepts `'string' | 'number' | 'boolean' | 'object' | 'array' | 'any'`, or an object-field map such as `returns: { total: 'number', currency: 'string' }`. `'any'` is valid only as the top-level `returns` of a `script@1.1` step—not on 1.0.0 and never as a field type (`check` reports `SCRIPT_RETURNS_UNKNOWN_TYPE`). It leaves the output untyped even when the body plainly returns one type.

## Writing the script as a function

For bodies longer than a line, prefer a TypeScript function so the editor and `tsc` check it like the rest of `.flow.ts`. Prefer it for new scripts; the examples write every script this way. The string form remains necessary for a body splicing an `out()` reference with `js`` ` and for an SDK older than 6.57.0.

```ts
import { script, type FlowVars } from '@uipath/maestro-builder-sdk';

// … flow(…) chain
  .step('normalize', script(normalize, { returns: { amount: 'number', valid: 'boolean' } }))

function normalize($vars: FlowVars) {
  const amount = Number($vars.start.output.amount);
  return { amount, valid: Number.isFinite(amount) };
}
```

- The function is never called. Its body, exactly as written, becomes the script. Its parameter stands for the runtime's `$vars`, and a second parameter for the instance metadata, `$metadata` ([below](#reading-the-instance-metadata)). Name them `$vars` and `$metadata`, as the examples do: then nothing is renamed and the body reads exactly as it runs. Any other name works too, and is renamed to the runtime's name. Parameters bind by position, so take them in that order: a parameter named like the other one (`($metadata) => …`) is refused.
- Read parameters only with dots (`$vars.start.output.amount`). Destructuring, aliases (`const v = $vars`), bracket/optional access (`$vars['start']`, `$vars?.start`), and passing `$vars` to a helper are refused because `check` cannot see hidden step reads.
<!--skill-flavor:script-function-returns-check:start-->
- `returns` is what the `.flow` declares, and its type is checked against the function's return: `returns: { amount: 'string' }` over the function above is a type error. `compile` does not type-check, so the error shows only where tsc runs: with a workspace copy (`npm install --save-dev @uipath/maestro-builder-sdk typescript`), `npx tsc --noEmit --strict --module nodenext --moduleResolution nodenext --skipLibCheck <file>.flow.ts` reports it. With only the global SDK copy nothing checks it, so match the `returns` fields to what the function returns by hand. Without `returns`, the body's type is inferred as for a string body.
<!--skill-flavor:script-function-returns-check:end-->
- The function reads only what [the runtime](#the-javascript-runtime) has. A value from outside the function is refused: a module constant or an import throws when the flow loads (`script(normalize) cannot be a script: it reads LIMIT, …`), and so does a module helper named like a runtime global (`parseInt`), which `compile` and `check` refuse. Move the value inside the function, or declare it with `.var()` and read `$vars.<name>`. Pass the function to `script()` by name or inline, from a `.ts` file: `compile` and `check` refuse any other shape (`script(h.check)`, a wrapper around `script`), because they cannot check what it reads.
- Refused with a message naming the function: `async`, generators, more than two parameters (more than one on an SDK older than 6.72.0, which lacks [the metadata parameter](#reading-the-instance-metadata)), default/rest parameters, `this` or `arguments` outside a nested function, a reference to the function’s own name, and a `var` or function declaration reusing a parameter name.
- With an SDK copy that has `dist/script-globals.d.ts`, these are refused too, each of which fails in the run (see [the runtime](#the-javascript-runtime)): a top-level declaration of, or assignment to, `console`, `uipath`, `aggregate`, `_aggregate` or `_pipe`, and a member of `crypto` or `console` the engine's lacks (`crypto.getRandomValues`, `console.table`).
- A script function may read `console`, but not `uipath`, `aggregate`, `_aggregate`, or `_pipe`; these undocumented engine helpers are refused by `compile`.

To type-check `randomUUID`, `btoa`, or `atob`, add `/// <reference types="@uipath/maestro-builder-sdk/script-globals" />` when the SDK has `dist/script-globals.d.ts`; older SDKs refuse those names. Do not import an implementation: the engine provides them and `compile` refuses module names. The reference does not declare `crypto`; `crypto.randomUUID()` needs `@types/node` or the DOM library, or call bare `randomUUID()`.

<!--skill-flavor:script-function-sdk-version:start-->
The function form needs `@uipath/maestro-builder-sdk` 6.57.0 or later: check that `dist/api-index.md` of the SDK copy in use lists `ScriptValue`. An older SDK fails on a function with `compile: Cannot read properties of undefined (reading 'matchAll')`. Upgrade the copy in use: `npm install @uipath/maestro-builder-sdk@latest` in a workspace that has its own `node_modules` copy (it is used before the global one), else `npm install -g @uipath/maestro-builder-sdk@latest`; or write `script({ code })`.
<!--skill-flavor:script-function-sdk-version:end-->

### Reading the instance metadata

A script may read `$metadata`: `InstanceId`, `FolderKey`, `ProcessKey`, `ExternalId` (the case’s external id, unset without a case), and `ElementCount` (runs per element id). A function takes it as its second parameter, typed `FlowMetadata`; name it `$metadata` (other names are renamed) and read it only with dots, as the first (`$metadata.InstanceId`, not `$metadata['InstanceId']`). Only that first read needs the dot: for a non-JavaScript element id, use brackets after it: `$metadata.ElementCount?.['my-step']`.

`ElementCount` and `ExternalId` may be unset (`ElementCount` until first count); access them with `?.`. Strict `tsc` refuses plain `.` or `[…]` on either, and runtime access throws `TypeError` when unset.

```ts
import { script, type FlowVars, type FlowMetadata } from '@uipath/maestro-builder-sdk';

// … flow(…) chain
  .step('tag', script(tag, { returns: 'string' }))

function tag($vars: FlowVars, $metadata: FlowMetadata) {
  return $metadata.InstanceId + ':' + $vars.start.output.id;
}
```

Those five keys are all the engine sets, so `check` warns `UNKNOWN_METADATA_KEY` on a read of any other key, in a script or any other expression: a misspelled key (`$metadata.instanceId`) reads `undefined` in the run, and the warning's suggestion names the right one.
A case that starts the flow can set keys of its own on the instance.
When the flow is meant to read one of those, keep the read, leave the warning, and widen the parameter's type: `$metadata: FlowMetadata & { Region?: string }`.
Decompile widens it as `FlowMetadata & Record<string, any>` instead; the two are interchangeable, so leave whichever form is there.

<!--skill-flavor:script-function-metadata-sdk-version:start-->
The metadata parameter requires `@uipath/maestro-builder-sdk` 6.72.0 or later. Check that the active SDK’s `dist/api-index.md` lists `FlowMetadata`. Older versions refuse two parameters and any `$metadata` read. Upgrade as above, or read `$metadata` from `script({ code })`.
<!--skill-flavor:script-function-metadata-sdk-version:end-->

## The JavaScript runtime

A script has modern syntax (`?.`, `??`, arrow functions), language built-ins, `console`, and engine extras: `btoa` and `atob` (UTF-8, unlike Node/browser Latin-1), `randomUUID()`, and `crypto.randomUUID()`. It has no `require`, `fetch`, Luxon `DateTime`, moment, lodash, `Intl`, `URL`, `TextEncoder`, `Buffer`, `structuredClone`, or other `crypto` member; these read `undefined` at runtime. Rewrite code ported from Node.js or a low-code code step accordingly.

`console` only has `debug`, `error`, `info`, `log`, and `warn`, all no-ops. Other methods such as `console.table` and `console.assert` are undefined and calling them fails. The execution envelope is ~64 MB: a script that allocates more fails with `Script has allocated <n> but is limited to 67108864` (incident 300501, no variable named). Copying a large `$vars` value counts, such as a connector output carrying attachment `contentBytes`, so copy only the fields the script needs. `toLocaleDateString` always returns long English regardless of locale/options; format dates from `getUTC…` parts.

The engine declares `console`, `uipath`, `aggregate`, `_aggregate`, and `_pipe` with `const` before execution. Do not top-level-declare (`const`, `let`, `var`, `function`, or `class`) or assign them: execution fails with `Identifier '…' has already been declared` or `Assignment to constant variable.` A nested block/function may own `let`, `const`, `function`, or `class`, and a nested function may own `var`; a plain-block `var` hoists and fails. Assigning these names anywhere fails unless an in-scope own declaration exists.

`flow validate` uses the ES2020 library and warns `EXPRESSION_DIAGNOSTIC` for later members such as `replaceAll`, although runtime executes them. Use `replace` with a global regular expression (`s.replace(/-/g, '+')`). It also warns `EXPRESSION_DIAGNOSTIC Cannot find name 'randomUUID'` and `Cannot find name 'crypto'`; these are expected because the library omits them, while runtime provides them. Leave the script unchanged; the flow remains `Valid`.
