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
