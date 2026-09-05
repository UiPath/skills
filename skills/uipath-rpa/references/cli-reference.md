# UiPath CLI (`uip`) Reference

`uip rpa` and sibling tools (`uip is`, `uip tm`, …) talk to UiPath Studio over named pipes (IPC). This file teaches **how to discover** commands, arguments, and flags — plus the non-obvious behaviors that `--help` won't tell you (auth, headless vs Desktop Studio, how to read run results, error recovery).

> **Do not treat any command/flag list here as exhaustive or current.** The CLI is the source of truth and it drifts. Discover the live surface with `--help` (below); this file carries only the HOW that `--help` omits.

> **Installation is automatic.** Do NOT install `uip` manually or instruct the user to install it.

---

## Discover the live CLI with `--help`

The CLI is self-documenting. Append `--help` at **any** level to drill from tools → groups → verbs → parameters. Each level lists the next.

```bash
uip --help                    # top-level commands + installed tools (rpa, is, tm, ...)
uip tools list                # installed tools, machine-readable
uip rpa --help                # all rpa command groups and verbs
uip rpa packages --help       # verbs inside a group
uip rpa validate --help       # parameters, accepted values, defaults for one verb
uip is --help                 # Integration Service surface
uip skills --help             # skill install/search/update
```

The same pattern works for every tool and depth (`uip rpa uia <verb> --help`, `uip login --help`, etc.). When unsure whether a verb, flag, or accepted value exists, **run `--help` rather than guessing** — guessed flags fail with `unknown command`/`unknown option`.

> **Run `--help` standalone — never combine it with other flags.** `uip rpa <verb> --help --project-dir "<path>"` parses `--project-dir`'s value as a positional command and exits with `unknown command '<value>'`. Drop every other flag when probing help.

> A verb may be **hidden from `--help`** yet still callable by exact name (e.g. diagnostic or UI-cue verbs). Absence from `--help` means "not part of the standard loop," not "does not exist."

---

## Output format

`--output` defaults to **`json`**. Accepted: `json`, `table`, `yaml`, `plain`. Keep `json` for anything parsed programmatically — `table` pads columns and can balloon to 100 KB+.

`--output-filter "<JMESPath>"` applies a JMESPath expression to the response envelope's `Data` field — use it to slice large responses instead of post-processing in the shell.

`--log-level <debug|info|warn|error>` and `--log-file <path>` are global. Raise log level or add `--verbose` when diagnosing a failure.

Most response envelopes share the shape `{Result: "Success"|"Failure", Code, Data, Message?, Instructions?}`. Branch on `Result`, not on stdout text.

---

## Authentication

Cloud features (templates/packages from feeds, Integration Service, Data Service entities, publishing) need a logged-in session.

```bash
uip login              # interactive browser login to UiPath Cloud
uip login status       # current session: org, tenant, expiry
uip login which        # which auth source uip resolves for this cwd
```

If a command fails with `not authenticated` / `401` / `403`, run `uip login` and retry. Discover non-interactive/CI login options (credentials folder, client id/secret, authority) via `uip login --help`.

---

## Project context: `--project-dir`

Most `uip rpa` verbs identify the project via `--project-dir`, defaulting to the current working directory. When the project is elsewhere, pass the absolute path to the folder containing `project.json`. A few verbs deviate (e.g. `init` takes `--name` + `--location`; `build`/`pack` take the project dir as a positional) — confirm with that verb's `--help`.

To create a project, see [environment-setup.md](environment-setup.md); `--target-framework` and `--expression-language` are immutable after creation, so decide them per SKILL.md before running `init`.

---

## Headless Studio (Helm) vs Studio Desktop

`uip rpa` connects to one of two Studio flavors behind the same IPC contract:

- **Headless Studio (Helm) — default.** Ships as a NuGet package and auto-launches on first use. **No Studio Desktop install needed.** First call on a cold NuGet cache may sit near-silent for 30–90 s while `dotnet restore` runs — the default shell timeout covers this; raise `timeoutSeconds` only behind a slow feed.
- **Studio Desktop.** The interactive UI. Used automatically only by verbs with **UI side effects** — those that open a window or highlight something in the designer (discover them via `--help`; they don't work headless). For such a verb, ensure Desktop is up first (`uip rpa studio start --project-dir "<PROJECT_DIR>"`), then run it. Force Desktop for any command with `UIPATH_RPA_TOOL_USE_STUDIO=1` (not recommended for the standard authoring loop).

`--studio-dir` is consulted **only when Studio Desktop is in use**; headless ignores it. When Desktop auto-detection fails, resolution falls back to `UIPATH_STUDIO_DIR`, then the default install path, then a dev build output. Errors like `"does not have interop support"` / `"Requires Studio 26.2+"` mean the detected Desktop is too old — tell the user to update it; this affects only the Desktop-only verbs.

---

## Installed package activity documentation

When a package is installed, its activity docs land under `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`. Read these directly — they carry the per-activity property surface and coded API signatures that no `--help` exposes.

| Action | How |
|--------|-----|
| **Read an activity doc** | `Read` `…/{PackageId}/activities/{ActivityName}.md` — preferred when you know package + class |
| **Read coded API doc** | `Read` `…/{PackageId}/coded/coded-api.md` — service API signatures for coded workflows |
| **Read package overview** | `Read` `…/{PackageId}/overview.md` |
| **List documented packages / activities** | `Bash`: `ls …/.local/docs/packages/` then `ls …/{PackageId}/activities/` |
| **Search activity docs** | `ls` the exact package directory via Bash (`…/.local/docs/packages/<PackageId>/activities/`), then `Read` the matching file by path. **NOT `Glob` or `Grep`** — both skip gitignored `.local/`; a miss from either proves nothing. |

---

## Reading run / debug results

`uip rpa run` runs a workflow with no debugging; the `debug` group drives breakpoints, stepping, and exception handling (see [debugging.md](debugging.md)). For UI automation, prefer `debug start` over `run` so the app is preserved for selector repair on error. Cancel an active run or session with `uip rpa execution cancel`. Pass workflow inputs as repeatable `--input-arguments key=value` pairs (see [Passing structured inputs](#passing-structured-inputs)); discover the remaining flags (log level, skip-build, profiling) via `--help`.

Both wrap the result in `{Result, Code, Data}`. `Data` is `{output, hasErrors, errorMessage, profiling, debugState, debugDetails}`: `output` is the workflow's serialized output arguments (`"{}"` when it declares none), and the workflow's own `Log Message` lines stream to stdout as `[Information] …` lines **above** the JSON envelope — they are not inside `Data`. Field-by-field meaning: [debugging.md § Output Format](debugging.md#output-format).

> **A run passed only when `Data.hasErrors` is `false` AND `Data.errorMessage` is `null` AND `Data.debugState` is `null` or `"Completed"`.** A `run` that faulted, failed validation, or named a missing entry point returns outer `Result: "Failure"` with the same field set JSON-encoded in `Message` (`hasErrors: true`, `errorMessage` = the failure text). A faulted `debug start` returns `Result: "Success"` with `hasErrors: false`, `debugState: "Suspended"`, the exception in `debugDetails` and command guidance in `errorMessage` — the session is still alive; cancel or continue it. **Never read the outer `Result: "Success"` as a passing run, and never infer failure from a `[Warning]` / `[Error]` log line** — `Log Message` activities emit at any level, and treating log levels as a verdict flips green runs to "failed" and burns retries.

### Capturing the verdict

**Always pass `--output-filter` on `run` / `debug start`, and always this filter.** It selects the five verdict fields and drops `profiling`. **Never write a filter that calls `length()`, `keys()`, or any function on a key that is not in `Data`** (`length(errors)`, `keys(Data)`): the CLI rejects the whole call with `Filter '…' failed to evaluate: Invalid type … received type null` *after* the workflow has already run, so the retry re-drives the application and costs a turn.

```bash
uip rpa run --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --skip-build --output json \
  --output-filter "{output: output, hasErrors: hasErrors, errorMessage: errorMessage, debugState: debugState, debugDetails: debugDetails}"
```

```text
[Information] Starting execution...
[Information] SumDemo execution started
[Information] 5 + 5 = 10
[Information] SumDemo execution ended in: 00:00:00
{ "Result": "Success", "Code": "ToolResult", "Data": {
    "output": "{}", "hasErrors": false, "errorMessage": null, "debugState": null, "debugDetails": null } }
```

Adjudicate off `hasErrors`, `errorMessage` and `debugState` per the rule above. The workflow's logged values are the `[Information]` lines above the envelope — read them there; do not strip them (`grep -v '^\['`) and do not look for them inside `Data`. The same filter on `debug start` returns `debugState` / `debugDetails` for the suspended-state exception that selector recovery needs.

**Never `| tail -N` or `| head -N` the payload.** The log lines precede the envelope, so either cut drops one of the two things you need, and recovering it means re-running — which re-drives the application; a workflow that is not re-run-safe behaves differently the second time. The filter already keeps the response to a dozen lines. On a `Result: "Failure"` envelope the filter has nothing to apply to (there is no `Data`): read `Message`, the same fields JSON-encoded.

When a failure needs more than the envelope shows (compile-phase error, a stack older than the visible lines), redirect the whole stdout — `> run.log` — and read the `[Error]` lines plus the envelope's `errorMessage` from the file. `jq` is absent on a standard Windows agent host; the envelope is the last JSON object in the file.
---

## Passing structured inputs

`--input-arguments` and `--input-variables` may be supplied as repeatable `key=value` pairs (`key:=value` for raw JSON, `key=@file` to read a value from a file), as an inline JSON string, or from a JSON file using `'@file'` or `--<flag>-file`. `--packages` takes one item per occurrence as comma-joined fields.

```bash
uip rpa run --file-path Main.xaml --input-arguments name=John --input-arguments retries:=3
uip rpa run --file-path Main.xaml --input-arguments 'message=Hello, world!'
uip rpa debug test-activity --input-variables greeting=@expression.txt
uip rpa run --file-path Main.xaml --input-arguments '@args.json'      # or: --input-arguments-file args.json
uip rpa packages install --packages 'id=UiPath.System.Activities,version=23.10.1' --packages id=UiPath.Excel.Activities
```

Rules:

- **`=` vs `:=`**: `count=42` sends the string `"42"`; `count:=42` sends the number `42`. For `debug test-activity` / `debug start-from-here`, values are VB/C# expression **strings** — always `=`.
- **Quoting**: single-quote any token containing spaces, commas, or a leading `@`; bare identifiers and numbers need no quotes. Values containing double quotes cannot be passed inline on Windows PowerShell 5.1 (it strips them) — write them to a UTF-8 file (`Set-Content -Encoding UTF8`) and use `key=@file`, `'@file'`, or `--<flag>-file`.
- **Inline JSON**: a single JSON blob (`--input-arguments '{"k":"v"}'`) remains accepted for backward compatibility, but is unreliable on PowerShell 5.1 — prefer pairs or files.
- **Empty value ≠ default**: `--input-arguments key=` passes an empty string, which OVERRIDES a coded workflow's declared default parameter value. Omit the flag entirely to use the default.

---

## validate

`uip rpa validate` returns diagnostics for a file or the whole project, re-validating first by default (`--skip-validation` reads cached, possibly stale, results; `--min-severity` filters). Confirm flags via `uip rpa validate --help`.

`--file-path` accepts a path relative to the project directory (`--file-path "Main.xaml"`) or an absolute one, with either separator style; forward-slash, backslash, and mixed forms all resolve. Prefer the relative form — it is shorter and keeps commands portable across machines.

---

## build

`uip rpa build` compiles the whole project — every workflow, not only the files a per-file `validate` was pointed at (§ What each phase covers). Required before returning a project to the user (see [§ Project Build Verification](#project-build-verification-required-before-returning-a-project)). Takes the project directory as a **positional** argument and runs independently of Studio IPC. Discover flags (log level, skip-analyze, governance, NuGet sources) via `uip rpa build --help`.

`run` and `debug start` compile internally, so a successful smoke test implies `build` would pass. When no smoke test runs (side effects, interactive workflow, no test input), `build` is the required compilability check.

---

## analyzer-rules list

`uip rpa analyzer-rules list` reports the Workflow Analyzer rules **enabled** for the project — the best-practice rules `validate` and `build` enforce. Reports rules, not violations. Do NOT run it as an authoring prerequisite — `validate`/`build` already enforce the rules and report violations with rule IDs and recommendations. Run it **only on demand**: (1) the user asks about the project's best-practice / analyzer rules, or (2) repeated violations of the same rule family across `validate`/`build` iterations suggest authoring against the full rule set. Each rule returns `severity` (`error`/`warning`/`info`), rule ID, scope, title, and (when available) `recommendation` and `docs` URL. Prefix convention: `ST-*` = built-in Studio rule, `MA-*` = package-shipped rule.

Rules with scope `Coded Workflow` run as Roslyn analyzers over the project's `.cs` files during `analyze`, `build`, and `pack` — same enforcement as the XAML-scoped rules. The four built-in ones are all Error severity; triggers and fixes: [coded/operations-guide.md § Coded Workflow Analyzer Rules](coded/operations-guide.md#coded-workflow-analyzer-rules).

> **Performance:** the unscoped call enumerates every rule across every package and can take a minute or more. Narrow with `--scope` (`Activity`, `Workflow`, `Project`, or `Coded Workflow`) — scoped calls return in seconds. See `--help` for accepted scope values.

---

## packages install

`uip rpa packages install` installs or updates NuGet packages (canonical way to add dependencies — **do not hand-edit `project.json`**; there is no `add-dependency` verb). Repeat `--packages` once per package with comma-joined `key=value` fields — `--packages 'id=<PackageId>,version=<Version>'` or just `--packages id=<PackageId>` (see [Passing structured inputs](#passing-structured-inputs)); discover the remaining flags via `uip rpa packages install --help`.

- **Omit the version** to resolve the latest compatible automatically (preferred). Pin only for a known compatibility constraint.
- **Discover available versions** with `uip rpa packages versions --package-id <Id> --include-prerelease`. **Default to `--include-prerelease`** — activity packages frequently ship `-preview` between stable releases, carrying the freshest activity surface and `.local/docs`. When a newer stable or preview exists over the installed version, inform the user and offer the upgrade — never force.
- **Package not found** → verify the exact ID (use `activities find` or the package's `.local/docs`). **Feed/network error** → check NuGet feed config in Studio settings.

---

## object-repository

Read the project's UI **Object Repository** — the saved hierarchy of applications, screens, and elements (selectors/targets) that UI Automation activities bind to. Two read commands cover the project's own entries and those exposed by referenced libraries; both require an open project.

> **Both verbs are top-level and hyphenated.** There is no `uip rpa object-repository` group — it returns `Unknown command: object-repository`, Studio running or not. Distinct from the UIA OR CLI, which writes entries and has no `get`.

- **Project Object Repository** — `uip rpa get-object-repository` returns the project's *own* Object Repository as a JSON tree of applications → screens → elements, each entry carrying `name`, `description`, `type`, and `reference`. Entries inherited from referenced libraries are **excluded** (use the library command below for those). Takes no arguments beyond the standard `--project-dir`.

  ```bash
  uip rpa get-object-repository --project-dir "<PROJECT_DIR>" --output json
  ```

  The `name` values are **Object Repository names, not C# members** — `Result Display` here is `Result_Display` in `Descriptors.*`. Convert per the coded authoring guide's § Descriptor Naming, routed from `ui-automation-guide.md` § Documentation.

- **Library Object Repository** — `uip rpa get-library-object-repository` reads the Object Repository out of one or more library `.nupkg` files and returns the applications, screens, and elements grouped by library. Pass the absolute path(s) to the library packages; packages without an Object Repository are omitted from the result.

  | Parameter | Required | Description |
  |-----------|----------|-------------|
  | `--library-paths` | yes | Absolute path(s) to the library `.nupkg` file(s) to read. Pass a single flag with the paths **comma-separated** (e.g. `"a.nupkg,b.nupkg"`) — it is not a repeatable flag. Avoid paths containing commas. |

  ```bash
  # multiple libraries: one --library-paths flag, comma-separated
  uip rpa get-library-object-repository \
    --project-dir "<PROJECT_DIR>" \
    --library-paths "C:\libs\Acme.UiLib.1.2.0.nupkg,C:\libs\Other.UiLib.2.0.0.nupkg" \
    --output json
  ```

Read the project repository before authoring UI Automation activities to discover existing screens/elements to reuse instead of re-indicating them; read the library repository to discover targets a referenced UI library already exposes. Confirm the live flags with `uip rpa get-object-repository --help` / `uip rpa get-library-object-repository --help`.

---

## Commands -- Data Fabric Entities

UiPath Data Fabric entities live in the Orchestrator tenant's Data Service. To use them in an RPA project — as typed arguments (`UiPath.DataService.Activities`, test-data bindings) or any generated entity type — they must first be **installed** into the project, which writes a manifest under `.entities/` and compiles a strongly-typed assembly.

Typical flow, all under `uip rpa data-fabric-entities` (discover exact flags via `--help`):

1. **List** — returns a unified view of entities installed in the project **and** available in the connected tenant, each with an `installed` flag. Run before installing to pick names or verify bindings.
2. **Install** — applies an add/remove delta to the installed set. Dependency expansion is automatic (adding an entity pulls in everything it references); server-deleted entities are silently dropped. Final selection = `(installed ∪ add) − remove`; an empty result uninstalls everything for that manifest.

**Install entities before** invoking any workflow or test case that references their generated types, and before any test-data command that binds to an entity.

---

## Integration Service (`uip is`)

`uip is` manages connectors, connections, resources, triggers, and webhooks. Discover the full surface via `uip is --help`, then drill in (`uip is connections --help`, `uip is resources describe --help`, …). All verbs support `--output json`.

The verbs you'll reach for: list/describe **connectors** and their **activities**/**resources**, list/create/ping/edit **connections** (OAuth opens a browser; `--no-browser` prints the URL), and run CRUD **resource** operations. For RPA-specific connector workflow patterns (activity/resource discovery, connection management, schema inspection), see [is-connector-xaml-guide.md](is-connector-xaml-guide.md).

---

## Test Manager

Two distinct surfaces — pick by intent:

- **`uip tm` (dedicated tool)** — *runtime* Test Manager operations: browsing manual test cases, runs, results. `uip tm --help`. Do **not** invoke these runtime verbs from `uip rpa`.
- **`uip rpa tm` (project configuration)** — *authoring/setup*: wire an RPA project to Test Manager by editing its `.tmh/config.json`. Pure file I/O — no Studio or Helm process is needed, so it works with everything closed.

### `uip rpa tm` verbs

| Verb | Purpose |
|---|---|
| `uip rpa tm connect --url <url>` | Set the Test Manager **server URL** (`testManagerBasePath`). Switching to a **different** server (different host/org/tenant) also **clears the default project**, since it belonged to the old server. |
| `uip rpa tm set-default-project --id <guid> [--name <name>] [--key <key>]` | Link the **default Test Manager project** (`defaultProject`). **Requires a connected server** — run `connect` first or it is rejected. |
| `uip rpa tm clear-default-project` | Unlink the default project; the server URL is kept. |
| `uip rpa tm status` | Show the current configuration — server URL and linked default project. |

Typical setup flow (all verbs take the standard `--project-dir` and `--output json`):

```
uip rpa tm connect --url "https://cloud.uipath.com/<org>/<tenant>/testmanager_" --project-dir "<PROJECT_DIR>" --output json
uip rpa tm set-default-project --id <project-guid> --name "<project-name>" --key "<KEY>" --project-dir "<PROJECT_DIR>" --output json
uip rpa tm status --project-dir "<PROJECT_DIR>" --output json
```

`set-default-project` does **not** call the server to validate the id (there is no server round-trip) — pass a real Test Manager project id (and optional name/key). Listing projects from the server is not available here; obtain the id from Test Manager itself. Confirm exact flags via `uip rpa tm --help`.

#### Acting on `reloadHint` in the output

A `connect` / `set-default-project` / `clear-default-project` response may include a **`reloadHint`** field. It appears only when the project is currently **open in a Studio older than 26.0.197**, which reads `.tmh/config.json` *only on project open*. When you see it, tell the user to **close and reopen the project in Studio** for the change to take effect — the CLI cannot do this for them. No `reloadHint` means nothing to do: either the project isn't open in Studio, or it's open in Studio 26.0.197+, which applies the change live.

---

## Fix One Thing at a Time

When an error occurs, identify the root cause, fix **only** that one thing, and re-run.

- Never bundle a speculative improvement with the actual fix.
- Changing two things at once makes it impossible to verify which change resolved the issue or whether the extra change introduced a new one.
- One fix per iteration, re-run, verify.

## Validation Iteration Loop

Phase 1 — per-file `validate` after every edit. Phase 2 — one project-level `build` per edit session.

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
       a. uip rpa validate --file-path "<OFFENDER>" --project-dir "<PROJECT_DIR>" --output json   # cheap targeted re-check
       b. fix one root cause, GOTO 1
    3. EXIT to Smoke Test
```

**Why both phases.** Per-file `validate` covers one file deeply — structural XAML, missing references, analyzer rules, schema violations, unknown members, invalid enums, and expression compilation. `build` covers the project broadly — every workflow including untouched ones, project-scope analyzer rules, and packaging. Validating each edited file does not establish that the project compiles, and building does not tell you which file to fix without re-running `validate` on the offender. Neither replaces the other, and neither detects an attribute-form expression that silently resolves to a literal (§ What each phase covers).

**Target the specific file:** `validate --file-path` validates only the file you changed (faster than whole-project). `build` is project-scoped (no `--file-path`); when it errors, the output names the offending file — re-run `validate --file-path` on it as part of Phase 2's fix loop.

**5-attempt cap per loop** — 5 attempts for each file's Phase 1 `validate` loop; a separate 5 attempts for the Phase 2 `build` loop. After a loop exhausts its budget, present the remaining errors to the user. They may require domain knowledge or environment-specific fixes. Each loop's counter resets when you start a new loop (e.g., new file, new user prompt, or resuming after user input).

### Rules

1. DO NOT stop until all errors are resolved (or cannot be resolved automatically).
2. DO NOT obsess on one error -- if it cannot be resolved, skip it, continue, and defer to the user through an informative, step-by-step message at the end.
3. DO NOT skip validation steps.
4. DO NOT assume edits worked without checking.
5. DO NOT bundle multiple fixes in one iteration. Fix the root cause, re-run, verify. Never add a speculative change alongside the actual fix -- changing two things at once makes it impossible to tell which one resolved the issue or whether the extra change introduced a new problem.
6. Warnings are non-blocking. Once `validate`/`build` (and, where the task requires, `pack`/`run`) are clean of errors, deliver — do not investigate warnings unless the user asked or one blocks an acceptance criterion.

Full `validate` and `run` command documentation: [§ validate](#validate) and [§ Reading run / debug results](#reading-run--debug-results).

## Project Build Verification (Required Before Returning a Project)

Every project returned to the user must compile. Phase 2 of the iteration loop above is this gate — when Phase 2 exits clean, the gate is satisfied. The standalone command below also satisfies it (for example, when re-verifying after a small fix outside an iteration loop):

```bash
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

If `build` fails, apply the Phase 2 fix loop (fix one root cause, re-run, cap at 5 attempts). A successful `run` smoke test substitutes for `build` — `run` compiles internally.

### What each phase covers

Per-file `validate` loads the target file through the workflow designer **and** compiles its expressions, so it reports these on the file it was pointed at:

| Error class | Example | Reported as |
|-------------|---------|-------------|
| Unknown member name | `<uix:NGetText Value="[x]" />` (correct: `TextString`) | `Could not load <file>: 'Cannot set unknown member '<Class>.<Prop>''` |
| Invalid enum value | `ClickType="BogusValue"` | `Could not load <file>: 'Failed to create a '<Prop>' from the text '<value>''` |
| Broken expression | `undefinedSymbol + 1` inside a `CSharpValue` | `CS0103: The name '<symbol>' does not exist in the current context` |

**`build` is still required, because its scope is the whole project, not the file you validated.** It compiles every workflow — including ones you never touched or never validated — and applies project-scope analyzer rules and packaging. A project whose every edited file validates clean still fails `build` when an unrelated file is broken, which is exactly the state a partial edit session leaves behind.

**Neither phase catches an attribute-form expression on an `InArgument<Object>`.** `Message="calcResult"` deserializes as a literal string, so `validate` reports no diagnostics, `build` succeeds, the run succeeds — and the activity logs the text `calcResult` instead of the variable's value. There is no error anywhere; the only signal is wrong output. This is why the gate ends with a smoke test whose **output is inspected**, not merely a run that exits clean — see [§ Smoke Test](#smoke-test) and [xaml/csharp-activity-binding-guide.md § C# Expression Pitfalls](xaml/csharp-activity-binding-guide.md#c-expression-pitfalls).

### Expected non-defect warnings

`build` prints `[WARN]` lines for enabled analyzer rules. These are **not** build failures and do not gate delivery (§ Validation Iteration Loop, Rule 6). Recurring ones that are correct-by-design and must not be "fixed":

| Warning | Rule | Why it is expected |
|---|---|---|
| `<activity> does not have the verification feature enabled` | — (matches no rule in the enabled `analyzer-rules list` output) | `VerifyOptions` is deliberately off by default; add only when the user asks. Observed once per `NClick` on a clean UIA build. Policy: the UIA package guide's § Execution Verification Policy. |
| `Your organization requires your project to have an Automation Hub URL defined` | `ST-USG-034` | Org governance setting, not a workflow property. Resolved in Project Settings by the project owner. |
| `<name> display name is defined many times. Current allowed threshold is 1` | `ST-NMG-004` | Real but cosmetic. Fix only while authoring the activity — repeated identical steps (two clicks on the same button) need disambiguating names anyway. |

Warnings naming a rule ID you do not recognize: look it up with `analyzer-rules list --scope <scope>` (§ analyzer-rules list) rather than guessing, and only when a warning actually blocks an acceptance criterion.

## Smoke Test

A clean `validate` + `build` gate is not runtime proof. Some defects produce no diagnostic in either phase — an attribute-form expression that silently became a literal (§ What each phase covers), activity CacheMetadata failures that surface only when the runtime instantiates the activity, and plain logic bugs. Always treat the smoke test as a critical validation step whose output is inspected, not just an optional extra.

After reaching 0 validation errors AND a clean project-level build (Phase 2), run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect. Use `--skip-build` because the project has just been built clean — default `run` re-validates and re-builds internally, repeating ~10s of compilation:

```bash
# Run with default arguments (post-build, skip the redundant rebuild):
uip rpa run --file-path "<FILE>" --skip-build --output json
# Run with input arguments (repeat --input-arguments per key; = string, := raw JSON):
uip rpa run --file-path "<FILE>" --skip-build --input-arguments key=value --output json
# Run with verbose logging for debugging:
uip rpa run --file-path "<FILE>" --skip-build --log-level Verbose --output json
```

`--skip-build` executes the existing compiled artifact — any edit since the last successful `build` is silently ignored. Use bare `run` after edits.

**When to run:**
1. Workflow has no compilation errors but you want to verify runtime behavior
2. Workflow involves file I/O, API calls, or data transformations that could fail at runtime
3. User specifically asks to test the workflow

**When NOT to run:**
1. Workflow has side effects (sends emails, modifies databases, calls external APIs) -- warn the user first
2. Workflow requires interactive input (UI automation, attended triggers)
3. Compilation errors still exist (fix those first)

**If runtime errors occur:** Analyze the output, apply the fix-one-thing rule, and loop back to fix. Stop after 2 failed runtime retry attempts and present the user with error details, a suggested fix, and options:

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

Dynamic activities (e.g., Integration Service connectors) retrieved via `uip rpa activities get-default-xaml` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### Focus Activity for Debugging

When `validate` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio Desktop designer. This helps the user see the problematic activity in context and verify fixes visually.

> **Studio Desktop required.** `focus-activity` does not run against headless Studio — it manipulates the Studio Desktop designer UI. Before invoking it, ensure Studio Desktop is up via `uip rpa studio start --project-dir "<PROJECT_DIR>"` (see [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop)). Skip this step entirely on headless-only setups — `validate` already includes the IdRef and file:line in its output, which is enough to locate the activity.

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1"
# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity
```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected

---

## Pack & Publish to Orchestrator

How to take a built `.nupkg` from `uip rpa pack` and get it onto Orchestrator or Studio Web. Covers the standalone-project paths only — solution publish (`.uipx` solutions and `solution publish` deploy lifecycle) lives in the `uipath-solution` skill.

### Pick a path

| Goal | Path | Reference |
|---|---|---|
| Run the project as an Orchestrator process / link as a Test Manager automation | **Pack → Orchestrator package upload** | This section § Pack → Upload |
| Edit / visualize in Studio Web | **Solution upload** | the `uipath-solution` skill (solution upload) |
| Deploy a packed solution (`.uipx`) to Orchestrator with the deployment lifecycle | **Solution publish** | the `uipath-solution` skill (pack-and-deploy lifecycle) |

This section documents the first row only — the legacy Orchestrator package feed flow that `uip tm testcases link-automation` requires.

### Pack → Upload (Orchestrator process flow)

The end-to-end is two CLI calls.

#### Step 1 — Pack the project

```bash
uip rpa pack "<PROJECT_DIR>" "<OUTPUT_DIR>" --output json
```

| Argument | Position | Notes |
|---|---|---|
| `<PROJECT_DIR>` | Positional 1 | Path to the project (folder containing `project.json`). |
| `<OUTPUT_DIR>` | Positional 2 | Directory the `.nupkg` is written to. Must exist and be OUTSIDE the project directory tree — `pack` refuses an output path inside the project. Use a sibling directory (e.g. `dist/`). |

Common optional flags (run `uip rpa pack --help` for the full set):
- `--package-version <SEMVER>` — pin the version. Defaults to the project version.
- `--skip-analyze` — skip the workflow-analyzer pass. Use only for known-clean builds.
- `--governance-file-path <PATH>` — apply a governance policy during pack.

Output (JSON) emits `OutputPath` — the full `.nupkg` path. Capture it for Step 2.

> **`uip rpa pack` does NOT accept `--project-path` or `--project-dir`.** Both arguments are positional. The `--project-dir` flag exists on most other `uip rpa` subcommands but not here.

#### Step 2 — Upload to Orchestrator

```bash
uip or packages upload "<NUPKG_PATH>" --output json
```

| Argument / Flag | Required | Notes |
|---|---|---|
| `<NUPKG_PATH>` | Yes (positional) | Path to the `.nupkg` produced by `pack`. |
| `--feed-id <UUID>` | No | Target a non-default feed. Defaults to the tenant feed. |
| `--folder-path <PATH>` / `--folder-key <UUID>` | No | Target a specific folder feed. |

Output JSON includes the package `Id` (the package name Orchestrator stores) and `Version`. Hold on to the `Id` — `uip tm testcases link-automation` takes it as `--package-name`; `uip or processes create` takes it as `--package-key` (with `--package-version` separately).

> **There is no `uip or packages publish` or `uip rpa publish`.** Agents that try those names get "unknown command". Pack writes a file; upload pushes that file. Two commands, two domains (`rpa`, `or`).

### Discovery cheatsheet

Folder key (UUID — required by `processes create`, `link-automation`, etc.):

```bash
uip or folders list --output json
```

The returned `Key` is the UUID; the `FullyQualifiedName` is the human path. Either is accepted by `--folder-path` / `--folder-key` — most other CLI calls require the UUID.

After upload, list the new package version:

```bash
uip or packages list --output json
```

### End-to-end: link a coded test case to Test Manager

For the full Pack → Upload → Link → Execute pipeline targeted at Test Manager (folder-key discovery, picking the right `--test-name`, etc.), delegate to the `uipath-test` skill (its publish-and-link guide).

### Common pitfalls

- **`uip solution publish` expects a packed `.zip`, not a project directory.** Solutions: run `uip solution pack` first, then `uip solution publish "<ZIP_PATH>"`. Single projects: use `uip or packages upload` instead.
- **Confusing `solution upload` and `solution publish`.** `upload` pushes to Studio Web (browser editing). `publish` pushes a packed solution `.zip` to the Orchestrator solution feed for `solution deploy`. They are NOT interchangeable. The `uipath-solution` skill owns the decision tree.
- **Re-uploading the same version.** Orchestrator rejects duplicate `<id>:<version>` uploads. Bump `--package-version` (or `project.json` `projectVersion`) before re-packing.
- **`pack` succeeds but `analyze` ran with errors.** A successful pack with errors in the analyzer log usually means warnings only. Re-run `uip rpa analyze "<PROJECT_DIR>"` (project dir is positional) if you need a clean failure / pass signal.

---

## CLI Error Recovery

Diagnose by error category, apply the recovery, retry **once** — do not loop the same failing command.

| Error pattern | Cause | Recovery |
|---------------|-------|----------|
| `connection refused`, `EPIPE`, `pipe not found` | Studio IPC unavailable. Headless: NuGet restore failed or process exited. Desktop: not running. | Re-run — headless relaunches automatically. If persistent, raise `--timeout` and check Helm restore output for NuGet errors. Run `uip rpa studio start` only for Desktop-only verbs or when `UIPATH_RPA_TOOL_USE_STUDIO=1`. |
| `timeout`, `ETIMEDOUT` | Cold Helm NuGet restore (30–90 s) or long operation. | Raise both limits together: shell `timeoutSeconds` toward its documented max, and `uip rpa --timeout <timeoutSeconds − 30> <command>` — the shell timeout must exceed `--timeout` by ≥ 30 s or the shell kills the CLI before it can cancel cleanly. For `validate`, also try `--skip-validation`. |
| `not authenticated`, `401`, `403` | Auth required for cloud features. | `uip login`, then retry. |
| `package not found`, `version not available` | Wrong package ID or version. | Verify via `uip rpa activities find`; omit `version` to auto-resolve latest. |
| `project not found`, `no project open` | Wrong `--project-dir` or project not open. | Verify the path points at the `project.json` folder; if it persists, `uip rpa project open --project-dir "<PROJECT_DIR>"`. For Desktop-only verbs, check instances with the hidden `uip rpa instances list --output json` and run `uip rpa studio start` if none is up. |
| `not in the project folder` (in `validate`) | Absolute `--file-path` + separator mismatch. | Pass `--file-path` relative to the project root (see [validate](#validate)). |
| `Studio is busy`, `operation in progress` | Studio processing a prior request. | Wait a few seconds, retry. |
| Unrecognized error | Unknown | Re-run with `--verbose` for debug detail, then inform the user. |

---

## RPA discovery tools (non-CLI)

| Action | How |
|--------|-----|
| **Explore project files** | `Glob` `**/*.xaml` |
| **Search XAML content** | `Grep` regex across `.xaml` |
| **Explore Object Repository** | `uip rpa get-object-repository` for the project's apps/screens/elements as JSON, `uip rpa get-library-object-repository` for a referenced library's (see [object-repository](#object-repository)); or `Glob` `**/*` under `{PROJECT_DIR}/.objects/` + `Read` metadata for raw files |
| **Get JIT type definitions** | `Read` `{PROJECT_DIR}/.project/JitCustomTypesSchema.json` |
| **Activity docs** | See [Installed package activity documentation](#installed-package-activity-documentation) above |
| **Inspect a NuGet package's API** | `uip rpa packages inspect` — see [coded/codedworkflow-reference.md § Inspect NuGet Package Tool](coded/codedworkflow-reference.md) |

---

## UI Automation (`uip rpa uia ...`)

`uip rpa uia --help` deliberately exposes no standard subcommands — the UIA CLI surface is owned and co-versioned by the `UiPath.UIAutomation.Activities` package. Start from `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` (Rule 7): its CLI-discovery section routes to the package's task guides and command inventory. Per-command flags: `<discovered command> --help`.
