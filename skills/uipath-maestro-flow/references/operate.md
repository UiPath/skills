# Operate — ship, run, and manage a deployed flow

<!--skill-flavor:operate-auth:start-->
Before any cloud operation—upload, deploy, debug, trigger, inspect, or instance lifecycle—run `uip login`; check with `uip login status --output json`.
<!--skill-flavor:operate-auth:end-->

Authoring is upstream. Do not ship source until it completes the loop in [`CLI-LOOP.md`](CLI-LOOP.md): `check` the source, `compile` it, and `validate` the emitted `.flow`.

## Lay out the emitted flow first

<!--skill-flavor:operate-format:start-->
```bash
uip maestro flow format <Name>.flow --output json
```

**Greenfield files only.** Run `format` on the last-emitted artifact before `solution upload`, `flow debug`, or opening it in a designer, unless its source sets `.layout()`. `validate` does not require layout. `compile` writes placeholder `ui.position` values and no top-level `layout`; the canvas uses `layout.nodes[<id>]` when present, otherwise `node.ui`, producing one flat row with sequential switch arms. `format` creates `layout`, fans arms into rows, sizes nodes, and reports `NodesRepositioned`.

**Never format a merged brownfield file.** `merge` preserves the original `layout`, shifts later nodes right or down, and grows containers as needed. Upload or debug the merged file exactly as `merge` wrote it.
<!--skill-flavor:operate-format:end-->

`nodes create` without `--position`, or a hand edit adding nodes, leaves new nodes at `layout.nodes[<id>].position` 0,0. After such an edit to a file without an author-chosen layout, run `format` and confirm every `layout.nodes` entry has a distinct position. With an author-chosen layout, skip `format` and pass `--position <x>,<y>` to every `nodes create`.

### Lay out from source instead: `.layout()`, `at()`, `dim()`

