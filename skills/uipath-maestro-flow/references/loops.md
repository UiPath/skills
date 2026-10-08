# Loops

Loop runs a body for every member of a collection.

Signature: `.loop(name, collection, bodyFn, options?)`.

```ts
.loop('eachOrder', input('orders'), (body) => body
  .step('handle', script({ code:
    'return { id: $vars.eachOrder.currentItem.id };' })))
```

Keep per-item dispatch and decisions in the body. A value the steps after the
loop need is written to a `.var()` from a body step with `{ updates }`, as
the last example below shows.

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
`$vars.<loop>.currentItem` and `$vars.<loop>.currentIteration` — or
`v('eachOrder.currentItem')` from the builder.

`currentIndex` is the field name of the legacy loop 1.0.0. On the default 2.4
loop it reads `undefined`, so `check` refuses it (`UNKNOWN_LOOP_FIELD`) and
suggests `currentIteration - 1` for a 0-based index. Do not rely on the exact
base of `currentIteration` yet: the 2.4 definition documents it as 1-based,
but the local engine (`flow-debug`) currently reads 0 for the first item, and
the cloud runtime is not yet verified
([flow-builder-sdk#874](https://github.com/UiPath/flow-builder-sdk/issues/874)).
If a flow's result depends on the number, confirm it with a live
`uip maestro flow debug` run.

The item is named after the LOOP, not after the collection and not by a
convention: **there is no `$vars.item`, `$vars.currentItem` or `$vars.<collection>`.**
A branch or step that decides on the item has to name the loop, so a loop called
`eachIssue` reads `$vars.eachIssue.currentItem.priority` — never
`$vars.item.priority`, which resolves to nothing and takes the false arm on every
iteration without erroring.

## At a glance

Run a body once for each value in a collection.

Per-iteration flow-variable writes go through `{ updates }` on a body step.
Every `.loop()` emits `core.logic.loop` 2.4: the body reads
`$vars.<loop>.currentItem` and `$vars.<loop>.currentIteration` (not the legacy
1.0.0 `currentIndex`, which `check` refuses). Options: `parallel: true`,
`completionCondition` (checked after each iteration, stops early), and
`body.break()` exits the whole loop from inside an arm. The option details and
examples are below.

## Loop options

Every `.loop()` emits the loop's 2.4 definition (inner `start`/`continue`/`break`
handles), the version the registry serves and the designer authors. The legacy
1.0.0 shape (body from `output`, back-edge into `loopBack`, `currentIndex`) is
emitted only for an explicit `{ version: '1.0.0' }`, which accepts none of the
options below.

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

## Do while

Run a body, then repeat **while a condition is true** — checked AFTER each
pass, so the body always runs at least once (`core.logic.dowhile`). The
container publishes no data output: write results to a `.var()` from inside
the body with `{ updates }`. `limit` caps iterations (1–10,000; blank means
the platform default of 10,000), and `body.break()` works exactly as in
`.loop()`.

Signature: `.doWhile(name, condition, bodyFn, { limit?, breakEnabled? })`.

```ts
.var('page', types.number, 1)
.doWhile('paginate', js`$vars.fetch.output.body.hasNextPage === true`, (body) => body
  .step('fetch', http({ url: tmpl`https://api.example.test/items?page=${v('page')}`,
    method: 'GET', managed: false, returns: { hasNextPage: 'boolean' } }),
    { updates: { page: js`$vars.page + 1` } }),
  { limit: 50 })
```
