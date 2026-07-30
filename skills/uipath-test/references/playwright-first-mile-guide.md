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
uip tm testsets run [--playwright-projects <names...>] → execute on serverless
uip tm wait / report / result        → outcome
```

The key difference from the RPA pipeline: there is **no link step**. Uploading the package is enough — ingestion creates one Test Manager test case per discovered Playwright test, already bound to the package, and labels each with:

- `PW_Tag_<tag>` — one per Playwright tag (`@smoke` → `PW_Tag_smoke`)
- `PW_Project_<name>` — one per Playwright project the test runs in
- `PW_Suite_<name>` / `PW_Path_<chain>` — describe-block grouping (name and full chain)
- `PW_File_<path>` — the spec file

> **Do NOT run `uip tm testcases link-automation` on Playwright test cases.** They are linked by ingestion; manual linking is the RPA pipeline and will corrupt the association.

> **Availability gate — check this first.** The external-package commands are newer than most installed CLIs. Run `uip tm pack --help --output json`: if it exposes no `--type` option, this pipeline is not available on this CLI — tell the user and stop rather than improvising. Step 5's probe is optional: if `testsets playwright-context` answers `unknown command`, skip it and carry on — its absence says nothing about project scoping. Only if `run --playwright-projects` itself is rejected (`unknown option`) is scoping unavailable in this build; then run the test set without it rather than retrying.

## Prerequisites

- A recent `@uipath/cli` — this flow's commands (`tm pack --type playwright`, `testcases add --labels`, `testsets playwright-context`, `run --playwright-projects`) do not exist on older CLIs and have no pre-rename fallback. If `uip tm pack --help` does not show `--type`, upgrade the CLI before anything else.
- Logged in: `uip login status --output json`. If not, `uip login`.
- A Test Manager project to land the test cases in: `uip tm project list --filter <name> --output json`, or `uip tm project create --name <NAME> --project-key <PROJECT_KEY> --output json`. Capture the project key.
- Trust `Status: "Logged in"` from `uip login status` — its `ExpirationDate` can read stale while calls succeed; if calls do 401, `uip login refresh`.
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

Each re-upload needs a **new `--package-version`** at pack time — Orchestrator feeds reject an existing version.

## Step 3 — Wait for ingestion

Ingestion is asynchronous and automatic. Poll until the auto-created test cases appear:

```bash
uip tm testcases list --project-key <PROJECT_KEY> --output json
```

- Poll **unfiltered** and count. Do NOT pass `--filter <PackageName>` — the auto-created test case *names* are `"<suite> > <test title>"`; the package name appears only in the description, which `--filter` does not search, so a package-name filter stays empty forever and reads as a false "ingestion never happened".
- In a project that already holds test cases, take a **baseline count before Step 2** and wait for it to grow by `TestCount` — an absolute count can look satisfied by pre-existing rows (or time out on a large paginated list). New rows are also recognizable by their `"<suite> > <title>"` names and package description.
- Expect exactly `TestCount` new test cases (from Step 1), typically within 1–2 minutes. `TestCount` is one per Playwright **test**, NOT multiplied by the number of Playwright projects (2 tests × 2 projects → 2 test cases).
- Ingested test cases show `IsAutomated: false` in list output — that is normal and does not mean ingestion failed; the package linkage is real (their execution logs carry `HasLinkedAutomation: true` and Orchestrator job keys).
- Poll every ~10 seconds, up to ~3 minutes. If nothing appears by then, STOP and report — the likely causes are the Playwright feature flag being off for the tenant or a wrong `--project-key`; both need the user, not retries.
- Spot-check the labels landed: `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type TestCase --filter PW_ --output json` (returns distinct label *names* only — enough to confirm ingestion labeled things, not which test case carries which label).

## Step 4 — Set the default folder, create a test set, fill it by label

Set the project's default Orchestrator folder FIRST — both the Step 5 probe and the Step 6 run resolve packages through it (Critical Rule #10):

```bash
uip or folders list --output json    # WITHOUT --all: only folders you are a member of
uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json
```

- Pick the folder from the **unflagged** `folders list` — `--all` returns every folder *visible* to you, including ones where you have no rights; choosing one of those fails later with `folderNotFoundOrNoAccess`.
- **The folder must have a Cloud Robots – Serverless machine assigned** or the run's job creation 500s and the execution is instantly `Cancelled`. Check with `uip or machines list --folder-key <FOLDER_KEY> --output json`; if none, create and assign one (one serverless machine per folder):

```bash
uip or machines create -n <name> --serverless --testing-slots 2 --output json   # capture Data.Key
uip or machines assign <MACHINE_KEY> --folder-key <FOLDER_KEY> --output json    # takes machine KEYS (GUIDs), not names
```

```bash
uip tm testsets create --project-key <PROJECT_KEY> --name "PW Smoke" --output json
uip tm testcases add --test-set-key <TEST_SET_KEY> --labels "PW_Suite_<name>" --output json
```

- Capture `TestSetKey` from the create output (e.g. `DEMO:10`).
- `--labels` is variadic and space-separated (quote names that contain spaces). Matching is **OR across labels, exact, and case-sensitive** — discover the real names first with `uip tm objectlabel list` rather than guessing.
- `--labels` works with any object label; the `PW_*` labels are simply what ingestion applies.
- Mutually exclusive with `--test-case-keys`; pass exactly one of the two.
- To run the whole suite on one browser: fill by a suite/file label (`PW_Suite_*` or `PW_File_*`) and pass the browser to `--playwright-projects` in Step 6. Filling by `PW_Project_<name>` is for selecting the subset of tests that participate in that project — it does not restrict which browsers run.
- **Labels select *tests*; `--playwright-projects` selects *browsers*.** Filling by `PW_Project_firefox` picks every test that runs in the firefox project (often all of them); it does not make the run firefox-only — that is what the run flag in Step 6 does. To "run only <project>", label-fill by whatever identifies the tests you want (tag, suite, file) and pass the project name to `--playwright-projects`.
- **Keep one test set = one Playwright package.** Per-project selection (Step 6) requires every test case in the set to come from a single Playwright package; label-filling across packages produces a set that cannot be project-scoped. Labels are NOT package-qualified — in a project holding several Playwright packages, a generic label like `PW_Tag_smoke` matches tests from all of them. There, fill by a package-unique label (`PW_File_<path>`, or a suite name unique to the package) or by explicit `--test-case-keys` from the current ingestion.

## Step 5 — Probe the Playwright context (when available)

Before deciding whether `--playwright-projects` applies, ask the server:

```bash
uip tm testsets playwright-context --test-set-key <TEST_SET_KEY> --output json
```

- `Data.IsPlaywright: true` → the set resolves to one Playwright package; `AvailablePlaywrightProjects` holds the only valid `--playwright-projects` values, and `SelectedPlaywrightProjects` shows any selection already stored on the test set. Both are **comma-joined strings** (`"chromium, firefox"`), not arrays — split on `", "` when scripting; no stored selection is `""`.
- `Data.IsPlaywright: false` → RPA, mixed, manual, or multi-package test set — run it **without** `--playwright-projects`.
- The server never errors on type here, so this is the safe discriminator for automation: probe first, branch on `IsPlaywright`.
- **False negative without a folder:** the probe resolves the package through the project's default folder — if that isn't set (Step 4), a genuine Playwright test set reports `IsPlaywright: false`. Set the default folder before trusting a `false`.

## Step 6 — Run, optionally per Playwright project

```bash
uip tm testsets run --test-set-key <TEST_SET_KEY> \
    --playwright-projects chromium firefox --wait --output json
