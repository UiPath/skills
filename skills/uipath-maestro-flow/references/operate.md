# Operate — ship, run, and manage a deployed flow

<!--skill-flavor:operate-auth:start-->
Everything that touches the cloud—upload, deploy, debug, trigger, inspect, and instance lifecycle—needs `uip login`; check with `uip login status --output json`.
<!--skill-flavor:operate-auth:end-->

Authoring is upstream. Do not ship source until it completes the loop in [`CLI-LOOP.md`](CLI-LOOP.md): `check` the source, `compile` it, and `validate` the emitted `.flow`.

## Layout of the emitted flow

<!--skill-flavor:operate-format:start-->
`compile` lays out the flow. For a flow or subflow whose source has no
`.layout()`, each node gets the position `uip maestro flow format` would give
it. Running `format` on the compiled file moves nothing; skip it.

Every node also gets its canvas-shape size, unless `.layout()` sets one: a
container (a loop, for example) is 560 × 320, an agent node (`inlineAgent`,
`conversationalAgent`, `voiceAgent`) 288 × 96, and every other node 96 × 96.

**Never format a merged brownfield file.** The original's `layout` already
holds the canvas author's positions, and `merge` keeps them, moving later
nodes right or down and growing containers only to fit added ones. `format`
re-lays out every node and discards them. Upload or debug the merged file as
`merge` wrote it.
<!--skill-flavor:operate-format:end-->

This needs `@uipath/maestro-builder-sdk` 6.113.0 or later. An older SDK
writes every node 96 × 96 on one row at y = 144 (an agent node's `ui.size` is
96 × 96, not 288 × 96). With such an SDK, run
`uip maestro flow format <Name>.flow --output json` once on a greenfield file
(never on a merged or `.layout()` file), and in a `.layout()` give each agent
node `dim(288, 96)` and each container at least `dim(560, 320)`;
<!--skill-flavor:compile-layout-sdk-upgrade:start-->
or upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:compile-layout-sdk-upgrade:end-->

`nodes create` without `--position`, or a hand edit adding nodes, leaves new nodes at `layout.nodes[<id>].position` 0,0. After such an edit to a file without an author-chosen layout, run `format` and confirm every `layout.nodes` entry has a distinct position. With an author-chosen layout, skip `format` and pass `--position <x>,<y>` to every `nodes create`.

### Lay out from source instead: `.layout()`, `at()`, `dim()`

