# Operate — ship, run, and manage a deployed flow

Everything that touches the cloud: upload, deploy, debug, trigger, inspect, and
instance lifecycle. All of it needs `uip login`; check with
`uip login status --output json`.

Authoring is upstream. Do not ship a flow whose source has not been through the
loop in [`CLI-LOOP.md`](CLI-LOOP.md) — `check` on the source, `compile` to emit,
`validate` on the emitted `.flow`.

## Lay out the emitted flow first

```bash
uip maestro flow format <Name>.flow --output json
```

Layout is not an authoring concern — nothing upstream needs it, and `validate`
passes without it. It becomes one here, the moment the emitted file is opened
by something that draws it: `solution upload`, `flow debug`, or a person
opening the project in a designer. Run `format` before any of those, on the
artifact as last emitted.

`compile` writes a placeholder `ui.position` on each node and no top-level
`layout` block at all — and the canvas renders from `layout`. The placeholders
are one flat row, so a four-armed switch arrives as a single 3,000px line with
the arms in sequence rather than side by side. `format` builds `layout`, fans
the arms onto their own rows, sizes each node by its canvas shape, and reports
`NodesRepositioned`. Skipping it is the most common cause of misshapen nodes in
Studio Web.

## Refresh solution resources first

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```

Run this before `solution upload`, `solution publish` or `flow debug`, every
time. It syncs connection and process resource declarations from the project's
`bindings_v2.json` into the solution, and a stale declaration fails at run time
with a binding error even when the emitted `.flow` is correct — so the symptom
never points at the cause.

There is no positional solution argument. Omit `--solution-folder` only when the
shell is already in the solution root.

## Publish

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

## Debug — a real end-to-end run

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

Operational constraints, each of which has its own failure:

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
- **Do not pass `--folder-path` or `--folder-key`.** Debug provisions into your
  personal workspace; a shared folder fails `HTTP 500` at
  `Stage: prepare-custom-debug` with no instance started. Shared resources reach
  the run through `resources refresh`, not through the debug folder. Use the flag
  only when the account has no personal workspace, or the flow needs
  folder-scoped assets or queues.

Inputs, for a flow with `.input(...)` parameters:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```

Build them from real records, never invented values: an invented key matches no
record, the lookup returns `[]`, and the run faults on empty data. Read an entity
id from `uip df entities list --output json`, then a live record from
`uip df records list <ENTITY_ID> --output json`.

A `types.file` input takes a local file instead, repeatable, and the left side is
the input's own name:

```bash
  --attachment <inputName>=<localPath>
```

At run time that variable is an OBJECT, not a path — a script reads the uploaded
name as `$vars.<triggerNodeId>.output.<inputName>.FullName`.

**A conversational flow cannot be debugged headlessly.** On a flow whose trigger
is `conversationTrigger()`, debug uploads, returns
`Code: FlowDebugStudioWebHandoff` with `Data.studioWebUrl`, and starts no run;
`--timeout` does nothing. Chat from Studio Web (`--open-in-browser` opens it) or
the Maestro VS Code extension.

### Reporting a debug run

`Data.studioWebUrl` and `Data.instanceId` are the **first two lines** of any
summary, before status text — they are what someone needs immediately, not after
scrolling:

```text
Studio Web URL: <url>
Instance ID: <instanceId>
```

Emit the label with `<not returned by CLI>` rather than dropping a line.

`Data.finalStatus: "Faulted"` means the cause is already in that same response.
Read it there rather than re-running. On a faulted run the CLI ignores
`--output-filter` and prints the whole envelope, so redirect and search the file:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json > /tmp/flow-debug.json
```

## Trigger a deployed process

```bash
uip maestro flow process list --output json
uip maestro flow process run <process-key> <folder-key> --output json \
  --inputs '{"numberA": 5}' --attachment <inputName>=<localPath>
```

On `process run` only, `--attachment` overrides `--inputs` on a key collision,
and `--validate` accepts pre-uploaded attachment references for file slots —
they pass the JSON-schema check even though the slot's nominal type is `string`.

## Inspect a job

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

Traces are the full execution timeline and are verbose. They are a last resort,
not a starting point.

## Instance lifecycle

Every `instance` command needs `--folder-key` (`-f`) or it is rejected before
reaching the API. Get one from `uip or folders list --output json`, or from the
job or process context. The instance id comes from a debug run's
`Data.instanceId`, a `job status` response, or `instance list`.

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
