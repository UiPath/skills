# Operate — ship, run, and manage a deployed flow

<!--skill-flavor:operate-auth:start-->
All cloud operations—upload, deploy, debug, trigger, inspect, and instance lifecycle—need `uip login`; check with `uip login status --output json`.
<!--skill-flavor:operate-auth:end-->

Authoring is upstream. Do not ship source until it completes the loop in [`CLI-LOOP.md`](CLI-LOOP.md): `check` the source, `compile`, then `validate` the emitted `.flow`.

## Lay out the emitted flow first

<!--skill-flavor:operate-format:start-->
```bash
uip maestro flow format <Name>.flow --output json
```

For greenfield files, run `format` on the last-emitted artifact before `solution upload`, `flow debug`, or opening it in a designer, unless its source sets `.layout()` below. `validate` does not require layout.

`compile` writes placeholder `ui.position` values and no top-level `layout`. The canvas uses `layout.nodes[<id>]` when present, otherwise `node.ui`; without layout, a new file draws placeholders in one row, including switch arms. `format` builds `layout`, fans arms into rows, sizes shapes, and reports `NodesRepositioned`. Skipping it on a greenfield file is the most common cause of misshapen nodes in Studio Web.

**Never format a merged brownfield file.** `merge` preserves the original `layout`, moves later nodes right or down, and expands containers as needed. Upload or debug the merged file as `merge` wrote it; `format` discards its positions.
<!--skill-flavor:operate-format:end-->

### Lay out from source instead: `.layout()`, `at()`, `dim()`