`.layout()` replaces compile's layout with positions you choose.
`.layout({ nodes })` on the flow takes one entry per node, keyed by node id; `at(x, y)` writes an entry, and `dim(width, height)` the size a container needs.
A step's id is its name.
The trigger's is `start` unless `.triggerId()` renamed it.
An End's is the `name` its `.return` gave it, and an unnamed End is `end`, then `end2`, `end3`, … in emission order, so a flow with several unnamed Ends has that many keys to write.
Use it when the request asks for a particular arrangement, or when a decompiled source already carries one ([`brownfield.md`](brownfield.md#designer-shapes-decompile-keeps)).
Otherwise leave it out: compile lays out the flow itself.

```ts
import { at, dim, flow } from '@uipath/maestro-builder-sdk';

export default flow('invoice-intake')
  // …steps…
  .layout({
    nodes: {
      start: at(256, 144), fetch: at(448, 144), eachInvoice: at(640, 144, dim(576, 320)),
      extract: at(144, 96), route: at(336, 96), // inside eachInvoice, relative to it
      review: at(1312, 144), // an agent node: compile gives it 288 × 96
      done: at(1696, 144),
      onFailure: at(448, 528), end: at(640, 528), // below the container, not beside its body
    },
  })
  .build();
```

Rules:

1. **Use the canvas grid.** A node is 96 px square; a column is 192 px, a row 160 px: `x = 256 + 192 × column`, `y = 144 + 160 × row`.
   The main path goes on row 0 left to right; an error handler or a side arm takes the row below.
   Compile gives a node without `dim()` its canvas-shape size: an agent node (`inlineAgent`, `conversationalAgent`, `voiceAgent`) is 288 × 96, so the next column starts 384 px to its right; a container is 560 × 320 unless its `dim()` makes it larger (rule 2), and the row below it starts one row gap (64 px) under its bottom edge, not at the next 160 px row.
2. **A child's position is relative to its container.** A loop or do-while body starts at `at(144, 96)` inside the container's padding. The container's 560 × 320 holds a small body; give it a `dim()` only when the body needs more: the right edge of its rightmost child plus 144, by the bottom edge of its lowest child plus 96.
   For one row of 96 px nodes that is `dim(192 × bodyNodes + 192, 320)` from two body nodes on (two nodes: `dim(576, 320)`, as `eachInvoice` above); a body with an inline agent, a second row or a nested container is measured from its own entries, not from the node count.
3. **Name every node, or none.** A missing entry falls back to compile's one-row placeholder, which lands on top of your layout. A key that names no node is dropped with a `LAYOUT_UNKNOWN_KEY` warning (an SDK older than 6.115.0 fails `compile` on it); remove it.
4. **Never `format` a file whose source sets `.layout()`.** `format` re-lays out every node and discards the source's positions, exactly as it does to a merged brownfield file.
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

Then run `uip solution publish`—see the `uipath-solution` skill. `uip maestro flow publish <project-path>` packs and uploads the `.nupkg` to Orchestrator packages in one step; `--folder-key` or `--folder-path` selects a folder feed. When the target is genuinely ambiguous, ask before packing.
<!--skill-flavor:operate-publish:end-->

## Debug — a real end-to-end run

<!--skill-flavor:operate-debug:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json
```

Pass the PROJECT directory containing `project.uiproj`. `flow debug` executes the flow for real; it is not validation (`validate` is). If the user can answer and did not request a run, ask once before the first run, even when the request is for a flow that works; that yes covers the fix-and-re-run loop on the flow the user asked to get working this turn. With nobody to ask, run it when the request is for a flow that works, unless a connection was guessed ([bindings.md](bindings.md#where-both-values-come-from)); otherwise report the flow as unverified rather than letting a passing `validate` stand as the result. Debug overwrites the Studio Web solution whose `SolutionId` matches local `.uipx`; for a solution not scaffolded this turn, debug only on a yes to a question that names that overwrite, and headless, never debug it.
<!--skill-flavor:operate-debug:end-->

Operational constraints:

<!--skill-flavor:operate-debug-wait:start-->
- **Foreground, with a tool timeout of 10 minutes or more.** It takes 1-5 minutes and prints JSON only at exit.
- **Poll the same process if the tool reports it still running.** An empty output file means unfinished, not failed.
- **Never start a second debug while one is running.** It re-uploads and re-executes.
- **Re-run only after changing the flow.** Do not rerun to reread or reshape completed output.
- **`Debug polling timed out after <N>s` is not a failure.** The run continues server-side. Take `instanceId` from stderr and poll `uip maestro flow debug-instance status <INSTANCE_ID> --output json`.
<!--skill-flavor:operate-debug-wait:end-->
- **An RPA step does not run under a headless debug** ([rpa-workflow.md](rpa-workflow.md#evidence-boundary)).
<!--skill-flavor:operate-debug-scratch-copy:start-->
- **Every process and connection node must resolve.** Missing tenant resources (a placeholder process key, a stub connection) prevent provisioning and starting; `Data.missingResources` names them although `check` and `validate` pass. To debug the rest, debug a scratch copy without those nodes, delete it afterward, and report the run as the copy's.
<!--skill-flavor:operate-debug-scratch-copy:end-->
- **Do not pass `--folder-path` or `--folder-key`.** Debug provisions into the personal workspace; another folder fails `403` at `Stage: prepare-custom-debug`, and a personal-workspace `--folder-key` gives `404`. No instance starts.
<!--skill-flavor:debug-shared-resources:start-->
Shared resources reach the run through `resources refresh`, not the debug folder.
<!--skill-flavor:debug-shared-resources:end-->

Exception to the folder rule: an account without a personal workspace (service-principal or CI token, `403` at `get-personal-folder`) passes `--folder-id <number>` to skip that lookup. `prepare-custom-debug` may still `403` for a non-personal folder; tell the user if it does.

Inputs for flows with `.input(...)` parameters:

<!--skill-flavor:operate-debug-inputs:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```
<!--skill-flavor:operate-debug-inputs:end-->

Build inputs from real records, never invented values: an invented key matches no record, the lookup returns `[]`, and the run faults on empty data. Read an entity id with `uip df entities list --output json`, then a live record with `uip df records list <ENTITY_ID> --output json`.

<!--skill-flavor:operate-debug-attachment:start-->
A `types.file` input takes a repeatable local file; the left side is the input name:

```bash
  --attachment <inputName>=<localPath>
```

At runtime the variable is an OBJECT, not a path: scripts read the uploaded name as `$vars.<triggerNodeId>.output.<inputName>.FullName` and see only `ID`, `FullName`, `MimeType`, `Metadata`, never content. A flow that parses the file passes that reference to a file-reading step, such as an RPA process taking it as its file argument ([rpa-workflow.md](rpa-workflow.md#where-the-job-runs)).
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

Emit the label with `<not returned by CLI>` rather than dropping a line. `Data.finalStatus: "Faulted"` means the response contains the cause. `--output-filter` never filters `Message` or `Instructions`; they summarize incidents when PIMS returned any and name `uip maestro flow debug-instance incidents <instanceId>`. If `Data.incidents` is missing or `null` in a projection, run that command. Do not rerun the flow. On the next run, add `incidents:incidents` to the projection, or redirect unfiltered output to a file and search it:
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

`--entry-point <triggerNodeId>` starts that root and makes `--validate` check its schema. A wrong id exits 3 and lists process trigger ids. Without it, the job starts at the release's default entry point. `flow pack` or `solution pack` sets that to the first trigger (the SDK-built default root); other packaging may differ. Pass `--entry-point` whenever the root matters. You do not need `--feed-id`; the CLI reads the release feed.

### Start a Flow when a queue item arrives

Check the registry first. On some tenants `registry search queue` lists
`core.trigger.queue` (and the `core.action.queue.*` nodes) with
`AvailableOnTenant: false`. `registry get core.trigger.queue` then answers
"Node not found", and adding the node is refused with "Node type
'core.trigger.queue' is not enabled for this tenant." Don't copy the node's
definition from anywhere else. Tell the user, then use the fallback below.

The fallback is an Orchestrator queue trigger on the deployed Flow process:

```bash
uip or triggers create --type queue --name "<TRIGGER_NAME>" \
  --release-key <FLOW_PROCESS_KEY> --queue-key <QUEUE_KEY> \
  --items-threshold 1 --items-per-job 1 --max-jobs 1 \
  --runtime-type Serverless --folder-path "<FOLDER_PATH>" --output json
```

- **The job starts without the queue item.** Orchestrator starts a job per
  item, but no job is tied to the item that started it. The Flow's trigger
  output is `null`, so nothing reaches the Flow from `SpecificContent`. The
  Flow, or a Coded Function it calls, must take the next item from the queue
  itself (start a transaction on the queue), cope with getting no item, and
  set the item's result when it is done. Guard every read of the trigger
  output against `null`.
- Keep `--items-threshold 1 --items-per-job 1`: Orchestrator fixes both to 1
  for a Maestro process (one item, one instance) and refuses anything else
  with HTTP 400 "The minimum number of items to trigger the first job must be
  1 for this process type". `--max-jobs` is the one batch setting you choose;
  it caps the instances running at once.
- Don't count on the trigger for items that were already `New` when it was
  created. Orchestrator evaluates it on creation and on each new item, and
  re-checks unprocessed items only on a tenant schedule (every 30 minutes by
  default). Create the trigger before you load the queue, or start one job by
  hand for the backlog.
- `uip or processes create --auto-create-triggers` creates only the connected
  event triggers a package declares (Integration Service triggers). It never
  creates a queue trigger, for any process type; create it with
  `uip or triggers create`.

## Inspect a job

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

Traces are verbose, full timelines, and a last resort except per-iteration timing: `elementExecutions` aggregates per element, so a loop body has one row. Spans stream to stderr, one JSON line each; use `--pretty` for readable lines.

## Instance lifecycle

<!--skill-flavor:operate-instance-id:start-->
Every `instance` command needs `--folder-key` (`-f`) or is rejected before the API. Get it from `uip or folders list --output json` or the job/process context. An instance id comes from debug `Data.instanceId`, `job status`, or `instance list`.
<!--skill-flavor:operate-instance-id:end-->

```bash
uip maestro flow instance pause  <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance retry  <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

`-f` does not filter `instance list`; do not assume every listed instance is in that folder. Never `retry` a faulted instance before reading why it faulted in its debug response or incident; retrying without the cause repeats the failure. When each takes effect and what is recoverable is Orchestrator's lifecycle model, not this skill's; consult `uip maestro flow instance <sub> --help` for flags.

## Evidence boundary

A green `validate` proves only that the emitted `.flow` is well formed. Only a run proves operation, and only against its tenant: successful upload does not prove connections resolve, and a completed debug does not prove correctness. Report the instance identity and CLI-returned status, never an inference.
