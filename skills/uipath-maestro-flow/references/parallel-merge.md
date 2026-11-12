# Parallel / Merge

`.parallel(name, [armFn, armFn, ...])` fans out independent arms and joins them at a Merge named `name`. Execution continues from `.parallel(...)`'s `output` port, which can read every arm's output.

```ts
.parallel('ready', [
  (a) => a.step('weather', http({ url: weatherUrl, managed: true })),
  (b) => b.step('news', http({ url: newsUrl, managed: true })),
])
.step('combine', script({ code: 'return "ready";' }))
```

If every arm ends with `.return`, `.terminate`, or `.stepToRef` into an End written by another arm, nothing is joined: no Merge is emitted, `name` names no node, and nothing may follow `.parallel`:

```ts
.step('prepare', script({ code: 'return 1;' }))
.parallel('prepareFork', [
  (a) => a.step('notifyA', script({ code: 'return "a";' })).return({}, { name: 'done' }),
  (b) => b.step('notifyB', script({ code: 'return "b";' })).stepToRef('done'),
])
```

`.terminate` must be the first arm call; `check` rejects a preceding step with `TERMINATE_NOT_ARM_HEAD`.

Decompile (SDK 6.46.6 or later) writes a canvas fan-out whose arms never meet again as `.parallel` `<node>Fork`, where `<node>` is the node they leave. A canvas arm that runs a step before its Terminate remains an unstructured fan-out (see [brownfield.md](brownfield.md)).

## At a glance

Use it only when no arm needs another arm's result before the join: it expresses graph independence, not executor concurrency; the local executor processes arms in authored order.

## Options

`.parallel(name, arms, options)` accepts `version` and `label` for the Merge, as `.branch()` does, plus `fork`. Both require `@uipath/maestro-builder-sdk` 6.44.0 or later; an older SDK ignores `fork` (writes no fork node and rejects the option in TypeScript),
<!--skill-flavor:fork-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:fork-sdk-upgrade:end-->

### A fork node

Studio Web draws a parallel split as a `core.logic.merge` node with one incoming edge and one edge per arm (the "Parallel" gateway). `fork` writes that node; without it, arms leave the previous step's own port, one edge per arm, and the platform runs both shapes identically. Use `fork` to preserve a canvas flow's shape. Decompiled canvas forks include it; leave it written, because removing it deletes the fork and rewires every arm.

```ts
.parallel('J1', [
  (a) => a.step('T1', work),
  (b) => b.step('T2', work),
], { fork: { name: 'PAR', label: 'Parallel: run the applicable tasks together' }, label: 'Join: wait for every branch' })
```

The fork name is a node id like a step's; `check` reports `DUP_STEP` if a step already has it.

### Arms that join at a step instead of a Merge

To model canvas edges where arms feed one step directly with no Merge, end every arm with `.stepToRef('<step>')` and place that step after `.parallel`. Compilation writes no Merge; refs join the arms, and the target receives one incoming edge per arm. The runtime starts it once per arriving token (only a gateway waits for every incoming flow), so it runs once per arm, not once after all arms as with a Merge. `check` reports `PARALLEL_REF_JOIN` (warning). For one run, end each arm on its own step and place the shared step after `.parallel`.

```ts
.parallel('prepareFork', [
  (a) => a.step('script1', work).stepToRef('sendMessage'),
  (b) => b.step('script2', work).stepToRef('sendMessage'),
])
.step('sendMessage', script({ code: 'return [$vars.script1.output, $vars.script2.output];' }))
```

`prepareFork` creates no node, but do not reuse it as a step or variable name: `check` treats `$vars.prepareFork` as a Merge read (`PARALLEL_HAS_NO_OUTPUT`). Decompile writes this shape as `<source>Fork`; it also writes a merge node with one incoming and one outgoing edge (a designer-left pass-through) as the `rawNode` of its own definition. Leave both as written, including the warning.
