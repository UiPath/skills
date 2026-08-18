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
uip solution init <Name>Sol
( cd <Name>Sol && uip maestro flow init <Name> )
```

The result has three related names: `<Name>.flow.ts`, the `<Name>` project
directory, and `<Name>.flow` inside that project. Keep them aligned for this
scaffold so each command addresses the intended project; `compile -o` remains
the authority over where the emitted file is written.

## Eval/product-CLI packaging: emit-only

The product-runtime eval sets `flowSdk.emitOnly` in `package.json` (with
`FLOW_SDK_EMIT_ONLY=1` retained as an environment override). Emit-only is a
property of the **project**, not of the directory you run from: the mode is the
nearest `package.json` up the tree that actually declares `flowSdk.emitOnly`, so
compiling from a scaffolded solution subdirectory behaves exactly as it does
from the project root. A nested `package.json` that says nothing about `flowSdk`
inherits; one that sets `emitOnly: false` opts out. In that mode
`uip maestro flow compile` only serializes source, and `uip maestro flow check`
refuses, because product validate/debug are the experiment's gates. A complete
pass is emit, any required artifact bindings, validate, resource refresh, then
debug:

```bash
uip maestro flow compile <Name> -o <Name>Sol/<Name>/<Name>.flow
uip maestro flow validate <Name>Sol/<Name>/<Name>.flow --output json
( cd <Name>Sol && uip solution resources refresh --solution-folder . --output json )
( cd <Name>Sol && UIPCLI_LOG_LEVEL=warn uip maestro flow debug <Name> --output json )
```

This loop has exactly one emitted artifact:
`<Name>Sol/<Name>/<Name>.flow`. Never emit a second root-level `<Name>.flow`;
validators and evidence collectors cannot choose safely between duplicates.
Re-run the whole sequence after the final source or binding edit.

## Product validation and conditional bindings

### Reading product validation

The JSON envelope has top-level `Result`; a successful validation also reports
`Data.Status: "Valid"` and may carry `Data.Warnings`. Treat warnings as failures
except for the reviewed shared-connection advisory. Preserve any exception's
exact code/text and rationale instead of broadening an allowlist.

### Managed HTTP: emitted-artifact bindings in emit-only projects

`http({ managed: true, ... })` needs real connection and folder bindings for
product debug. After **every emit**, select an enabled HTTP connection and add
both bindings to the emitted artifact:

```bash
uip is connections list --all-folders \
  --output-filter "[?ConnectorKey=='uipath-uipath-http'].{Id:Id,FolderKey:FolderKey,Name:Name}"

uip maestro flow binding add <Name>Sol/<Name>/<Name>.flow \
  "uipath-uipath-http connection" connection <connection-id> \
  --resource-key <connection-id> --property-attribute ConnectionId --output json

uip maestro flow binding add <Name>Sol/<Name>/<Name>.flow \
  "FolderKey" folderKey <folder-key> \
  --resource-key <folder-key> --property-attribute FolderKey --output json
```

These are product bindings embedded in the emitted `.flow`, not the symbolic
connector names authored in a root-level `bindings.json`. A managed-HTTP-only
flow needs no authored `bindings.json`, but it still needs the two
emitted-artifact bindings for product debug. Re-emission overwrites the artifact,
so run both `binding add` commands again after the last compile.

## Refresh, debug, and preserve evidence

`flow debug` takes the project directory, not the `.flow` file, and resource
refresh must run first. From the solution directory, `<Name>` names that project:

```bash
( cd <Name>Sol && uip solution resources refresh --solution-folder . --output json )
( cd <Name>Sol && UIPCLI_LOG_LEVEL=warn uip maestro flow debug <Name> --output json )
```

Read and retain the debug envelope's `Result`, `Data.instanceId`,
`Data.finalStatus`, `Data.studioWebUrl`, incomplete/faulted element executions,
global outputs, and incidents. `Completed` with the expected outputs and no
unexpected incidents is evidence for the product-runtime path; a bare process
exit code is not.

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
