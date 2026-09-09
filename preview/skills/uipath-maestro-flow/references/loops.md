# Loops

Loop runs a body for every member of a collection.

Signature: `.loop(name, collection, bodyFn)`.

```ts
.loop('eachOrder', input('orders'), (body) => body
  .step('handle', script({ code:
    'return { id: $vars.eachOrder.currentItem.id };' })))
```

The SDK does not expose mutation of a Flow variable on each iteration. Keep
per-item dispatch and decisions in the body. If work after the loop needs a
summary, compute it from data already available outside the loop or use a
dedicated step whose contract supplies that aggregate.

Use a one-armed branch to skip the rest of one iteration without terminating
the run. When the condition is false, that iteration completes and the loop
advances:

```ts
.loop('eachRepo', input('repos'), (body) => body
  .step('fetch', http({ managed: false, url: 'https://example.test',
    returns: { name: 'string' } }))
  .branch('found', js`$vars.fetch.output.statusCode !== 404`,
    (yes) => yes.step('notify', script({
      code: 'return $vars.fetch.output.body.name;' }))))
```

The loop runs sequentially (`parallel: false`). Inside the body, read
`$vars.<loop>.currentItem` and `$vars.<loop>.currentIndex` — or `v('eachOrder.currentItem')`
from the builder.

## Rich loop options (loop 2.4)

Any of these — or a `body.break()` in the body — selects the loop's 2.4
definition (inner `start`/`continue`/`break` handles); a plain `.loop()` keeps
the long-standing 1.0.0 shape.

- `parallel: true` — run iterations concurrently instead of sequentially.
- `completionCondition` — an expression checked after each iteration; the loop
  stops early when it is true.
- `body.break()` — exit the whole loop from inside an arm. Terminal on its
  path, like `.terminate()` but scoped to the loop; using it shows the loop's
  break handle automatically (`breakEnabled`).

```ts
.var('found', types.string, '')
.loop('scan', input('items'), (body) => body
  .step('probe', script({ code: 'return $vars.scan.currentItem;', returns: 'object' }),
    { updates: { found: js`$vars.probe.output.id` } })
  .branch('hit', js`$vars.probe.output.score > 90`, (t) => t.break()),
  { completionCondition: js`$vars.found !== ""` })
```

Per-iteration flow-variable writes go through `{ updates }` on a body step —
`{ updates: { seen: js`$vars.seen + 1` } }` — never through a mutation node.