A builder `.layout({ nodes })` avoids `format` when every non-96 × 96 node carries its size (rule 1). Entries are keyed by node id; `at(x, y)` writes position and `dim(width, height)` writes container size. A step id is its name; the trigger id is `start` unless renamed by `.triggerId()`; an End id is the name supplied to `.return`, or unnamed `end`, `end2`, `end3`, … in emission order. Include one entry per node. Use source layout for a requested arrangement or decompiled source carrying one ([`brownfield.md`](brownfield.md#the-same-loop-by-hand)); otherwise `format` is simpler.

Rules:

1. **Use the canvas grid.** A node is 96 px square; columns are 192 px and rows 160 px: `x = 256 + 192 × column`, `y = 144 + 160 × row`. Put the main path on row 0 left-to-right and an error handler or side arm below. Compile writes 96 × 96; larger shapes must carry their size: an agent (`inlineAgent`, `conversationalAgent`, `voiceAgent`) uses `at(x, y, dim(288, 96))`, with the next column 384 px right. Containers carry `dim()` (rule 2). A row below a container starts one row gap (64 px) below its bottom edge, not at the next 160 px row.
2. **A child's position is relative to its container.** A loop or do-while body starts at `at(144, 96)` inside the padding. The container must contain the body: right edge of the rightmost child plus 144, bottom edge of the lowest child plus 96, and never smaller than `format`'s `dim(560, 320)`. One row of 96 px nodes uses `dim(max(560, 192 × bodyNodes + 192), 320)`; measure inline agents, second rows, and nested containers from their entries, not node count.
3. **Name every node, or none.** A missing entry falls back to compile's one-row placeholder and can overlap; an unknown key fails `compile`.
4. **Never `format` a file whose source sets `.layout()`.** It discards source positions, as with merged brownfield files.
<!--skill-flavor:layout-sdk-version:start-->
5. **`at` and `dim` need `@uipath/maestro-builder-sdk` 6.36.0 or later** — check that `dist/api-index.md` in the SDK copy in use lists them. If not, upgrade that copy: run `npm install @uipath/maestro-builder-sdk@latest` in a workspace with its own `node_modules` copy (used before the global one), else run `npm install -g @uipath/maestro-builder-sdk@latest`; or write `{ position: { x, y } }` with optional `size: { width, height }`.
<!--skill-flavor:layout-sdk-version:end-->

## Refresh solution resources first

<!--skill-flavor:refresh-command:start-->
```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```
<!--skill-flavor:refresh-command:end-->

<!--skill-flavor:refresh-when:start-->
Run this before `solution upload`, `solution publish` or `flow debug`, every time. It syncs connection and process declarations from `bindings_v2.json`; stale declarations cause runtime binding errors even when the `.flow` is correct.
<!--skill-flavor:refresh-when:end-->

There is no positional solution argument. Omit `--solution-folder` only from the solution root.

## Publish

<!--skill-flavor:operate-publish:start-->
"Publish", without a target, means **Studio Web**:

```bash
uip solution upload <SolutionDir> --output json
```

Pass the solution root containing the `.uipx`, or `.` from inside it. From a nested project folder pass `..` or an absolute path, never the solution name again. Report the Studio Web URL on success.

Use Orchestrator only when explicitly requested because it bypasses Studio Web:

```bash
uip maestro flow pack <project-path> <OutputDir>
```

Then run `uip solution publish`—see the `uipath-solution` skill. `uip maestro flow publish <project-path>` packs and uploads the `.nupkg` in one step; `--folder-key` or `--folder-path` selects a folder feed. When the target is genuinely ambiguous, ask before packing.
<!--skill-flavor:operate-publish:end-->

## Debug — a real end-to-end run

<!--skill-flavor:operate-debug:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json
```

Pass the PROJECT directory containing `project.uiproj`. `flow debug` executes the flow for real; it is not validation (`validate` is). If the user can answer and did not request a run, ask once before the first run; that approval covers fix-and-rerun for this turn. With nobody to ask, run it when the request is for a working flow unless a connection was guessed ([bindings.md](bindings.md#where-both-values-come-from)); otherwise report it unverified. Debug overwrites the Studio Web solution whose `SolutionId` matches local `.uipx`; for a solution not scaffolded this turn, debug only after an explicit question naming that overwrite, and never headlessly.
<!--skill-flavor:operate-debug:end-->

Operational constraints:

<!--skill-flavor:operate-debug-wait:start-->
- **Foreground, with a tool timeout of 10 minutes or more.** It takes 1-5 minutes and prints JSON only at exit.
- **Poll the same process if it reports still running.** Empty output means unfinished, not failed.
- **Never start a second debug while one is running.** It re-uploads and re-executes.
- **Re-run only after changing the flow.** Do not rerun to reread or reshape completed output.
- **`Debug polling timed out after <N>s` is not a failure.** The run continues server-side. Take `instanceId` from stderr and poll `uip maestro flow debug-instance status <INSTANCE_ID> --output json`.
<!--skill-flavor:operate-debug-wait:end-->
- **An RPA step does not run under a headless debug** ([rpa-workflow.md](rpa-workflow.md#evidence-boundary)).
<!--skill-flavor:operate-debug-scratch-copy:start-->
- **Every process and connection node must resolve.** Missing tenant resources prevent provisioning and starting; `Data.missingResources` names them although `check` and `validate` pass. To debug the rest, debug a scratch copy without those nodes, delete it afterward, and report the run as the copy's.
<!--skill-flavor:operate-debug-scratch-copy:end-->
- **Do not pass `--folder-path` or `--folder-key`.** Debug provisions into the personal workspace; another folder fails `403` at `Stage: prepare-custom-debug`, and a personal-workspace `--folder-key` gives `404`. No instance starts.
<!--skill-flavor:debug-shared-resources:start-->
Shared resources reach the run through `resources refresh`, not the debug folder.
<!--skill-flavor:debug-shared-resources:end-->

Exception: an account without a personal workspace (service-principal or CI token, `403` at `get-personal-folder`) passes `--folder-id <number>` to skip that lookup. `prepare-custom-debug` may still `403` for a non-personal folder; tell the user if it does.

Inputs for flows with `.input(...)` parameters:

<!--skill-flavor:operate-debug-inputs:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```
<!--skill-flavor:operate-debug-inputs:end-->

Build inputs from real records, never invented values. Read an entity id with `uip df entities list --output json`, then a live record with `uip df records list <ENTITY_ID> --output json`.

<!--skill-flavor:operate-debug-attachment:start-->
A `types.file` input takes a repeatable local file; the left side is the input name:

```bash
  --attachment <inputName>=<localPath>
```

At runtime the variable is an OBJECT, not a path: scripts read `$vars.<triggerNodeId>.output.<inputName>.FullName` and see only `ID`, `FullName`, `MimeType`, `Metadata`, never content. Pass that reference to a file-reading step, such as an RPA process taking it as its file argument ([rpa-workflow.md](rpa-workflow.md#where-the-job-runs)).
<!--skill-flavor:operate-debug-attachment:end-->

<!--skill-flavor:operate-debug-entry-point:start-->
**A flow with more than one root starts at the default root.** It is the trigger marked `isDefaultEntryPoint`, else the first trigger. To run another root, pass its trigger node id:

```bash
uip maestro flow debug <project-dir> --output json --entry-point <triggerNodeId>
```

A wrong id exits 3 and lists valid trigger ids. `Data.entryPoint` names the starting trigger.
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

Use `<not returned by CLI>` rather than dropping a missing line. `Data.finalStatus: "Faulted"` means the response contains the cause. `--output-filter` never filters `Message` or `Instructions`; they summarize incidents when PIMS returned any and name `uip maestro flow debug-instance incidents <instanceId>`. If `Data.incidents` is missing or `null` in a projection, run that command. Do not rerun the flow. On the next run, add `incidents:incidents` to the projection, or redirect unfiltered output to a file and search it:
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

`process list` also accepts `--folder-path <path>` instead of `--folder-key`. For `process list`, take `<folder-key>` from the user or `Key` in `uip or folders list --output json`; for `process run`, its list entry's `folderKey` also works.

Only `process run` lets `--attachment` override `--inputs` on key collision. Its `--validate` accepts pre-uploaded attachment references for file slots and is not a dry run: after validation it starts a real job. Give `types.file` inputs with `flow process run --attachment`, never `uip or jobs start --attachment`.

`--entry-point <triggerNodeId>` starts that root and makes `--validate` check its schema. A wrong id exits 3 and lists process trigger ids. Without it, use the release default entry point. `flow pack` or `solution pack` sets that to the first trigger (the SDK-built default root); other packaging may differ. Pass `--entry-point` whenever the root matters. Do not pass `--feed-id`; the CLI reads the release feed.

## Inspect a job

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

Traces are verbose, full timelines, and a last resort except per-iteration timing: `elementExecutions` aggregates per element, so a loop body has one row. Spans stream to stderr, one JSON line each; use `--pretty` for readable lines.

## Instance lifecycle

<!--skill-flavor:operate-instance-id:start-->
Every `instance` command needs `--folder-key` (`-f`) or is rejected before the API. Get it from `uip or folders list --output json`, the job/process context, or `instance list`. An instance id comes from debug `Data.instanceId`, `job status`, or `instance list`.
<!--skill-flavor:operate-instance-id:end-->

```bash
uip maestro flow instance pause  <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance retry  <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

`-f` does not filter `instance list`; do not assume every listed instance is in that folder. Never `retry` a faulted instance before reading its debug response or incident. Orchestrator defines effect and recoverability; consult `uip maestro flow instance <sub> --help` for flags.

## Evidence boundary

A green `validate` proves only that the emitted `.flow` is well formed. Only a run proves operation, and only against its tenant: successful upload does not prove connections resolve, and a completed debug does not prove correctness. Report the instance identity and CLI-returned status, never an inference.