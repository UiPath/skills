---
name: uipath-test
description: "UiPath Test Manager — manage test projects, cases, sets, executions; generate reports. For Orchestrator→uipath-platform. For test automation→uipath-rpa."
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

## Concepts
### What is Testmanager?

UiPath Testmanager is a web application that manages the testing lifecycle of projects, enabling requirements traceability, test planning, and reporting. Its key business objects are:

- **Requirements** — Defines what needs to be tested.
- **Testcases** — Defines the scenarios to be tested
- **Testsets** — Groups of test cases for execution
- **Test executions** — Defining triggers and schedules for unattended execution
- **Testcaselogs** — Logs of a tescase in a execution.
- **Testcaselog assertions** — Assertion steps of a testcaselog in a execution.

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

> Get folder keys with `uip or folders list-current-user --output json` — returns all folders visible to the current user. Prefer it over `uip or folders list`, which is a narrower view and may miss folders the user can access.

### TestCase Commands

| Command | Purpose |
|---|---|
| `uip tm testcases create --project-key <PROJECT_KEY> --name <TEST_CASE_NAME>` | Create a new test case in a Test Manager project. |
| `uip tm testcases list --project-key <PROJECT_KEY>` | List all test cases in a Test Manager project. |
| `uip tm testcases update --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --name <TEST_CASE_NAME>` | Update a test case name or description (at least one of `--name` or `--description` required). |
| `uip tm testcases delete --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Delete a test case by its key. |
| `uip tm testcases link-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME> --test-name <TEST_NAME>` | Link an Orchestrator package automation to a test case. |
| `uip tm testcases unlink-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Unlink the automation from a test case. |
| `uip tm testcases list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` | List test entry points available in an Orchestrator folder (optional: `--package-name <PACKAGE_NAME>` to filter). |
| `uip tm testcases list-testsets --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | List test sets that contain a given test case. |
| `uip tm testcases list-steps --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List test steps for a test case. **Uses `--test-case-id <UUID>`, not `--test-case-key`.** |
| `uip tm testcases list-result-history --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List testcase log result history for a specific test case. |
| `uip tm testcases run --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID> --execution-type <TYPE>` | Run a new execution for one or more test cases. **Uses `--test-case-id <UUID>` (space-separated for multiple), not `--test-case-key`.** |
| `uip tm testcases add --test-set-key <TEST_SET_KEY> --test-case-keys <TEST_CASE_KEYS>` | Add test cases to a test set. |
| `uip tm testcases remove --test-set-key <TEST_SET_KEY> --test-case-keys <TEST_CASE_KEYS>` | Remove test cases from a test set. |

> Get a test case UUID with `uip tm testcases list --project-key <PROJECT_KEY> --output json` and read the `Id` field. The `--test-case-id` flag requires a UUID; the `--test-case-key` flag (used by `update`, `delete`, `link-automation`, `unlink-automation`, `list-testsets`) requires the `PROJECT_KEY:NUMBER` form (e.g., `DEMO:1`). Do not interchange them.

### TestSet Commands

| Command | Purpose |
|---|---|
| `uip tm testsets create --project-key <PROJECT_KEY> --name <TEST_SET_NAME>` | Create a new test set in a Test Manager project. |
| `uip tm testsets list --project-key <PROJECT_KEY>` | List test sets in a Test Manager project. |
| `uip tm testsets update --test-set-key <TEST_SET_KEY> --name <TEST_SET_NAME>` | Update a test set name or description. |
| `uip tm testsets delete --test-set-key <TEST_SET_KEY>` | Delete a test set by its key. |
| `uip tm testsets list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY>` | List test cases assigned to a test set. |
| `uip tm testsets run --test-set-key <TEST_SET_KEY>` | Run a test set and return the execution ID. |

> Adding/removing test cases to/from a test set lives under `testcases`, not `testsets`: `uip tm testcases add` / `uip tm testcases remove`.
> Keys use the format `PROJECT_KEY:NUMBER` (e.g., `INV:42`).

### Execution Commands

| Command | Purpose |
|---|---|
| `uip tm executions get-stats --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | Get a test execution with aggregated pass/fail/none stats. |
| `uip tm executions run --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --execution-type <TYPE>` | Re-run an existing test execution (optionally a subset via `--test-case-log-ids`). |
| `uip tm executions retry --execution-id <EXECUTION_ID>` | Retry only the failed test cases of a finished execution. |
| `uip tm executions list --project-key <PROJECT_KEY> [--test-set-id <TEST_SET_ID>]` | List top n executions for a project or a specific test set. |
| `uip tm executions list-filtered --project-key <PROJECT_KEY>` | List executions with full filter set (labels, status, interval, ids, order-by). |
| `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | List test case logs of an execution. |

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

## Critical Rules

1. **Always check login first** — run `uip login status --output json` before any Test Manager operation. Use `uip login`.
2. **Probe the CLI surface once per session, before the first `uip tm` command.** Run `uip tm testcases --help --output json` (any flags accepted). Result `Success` → post-rename CLI; use the command tables above as-is. `unknown command` / non-zero exit → pre-rename CLI; translate via the [Pre-rename fallbacks](#pre-rename-fallbacks) table before each call. Re-probe on any later `unknown command` error.
3. **Always pass `--output json`** to every `uip` command — no exceptions. Structured JSON output is what you need to reason about results reliably, even when you only plan to summarize them back to the user.
4. **Cap retries at 3** for any failing API call. After 3 failures, stop and report the error to the user.
5. **Handle empty results** — if a list command returns an empty array, stop and inform the user rather than proceeding with a null key.
6. **Confirm before delete** — always confirm the target resource key with the user before running any `delete` command.
7. **For operations requiring folder key** — use `uip or folders list-current-user --output json` (run `/uipath-platform` for folder management details).
8. **Discover before assuming** — never guess automation names, folder keys, project IDs, or test case keys. Always run the matching `list` command first (e.g., `uip tm testcases list-automations`, `uip or folders list-current-user`).

### Pre-rename fallbacks

If the probe in Rule #2 shows singular subjects, the CLI predates the closed-verb-set renames. Translate before running:

| Post-rename (tables above) | Pre-rename equivalent |
|---|---|
| `uip tm testcases <verb>` | `uip tm testcase <verb>` |
| `uip tm testsets <verb>` | `uip tm testset <verb>` |
| `uip tm executions <verb>` | `uip tm execution <verb>` |
| `uip tm testcases run` | `uip tm testcase execute` |
| `uip tm testsets run` | `uip tm testset execute` |
| `uip tm testcases add --test-set-key … --test-case-keys …` | `uip tm testset add-testcases --test-set-key … --test-case-keys …` |
| `uip tm testcases remove --test-set-key … --test-case-keys …` | `uip tm testset remove-testcases …` |
| `uip tm executions testcaselogs list` | `uip tm execution list-testcaselogs` |

`uip tm wait`, `tm testcaselog`, `tm report`, `tm result`, `tm attachment`, `tm project`, `tm user`, `tm requirement` are unchanged on both surfaces.

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
  uip tm testsets list --project-key <PROJECT_KEY> --filter <TEST_SET_NAME_OR_KEY> --output json

  # Get testcases in a testset
  uip tm testsets list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY> --output json

  # Get testexecution
  uip tm executions list --project-key <PROJECT_KEY> --test-set-id <TEST_SET_ID> --top 100 --output json

  # Get testcaselogs in a testexecution
  uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json

  # Get testcaselog assertions of a testcaselogs
  uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID> --output json
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` on REST API | `uip login` to re-authenticate. |

