---
name: uipath-test
description: "UiPath Test Manager — manage test projects, cases, sets, executions, and run performance scenarios (load groups, dry runs); generate reports. For Orchestrator→uipath-platform. For test automation→uipath-rpa."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Test Assistant

> **Preview** — skill is under active development; surface and behavior may change.

Manage UiPath Test Manager resources (projects, test cases, test sets, executions) and generate persona-tailored shareable test reports.

## When to Use This Skill

- User wants to **list, create, update, delete** Test Manager projects, test cases, test sets, or executions
- User wants to **view or analyse** test execution results
- User wants to **generate a shareable test report** tailored to a QA engineer, developer, or release manager
- User asks about **test coverage, regression trends, or failure rates**
- User needs a **go/no-go decision summary** based on recent test executions
- User mentions **performance scenarios, load groups, dry runs, scenario executions, p95/p99 latency, SLO violations,** or wants to **load test** an existing test case

## Concepts
### What is Testmanager?

UiPath Testmanager is a web application that manages the testing lifecycle of projects, enabling requirements traceability, test planning, and reporting. Its key business objects are:

- **Requirements** — Defines what needs to be tested.
- **Testcases** — Defines the scenarios to be tested
- **Testsets** — Groups of test cases for execution
- **Test executions** — Defining triggers and schedules for unattended execution
- **Testcaselogs** — Logs of a tescase in a execution.
- **Testcaselog assertions** — Assertion steps of a testcaselog in a execution.
- **Performance scenarios** — Reusable load test definitions composed of one or more load groups.
- **Load groups** — A bound test case + load profile (virtual users, ramp-up / peak / ramp-down) attached to a scenario. One scenario can have many.
- **Scenario executions** — A scheduled run of a scenario; produces cumulative metrics, per-second time series, application logs, and SLO violation reasons.

