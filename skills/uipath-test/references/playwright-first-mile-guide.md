# Playwright First Mile — Pack, Ingest, and Run on Serverless

End-to-end pipeline: take a Playwright test suite from a repo to executed results in UiPath Test Manager, using only `uip` commands. This flow is **Playwright-specific** — the pack command, the auto-created test cases, the `PW_*` labels, and the per-project run selection below do NOT apply to UiPath Studio/RPA packages. For Studio test automation use [publish-and-link-guide.md](publish-and-link-guide.md) instead; never mix the two pipelines.

## Pipeline

```
uip tm pack --type playwright        → .nupkg with embedded test metadata
uip or packages upload               → package on the Orchestrator feed
(Test Manager ingestion, automatic)  → test cases auto-create, PW_* labels applied
uip tm testsets create               → empty test set
uip tm testcases add --labels        → fill it by label
uip tm testsets playwright-context   → probe: is this a Playwright test set? which projects?
uip tm testsets run [--playwright-project <name>] → execute on serverless
uip tm wait / report / result        → outcome
```

The key difference from the RPA pipeline: there is **no link step**. Uploading the package is enough — ingestion creates one Test Manager test case per discovered Playwright test, already bound to the package, and labels each with:

- `PW_Tag_<tag>` — one per Playwright tag (`@smoke` → `PW_Tag_smoke`)
- `PW_Project_<name>` — one per Playwright project the test runs in
- `PW_Suite_<name>` / `PW_Path_<chain>` — describe-block grouping (name and full chain)
- `PW_File_<path>` — the spec file

> **Do NOT run `uip tm testcases link-automation` on Playwright test cases.** They are linked by ingestion; manual linking is the RPA pipeline and will corrupt the association.

> **Reading command output.** `--output json` prints a JSON envelope, but not on its own line: auto-updater chatter (including `Update completed with failures.`, which is unrelated to your command), `Resolved project …` progress lines and trailing telemetry warnings share the same stream. Judge a command by the `Result` field inside the envelope, never by surrounding text. Noise appears on **both sides** of the JSON, so taking everything from the first `{` is not enough — slice from the first `{` to the **matching final `}`** (or read the last balanced JSON object) before parsing, or a trailing telemetry line will break the parse.

