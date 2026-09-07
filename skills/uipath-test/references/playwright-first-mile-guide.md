# Playwright First Mile — Pack, Ingest, and Run on Serverless

End-to-end Playwright pipeline from repository to UiPath Test Manager results using only `uip` commands. This is **Playwright-specific**: `pack`, auto-created test cases, `PW_*` labels, and per-project run selection do not apply to UiPath Studio/RPA packages. For Studio automation, use [publish-and-link-guide.md](publish-and-link-guide.md); never mix pipelines.

## Pipeline rules

1. Pack with `uip tm pack --type playwright`; it creates a `.nupkg` containing test metadata.
2. Upload with `uip or packages upload`.
3. Ingestion is automatic: one Test Manager case per discovered Playwright **test**, bound to the package, with `PW_Tag_<tag>`, `PW_Project_<name>`, `PW_Suite_<name>`, `PW_Path_<chain>`, and `PW_File_<path>` labels as applicable.
4. Create an empty test set and fill it with `uip tm testcases add --labels`.
5. Run `uip tm testsets playwright-context` when available.
6. Run with `uip tm testsets run`, optionally `--playwright-projects <names...>`.
7. Wait, report, and retrieve results.

There is **no link step**. Do **NOT** run `uip tm testcases link-automation` on Playwright cases: ingestion links them; manual linking is the RPA pipeline and corrupts the association.

For `--output json`, parse the JSON envelope from the first `{` through its matching final `}` (or read the last balanced JSON object). Auto-updater chatter, `Update completed with failures.`, `Resolved project …` lines, and telemetry warnings may occur on either side. Judge the command only by the envelope's `Result` field.

`testsets playwright-context` and `run --playwright-projects` are hidden from `--help`. Older CLIs may return `unknown command` / `unknown option`: if the probe is missing, skip Step 5 and continue; if `--playwright-projects` is rejected, run without it so every project in the package config runs, and do not retry the flag. Project scoping still works without the probe.

## Prerequisites

Find or create a Test Manager project and capture its key:
```bash
uip tm project list --filter <name> --output json
uip tm project create --name <NAME> --project-key <PROJECT_KEY> --output json
```

Playwright support must be enabled for the tenant. If Step 3 never creates cases, stop and ask the user; suspect this feature flag first. The project directory must contain `package.json` with `@playwright/test` installed, one of `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` / `bun.lock`, and a `playwright.config` file. Discovery shells out to the project's own `playwright test --list`, needs no browsers, and serverless performs a deterministic install.

## Step 1 — Pack

Run:
```bash
uip tm pack --project-path <dir> --type playwright \
    --project-key <PROJECT_KEY> --name <PackageName> \
    --package-version 1.0.0 -o <out-dir> --output json
```

`--project-key` is required by default because auto-creation is enabled; pass `--no-create-test-cases` to omit it, while label metadata remains embedded. Preview with `--dry-run` (writes nothing). Read `Data.Output` for the `.nupkg` path and `Data.TestCount`; retain `TestCount` for Step 3. It is the number of cases ingestion creates, one per Playwright test rather than per test-project combination. Missing `package.json`, lockfile, or `@playwright/test` fails loudly; fix the project.

## Step 2 — Upload

Run:
```bash
uip or packages upload "<out-dir>/<PackageName>.1.0.0.nupkg" --output json
```

`--package-version` must be NuGet/SemVer-style with **three or four** numeric parts and optional prerelease/build suffix (`1.0.0`, `1.0.0.0`, `1.0.1-beta.1`); `1.0` is rejected. Each upload needs a new feed version. Before repacking, run:
```bash
uip or packages list --search <PackageName> --output json
```
The result is the feed's **latest** version only (`IsLatestVersion: true`, one row), not version history; choose a higher version.

## Step 3 — Wait for ingestion

Ingestion is asynchronous and automatic. Poll unfiltered:
```bash
uip tm testcases list --project-key <PROJECT_KEY> --output json
```

Do NOT pass `--filter <PackageName>`: `--filter` matches a test case name or key by prefix (SKILL.md Rule 8), while ingested names are `"<suite> > <test title>"`; the package name therefore produces a permanent false empty result. Count `TestCaseKey` (for example `SHIP:1`), not UUID `Id`, and inspect `Name`. Ingestion is complete when the Step 1 `TestCount` new cases appear, each named `"<suite> > <test title>"`. Plain `pack` prints only `Package`, `Output`, and `TestCount`; use `--dry-run` or inspect `testCases.json` in the `.nupkg` for exact expected names. `TestCount` is not multiplied by projects. `IsAutomated: false` is normal.

Poll every ~10 seconds for up to ~3 minutes. If expected names do not appear, STOP and report; likely causes are the tenant feature flag or wrong `--project-key`, neither fixed by retrying. Spot-check labels:
```bash
uip tm objectlabel list --project-key <PROJECT_KEY> --object-type TestCase --filter PW_ --output json
```
This returns distinct label *names* only.

