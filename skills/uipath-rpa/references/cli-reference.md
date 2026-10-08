# UiPath CLI (`uip`) Reference

`uip rpa` and sibling tools (`uip is`, `uip tm`, …) communicate with UiPath Studio over named pipes (IPC). Use this reference to discover live commands and flags and handle behaviors `--help` omits.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
> Command and flag lists here are not exhaustive or necessarily current; the CLI is the source of truth. Discover the live surface with `--help`.
>
> Installation is automatic. Do NOT install `uip` manually or instruct the user to install it.

---

## Discover the live CLI with `--help`

Append `--help` at any level to drill from tools to groups, verbs, and parameters. Run `--help` rather than guessing commands, flags, or values; guesses fail with `unknown command`/`unknown option`.

```bash
uip --help
uip tools list
uip rpa --help
uip rpa packages --help
uip rpa validate --help
uip is --help
uip skills --help
```

The pattern works for every tool and depth (`uip rpa uia <verb> --help`, `uip login --help`, etc.). **Run `--help` standalone; never combine it with other flags.** For example, `uip rpa <verb> --help --project-dir "<path>"` parses the value as a positional command and exits with `unknown command '<value>'`; drop every other flag when probing help. A verb may be hidden yet callable by exact name (for example diagnostic or UI-cue verbs); absence from help means it is not part of the standard loop, not that it does not exist.

---

## Output format

`--output` defaults to `json`; accepted values are `json`, `table`, `yaml`, `plain`. Use `json` for programmatic parsing; `table` pads columns and can exceed 100 KB. `--output-filter "<JMESPath>"` applies JMESPath to the response envelope's `Data`; use it to slice large responses instead of shell post-processing. Global flags: `--log-level <debug|info|warn|error>` and `--log-file <path>`. Raise log level or add `--verbose` to diagnose failures.

Most envelopes have `{Result: "Success"|"Failure", Code, Data, Message?, Instructions?}`. Branch on `Result`, not stdout text.

---

## Authentication

Cloud features (feed templates/packages, Integration Service, Data Service entities, publishing) require a logged-in session:

```bash
uip login
uip login status
uip login which
```

If a command fails with `not authenticated` / `401` / `403`, run `uip login` and retry. Discover non-interactive/CI options (credentials folder, client id/secret, authority) with `uip login --help`.

---

## Project context: `--project-dir`

Most `uip rpa` verbs use `--project-dir`, defaulting to the current working directory. For another project, pass the absolute path to the folder containing `project.json`. Some verbs differ: `init` takes `--name` + `--location`; `build`/`pack` take the project dir positionally. Confirm with that verb's `--help`.

For project creation, see [environment-setup.md](environment-setup.md). `--target-framework` and `--expression-language` are immutable after `init`; choose them per SKILL.md first.

---

## Headless Studio (Helm) vs Studio Desktop

`uip rpa` uses one of two Studio flavors over the same IPC contract:

