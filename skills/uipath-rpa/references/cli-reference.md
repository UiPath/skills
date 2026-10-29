# UiPath CLI (`uip`) Reference

`uip rpa` and sibling tools (`uip is`, `uip tm`, …) communicate with UiPath Studio over named pipes (IPC). Use this reference to discover live commands, arguments, and flags, and to handle authentication, Studio backends, run results, and recovery.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->

> Command and flag lists are not exhaustive or current. Discover the live surface with `--help`; this document covers behavior `--help` omits.

> Installation is automatic. Do NOT install `uip` manually or instruct the user to install it.

## Discover the live CLI with `--help`

Append `--help` at any level to drill from tools to groups, verbs, and parameters. Run `--help` rather than guessing unknown verbs, flags, or values.

```bash
uip --help
uip tools list
uip rpa --help
uip rpa packages --help
uip rpa validate --help
uip is --help
uip skills --help
```

The pattern works at every depth (`uip rpa uia <verb> --help`, `uip login --help`, etc.). Run `--help` standalone, never with other flags: `uip rpa <verb> --help --project-dir "<path>"` parses the value as a positional command and returns `unknown command '<value>'`. A verb may be hidden from help but callable by exact name; absence means it is not part of the standard loop, not that it does not exist.

## Output format

`--output` defaults to `json`; accepted values are `json`, `table`, `yaml`, and `plain`. Keep `json` for programmatic parsing; `table` can balloon to 100 KB+. `--output-filter "<JMESPath>"` filters the response envelope's `Data` field. Global `--log-level <debug|info|warn|error>` and `--log-file <path>` are available; raise the log level or add `--verbose` when diagnosing. Most envelopes are `{Result: "Success"|"Failure", Code, Data, Message?, Instructions?}`. Branch on `Result`, not stdout text: it says whether the command ran; what the command found is in `Data` (`validate`'s diagnostics: § validate).

## Authentication

Cloud features (feed templates/packages, Integration Service, Data Service entities, and publishing) require a logged-in session.

```bash
uip login
uip login status
uip login which
```

If a command returns `not authenticated`, `401`, or `403`, run `uip login` and retry. Discover non-interactive/CI credentials-folder, client-id/secret, and authority options with `uip login --help`.

## Project context: `--project-dir`

Most `uip rpa` verbs use `--project-dir`, defaulting to the current directory. When elsewhere, pass the absolute folder containing `project.json` in long form. An 8.3 path such as `C:\\Users\\ABCDEF~1\\…` can make `run` fail at `Building for execution` with `An item with the same key has already been added. Key: <workflow path>`. `init` instead uses `--name` and `--location`; `build` and `pack` take the project directory positionally, so confirm each verb with `--help`.

To create a project, see [environment-setup.md](environment-setup.md). Decide `--target-framework` and `--expression-language` before `init`; they are immutable afterward.

## Headless Studio (Helm) vs Studio Desktop

`uip rpa` uses one of two backends:

- **Headless Studio (Helm), default:** a NuGet package auto-launches on first use; Studio Desktop is unnecessary. A cold cache may be nearly silent for 30–90 s during `dotnet restore`; the default shell timeout covers this, so raise `timeoutSeconds` only behind a slow feed.
- **Studio Desktop:** a running Desktop instance with the project open handles that project's calls, including `run` and `debug start`. `uip rpa instances list --output json` shows project ownership. UI-side-effect verbs work only here: ensure Desktop is up with `uip rpa studio start --project-dir "<PROJECT_DIR>"`, then run them. Force Desktop with `UIPATH_RPA_TOOL_USE_STUDIO=1` (not recommended for the standard authoring loop).