> **If a command is missing.** Two commands in this pipeline are hidden from `--help`, so `--help` is not a reliable way to tell whether a build has them: `testsets playwright-context` (Step 5) and `run --playwright-project` (Step 6). Older CLIs answer `unknown command` / `unknown option` for them. Treat them differently:
>
> - **Probe missing** → skip Step 5 and continue. The probe only *reports* whether a test set is Playwright; it does not enable anything, so losing it costs you the pre-check, not the capability. Project scoping still works.
> - **`--playwright-project` rejected** → this build cannot scope a run to selected projects. Run the test set without the flag (every project in the package's config runs) rather than retrying.

## Prerequisites

- A Test Manager project to land the test cases in: `uip tm project list --filter <name> --output json`, or `uip tm project create --name <NAME> --project-key <PROJECT_KEY> --output json`. Capture the project key.
- The tenant's Test Manager must have Playwright support enabled (a server-side feature flag). If ingestion never produces test cases (Step 3), this is the first thing to suspect — stop and ask the user.
- The Playwright project directory must contain:
  - `package.json` with `@playwright/test` installed (discovery shells out to the project's own `playwright test --list`; no browsers needed),
  - a **lockfile** (`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` / `bun.lock`) — serverless does a deterministic install,
  - a `playwright.config` file.

## Step 1 — Pack

```bash
uip tm pack --project-path <dir> --type playwright \
    --project-key <PROJECT_KEY> --name <PackageName> \
    --package-version 1.0.0 -o <out-dir> --output json
```

- `--project-key` is **required** by default because test-case auto-creation is on; pass `--no-create-test-cases` to pack without it (label metadata stays embedded for later use).
- Preview with `--dry-run` (writes nothing).
- Capture `Data.Output` (the `.nupkg` path) and `Data.TestCount` from the JSON output. `TestCount` is the number of test cases ingestion will create — remember it for Step 3.
- Pack fails loudly when the lockfile or `@playwright/test` is missing — fix the project, do not improvise around it.

## Step 2 — Upload to Orchestrator

```bash
uip or packages upload "<out-dir>/<PackageName>.1.0.0.nupkg" --output json
```

`--package-version` is a NuGet/SemVer-style version: **three or four** numeric parts with an optional prerelease/build suffix (`1.0.0`, `1.0.0.0`, `1.0.1-beta.1`) — `1.0` is rejected. Each upload needs a version the feed does not already have, so before re-packing check what is published and go above it:

```bash
uip or packages list --search <PackageName> --output json
```

The match returns the feed's **latest** version only (one row, `IsLatestVersion: true`) — enough to pick the next version, but it is not a version history.

## Step 3 — Wait for ingestion

Ingestion is asynchronous and automatic. Poll until the auto-created test cases appear:

```bash
uip tm testcases list --project-key <PROJECT_KEY> --output json
```

- Poll **unfiltered**. Do NOT pass `--filter <PackageName>` — `--filter` matches a test case's name or key by **prefix** (see SKILL.md Rule 8), and an ingested test case is named `"<suite> > <test title>"`, so a package name never matches: the call stays empty forever and reads as a false "ingestion never happened".
- The rows carry `TestCaseKey` (e.g. `SHIP:1`) plus `Id` (the UUID) and `Name` — count `TestCaseKey`, not `Id`, when polling.
- Ingestion is done when `TestCount` new test cases from Step 1 are present, each named `"<suite> > <test title>"`. A plain `pack` prints only `Package`, `Output` and `TestCount` — if you want the exact expected names up front, run `--dry-run` first or read `testCases.json` inside the `.nupkg`; otherwise match on the count plus that name shape.
- `TestCount` from Step 1 is one test case per Playwright **test** — it is not multiplied by the number of Playwright projects (2 tests × 2 projects → 2 test cases).
- Ingested test cases show `IsAutomated: false` in list output; that is normal and does not mean ingestion failed.
- Poll every ~10 seconds for up to ~3 minutes. If the expected names never appear, STOP and report — the likely causes are the Playwright feature flag being off for the tenant or a wrong `--project-key`, and neither is fixed by retrying.
- Spot-check the labels landed: `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type TestCase --filter PW_ --output json` (returns distinct label *names* only).

## Step 4 — Set the default folder, create a test set, fill it by label

Set the project's default Orchestrator folder FIRST — both the Step 5 probe and the Step 6 run resolve packages through it (Critical Rule #9):

```bash
uip or folders list --output json    # WITHOUT --all: only folders you are a member of
uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json
```

- Pick the folder from the **unflagged** `folders list` — `--all` returns every folder *visible* to you, including ones where you have no rights; choosing one of those fails later with `folderNotFoundOrNoAccess`.
The folder needs **two** things, and missing either one fails the run differently:

- **A Cloud Robots – Serverless machine** — without it job creation 500s and the execution is instantly `Cancelled`. Check with `uip or machines list --folder-key <FOLDER_KEY> --output json`; if none, create and assign one (one serverless machine per folder):

```bash
uip or machines create -n <name> --serverless --testing-slots 2 --output json   # capture Data.Key
uip or machines assign <MACHINE_KEY> --folder-key <FOLDER_KEY> --output json    # takes machine KEYS (GUIDs), not names
```

- **A folder member who can run unattended** — the run executes as a robot user drawn from the folder, and `uip tm testsets run` has no flag to choose one (only `uip tm testcases run` does), so folder membership is the only lever:

```bash
uip or users list-in-folder --folder-key <FOLDER_KEY> --output json
uip or users get <USER_KEY> --all-fields --output json      # needs MayHaveUnattendedSession: true
```

Folder, machine and robot-user management is the platform skill's domain — see [/uipath:uipath-platform § orchestrator/setup-environment.md](../../uipath-platform/references/orchestrator/setup-environment.md) for the authoritative flags and the one-serverless-machine-per-folder rule. An ordinary interactive user usually has `MayHaveUnattendedSession: false`, and `uip or users update --allow-unattended` cannot fix that here — it requires a Windows unattended username and password, which serverless does not use. Assign an already-unattended-capable principal instead (a `DirectoryRobot` account is the reliable pick). Creating your own folder is a first-class option when no existing one qualifies: `uip or folders create <NAME> --output json` (name is positional), then attach a machine and such a user.

```bash
uip tm testsets create --project-key <PROJECT_KEY> --name "PW Smoke" --output json
uip tm testcases add --test-set-key <TEST_SET_KEY> --labels "PW_File_<path>" --output json
```

- Capture `TestSetKey` from the create output (e.g. `DEMO:10`).
- `--labels` is variadic and space-separated (quote names that contain spaces). Matching is **OR across labels, exact, and case-sensitive** — discover the real names first with `uip tm objectlabel list` rather than guessing.
- `--labels` works with any object label; the `PW_*` labels are simply what ingestion applies.
- Mutually exclusive with `--test-case-keys`; pass exactly one of the two.
- To run the whole suite on one browser: fill by a suite/file label (`PW_Suite_*` or `PW_File_*`) and pass the browser to `--playwright-project` in Step 6. Filling by `PW_Project_<name>` is for selecting the subset of tests that participate in that project — it does not restrict which browsers run.
- **Labels select *tests*; `--playwright-project` selects *the browser* (one project).** Filling by `PW_Project_firefox` picks every test that runs in the firefox project (often all of them); it does not make the run firefox-only — that is what the run flag in Step 6 does. To "run only <project>", label-fill by whatever identifies the tests you want (tag, suite, file) and pass the one project name to `--playwright-project`.
- **Keep one test set = one Playwright package.** Per-project selection (Step 6) requires every test case in the set to come from a single Playwright package; label-filling across packages produces a set that cannot be project-scoped. Labels are NOT package-qualified — in a project holding several Playwright packages, a generic label like `PW_Tag_smoke` matches tests from all of them. There, fill by a package-unique label (`PW_File_<path>`, or a suite name unique to the package) or by explicit `--test-case-keys` from the current ingestion.

## Step 5 — Probe the Playwright context (when available)

Before deciding whether `--playwright-project` applies, ask the server:

```bash
uip tm testsets playwright-context --test-set-key <TEST_SET_KEY> --output json
```

Read the fields off the JSON response rather than relying on the names below staying current — this list describes today's shape, and `--output json` always carries whatever the API returns.

- `Data.IsPlaywright: true` → the set resolves to one Playwright package; `AvailablePlaywrightProjects` (a **comma-joined string**, e.g. `"chromium, firefox"`, not an array — split on `", "` when scripting) holds the valid `--playwright-project` values, and `SelectedPlaywrightProjects` shows the single stored selection (at most one project per execution), `""` when none.
- `Data.IsPlaywright: false` → the set does **not** resolve to exactly one synced Playwright package (RPA, multi-package, or no package at all) — run it **without** `--playwright-project`.
- **`true` does not mean "only Playwright".** The check is *one* Playwright package, not *only* Playwright tests: a set holding Playwright tests from one package plus manual test cases still reports `true`, because manual cases resolve to no package. Treat the flag as "project selection is available here", not as a purity test.
- The server never errors on type here, so this is the safe discriminator for automation: probe first, branch on `IsPlaywright`.
- **False negative without a folder:** the probe resolves the package through the project's default folder — if that isn't set (Step 4), a genuine Playwright test set reports `IsPlaywright: false`. Set the default folder before trusting a `false`.

## Step 6 — Run, optionally per Playwright project

```bash
uip tm testsets run --test-set-key <TEST_SET_KEY> \
    --playwright-project chromium --output json
```

`--playwright-project` does not appear in `uip tm testsets run --help` — functional but unlisted, so treat this guide as its reference rather than concluding the build lacks it. Semantics (all enforced with clear errors, nothing silently ignored):

- Space-separated, case-sensitive names from the package's `playwright.config`. Passing several (`chromium firefox`) runs all of them, but results stay one log per test case — not per browser — so a per-browser breakdown is not available from Test Manager; scope to one project when you need attributable results. Unknown names **fail fast, before anything is persisted**, listing the available projects.
- Valid only when every test case in the set comes from one single Playwright package (see Step 4); fails for Studio/RPA test sets — run those without the flag.
- The selection **persists on the test set** and applies to later runs until changed; omit the flag to reuse the stored selection (or the config's defaults if none was ever stored).
- On a Test Manager without Playwright support the command fails with instructions rather than running incorrectly.

Omit `--playwright-project` entirely for a plain run (all config-default projects).

**Getting the execution id.** Start the run **without** `--wait`: it returns a complete JSON envelope immediately, carrying `ExecutionId` and `Status: Pending` — the cleanest handle for automation. With `--wait` the envelope only arrives at terminal state, so take the id from the `Execution started: <id> (Pending)` progress line — not from `Starting execution for test set …`, whose UUID is the *test set*.

**Agent-friendly waiting:** a single `--wait` call can sit silent for many minutes, which trips agent-harness watchdogs and shell timeouts. When running as an agent, prefer starting the run **without** `--wait`, then poll in bounded chunks: `uip tm wait --execution-id <EXECUTION_ID> --timeout 120 --output json` in a loop (or `uip tm executions get-stats` every 30–60 s), so every call returns quickly and progress stays visible. `wait` polls on a fixed 60 s interval, so keep `--timeout` a multiple of that — a shorter timeout can report a timeout for a run that already finished. A `wait` that hits its `--timeout` returns a Failure envelope with `Retry: "RetryWillNotFix"` — for a non-terminal execution that just means "still running"; keep polling, don't treat it as fatal.

## Step 7 — Results

- `--wait` on the run blocks until terminal; without it, use `uip tm wait --execution-id <EXECUTION_ID> --output json`.
- Summary: `uip tm report get --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json` (`--project-key` or `--test-set-key` is required — bare `--execution-id` exits with "Provide --project-key or --test-set-key").
- Per-test detail: `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json`. Judge pass/fail by `Result` (`Passed` / `Failed` / `None`) — a failed test still reports `HasError: false`, so that field is not the outcome.
- JUnit export: `uip tm result download --execution-id <EXECUTION_ID> --result-path <dir> --output json` — counts only for Playwright: the XML names every case after the spec file, not the test title, so use `testcaselogs list` when you need to know *which* test failed.
- **Proving the run was scoped as asked:** `uip tm executions get-stats --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json` returns a `PlaywrightExecutionSnapshot` whose `Projects` is the project list the run actually used (`["chromium"]`). Read only `Projects` from it — its `Version` is two-component (`1.0`), like `list-automations` and `playwright-context`, so none of the three can tell 1.0.1 from 1.0.0; `TestCaseVersion` on the logs is the only field that can. Counting logs proves nothing here — there is one test case log per Playwright **test**, not per test × project, so a two-project run yields the same number of logs as a one-project run.

Execution happens on UiPath serverless cloud runtimes — no robot or package deployment into the folder is needed beyond the upload in Step 2, but the folder does need its serverless machine assignment (Step 4).

### When a run produces no results

Three shapes, one rule: diagnose with the two commands below, then stop — retrying doesn't fix any of them.

- **`Cancelled` within seconds**, logs pointing at `CreateTestAutomationJobs` / `InternalServerError` → the default folder has no serverless machine assigned (Step 4).
- **`Finished` with `Passed: 0 / Failed: 0 / None: N`** → the run ended without per-test results reaching Test Manager; the test case log's `Info` carries the reason (results upload failed, or the job never started). Note `report get` counts `None` as **`Skipped`**, so 0% here means "results lost", not "tests skipped".
- **Stuck `Pending`** → dispatch worked but nothing is executing. A faulted job may never sync back, so don't sit out the 30-minute wait; check after ~5 minutes. Fixing the folder does **not** rescue an already-pending execution — start a new run after fixing.
- **`Serverless.Runtime.CannotIssueUserTokenDueToUserNotPartOfOrg`** in a log's `Info` → the folder's robot-user pool is bad: the account Test Manager picked is still folder-assigned but no longer valid in the org. Unlike the shapes above this **is** fixable from the CLI — point the project at a folder whose members satisfy Step 4 (or create one), then re-run.

```bash
uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
uip or jobs list --folder-key <FOLDER_KEY> --output json
```

Everything past the Test Manager boundary — job states, machines, folder membership — belongs to [/uipath:uipath-platform § orchestrator/run-jobs.md](../../uipath-platform/references/orchestrator/run-jobs.md) and [§ orchestrator/setup-environment.md](../../uipath-platform/references/orchestrator/setup-environment.md); use those for the job-side detail. A `Duration` of `00:00:00` and an empty `StartTime` on an already-finished execution are normal — not evidence of a broken run. `JobKey` values on the logs prove Test Manager dispatched; jobs `Faulted` with no host machine mean the tenant can't run them. Either way it needs the platform team — report it rather than re-running (there is no CLI verb to cancel a Test Manager execution).

## Iterating on the suite (and getting a fix back in)

Changing a test — including fixing one the run just failed — uses the same pipeline with a bumped version:

```bash
uip tm pack --project-path <dir> --type playwright --project-key <PROJECT_KEY> --name <PackageName> --package-version 1.0.1 -o <out-dir> --output json
uip or packages upload "<out-dir>/<PackageName>.1.0.1.nupkg" --output json
```

The version **must** be new — the Orchestrator feed rejects one it already has (Step 2). Ingestion then **updates** the existing test cases in place (matched per test), creates any new ones, and unlinks removed ones, so:

- **A test set keeps its membership** when the test list is unchanged — nothing to re-add, no new test set, re-run the same `--test-set-key`. Only re-run `uip tm testcases add --labels` if new tests should join.
- **A stored Playwright project selection survives** too, so the re-run stays scoped.

**Confirming the new package actually ran:** the test case logs carry `TestCaseVersion`, so after the re-run

```bash
uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
```

reports the version you just packed (`1.0.1`). That is the reliable check — `list-automations` shows a two-component `PackageVersion` (`1.0`) that cannot distinguish 1.0.1 from 1.0.0. Ingestion of an update is otherwise invisible (same count, same names), so allow ~60–90 s after the upload before re-running; an old `TestCaseVersion` in the results means a stale package, not a bad fix.
