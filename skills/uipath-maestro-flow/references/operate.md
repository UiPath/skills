# Operate — ship, run, and manage a deployed flow

<!--skill-flavor:operate-auth:start-->
Everything that touches the cloud: upload, deploy, debug, trigger, inspect, and
instance lifecycle. All of it needs `uip login`; check with
`uip login status --output json`.
<!--skill-flavor:operate-auth:end-->

Authoring is upstream. Do not ship a flow whose source has not been through the
loop in [`CLI-LOOP.md`](CLI-LOOP.md) — `check` on the source, `compile` to emit,
`validate` on the emitted `.flow`.

## Lay out the emitted flow first

<!--skill-flavor:operate-format:start-->
```bash
uip maestro flow format <Name>.flow --output json
```

**Greenfield files only.** Layout is not an authoring concern — nothing
upstream needs it, and `validate` passes without it. It becomes one here, the
moment a file `compile` wrote from scratch is opened by something that draws
it: `solution upload`, `flow debug`, or a person opening the project in a
designer. Run `format` before any of those, on the artifact as last emitted,
unless its source sets `.layout()` (below).

`compile` writes a placeholder `ui.position` on each node and no top-level
`layout` block. The canvas places each node from its `layout.nodes[<id>]`
entry when there is one, and from `node.ui` otherwise, so a greenfield file
draws at the placeholders. They are one flat row: a four-armed switch arrives
as a single 3,000px line with the arms in sequence rather than side by side.
`format` builds `layout`, fans the arms onto their own rows, sizes each node by
its canvas shape, and reports `NodesRepositioned`. Skipping it on a greenfield
file is the most common cause of misshapen nodes in Studio Web.

**Never format a merged brownfield file.** The original's `layout` already
holds the canvas author's positions, and `merge` keeps them. `format` re-lays
out every node and discards them. Upload or debug the merged file as `merge`
wrote it.
<!--skill-flavor:operate-format:end-->

### Lay out from source instead: `.layout()`, `at()`, `dim()`

