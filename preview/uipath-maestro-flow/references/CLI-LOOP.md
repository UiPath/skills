# Authoring and product-CLI loops

Choose one loop before running any build command:

- if the task requests product-CLI validation/debug, or the workspace enables
  `flowSdk.emitOnly`/`FLOW_SDK_EMIT_ONLY=1`, use only the eval/product-CLI loop;
- otherwise use the packaged-SDK local gates.

In eval/product mode, create the solution/project scaffold immediately after
choosing the loop, before tenant discovery or source authoring. Once the source
first compiles, emit it into that nested project artifact—not `/tmp`—and keep
the artifact current after every source edit.

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

## Local authoring hard gates

Use this section only when emit-only mode is disabled. Source and compiled
checks are separate commands: use the source check as the fast no-output inner
loop, compile to emit, then run the deep checker on the artifact.

```bash
uip maestro flow check <Name>.flow.ts --source
uip maestro flow compile <Name> -o <Name>.flow
uip maestro flow check <Name>.flow --compiled
```

Warnings require deliberate review; whether one blocks a release comes from the
surrounding task or release policy.

These authoring verbs require a prerelease of `@uipath/cli` that exposes them.

## Product-CLI scaffold

Product debug needs a solution containing a Flow project. Keep the authored
source at the workspace root beside `node_modules/`, and create the nested
scaffold once:

```bash
uip solution init <Solution>
( cd <Solution> && uip maestro flow init <Name> )
```

`<Solution>` and `<Name>` are the request's own names, used verbatim: a request
that gives one name for both ("inside a solution of the same name") uses it for
both, and a request that names only the Flow uses `<Name>` for both. The result
has three related names: `<Name>.flow.ts`, the `<Name>` project directory, and
`<Name>.flow` inside that project. Keep them aligned for this scaffold so each
command addresses the intended project; `compile -o` remains the authority over
where the emitted file is written.

## Eval/product-CLI packaging: emit-only

The product-runtime eval sets `flowSdk.emitOnly` in `package.json` (with
`FLOW_SDK_EMIT_ONLY=1` retained as an environment override). Emit-only is a
property of the **project**, not of the directory you run from: the mode is the
nearest `package.json` up the tree that actually declares `flowSdk.emitOnly`, so
compiling from a scaffolded solution subdirectory behaves exactly as it does
from the project root. A nested `package.json` that says nothing about `flowSdk`
inherits; one that sets `emitOnly: false` opts out. In that mode
`uip maestro flow compile` only serializes source, and `uip maestro flow check`
refuses, because product validation owns structural verification. The required
base pass is emit, any required artifact bindings, then validate. Add resource
refresh and debug only when the stated acceptance bar requires product-runtime
behavior evidence:

```bash
uip maestro flow compile <Name>.flow.ts -o <Solution>/<Name>/<Name>.flow
uip maestro flow validate <Solution>/<Name>/<Name>.flow --output json
# Only for a stated runtime-behavior claim:
( cd <Solution> && uip solution resources refresh --solution-folder . --output json )
( cd <Solution> && uip maestro flow debug <Name> --log-level error \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},globals:variables.globals}" \
  --output json )
```

This loop has exactly one emitted artifact:
`<Solution>/<Name>/<Name>.flow`. Never emit a second root-level `<Name>.flow`;
validators and evidence collectors cannot choose safely between duplicates.
Re-run the whole sequence after the final source or binding edit.

## Product validation and conditional bindings

### Reading product validation

The JSON envelope has top-level `Result`; a successful validation also reports
`Data.Status: "Valid"` and may carry `Data.Warnings`. Treat warnings as failures
except for the reviewed shared-connection advisory. Preserve any exception's
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

# The standard read-back: status, where to look, what did NOT complete, all globals.
--output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,\
failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},\
globals:variables.globals}"

# Just the values the flow produced.
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

**There is no `incidents` in this envelope.** `Data` carries exactly
`finalStatus`, `instanceId`, `studioWebUrl`, `jobKey`, `runId`, `folderKey`,
`solutionId`, `variables` and `elementExecutions` — an `incidents:incidents`
projection silently yields `null`. Incidents come from the separate
`debug-instance incidents` call below, keyed by the `instanceId` you just read.

For example, a direct-input claim can keep the useful status, outputs, and
diagnostics in one read-back instead of printing the full execution envelope:

```bash
( cd <Solution> && uip solution resources refresh --solution-folder . --output json )
( cd <Solution> && uip maestro flow debug <Name> --log-level error \
  --inputs @inputs.json \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},globals:variables.globals}" \
  --output json )
```

The top-level envelope still carries `Result`; the projection above selects
from `Data`. Read and retain `Result`, the projected status/instance/URL, the
`failed` element executions, and the globals the claim needs.
`Completed` with the expected globals and an empty `failed` is evidence for the
product-runtime path; a bare process exit code is not. Omit the filter only when
diagnosing a field the projection did not retain.

Incidents are **not** in this envelope — fetch them by the `instance` you just
read, and only when something actually failed.

For a fault, query the backend incident payload with the returned instance id:

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
