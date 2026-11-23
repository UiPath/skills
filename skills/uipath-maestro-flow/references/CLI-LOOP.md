# Authoring and product-CLI loops

<!--skill-flavor:loop-choice:start-->
Choose one loop before any build command, as [SKILL.md — Lifecycle](../SKILL.md#lifecycle) says:

- For product-CLI validation/debug, or when `flowSdk.emitOnly`/`FLOW_SDK_EMIT_ONLY=1` is enabled, use only the eval/product-CLI loop. Its scaffold and full command block are in SKILL.md; the debug flags and projections here are only for runtime-evidence bars.
- Otherwise use this file's packaged-SDK local gates.

In eval/product mode, create the solution/project scaffold immediately after choosing the loop, before authoring. After the source first compiles, emit it into that nested project artifact—not `/tmp`—and keep the artifact current after every source edit.
<!--skill-flavor:loop-choice:end-->

Tenant discovery is not a loop phase. First choose the node ([SKILL.md, "Choose the node before writing it"](../SKILL.md)); `check` cannot flag a node never written, so a script or `mock()` substitution goes unflagged. Author from the task's words; source `check` names every owed tenant call—unresolved lookup, unmaterialized object, and out-of-snapshot field—with its exact `registry prepare` command. Spend that one expensive `registry prepare` call once, after the cheap pass finds all other errors.

Do not mix loops or use one mode as the other's probe; their output layouts and evidence contracts differ.

## Source-model and brownfield judgment

TypeScript runs while constructing the graph. Use Flow Branch, Switch, Loop, and action nodes for runtime decisions/work; use native `if` or `for` only for deliberate author-time graph generation.

When editing an existing Flow, edit the supplied `.flow.ts`, preserve existing step names and unaffected wiring, and route an edge through an inserted step rather than retaining the old bypass. If given only raw `.flow` JSON, reconstruct source, compile once to compare the emitted baseline, then edit; these before/after judgments cannot be established from the final artifact.

## Installing the package

<!--skill-flavor:install-package:start-->
Skip the install when the SDK is already installed: `npm ls -g @uipath/maestro-builder-sdk` lists it, or a prepared workspace has `node_modules/@uipath/maestro-builder-sdk` (a workspace copy is used before a global one).
Every `uip maestro flow` authoring verb — `check`, `compile`, `decompile`, `merge` — runs from the installed package, so all of them refuse until it is installed; the package cannot bootstrap itself.

Install globally once per machine, so the workspace needs no `package.json` or `node_modules/`:

```bash
npm install -g @uipath/maestro-builder-sdk
```

The public npm package needs no token and follows npm's configured registry/mirror. Only after E401 or E404 **and** `npm config get @uipath:registry` names GitHub Packages, retry once with `--@uipath:registry=https://registry.npmjs.org` appended. After EACCES, do not use `sudo`; run `npm install --save-dev @uipath/maestro-builder-sdk` in the workspace, which `uip` also finds. Report other failures (including timeout or mirror refusal) for the user's network/registry to fix; do not route around them.

When `uip` reports the SDK below minimum, run the command in its `Instructions`, which specifies `-g` or `--save-dev` for the discovered copy. Connector-definition fetching requires `@uipath/maestro-builder-sdk` 6.97.0 or later, through either `uip` or `flow-sdk`. When `uip` says the SDK cannot fetch definitions, run its named upgrade (`npm install -g @uipath/maestro-builder-sdk@latest`, or `--save-dev` for a workspace copy); on cloud, `uip maestro registry pull` also works.

### Ask the SDK what it supports

Read this even when the SDK is already installed.
From `@uipath/maestro-builder-sdk` 6.101.0 the SDK can say which features it has: run `npx --no flow-sdk capabilities`.
`--no` stops npx from downloading anything: it runs the workspace copy, else the global one.
The command prints the name and version, then one feature name per line:

```text
$ npx --no flow-sdk capabilities
@uipath/maestro-builder-sdk 6.101.0 (gitref 1a2b3c4)
json-result
flow-check-baseline
flow-pipeline-strict
...
```

`--json` prints one object instead: `{"ok":true,"name":"@uipath/maestro-builder-sdk","version":"6.101.0","gitref":"1a2b3c4","capabilities":["json-result",...]}`.
Test one feature with `npx --no flow-sdk capabilities | grep -qx <name>`.
Read the answer this way:

- The list prints and has the name: the feature is there.
- The list prints and lacks the name: the feature is not there. Upgrade the SDK, or use the fallback the reference gives.
- `error: unknown command 'capabilities'`: the SDK is older than 6.101.0. That says nothing about the features below, which all shipped earlier. For one of them, follow the version note in its reference (for example, `check --baseline` works from 6.64.0).

The names are stable:

| Name | Feature |
|---|---|
| `flow-check-baseline` | `check --baseline <original>.flow` ([brownfield.md](brownfield.md#check-only-what-you-changed-check---baseline)) |
| `flow-pipeline-strict` | `node .flow-sdk/<Name>.pipeline.mjs --strict` |
| `flow-decompile-scripts` | decompile prints scripts as functions and takes `--scripts string` |
| `flow-script-metadata` | the `$metadata` parameter of a script function |
| `flow-merge-source` | `merge <Name>.flow.ts --original <Name>.flow`, from the `// @decompiled-from` stamp |
| `project-min-version` | `flowSdk.minVersion`, below |
| `flow-entry-point-default` | `.entryPoint(id, spec, { default: true })` ([manual-trigger.md](manual-trigger.md#multiple-entry-points)) |

To pin one SDK floor for a project, add `"flowSdk": { "minVersion": "<version>" }` to its `package.json`.
From 6.101.0, `compile`, `check`, `decompile` and `merge` then refuse an older SDK with exit 2. The message names the copy that ran and the `npm install ...@latest` command that upgrades it (`--save-dev` in the project for a workspace copy, else `-g`).
Both need `@uipath/maestro-builder-sdk` 6.101.0 or later (UiPath/builder-sdk#2009). An older SDK ignores `minVersion`, so a floor only takes effect once the SDK in use is 6.101.0 or later; upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` (or `--save-dev` for a workspace copy).
<!--skill-flavor:install-package:end-->

## Local authoring hard gates

<!--skill-flavor:local-gates:start-->
Use this section only with emit-only disabled. Use source `check` as the fast no-output loop; with a library and `.flow-sdk/bindings.json` beside the source it reports every connector-input and binding refusal that `compile` would raise. Compile to emit, then run product static check on the artifact. There is no compiled-artifact `check`; `validate` is that rung. `validate` judges connector and other tenant nodes against the node cache `registry pull` wrote for your login (CLI 1.206 and earlier judge built-in nodes against that cache too); after a stale-handle error, run `uip maestro flow registry pull --force` once and validate again. `compile` does not run `check` and writes any serializable flow, so never compile with a `check` error. Ignore only an error whose own message says to ignore it, when applicable (for example `INLINE_AGENT_PROMPT_JSON_TEXT` when JSON is mentioned only as data). For a brownfield edit, add `--baseline <original.flow>` ([brownfield.md](brownfield.md#check-only-what-you-changed-check---baseline)).

Run this sequence in order; run `registry prepare` only when `check` names it:

```bash
uip maestro flow check .flow-sdk/<Name>.flow.ts --source
# run each prepare the check names, with the exact command it prints:
uip maestro registry prepare <key> --action <action> [--object <name>] [--resolve <field>:<by>=<value>] [-f <parent>=<value>]
uip maestro flow check .flow-sdk/<Name>.flow.ts --source    # re-check until clean
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow
uip maestro flow validate <Name>.flow --output json
```

Review warnings deliberately; task or release policy determines whether one blocks release.

Layout is not a step in this sequence. `compile` lays out a source with no
`.layout()` the way `uip maestro flow format` does, so the file is ready for
`solution upload`, `flow debug`, or a designer. Do not run `format` on a merged
brownfield file, or on one whose source sets `.layout()`: `format` re-lays out
every node, so it discards the positions the author chose. See
[`operate.md`](operate.md#layout-of-the-emitted-flow).

These authoring verbs require a prerelease of `@uipath/cli` that exposes them.
<!--skill-flavor:local-gates:end-->

## Product-CLI scaffold

<!--skill-flavor:product-cli-scaffold:start-->
The scaffold (`uip solution init`, `flow init --sdk-source` for the seed, and `--automate` for a Maestro Automate project) is in [SKILL.md — Project layout](../SKILL.md#project-layout); keep it there so copies cannot drift.
<!--skill-flavor:product-cli-scaffold:end-->

## Eval/product-CLI packaging: emit-only

Emit-only rules—mode selection by `package.json`, and `compile`/`check` behavior—and the compile → validate → format → refresh → debug block are in [SKILL.md — Lifecycle](../SKILL.md#lifecycle). The following adds runtime-evidence detail.

## Product validation and conditional bindings

### Reading product validation

The JSON envelope has top-level `Result`; successful validation also reports `Data.Status: "Valid"` and may contain `Data.Warnings`. Treat warnings as failures except the reviewed shared-connection advisory and `err()` read diagnostics in [`error-handling.md`](error-handling.md#reading-the-failure). Preserve an exception's exact code/text and rationale; do not broaden the allowlist.

### Bounded completion

Match final evidence to the acceptance bar after the last edit:

- Validate-only: require `Data.Status: "Valid"` plus the required structural self-check, then stop; do not debug merely for confidence.
- For each distinct behavior claim named by the bar, plan at most one bounded debug with inputs/attachments that exercise it; combine compatible claims and do not repeat equivalent inputs.
- If one unknown blocks final wiring, run one bounded experiment distinguishing the choices, apply its answer, and return to final emit/validate. Do not create scratch-solution families.

If evidence cannot be obtained within the bound, report the evidence boundary rather than repeating debug launches.

### Managed HTTP: authored connection bindings

`http({ managed: true, ... })` requires real connection and folder bindings for connector-authenticated product debug. Select an enabled HTTP connection:

```bash
uip is connections list --all-folders \
  --output-filter "[?ConnectorKey=='uipath-uipath-http'].{Id:Id,FolderKey:FolderKey,Name:Name}"
```

Declare symbolic entries in `bindings.json` and pass both names to the node:

```ts
http({ managed: true, method: 'GET', url: '/me',
  connection: 'spotifyHttp', folder: 'shared' })
```

Compilation resolves the names and writes connector-authenticated node detail and required product bindings into `.flow`. Do not patch them into the artifact after emission; compilation overwrites that edit. Omit both options only for manual/implicit authentication.

## Refresh, debug, and preserve evidence

<!--skill-flavor:debug-flags:start-->
`flow debug` takes the project directory, not the `.flow` file; run resource refresh first. From the solution directory, `<Name>` names the project. A `500` at `prepare-custom-debug` is transient: retry once. A `403`/`404` there comes from a folder flag: drop it unless the account has no personal workspace ([operate.md](operate.md#debug--a-real-end-to-end-run)). Use only flags required by the claim:

| Need | Exact form |
|---|---|
| JSON inputs | `-i '{"name":"value"}'` or `--inputs @inputs.json` |
| File input | `--attachment <input-name>=<path>`; repeat for multiple files |
| Folder | omit it; debug uses your personal workspace. With none (service-principal or CI token): `--folder-id <number>` |
| Start trigger | `--entry-point <trigger-node-id>`; omit to start at the default root |
| Poll bound | `--timeout <seconds> --poll-interval <milliseconds>`; keep the stated task bound |
| Compact read-back | `--output-filter "<JMESPath>" --output json` |
| Quiet logs | `--log-level error`, or `--log-file <path>` to move them off the stream entirely |
<!--skill-flavor:debug-flags:end-->

<!--skill-flavor:debug-readback:start-->
### `--output-filter` is JMESPath, and three things about it are worth knowing

Use `'single-quoted'` for a string literal, not `` `backticked` ``; backticks delimit a JSON literal, so `` `Completed` `` is invalid. Both forms below work; prefer the first (its failure is loud), wrapped in DOUBLE quotes so the inner `'…'` survives the shell:

```bash
--output-filter "elementExecutions[?status!='Completed']"     # raw string literal
--output-filter 'elementExecutions[?status!=`"Completed"`]'   # JSON literal
```

Project from `Data`, not the envelope: `Result` and `Code` remain top-level, so a filter naming `finalStatus` reads `Data.finalStatus`. Filter rather than pipe through `jq`; a rejected filter exits non-zero with a parse error, so fix it rather than falling back to `--output json | jq`.

### Ready-made projections — copy one, do not compose your own

Use the narrowest verified projection that answers the claim:

```bash
# Did it finish? The cheapest possible check.
--output-filter "{status:finalStatus,instance:instanceId}"

# The standard read-back: status, where to look, what did NOT complete, the
# flow's declared outputs — one <Out>:variables.globals.<Out> pair per output —
# and incidents.
--output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,\
failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},\
weatherVerdict:variables.globals.weatherVerdict,incidents:incidents}"

# Every global, including each step's raw output — diagnosis only (see below).
--output-filter "variables.globals"

# Every element's status, when you need the path the run actually took.
--output-filter "elementExecutions[].{id:elementId,status:status}"
```

`variables.globals` is a flat map whose keys may contain dots. A step output is `"<step>.output.<field>"`, alongside each declared global's bare name:

```jsonc
{ "product": 42, "start.output.a": 6, "multiply.output": 42, "multiply.error": null }
```

Read bare globals as `variables.globals.product`; quote dotted keys, flipping shell quoting:

```bash
--output-filter '{status:finalStatus,raw:variables.globals."multiply.output"}'
```

Name only globals needed by the claim; never project all for a verdict. Each step output is whole (HTTP response body/headers, or a connector's full record). One geocoding call can make hundreds of lines; `tail`/`head` can drop `status` and `failed`, requiring another `flow debug` run (~30 s against the cloud). Name each declared output and add a step output only when that step is the claim.

A completed envelope has no `incidents`; its `Data` carries `finalStatus`, `entryPoint`, `instanceId`, `studioWebUrl`, `jobKey`, `runId`, `folderKey`, `solutionId`, `variables`, and `elementExecutions`, plus `variablesFetch` when variable reading retried; `variablesError` replaces `variables` when it fails. Thus `incidents:incidents` is `null`. A fault usually carries `Data.incidents` (absent if PIMS returns none or fetching fails); `--output-filter` projects failure `Data` too, so add `incidents:incidents` to keep them. If missing, fetch with the separate `debug-instance incidents` command below using the returned `instanceId`. With `variablesError`, outputs are unknown, not empty: run the re-read command its `Instructions` give.

For direct-input evidence (a real run: [ask first](operate.md#debug--a-real-end-to-end-run)), refresh first and retain `Result`, status, instance, URL, failed executions, required declared outputs (`<Out>` is each `direction: out` global), and incidents:

```bash
( cd "<Solution>" && uip solution resources refresh --solution-folder . --output json )
( cd "<Solution>" && uip maestro flow debug <Name> --log-level error \
  --inputs @inputs.json \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},<Out>:variables.globals.<Out>,incidents:incidents}" \
  --output json )
```

The envelope still carries `Result`; the projection selects `Data`. `Completed` with expected globals and empty `failed` evidences the product-runtime path; process exit code alone does not. Omit the filter only to diagnose an unretained field. Fetch incidents by `instance` only when a failed run has no `Data.incidents` (`null` in a projection) or the projection dropped it:

```bash
uip maestro flow debug-instance incidents <instanceId> \
  --output-filter "[*].{E:ElementId,C:ErrorCode,M:ErrorMessage,D:ErrorDetails}"
```

`ErrorDetails` commonly contains the service response or unresolved-resource value omitted by the summary.
<!--skill-flavor:debug-readback:end-->

## CLI output conventions

Use `--output json`, not `--format json`; use `--output-filter '<JMESPath>'` for `Data`. Successful commands may print progress/update text to stderr, so judge success from structured `Result`, status, outputs, and incidents—not stderr.

Product debug creates real side effects. Use sandbox resources and serialize runs sharing queues, issues, mailboxes, or other mutable tenant state.