The backends return different `run`/`debug start` payloads; see [Reading run / debug results](#reading-run--debug-results). `--studio-dir` applies only to Desktop; Helm ignores it. If Desktop detection fails, resolution falls back to `UIPATH_STUDIO_DIR`, the default install path, then a dev build output. `does not have interop support` or `Requires Studio 26.2+` means the detected Desktop is too old; tell the user to update it. This affects only Desktop-only verbs.

## Installed package activity documentation

Installed activity docs are under `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`; read them directly because they expose per-activity properties and coded API signatures unavailable through `--help`.

| Action | How |
|---|---|
| Read an activity doc | `Read` `…/{PackageId}/activities/{ActivityName}.md` |
| Read coded API doc | `Read` `…/{PackageId}/coded/coded-api.md` |
| Read package overview | `Read` `…/{PackageId}/overview.md` |
| List packages/activities | `Bash`: `ls …/.local/docs/packages/`, then `ls …/{PackageId}/activities/` |
| Search activity docs | Use Bash `ls` on `…/.local/docs/packages/<PackageId>/activities/`, then `Read` the matching path. Do NOT use `Glob` or `Grep`; both skip gitignored `.local/`, and a miss proves nothing. |

## Reading run / debug results

`uip rpa run` executes without debugging. The `debug` group handles breakpoints, stepping, and exceptions; see [debugging.md](debugging.md). Prefer `debug start` for UI automation so the application remains available for selector repair. Cancel an active run/session with `uip rpa execution cancel`. Pass workflow inputs as repeatable `--input-arguments key=value` pairs; see [Passing structured inputs](#passing-structured-inputs). Discover remaining flags (log level, skip-build, profiling) with `--help`.

Both return `{Result, Code, Data}`. Identify the backend from `Data`:

| Backend | `Data` keys | Workflow `Log Message` output |
|---|---|---|
| Headless Studio (Helm) | `output` (serialized output arguments, `"{}"` if none), `hasErrors`, `errorMessage`, `profiling`, `debugState`, `debugDetails` | stdout lines such as `[Information] …` and `[Error] …` above the JSON envelope; none in `Data` |
| Studio Desktop | `output` (completion status `"Session ended"`), `errors` array, `logEntries` array of `{source, level, message}` where `source` is `Compile` or `Debug`, and `debugState` (`"Completed"` on completion; absent if the file could not open) | `Data.logEntries`; nothing above the envelope |

Field meanings are in [debugging.md § Output Format](debugging.md#output-format).

- **Helm passes only when** `hasErrors` is `false`, `errorMessage` is `null`, and `debugState` is `null` or `"Completed"`. A fault, validation failure, or missing entry point returns outer `Result: "Failure"` with the same fields JSON-encoded in `Message` (`hasErrors: true`, `errorMessage` containing the failure). A faulted Helm `debug start` returns `Result: "Success"` with `hasErrors: false`, `debugState: "Suspended"`, the exception in `debugDetails` and command guidance in `errorMessage` — the session is still alive; cancel or continue it.
- **Desktop passes only when** `errors` is empty and `output` is `"Session ended"`. A missing entry point can return `Result: "Success"`, `errors: []`, `logEntries: []`, and `output: "Failed to open the file <absolute path>"`. Undeclared `--input-arguments` keys are silently accepted with `"Session ended"`.
- Never treat outer `Result: "Success"` alone as a pass or infer failure from `Warning`/`Error` log levels; `Log Message` can emit any level.

### Capturing the verdict

**Run `run` / `debug start` with no `--output-filter` and read the envelope as printed.** The two backends return different key sets, so a filter written for one names keys the other does not have; the CLI then rejects the whole call with `Filter '…' failed to evaluate: Invalid type … received type null` *after* the workflow has already run (`length(errors)` on Helm, any function on `hasErrors` on Desktop), and the retry re-drives the application and costs a turn. On Helm the filter cannot reach the log lines at all — they are outside `Data`.

```bash
uip rpa run --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --skip-build --output json
```

Helm:

```text
[Information] Starting execution...
[Information] <PROJECT_NAME> execution started
[Information] Sum: 10
[Information] <PROJECT_NAME> execution ended in: 00:00:00
{ "Result": "Success", "Code": "ToolResult", "Data": {
    "output": "{}", "hasErrors": false, "errorMessage": null, "profiling": null, "debugState": null, "debugDetails": null } }
```

Studio Desktop (same command, project open in Studio):

```json
{ "Result": "Success", "Code": "ToolResult", "Data": {
    "output": "Session ended", "errors": [],
    "logEntries": [ { "source": "Debug", "level": "Information", "message": "<PROJECT_NAME> execution started" },
                    { "source": "Debug", "level": "Information", "message": "Sum: 10" },
                    { "source": "Debug", "level": "Information", "message": "<PROJECT_NAME> execution ended in: 00:00:06" } ],
    "debugState": "Completed" } }
```

Read Helm `[Information]` lines above the envelope without stripping them (`grep -v '^\['` is wrong). Read Desktop workflow values from `logEntries`; `Trace` entries such as `Unregistered service requested …` and `Audit: …` may outnumber them. Helm `debug start` puts suspended-state exception details in `debugState`/`debugDetails`.

Never pipe the payload through `tail -N` or `head -N`: Helm places logs before the envelope, while Desktop places `output` and `errors` before a potentially long `logEntries`; recovering either requires a rerun and may change a non-rerun-safe workflow. For Helm `Result: "Failure"` without `Data`, read `Message`: it contains JSON-encoded `Data` fields (`hasErrors: true`) for a fault, validation failure, or missing entry point; a project that cannot open or a busy executor returns `{"success": false, "errorMessage": "…"}`.

When the envelope lacks enough detail, redirect all stdout with `> run.log` and read the file: Helm `[Error]` lines plus `errorMessage`; Desktop `errors` and `logEntries`. `jq` is absent on a standard Windows agent host; the envelope is the last JSON object in the file.

## Passing structured inputs

`--input-arguments` and `--input-variables` accept repeatable `key=value`, `key:=value` (raw JSON), or `key=@file` pairs; an inline JSON string; or a JSON file via `'@file'` or `--<flag>-file`. `--packages` is repeatable, one item per occurrence, with comma-joined fields.

```bash
uip rpa run --file-path Main.xaml --input-arguments name=John --input-arguments retries:=3
uip rpa run --file-path Main.xaml --input-arguments 'message=Hello, world!'
uip rpa debug test-activity --input-variables greeting=@expression.txt
uip rpa run --file-path Main.xaml --input-arguments '@args.json'
uip rpa run --file-path Main.xaml --input-arguments-file args.json
uip rpa packages install --packages 'id=UiPath.System.Activities,version=23.10.1' --packages id=UiPath.Excel.Activities
```

Rules: `count=42` sends string `"42"`; `count:=42` sends number `42`. `debug test-activity` and `debug start-from-here` require VB/C# expression strings, so always use `=`. Single-quote tokens containing spaces, commas, or leading `@`; bare identifiers/numbers need no quotes. Windows PowerShell 5.1 strips inline double quotes: write such values to a UTF-8 file with `Set-Content -Encoding UTF8`, then use `key=@file`, `'@file'`, or `--<flag>-file`. Inline JSON remains accepted for backward compatibility but is unreliable on PowerShell 5.1; prefer pairs/files. `key=` passes an empty string and overrides a coded workflow's declared default; omit the flag to use the default.

## validate

`uip rpa validate` returns diagnostics for a file or project and revalidates by default. `--skip-validation` reads possibly stale cached results; `--min-severity` filters. Confirm flags with `uip rpa validate --help`. `--file-path` accepts a project-relative or absolute path with forward, back, or mixed separators; prefer the shorter relative form.

`Result: Success` and exit code 0 mean validate ran, with or without findings. The diagnostics are the text of `Data.message`: `No diagnostics found.`, or `Found N error(s)[, M warning(s)]:` followed by one `[error]` or `[warning]` line per finding (file, message, activity).

An activity that can run without a target reports no unset target: Type Into and Keyboard Shortcuts act on the focused element by design, so validate's "Target or Input UI Element must be set" errors are not a count of a file's target slots.

Validate reads the entity types the project last generated. After a Data Fabric entity install changes the project's entities, run `build`: a workflow whose entity type the install removed still validates with no diagnostics, and build fails with `Cannot create unknown type`.

## build

`uip rpa build` compiles every workflow in the project, not just files passed to `validate` (§ What each phase covers); it is required before returning a project (see [§ Project Build Verification](#project-build-verification-required-before-returning-a-project)). It takes the project directory positionally, runs independently of Studio IPC, and exposes log level, `skip-analyze`, governance, and NuGet-source flags through `uip rpa build --help`.

`run` and `debug start` compile internally but do not apply analyzer rules. A successful smoke test proves compilation, not `build`. A successful `build` writes `entry-points.json` (each entry point's argument schema) and `bindings_v2.json` (resources such as the queue a Get Queue Item names) under `.local/content/`, which `pack` ships, and deletes a root `entry-points.json` (templates ship one). Leave the root file deleted: restoring it changes nothing, and the next build deletes it again.

## analyzer-rules list

`uip rpa analyzer-rules list` reports enabled rules, not violations. Do NOT run it as an authoring prerequisite; run it only when the user asks about analyzer/best-practice rules or recurring `build` violations suggest authoring against the full set. Results contain `severity` (`error`/`warning`/`info`), rule ID, scope, title, and optionally `recommendation` and `docs`. `ST-*` means built-in Studio; `MA-*` means package-shipped.

`Coded Workflow` rules run as Roslyn analyzers over `.cs` files during `analyze`, `build`, and `pack`, with the same enforcement as XAML rules. The four built-in rules are Error severity; see [coded/operations-guide.md § Coded Workflow Analyzer Rules](coded/operations-guide.md#coded-workflow-analyzer-rules). The unscoped call can enumerate every package rule for a minute or more; narrow with `--scope` values `Activity`, `Workflow`, `Project`, or `Coded Workflow`.

## packages install

`uip rpa packages install` is the canonical dependency operation; do not hand-edit `project.json`, and there is no `add-dependency` verb. Repeat `--packages` with comma-joined `key=value` fields (`--packages 'id=<PackageId>,version=<Version>'` or `--packages id=<PackageId>`); discover remaining flags with `uip rpa packages install --help`.

Omit `version` to resolve the latest compatible version; pin only for known compatibility constraints. Discover versions with `uip rpa packages versions --package-id <Id> --include-prerelease`; default to `--include-prerelease`, since preview activity packages often contain the freshest surface and `.local/docs`. Inform the user and offer upgrades; never force them. For a missing package, verify the exact ID with `activities find` or `.local/docs`. For feed/network errors, check Studio NuGet feed configuration.

Remove unused dependencies with `uip rpa cleanup "<PROJECT_DIR>" --skip-imports --output json`; use `--dry-run` first and inspect `Data.UnusedItems`. Without `--skip-imports`, cleanup also removes unused namespace imports and resaves every workflow. No verb removes one named dependency.

## object-repository

Both project-repository verbs are top-level and hyphenated, require an open project, and support standard `--project-dir`; there is no `uip rpa object-repository` group — it returns `Unknown command: object-repository`, Studio running or not. They differ from the UIA OR CLI, which writes entries and has no `get`.

`uip rpa get-object-repository` returns only the project's own JSON tree of applications, screens, and elements, each with `name`, `description`, `type`, and `reference`; referenced-library entries are excluded. `name` is an Object Repository name, not a C# member (`Result Display` becomes `Result_Display` in `Descriptors.*`); follow the coded authoring guide's § Descriptor Naming routed from `ui-automation-guide.md` § Documentation.

```bash
uip rpa get-object-repository --project-dir "<PROJECT_DIR>" --output json
```

`uip rpa get-library-object-repository` reads one or more library `.nupkg` files and groups returned applications, screens, and elements by library; packages without an Object Repository are omitted. `--library-paths` is required, accepts absolute paths comma-separated in one flag, is not repeatable, and should not contain commas.

```bash
uip rpa get-library-object-repository \
  --project-dir "<PROJECT_DIR>" \
  --library-paths "C:\libs\Acme.UiLib.1.2.0.nupkg,C:\libs\Other.UiLib.2.0.0.nupkg" \
  --output json
```

Read the project repository before authoring UI Automation to reuse existing targets; read library repositories for targets exposed by referenced libraries. Confirm flags with `uip rpa get-object-repository --help` and `uip rpa get-library-object-repository --help`.

## Commands -- Data Fabric Entities

Data Fabric entities in the Orchestrator tenant's Data Service must be installed into the RPA project before typed arguments, `UiPath.DataService.Activities`, test-data bindings, or generated entity types can be used. Installation writes `.entities/` and compiles a strongly typed assembly. `.entities/EntitiesStore.json` holds the definitions of every entity the tenant's Data Service exposes, the installed ones marked, and the tenant's URL, and `pack` ships it in the package: review it before a package leaves the tenant's audience. Under `uip rpa data-fabric-entities`, discover exact flags with `--help`:

1. **List:** show entities installed in the project and available in the tenant, each with `installed`; run before installing to select names or verify bindings.
2. **Install:** apply an add/remove delta. Dependencies expand automatically; server-deleted entities are dropped. Final selection is `(installed ∪ add) − remove`; empty selection uninstalls the manifest.

Install entities before invoking workflows/test cases using generated types and before test-data commands binding to an entity.

## Integration Service (`uip is`)

Discover `uip is` with `uip is --help`, then drill down (`uip is connections --help`, `uip is resources describe --help`, …). All verbs support `--output json`. The surface covers connectors and their activities/resources; list/create/ping/edit connections (OAuth opens a browser; `--no-browser` prints the URL); and CRUD resource operations. For RPA connector patterns see [is-connector-xaml-guide.md](is-connector-xaml-guide.md).

## Test Manager

Use **`uip tm`** for runtime Test Manager operations (manual cases, runs, results); discover with `uip tm --help` and do not invoke these runtime verbs from `uip rpa`. Use **`uip rpa tm`** for project configuration in `.tmh/config.json`; it is pure file I/O and needs no Studio or Helm process.

### `uip rpa tm` verbs

- `uip rpa tm connect --url <url>` sets `testManagerBasePath`; switching server host/org/tenant clears `defaultProject`.
- `uip rpa tm set-default-project --id <guid> [--name <name>] [--key <key>]` sets `defaultProject`; `connect` is required first.
- `uip rpa tm clear-default-project` unlinks the default while retaining the server URL.
- `uip rpa tm status` shows the server URL and linked project.

All take standard `--project-dir` and `--output json`:

```bash
uip rpa tm connect --url "https://cloud.uipath.com/<org>/<tenant>/testmanager_" --project-dir "<PROJECT_DIR>" --output json
uip rpa tm set-default-project --id <project-guid> --name "<project-name>" --key "<KEY>" --project-dir "<PROJECT_DIR>" --output json
uip rpa tm status --project-dir "<PROJECT_DIR>" --output json
```

`set-default-project` does not validate the ID server-side; obtain a real Test Manager project ID from Test Manager. Listing projects is unavailable here. Confirm flags with `uip rpa tm --help`.

### Acting on `reloadHint` in the output

A `connect`, `set-default-project`, or `clear-default-project` response may contain `reloadHint` only when the project is open in Studio older than 26.0.197. Tell the user to close and reopen the project; the CLI cannot do it. No `reloadHint` means no action is needed.

## Fix One Thing at a Time

When an error occurs, identify the root cause, fix only that one thing, rerun, and verify. Never bundle speculative improvements with the fix or change two things before verification.

## Validation Iteration Loop

**Phase 1 — per-file validate after every edit.** For every file created or edited:

```text
REPEAT:
  1. uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
  2. IF validate has errors -> fix one root cause, GOTO 1
  3. EXIT when validate is clean
```

**Phase 2 — one project build per edit session.**

```text
REPEAT:
  1. uip rpa build "<PROJECT_DIR>" --log-level Warn --detailed-log-path "<LOG_FILE>" --output json
  2. IF build has errors:
     a. <OFFENDER> and its activity are each error's FilePath and ActivityId.IdRef in <LOG_FILE>
     b. uip rpa validate --file-path "<OFFENDER>" --project-dir "<PROJECT_DIR>" --output json   # compile errors only; an analyzer error is re-checked by the next build
     c. fix one root cause, GOTO 1
  3. EXIT to Smoke Test
```

Per-file `validate` covers structural XAML, references, schema, members, enums, and expression compilation for one file. `build` covers every workflow, analyzer rules, and packaging. Neither replaces the other, and neither detects an attribute-form expression that silently becomes a literal; see [§ What each phase covers](#what-each-phase-covers).

Target changed files with `validate --file-path`; `build` is project-scoped; its stdout names an analyzer error by its activity only, and the detailed log (`--detailed-log-path`) gives every error's `FilePath` and `ActivityId` — re-run `validate --file-path` on that file for a compile error. Each loop has a **5-attempt cap**: five Phase 1 attempts per file and a separate five Phase 2 attempts. After exhaustion, present remaining errors. Counters reset for a new file, user prompt, or resumed loop.

### Rules

1. DO NOT stop until all errors are resolved or cannot be resolved automatically.
2. DO NOT obsess over one error; if it cannot be resolved, continue and defer it with an informative step-by-step message.
3. DO NOT skip validation.
4. DO NOT assume edits worked without checking.
5. DO NOT bundle fixes; fix one root cause, rerun, and verify.
6. Warnings are non-blocking. Once `validate`/`build` (and, where the task requires, `pack`/`run`) are clean of errors, deliver — do not investigate warnings unless the user asked or one blocks an acceptance criterion.

See [§ validate](#validate) and [§ Reading run / debug results](#reading-run--debug-results).

## Project Build Verification (Required Before Returning a Project)

Every returned project must compile. A clean Phase 2 satisfies the gate; standalone verification is:

```bash
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

If it fails, apply the Phase 2 loop with one fix per iteration and a five-attempt cap. A successful `run` does not substitute for `build` because `run` applies no analyzer rule.

### What each phase covers

Per-file `validate` loads the target through the workflow designer and compiles expressions. It reports these on the file it was pointed at:

| Error class | Example | Reported as |
|-------------|---------|-------------|
| Unknown member name | `<uix:NGetText Value="[x]" />` (correct: `TextString`) | `Could not load <file>: 'Cannot set unknown member '<Class>.<Prop>''` |
| Invalid enum value | `ClickType="BogusValue"` | `Could not load <file>: 'Failed to create a '<Prop>' from the text '<value>''` |
| Broken expression | `undefinedSymbol + 1` inside a `CSharpValue` | `CS0103: The name '<symbol>' does not exist in the current context` |

`build` compiles every workflow, including untouched/unvalidated files, and applies analyzer rules and packaging. A project can therefore have clean edited files but fail on another file.

Neither per-file nor project `validate` checks an Invoke Workflow File's arguments against the invoked workflow; `build` does:

| Defect | `validate` | `build` |
|---|---|---|
| Extra argument (a key the invoked workflow does not declare) | not reported | `SY-USG-016` Error: `Extra argument '<name>' not found in invoked workflow.` |
| Argument type mismatch | not reported | `SY-USG-016` Error: `Type mismatch for argument '<name>': imported type '<type>', target type '<type>'.` |
| Missing argument (an argument of the invoked workflow left unbound) | not reported | `SY-USG-015` Warning: `Missing argument '<name>' for the invoked workflow.` — the build passes |

When a step starts invoking another workflow (a helper split into its parts, a callee whose arguments changed), build the project before calling the step done. Check a missing In argument by hand: it builds, and the invoked workflow runs with the argument's default.

Neither phase catches an attribute-form expression on `InArgument<Object>`: `Message="calcResult"` becomes a literal, so validation/build/run can succeed while logging `calcResult`. Inspect smoke-test output; see [§ Smoke Test](#smoke-test) and [xaml/csharp-activity-binding-guide.md § C# Expression Pitfalls](xaml/csharp-activity-binding-guide.md#c-expression-pitfalls).

### Analyzer errors

Error-severity analyzer rules fail `analyze`, `build`, and `pack`; per-file `validate` does not report them. Fix the workflow first. If a rule cannot be satisfied, decide with the user whether to lower it or pack with analysis skipped, and record the decision.

| Rule | Fires on | Fix |
|---|---|---|
| `ST-SEC-007` | A `SecureString` workflow argument | Carry the credential asset name; read the secret inside the consuming scope. |
| `ST-SEC-008` | A `SecureString` variable used outside its declaring scope | Declare it on the Sequence directly containing both its creator and consumers. |
| `ST-SEC-009` | Converting a `SecureString` to text (`NetworkCredential(…).Password`) for a plain-string property | Read identifiers such as OAuth client or tenant IDs from a Text asset; pass request secrets as `SecureString` to the code step and convert inside it. |
| `ST-DBP-002` | More than 20 workflow arguments | Put them in one options object/coded class. |
| `UI-REL-001` | Literal `idx` above 2 in a strict selector | Replace it with a stable attribute by reconfiguring the target (SKILL.md Rule 7). |

### Expected non-defect warnings

`build` prints `[WARN]` lines for enabled analyzer rules. These are **not** build failures and do not gate delivery (§ Validation Iteration Loop, Rule 6). Recurring ones that are correct-by-design and must not be "fixed": `<activity> does not have the verification feature enabled` (no matching enabled rule; `VerifyOptions` is deliberately off by default; add only when requested, per the UIA package guide's § Execution Verification Policy); `Your organization requires your project to have an Automation Hub URL defined` (`ST-USG-034`, organization governance resolved by the project owner in Project Settings); `<name> display name is defined many times. Current allowed threshold is 1` (`ST-NMG-004`, cosmetic; fix while authoring, since repeated identical steps need distinct names — unless the names are dictated, the user's or a migrated source's kept by request, where it is expected); and `Potential infinite loop detected in Flowchart <name> starting with activity <node>` (`ST-REL-006`), which every Flowchart with a back link raises, a bounded retry included: check that each cycle has a counter or a state change that ends it, then leave it. For an unfamiliar warning rule ID, run `analyzer-rules list --scope <scope>` only when it blocks an acceptance criterion.

## Smoke Test

Clean `validate` and `build` are not runtime proof: attribute literals, activity CacheMetadata failures, and logic defects may appear only at runtime. After zero validation errors and a clean project build, run the workflow and inspect its output. Use `--skip-build` only when no edits occurred after the successful build; it executes the existing artifact and silently ignores later edits.

```bash
uip rpa run --file-path "<FILE>" --skip-build --output json
uip rpa run --file-path "<FILE>" --skip-build --input-arguments key=value --output json
uip rpa run --file-path "<FILE>" --skip-build --log-level Verbose --output json
```

Use bare `run` after edits. For coded workflows, do not pair `build` with a default `run`/`debug start`: `build` deletes `.local/.codedworkflows/WorkflowRunnerService.cs`, causing default execution to fail `CS0246 'WorkflowRunnerService' does not exist in the namespace`. Use `build` → `run`/`debug start --skip-build`, or a bare `run`/`debug start`.

**When to run:**
1. Workflow has no compilation errors but you want to verify runtime behavior
2. Workflow involves file I/O, API calls, or data transformations that could fail at runtime
3. User specifically asks to test the workflow

**When NOT to run:**
1. Workflow has side effects (sends emails, modifies databases, calls external APIs) -- warn the user first
2. Workflow requires interactive input (UI automation, attended triggers)
3. Compilation errors still exist (fix those first)

For runtime errors, analyze output, apply the one-fix rule, and retry. Stop after **2 failed runtime retry attempts** and present:

```text
Workflow execution failed after 2 retry attempts.

**Error Details:** <specific error message and location>
**Suggested Fix:** <analysis of what went wrong>
**Next Steps:** Would you like me to:
A) <recommended fix approach>
B) <alternative approach>
C) <user-driven approach>
```

## RPA-Specific Fix Procedures

### Resolving Dynamic Activity Custom Types

Dynamic activities retrieved with `uip rpa activities get-default-xaml` and `--activity-type-id` may use JIT-compiled custom property types. After adding one, read the schema to discover CLR property types for `Assign` targets or variables:

```text
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### Focus Activity for Debugging

When `validate` identifies an activity by IdRef or DisplayName, use `focus-activity` to highlight it in Studio Desktop. `focus-activity` is Desktop-only. Before invoking it, ensure Studio Desktop is up via `uip rpa studio start --project-dir "<PROJECT_DIR>"` (see [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop)). Skip this step entirely on headless-only setups — `validate` already includes the IdRef and file:line in its output, which is enough to locate the activity.

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1"
# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity
```

Use it to show the user's problematic context, show a modified activity, or disambiguate an error.

## Pack & Publish to Orchestrator

This section covers standalone projects only. Solution `.uipx` upload/publish/deploy belongs to the `uipath-solution` skill.

| Goal | Path | Reference |
|---|---|---|
| Orchestrator process, Test Manager automation, or library sharing | Pack → Publish | This section § Pack → Publish |
| Studio Web editing/visualization | Solution upload | `uipath-solution` skill |
| Packed solution deployment lifecycle | Solution publish | `uipath-solution` skill |

### Pack → Publish (Orchestrator package flow)

Pack then publish:

```bash
uip rpa pack "<PROJECT_DIR>" "<OUTPUT_DIR>" --output json
uip rpa publish "<NUPKG_PATH>" --output json
```

`<PROJECT_DIR>` is positional 1 and contains `project.json`; `<OUTPUT_DIR>` is positional 2, must exist, and must be outside the project tree. `pack` refuses an in-tree output. Common optional flags (run `uip rpa pack --help` for the full set): `--package-version <SEMVER>` pins the version (otherwise project version); `--skip-analyze` skips the workflow-analyzer pass; use it only for known-clean builds or for a rule the user chose to skip ([§ Analyzer errors](#analyzer-errors)); `--governance-file-path <PATH>` applies governance. Capture JSON `PackagePath` (not merely `OutputPath`) for publishing. `pack` accepts neither `--project-path` nor `--project-dir`.

`publish` takes a package, never a project folder. Without a destination flag it uses the package type: process/test to the tenant Processes feed, library to tenant Libraries. Success returns `Data.Destination` (`TenantFeed`, `PersonalWorkspace`, `FolderFeed`, `SharedLibraries`), `Data.Feed`, and `Data.FeedId`. Pass at most one destination:

- `--personal-workspace`: personal workspace feed; processes only and also creates the process.
- `--folder-path <PATH>` / `--folder-key <UUID>`: a folder feed; without one, `Folder '<PATH>' has no associated package feed.`
- `--shared-libraries`: host shared libraries; without one, `No accessible shared (host) libraries feed was found.`
- `--feed-id <UUID>`: the specified feed.

Invalid package/destination combinations are refused before upload with `The selected destination does not accept <Type> packages.` and `Instructions` lists the destinations that do — re-run with one of them. A library or test package sent to `--personal-workspace` is refused this way. The Orchestrator package ID is project `name`, shown as `Id` by `uip or packages list --output json`; `uip tm testcases link-automation` uses it as `--package-name`, while `uip or processes create` uses it as `--package-key` with `--package-version`.

A test package includes only test cases whose `project.json` `fileInfoCollection` entry has `"editingStatus": "Publishable"`. With none, upload fails `A testing project should contain at least one entry point.` (`errorCode` 2006). Marking cases Publishable is the user's decision; see [testing-guide.md § project.json Registration](testing-guide.md#projectjson-registration). There is no `uip or packages publish`; use `uip rpa publish`.

### Discovery cheatsheet

```bash
uip or folders list --output json
uip or packages list --output json
```

The folder `Key` is the UUID and `FullyQualifiedName` is the human path. Either is accepted by `--folder-path`/`--folder-key`; most other calls require the UUID. For Pack → Publish → Link → Execute to Test Manager, delegate to the `uipath-test` skill.

### Common pitfalls

`uip solution publish` expects a packed `.zip`, so run `uip solution pack` first, then `uip solution publish "<ZIP_PATH>"`; standalone projects use `uip rpa publish`. `solution upload` targets Studio Web, while `solution publish` targets the packed solution feed and later `solution deploy`; they are not interchangeable. Re-publishing an existing `<id>:<version>` returns `409 Conflict - {"message":"Package already exists.","errorCode":1004}`; bump `--package-version` or `project.json` `projectVersion`. If `pack` succeeds but analyzer output contains errors, warnings may be the cause; run `uip rpa analyze "<PROJECT_DIR>"` (project directory positional) when a clean signal is needed.

## CLI Error Recovery

Diagnose the category, apply recovery, and retry once; do not loop the same failing command.

| Error | Cause | Recovery |
|---|---|---|
| `connection refused`, `EPIPE`, `pipe not found` | IPC unavailable; Helm restore/process failure or Desktop stopped | Rerun; Helm relaunches. If persistent, raise `--timeout` and inspect Helm restore/NuGet errors. Run `uip rpa studio start` only for Desktop-only verbs or `UIPATH_RPA_TOOL_USE_STUDIO=1`. |
| `timeout`, `ETIMEDOUT` | Cold 30–90 s Helm restore or long operation | Raise shell `timeoutSeconds` toward its documented maximum and `uip rpa --timeout <timeoutSeconds − 30> <command>`; shell timeout must exceed CLI timeout by ≥ 30 s, or the shell kills the CLI before it can cancel cleanly. For `validate`, try `--skip-validation`. |
| `not authenticated`, `401`, `403` | Cloud authentication required | Run `uip login`, then retry. |
| `package not found`, `version not available` | Wrong ID/version | Verify with `uip rpa activities find`; omit `version` to auto-resolve latest. |
| `project not found`, `no project open` | Wrong path or unopened project | Verify `--project-dir` contains `project.json`; if it persists, `uip rpa project open --project-dir "<PROJECT_DIR>"`. For Desktop-only verbs inspect hidden `uip rpa instances list --output json` and run `uip rpa studio start` if needed. |
| `not in the project folder` in `validate` | Absolute path/separator mismatch | Use a project-relative `--file-path` (see [validate](#validate)). |
| `Studio is busy`, `operation in progress` | Prior request still processing | Wait a few seconds, then retry. |
| Unrecognized error | Unknown | Rerun with `--verbose`, then inform the user. |

## RPA discovery tools (non-CLI)

| Action | How |
|---|---|
| Explore project files | `Glob` `**/*.xaml` |
| Search XAML | `Grep` regex across `.xaml` |
| Explore Object Repository | `uip rpa get-object-repository` or `uip rpa get-library-object-repository`; alternatively `Glob` `**/*` under `{PROJECT_DIR}/.objects/` and `Read` metadata |
| Get JIT types | `Read` `{PROJECT_DIR}/.project/JitCustomTypesSchema.json` |
| Activity docs | [Installed package activity documentation](#installed-package-activity-documentation) |
| Inspect NuGet API | `uip rpa packages inspect`; see [coded/codedworkflow-reference.md § Inspect NuGet Package Tool](coded/codedworkflow-reference.md) |

## UI Automation (`uip rpa uia ...`)

`uip rpa uia --help` deliberately exposes no standard subcommands; the `UiPath.UIAutomation.Activities` package owns and versions this surface. Start from `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` (Rule 7), whose CLI-discovery section routes to task guides and the command inventory. Discover per-command flags with `<discovered command> --help`.
