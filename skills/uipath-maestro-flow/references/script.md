# Script

*Exact signatures, fields, and defaults: `script()`.*

Script runs inline JavaScript for a computation that has no first-class Flow
node. Upstream data is available through `$vars`; the result is read with
`out(step, path?)`.

A flow input is read off the trigger, `$vars.start.output.<name>` (what
`input('<name>')` lowers to); a `.var()` is read as `$vars.<name>`.

```ts
.step('normalize', script({ code: `
  const amount = Number($vars.start.output.amount);
  return { amount, valid: Number.isFinite(amount) };
` }))
```

Use the named first-class node when the scenario needs a connector or HTTP for
any external data or API call, Transform, Delay, or another product capability,
whether or not the request names the node. A script is appropriate for
local calculation, reshaping that needs arbitrary code, or computing a value
before passing a bare reference to another node.

Return an object literal for named fields and read them with `out('parse', 'tag')`;
read a scalar return with `out('parse')`.

## At a glance

Run inline JavaScript for computation that is not a first-class Flow node.

Signature: `script({ code: string })`, or `script(fn, { returns })` for [a function](#writing-the-script-as-a-function); read the result with `out(step, path?)`.

Use a first-class action when the scenario names one; use script for computation.

## What the step publishes

The node's own definition can only declare a generic output (`object` on
1.0.0, `any` on 1.1) — a node TYPE cannot know what a particular body returns —
so the designer would type every script read as `Record<string, any>` and
reject mapping one into a `string` flow output. The compiler therefore reads the body and declares what it plainly
returns, so this needs nothing from you:

```ts
.step('flag', script({ code: 'return "pending-approval";' }))
.return({ status: out('flag') })          // status: types.string — fine
```

It types, it does not enumerate: an object return stays the open object rather
than gaining a field list, and nothing is declared unless every `return` in the
body agrees. A body whose return type is not written down — a runtime read, a
call — declares nothing, which is where `returns` comes in:

```ts
.step('policyLimit', script({
  code: 'return $vars.fetchPolicy.output.body.limit;',
  returns: 'number',
}))
```

`returns` always wins over the body, and takes either a type
(`'string' | 'number' | 'boolean' | 'object' | 'array' | 'any'`) or, to name the fields
of an object return, a map — `returns: { total: 'number', currency: 'string' }`.
`'any'` is valid only as the top-level `returns` of a `script@1.1` step — not
on 1.0.0 and never as a field type (`check` reports `SCRIPT_RETURNS_UNKNOWN_TYPE`).
It keeps the output untyped even when the body plainly returns one type.

## Writing the script as a function

A body longer than a line is easier to get right as a TypeScript function: pass the function instead of a string, and the editor and tsc check the body like the rest of the `.flow.ts`.

```ts
import { script, type FlowVars } from '@uipath/maestro-builder-sdk';

// … flow(…) chain
  .step('normalize', script(normalize, { returns: { amount: 'number', valid: 'boolean' } }))

function normalize(vars: FlowVars) {
  const amount = Number(vars.start.output.amount);
  return { amount, valid: Number.isFinite(amount) };
}
```

- The function is never called. Its body, exactly as written, becomes the script, and its parameter is renamed to the runtime's `$vars`. Name the parameter `$vars` and nothing is renamed.
- Read the parameter only with dots (`vars.start.output.amount`). A destructured parameter, an alias (`const v = vars`), `vars['start']`, `vars?.start`, or passing `vars` to a helper is refused, because a step read hidden that way is invisible to `check`.
- `returns` is what the `.flow` declares, and its type is checked against the function's return: `returns: { amount: 'string' }` over the function above is a type error. `compile` does not type-check, so the error shows only where tsc runs: with a workspace copy (`npm install --save-dev @uipath/maestro-builder-sdk typescript`), `npx tsc --noEmit --strict --module nodenext --moduleResolution nodenext --skipLibCheck <file>.flow.ts` reports it. With only the global SDK copy nothing checks it, so match the `returns` fields to what the function returns by hand. Without `returns`, the body's type is inferred as for a string body.
- The function reads only what [the runtime](#the-javascript-runtime) has. A value from outside the function is refused: a module constant or an import throws when the flow loads (`script(normalize) cannot be a script: it reads LIMIT, …`), and so does a module helper named like a runtime global (`parseInt`), which `compile` and `check` refuse. Move the value inside the function, or declare it with `.var()` and read `vars.<name>`.
- Also refused, with a message naming the function: `async`, generators, more than one parameter, a default or rest parameter, `this` or `arguments` outside a nested function, a reference to the function's own name, and a `var` or function declaration that reuses the parameter's name.

The function form needs an SDK whose `dist/api-index.md` (in the SDK copy in use) lists `ScriptValue`. An older SDK fails on a function with `compile: Cannot read properties of undefined (reading 'matchAll')`. Upgrade the copy in use: `npm install @uipath/maestro-builder-sdk@latest` in a workspace that has its own `node_modules` copy (it is used before the global one), else `npm install -g @uipath/maestro-builder-sdk@latest`; or write `script({ code })`.

## The JavaScript runtime

A script gets modern syntax (`?.`, `??`, arrow functions), the
language's built-in objects and `console`, and nothing more. `require`,
`fetch`, Luxon's `DateTime`, moment, lodash, `Intl`, `URL`, `TextEncoder`,
`Buffer` and `structuredClone` all read `undefined` in a real run. A body ported
from a runtime that has them (a Node.js script, a low-code platform's code step)
is rewritten without them. `toLocaleDateString` returns the long English form
whatever locale and options it is given, so build a formatted date from its
`getUTC…` parts.

`flow validate` types scripts against the ES2020 library, so it warns
`EXPRESSION_DIAGNOSTIC` on later members such as `replaceAll`, which the run
executes. Write `replace` with a global regular expression
(`s.replace(/-/g, '+')`) instead.
