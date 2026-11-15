# Loops

Run a body once per collection member: `.loop(name, collection, bodyFn, options?)`. Keep per-item dispatch and decisions in the body. Write values needed after the loop to a `.var()` via a body step's `{ updates }`; parallel results differ (`parallel: true` in [Loop options](#loop-options)).

Loops are sequential by default (`parallel: false`). In the body, read `$vars.<loop>.currentItem` and `$vars.<loop>.currentIteration`, or `v('eachOrder.currentItem')` from the builder. The item is named after the LOOP, never the collection: there is no `$vars.item`, `$vars.currentItem`, or `$vars.<collection>`. A one-armed branch skips the rest of an iteration: false completes that iteration and advances. A non-2xx HTTP result fails its step and faults the loop; end its `.onError()` handler with `.continue()` to skip that item ([Loop options](#loop-options)).

`currentIndex` is legacy loop 1.0.0 only. On default 2.4 it is `undefined`; `check` rejects it with `UNKNOWN_LOOP_FIELD` and suggests `currentIteration - 1` for a 0-based index. Do not rely on `currentIteration`'s exact base: 2.4 documents 1-based, but local `flow-debug` currently reads 0 for the first item and the cloud runtime is unverified ([flow-builder-sdk#874](https://github.com/UiPath/flow-builder-sdk/issues/874)). If the result depends on the number, confirm it with a live `uip maestro flow debug` run ([ask first](operate.md#debug--a-real-end-to-end-run)).

## At a glance

Every `.loop()` emits `core.logic.loop` 2.4. Body writes use `{ updates }`, never a mutation node. Read `$vars.<loop>.currentItem` and `$vars.<loop>.currentIteration`, not legacy `currentIndex`. Options are `parallel: true`, `completionCondition` (checked after each iteration), `body.break()` (exits the loop), and `body.continue()` (advances to the next item).

## Loop options

`.loop()` emits the 2.4 definition with inner `start`/`continue`/`break` handles, matching the registry and designer. Emit legacy 1.0.0 only with `{ version: '1.0.0' }`; it uses body from `output`, a back-edge into `loopBack`, and `currentIndex`. On 1.0.0, `body.continue()` works; `breakEnabled` and `body.break()` fail `check` with `LOOP_VERSION_UNSUPPORTED`. `completionCondition` passes `check` with `@uipath/maestro-builder-sdk` 6.86.25 or later; older SDKs fail `check` with `LOOP_VERSION_UNSUPPORTED`. `parallel: true` on 1.0.0 only round-trips a canvas 1.0.0 loop and `check` warns `LOOP_PARALLEL_LEGACY`; parallel execution is unconfirmed. For a new parallel loop, omit `version` (2.4).

- `parallel: true` runs iterations concurrently. Their `{ updates }` writes overwrite one another in no fixed order, so a `.var()` updated by all iterations retains only some writes. After the loop, `$vars.<loop>.output` has one entry per item in collection order, each `{ <bodyStep>: { output } }`. Do not use parallel when a body step reads `currentItem`; iterations do not isolate it (30 items produced 26 distinct values, run `Completed`, no warning), so run that loop sequentially. Entries omit HTTP steps, and a step that did not run in a pass carries the previous pass's value; therefore do not read either from `$vars.<loop>.output`.
- `completionCondition` is checked after each iteration and stops the loop when true. It requires `@uipath/maestro-builder-sdk` 6.87.2 or later; older SDKs compile it but ignore it, run every item, and report `Completed`, no warning,
<!--skill-flavor:completion-condition-sdk-upgrade:start-->
  so upgrade the copy `uip` uses by running:
  `npm install -g @uipath/maestro-builder-sdk@latest`, or
  `npm install --save-dev @uipath/maestro-builder-sdk@latest` for a
  workspace copy.
<!--skill-flavor:completion-condition-sdk-upgrade:end-->
- `body.break()` exits the whole loop from inside an arm; its path is terminal, like `.terminate()` but loop-scoped, and automatically shows the loop's `breakEnabled` handle.
- `body.continue()` advances to the next iteration from an arm or `.onError()` handler through the loop's continue handle; its path is terminal. Without it, a handler inside the body ends the whole run on its own End. Do not use `.stepToRef('<the loop>')`: it re-enters from the outer input and restarts the loop, and `check` rejects it with `REF_TO_OWN_LOOP`. It also works on 1.0.0 through `loopBack`. It requires `@uipath/maestro-builder-sdk` 6.20.0 or later; older SDKs fail with `continue is not a function`,
<!--skill-flavor:continue-sdk-upgrade:start-->
  so upgrade the copy `uip` uses by running:
  `npm install -g @uipath/maestro-builder-sdk@latest`, or
  `npm install --save-dev @uipath/maestro-builder-sdk@latest` for a
  workspace copy.
<!--skill-flavor:continue-sdk-upgrade:end-->

```ts
.loop('each', input('items'), (body) => body
  .step('call', http({ url: 'https://api.example.test/items', method: 'POST', managed: true }))
  .onError((h) => h
    .step('logFailure', script({ code: 'return "logged";' }))
    .continue()))
```

## Do while

`.doWhile(name, condition, bodyFn, { limit?, breakEnabled? })` runs the body, then repeats while the condition is true; check the condition AFTER each pass, so it runs at least once (`core.logic.dowhile`). The container publishes no data output: write results to a `.var()` inside the body with `{ updates }`. `limit` caps iterations at 1–10,000; blank means the platform default of 10,000. `body.break()` and `body.continue()` work exactly as in `.loop()`. A body-step failure can route to `.onError()` after `.doWhile(...)`, as with `.loop()` ([error-handling.md](error-handling.md)).
