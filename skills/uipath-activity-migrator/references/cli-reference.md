# CLI Reference — `UiPath.Upgrade.exe`

Every command the skill runs, its flags, and what the tool writes. Extension flags are attached to `analyze`, `upgrade`, and `bulk` dynamically; the exact set for an installed build is `UiPath.Upgrade.exe analyze --help`.

## Commands

| Command | Purpose | Writes |
|---|---|---|
| `analyze -p <PROJECT_DIR>` | Full pipeline minus the project copy. Read-only on the project tree except the `.upgrade/` report folder | `<PROJECT_DIR>/.upgrade/<name>-<id>.{sarif,html,log}` |
| `upgrade -p <PROJECT_DIR> -o <OUTPUT_DIR>` | Full pipeline; writes the migrated copy | Same reports, plus `<OUTPUT_DIR>` |
| `bulk -p <ROOT> -c analyze\|upgrade` | Finds every `project.json` under `<ROOT>`, runs one child process per project in parallel, merges results | `<ROOT>/repository-<cmd>-results.sarif` + `.html`; per-project `.upgrade/` folders |
| `version` | Prints the tool version | stdout |

`--project-path` accepts the project folder or the `project.json` path.

## Global options

| Flag | Meaning |
|---|---|
| `-p, --project-path <PATH>` | Required for `analyze` / `upgrade` |
| `-o, --output-path <PATH>` | `upgrade` only. Default `<PROJECT_DIR>_Upgraded`. An existing folder is merged into, not replaced |
| `--ignore-missing-dependencies` | Continue when a package cannot be restored. Workflows using it then report missing types and fail to compile. Use only on explicit user decision |
| `-f, --output-format console\|sarif` | Always `sarif` (Critical Rule 2). `sarif` prints the SARIF log to stdout, suppresses console logging, writes the same log plus HTML into `.upgrade/`, and never opens a browser |
| `-v, --verbose` | Verbose logging into the `.log` file |
| `-e, --extension-directory <DIR>` | Alternate extensions folder. Not needed with the shipped layout |
| `--enabled-extensions <A,B>` / `--disabled-extensions <A,B>` / `--disable-all-extensions` | Mutually exclusive. Default: all discovered extensions enabled. Do not filter unless a package guide says so |

## Orchestrator feed options

Needed only when a dependency lives on a tenant feed (libraries published to Orchestrator). Without `--orchestrator-url`, the tool falls back to the local Studio or Robot connection, which is the preferred path (Critical Rule 6).

| Flag | Meaning |
|---|---|
| `--orchestrator-url <URL>` | Full URL including organization, e.g. `https://cloud.uipath.com/<ORG>` |
| `--orchestrator-tenant <NAME>` | Default `DefaultTenant` |
| `--orchestrator-pat <TOKEN>` | Personal access token with `OR.Execution.Read` |
| `--orchestrator-application-id <ID>` + `--orchestrator-application-secret <SECRET>` | Confidential external application with `OR.Execution.Read`; mutually exclusive with the PAT |

Hand-off template when a tenant feed is required:

```bash
"<MIGRATOR_EXE>" analyze --project-path "<PROJECT_DIR>" --output-format sarif --orchestrator-url "https://cloud.uipath.com/<ORG>" --orchestrator-tenant "<TENANT>" --orchestrator-pat "<PAT>" > "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
```

## Extension options

Only the extensions present in the build expose flags. Names as printed by `--help`.

**Pass extension options as `--name=value`.** The space-separated form parses without error and is silently ignored: `--uia-package-version 25.10.39` leaves the default in place, `--uia-package-version=25.10.39` binds (verified on build `25.10.0` from Git Bash and PowerShell alike). Core options accept both forms.

