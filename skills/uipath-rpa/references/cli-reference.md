# UiPath CLI (`uip rpa`) Reference

CLI reference for `uip rpa` -- communicates with UiPath Studio over named pipes (IPC).

> **Installation is automatic.** Do NOT attempt to install `uip` manually or instruct the user to install it.

## Studio Desktop vs headless Studio (Helm)

`uip rpa` connects to one of two flavors of Studio behind the same IPC contract:

- **Headless Studio (Helm) — default.** Ships as a NuGet package (`UiPath.Studio.Helm.{Platform}`) and auto-launches on first use. **No Studio Desktop install needed.** First call on a cold NuGet cache may sit near-silent for 30–90 s while `dotnet restore` runs; raise `--timeout` to ≥ 180 for that call.
- **Studio Desktop.** The interactive UI. Used automatically only by commands with UI side effects.

### Which commands need Studio Desktop

Only these two — they do not work headless:

| Command | Why |
|---------|-----|
| `uip rpa files diff` | Opens an interactive diff window in Studio's UI |
| `uip rpa focus-activity` | Highlights an activity in Studio's active workflow designer (hidden from `--help` — agent → user UI cue) |

For these, run `uip rpa studio start --project-dir "<PROJECT_DIR>"` first if Studio Desktop is not already up.

Everything else — `init`, `run`, `debug start`, `execution cancel`, `validate`, `build`, `analyzer-rules list`, `activities find`, `activities get-default-xaml`, `packages versions`, `packages inspect`, `packages install`, `data-fabric-entities list`, `data-fabric-entities install`, `templates search`, `workflow-examples list`, `workflow-examples get`, `indicate-application`, `indicate-element`, all `uia` subcommands, all `uip is` subcommands — runs headless with no Studio Desktop required.

To force Studio Desktop for any command, set `UIPATH_RPA_TOOL_USE_STUDIO=1`. Not recommended for the standard authoring loop.

> **This guide may not list every available command.** The CLI is self-documenting -- append `--help` at any level to progressively discover commands, subcommands, and parameters:

```bash
uip --help                              # top-level command groups
uip rpa --help                          # all rpa subcommands (canonical, grouped)
uip rpa packages --help                 # verbs inside a group
uip rpa validate --help                 # parameters for a specific command
```

> **Run `--help` standalone — never combine it with other flags.** `uip rpa <subcommand> --help --project-dir "<path>"` parses `--project-dir` as a positional command and exits with `unknown command '<path>'`. Drop every other flag when probing help.

---

## Global Options

Every `uip rpa` invocation accepts these flags:

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir <path>` | Project directory to match against running Studio instances | Current working directory |
| `--studio-dir <path>` | Path to Studio Desktop installation (only used when Studio Desktop is in use) | Auto-detected (see below) |
| `--timeout <seconds>` | Timeout in seconds for Studio resolution (raise to ≥ 180 on a cold Helm NuGet cache) | `300` |
| `--verbose` | Enable verbose/debug logging | Off |
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` | `table` |

> **Always use `--output json`** when calling `uip rpa` commands programmatically. The `table` format pads columns and can produce extremely large output (100KB+). JSON is compact and machine-readable.

### Shell quoting on Windows for JSON-bearing flags

Several `uip rpa` flags accept a JSON value — most commonly `packages install --packages` (JSON array) and `run` / `debug start --input-arguments` (JSON object). Pass these from `bash` on Windows when possible.

PowerShell's argument parser mangles JSON containing `:`, `/`, `=`, or `?` depending on how the surrounding string is quoted. The behavior is also inconsistent across flags — escaping that satisfies one flag has been observed to fail on another in the same session. `bash` (Git Bash, WSL, MSYS) passes single-quoted JSON straight through.

```bash
# bash — works for any JSON-bearing flag:
uip rpa packages install --packages '[{"id":"<PackageId>","version":"<version>"}]'
uip rpa run --input-arguments '{"<argName>":"<value>"}'
```

If you must use PowerShell, single-quote the whole value and escape inner quotes with backslash. This works for `--packages`; for `--input-arguments` it has been observed not to work and `bash` was required:

```powershell
# PowerShell — known-working for --packages:
uip rpa packages install --packages '[{\"id\":\"<PackageId>\",\"version\":\"<version>\"}]'
```

