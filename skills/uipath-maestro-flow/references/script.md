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

- The function is never called; its body becomes the script exactly as written. Parameter one is runtime `$vars`, parameter two is `$metadata` ([below](#reading-the-instance-metadata)); name them accordingly, though other names are renamed. Parameters bind by position, so `($metadata) => …` is refused.
- Read parameters only with dots (`$vars.start.output.amount`). Destructuring, aliases (`const v = $vars`), bracket/optional access (`$vars['start']`, `$vars?.start`), and passing `$vars` to a helper are refused because `check` cannot see hidden step reads.
<!--skill-flavor:script-function-returns-check:start-->
- `returns` is the `.flow` declaration and is checked against the function’s return; `compile` does not type-check. With a workspace copy, run `npm install --save-dev @uipath/maestro-builder-sdk typescript`, then run `npx tsc --noEmit --strict --module nodenext --moduleResolution nodenext --skipLibCheck <file>.flow.ts`. A global SDK copy checks nothing; match fields manually. Without `returns`, the body’s type is inferred as for a string body.
<!--skill-flavor:script-function-returns-check:end-->
- The function may read only what [the runtime](#the-javascript-runtime) provides. Module constants/imports and module helpers named like runtime globals (such as `parseInt`) are refused; errors name the function (for example, `script(normalize) cannot be a script: it reads LIMIT, …`). Move values inside, or declare them with `.var()` and read `$vars.<name>`. Pass a named or inline function from a `.ts` file; `script(h.check)` and wrappers are refused because they cannot be checked.
- Refused with a message naming the function: `async`, generators, more than two parameters (more than one on an SDK older than 6.72.0, which lacks [the metadata parameter](#reading-the-instance-metadata)), default/rest parameters, `this` or `arguments` outside a nested function, a reference to the function’s own name, and a `var` or function declaration reusing a parameter name.
- With an SDK containing `dist/script-globals.d.ts`, also refuse top-level declaration or assignment of `console`, `uipath`, `aggregate`, `_aggregate`, or `_pipe`, and unsupported members such as `crypto.getRandomValues` or `console.table` (each fails at runtime; see [the runtime](#the-javascript-runtime)).
- A script function may read `console`, but not `uipath`, `aggregate`, `_aggregate`, or `_pipe`; these undocumented engine helpers are refused by `compile`.

To type-check `randomUUID`, `btoa`, or `atob`, add `/// <reference types="@uipath/maestro-builder-sdk/script-globals" />` when the SDK has `dist/script-globals.d.ts`; older SDKs refuse those names. Do not import an implementation: the engine provides them and `compile` refuses module names. The reference does not declare `crypto`; `crypto.randomUUID()` needs `@types/node` or the DOM library, or call bare `randomUUID()`.

<!--skill-flavor:script-function-sdk-version:start-->
The function form requires `@uipath/maestro-builder-sdk` 6.57.0 or later. Check that the active SDK’s `dist/api-index.md` lists `ScriptValue`. An older SDK fails with `compile: Cannot read properties of undefined (reading 'matchAll')`. Upgrade by running `npm install @uipath/maestro-builder-sdk@latest` in a workspace with its own `node_modules` copy (used before the global copy), or run `npm install -g @uipath/maestro-builder-sdk@latest`; otherwise use `script({ code })`.
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

Those five keys are all the engine sets. `check` warns `UNKNOWN_METADATA_KEY` for any other key, including misspellings, and suggests the correct key. A case may add keys; retain such reads, leave the warning, and widen the parameter: `$metadata: FlowMetadata & { Region?: string }`. Decompile instead uses `FlowMetadata & Record<string, any>`; the forms are interchangeable.

<!--skill-flavor:script-function-metadata-sdk-version:start-->
The metadata parameter requires `@uipath/maestro-builder-sdk` 6.72.0 or later. Check that the active SDK’s `dist/api-index.md` lists `FlowMetadata`. Older versions refuse two parameters and any `$metadata` read. Upgrade as above, or read `$metadata` from `script({ code })`.
<!--skill-flavor:script-function-metadata-sdk-version:end-->

## The JavaScript runtime

A script has modern syntax (`?.`, `??`, arrow functions), language built-ins, `console`, and engine extras: `btoa` and `atob` (UTF-8, unlike Node/browser Latin-1), `randomUUID()`, and `crypto.randomUUID()`. It has no `require`, `fetch`, Luxon `DateTime`, moment, lodash, `Intl`, `URL`, `TextEncoder`, `Buffer`, `structuredClone`, or other `crypto` member; these read `undefined` at runtime. Rewrite code ported from Node.js or a low-code code step accordingly.

`console` only has `debug`, `error`, `info`, `log`, and `warn`, all no-ops. Other methods such as `console.table` and `console.assert` are undefined and calling them fails. `toLocaleDateString` always returns long English regardless of locale/options; format dates from `getUTC…` parts.

The engine declares `console`, `uipath`, `aggregate`, `_aggregate`, and `_pipe` with `const` before execution. Do not top-level-declare (`const`, `let`, `var`, `function`, or `class`) or assign them: execution fails with `Identifier '…' has already been declared` or `Assignment to constant variable.` A nested block/function may own `let`, `const`, `function`, or `class`, and a nested function may own `var`; a plain-block `var` hoists and fails. Assigning these names anywhere fails unless an in-scope own declaration exists.

`flow validate` uses the ES2020 library and warns `EXPRESSION_DIAGNOSTIC` for later members such as `replaceAll`, although runtime executes them. Use `replace` with a global regular expression (`s.replace(/-/g, '+')`). It also warns `EXPRESSION_DIAGNOSTIC Cannot find name 'randomUUID'` and `Cannot find name 'crypto'`; these are expected because the library omits them, while runtime provides them. Leave the script unchanged; the flow remains `Valid`.