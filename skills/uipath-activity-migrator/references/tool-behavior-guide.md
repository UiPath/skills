# Tool Behavior Guide

Facts about `UiPath.Upgrade.exe` that neither `--help` nor the product documentation states, learned from the tool's source and from live runs. For the list of commands and flags, the installed build is the only authority:

```bash
"<MIGRATOR_EXE>" analyze --help
```

Core options come first, then one block per active extension. A flag named anywhere in this skill but missing from that output does not exist in this build: do not pass it, and say so in the report.

## Option binding

- Core options (`--project-path`, `--output-path`, `--output-format`, `--orchestrator-*`, `--enabled-extensions`) accept both `--name value` and `--name=value`.
- Extension options (`--uia-*`, `--mail-*`, `--config`, `--gsuite-*`) bind only as `--name=value`. The space-separated form parses without error and is silently ignored. Verified: `--uia-package-version 25.10.39` left the default in place; `--uia-package-version=25.10.39` bound. The symptom is the `UIAUTOMATION-PACKAGE-UPGRADE` message naming the default version.

## Exit code

`0` for success, partial success, and failure alike. Only an unhandled crash returns `1`. Status comes from the SARIF results (see [sarif-triage-guide.md](sarif-triage-guide.md)).

## Output streams

- `--output-format sarif`: stdout is the SARIF 2.1.0 log, sometimes preceded by stray `info:` lines from extension steps. Redirect it to a file; the summarizer skips the leading lines, a raw JSON parse does not. Console logging is otherwise suppressed and no browser opens.
- `--output-format console` (the default): a text summary plus an HTML report that the tool opens in the browser. Never use it from the agent.

## The `.upgrade` folder

Created inside the source project on every run, `analyze` included. Files per run: `<project-name>-<UpgradeId>.sarif`, `<project-name>-<UpgradeId>.html`, `project-<UpgradeId>.log`; the `UpgradeId` is a per-run GUID. The skill adds `analyze-latest.sarif` and `upgrade-latest.sarif` by redirecting stdout there. The folder is never copied to the output project.

## Output folder

- `upgrade` writes to `--output-path`, default `<PROJECT_DIR>_Upgraded`.
- The tool never empties the output folder first. It copies file by file with overwrite, so when `MyProj_Upgraded` already exists from an earlier run, files that the current source no longer has (a deleted workflow, old screenshots) survive next to the new output. Use a folder that does not exist yet, or ask the user before deleting the old one (Step 1).
- Contents: the source tree minus `.settings` and `.upgrade`, each workflow re-serialized from the migrated object model, `project.json` saved with the new framework and dependency versions. A workflow the pipeline could not load is copied unchanged with a warning.

## Package versions during restore

- Extension package pins run before restore and replace the dependency with an exact `[x.y.z]`.
- Every other dependency that is not Windows-compatible moves to the smallest compatible `major.minor` above its current version, highest patch. The tool does not chase the newest line.
- A pinned version that no reachable feed serves surfaces as `RESTORE-MISSING-PACKAGE`.
- Tenant feeds: without `--orchestrator-url`, the tool falls back to the local Studio or Robot connection. With the URL, it needs a PAT or a confidential external application with `OR.Execution.Read`.

## Orchestrator hand-off template

Secrets never pass through the agent (Critical Rule 6). Hand the user the complete command with placeholders:

```bash
"<MIGRATOR_EXE>" analyze --project-path "<PROJECT_DIR>" --output-format sarif --orchestrator-url "https://cloud.uipath.com/<ORG>" --orchestrator-tenant "<TENANT>" --orchestrator-pat "<PAT>" > "<PROJECT_DIR>/.upgrade/analyze-latest.sarif"
```

## Extensions

- Loaded from `Extensions/<Name>/` next to the executable; all discovered extensions are enabled by default. `--enabled-extensions`, `--disabled-extensions`, and `--disable-all-extensions` are mutually exclusive; do not filter unless a package guide says so.
- The UIAutomation extension holds no conversion rules. It loads the migration service shipped inside the target UIAutomation package, so what migrates depends on the pinned package version, not on the tool build.
- Extension activity migrators run after workflows load into the object model; package pins run before restore; the UIAutomation finalizer runs after the project copy and writes `<OUTPUT_DIR>/.screenshots/`.

## bulk

```bash
"<MIGRATOR_EXE>" bulk --path "<ROOT>" --command analyze
node "<SKILL_DIR>/scripts/summarize-sarif.mjs" "<ROOT>/repository-analyze-results.sarif"
```

- `bulk` has its own, smaller option set: `--path`, `--command analyze|upgrade`, `--verbose`, `--output-path` (upgrade only; each project lands in `<OUTPUT>/<project-folder-name>`), the `--orchestrator-*` options, and the three extension-management options. It rejects `--output-format` and every extension option such as `--uia-package-version`; children run with the extensions' built-in defaults, so the target UIAutomation version cannot be chosen in bulk mode.
- Its stdout is a text log, not SARIF. Children are started with `--output-format sarif` internally; `bulk` merges their logs into `<ROOT>/repository-<command>-results.sarif` plus an HTML twin, and each project still gets its own `.upgrade/` folder. Read the merged `.sarif` with the summarizer.
- No dependency ordering: a consumer migrated before its library fails restore. Use `bulk` with `analyze` to survey a repository; run `upgrade` per project, libraries first, which also restores the ability to pass `--uia-package-version=`.