| Extension | Flags | Guide |
|---|---|---|
| `UiAutomationActivities` | `--uia-package-version=<VER>`, `--uia-fix-selector-strategy=true`, `--uia-enable-partial-migration=true` (absent in build `25.10.0`) | [packages/uia-guide.md](packages/uia-guide.md) |
| `MailActivities` | `--mail-o365-package-version=<VER>`, `--config=<FILE>` (alias `--mail-config`) | [packages/mail-guide.md](packages/mail-guide.md) |
| `GSuiteActivities` (preview builds) | `--gsuite-package-version=<VER>`, `--gsuite-config=<FILE>`, `--gsuite-migrate-only=<svc,...>` | [packages/gsuite-guide.md](packages/gsuite-guide.md) |
| `MicrosoftActivitiesExtension` | none | [packages/microsoft-activities-guide.md](packages/microsoft-activities-guide.md) |
| `MicrosoftOffice365Activities` | package-version bump only in the current build | — |

## Output semantics

- **Exit code** is `0` for success, partial success, and failure alike. Only an unhandled crash returns `1`. Classify from SARIF (see [sarif-triage-guide.md](sarif-triage-guide.md)).
- **stdout in `sarif` mode** is the complete SARIF 2.1.0 log, sometimes preceded by stray `info:` log lines from extension steps. Redirect it to a file; never let it print into the conversation. The summarizer skips the leading lines; a raw `JSON.parse` on the file does not. The tool's own `<project-name>-<UpgradeId>.sarif` in `.upgrade/` is clean JSON.
- **`.upgrade/` folder** is created inside the source project on every run, including `analyze`. Files are named `<project-name>-<UpgradeId>.sarif`, `<project-name>-<UpgradeId>.html`, and `project-<UpgradeId>.log`; the `UpgradeId` is a per-run GUID. The skill additionally redirects stdout to `analyze-latest.sarif` / `upgrade-latest.sarif` in the same folder.
- **Output folder** (`upgrade`): the source tree is copied except `.settings` and `.upgrade`, each workflow is re-serialized from the migrated object model, `project.json` is saved with the new framework and dependency versions. Workflows the pipeline could not load are copied with a warning.
- **HTML report**: same content as the SARIF, human-readable. Point the user at it; do not parse it.

## Pipeline (what a run does)

1. Load `project.json`, discover workflows.
2. Flip `targetFramework` Legacy → Windows (`PROJECT-FRAMEWORK-UPDATE`).
3. Parse each XAML into a DOM (`XAML-WORKFLOW-PARSE`).
4. Extension package bumps (for example `UIAUTOMATION-PACKAGE-UPGRADE`), then restore. Dependencies that are not Windows-compatible are moved to the smallest compatible `major.minor` above the current one, highest patch (`RESTORE-PACKAGE-UPGRADE`, `RESTORE-MISSING-PACKAGE`, `RESTORE-INCOMPATIBLE-PACKAGE`, `RESTORE-CUSTOM-LIBRARY-MIGRATION-REQUIRED`).
5. Load package assemblies (`ASSEMBLY-LOAD`); regenerate local generated assemblies (`REPAIR_LOCAL_ASSEMBLIES`).
6. Type-check every referenced type (`TYPE-CHECK`, `TYPE-MISSING`).
7. Fix assembly and namespace references, including `mscorlib` → `System.Private.CoreLib` and obsolete `UiPath.Core` references (`REFERENCES-FIX`, `OBSOLETE-UIPATH-CORE-REPLACEMENT`).
8. Load workflows into the object model (`WORKFLOW-LOAD`); extension activity migrators run here.
9. Validate (`WORKFLOW-VALIDATION-SUCCESS`, `WORKFLOW-VALIDATION-ISSUE`, `WORKFLOW-COMPILATION-ERROR`).
10. `upgrade` only: copy and serialize to `<OUTPUT_DIR>` (`PROJECT-COPY`); extension finalizers run after this.

A critical error stops the pipeline at that step; later rules simply do not appear in the log.

## bulk

```bash
"<MIGRATOR_EXE>" bulk --path "<ROOT>" --command analyze --output-format sarif > "<ROOT>/bulk-analyze-latest.sarif"
```

Use `bulk --command analyze` to survey a repository. Prefer per-project `upgrade` runs over `bulk --command upgrade`: bulk does not order libraries before their consumers, and a consumer migrated before its library fails restore. Each child project still gets its own `.upgrade/` folder; the merged log at `<ROOT>` is what the summarizer should read.