## Step 4 — Configure the folder and fill a test set

Set the project's default Orchestrator folder FIRST; both the Step 5 probe and Step 6 run resolve packages through it (Critical Rule #9):
```bash
uip or folders list --output json
uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json
```
Run `folders list` **without `--all`**: it lists only folders where you are a member; `--all` includes visible folders without your rights and may cause `folderNotFoundOrNoAccess` later.

The folder needs one Cloud Robots – Serverless machine and a folder member who can run unattended. Check/create/assign one machine (one serverless machine per folder):
```bash
uip or machines list --folder-key <FOLDER_KEY> --output json
uip or machines create -n <name> --serverless --testing-slots 2 --output json
uip or machines assign <MACHINE_KEY> --folder-key <FOLDER_KEY> --output json
```
Capture `Data.Key`; `assign` takes machine KEYS (GUIDs), not names. Without the machine, job creation returns 500 and execution is instantly `Cancelled`.

The run chooses a robot user from the folder, and `uip tm testsets run` has no user-selection flag (only `uip tm testcases run` does); membership is the only lever:
```bash
uip or users list-in-folder --folder-key <FOLDER_KEY> --output json
uip or users get <USER_KEY> --all-fields --output json
```
Require `MayHaveUnattendedSession: true`. Ordinary interactive users usually have `MayHaveUnattendedSession: false`; `uip or users update --allow-unattended` cannot fix this because it requires a Windows unattended username and password, which serverless does not use. Assign an already-capable principal, reliably a `DirectoryRobot` account. If no folder qualifies, create one with `uip or folders create <NAME> --output json` (name positional), then attach a machine and capable user.

Folder, machine, and robot-user management belongs to the platform skill; use [/uipath:uipath-platform § orchestrator/setup-environment.md](../../uipath-platform/references/orchestrator/setup-environment.md) for authoritative flags and the one-serverless-machine-per-folder rule.

Create and fill the set:
```bash
uip tm testsets create --project-key <PROJECT_KEY> --name "PW Smoke" --output json
uip tm testcases add --test-set-key <TEST_SET_KEY> --labels "PW_File_<path>" --output json
```
Capture `TestSetKey` (for example `DEMO:10`). `--labels` is variadic, space-separated, exact, case-sensitive, and OR-matched; quote names containing spaces and discover real names with `uip tm objectlabel list` rather than guessing. It accepts any object label; `PW_*` are ingestion labels only. It is mutually exclusive with `--test-case-keys`; pass exactly one.

Labels select **tests**; `--playwright-projects` selects browsers/projects. To run a whole suite on one browser, fill with `PW_Suite_*` or `PW_File_*` and pass that browser in Step 6. `PW_Project_<name>` selects tests participating in that project but does not make the run project-only. To run only a project, label-fill the desired tests by tag, suite, or file and pass the project name at run time.

Keep one test set = one Playwright package for project scoping. Labels are not package-qualified: generic labels such as `PW_Tag_smoke` match all packages in a multi-package project. Use a package-unique `PW_File_<path>`, a unique suite label, or explicit `--test-case-keys` from the current ingestion. A mixed-package set cannot be project-scoped.

## Step 5 — Probe Playwright context

When available, run:
```bash
uip tm testsets playwright-context --test-set-key <TEST_SET_KEY> --output json
```

Read response fields rather than assuming the shape. `Data.IsPlaywright: true` means the set resolves to one Playwright package; `AvailablePlaywrightProjects` contains valid flag values and `SelectedPlaywrightProjects` contains the stored selection. Both are comma-joined strings such as `"chromium, firefox"`, not arrays; split on `", "` when scripting, and no stored selection is `""`.

`Data.IsPlaywright: false` means the set does not resolve to exactly one synced Playwright package (RPA, multiple packages, or no package); run without `--playwright-projects`. `true` does not mean the set contains only Playwright tests: manual cases plus one Playwright package still return `true`. Treat it as “project selection is available.” The server does not error on type, so probe first and branch on `IsPlaywright`. Without a default folder, a genuine Playwright set falsely reports `IsPlaywright: false`; set the folder in Step 4 before trusting false.

## Step 6 — Run

For a scoped run, run:
```bash
uip tm testsets run --test-set-key <TEST_SET_KEY> \
    --playwright-projects chromium --output json
```

`--playwright-projects` is functional but absent from `uip tm testsets run --help`. Values are space-separated, case-sensitive names from `playwright.config`; several (`chromium firefox`) run all selected projects but still produce one log per test case, not per browser, so scope to one for attributable results. Unknown names fail fast before persistence and list available projects. The flag requires every case to come from one Playwright package and fails for Studio/RPA sets; omit it there. Selection persists on the test set until changed; omitting it reuses the stored selection, or config defaults if none was stored. Without tenant Playwright support, the command fails with instructions rather than running incorrectly. Omit the flag for a plain run using all config-default projects.

