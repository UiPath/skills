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

- **Headless Studio (Helm) — default.** Ships as a NuGet package and auto-launches on first use. **No Studio Desktop install needed.** First call on a cold NuGet cache may sit near-silent for 30–90 s while `dotnet restore` runs — raise `--timeout` to ≥ 180 for that call.
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
| **Search activity docs** | `Glob` `**/*.md` under `…/.local/docs/packages/`, then `Read` matches. **Not `Grep`** — `.local/` is gitignored and `Grep` skips it. |

---

## Reading run / debug results

`uip rpa run` runs a workflow with no debugging; the `debug` group drives breakpoints, stepping, and exception handling (see [debugging.md](debugging.md)). For UI automation, prefer `debug start` over `run` so the app is preserved for selector repair on error. Cancel an active run or session with `uip rpa execution cancel`. Pass workflow inputs as repeatable `--input-arguments key=value` pairs (see [Passing structured inputs](#passing-structured-inputs)); discover the remaining flags (log level, skip-build, profiling) via `--help`.

Both `run` and `debug start` return the same envelope: `{Result, Code, Data: {runResult: "<json-string>"}, ...}`. `Data.runResult` is a **JSON string** — parse it separately. It has three fields (plus optional `Profiling`):

- `Output` — the workflow's own serialized output arguments JSON (`""` for non-`Start*` commands). **Carries the workflow's data, not a verdict.**
- `HasErrors` — `true` iff execution did not complete successfully (compile/validation failure, unhandled exception, cancellation, or timeout); `false` otherwise.
- `ErrorMessage` — formatted error chain when `HasErrors: true`; `null` otherwise.
- `Profiling.OutputDirectory` — present only when `--profiling` was passed on a start verb and collection succeeded; absolute path to the per-run `*.uistat` files and runtime screenshots. See [debugging.md § Profiling Workflow Performance](debugging.md#profiling-workflow-performance).

Workflow log output (`Log Message`, system traces) does **not** appear in `runResult` — logs stream in real time on a separate channel; the envelope carries only the verdict and output data.

> **Single source of truth for success/failure: outer `Result` (equivalently `HasErrors` inside `runResult`).** `Result: "Success"` already accounts for compile failures, validation failures, and unhandled exceptions — the CLI propagates them. **DO NOT infer failure from a streamed log entry's `Level`.** A successful workflow may emit `Log Message` at `Error`/`Warning` level as observability — that is workflow data, not a CLI failure. Treating log levels as a verdict flips green runs to "failed" and burns retries.

---

## Passing structured inputs

`--input-arguments` and `--input-variables` may be supplied as repeatable `key=value` pairs (`key:=value` for raw JSON, `key=@file` to read a value from a file), as an inline JSON string, or from a JSON file using `'@file'` or `--<flag>-file`. `--packages` takes one item per occurrence as comma-joined fields. The exact flag names are `--input-arguments` / `--input-variables` / `--packages` — there is no `--input` flag.

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

---

## validate

`uip rpa validate` returns diagnostics for a file or the whole project, re-validating first by default (`--skip-validation` reads cached, possibly stale, results; `--min-severity` filters). Confirm flags via `uip rpa validate --help`.

> **Known issue: an absolute `--file-path` with an absolute `--project-dir` falsely fails** with `The targeted project file <X> is not in the project folder <Y>`. The CLI normalizes `--file-path` to forward slashes but leaves `--project-dir` with backslashes, then string-compares — same path, different separators. Pass `--file-path` **relative** to the project directory (e.g. `--file-path "Main.xaml"`) to sidestep it. For a project-level compile gate without this quirk, use `build`.

---

## build

`uip rpa build` compiles the project — catching runtime-compile failures `validate` misses (including attribute-form expression failures like `JIT compilation is disabled for non-Legacy projects` in C#-expression XAML projects). Required before returning a project to the user (see [validation-guide.md § Project Build Verification](validation-guide.md#project-build-verification-required-before-returning-a-project)). Takes the project directory as a **positional** argument and runs independently of Studio IPC. Discover flags (log level, skip-analyze, governance, NuGet sources) via `uip rpa build --help`.

`run` and `debug start` compile internally, so a successful smoke test implies `build` would pass. When no smoke test runs (side effects, interactive workflow, no test input), `build` is the required compilability check.

---

## analyzer-rules list

`uip rpa analyzer-rules list` reports the Workflow Analyzer rules **enabled** for the project — the best-practice rules `validate` and `build` enforce. Reports rules, not violations. Each rule returns `severity` (`error`/`warning`/`info`), rule ID, scope, title, and (when available) `recommendation` and `docs` URL. Prefix convention: `ST-*` = built-in Studio rule, `MA-*` = package-shipped rule.

> **Performance:** the unscoped call enumerates every rule across every package and can take a minute or more. If the default 60 s shell timeout fires, narrow with `--scope` (`Activity`, `Workflow`, `Project`, or `Coded Workflow`) — scoped calls return in seconds. See `--help` for accepted scope values.

---

## packages install

`uip rpa packages install` installs or updates NuGet packages (canonical way to add dependencies — **do not hand-edit `project.json`**; there is no `add-dependency` verb). Repeat `--packages` once per package with comma-joined `key=value` fields — `--packages 'id=<PackageId>,version=<Version>'` or just `--packages id=<PackageId>` (see [Passing structured inputs](#passing-structured-inputs)); discover the remaining flags via `uip rpa packages install --help`.

- **Omit the version** to resolve the latest compatible automatically (preferred). Pin only for a known compatibility constraint.
- **Discover available versions** with `uip rpa packages versions --package-id <Id> --include-prerelease`. **Default to `--include-prerelease`** — activity packages frequently ship `-preview` between stable releases, carrying the freshest activity surface and `.local/docs`. When a newer stable or preview exists over the installed version, inform the user and offer the upgrade — never force.
- **Package not found** → verify the exact ID (use `activities find` or the package's `.local/docs`). **Feed/network error** → check NuGet feed config in Studio settings.

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

The verbs you'll reach for: list/describe **connectors** and their **activities**/**resources**, list/create/ping/edit **connections** (OAuth opens a browser; `--no-browser` prints the URL), and run CRUD **resource** operations. For RPA-specific connector workflow patterns (activity/resource discovery, connection management, schema inspection), see [connector-capabilities.md](connector-capabilities.md).

---

## Test Manager (`uip tm`)

Test Manager integration lives in the dedicated `uip tm` tool — `uip tm --help`. Do not document or invoke Test Manager verbs from `uip rpa`.

---

## CLI Error Recovery

Diagnose by error category, apply the recovery, retry **once** — do not loop the same failing command.

| Error pattern | Cause | Recovery |
|---------------|-------|----------|
| `connection refused`, `EPIPE`, `pipe not found` | Studio IPC unavailable. Headless: NuGet restore failed or process exited. Desktop: not running. | Re-run — headless relaunches automatically. If persistent, raise `--timeout` and check Helm restore output for NuGet errors. Run `uip rpa studio start` only for Desktop-only verbs or when `UIPATH_RPA_TOOL_USE_STUDIO=1`. |
| `timeout`, `ETIMEDOUT` | Cold Helm NuGet restore (30–90 s) or long operation. | Raise timeout: `uip rpa --timeout 600 <command>`. For `validate`, also try `--skip-validation`. |
| `not authenticated`, `401`, `403` | Auth required for cloud features. | `uip login`, then retry. |
| `package not found`, `version not available` | Wrong package ID or version. | Verify via `uip rpa activities find`; omit `version` to auto-resolve latest. |
| `project not found`, `no project open` | Wrong `--project-dir` or project not open. | Verify the path points at the `project.json` folder. |
| `not in the project folder` (in `validate`) | Absolute `--file-path` + separator mismatch. | Pass `--file-path` relative to the project root (see [validate](#validate)). |
| `Studio is busy`, `operation in progress` | Studio processing a prior request. | Wait a few seconds, retry. |
| Unrecognized error | Unknown | Re-run with `--verbose` for debug detail, then inform the user. |

---

## RPA discovery tools (non-CLI)

| Action | How |
|--------|-----|
| **Explore project files** | `Glob` `**/*.xaml` |
| **Search XAML content** | `Grep` regex across `.xaml` |
| **Explore Object Repository** | `Glob` `**/*` under `{PROJECT_DIR}/.objects/` + `Read` metadata |
| **Get JIT type definitions** | `Read` `{PROJECT_DIR}/.project/JitCustomTypesSchema.json` |
| **Activity docs** | See [Installed package activity documentation](#installed-package-activity-documentation) above |
| **Inspect a NuGet package's API** | `uip rpa packages inspect` — see [coded/inspect-package-guide.md](coded/inspect-package-guide.md) |

---

## UI Automation (`uip rpa uia ...`)

`uip rpa uia --help` deliberately exposes no standard subcommands — the UIA CLI surface is owned and co-versioned by the `UiPath.UIAutomation.Activities` package. Subcommands, flags, accepted values, and artifact filenames live in `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`. Read that file rather than improvising from `--help`.