- **Headless Studio (Helm), default:** Ships as a NuGet package and auto-launches on first use; no Desktop install is needed. A cold NuGet cache may be nearly silent for 30–90 s during `dotnet restore`; the default shell timeout covers it. Raise `timeoutSeconds` only for a slow feed.
- **Studio Desktop:** A running Desktop instance with the project open handles its `uip rpa` calls, including `run` and `debug start`. Run `uip rpa instances list --output json` to see instance/project ownership. UI-side-effect verbs (open a window, highlight the designer; discover via `--help`) work only here: ensure Desktop is running with `uip rpa studio start --project-dir "<PROJECT_DIR>"` first. Force Desktop for any command with `UIPATH_RPA_TOOL_USE_STUDIO=1` (not recommended for the standard authoring loop). `run` / `debug start` payloads differ by backend; see [Reading run / debug results](#reading-run--debug-results).

`--studio-dir` is consulted only for Desktop; Helm ignores it. If Desktop auto-detection fails, resolution falls back to `UIPATH_STUDIO_DIR`, default install path, then dev build output. Errors `"does not have interop support"` / `"Requires Studio 26.2+"` mean Desktop is too old: tell the user to update it. This affects only Desktop-only verbs.

---

## Installed package activity documentation

Installed package activity docs are under `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`; read them for per-activity properties and coded API signatures unavailable through `--help`.

| Action | How |
|---|---|
| Read an activity doc | `Read` `…/{PackageId}/activities/{ActivityName}.md` (preferred when package + class are known) |
| Read coded API doc | `Read` `…/{PackageId}/coded/coded-api.md` |
| Read package overview | `Read` `…/{PackageId}/overview.md` |
| List documented packages / activities | `Bash`: `ls …/.local/docs/packages/`, then `ls …/{PackageId}/activities/` |
| Search activity docs | Use Bash `ls` on the exact package directory (`…/.local/docs/packages/<PackageId>/activities/`), then `Read` the matching path. Do NOT use `Glob` or `Grep`: both skip gitignored `.local/`, and a miss proves nothing. |

---

## Reading run / debug results

`uip rpa run` executes without debugging; the `debug` group handles breakpoints, stepping, and exceptions (see [debugging.md](debugging.md)). For UI automation, prefer `debug start` over `run` to preserve the app for selector repair on error. Cancel active runs/sessions with `uip rpa execution cancel`. Pass inputs as repeatable `--input-arguments key=value` pairs (see [Passing structured inputs](#passing-structured-inputs)); discover other flags (log level, skip-build, profiling) with `--help`.

Both return `{Result, Code, Data}`; identify the backend from `Data` keys ([§ Headless Studio (Helm) vs Studio Desktop](#headless-studio-helm-vs-studio-desktop)):

| Backend | `Data` keys | Workflow `Log Message` output |
|---|---|---|
| **Helm** (no Desktop instance has project open) | `output` (serialized output arguments; `"{}"` if none), `hasErrors`, `errorMessage`, `profiling`, `debugState`, `debugDetails` | Stdout `[<Level>] …` lines (`[Information]`, `[Error]`, …) above JSON; not in `Data` |
| **Studio Desktop** (project open in running Desktop) | `output` (status string; `"Session ended"` on completion), `errors` (array), `logEntries` (array of `{source, level, message}`; `source` is `Compile` or `Debug`), `debugState` (`"Completed"` on completion; absent if file could not open) | `Data.logEntries`; nothing above envelope |

Field meanings: [debugging.md § Output Format](debugging.md#output-format).

- **Helm passes only if** `hasErrors` is `false`, `errorMessage` is `null`, and `debugState` is `null` or `"Completed"`. A faulted run, failed validation, or missing entry point returns outer `Result: "Failure"`, with the same fields JSON-encoded in `Message` (`hasErrors: true`, `errorMessage` = failure text). A faulted `debug start` instead returns `Result: "Success"`, `hasErrors: false`, `debugState: "Suspended"`, exception in `debugDetails`, and command guidance in `errorMessage`; the session remains alive, so cancel or continue it.
- **Desktop passes only if** `errors` is empty and `output` is `"Session ended"`. A missing entry point returns outer `Result: "Success"`, `errors: []`, `logEntries: []`, and `output: "Failed to open the file <absolute path>"`. An undeclared `--input-arguments` key is silently accepted (`"Session ended"`).
- **On either backend: never read the outer `Result: "Success"` as a passing run, and never infer failure from a `Warning` / `Error` log level** — `Log Message` activities emit at any level, and treating log levels as a verdict flips green runs to "failed" and burns retries.

### Capturing the verdict

Run `run` / `debug start` **without `--output-filter`** and read the printed envelope. Backend-specific keys make cross-backend filters fail (`Filter '…' failed to evaluate: Invalid type … received type null`) after the workflow has run: for example, `length(errors)` on Helm or a function on `hasErrors` on Desktop. Retrying re-drives the application. On Helm filters cannot reach log lines outside `Data`.

```bash
uip rpa run --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --skip-build --output json
```

On Helm, read workflow values from `[Information]` lines above the envelope; do not strip them with `grep -v '^\['`. On Desktop, use `logEntries`; `Trace` entries (`Unregistered service requested …`, `Audit: …`) may outnumber workflow lines. Helm `debug start` exposes suspended-state exceptions through `debugState` / `debugDetails` for selector recovery.

Never use `| tail -N` or `| head -N`: Helm logs precede the envelope, while Desktop's `output` and `errors` precede potentially long `logEntries`; either truncation loses required information and recovery requires re-running (which may change a non-rerun-safe workflow). For a Helm `Result: "Failure"` with no `Data`, read `Message`: JSON-encoded Data fields (`hasErrors: true`) indicate a run fault, validation failure, or missing entry point; `{"success": false, "errorMessage": "…"}` indicates an unopenable project directory or busy executor.

If more detail is needed (compile-phase error or stack older than visible lines), redirect all stdout with `> run.log` and read the file: Helm `[Error]` lines and envelope `errorMessage`, or Desktop `errors` and `logEntries`. `jq` is absent on a standard Windows agent host; the envelope is the file's last JSON object.

---

## Passing structured inputs

`--input-arguments` and `--input-variables` accept repeatable `key=value` pairs, `key:=value` raw JSON, `key=@file`, inline JSON, or JSON files via `'@file'` / `--<flag>-file`. `--packages` takes one item per occurrence as comma-joined fields.

```bash
uip rpa run --file-path Main.xaml --input-arguments name=John --input-arguments retries:=3
uip rpa run --file-path Main.xaml --input-arguments 'message=Hello, world!'
uip rpa debug test-activity --input-variables greeting=@expression.txt
uip rpa run --file-path Main.xaml --input-arguments '@args.json'
uip rpa run --file-path Main.xaml --input-arguments-file args.json
uip rpa packages install --packages 'id=UiPath.System.Activities,version=23.10.1' --packages id=UiPath.Excel.Activities
```

- `=` sends a string (`count=42` → `"42"`); `:=` sends raw JSON (`count:=42` → number `42`). For `debug test-activity` / `debug start-from-here`, values are VB/C# expression strings: always use `=`.
- Single-quote tokens containing spaces, commas, or leading `@`; bare identifiers/numbers need no quotes. Windows PowerShell 5.1 strips inline double quotes: write such values to UTF-8 with `Set-Content -Encoding UTF8` and use `key=@file`, `'@file'`, or `--<flag>-file`.
- Inline JSON such as `--input-arguments '{"k":"v"}'` remains accepted for backward compatibility but is unreliable on PowerShell 5.1; prefer pairs or files.
- `--input-arguments key=` passes an empty string and overrides a coded workflow's declared default. Omit the flag to use the default.

---

## validate

`uip rpa validate` returns file or project diagnostics, re-validating by default. `--skip-validation` reads cached, possibly stale, results; `--min-severity` filters. Confirm flags with `uip rpa validate --help`.

`--file-path` accepts project-relative (`--file-path "Main.xaml"`) or absolute paths with forward, back, or mixed separators. Prefer relative paths for portability.

---

## build

`uip rpa build` compiles the whole project, not only files passed to per-file `validate`. It is required before returning a project (see [§ Project Build Verification](#project-build-verification-required-before-returning-a-project)), takes project dir positionally, and runs independently of Studio IPC. Discover log level, skip-analyze, governance, and NuGet source flags with `uip rpa build --help`.

`run` and `debug start` compile internally, so a successful smoke test implies build would pass. If no smoke test runs (side effects, interactive workflow, no test input), `build` is the compilability check.

---

## analyzer-rules list

`uip rpa analyzer-rules list` reports enabled Workflow Analyzer rules enforced by `validate` and `build`, not violations. Do NOT run as an authoring prerequisite; run only if the user asks about best-practice/analyzer rules or repeated same-family violations suggest authoring against the full set. Each rule gives `severity` (`error`/`warning`/`info`), rule ID, scope, title, and optionally `recommendation` and `docs` URL. Prefixes: `ST-*` built-in Studio; `MA-*` package-shipped.

`Coded Workflow` rules run Roslyn analyzers over project `.cs` files during `analyze`, `build`, and `pack`, with the same enforcement as XAML-scoped rules. The four built-ins are all Error severity; triggers/fixes: [coded/operations-guide.md § Coded Workflow Analyzer Rules](coded/operations-guide.md#coded-workflow-analyzer-rules).

The unscoped command enumerates every rule across every package and can take a minute or more. Narrow using `--scope` (`Activity`, `Workflow`, `Project`, or `Coded Workflow`) for results in seconds; confirm accepted values with `--help`.

---

## packages install

`uip rpa packages install` is the canonical way to add/update NuGet dependencies; do not hand-edit `project.json` (there is no `add-dependency` verb). Repeat `--packages` per package with comma-joined `key=value` fields, such as `--packages 'id=<PackageId>,version=<Version>'` or `--packages id=<PackageId>` (see [Passing structured inputs](#passing-structured-inputs)); discover other flags with `uip rpa packages install --help`.

- Omit version to resolve latest compatible automatically (preferred); pin only for known compatibility constraints.
- Discover versions with `uip rpa packages versions --package-id <Id> --include-prerelease`. Default to `--include-prerelease`: activity packages often ship `-preview` versions between stable releases with the freshest activity surface and `.local/docs`. If a newer stable or preview exists, inform the user and offer the upgrade; never force it.
- For package not found, verify exact ID using `activities find` or package `.local/docs`. For feed/network errors, check NuGet feed config in Studio settings.

---

## object-repository

The project's UI Object Repository stores applications, screens, and elements (selectors/targets) used by UI Automation activities. Both read commands require an open project.

> Both verbs are top-level and hyphenated; `uip rpa object-repository` returns `Unknown command: object-repository`, whether Studio is running or not. This differs from the UIA OR CLI, which writes entries and has no `get`.

- **Project repository:** `uip rpa get-object-repository` returns the project's own JSON tree (applications → screens → elements), with each entry's `name`, `description`, `type`, `reference`; referenced-library entries are excluded. It takes only standard `--project-dir`:

  ```bash
  uip rpa get-object-repository --project-dir "<PROJECT_DIR>" --output json
  ```

  `name` values are Object Repository names, not C# members: `Result Display` becomes `Result_Display` in `Descriptors.*`. Convert per coded authoring guide § Descriptor Naming, routed from `ui-automation-guide.md` § Documentation.

- **Library repository:** `uip rpa get-library-object-repository` reads repositories in library `.nupkg` files, grouped by library; packages without one are omitted. Required `--library-paths` takes absolute path(s) as one comma-separated flag (not repeatable; avoid paths containing commas):

  ```bash
  uip rpa get-library-object-repository --project-dir "<PROJECT_DIR>" --library-paths "C:\\libs\\Acme.UiLib.1.2.0.nupkg,C:\\libs\\Other.UiLib.2.0.0.nupkg" --output json
  ```

Before authoring UI Automation activities, read the project repository to reuse existing screens/elements rather than re-indicating them; read the library repository for targets exposed by referenced UI libraries. Confirm flags with `uip rpa get-object-repository --help` / `uip rpa get-library-object-repository --help`.

---

## Commands -- Data Fabric Entities

Data Fabric entities live in the Orchestrator tenant's Data Service. To use them in an RPA project (typed arguments with `UiPath.DataService.Activities`, test-data bindings, or generated entity types), install them first; installation writes `.entities/` manifest and compiles a strongly-typed assembly. Discover exact flags with `uip rpa data-fabric-entities --help`.

1. **List:** Shows entities installed in the project and available in the connected tenant, with an `installed` flag. Run before installing to select names or verify bindings.
2. **Install:** Applies an add/remove delta; dependency expansion automatically adds referenced entities and server-deleted entities are silently dropped. Final selection is `(installed ∪ add) − remove`; an empty result uninstalls all entities in that manifest.

Install entities before invoking workflows/test cases referencing generated types and before test-data commands binding to an entity.

---

## Integration Service (`uip is`)

`uip is` manages connectors, connections, resources, triggers, and webhooks. Discover `uip is` with `uip is --help`, then drill down (for example, `uip is connections --help`, `uip is resources describe --help`). All verbs support `--output json`. The surface covers connector/activity/resource listing and description, connection list/create/ping/edit (OAuth opens a browser; `--no-browser` prints URL), and resource CRUD. For RPA connector activity/resource discovery, connections, and schema inspection, see [is-connector-xaml-guide.md](is-connector-xaml-guide.md).

---

## Test Manager

Choose by intent:

- **`uip tm` dedicated tool:** Runtime Test Manager operations (manual test cases, runs, results); discover with `uip tm --help`. Do not invoke runtime verbs from `uip rpa`.
- **`uip rpa tm`:** Project authoring/setup, editing `.tmh/config.json`; pure file I/O, no Studio or Helm process required.

### `uip rpa tm` verbs

| Verb | Purpose |
|---|---|
| `uip rpa tm connect --url <url>` | Set server URL (`testManagerBasePath`). Switching host/org/tenant clears the old server's default project. |
| `uip rpa tm set-default-project --id <guid> [--name <name>] [--key <key>]` | Set default project (`defaultProject`); requires `connect` first. |
| `uip rpa tm clear-default-project` | Clear default project; keep server URL. |
| `uip rpa tm status` | Show server URL and linked default project. |

All verbs take standard `--project-dir` and `--output json`. Typical setup:

```
uip rpa tm connect --url "https://cloud.uipath.com/<org>/<tenant>/testmanager_" --project-dir "<PROJECT_DIR>" --output json
uip rpa tm set-default-project --id <project-guid> --name "<project-name>" --key "<KEY>" --project-dir "<PROJECT_DIR>" --output json
uip rpa tm status --project-dir "<PROJECT_DIR>" --output json
```

`set-default-project` does not validate the id with a server round-trip; supply a real project id and optional name/key. Project listing is unavailable here; get the id from Test Manager. Confirm flags with `uip rpa tm --help`.

#### Acting on `reloadHint` in the output

`connect` / `set-default-project` / `clear-default-project` may return `reloadHint` only if the project is open in Studio older than 26.0.197, which reads `.tmh/config.json` only at project open. If present, tell the user to close and reopen the project; CLI cannot do this. If absent, no action is needed: the project is not open in Studio or Studio 26.0.197+ applies changes live.

---

## Fix One Thing at a Time

When an error occurs, identify its root cause, fix only that issue, then rerun. Never bundle speculative improvements with the actual fix: multiple changes prevent identifying what resolved or introduced the issue. Verify one fix per iteration.

## Validation Iteration Loop

Phase 1: per-file `validate` after every edit. Phase 2: one project-level `build` per edit session.

```
PHASE 1 — validate-clean (per-file):
  FOR each file created or edited in this session:
    REPEAT:
      1. uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
      2. IF validate has errors -> fix one root cause, GOTO 1
      3. EXIT inner loop when validate is clean

PHASE 2 — build-clean (per-project, once per edit session):
  REPEAT:
    1. uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
    2. IF build has errors -> identify offending file from build output
       a. uip rpa validate --file-path "<OFFENDER>" --project-dir "<PROJECT_DIR>" --output json
       b. fix one root cause, GOTO 1
    3. EXIT to Smoke Test
```

Both phases are required: per-file `validate` covers the target deeply (structural XAML, missing references, analyzer rules, schema violations, unknown members, invalid enums, expression compilation); project-wide `build` covers every workflow, project-scope rules, and packaging. Build output identifies the offender; re-run targeted `validate` to locate its issue. Neither phase detects an attribute-form expression that silently resolves to a literal (see § What each phase covers).

Target changed files with `validate --file-path` (faster than whole-project); `build` has no `--file-path` and is project-scoped.

**5-attempt cap per loop:** allow 5 attempts for each Phase 1 file loop and a separate 5 for Phase 2 build loop. When exhausted, present remaining errors; they may require domain knowledge or environment-specific fixes. Reset each loop's counter when starting a new loop (new file, new user prompt, or resuming after user input).

### Rules

1. DO NOT stop until all errors are resolved or cannot be resolved automatically.
2. DO NOT obsess over one error: skip an unresolvable one, continue, and defer it to the user with an informative, step-by-step message at the end.
3. DO NOT skip validation steps.
4. DO NOT assume edits worked without checking.
5. DO NOT bundle fixes: fix one root cause, rerun, and verify; never add speculative changes alongside the actual fix.
6. Warnings are non-blocking. When `validate`/`build` (and, if required, `pack`/`run`) have no errors, deliver; investigate warnings only if requested or blocking an acceptance criterion.

Full command docs: [§ validate](#validate) and [§ Reading run / debug results](#reading-run--debug-results).

## Project Build Verification (Required Before Returning a Project)

Every returned project must compile. A clean Phase 2 build satisfies this gate; otherwise run the standalone command (for example, to reverify after a small fix outside the loop):

```bash
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

If build fails, use the Phase 2 fix loop (one root cause per iteration, rerun, cap 5 attempts). A successful `run` smoke test substitutes for build because `run` compiles internally.

### What each phase covers

Per-file `validate` loads the target through the workflow designer and compiles its expressions, reporting:

| Error class | Example | Reported as |
|---|---|---|
| Unknown member name | `<uix:NGetText Value="[x]" />` (correct: `TextString`) | `Could not load <file>: 'Cannot set unknown member '<Class>.<Prop>''` |
| Invalid enum value | `ClickType="BogusValue"` | `Could not load <file>: 'Failed to create a '<Prop>' from the text '<value>''` |
| Broken expression | `undefinedSymbol + 1` inside a `CSharpValue` | `CS0103: The name '<symbol>' does not exist in the current context` |

Build remains required because it compiles every workflow (including untouched/unvalidated files), enforces project-scope rules, and packages. Edited files can validate clean while another file makes build fail.

Neither phase catches an attribute-form expression on an `InArgument<Object>`: `Message="calcResult"` deserializes as a literal, so validate/build/run can all succeed while logging `calcResult` instead of the variable value. The signal is wrong output; inspect the smoke-test output (see [§ Smoke Test](#smoke-test) and [xaml/csharp-activity-binding-guide.md § C# Expression Pitfalls](xaml/csharp-activity-binding-guide.md#c-expression-pitfalls)).

### Expected non-defect warnings

`build` `[WARN]` lines for enabled analyzer rules are not failures and do not gate delivery (§ Validation Iteration Loop, Rule 6). Do not “fix” these expected warnings:

| Warning | Rule | Why expected |
|---|---|---|
| `<activity> does not have the verification feature enabled` | — (matches no rule in enabled `analyzer-rules list`) | `VerifyOptions` deliberately defaults off; add only if user asks. Observed once per `NClick` on a clean UIA build. Policy: UIA package guide § Execution Verification Policy. |
| `Your organization requires your project to have an Automation Hub URL defined` | `ST-USG-034` | Organization governance setting, not workflow property; project owner resolves in Project Settings. |
| `<name> display name is defined many times. Current allowed threshold is 1` | `ST-NMG-004` | Real but cosmetic; fix only while authoring the activity. Repeated identical steps (for example, two clicks on same button) need distinct names. |

For an unknown rule ID, look it up with `analyzer-rules list --scope <scope>` (§ analyzer-rules list) rather than guessing, and only when the warning blocks an acceptance criterion.

## Smoke Test

Clean validate + build is not runtime proof: attribute-form expressions can silently become literals (§ What each phase covers), CacheMetadata failures appear only when runtime instantiates an activity, and logic bugs may remain. After zero validation errors and clean project build (Phase 2), run a workflow to detect runtime issues (credentials, missing files, logic). Always treat the smoke test as a critical validation step whose output is inspected, not just an optional extra. Use `--skip-build` after the clean build to avoid redundant ~10s compilation:

```bash
uip rpa run --file-path "<FILE>" --skip-build --output json
uip rpa run --file-path "<FILE>" --skip-build --input-arguments key=value --output json
uip rpa run --file-path "<FILE>" --skip-build --log-level Verbose --output json
```

`--skip-build` runs the existing compiled artifact, silently ignoring edits since the last successful build. Use bare `run` after edits.

**[Coded] Do not pair `build` with default `run`/`debug start`.** `build` deletes `.local/.codedworkflows/WorkflowRunnerService.cs`; a default `run`/`debug start` then re-validates the inconsistent generated set and fails `CS0246 'WorkflowRunnerService' does not exist in the namespace`. Choose `build` → `run`/`debug start --skip-build` (built artifact), or bare `run`/`debug start` (builds internally).

Run when: (1) compilation is clean and runtime behavior needs verification; (2) workflow has file I/O, API calls, or transformations; (3) user asks for a test. Do not run when: (1) side effects (email, database changes, external APIs) exist—warn user first; (2) interactive input is required (UI automation, attended triggers); (3) compilation errors remain.

For runtime errors, analyze output, apply the fix-one-thing rule, and retry. Stop after 2 failed runtime retry attempts; present error details, a suggested fix, and options:

```
Workflow execution failed after 2 retry attempts.

**Error Details:** <specific error message and location>
**Suggested Fix:** <analysis of what went wrong>
**Next Steps:** Would you like me to:
A) <recommended fix approach>
B) <alternative approach>
C) <user-driven approach>
```

---

## RPA-Specific Fix Procedures

### Resolving Dynamic Activity Custom Types

Dynamic activities (for example Integration Service connectors) retrieved through `uip rpa activities get-default-xaml` with `--activity-type-id` may use JIT-compiled custom input/output types. After adding the activity, read the schema to discover custom entity property names and CLR types (for Assign targets or custom-type variables):

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### Focus Activity for Debugging

When `validate` identifies an activity by IdRef or DisplayName, use `focus-activity` to highlight it in the Studio Desktop designer so the user can inspect context or verify a fix.

> **Studio Desktop required.** This manipulates the Desktop UI and does not run on Helm. Before invoking, ensure Desktop is up with `uip rpa studio start --project-dir "<PROJECT_DIR>"` (see [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop)). Skip on headless-only setups; `validate`'s IdRef and file:line locate the activity.

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1"
# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity
```

Use it when an error needs visual context, after a fix to show the modified activity, or to disambiguate an activity instance.

---

## Pack & Publish to Orchestrator

This covers standalone-project packaging/upload only. Solution publish (`.uipx` and `solution publish` deploy lifecycle) belongs to `uipath-solution`.

### Pick a path

| Goal | Path | Reference |
|---|---|---|
| Run as Orchestrator process / link as Test Manager automation | **Pack → Orchestrator package upload** | This section § Pack → Upload |
| Edit / visualize in Studio Web | **Solution upload** | `uipath-solution` skill (solution upload) |
| Deploy packed `.uipx` solution through Orchestrator lifecycle | **Solution publish** | `uipath-solution` skill (pack-and-deploy lifecycle) |

Only the first row is documented here: the legacy Orchestrator package feed flow required by `uip tm testcases link-automation`.

### Pack → Upload (Orchestrator process flow)

Two CLI calls:

#### Step 1 — Pack the project

```bash
uip rpa pack "<PROJECT_DIR>" "<OUTPUT_DIR>" --output json
```

`<PROJECT_DIR>` is positional 1 (folder containing `project.json`); `<OUTPUT_DIR>` is positional 2, must already exist and be outside the project tree (pack refuses paths inside it; use a sibling such as `dist/`). Optional flags (confirm full list with `uip rpa pack --help`): `--package-version <SEMVER>` (defaults to project version), `--skip-analyze` (only for known-clean builds), `--governance-file-path <PATH>` (governance policy). JSON `OutputPath` is the full `.nupkg` path; capture it for upload.

`uip rpa pack` accepts neither `--project-path` nor `--project-dir`; both arguments are positional.

#### Step 2 — Upload to Orchestrator

```bash
uip or packages upload "<NUPKG_PATH>" --output json
```

`<NUPKG_PATH>` is the required positional `.nupkg` from pack. Optional `--feed-id <UUID>` targets a non-default feed (default is tenant feed); `--folder-path <PATH>` / `--folder-key <UUID>` targets a folder feed. Output JSON gives package `Id` (Orchestrator package name) and `Version`: use `Id` as `uip tm testcases link-automation --package-name` or `uip or processes create --package-key` (pass `--package-version` separately).

There is no `uip or packages publish` or `uip rpa publish`: pack writes a file; upload pushes it. Use the `rpa` and `or` domains respectively.

### Discovery cheatsheet

Discover folder UUIDs (required by `processes create`, `link-automation`, etc.):

```bash
uip or folders list --output json
```

`Key` is UUID; `FullyQualifiedName` is the human path. Both work with `--folder-path` / `--folder-key`; most other CLI calls require UUID. List uploaded package versions with:

```bash
uip or packages list --output json
```

### End-to-end: link a coded test case to Test Manager

For Pack → Upload → Link → Execute targeted at Test Manager (folder-key discovery, choosing `--test-name`, etc.), delegate to `uipath-test` skill's publish-and-link guide.

### Common pitfalls

- `uip solution publish` requires a packed `.zip`, not a project directory. Run `uip solution pack` first, then `uip solution publish "<ZIP_PATH>"`; for single projects use `uip or packages upload`.
- `solution upload` edits in Studio Web; `solution publish` sends a packed solution `.zip` to Orchestrator's solution feed for `solution deploy`. They are not interchangeable; `uipath-solution` owns the decision tree.
- Orchestrator rejects duplicate `<id>:<version>` uploads. Bump `--package-version` or `project.json` `projectVersion` before repacking.
- A successful pack with errors in the analyzer log usually means warnings only. If a clean pass/fail signal is needed, run `uip rpa analyze "<PROJECT_DIR>"` (project dir positional).

---

## CLI Error Recovery

Identify the error category, apply recovery, and retry **once**; do not loop the same failing command.

| Error pattern | Cause | Recovery |
|---|---|---|
| `connection refused`, `EPIPE`, `pipe not found` | Studio IPC unavailable: Helm restore failed/process exited, or Desktop not running. | Rerun; Helm relaunches automatically. If persistent, raise `--timeout` and inspect Helm restore output for NuGet errors. Run `uip rpa studio start` only for Desktop-only verbs or `UIPATH_RPA_TOOL_USE_STUDIO=1`. |
| `timeout`, `ETIMEDOUT` | Cold Helm restore (30–90 s) or long operation. | Raise both limits: shell `timeoutSeconds` toward documented max and `uip rpa --timeout <timeoutSeconds − 30> <command>`. Shell timeout must exceed `--timeout` by ≥ 30 s so it does not kill CLI before clean cancellation. For `validate`, also try `--skip-validation`. |
| `not authenticated`, `401`, `403` | Cloud authentication required. | Run `uip login`, then retry. |
| `package not found`, `version not available` | Wrong package ID/version. | Verify with `uip rpa activities find`; omit version to resolve latest. |
| `project not found`, `no project open` | Wrong `--project-dir` or project not open. | Verify path is the `project.json` folder; if persistent run `uip rpa project open --project-dir "<PROJECT_DIR>"`. For Desktop-only verbs, check hidden `uip rpa instances list --output json`; run `uip rpa studio start` if none is up. |
| `not in the project folder` (`validate`) | Absolute `--file-path` separator mismatch. | Use project-relative `--file-path` (see [validate](#validate)). |
| `Studio is busy`, `operation in progress` | Studio handling prior request. | Wait a few seconds, retry. |
| Unrecognized | Unknown. | Rerun with `--verbose` for details, then inform the user. |

---

## RPA discovery tools (non-CLI)

| Action | How |
|---|---|
| Explore project files | `Glob` `**/*.xaml` |
| Search XAML | `Grep` regex across `.xaml` |
| Explore Object Repository | `uip rpa get-object-repository` for project apps/screens/elements; `uip rpa get-library-object-repository` for a referenced library (see [object-repository](#object-repository)); or `Glob` `**/*` under `{PROJECT_DIR}/.objects/` and `Read` metadata. |
| Get JIT type definitions | `Read` `{PROJECT_DIR}/.project/JitCustomTypesSchema.json` |
| Activity docs | See [Installed package activity documentation](#installed-package-activity-documentation). |
| Inspect NuGet package API | `uip rpa packages inspect`; see [coded/codedworkflow-reference.md § Inspect NuGet Package Tool](coded/codedworkflow-reference.md). |

---

## UI Automation (`uip rpa uia ...`)

`uip rpa uia --help` deliberately lists no standard subcommands: the UIA CLI is owned and co-versioned by `UiPath.UIAutomation.Activities`. Start at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` (Rule 7), whose CLI-discovery section routes to task guides and command inventory. Discover each command's flags with `<discovered command> --help`.