```

`--playwright-projects` semantics (all enforced with clear errors, nothing is silently ignored):

- Space-separated, case-sensitive names from the package's `playwright.config`. Unknown names **fail fast, before anything is persisted**, listing the available projects.
- Valid only when every test case in the set comes from one single Playwright package (see Step 4); fails for Studio/RPA test sets — run those without the flag.
- The selection **persists on the test set** and applies to later runs until changed; omit the flag to reuse the stored selection (or the config's defaults if none was ever stored).
- On a Test Manager without Playwright support the command fails with instructions rather than running incorrectly.

Omit `--playwright-projects` entirely for a plain run (all config-default projects).

**Getting the execution id.** Start the run **without** `--wait`: it returns a complete JSON envelope immediately, carrying `ExecutionId` and `Status: Pending` — the cleanest handle for automation. With `--wait` the envelope only arrives at terminal state, so take the id from the `Execution started: <id> (Pending)` progress line — not from `Starting execution for test set …`, whose UUID is the *test set*.

**Agent-friendly waiting:** a single `--wait` call can sit silent for many minutes, which trips agent-harness watchdogs and shell timeouts. When running as an agent, prefer starting the run **without** `--wait`, then poll in bounded chunks: `uip tm wait --execution-id <EXECUTION_ID> --timeout 120 --output json` in a loop (or `uip tm executions get-stats` every 30–60 s), so every call returns quickly and progress stays visible. A `wait` that hits its `--timeout` returns a Failure envelope with `Retry: "RetryWillNotFix"` — for a non-terminal execution that just means "still running"; keep polling, don't treat it as fatal.

## Step 7 — Results

- `--wait` on the run blocks until terminal; without it, use `uip tm wait --execution-id <EXECUTION_ID> --output json`.
- Summary: `uip tm report get --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json` (`--project-key` or `--test-set-key` is required — bare `--execution-id` exits with "Provide --project-key or --test-set-key").
- Per-test detail: `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json`.
- JUnit export: `uip tm result download --execution-id <EXECUTION_ID> --result-path <dir> --output json`.

Execution happens on UiPath serverless cloud runtimes — no robot or package deployment into the folder is needed beyond the upload in Step 2, but the folder does need its serverless machine assignment (Step 4).

### When a run produces no results

Three shapes, one rule: diagnose with the two commands below, then stop — retrying doesn't fix any of them.

- **`Cancelled` within seconds**, logs pointing at `CreateTestAutomationJobs` / `InternalServerError` → the default folder has no serverless machine assigned (Step 4).
- **`Finished` with `Passed: 0 / Failed: 0 / None: N`** → the run ended without per-test results reaching Test Manager; the test case log's `Info` carries the reason (results upload failed, or the job never started). Note `report get` counts `None` as **`Skipped`**, so 0% here means "results lost", not "tests skipped".
- **Stuck `Pending`** → dispatch worked but nothing is executing. A faulted job may never sync back, so don't sit out the 30-minute wait; check after ~5 minutes.

```bash
uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json
uip or jobs list --folder-key <FOLDER_KEY> --output json
```

A `Duration` of `00:00:00` and an empty `StartTime` on an already-finished execution are normal — not evidence of a broken run. `JobKey` values on the logs prove Test Manager dispatched; jobs `Faulted` with no host machine mean the tenant can't run them. Either way it needs the platform team — report it rather than re-running (there is no CLI verb to cancel a Test Manager execution).

## Iterating on the suite (and getting a fix back in)

Changing a test — including fixing one the run just failed — uses the same pipeline with a bumped version:

```bash
uip tm pack --project-path <dir> --type playwright --project-key <PROJECT_KEY> --name <PackageName> --package-version 1.0.1 -o <out-dir> --output json
uip or packages upload "<out-dir>/<PackageName>.1.0.1.nupkg" --output json
```

The version **must** be new — the Orchestrator feed rejects one it already has (Step 2). Ingestion then **updates** the existing test cases in place (matched per test), creates any new ones, and unlinks removed ones, so:

- **A test set keeps its membership** when the test list is unchanged — nothing to re-add, no new test set, re-run the same `--test-set-key`. Only re-run `uip tm testcases add --labels` if new tests should join.
- **A stored Playwright project selection survives** too, so the re-run stays scoped.

**Verifying the update landed is the weak spot.** On a first upload you count new test cases; on an update nothing observably moves — the count and names are identical, and `uip tm testcases list-automations` reports a two-component `PackageVersion` (`1.0`), which cannot distinguish 1.0.1 from 1.0.0. There is no CLI confirmation today, so: wait ~60–90 s after the upload, then re-run and read the results. If the re-run reproduces the *previous* failure verbatim, suspect a stale package rather than a bad fix — re-check that the upload succeeded and that you bumped the version.