CLI tool for UiPath Test Manager (`uip tm`). Use `uip tm --help` and `uip tm <command> <option> --help` to discover all commands and options. **Always pass `--output json`** on every `uip` command (see Critical Rule #2).
Common `uip tm` (Test Manager) commands organized by resource type:

### Project Commands

| Command | Purpose |
|---|---|
| `uip tm project list --filter <NAME_OR_KEY>` | Find a project by name or key. |
| `uip tm project create --name <PROJECT_NAME> --project-key <PROJECT_KEY>` | Create a new Test Manager project. |
| `uip tm project update --project-key <PROJECT_KEY> --name <PROJECT_NAME>` | Update project name or description. |
| `uip tm project delete --project-key <PROJECT_KEY>` | Delete a Test Manager project. |
| `uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` | Set the default Orchestrator folder for a project. |
| `uip tm project clear-default-folder --project-key <PROJECT_KEY>` | Clear the default Orchestrator folder from a project. |

> Get folder keys with `uip or folders list --output json` — returns folders the current user has access to (personal workspace + assigned folders). Use `--all` to enumerate every folder in the tenant.

### TestCase Commands

| Command | Purpose |
|---|---|
| `uip tm testcase create --project-key <PROJECT_KEY> --name <TEST_CASE_NAME>` | Create a new test case in a Test Manager project. |
| `uip tm testcase list --project-key <PROJECT_KEY>` | List all test cases in a Test Manager project. |
| `uip tm testcase update --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --name <TEST_CASE_NAME>` | Update a test case name or description (at least one of `--name` or `--description` required). |
| `uip tm testcase delete --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Delete a test case by its key. |
| `uip tm testcase link-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME> --test-name <TEST_NAME>` | Link an Orchestrator package automation to a test case. |
| `uip tm testcase unlink-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Unlink the automation from a test case. |
| `uip tm testcase list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` | List test entry points available in an Orchestrator folder (optional: `--package-name <PACKAGE_NAME>` to filter). |
| `uip tm testcase list-testsets --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | List test sets that contain a given test case. |
| `uip tm testcase list-steps --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List test steps for a test case. **Uses `--test-case-id <UUID>`, not `--test-case-key`.** |
| `uip tm testcase list-result-history --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List testcase log result history for a specific test case. |
| `uip tm testcase execute --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID> --execution-type <TYPE>` | Start an execution for one or more test cases. **Uses `--test-case-id <UUID>` (space-separated for multiple), not `--test-case-key`.** |

> Get a test case UUID with `uip tm testcase list --project-key <PROJECT_KEY> --output json` and read the `Id` field. The `--test-case-id` flag requires a UUID; the `--test-case-key` flag (used by `update`, `delete`, `link-automation`, `unlink-automation`, `list-testsets`) requires the `PROJECT_KEY:NUMBER` form (e.g., `DEMO:1`). Do not interchange them.

### TestSet Commands

| Command | Purpose |
|---|---|
| `uip tm testset create --project-key <PROJECT_KEY> --name <TEST_SET_NAME>` | Create a new test set in a Test Manager project. |
| `uip tm testset list --project-key <PROJECT_KEY>` | List test sets in a Test Manager project. |
| `uip tm testset update --test-set-key <TEST_SET_KEY> --name <TEST_SET_NAME>` | Update a test set name or description. |
| `uip tm testset delete --test-set-key <TEST_SET_KEY>` | Delete a test set by its key. |
| `uip tm testset add-testcases --test-set-key <TEST_SET_KEY> --test-case-keys <TEST_CASE_KEYS>` | Add test cases to a test set. |
| `uip tm testset remove-testcases --test-set-key <TEST_SET_KEY> --test-case-keys <TEST_CASE_KEYS>` | Remove test cases from a test set. |
| `uip tm testset list-testcases --test-set-key <TEST_SET_KEY>` | List test cases assigned to a test set. |
| `uip tm testset execute --test-set-key <TEST_SET_KEY>` | Execute a test set and return the execution ID. |

> Keys use the format `PROJECT_KEY:NUMBER` (e.g., `INV:42`).

### Execution Commands

| Command | Purpose |
|---|---|
| `uip tm execution retry --execution-id <EXECUTION_ID>` | Retry only the failed test cases of a finished execution. |
| `uip tm execution list --project-key <PROJECT_KEY> --test-set-id <TEST_SET_ID>` | List top n executions for a test set. |
| `uip tm execution list-testcaselogs --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | List test case logs of an execution. |

### Testcaselog Commands

| Command | Purpose |
|---|---|
| `uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID>` | List assertions of a testcase log. |

### Report Commands

| Command | Purpose |
|---|---|
| `uip tm report get --execution-id <EXECUTION_ID>` | Get a summary report for a completed test execution. |

### Attachment Commands

| Command | Purpose |
|---|---|
| `uip tm attachment download --execution-id <EXECUTION_ID>` | Download attachments for test cases in an execution. |

### Result Commands

| Command | Purpose |
|---|---|
| `uip tm result download --execution-id <EXECUTION_ID>` | Download test execution results as JUnit XML. |

### Wait Commands

| Command | Purpose |
|---|---|
| `uip tm wait --execution-id <EXECUTION_ID>` | Wait for a test execution to reach a terminal state. |

### Scenario Commands (Performance Testing)

| Command | Purpose |
|---|---|
| `uip tm scenario create --project-key <PROJECT_KEY> --name <NAME>` | Create a performance scenario. Returns `ScenarioKey` (`PROJECT_KEY:NUMBER`). |
| `uip tm scenario get --scenario-key <SCENARIO_KEY>` | Scenario metadata + every load group bound to it. Project is derived from the scenario-key prefix — **no `--project-key` flag**. |
| `uip tm scenario add-testcase --scenario-key <SCENARIO_KEY> --test-case-key <TEST_CASE_KEY> --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME>` | Attach a test case as a load group. **Omit `--package-version`** to auto-resolve the latest published version (preferred). Optional load-profile flags: `--virtual-users`, `--ramp-up-minutes`, `--peak-minutes`, `--ramp-down-minutes`, `--max-response-time-ms`, `--max-error-rate`. |
| `uip tm scenario execute --scenario-key <SCENARIO_KEY> --wait` | Kick off a run. With `--wait` the CLI polls until terminal (`Finished`/`Cancelled`/`Faulted`) and emits the same shape as `execution-results`. Tune the loop with `--poll-interval-sec` (default `12`) and `--timeout-sec` (default `1800`). Use `--execution-type performanceTesting` for a full load run honouring the load-profile flags on each load group; default is `dryRun` (fast smoke). |
| `uip tm scenario execution-results --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | Re-fetch results for any past `ExecutionId`. Add `--full` to include the per-second time series under each load group (`AggregatedData[]`). Default payload is ~6 KB; `--full` is ~50 KB. |
| `uip tm scenario transaction-metrics --load-group-id <LOAD_GROUP_ID> --project-key <PROJECT_KEY>` | Per-transaction (per-API call) metrics for one load-group execution: `avg/min/max/p50/p90/p95/p99 ResponseTimeMs`, `RequestCount`, `HttpErrorCount/Rate`. Use the `LoadGroupId` from `scenario execute` / `execution-results`. Optional `--start-time-ms <N>` / `--end-time-ms <N>` window. **Only returns rows when `AppType=api`.** For `web` / `desktop` scenarios the endpoint returns `200 OK` with `Transactions: []` (no API-level transactions exist — those scenarios are UI-driven). |
| `uip tm scenario update-loadgroup --load-group-id <LOAD_GROUP_ID> --project-key <PROJECT_KEY> [--virtual-users <n>] [--ramp-up-minutes <n>] [--peak-minutes <n>] [--ramp-down-minutes <n>] [--delay-minutes <n>] [--max-response-time-ms <ms>] [--max-error-rate <rate>] [--multiplexing-factor <n>] [--robot-type <type>] [--enabled <bool>]` | Update one load group's load profile in place. Use **between** a passing dry run and a full `performanceTesting` run to dial in the real load (apply the dry run's `Recommended multiplexing factor: N` here). True partial update — flags you omit are preserved from current server state. |
| `uip tm scenario stop --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | Cancel a running scenario execution. Use when a long full-load run needs to be aborted — including from a **separate terminal** while `scenario execute --wait` is still polling in the main session. Server acknowledges the cancel; confirm with `execution-results` (terminal status = `Cancelled`). |
| `uip tm scenario list-dry-run-reports --scenario-key <SCENARIO_KEY>` | Check whether a passing dry-run report already exists for the scenario. Use **before** submitting `performanceTesting` on an existing scenario to decide whether a fresh dry run is needed. `Data.HasPassingDryRun: true` → skip the dry run. ⚠️ Requires the load group's test case to have an `automationId` (modern linkage). For test cases linked via the legacy `packageEntryPointUniqueId` flow, this command errors — fall back to the try-then-fallback pattern (attempt `performanceTesting`, run dry run on rejection). |

> **Required scopes**: granular `TM.*` set + `TM.PerformanceScenarios`, `TM.PerformanceScenarioExecutions`, `PerfService`. If `uip login` was performed before these were added to the CLI, run `uip logout && uip login` to refresh the token.
>
> **Prefer `--wait` over a hand-rolled poll loop.** The CLI handles backoff, status-change deduping, and tenant-feed fallback for you.
>
> **BUT — for long full-load runs (`peak-minutes > 5` or expected total > 10 min), kick off WITHOUT `--wait`** and instead give the user the `ExecutionId` plus the two follow-up commands. Reason: `--wait` is a synchronous blocking call inside Claude Code's Bash tool — while it polls, the agent cannot read new user input, so the user can't cancel, ask a side question, or check status from the same session. Pattern:
> ```bash
> # 1. Kick off without --wait (returns immediately with ExecutionId)
> uip tm scenario execute --scenario-key <KEY> --execution-type performanceTesting --output json
> # 2. Tell user: ExecutionId, plus how to check / how to cancel
> #    Check: uip tm scenario execution-results --execution-id <ID> --project-key <KEY> --output json
> #    Cancel: uip tm scenario stop --execution-id <ID> --project-key <KEY>
> ```
> Use `--wait` only for fast runs (dry runs, short peaks ≤ 5 min) where blocking the agent for that duration is acceptable.
>
> **Dry run vs. full — two distinct phases with different rules:**
> - **`dryRun` ignores the load profile.** Always 1 VU with a fixed short profile; server probes the automation and emits `Recommended multiplexing factor: N`. `--virtual-users`, `--ramp-up-minutes`, `--peak-minutes`, `--ramp-down-minutes`, SLO thresholds — all ignored. Don't ask the user about these before a dry run; don't `update-loadgroup` before a dry run.
> - **`performanceTesting` honours the load profile.** Requires a passing dry run on file. This is when the load-profile values matter.
>
> **Full execution requires a prior successful dry run — but treat new-vs-existing scenarios differently:**
> - **Scenario / load group was just created this turn** → dry run doesn't exist yet → run `--execution-type dryRun --wait` first, then full.
> - **User gave you an existing `<SCENARIO_KEY>` (or scenario has load groups attached from a prior session)** → assume a dry run already ran. **Try `performanceTesting` directly.** Only if the server rejects with HTTP 400 *"No dry run reports found"* should you fall back to dry-run + retry. Don't burn a dry run pre-emptively against the user's explicit "run a full perf test" intent.
> - When unsure, call `scenario list-dry-run-reports --scenario-key <KEY>` to check before deciding.
>
> **`create` + `add-testcase` + `execute` are independent — don't fuse them.** When the user supplies a `<SCENARIO_KEY>` (e.g. `SP1:1276`), or refers to a scenario you already created earlier in the conversation, **jump straight to `execute`**. Run `scenario get --scenario-key <KEY>` first to confirm load groups are attached; only call `create` / `add-testcase` if the scenario doesn't exist or has zero load groups. See [references/perf-scenario-guide.md § Reuse vs. create](references/perf-scenario-guide.md).
>
> **Confirm the load profile with the user BEFORE the full run — NOT before the dry run.** Server-side stored defaults drift (`VirtualUsers=20`, `MaxErrorRate=1.0` have been observed in the wild regardless of what the CLI sent). Required pre-flight sequence *before `performanceTesting`*: (1) `scenario get` → read the current load profile, (2) ask the user to confirm/override each of `virtual-users`, `ramp-up-minutes`, `peak-minutes`, `ramp-down-minutes`, `delay-minutes`, `max-response-time-ms`, `max-error-rate`, `multiplexing-factor` for **every** load group, (3) apply via `scenario update-loadgroup`, (4) THEN submit `performanceTesting`. Use the dry run's `Recommended multiplexing factor: N` as the suggested value when asking. **Skip this step entirely for dry runs** — those values don't apply there.

## Critical Rules

1. **Always check login first** — run `uip login status --output json` before any Test Manager operation. Use `uip login`.
2. **Always pass `--output json`** to every `uip` command — no exceptions. Structured JSON output is what you need to reason about results reliably, even when you only plan to summarize them back to the user.
3. **Cap retries at 3** for any failing API call. After 3 failures, stop and report the error to the user.
4. **Handle empty results** — if a list command returns an empty array, stop and inform the user rather than proceeding with a null key.
5. **Confirm before delete** — always confirm the target resource key with the user before running any `delete` command.
6. **For operations requiring folder key** — use `uip or folders list --output json` (run `/uipath-platform` for folder management details).
7. **Discover before assuming** — never guess automation names, folder keys, project IDs, or test case keys. Always run the matching `list` command first (e.g., `uip tm testcase list-automations`, `uip or folders list-current-user`).

## Quick Start

### Verify authentication
   ```bash
   uip login status --output json
   ```
   If not authenticated, run `uip login` to sign in.

   **Set the active tenant** (if needed)
   ```bash
   uip login tenant set <TENANT_NAME> --output json
   ```
  For more authentication details, run `/uipath-platform`.

```bash

  # Get project
  uip tm project list --filter <PROJECT_NAME_OR_KEY> --output json

  # Get testset
  uip tm testset list --project-key <PROJECT_KEY> --filter <TEST_SET_NAME_OR_KEY> --output json

  # Get testcases in a testset
  uip tm testset list-testcases --test-set-key <TEST_SET_KEY> --output json

  # Get testexecution
  uip tm execution list --project-key <PROJECT_KEY> --test-set-id <TEST_SET_ID> --top 100 --output json

  # Get testcaselogs in a testexecution
  uip tm execution list-testcaselogs --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json

  # Get testcaselog assertions of a testcaselogs
  uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID> --output json
```

```bash
  # Run a perf scenario end-to-end (--wait flow)

  # 1. Create the scenario
  uip tm scenario create --project-key <PROJECT_KEY> --name "<SCENARIO_NAME>" --output json
  # capture ScenarioKey from .Data.ScenarioKey

  # 2. Discover folder + automation (cross-link: see references/publish-and-link-guide.md)
  uip or folders list --output json
  uip tm testcase list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json

  # 3. Attach the test case as a load group (omit --package-version to auto-resolve latest)
  uip tm scenario add-testcase --scenario-key <SCENARIO_KEY> --test-case-key <TEST_CASE_KEY> \
    --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME> --output json

  # 4. Execute + wait until terminal (preferred over hand-rolling a poll loop)
  uip tm scenario execute --scenario-key <SCENARIO_KEY> --wait --output json

  # 5. (Optional) Re-fetch with the per-second time series for a Performance Engineer report
  uip tm scenario execution-results --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --full --output json
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` on REST API | `uip login` to re-authenticate. |
| `HTTP 400: Insufficient Performance Testing runtimes available in the folder 'X'. Required: 1, Available: 0.` | A perf-testing runtime is busy or not allocated. Wait for an in-flight scenario to release one, or have an admin allocate more in that Orchestrator folder. |
| `HTTP 404: Performance Testing Scenario Test Case Configurations does not exist.` | You called `scenario execute` without first attaching a load group. Run `scenario add-testcase` first, then re-execute. |
| `HTTP 409 Conflict: This automation is already linked to a different Test Case` | The package + entry point is already linked to another test case in the project. Pick a different test case, or unlink the existing one first. |

> If a command fails unexpectedly:
> 1. Verify the command syntax: `uip tm <command> --help`
> 2. Check authentication: `uip login status --output json`

## Navigate to a workflow

| I want to... | Start here |
|---|---|
| **Generate a shareable test report** (tester or release manager view) | [references/test-result-report-guide.md](references/test-result-report-guide.md) |
| **Publish a project and link it to a Test Manager test case** | [references/publish-and-link-guide.md](references/publish-and-link-guide.md) |
| **Run a performance scenario end-to-end** (create → load group → execute → persona-tailored perf report) | [references/perf-scenario-guide.md](references/perf-scenario-guide.md) |


## Anti-patterns

- **Do NOT proceed if authentication fails** — all Test Manager API calls require a valid bearer token. Fail fast rather than surfacing confusing 401 errors later.
- **Do NOT guess command names — verb-noun composites are required.** The CLI uses explicit verb-noun forms; bare verbs do not exist. Always run `uip tm <resource> --help` to confirm. Common landmines:
  - `uip tm testcase link` ❌ → `uip tm testcase link-automation` ✓
  - `uip tm testcase unlink` ❌ → `uip tm testcase unlink-automation` ✓
  - `uip tm execution wait` ❌ → `uip tm wait` ✓ (top-level under `tm`, not `execution`)
  - `uip tm scenario run` ❌ → `uip tm scenario execute` ✓
- **Do NOT hand-roll a polling loop for `scenario execute`** — pass `--wait` (with `--poll-interval-sec` / `--timeout-sec` if defaults don't fit). The CLI dedupes status-change events and surfaces every application-log message; reimplementing it in the agent loses fidelity.
- **Do NOT pin `--package-version`** unless the user explicitly asked for a specific version. Omit the flag and let `add-testcase` auto-resolve to the latest published version in the folder.
- **Do NOT use `--full` for a Release Manager report** — the per-second time series is noise for a go/no-go audience. `--full` is for Performance Engineers who need p95 / p99 / cpu / ram timelines.
- **Do NOT recompute cumulative metrics from `AggregatedData[]`.** The server already does the math in `CumulativeResponseTimeMs`, `SuccessfulWorkflowCount`, `FailedWorkflowCount`, `HttpErrorRate`, `AutomationErrorRate` — read those fields directly.
- **Do NOT pre-emptively run a dry run when the user explicitly asked for a full perf test on an existing scenario.** Existing scenarios usually have a passing dry run on file from a prior session — try `performanceTesting` directly and only fall back to dry-run-first if the server rejects with HTTP 400 *"No dry run reports found"*. Pre-emptive dry-runs waste the user's time and burn perf runtimes. The "dry run first" rule applies ONLY to scenarios / load groups you just created this turn (where a dry run obviously can't exist yet).
- **Do NOT ask the user about load profile params before a dry run.** `dryRun` ignores `virtual-users`, `ramp-up-minutes`, `peak-minutes`, `ramp-down-minutes`, and SLO thresholds — those values only matter for `performanceTesting`. Ask AFTER the dry run completes, BEFORE submitting the full run.
- **Do NOT call `scenario update-loadgroup` before a dry run** for the same reason — the load-profile values you'd set don't take effect there. Update happens between dry run and full run.
- **Do NOT call `scenario create` + `scenario add-testcase` when a scenario already exists.** When the user supplies a scenario key, OR refers to a scenario from earlier in the conversation, OR a `scenario get` shows `LoadGroupCount >= 1`, the scenario is ready — jump directly to `scenario execute`. Creating a duplicate scenario every run is wasteful and clutters Test Manager.
- **Do NOT submit `--execution-type performanceTesting` without first confirming the load profile with the user.** The CLI's `add-testcase` defaults (`VU=1`, `peak=1m`) and the perf service's stored defaults are not necessarily what the user wants for a real load run. Always `scenario get` → present the current profile → ask the user → `scenario update-loadgroup` if changes are needed → then execute. Trusting server-side stored defaults for a full run is reckless.