The builder can place the nodes itself, so the emitted file never needs `format` — provided every node that is not 96 × 96 carries its size (rule 1).
`.layout({ nodes })` on the flow takes one entry per node, keyed by node id; `at(x, y)` writes an entry, and `dim(width, height)` the size a container needs.
A step's id is its name.
The trigger's is `start` unless `.triggerId()` renamed it.
An End's is the `name` its `.return` gave it, and an unnamed End is `end`, then `end2`, `end3`, … in emission order, so a flow with several unnamed Ends has that many keys to write.
Use it when the request asks for a particular arrangement, or when a decompiled source already carries one ([`brownfield.md`](brownfield.md#the-same-loop-by-hand)).
Otherwise `format` is less work and lays out as well.

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

1. **Use the canvas grid.** A node is 96 px square; a column is 192 px, a row 160 px: `x = 256 + 192 × column`, `y = 144 + 160 × row`.
   The main path goes on row 0 left to right; an error handler or a side arm takes the row below.
   Compile writes 96 × 96 on every node and the designer draws the persisted size, so a node whose canvas shape is larger must carry it: an agent node (`inlineAgent`, `conversationalAgent`, `voiceAgent`) is `at(x, y, dim(288, 96))`, and the next column starts 384 px to its right; a container carries its `dim()` (rule 2), and the row below it starts one row gap (64 px) under its bottom edge, not at the next 160 px row.
2. **A child's position is relative to its container.** A loop or do-while body starts at `at(144, 96)` inside the container's padding, and the container needs a `dim()` that holds the body: the right edge of its rightmost child plus 144, by the bottom edge of its lowest child plus 96, never smaller than `format`'s `dim(560, 320)`.
   For one row of 96 px nodes that is `dim(max(560, 192 × bodyNodes + 192), 320)`; a body with an inline agent, a second row or a nested container is measured from its own entries, not from the node count.
3. **Name every node, or none.** A missing entry falls back to compile's one-row placeholder, which lands on top of your layout; an unknown key fails `compile`.
4. **Never `format` a file whose source sets `.layout()`.** `format` re-lays out every node and discards the source's positions, exactly as it does to a merged brownfield file.
<!--skill-flavor:layout-sdk-version:start-->
5. **`at` and `dim` need `@uipath/maestro-builder-sdk` 6.36.0 or later** — check that `dist/api-index.md` of the SDK copy in use lists them. If not, upgrade that copy: `npm install @uipath/maestro-builder-sdk@latest` in a workspace that has its own `node_modules` copy (it is used before the global one), else `npm install -g @uipath/maestro-builder-sdk@latest`; or write the entry long-hand, `{ position: { x, y } }` with an optional `size: { width, height }`.
<!--skill-flavor:layout-sdk-version:end-->

## Refresh solution resources first

<!--skill-flavor:refresh-command:start-->
```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```
<!--skill-flavor:refresh-command:end-->

<!--skill-flavor:refresh-when:start-->
Run this before `solution upload`, `solution publish` or `flow debug`, every
time. It syncs connection and process resource declarations from the project's
`bindings_v2.json` into the solution, and a stale declaration fails at run time
with a binding error even when the emitted `.flow` is correct — so the symptom
never points at the cause.
<!--skill-flavor:refresh-when:end-->

There is no positional solution argument. Omit `--solution-folder` only when the
shell is already in the solution root.

## Publish

<!--skill-flavor:operate-publish:start-->
"Publish", with no target named, means **Studio Web**:

```bash
uip solution upload <SolutionDir> --output json
```

Pass the solution root — the directory holding the `.uipx` — or `.` from inside
it. From a nested project folder pass `..` or the absolute path, never the
solution name again: that resolves to a child path which does not exist. Report
the Studio Web URL when it succeeds.

Orchestrator is a different path, and only on an explicit request for it,
because it bypasses Studio Web and the flow cannot be visualised or edited
there:

```bash
uip maestro flow pack <project-path> <OutputDir>
```

then `uip solution publish` — see the `uipath-solution` skill. When the target is
genuinely ambiguous, ask before packing.
<!--skill-flavor:operate-publish:end-->

## Debug — a real end-to-end run

<!--skill-flavor:operate-debug:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json
```

The argument is the PROJECT directory, the one holding `project.uiproj`.

`flow debug` executes the flow for real: it sends the emails, posts the
messages, calls the APIs. It is not a validation step — `validate` is. Run it
when the request is for a flow that works; ask when the request stops at build
or validate; and with nobody to ask, report the flow as unverified rather than
letting a passing `validate` stand as the result. Never debug a solution this
run did not scaffold: debug overwrites the Studio Web solution whose
`SolutionId` matches the local `.uipx`.
<!--skill-flavor:operate-debug:end-->

Operational constraints, each of which has its own failure:

<!--skill-flavor:operate-debug-wait:start-->
- **Foreground, with a tool timeout of 10 minutes or more.** It takes 1-5
  minutes and prints its JSON only at exit, so a shell that kills commands after
  1-2 minutes loses the whole payload.
- **Poll the same process if the tool reports it still running.** An empty output
  file means not finished, not failed.
- **Never start a second debug while one is running.** It re-uploads and
  re-executes.
- **Re-run only after changing the flow.** Never to re-read or reshape output the
  completed run already returned.
- **`Debug polling timed out after <N>s` is not a failure.** The run continues
  server-side. Take `instanceId` from stderr and poll
  `uip maestro flow debug-instance status <INSTANCE_ID> --output json`.
<!--skill-flavor:operate-debug-wait:end-->
- **An RPA step does not run under a headless debug** ([rpa-workflow.md](rpa-workflow.md#evidence-boundary)).
<!--skill-flavor:operate-debug-scratch-copy:start-->
- **Every process and connection node must resolve.** A node bound to a
  resource the tenant lacks (a placeholder key awaiting the real process, a stub
  connection) fails provisioning and starts no instance; `Data.missingResources`
  names it, though `check` and `validate` pass it. To debug the rest before the
  resource exists, debug a scratch copy of the project without those nodes,
  delete the copy afterwards, and report the run as the copy's.
<!--skill-flavor:operate-debug-scratch-copy:end-->
- **Do not pass `--folder-path` or `--folder-key`.** Debug provisions into your
  personal workspace; a shared folder fails `HTTP 500` at
  `Stage: prepare-custom-debug` with no instance started.
<!--skill-flavor:debug-shared-resources:start-->
  Shared resources reach
  the run through `resources refresh`, not through the debug folder.
<!--skill-flavor:debug-shared-resources:end-->
  Use the flag
  only when the account has no personal workspace, or the flow needs
  folder-scoped assets or queues.

Inputs, for a flow with `.input(...)` parameters:

<!--skill-flavor:operate-debug-inputs:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```
<!--skill-flavor:operate-debug-inputs:end-->

Build them from real records, never invented values: an invented key matches no
record, the lookup returns `[]`, and the run faults on empty data. Read an entity
id from `uip df entities list --output json`, then a live record from
`uip df records list <ENTITY_ID> --output json`.

<!--skill-flavor:operate-debug-attachment:start-->
A `types.file` input takes a local file instead, repeatable, and the left side is
the input's own name:

```bash
  --attachment <inputName>=<localPath>
```

At run time that variable is an OBJECT, not a path — a script reads the uploaded
name as `$vars.<triggerNodeId>.output.<inputName>.FullName`. A script sees only
that reference (`ID`, `FullName`, `MimeType`, `Metadata`), never the file's
content: a flow that parses an uploaded file hands the reference to a step that
reads files, such as an RPA process taking it as its file argument
([rpa-workflow.md](rpa-workflow.md#where-the-job-runs)).
<!--skill-flavor:operate-debug-attachment:end-->

<!--skill-flavor:operate-debug-entry-point:start-->
**A flow with more than one root starts at the default root.** That is the
trigger marked `isDefaultEntryPoint`, else the first trigger. To run another
root, pass its trigger node id:

```bash
uip maestro flow debug <project-dir> --output json --entry-point <triggerNodeId>
```

A wrong id exits 3 and lists the valid trigger node ids. `Data.entryPoint` names
the trigger the run started from.
<!--skill-flavor:operate-debug-entry-point:end-->

**A conversational flow cannot be debugged headlessly.** When the start root is
a `conversationTrigger()` (the default root, or the one `--entry-point` names),
debug uploads, returns
`Code: FlowDebugStudioWebHandoff` with `Data.studioWebUrl`, and starts no run;
`--timeout` does nothing. Chat from Studio Web (`--open-in-browser` opens it) or
the Maestro VS Code extension.

**An inbound voice flow cannot be debugged at all.** Do not run debug on a
`voiceTrigger()` flow; [voice.md](voice.md#evidence-boundary) has the test loop.

### Reporting a debug run

<!--skill-flavor:operate-debug-report:start-->
`Data.studioWebUrl` and `Data.instanceId` are the **first two lines** of any
summary, before status text — they are what someone needs immediately, not after
scrolling:

```text
Studio Web URL: <url>
Instance ID: <instanceId>
```

Emit the label with `<not returned by CLI>` rather than dropping a line.

`Data.finalStatus: "Faulted"` means the cause is already in that same response.
A projection can drop `Data.incidents`, but `--output-filter` never filters
`Message` and `Instructions`: they summarize the incidents, when PIMS returned
any, and name the `uip maestro flow debug-instance incidents <instanceId>`
command. If `Data.incidents` is missing, or `null` in a projection, run that
command. Do not re-run the flow. On the next run, add `incidents:incidents` to the projection,
or redirect the unfiltered output to a file and search it:
<!--skill-flavor:operate-debug-report:end-->

<!--skill-flavor:operate-debug-redirect:start-->
```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json > /tmp/flow-debug.json
```
<!--skill-flavor:operate-debug-redirect:end-->

## Trigger a deployed process

```bash
uip maestro flow process list --output json
uip maestro flow process run <process-key> <folder-key> --output json \
  --inputs '{"numberA": 5}' --attachment <inputName>=<localPath>
```

On `process run` only, `--attachment` overrides `--inputs` on a key collision,
and `--validate` accepts pre-uploaded attachment references for file slots —
they pass the JSON-schema check even though the slot's nominal type is `string`.

`--entry-point <triggerNodeId>` starts the job at that root, and `--validate`
then checks the inputs against that root's schema. A wrong id exits 3 and lists
the process's trigger node ids. Without it, the job starts at the release's
default entry point. A package from `flow pack` or `solution pack` sets that to
the first trigger in the flow, which for an SDK-built flow is the default root;
a package built another way can differ. Pass `--entry-point` whenever the root
matters. You do not need `--feed-id`; the CLI
reads the feed from the release.

## Inspect a job

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

Traces are the full execution timeline and are verbose. They are a last resort,
not a starting point.

## Instance lifecycle

<!--skill-flavor:operate-instance-id:start-->
Every `instance` command needs `--folder-key` (`-f`) or it is rejected before
reaching the API. Get one from `uip or folders list --output json`, or from the
job or process context. The instance id comes from a debug run's
`Data.instanceId`, a `job status` response, or `instance list`.
<!--skill-flavor:operate-instance-id:end-->

```bash
uip maestro flow instance pause  <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance retry  <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Never `retry` a faulted instance before reading why it faulted — the fault cause
is in the debug response or the incident, and retrying without it repeats the
failure. When each takes effect and what is recoverable is Orchestrator's
lifecycle model, not this skill's; `uip maestro flow instance <sub> --help` has
the flags.

## Evidence boundary

A green `validate` proves the emitted `.flow` is well formed. Only a run proves
the flow works, and only against the tenant it ran on: an upload that succeeds
says nothing about whether the connections resolve, and a debug run that
completes says nothing about whether the answer was right. Report the instance
identity and the status the CLI returned, not an inference from either.
