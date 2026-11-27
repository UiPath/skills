# Script

*Exact signatures, fields, and defaults: `script()`.*

`script` runs inline JavaScript without a first-class Flow node. Read upstream data through `$vars`; read results with `out(step, path?)`. Flow inputs are `$vars.start.output.<name>` (what `input('<name>')` lowers to), and `.var()` values are `$vars.<name>`.

Use the named first-class node whenever the scenario needs a connector or HTTP for external data or an API call, Transform, Delay, or another product capability, whether or not the request names it. Use script for local calculation, reshaping that needs arbitrary code, or computing a value before passing a bare reference to another node. Return an object literal for named fields (`out('parse', 'tag')`) or a scalar (`out('parse')`).

A script that reads agent or LLM output must not throw on its format, style, or wording (markdown characters, length, phrasing): output varies per run, and one throw faults the whole flow and loses a correct result. Enforce format in the agent prompt and output schema; normalise the text or pass it through. Throw only when a required contract field is missing or invalid.

## At a glance

Run inline JavaScript for computation that is not a first-class Flow node. Signatures are `script({ code: string })` and `script(fn, { returns })` for [a function](#writing-the-script-as-a-function); read results with `out(step, path?)`. Use a first-class action when the scenario names one; use script for computation.

## What the step publishes

A node TYPE declares only a generic output (`object` on 1.0.0, `any` on 1.1), so the designer would reject mapping a script read into a `string` flow output. The compiler reads the body and declares an evident return type; typing does not enumerate fields, so an object remains open, and nothing is declared unless every `return` agrees. A body returning a runtime read or a call declares nothing; provide `returns`:

```ts
.step('policyLimit', script({
  code: 'return $vars.fetchPolicy.output.body.limit;',
  returns: 'number',
}))
```

`returns` always wins over the body. It accepts `'string' | 'number' | 'boolean' | 'object' | 'array' | 'any'`, or an object-field map such as `returns: { total: 'number', currency: 'string' }`. `'any'` is valid only as the top-level `returns` of a `script@1.1` step, never on 1.0.0 or as a field type (`check` reports `SCRIPT_RETURNS_UNKNOWN_TYPE`); it leaves the output untyped even when the body has one evident type.

## Writing the script as a function

For new scripts (the examples write every script this way), pass a TypeScript function so the editor and `tsc` check it. The string form remains necessary when a body splices an `out()` reference with `js`` ` or the SDK is older than 6.57.0.

```ts
import { script, type FlowVars } from '@uipath/maestro-builder-sdk';

// … flow(…) chain
  .step('normalize', script(normalize, { returns: { amount: 'number', valid: 'boolean' } }))
function normalize($vars: FlowVars) {
  const amount = Number($vars.start.output.amount);
  return { amount, valid: Number.isFinite(amount) };
}
```

- The function is never called: its body becomes the script exactly as written. Parameter one is runtime `$vars`; parameter two is `$metadata` ([below](#reading-the-instance-metadata)). Name them `$vars` and `$metadata` to avoid renaming; other names are renamed. Parameters bind by position, so take them in that order: a parameter named like the other one (`($metadata) => …`) is refused.
- Read parameters only with dots (`$vars.start.output.amount`). Destructuring, aliases (`const v = $vars`), `$vars['start']`, `$vars?.start`, and passing `$vars` to a helper are refused because `check` cannot see the step read.
<!--skill-flavor:script-function-returns-check:start-->
- `returns` is the `.flow` declaration and is checked against the function return; `returns: { amount: 'string' }` for the example is a type error. `compile` does not type-check. In a workspace copy, run `npm install --save-dev @uipath/maestro-builder-sdk typescript`, then run `npx tsc --noEmit --strict --module nodenext --moduleResolution nodenext --skipLibCheck <file>.flow.ts`; with only the global SDK copy, nothing checks it, so match `returns` fields by hand. Without `returns`, the body's type is inferred as for a string body.
<!--skill-flavor:script-function-returns-check:end-->
- The function may read only [the runtime](#the-javascript-runtime). External values, module constants, imports, and module helpers named like runtime globals (such as `parseInt`) are refused: each throws when the flow loads (`script(normalize) cannot be a script: it reads LIMIT, …`), and `compile` and `check` also refuse such a helper. Move values inside the function or declare them with `.var()` and read `$vars.<name>`. Pass the function by name or inline from a `.ts` file; `compile` and `check` refuse any other shape (`script(h.check)`, a wrapper around `script`).
- Refused with a function-naming message: `async`, generators, more than two parameters (more than one on an SDK older than 6.72.0, which lacks [the metadata parameter](#reading-the-instance-metadata)), default or rest parameters, `this` or `arguments` outside a nested function, a reference to the function's own name, and a `var` or function declaration reusing a parameter name.
- With an SDK containing `dist/script-globals.d.ts`, these are also refused, each because it fails in the run: top-level declaration or assignment of `console`, `uipath`, `aggregate`, `_aggregate`, or `_pipe`, and a `crypto` or `console` member the engine lacks (`crypto.getRandomValues`, `console.table`).
- A script function may read `console`, but not `uipath`, `aggregate`, `_aggregate`, or `_pipe`; these undocumented helpers make `compile` refuse the function.

To type-check a function using `randomUUID`, `btoa`, or `atob`, add `/// <reference types="@uipath/maestro-builder-sdk/script-globals" />` when the SDK has `dist/script-globals.d.ts`; older SDKs refuse those names. Do not import an implementation: the engine provides them and `compile` refuses module reads. The reference does not declare `crypto`; `crypto.randomUUID()` requires `@types/node` or the DOM library, or call bare `randomUUID()`.

<!--skill-flavor:script-function-sdk-version:start-->
The function form requires `@uipath/maestro-builder-sdk` 6.57.0 or later. Check that the SDK copy's `dist/api-index.md` lists `ScriptValue`. An older SDK fails with `compile: Cannot read properties of undefined (reading 'matchAll')`. Upgrade it by running `npm install @uipath/maestro-builder-sdk@latest` in a workspace with its own `node_modules` copy (used before the global one); else run `npm install -g @uipath/maestro-builder-sdk@latest`; otherwise write `script({ code })`.
<!--skill-flavor:script-function-sdk-version:end-->

### Reading the instance metadata

A script can read `$metadata`: `InstanceId`, `FolderKey`, `ProcessKey`, `ExternalId` (the external id a case gives the instance; unset when no case started the flow), and `ElementCount` (the count for each element id). In a function, take it as the second `FlowMetadata` parameter. Name it `$metadata` or use another name, which is renamed; read the key after it only with a dot (`$metadata.InstanceId`, not `$metadata['InstanceId']`). After that key, bracket an element id that is not a JavaScript name: `$metadata.ElementCount?.['my-step']`.

`ElementCount` and `ExternalId` can be unset (`ElementCount` until its first count). Read through either with `?.`; strict `tsc` refuses plain `.` or `[…]`, and the run throws `TypeError` when the key is unset.

```ts
import { script, type FlowVars, type FlowMetadata } from '@uipath/maestro-builder-sdk';

// … flow(…) chain
  .step('tag', script(tag, { returns: 'string' }))

function tag($vars: FlowVars, $metadata: FlowMetadata) {
  return $metadata.InstanceId + ':' + $vars.start.output.id;
}
```

These five keys are all the engine sets. `check` warns `UNKNOWN_METADATA_KEY` for any other key, including misspellings (`$metadata.instanceId` reads `undefined`); the suggestion names the correct key. A case that starts the flow may set its own instance keys. When the flow is meant to read one of those, keep the read and warning, and widen the parameter type: `$metadata: FlowMetadata & { Region?: string }`. Decompile instead widens it to `FlowMetadata & Record<string, any>`; these forms are interchangeable, so leave either.

<!--skill-flavor:script-function-metadata-sdk-version:start-->
The metadata parameter requires `@uipath/maestro-builder-sdk` 6.72.0 or later. Check that the SDK copy's `dist/api-index.md` lists `FlowMetadata`. An older SDK refuses two parameters and any function reading `$metadata`. Upgrade as above, or read `$metadata` from `script({ code })`.
<!--skill-flavor:script-function-metadata-sdk-version:end-->

## The JavaScript runtime

A script has modern syntax (`?.`, `??`, arrow functions), built-in objects, `console`, and exactly four provided extras: `btoa`, `atob` (UTF-8, unlike Node/browser Latin-1), `randomUUID()`, and `crypto.randomUUID()`. Nothing else is provided: `require`, `fetch`, Luxon's `DateTime`, moment, lodash, `Intl`, `URL`, `TextEncoder`, `Buffer`, and `structuredClone` are `undefined` at runtime, and `crypto` has no other member. Rewrite Node or low-code code-step code accordingly.

`console` only has `debug`, `error`, `info`, `log`, and `warn`, all no-ops. Other methods such as `console.table` and `console.assert` are undefined and calling them fails the run. The execution envelope is ~64 MB; exceeding it fails with `Script has allocated <n> but is limited to 67108864` (incident 300501, no variable named). Copying a large `$vars` value counts, including connector output with attachment `contentBytes`; copy only needed fields. `toLocaleDateString` always returns the long English form regardless of locale/options; format dates from `getUTC…` parts.

The engine declares `console`, `uipath`, `aggregate`, `_aggregate`, and `_pipe` with `const` before the body. Do not declare any at top level with `const`, `let`, `var`, `function`, or `class`, or assign to it: the run fails with `Identifier '…' has already been declared` or `Assignment to constant variable.` A `let`, `const`, `function`, or `class` in a nested block/function, and a `var` inside a nested function, is your own. A `var` in a plain block hoists and fails; assigning one of these names anywhere also fails unless your own declaration is in scope.

`flow validate` types scripts against ES2020 and warns `EXPRESSION_DIAGNOSTIC` for later members such as `replaceAll`, although the run executes them. Use `replace` with a global regular expression (`s.replace(/-/g, '+')`). It also warns `EXPRESSION_DIAGNOSTIC Cannot find name 'randomUUID'` and `Cannot find name 'crypto'` because its library does not declare them (`btoa` and `atob` are known). The `randomUUID` and `crypto` warnings are expected: the flow remains `Valid`, the run provides the names, and the script should remain unchanged.

The Studio Web canvas also type-checks each script body as TypeScript and marks a type error red, although the run executes the body as JavaScript. The common case is an object built up after an empty literal: `const t = {}; t.field = 1` is marked `Property 'field' does not exist on type '{}'`. `flow validate` reports it as the warning `EXPRESSION_DIAGNOSTIC`, and `flow check` as the warning `SCRIPT_TYPE_DIAGNOSTIC` (an SDK that includes builder-sdk#2100; an older `check` reports nothing). Build the object in one literal (`const t = { field: 1 }`), or add fields with a spread (`t = { ...t, field: 1 }` on a `let`). A type annotation does not help: in a `script({ code })` string, `const t: any = {}` fails the run; in a function, compile erases it, so the canvas still sees `const t = {}`.