> If a command fails unexpectedly:
> 1. Verify the command syntax: `uip tm <command> --help`
> 2. Check authentication: `uip login status --output json`

## Navigate to a workflow

| I want to... | Start here |
|---|---|
| **Generate a shareable test report** (tester or release manager view) | [references/test-result-report-guide.md](references/test-result-report-guide.md) |
| **Publish a project and link it to a Test Manager test case** | [references/publish-and-link-guide.md](references/publish-and-link-guide.md) |


## Anti-patterns

- **Do NOT proceed if authentication fails** — all Test Manager API calls require a valid bearer token. Fail fast rather than surfacing confusing 401 errors later.
- **Do NOT skip the surface probe** (Critical Rule #2). On a pre-rename CLI, post-rename commands fail with `unknown command`; on a post-rename CLI, pre-rename commands fail the same way. The skill targets the post-rename surface and falls back per the [Pre-rename fallbacks](#pre-rename-fallbacks) table. Picking the wrong shape without probing burns a retry on every call.
- **Do NOT guess command names — verb-noun composites are required.** The CLI uses explicit verb-noun forms; bare verbs do not exist. Confirm with `uip tm <resource> --help --output json`. Common landmines:
  - `uip tm testcases link` ❌ → `uip tm testcases link-automation` ✓
  - `uip tm testcases unlink` ❌ → `uip tm testcases unlink-automation` ✓
  - `uip tm executions wait` ❌ → `uip tm wait` ✓ (top-level under `tm`, not `executions`)