Use source layout so the emitted file needs no `format`, provided every non-96 × 96 node carries its size (rule 1). `.layout({ nodes })` needs one node-id entry per node; `at(x, y)` writes position and `dim(width, height)` size. A step id is its name; the trigger id is `start` unless `.triggerId()` renames it; an End id is its `.return` name, or `end`, `end2`, `end3`, … for unnamed Ends in emission order. A flow with several unnamed Ends needs all keys. Use this for a requested arrangement or decompiled source carrying layout ([`brownfield.md`](brownfield.md#the-same-loop-by-hand)); otherwise run `format`.

```ts
import { at, dim, flow } from '@uipath/maestro-builder-sdk';

export default flow('invoice-intake')
  // …steps…
  .layout({
    nodes: {
      start: at(256, 144), fetch: at(448, 144), eachInvoice: at(640, 144, dim(576, 320)),
      extract: at(144, 96), route: at(336, 96), // inside eachInvoice, relative to it
      review: at(1312, 144, dim(288, 96)), // an agent node carries its size
      done: at(1696, 144),
      onFailure: at(448, 528), end: at(640, 528), // below the container, not beside its body
    },
  })
  .build();
```

Rules:

1. **Use the canvas grid.** A node is 96 px square; columns are 192 px and rows 160 px: `x = 256 + 192 × column`, `y = 144 + 160 × row`. Put the main path on row 0 left-to-right and an error handler or side arm below. Compile writes 96 × 96 for every node, so larger shapes need sizes: an agent (`inlineAgent`, `conversationalAgent`, `voiceAgent`) is `at(x, y, dim(288, 96))`, with the next column 384 px right. A container needs `dim()` (rule 2); its next row starts 64 px below its bottom edge, not at the next 160 px row.
2. **Children are relative to their container.** Start a loop or do-while body at `at(144, 96)` inside its padding. Size the container to the rightmost child edge plus 144 and lowest child edge plus 96, never below `format`'s `dim(560, 320)`. For one row of 96 px nodes use `dim(max(560, 192 × bodyNodes + 192), 320)`; measure inline agents, second rows, and nested containers from their entries, not node count.
3. **Name every node, or none.** A missing entry falls back to compile's one-row placeholder and overlaps this layout; an unknown key fails `compile`.
4. **Never `format` a file whose source sets `.layout()`.** It discards source positions, as with merged brownfield files.
<!--skill-flavor:layout-sdk-version:start-->
5. **`at` and `dim` need `@uipath/maestro-builder-sdk` 6.36.0 or later** — check that `dist/api-index.md` of the SDK copy in use lists them. If not, upgrade that copy: run `npm install @uipath/maestro-builder-sdk@latest` in a workspace with its own `node_modules` copy (used before the global one), else run `npm install -g @uipath/maestro-builder-sdk@latest`; or write the entry long-hand, `{ position: { x, y } }` with an optional `size: { width, height }`.
<!--skill-flavor:layout-sdk-version:end-->

## Refresh solution resources first

<!--skill-flavor:refresh-command:start-->
```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```
<!--skill-flavor:refresh-command:end-->

<!--skill-flavor:refresh-when:start-->
Run this every time before `solution upload`, `solution publish`, or `flow debug`. It syncs connection and process declarations from `bindings_v2.json`; stale declarations cause runtime binding errors even when `.flow` is correct.
<!--skill-flavor:refresh-when:end-->

There is no positional solution argument. Omit `--solution-folder` only from the solution root.

## Publish

<!--skill-flavor:operate-publish:start-->
“Publish” without a target means **Studio Web**:

```bash
uip solution upload <SolutionDir> --output json
```

Pass the solution root containing `.uipx`, or `.` from inside it. From a nested project use `..` or an absolute path, never the solution name again; that resolves to a nonexistent child. On success report the Studio Web URL.

Use Orchestrator only when explicitly requested because it bypasses Studio Web:

```bash
uip maestro flow pack <project-path> <OutputDir>
```

Then run `uip solution publish`; see the `uipath-solution` skill. `uip maestro flow publish <project-path>` packs and uploads the `.nupkg` to Orchestrator packages in one step (`--folder-key` or `--folder-path` picks a folder feed). Ask before packing when the target is genuinely ambiguous.
<!--skill-flavor:operate-publish:end-->

## Debug — a real end-to-end run

<!--skill-flavor:operate-debug:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json
```

Pass the PROJECT directory containing `project.uiproj`.

`flow debug` executes the flow for real, including emails, messages, and APIs; `validate` is the validation step. When a user can answer and did not ask for the run, ask once before the first run, even when the request is for a flow that works; that yes covers the fix-and-re-run loop on the flow the user asked to get working this turn. With nobody to ask, run it when the request is for a flow that works, unless a connection was guessed ([bindings.md](bindings.md#where-both-values-come-from)); otherwise report the flow as unverified rather than letting a passing `validate` stand as the result. Debug overwrites the Studio Web solution whose `SolutionId` matches the local `.uipx`: for a solution not scaffolded this turn, debug only on a yes to a question that names that overwrite, and headless, never debug it.
<!--skill-flavor:operate-debug:end-->

Operational constraints:

<!--skill-flavor:operate-debug-wait:start-->
- **Foreground, with a tool timeout of 10 minutes or more.** It takes 1-5 minutes and emits JSON only at exit; a 1-2 minute shell timeout loses it.
- **Poll the same process if the tool reports it still running.** Empty output means unfinished, not failed.
- **Never start a second debug while one is running.** It re-uploads and reruns.
- **Re-run only after changing the flow.** Do not rerun to reread or reshape returned output.
- **`Debug polling timed out after <N>s` is not a failure.** The run continues server-side. Take `instanceId` from stderr and poll `uip maestro flow debug-instance status <INSTANCE_ID> --output json`.
<!--skill-flavor:operate-debug-wait:end-->
- **An RPA step does not run under a headless debug** ([rpa-workflow.md](rpa-workflow.md#evidence-boundary)).
<!--skill-flavor:operate-debug-scratch-copy:start-->
- **Every process and connection node must resolve.** Missing tenant resources (placeholder process keys or stub connections) fail provisioning and start no instance; `Data.missingResources` names them, although `check` and `validate` pass. To debug other nodes first, debug a scratch copy without them, delete it afterward, and report the run as the copy's.
<!--skill-flavor:operate-debug-scratch-copy:end-->
- **Do not pass `--folder-path` or `--folder-key`.** Debug provisions into your personal workspace; any other folder fails `403` at `Stage: prepare-custom-debug`, even for a trivial flow, and a personal workspace `--folder-key` gives `404`. No instance starts.
<!--skill-flavor:debug-shared-resources:start-->
Shared resources reach the run through `resources refresh`, not the debug folder.
<!--skill-flavor:debug-shared-resources:end-->
  Exception: an account with no personal workspace (a service-principal or CI
  token gets `403` at `get-personal-folder`) passes `--folder-id <number>`, which
  skips that lookup. `prepare-custom-debug` for a non-personal folder may still
  `403`; if it does, tell the user.

Inputs for flows with `.input(...)` parameters:

<!--skill-flavor:operate-debug-inputs:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```
<!--skill-flavor:operate-debug-inputs:end-->

Build inputs from real records, never invented values: invented keys match no record, return `[]`, and fault on empty data. Read an entity id with `uip df entities list --output json`, then a live record with `uip df records list <ENTITY_ID> --output json`.

<!--skill-flavor:operate-debug-attachment:start-->
A `types.file` input takes a repeatable local file; the left side is the input name:

```bash
--attachment <inputName>=<localPath>
```

At runtime the variable is an OBJECT, not a path. A script reads the uploaded name as `$vars.<triggerNodeId>.output.<inputName>.FullName` and sees only `ID`, `FullName`, `MimeType`, `Metadata`, never content. Pass that reference to a file-reading step such as an RPA process taking it as its file argument ([rpa-workflow.md](rpa-workflow.md#where-the-job-runs)).
<!--skill-flavor:operate-debug-attachment:end-->

<!--skill-flavor:operate-debug-entry-point:start-->
**A flow with more than one root starts at the default root.** Use the trigger marked `isDefaultEntryPoint`, else the first trigger. Run another root with its trigger node id:

```bash
uip maestro flow debug <project-dir> --output json --entry-point <triggerNodeId>
```

A wrong id exits 3 and lists valid trigger ids. `Data.entryPoint` names the started trigger.
<!--skill-flavor:operate-debug-entry-point:end-->

<!--skill-flavor:operate-debug-conversational:start-->
**A conversational flow cannot be debugged headlessly.** If the start root is a `conversationTrigger()` (default or selected by `--entry-point`), debug uploads, returns `Code: FlowDebugStudioWebHandoff` with `Data.studioWebUrl`, and starts no run; `--timeout` does nothing. Chat from Studio Web (`--open-in-browser` opens it) or the Maestro VS Code extension.
<!--skill-flavor:operate-debug-conversational:end-->

**An inbound voice flow cannot be debugged at all.** Do not run debug on a `voiceTrigger()` flow; [voice.md](voice.md#evidence-boundary) has the test loop.

### Reporting a debug run

<!--skill-flavor:operate-debug-report:start-->
`Data.studioWebUrl` and `Data.instanceId` are the first two summary lines:

```text
Studio Web URL: <url>
Instance ID: <instanceId>
```

Use `<not returned by CLI>` when either is absent. `Data.finalStatus: "Faulted"` means the response already contains the cause. A projection may drop `Data.incidents`, but `--output-filter` never filters `Message` or `Instructions`; those summarize returned incidents and name `uip maestro flow debug-instance incidents <instanceId>`. If `Data.incidents` is missing or null in a projection, run that command. Do not rerun the flow. On the next run add `incidents:incidents` to the projection, or redirect unfiltered output to a file and search it:
<!--skill-flavor:operate-debug-report:end-->

<!--skill-flavor:operate-debug-redirect:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json > /tmp/flow-debug.json
```
<!--skill-flavor:operate-debug-redirect:end-->

## Trigger a deployed process

```bash
uip maestro flow process list --folder-key <folder-key> --output json
uip maestro flow process run <process-key> <folder-key> --output json \
  --inputs '{"numberA": 5}' --attachment <inputName>=<localPath>
```

`process list` also accepts `--folder-path <path>` instead of `--folder-key`. For `process list`, use `<folder-key>` from the user or the `Key` of `uip or folders list --output json`; for `process run`, the list entry's `folderKey` also works.

For `process run` only, `--attachment` overrides `--inputs` on key collision, and `--validate` accepts pre-uploaded attachment references for file slots even though their nominal type is `string`.
`--validate` is not a dry run: after the check passes it starts a real job.

Give a Flow's `types.file` input with `flow process run --attachment`, never
`uip or jobs start --attachment`.

`--entry-point <triggerNodeId>` starts that root and makes `--validate` check that root's schema. A wrong id exits 3 and lists process trigger ids. Without it, use the release's default entry point. `flow pack` or `solution pack` sets that to the flow's first trigger, which is the default for an SDK-built flow; other packaging can differ. Pass `--entry-point` whenever the root matters. You do not need `--feed-id`; the CLI reads the feed from the release.

## Inspect a job

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

Traces are verbose full timelines and a last resort, not a starting point.

## Instance lifecycle

<!--skill-flavor:operate-instance-id:start-->
Every `instance` command needs `--folder-key` (`-f`) or is rejected before the API. Get it from `uip or folders list --output json`, or from the job or process context. Get the instance id from debug `Data.instanceId`, a `job status` response, or `instance list`.
<!--skill-flavor:operate-instance-id:end-->

```bash
uip maestro flow instance pause  <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance retry  <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

`-f` does not filter `instance list`: do not assume every listed instance is
in that folder.

Never `retry` a faulted instance before reading its cause in the debug response or incident; retrying without it repeats the failure. Orchestrator defines effect and recovery behavior; run `uip maestro flow instance <sub> --help` for flags.

## Evidence boundary

A green `validate` proves only that the emitted `.flow` is well formed. Only a run proves operation, and only against its tenant: successful upload does not prove connections resolve, and a completed debug does not prove correctness. Report the instance identity and CLI status, not an inference.
