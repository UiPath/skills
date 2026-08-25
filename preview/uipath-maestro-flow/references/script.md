# Script

*Exact signatures, fields, and defaults: [`script()`](api.md#script-function).*

Script runs inline JavaScript for a computation that has no first-class Flow
node. Upstream data is available through `$vars`; the result is read with
`out(step, path?)`.

```ts
.step('normalize', script({ code: `
  const amount = Number($vars.amount);
  return { amount, valid: Number.isFinite(amount) };
` }))
```

Use the named first-class node when the scenario asks for HTTP, Transform,
Delay, a connector, or another product capability. A script is appropriate for
local calculation, reshaping that needs arbitrary code, or computing a value
before passing a bare reference to another node.

Return an object literal for named fields and read them with `out('parse', 'tag')`;
read a scalar return with `out('parse')`.

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
