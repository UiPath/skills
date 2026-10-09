# Authoring and product-CLI loops

Choose one loop before running any build command, as
[SKILL.md — Lifecycle](../SKILL.md#lifecycle) says:

- if the task requests product-CLI validation/debug, or the workspace enables
  `flowSdk.emitOnly`/`FLOW_SDK_EMIT_ONLY=1`, use only the eval/product-CLI loop.
  Its scaffold and its full command block are in SKILL.md, so a greenfield run
  needs nothing from this file; the debug flags and projections below are for
  runs whose acceptance bar needs product-runtime evidence;
- otherwise use the packaged-SDK local gates (this file).

In eval/product mode, create the solution/project scaffold immediately after
choosing the loop, before authoring the source. Once the source first
compiles, emit it into that nested project artifact—not `/tmp`—and keep the
artifact current after every source edit.

Tenant discovery is not a phase of either loop. The one step before authoring
is choosing the node ([SKILL.md, "Choose the node before writing it"](../SKILL.md)):
`check` cannot flag a node you never wrote, so a script or `mock()` written in
its place goes unflagged.
After that, author the source from the task's own words; the source `check`
names every tenant call you owe —
each unresolved lookup, unmaterialized object, and out-of-snapshot field, with
the exact `registry prepare` command — so the one expensive call is spent
once, after the cheap pass has found everything else that is wrong.

Do not mix the two loops in one workspace or use one mode as a probe for the
other. Their output layouts and evidence contracts are different.

## Source-model and brownfield judgment

TypeScript executes while the graph is constructed. Use Flow Branch, Switch,
Loop, and action nodes for decisions or work that must happen at runtime; a
native `if` or `for` is appropriate only for deliberate author-time graph
generation.

When editing an existing Flow, change the supplied `.flow.ts`, preserve existing
step names and unaffected wiring, and move an edge through an inserted step
rather than leaving the old bypass in place. If the input is only raw `.flow`
JSON, reconstruct source, compile once to compare the emitted baseline, and
then make the requested edit. Those are before/after judgments no final
artifact can establish.

## Installing the package

Skip this when the SDK is already installed: `npm ls -g @uipath/maestro-builder-sdk` lists it, or a prepared workspace has `node_modules/@uipath/maestro-builder-sdk` (a workspace copy is used before a global one).
Every `uip maestro flow` authoring verb — `check`, `compile`, `decompile` — runs from the installed package, so all of them refuse until it is installed; the package cannot bootstrap itself.
Install it once per machine, globally, so the workspace needs no `package.json` or `node_modules/`:

```bash
npm install -g @uipath/maestro-builder-sdk
```

The package is public on npmjs.com, so this needs no token and follows whatever registry or mirror the machine's npm config names.
Only if it fails with E401 or E404 **and** `npm config get @uipath:registry` names GitHub Packages, retry once with `--@uipath:registry=https://registry.npmjs.org` appended.
If it fails with EACCES (npm's global folder is not writable), do not use `sudo`; install into the workspace instead with `npm install --save-dev @uipath/maestro-builder-sdk`, which `uip` also finds.
Any other failure (a timeout, a mirror refusing the package) is the user's network or registry to fix, so report it rather than routing around it.
When `uip` reports the SDK is below its minimum version, run the command its `Instructions` give: it names `-g` or `--save-dev` depending on which copy it found.

## Local authoring hard gates

Use this section only when emit-only mode is disabled. Use the source check as
the fast no-output inner loop (with a library and `.flow-sdk/bindings.json` beside the
source it reports every connector-input and binding refusal `compile` would
raise), compile to emit, then run the product's static check on the artifact.
There is no compiled-artifact `check`; `validate` is that rung.

The full sequence, in order — `registry prepare` appears only where `check`
names it, never before the source exists:

```bash
uip maestro flow check .flow-sdk/<Name>.flow.ts --source
# run each prepare the check names, with the exact command it prints:
uip maestro registry prepare <key> <action> [--object <name>] [--resolve <field>:<by>=<value>] [-f <parent>=<value>]
uip maestro flow check .flow-sdk/<Name>.flow.ts --source    # re-check until clean
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow
uip maestro flow validate <Name>.flow --output json
```

Warnings require deliberate review; whether one blocks a release comes from the
surrounding task or release policy.

Layout is deliberately absent from this sequence. `uip maestro flow format`
is not an authoring gate — `validate` passes without it and nothing upstream
reads a position. It is required before the emitted file reaches anything that
draws it: `solution upload`, `flow debug`, or a person opening the project in a
designer. See [`operate.md`](operate.md#lay-out-the-emitted-flow-first).

These authoring verbs require a prerelease of `@uipath/cli` that exposes them.

## Product-CLI scaffold

The scaffold (`uip solution init`, `flow init --sdk-source` for the seed, and
`--automate` for a Maestro Automate project) is in
[SKILL.md — Project layout](../SKILL.md#project-layout). It is kept in one place
so the two copies cannot drift.

## Eval/product-CLI packaging: emit-only

The emit-only rules (which `package.json` decides the mode, what `compile` and
`check` do in it) and the compile → validate → format → refresh → debug block
are in [SKILL.md — Lifecycle](../SKILL.md#lifecycle). The sections below add the
detail a runtime-evidence bar needs.

## Product validation and conditional bindings

### Reading product validation

The JSON envelope has top-level `Result`; a successful validation also reports
`Data.Status: "Valid"` and may carry `Data.Warnings`. Treat warnings as failures
except for the reviewed shared-connection advisory and the `err()` read
diagnostics in [`error-handling.md`](error-handling.md#reading-the-failure). Preserve any exception's
exact code/text and rationale instead of broadening an allowlist.

### Bounded completion

Match the final evidence to the stated acceptance bar after the last edit:

- For a validate-only bar, `Data.Status: "Valid"` plus the required structural
  self-check is completion. Stop there; do not run debug only for confidence.
- For each distinct behavior claim named by the bar, plan at most one bounded
  debug with the inputs and attachments that exercise it. One run may cover
  compatible claims; do not repeat equivalent inputs.
- If one unknown still blocks the final wiring, run one bounded experiment that
  distinguishes the choices, apply its answer, and return to the final
  emit/validate pass. Do not create a scratch-solution family.

If the requested evidence cannot be obtained inside that bound, report the
evidence boundary instead of replacing it with repeated debug launches.

### Managed HTTP: authored connection bindings

`http({ managed: true, ... })` needs real connection and folder bindings for
connector-authenticated product debug. Select an enabled HTTP connection:

```bash
uip is connections list --all-folders \
  --output-filter "[?ConnectorKey=='uipath-uipath-http'].{Id:Id,FolderKey:FolderKey,Name:Name}"
```

Declare symbolic entries in `bindings.json`, then pass both names to the node:

```ts
http({ managed: true, method: 'GET', url: '/me',
  connection: 'spotifyHttp', folder: 'shared' })
```

Compilation resolves those names and writes both the connector-authenticated
node detail and the required product bindings into the emitted `.flow`. Do not
patch them into the artifact after emission; that edit would be lost on the next
compile. Omit both options only when manual/implicit authentication is intended.

## Refresh, debug, and preserve evidence

`flow debug` takes the project directory, not the `.flow` file, and resource
refresh must run first. From the solution directory, `<Name>` names that project.
These are the common flags; use only the ones the behavior claim needs:

| Need | Exact form |
|---|---|
| JSON inputs | `-i '{"name":"value"}'` or `--inputs @inputs.json` |
| File input | `--attachment <input-name>=<path>`; repeat for multiple files |
| Folder | one of `--folder-id`, `--folder-key`, or `--folder-path`; omit to auto-detect |
| Poll bound | `--timeout <seconds> --poll-interval <milliseconds>`; keep the stated task bound |
| Compact read-back | `--output-filter "<JMESPath>" --output json` |
| Quiet logs | `--log-level error`, or `--log-file <path>` to move them off the stream entirely |

### `--output-filter` is JMESPath, and three things about it are worth knowing

**A string literal is `'single-quoted'`, not `` `backticked` ``.** Backticks
delimit a JSON literal, so `` `Completed` `` is a syntax error — bare words are
not JSON. Both forms below work; prefer the first, because its failure is loud.
Wrap the whole expression in DOUBLE quotes so the inner `'…'` survives the shell:

```bash
--output-filter "elementExecutions[?status!='Completed']"     # raw string literal
--output-filter 'elementExecutions[?status!=`"Completed"`]'   # JSON literal
```

**The projection selects from `Data`, not from the envelope.** `Result` and
`Code` stay at the top level and are still printed, so a filter naming
`finalStatus` reads `Data.finalStatus`.

**Filter, do not post-process.** `--output-filter` is cheaper and less brittle
than piping the whole envelope through `jq`, and much cheaper than hunting for
the JSON inside interleaved log lines. If a filter is rejected, fix the
expression rather than falling back to `--output json | jq` — a rejected filter
exits non-zero with the parse error, so the fix is usually one edit.

### Ready-made projections — copy one, do not compose your own

These are verified against a real `flow debug` envelope. Pick the narrowest one
that answers the claim; composing a projection from scratch is what turns a
read-back into seven tool calls.

```bash
# Did it finish? The cheapest possible check.
--output-filter "{status:finalStatus,instance:instanceId}"

# The standard read-back: status, where to look, what did NOT complete, and the
# flow's declared outputs — one <Out>:variables.globals.<Out> pair per output.
--output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,\
failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},\
weatherVerdict:variables.globals.weatherVerdict}"

# Every global, including each step's raw output — diagnosis only (see below).
--output-filter "variables.globals"

# Every element's status, when you need the path the run actually took.
--output-filter "elementExecutions[].{id:elementId,status:status}"
```

**`variables.globals` is a FLAT map, and its keys contain dots.** A step output is
`"<step>.output.<field>"`, alongside the bare name of every declared global:

```jsonc
{ "product": 42, "start.output.a": 6, "multiply.output": 42, "multiply.error": null }
```

So a bare global reads as `variables.globals.product`, and a dotted key needs
quoting — which flips the shell quoting, because the expression now contains
double quotes instead of single ones:

```bash
--output-filter '{status:finalStatus,raw:variables.globals."multiply.output"}'
```

**Name the globals the claim needs; never project all of them for a verdict.**
Every step's output is in this map whole: an HTTP step carries its response
body and headers, a connector step its full record. One geocoding call can make
the read-back hundreds of lines. Trimming it with `tail` or `head` then drops
`status` and `failed`, and the only way back is a second `flow debug` run
(~30 s against the cloud). Name each declared output, and add a step's output
only when the claim is about that step.

**`incidents` is filled only for a faulted run.** `Data` carries `finalStatus`,
`instanceId`, `studioWebUrl`, `jobKey`, `runId`, `folderKey`, `entryPoint`,
`solutionId`, `variables` and `elementExecutions`; when the run faulted, the CLI
also fetches its incidents into `Data.incidents` and names the first in the
error `Message`. When the outputs could not be read, `Data.variablesError`
replaces `variables`: treat the outputs as unknown, not empty, and read them
with `uip maestro flow debug-instance variables <instanceId>`.

For example, a direct-input claim can keep the useful status, outputs, and
diagnostics in one read-back instead of printing the full execution envelope:

```bash
( cd "<Solution>" && uip solution resources refresh --solution-folder . --output json )
( cd "<Solution>" && uip maestro flow debug <Name> --log-level error \
  --inputs @inputs.json \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},<Out>:variables.globals.<Out>}" \
  --output json )
```

The top-level envelope still carries `Result`; the projection above selects
from `Data`. Read and retain `Result`, the projected status/instance/URL, the
`failed` element executions, and the declared outputs the claim needs
(`<Out>` is each `direction: out` global, as in the standard read-back above).
`Completed` with the expected globals and an empty `failed` is evidence for the
product-runtime path; a bare process exit code is not. Omit the filter only when
diagnosing a field the projection did not retain.

For the full backend incident payload of a fault, or for a run the CLI did not
wait on, query it by the returned instance id:

```bash
uip maestro flow debug-instance incidents <instanceId> \
  --output-filter "[*].{E:ElementId,C:ErrorCode,M:ErrorMessage,D:ErrorDetails}"
```

`ErrorDetails` commonly contains the service response or unresolved-resource
value that the summary message omits.

## CLI output conventions

Use `--output json`, not `--format json`. Use `--output-filter '<JMESPath>'` to
select fields from `Data`. Some successful commands print update/progress text
to stderr, so judge success from the structured `Result`, status, outputs, and
incidents rather than from the presence of stderr.

Product debug creates real side effects. Use sandbox resources and serialize
runs that share queues, issues, mailboxes, or other mutable tenant state.
