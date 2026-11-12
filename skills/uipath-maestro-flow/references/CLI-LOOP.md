# Authoring and product-CLI loops

<!--skill-flavor:loop-choice:start-->
Choose one loop before any build command, per [SKILL.md — Lifecycle](../SKILL.md#lifecycle):

- For product-CLI validation/debug, or when `flowSdk.emitOnly`/`FLOW_SDK_EMIT_ONLY=1` is enabled, use only the eval/product-CLI loop. Its scaffold and full command block are in SKILL.md; the debug flags and projections here apply only when product-runtime evidence is required.
- Otherwise use this file's packaged-SDK local gates.

In eval/product mode, create the solution/project scaffold immediately after choosing the loop and before authoring. After the first successful compile, emit into that nested project artifact, not `/tmp`, and refresh it after every source edit.
<!--skill-flavor:loop-choice:end-->

Tenant discovery is not a loop phase. First choose the node ([SKILL.md, "Choose the node before writing it"](../SKILL.md)); `check` cannot flag a node replaced by a script or `mock()`. Author from the task's words. Source `check` names every owed tenant call—unresolved lookup, unmaterialized object, and out-of-snapshot field—with the exact `registry prepare` command; spend the one expensive call only after the cheap pass finds all other errors.

Do not mix loops or use one mode to probe the other; output layouts and evidence contracts differ.

## Source-model and brownfield judgment

TypeScript runs while constructing the graph. Use Flow Branch, Switch, Loop, and action nodes for runtime decisions/work; use native `if` or `for` only for deliberate author-time graph generation.

When editing an existing Flow, edit the supplied `.flow.ts`, preserve existing step names and unaffected wiring, and move an edge through an inserted step rather than leaving the old bypass in place. If given only raw `.flow` JSON, reconstruct source, compile once to compare the emitted baseline, then edit; no final artifact can establish those before/after judgments.

## Installing the package

<!--skill-flavor:install-package:start-->
Skip installation when `npm ls -g @uipath/maestro-builder-sdk` lists the SDK or a prepared workspace contains `node_modules/@uipath/maestro-builder-sdk` (workspace copy precedes global). Every `uip maestro flow` authoring verb—`check`, `compile`, `decompile`—runs from the installed package and refuses until installation; the package cannot bootstrap itself.

Install once per machine globally:

```bash
npm install -g @uipath/maestro-builder-sdk
```

The public npm package needs no token and follows the configured registry/mirror. Only after E401 or E404 **and** `npm config get @uipath:registry` names GitHub Packages, retry once with `--@uipath:registry=https://registry.npmjs.org` appended. On EACCES, do not use `sudo`; run `npm install --save-dev @uipath/maestro-builder-sdk` in the workspace, which `uip` also finds. Report all other failures (including timeout or mirror refusal) as network/registry issues; do not route around them. If `uip` reports the SDK below its minimum, run the command in its `Instructions`, which specifies `-g` or `--save-dev` for the copy found.
<!--skill-flavor:install-package:end-->

## Local authoring hard gates

<!--skill-flavor:local-gates:start-->
Use only with emit-only disabled. Use source `check` as the fast no-output inner loop; with a library and `.flow-sdk/bindings.json` beside the source it reports every connector-input and binding refusal that `compile` would raise. Compile to emit, then run product static `validate` on the artifact. There is no compiled-artifact `check`; `validate` is that rung. `compile` does not run `check` and writes any serializable flow, so never compile with a `check` error except one whose message says to ignore it in an applicable case (for example `INLINE_AGENT_PROMPT_JSON_TEXT` when JSON is mentioned only as data). In brownfield edits, add `--baseline <original.flow>` ([brownfield.md](brownfield.md#check-only-what-you-changed-check---baseline)).

Run this sequence in order; run `registry prepare` only when `check` names it, never before the source exists:

```bash
uip maestro flow check .flow-sdk/<Name>.flow.ts --source
# run each prepare the check names, with the exact command it prints:
uip maestro registry prepare <key> --action <action> [--object <name>] [--resolve <field>:<by>=<value>] [-f <parent>=<value>]
uip maestro flow check .flow-sdk/<Name>.flow.ts --source    # re-check until clean
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow
uip maestro flow validate <Name>.flow --output json
```

Review warnings deliberately; whether they block release comes from the task or release policy.

Layout is absent deliberately. `uip maestro flow format` is not an authoring gate: `validate` passes without it and nothing upstream reads position. For a greenfield file written from scratch by `compile`, run it before `solution upload`, `flow debug`, or a person opens the project in a designer. Do not run it on a merged brownfield file or source using `.layout()`: `format` re-lays every node and discards chosen positions. See [`operate.md`](operate.md#lay-out-the-emitted-flow-first).

These authoring verbs require a prerelease of `@uipath/cli` that exposes them.
<!--skill-flavor:local-gates:end-->

## Product-CLI scaffold

<!--skill-flavor:product-cli-scaffold:start-->
The scaffold (`uip solution init`, `flow init --sdk-source` for the seed, and `--automate` for a Maestro Automate project) is in [SKILL.md — Project layout](../SKILL.md#project-layout), kept there so the copies cannot drift.
<!--skill-flavor:product-cli-scaffold:end-->

## Eval/product-CLI packaging: emit-only

Emit-only rules (mode selection by `package.json`, and what `compile`/`check` do) plus the compile → validate → format → refresh → debug block are in [SKILL.md — Lifecycle](../SKILL.md#lifecycle). The following adds runtime-evidence detail.

## Product validation and conditional bindings

### Reading product validation

The JSON envelope has top-level `Result`; successful validation also has `Data.Status: "Valid"` and may have `Data.Warnings`. Treat warnings as failures except the reviewed shared-connection advisory and `err()` read diagnostics in [`error-handling.md`](error-handling.md#reading-the-failure). Preserve each exception's exact code/text and rationale; do not broaden the allowlist.

### Bounded completion

Match final evidence to the acceptance bar after the last edit:

- Validate-only: `Data.Status: "Valid"` plus the required structural self-check completes the task; stop and do not debug merely for confidence.
- For each distinct behavior claim, plan at most one bounded debug with inputs/attachments exercising it; one run may cover compatible claims, and equivalent inputs must not be repeated.
- If one unknown blocks final wiring, run one bounded experiment distinguishing the choices, apply its answer, and return to final emit/validate. Do not create a scratch-solution family.

If the bound cannot obtain the requested evidence, report the evidence boundary rather than repeating debug launches.

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

Compilation resolves the names and writes connector-authenticated node detail and required product bindings into `.flow`. Do not patch the emitted artifact; recompilation loses the edit. Omit both options only for manual/implicit authentication.

## Refresh, debug, and preserve evidence

<!--skill-flavor:debug-flags:start-->
`flow debug` takes the project directory, not the `.flow` file; run resource refresh first. From the solution directory, `<Name>` names that project. A `500` at `prepare-custom-debug` is transient; retry once. A `403` or `404` there comes from a folder flag: drop it, unless the account has no personal workspace ([operate.md](operate.md#debug--a-real-end-to-end-run)). Use only flags needed by the behavior claim:

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

Use `'single-quoted'` for a string literal, not `` `backticked` ``; backticks delimit a JSON literal, so `` `Completed` `` is a syntax error. Prefer the first form; quote the whole expression with DOUBLE quotes so inner single quotes survive:

```bash
--output-filter "elementExecutions[?status!='Completed']"     # raw string literal
--output-filter 'elementExecutions[?status!=`"Completed"`]'   # JSON literal
```

Projection selects from `Data`, not the envelope: `Result` and `Code` remain top-level, so `finalStatus` means `Data.finalStatus`. Filter with `--output-filter` rather than piping to `jq` or searching interleaved logs. If rejected, fix the expression rather than falling back to `--output json | jq`; rejection exits non-zero with a parse error.

### Ready-made projections — copy one, do not compose your own

These are verified against a real `flow debug` envelope. Choose the narrowest:

```bash
# Did it finish? The cheapest possible check.
--output-filter "{status:finalStatus,instance:instanceId}"

# Standard read-back: status, location, incomplete elements, declared outputs
# (one <Out>:variables.globals.<Out> pair per output), incidents.
--output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,\
failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},\
weatherVerdict:variables.globals.weatherVerdict,incidents:incidents}"

# Every global, including each step's raw output—diagnosis only.
--output-filter "variables.globals"

# Every element's status, when the executed path is needed.
--output-filter "elementExecutions[].{id:elementId,status:status}"
```

`variables.globals` is a FLAT map whose keys contain dots. A step output is `"<step>.output.<field>"`, beside the bare name of each declared global:

```jsonc
{ "product": 42, "start.output.a": 6, "multiply.output": 42, "multiply.error": null }
```

Read a bare global as `variables.globals.product`; quote a dotted key, reversing shell quoting because the expression contains double quotes:

```bash
--output-filter '{status:finalStatus,raw:variables.globals."multiply.output"}'
```

Project only globals needed by the claim; never project all for a verdict. Each step output is whole: HTTP includes body and headers, connector steps include the full record. One geocoding call can produce hundreds of lines; `tail`/`head` can drop `status` and `failed`, requiring a second `flow debug` (~30 s against the cloud). Name each declared output and add step output only when claimed.

A completed run has no `incidents` in this envelope, so `incidents:incidents` projects `null`. Its `Data` carries `finalStatus`, `entryPoint`, `instanceId`, `studioWebUrl`, `jobKey`, `runId`, `folderKey`, `solutionId`, `variables`, and `elementExecutions`, plus `variablesFetch` when the variables read retried; `variablesError` replaces `variables` when that read fails. A faulted run usually carries `Data.incidents` (absent when PIMS returns none or fetch fails); filters also project failure `Data`, so include `incidents:incidents`. If missing, fetch incidents with the separate `debug-instance incidents` call using the returned `instanceId`. With `variablesError`, outputs are unknown, not empty; run the re-read command its `Instructions` give.

For a direct-input claim, refresh and use one compact read-back (a real run: [ask first](operate.md#debug--a-real-end-to-end-run)):

```bash
( cd "<Solution>" && uip solution resources refresh --solution-folder . --output json )
( cd "<Solution>" && uip maestro flow debug <Name> --log-level error \
  --inputs @inputs.json \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},<Out>:variables.globals.<Out>,incidents:incidents}" \
  --output json )
```

The envelope still carries `Result`; the projection selects `Data`. Retain `Result`, projected status/instance/URL, failed element executions, declared outputs needed by the claim (`<Out>` is each `direction: out` global), and `incidents` on faults. `Completed` with expected globals and empty `failed` evidences the product-runtime path; process exit status alone does not. Omit the filter only to diagnose an unretained field.

Fetch incidents by `instance` only when a failed run has no `Data.incidents` (`null` in a projection) or the projection dropped it:

```bash
uip maestro flow debug-instance incidents <instanceId> \
  --output-filter "[*].{E:ElementId,C:ErrorCode,M:ErrorMessage,D:ErrorDetails}"
```

`ErrorDetails` commonly contains the service response or unresolved-resource value omitted by the summary.
<!--skill-flavor:debug-readback:end-->

## CLI output conventions

Use `--output json`, not `--format json`; use `--output-filter '<JMESPath>'` to select fields from `Data`. Successful commands may print progress/update text to stderr, so judge success from structured `Result`, status, outputs, and incidents—not stderr presence.

Product debug creates real side effects. Use sandbox resources and serialize runs sharing queues, issues, mailboxes, or other mutable tenant state.