Start without `--wait` for automation: the immediate complete JSON envelope carries `ExecutionId` and `Status: Pending`. With `--wait`, take the id from `Execution started: <id> (Pending)`, not `Starting execution for test set …`, whose UUID is the test-set id.

Wait in bounded chunks:
```bash
uip tm wait --execution-id <EXECUTION_ID> --timeout 120 --output json
```
Run it in a loop, or run `uip tm executions get-stats` every 30–60 s. A single `--wait` may be silent for minutes and trigger watchdogs/timeouts. `wait` polls every 60 s; use a `--timeout` that is a multiple of 60. If it reaches its timeout, it returns a Failure envelope with `Retry: "RetryWillNotFix"`; for a non-terminal execution this means still running, so keep polling.

## Step 7 — Results

`--wait` blocks the run to terminal; without it, run:
```bash
uip tm wait --execution-id <EXECUTION_ID> --output json
```

Summary:
```bash
uip tm report get --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
```
`--project-key` or `--test-set-key` is required; bare `--execution-id` exits with `Provide --project-key or --test-set-key`.

Per-test detail:
```bash
uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
```
Judge by `Result` (`Passed` / `Failed` / `None`), not `HasError` (`false` can accompany a failed test).

JUnit:
```bash
uip tm result download --execution-id <EXECUTION_ID> --result-path <dir> --output json
```
For Playwright, XML names every case after the spec file, not title; use `testcaselogs list` to identify failures.

To prove project scope:
```bash
uip tm executions get-stats --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
```
Read `PlaywrightExecutionSnapshot.Projects` (for example `["chromium"]`) only. `Version` is two-component (`1.0`), as in `list-automations` and `playwright-context`, so it cannot distinguish `1.0.1` from `1.0.0`; `TestCaseVersion` in logs can. Log count proves nothing: there is one log per Playwright test, not per test × project.

Execution runs on UiPath serverless cloud runtimes; no robot or package deployment into the folder is needed beyond Step 2 upload, but the folder must have its serverless machine assignment from Step 4.

## When a run produces no results

Diagnose with both commands below, then stop; retrying does not fix these shapes:
```bash
uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
uip or jobs list --folder-key <FOLDER_KEY> --output json
```

- `Cancelled` within seconds with logs pointing to `CreateTestAutomationJobs` / `InternalServerError`: no serverless machine in the default folder.
- `Finished` with `Passed: 0 / Failed: 0 / None: N`: no per-test results reached Test Manager; the log `Info` contains the reason (results upload failed or job never started). `report get` counts `None` as **`Skipped`**, so 0% means results lost, not tests skipped.
- Stuck `Pending`: dispatch worked but nothing executes. A faulted job may never sync; check after ~5 minutes rather than waiting 30 minutes. Fixing the folder does not rescue the existing execution; fix it and start a new run.
- `Serverless.Runtime.CannotIssueUserTokenDueToUserNotPartOfOrg` in `Info`: the selected folder account remains assigned but is no longer valid in the org. Point the project to a folder whose members satisfy Step 4, or create one, then rerun.

Everything beyond the Test Manager boundary—job states, machines, and folder membership—belongs to [/uipath:uipath-platform § orchestrator/run-jobs.md](../../uipath-platform/references/orchestrator/run-jobs.md) and [§ orchestrator/setup-environment.md](../../uipath-platform/references/orchestrator/setup-environment.md). A `Duration` of `00:00:00` and empty `StartTime` on a finished execution are normal. `JobKey` in logs proves dispatch; jobs `Faulted` with no host machine mean the tenant cannot run them. Report this to the platform team rather than rerunning; there is no CLI verb to cancel a Test Manager execution.

## Iterating on the suite

Changing or fixing a test requires a new package version:
```bash
uip tm pack --project-path <dir> --type playwright --project-key <PROJECT_KEY> --name <PackageName> --package-version 1.0.1 -o <out-dir> --output json
uip or packages upload "<out-dir>/<PackageName>.1.0.1.nupkg" --output json
```

The version must be new; the feed rejects duplicates. Ingestion updates existing cases in place by test, creates new ones, and unlinks removed ones. If the test list is unchanged, the test set keeps its membership and needs no re-add or replacement; rerun the same `--test-set-key`. Run `uip tm testcases add --labels` again only when new tests should join. Stored Playwright project selection survives.

Allow ~60–90 s after upload before rerunning. Confirm the new package actually ran with:
```bash
uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
```
Read `TestCaseVersion` and expect the packed version (`1.0.1`). `list-automations` exposes only two-component `PackageVersion` (`1.0`), which cannot distinguish `1.0.1` from `1.0.0`; unchanged counts and names make ingestion updates otherwise invisible. An old `TestCaseVersion` means a stale package, not a bad fix.
