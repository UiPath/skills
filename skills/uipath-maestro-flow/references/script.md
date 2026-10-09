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

Signature: `script({ code: string })`; read the result with `out(step, path?)`.

Use a first-class action when the scenario names one; use script for computation.

## What the step publishes

The node's own definition can only say `output: {type: 'object'}` — a node TYPE
cannot know what a particular body returns — so the designer would type every
script read as `Record<string, any>` and reject mapping one into a `string` flow
output. The compiler therefore reads the body and declares what it plainly
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
(`'string' | 'number' | 'boolean' | 'object' | 'array'`) or, to name the fields
of an object return, a map — `returns: { total: 'number', currency: 'string' }`.

## The JavaScript runtime

A script gets modern syntax (`?.`, `??`, arrow functions, `replaceAll`), the
language's built-in objects and `console`, and nothing more. `require`,
`fetch`, Luxon's `DateTime`, moment, lodash, `Intl`, `URL`, `TextEncoder`,
`Buffer` and `structuredClone` all read `undefined` in a real run. A body ported
from a runtime that has them (a Node.js script, a low-code platform's code step)
is rewritten without them. `toLocaleDateString` returns the long English form
whatever locale and options it is given, so build a formatted date from its
`getUTC…` parts.