### STUDIO_DIR Resolution

`--studio-dir` is **only consulted when Studio Desktop is in use** (i.e. you ran `studio start`, called `files diff`/`focus-activity`, or set `UIPATH_RPA_TOOL_USE_STUDIO=1`). Headless Studio (Helm) ignores it. When Studio Desktop is needed and auto-detection fails, the resolution waterfall is:

1. Environment variable `UIPATH_STUDIO_DIR` if set.
2. Default install: `C:\Program Files\UiPath\Studio` (or `x86` variant) if `UiPathStudio.exe` exists there.
3. Dev build: Studio source tree build output (e.g. `<repo-root>\Output\bin\Debug`).

> **Error `"Studio X.X.X does not have interop support"` or `"Requires Studio 26.2+"`** means the detected Studio Desktop is too old. This affects only the two Studio-only tools (`diff`, `focus-activity`) and any explicitly forced Studio runs. Inform the user to update Studio Desktop.

### PROJECT_DIR Resolution

`--project-dir` defaults to the current working directory. When the project is elsewhere, pass the absolute path to the folder containing `project.json`.

---

## Installed Package Activity Documentation

Located at `{projectRoot}/.local/docs/packages/{PackageId}/`.

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Read activity doc directly** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md` | Package ID + activity simple class name. **Preferred when you know both.** |
| **Read coded API doc** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/coded/coded-api.md` | Package ID. **Use for coded workflows** — contains service API signatures and usage. |
| **Read package overview** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/overview.md` | Package ID (e.g., `UiPath.WebAPI.Activities`) |
| **List documented packages** | `Bash`: `ls {projectRoot}/.local/docs/packages/` | Project root directory |
| **List documented activities** | `Bash`: `ls {projectRoot}/.local/docs/packages/{PackageId}/activities/` | Package ID |
| **Search activity docs by keyword** | `Glob` with `**/*.md` in `{projectRoot}/.local/docs/packages/` to list files, then `Read` matches. **Do not use `Grep`** -- `.local/` is gitignored and `Grep` skips it. | Glob pattern + Read |

---

## Commands -- Studio Desktop Management (edge cases only)

> Skip this section unless you need to invoke `diff` or `focus-activity`. Every other command auto-launches headless Studio (Helm) when needed.

### instances list

List running Studio Desktop instances and their IPC status. Hidden diagnostic command — does **not** report the auto-launched headless Studio (Helm) instances.

```bash
uip rpa instances list --output json
```

No command-specific options. An empty `Data` array does NOT mean `uip rpa` won't work — headless Studio starts on demand.

---

### studio start

Ensure a **Studio Desktop** instance is running. Only required before invoking `files diff` or `focus-activity`, or when forcing Studio Desktop with `UIPATH_RPA_TOOL_USE_STUDIO=1`. Resolution waterfall:
1. Match by `--project-dir` -- reuse if available, wait if busy
2. Use an idle instance (no project loaded)
3. Start a new instance via `--studio-dir` -- poll until available

```bash
uip rpa studio start --project-dir "<PROJECT_DIR>" --output json
```

---

## Commands -- Project Lifecycle

### init

Create a new UiPath project from a template.

```bash
uip rpa init --name "<NAME>" --location "<PARENT_DIR>" --target-framework <Windows|Portable> --expression-language <VisualBasic|CSharp> --output json
```

> **Always pass `--target-framework` and `--expression-language`.** Both are fixed at creation and immutable afterward; omitting `--target-framework` silently produces a **Windows** project. The example shows the two new-project options (`Windows`, `Portable`). Windows - Legacy is a last resort (explicit ask or hard .NET 4.6.1 need) and is created/authored in **Legacy mode**, not via this command. Decide each per SKILL.md Common Rule 2a before running `init`.

> **Flag names are non-standard.** Most `uip rpa` commands take `--project-dir` to identify the project. `init` instead uses `--name` (project name) + `--location` (parent directory). Do NOT use `--project-name` or `--project-dir` here — both fail with `error: required option '--name <string>' not specified`.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--name` | Yes | -- | Name of the project |
| `--location` | Yes | -- | Parent directory where the project folder will be created |
| `--template-id` | No | `BlankTemplate` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` |
| `--template-package-id` | No | -- | NuGet template package ID from `templates search`. Overrides `--template-id` when set |
| `--template-package-version` | No | (latest) | Version of the template package |
| `--allow-prerelease-packages` | No | false | Allow prerelease activity package versions |
| `--description` | No | -- | Project description |
| `--expression-language` | No (decide explicitly — Rule 2a) | none | `VisualBasic` or `CSharp`. Immutable after creation |
| `--target-framework` | No (decide explicitly — Rule 2a) | none → **Windows** | `Windows` or `Portable` (Cross-platform) for new projects. The flag accepts `Legacy`, but Windows - Legacy projects are created/authored in **Legacy mode**, not via this command (last resort — explicit ask or hard .NET 4.6.1 need). Immutable after creation; omitting it yields a Windows project |

For template selection logic (when to use `--template-package-id` vs `--template-id`), see [environment-setup.md § Template selection](environment-setup.md#template-selection).

---

### templates search

Search NuGet feeds for available project templates. Use before `init` when the user names a template or asks for a domain-specific starter.

```bash
uip rpa templates search --query "<TERM>" --output json
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--query` | No | -- | Filter by name/description. Omit to list all |
| `--limit` | No | 20 | Maximum results |
| `--include-prerelease` | No | false | Include prerelease template versions |

Returns `Data[*]` with `packageId`, `version`, `title`, `description`, `authors`, `source` (`"Official"` / `"Marketplace"` / feed URL), `tags`. Pass `packageId` and `version` to `init --template-package-id` / `--template-package-version`.

---

### project open / project close (hidden)

Open or close a project explicitly in Studio. The `project` group and both verbs are hidden from `--help` because the standard authoring loop (`validate`, `run`, etc.) auto-resolves a Studio instance and opens the project on its own. Use only when you need to force open/close (e.g. immediately after `init` before any other command, or when releasing a project lock).

```bash
uip rpa project open  --project-dir "<PROJECT_DIR>" --output json
uip rpa project close --output json
```

---

## Commands -- Validation and Execution

### run

Run a workflow file via Studio (no debugging — closes app on completion or error).

```bash
uip rpa run --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | Yes | Path to the workflow file to run |
| `--input-arguments` | No | JSON string of input arguments |
| `--log-level` | No | Logging verbosity level |
| `--skip-build` | No | Skip the pre-run build step (use only when you have just built) |
| `--profiling` | No | Collect per-activity timings and runtime screenshots for the run — verifies UI automation correctness and workflow performance. Boolean flag (no value needed). Also accepted on `debug start`, `debug test-activity`, `debug start-from-here`; silently ignored on stepping/breakpoint verbs. Response carries `Profiling.OutputDirectory` when collection succeeds. See [debugging.md § Profiling Workflow Performance](debugging.md#profiling-workflow-performance). |

For debugging — breakpoints, stepping, exception-handling lifecycle — use the `debug` group (see [debugging.md](debugging.md)). For UI automation workflows in particular, prefer `debug start` over `run` so the app is preserved for selector repair on error.

```bash
uip rpa debug start --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
uip rpa execution cancel --project-dir "<PROJECT_DIR>" --output json
```

Both `run` and `debug start` return the same envelope: `{Result: "Success"|"Failure", Code, Data: {runResult: "<json-string>"}, Message?, Instructions?}`. `Data.runResult` is a **JSON string** (not an object) — parse it separately to read the run result, which has exactly three fields:

- `Output` — the workflow's own serialized output arguments JSON (`""` for non-`Start*` commands and on debug-command responses). **`Output` carries the workflow's data, not a verdict.**
- `HasErrors` — `true` iff execution did not complete successfully (compile failure, validation failure, unhandled exception, cancellation, or timeout); `false` otherwise.
- `ErrorMessage` — formatted error chain when `HasErrors: true`; `null` otherwise.
- `Profiling` — present only when `--profiling` was passed on a start verb **and** profiling collection succeeded. Single field `OutputDirectory` is the absolute path to `%LOCALAPPDATA%\UiPath\ProfiledRuns\HHmmss_yyyy-MM-dd_<entryPoint>_<projectName>\` containing the `*.uistat` files and runtime screenshots for that run — used to verify UI automation correctness and workflow performance. `null` / omitted otherwise (profiling not requested, run did not reach the executor, or the active Studio profile does not support profiling).

Workflow log output (`Log Message` activity, system traces) does NOT appear in `runResult`. Logs are streamed in real time during execution on a separate channel; the result envelope only carries the verdict and the workflow's output data.

> **Single source of truth for success/failure: outer `Result` (and equivalently `HasErrors` inside `runResult`).** `Result: "Success"` already accounts for compile failures, validation failures, and unhandled runtime exceptions — the CLI propagates them. **DO NOT infer failure from streamed log entries' `Level`.** A successful workflow may emit `Log Message` at `Error` or `Warning` level as observability — those are workflow-emitted data, not CLI failures. Treating log levels as a verdict flips green runs to "failed" and burns retries on healthy workflows.

---

### validate

Return validation errors for a file or project. By default, forces Studio to re-validate before returning errors.

```bash
uip rpa validate [--file-path "<FILE>"] [--skip-validation] --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | No | File to check, **relative to the project directory**. Omit to check the whole project. |
| `--skip-validation` | No | Return cached errors without re-validating (faster, but may be stale) |

> **Known issue: absolute `--file-path` + absolute `--project-dir` falsely fails with `The targeted project file <X> is not in the project folder <Y>`.** The CLI normalizes `--file-path` to forward slashes (`C:/.../Main.xaml`) but leaves `--project-dir` as backslashes (`C:\...\Project`), then string-compares them — same path, different separator, comparison fails. Pass `--file-path` **relative** to the project directory (e.g. `--file-path "Main.xaml"`) to sidestep the normalization mismatch. If you need a project-level compile gate that doesn't have this quirk, use `uip rpa build "<PROJECT_DIR>"` (positional arg, no slash compare).

---

### build

Build (compile) a UiPath project. Compiles all XAML expressions — catches runtime-compile failures that `validate` misses. Required before returning a project to the user (see [validation-guide.md § Project Build Verification](validation-guide.md#project-build-verification-required-before-returning-a-project)). Runs independently of Studio IPC; takes the project directory as a positional argument.

```bash
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<projectDir>` | Yes | Path to the project directory (positional — not `--project-dir`) |
| `--log-level` | No | `Debug` / `Info` / `Warn` / `Error`. Default `Warn`. |
| `--skip-analyze` | No | Skip the static analysis step (faster, less thorough) |
| `--exclude-configured-sources` | No | Exclude user/machine-configured NuGet sources |
| `--nuget-sources-config-path` | No | Path to a custom NuGet sources config file |
| `--governance-file-path` | No | Path to a governance/policy rules file |
| `--governance-file-type` | No | Type of the governance file |
| `--detailed-log-path` | No | Path to write a detailed log file |

**Relationship to `run`:** `run` (and `debug start`) compile internally, so a successful smoke test implies `build` would pass. When no smoke test is run (side effects, interactive workflow, no test input), `build` is the required end-goal check for compilability — including attribute-form expression failures (`JIT compilation is disabled for non-Legacy projects`) in XAML projects with `expressionLanguage: CSharp` that don't surface during static `validate`.

---

### analyzer-rules list

List the Workflow Analyzer rules currently **enabled** for the project — the best-practice rules that `validate` and `uip rpa build` will enforce. Reports rules only, not violations.

```bash
uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--project-dir` | No | Project directory. Defaults to CWD. |
| `--scope` | No | Narrow results: `Activity`, `Workflow`, `Project`, or `Coded Workflow`. |

Each rule returns `severity` (`error` / `warning` / `info`), rule ID (e.g. `ST-DBP-010`, `MA-DBP-028`), scope (`Activity` / `Workflow` / `Coded Workflow` / `Project`), title, and — when available — `recommendation` and `docs` URL. Prefix convention: `ST-*` = built-in Studio rule, `MA-*` = package-shipped rule.

> **Performance:** the unscoped call enumerates every rule across every package and can take a minute or more on projects with many activities packages. If the default 60 s shell timeout fires, retry with `--scope <ScopeYouNeed>` (e.g. `Activity` for single-activity generation, `Coded Workflow` for `.cs` authoring) — scoped calls return in seconds.

---

## Commands -- Package Management

### packages install

Install or update NuGet packages in the project.

```bash
uip rpa packages install --packages '[{"id": "UiPath.Excel.Activities"}]' --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--packages` | Yes | JSON array of objects with `id` and optional `version` |

Omit `version` to automatically resolve the latest compatible version (preferred). Only pin a specific version when there is a known compatibility constraint.

**Error recovery:**
- **Package not found** -- verify the exact package ID; use `--help` or activity docs to discover the correct name.
- **Network/feed error** -- check NuGet feed configuration in Studio settings.

---

### packages versions

Get available versions for a NuGet package.

```bash
uip rpa packages versions --package-id <PackageId> --include-prerelease --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--package-id` | Yes | NuGet package ID to query |
| `--include-prerelease` | No | Include prerelease versions (default false) |

> **Default to `--include-prerelease`.** UiPath activity packages frequently ship as `-preview` between stable releases, and previews carry the freshest activity surface and `.local/docs` content. Omitting the flag hides them and the agent picks a stale stable. When the user already has a stable version installed and a newer (stable or preview) is available, inform them and offer the upgrade — never force.

---

## Commands -- Data Fabric Entities

UiPath Data Fabric entities live in the Orchestrator tenant's Data Service. To use them in an RPA project -- as typed arguments (e.g. `UiPath.DataService.Activities`, `test-data add-entity`) or anywhere else that binds to generated entity types -- they must first be **installed** into the project. Installation writes a manifest at `.entities/EntitiesStore.json` and compiles a strongly-typed assembly; all entity-aware activities, coded service calls, and test-data bindings resolve against it.

Typical flow: `data-fabric-entities list` (discover) → `data-fabric-entities install --add ...` (install) → reference the generated entity types from your workflow or test case.

---

### data-fabric-entities list

List Data Fabric entities relevant to the active project. Returns a unified view of entities currently installed in the project **and** entities available in the connected tenant, each tagged with an `installed` flag.

```bash
uip rpa data-fabric-entities list --project-dir "<PROJECT_DIR>" --output json
uip rpa data-fabric-entities list --service-document "<PATH>" --project-dir "<PROJECT_DIR>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--service-document` | No | Project-relative path to a specific entities manifest (e.g. `.entities/Custom.json`). Omit to use the project's default. |

Each returned entry includes: `name`, `displayName`, `namespace` (if installed), `serviceDocument` (if installed), `storeUrl` (if cloud-available), and `installed: true | false`.

Use this before `data-fabric-entities install` to pick names from the tenant, or to verify what is already bound to the project.

---

### data-fabric-entities install

Install, update, or remove Data Fabric entity bindings by applying an add/remove delta to the project's currently installed set. Dependency expansion is automatic -- adding `E1` pulls in any entity `E1` references.

```bash
uip rpa data-fabric-entities install --add "Invoice" --add "Customer" --project-dir "<PROJECT_DIR>" --output json
uip rpa data-fabric-entities install --remove "LegacyOrder" --project-dir "<PROJECT_DIR>" --output json
uip rpa data-fabric-entities install --add "Invoice" --remove "LegacyOrder" --namespace "My.App.Entities" --project-dir "<PROJECT_DIR>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--add` | One of `--add`/`--remove` | Entity name to add. Pass the flag multiple times for multiple entities (e.g. `--add Invoice --add Customer`). |
| `--remove` | One of `--add`/`--remove` | Entity name to remove. Pass the flag multiple times for multiple entities (e.g. `--remove LegacyOrder --remove StaleCustomer`). |
| `--service-document` | No | Project-relative manifest path. Omit to use the project's default. |
| `--namespace` | No | .NET namespace for the generated entity types. Omit to keep the previously-used namespace, or derive one from the project name on a first install. |

Behavior notes:

- **Semantics:** final selection = `(currently installed ∪ add) − remove`. If the same name appears in both `--add` and `--remove`, remove wins.
- **Dependencies:** pulled in automatically; the returned `entities` array is the full set actually installed.
- **Server-deleted entities:** silently filtered before install -- they can't be compiled against. The diff between request and returned `entities` tells you what was dropped.
- **Empty resulting selection:** uninstalls everything for the target service document (removes the manifest + generated assembly).
- **At least one of `--add` / `--remove` must be non-empty.** To fully uninstall, pass every currently-installed name in `--remove`.

Returns JSON:
```json
{ "serviceDocument": ".entities/EntitiesStore.json", "namespace": "My.App.Entities", "entities": ["Invoice", "Customer", "Address"] }
```

**Use this before** invoking any workflow or test case that references the entity types, and before `test-data add-entity` -- the test-data command requires its target entity to already be managed in the project.

---

## Commands -- Test Manager

Test Manager integration has moved to the dedicated `uip tm` tool — see `uip tm --help`. The two read-only verbs previously exposed under `uip rpa` (`get-manual-test-cases`, `get-manual-test-steps`) are no longer documented here and should not appear in new skill content.

---

## Commands -- Integration Service (IS)

All IS commands support `--output json`. The CLI is self-documenting: `uip is --help`, `uip is connections --help`, etc.

### connectors list

List available connectors, optionally filtered by name or key.

```bash
uip is connectors list --output json
uip is connectors list --filter "<NAME_OR_KEY>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--filter` | No | Filter by connector name or key |

---

### connectors get

Get details for a specific connector.

```bash
uip is connectors get <CONNECTOR_KEY> --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |

---

### connections list

List connections, optionally filtered by connector.

```bash
uip is connections list --output json
uip is connections list <CONNECTOR_KEY> --output json
uip is connections list --connection-id "<ID>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | No | Filter by connector key (positional) |
| `--connection-id` | No | Filter by specific connection ID |
| `--folder-key` | No | Filter by folder key |

---

### connections create

Create a new connection via OAuth flow. Opens a browser for authentication.

```bash
uip is connections create <CONNECTOR_KEY>
uip is connections create <CONNECTOR_KEY> --no-browser
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |
| `--no-browser` | No | Print the OAuth URL instead of opening a browser |

---

### connections ping

Verify a connection is alive and authenticated.

```bash
uip is connections ping <CONNECTION_ID>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connection-id>` | Yes | Connection ID (positional) |

---

### connections edit

Re-authenticate or edit an existing connection. Opens OAuth flow.

```bash
uip is connections edit <CONNECTION_ID>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connection-id>` | Yes | Connection ID (positional) |

---

### activities list

List activities available for a connector.

```bash
uip is activities list <CONNECTOR_KEY> --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |

---

### resources list

List resources available for a connector, optionally filtered by operation.

```bash
uip is resources list <CONNECTOR_KEY> --output json
uip is resources list <CONNECTOR_KEY> --operation List --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |
| `--operation` | No | Filter by operation: `List`, `Retrieve`, `Create`, `Update`, `Delete`, `Replace` |

---

### resources describe

Get the schema for a specific resource object.

```bash
uip is resources describe <CONNECTOR_KEY> <OBJECT_NAME> --output json
uip is resources describe <CONNECTOR_KEY> <OBJECT_NAME> --operation Create --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |
| `<object-name>` | Yes | Resource object name (positional) |
| `--operation` | No | Schema for a specific operation |

---

### resources run

Run a CRUD operation on a connector resource.

```bash
uip is resources run <OPERATION> <CONNECTOR_KEY> <OBJECT_NAME> --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<operation>` | Yes | One of: `create`, `list`, `get`, `update`, `replace`, `delete` |
| `<connector-key>` | Yes | Connector key (positional) |
| `<object-name>` | Yes | Resource object name (positional) |

---

## CLI Error Recovery

When `uip` commands fail, diagnose by error category:

| Error Pattern | Cause | Recovery |
|---------------|-------|----------|
| `"connection refused"`, `"EPIPE"`, `"pipe not found"` | Studio IPC not available. Headless Studio (Helm): NuGet restore failed or process exited. Studio Desktop: not running. | Re-run the command — headless Studio relaunches automatically. If it persists, raise `--timeout` and check the Helm restore output for NuGet errors. Only run `uip rpa studio start` if the failing command is `files diff`/`focus-activity` or `UIPATH_RPA_TOOL_USE_STUDIO=1` is set. |
| `"timeout"`, `"ETIMEDOUT"` | Command took too long. Cold Helm NuGet restore can take 30–90 s. | Raise the timeout: `uip rpa --timeout 600 <command>`. For `validate`, also try `--skip-validation`. |
| `"not authenticated"`, `401`, `403` | Auth required for cloud features | Run `uip login` and re-try |
| `"package not found"`, `"version not available"` | Wrong package ID or version | Verify package name via `uip rpa activities find`; omit `version` to auto-resolve latest |
| `"project not found"`, `"no project open"` | Wrong project-dir or project not open in Studio | Verify `--project-dir` path, run `uip rpa project open` |
| `"file not found"` in `validate` | Wrong `--file-path` (must be relative to project) | Use path relative to project root, not absolute |
| `"Studio is busy"`, `"operation in progress"` | Studio is processing a previous request | Wait a few seconds and retry the command |
| Any unrecognized error | Unknown | Check `--verbose` flag: `uip rpa --verbose <command>` for debug details, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.

---

## RPA-Specific Commands

### activities find

Search for activities by keyword. Global search -- not limited to installed packages.

```bash
uip rpa activities find --query "<KEYWORD>" --output json
uip rpa activities find --query "<KEYWORD>" --tags "<TAGS>" --limit 20 --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--query` | Yes | Search keyword |
| `--tags` | No | Filter by tags |
| `--limit` | No | Max results (default 10) |

---

### activities get-default-xaml

Get the default XAML template for an activity. Two modes depending on whether the activity is dynamic (connector-backed) or not.

```bash
# Non-dynamic activity:
uip rpa activities get-default-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json
# Dynamic activity (connector-backed):
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--activity-class-name` | One mode | Fully qualified class name (non-dynamic) |
| `--activity-type-id` | One mode | Activity type ID (dynamic) |
| `--connection-id` | No | Connection ID for dynamic activities |

---

### workflow-examples list

Search example workflows by service tags.

```bash
uip rpa workflow-examples list --tags "service1,service2" --output json
uip rpa workflow-examples list --tags "service1" --prefix "<PREFIX>" --limit 20 --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--tags` | Yes | Comma-separated service tags |
| `--prefix` | No | Filter by name prefix |
| `--limit` | No | Max results (default 10) |

---

### workflow-examples get

Retrieve the full XAML content of an example workflow.

```bash
uip rpa workflow-examples get --key "<BLOB_PATH>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--key` | Yes | Blob path from `workflow-examples list` results |

---

### focus-activity (hidden)

Focus an activity in the Studio Desktop designer view. **Requires a running Studio Desktop instance** — does not work against headless Studio. Hidden from `--help` (agent → user UI cue), but reachable directly by name. Run `uip rpa studio start --project-dir "<PROJECT_DIR>"` first if Studio Desktop is not already up.

```bash
uip rpa focus-activity --activity-id "<IDREF>" --output json
uip rpa focus-activity --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--activity-id` | No | Activity IdRef. Omit to focus all activities sequentially. |

---

### RPA Discovery Tools

| Action | How |
|--------|-----|
| **Explore project files** | `Glob` with `**/*.xaml` pattern |
| **Search XAML content** | `Grep` with regex across `.xaml` files |
| **Explore object repository** | `Glob` `**/*` in `{projectRoot}/.objects/` + `Read` metadata |
| **Get JIT type definitions** | `Read` `{projectRoot}/.project/JitCustomTypesSchema.json` |
| **Activity docs** | See the Installed Package Activity Documentation section above |

## Debugging — the `debug` group

The `uip rpa debug` group exposes full interactive debugging: breakpoints, step-by-step execution, isolated activity testing, exception handling, and runtime state inspection. Cancel a run or debug session with `uip rpa execution cancel`. For the complete debug verb reference and common debugging workflows, see **[debugging.md](debugging.md)**.

### Connector Capabilities

For RPA-specific connector workflow patterns (activity/resource discovery, connection management, schema inspection), see [connector-capabilities.md](connector-capabilities.md).

---

## Coded-Specific Commands

### packages inspect

Inspect a NuGet package to discover its API surface (classes, methods, properties). See [coded/inspect-package-guide.md](coded/inspect-package-guide.md) for full usage.

---

## UI Automation Commands (`uip rpa uia ...`)

UIA subcommands and flags are documented in the `UiPath.UIAutomation.Activities` package. See `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.
