---
name: uipath-test
description: "[PREVIEW] UiPath Test Manager — manage test projects, cases, sets, executions; generate reports. TRIGGER when: test ops, reports, results. DO NOT TRIGGER: Orchestrator → uipath-platform; test automation → uipath-rpa."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Test Assistant

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

CLI tool for UiPath Test Manager (`uip tm`). Use `uip tm --help` and `uip tm <command> <option> --help` to discover all commands and options. **Always use `--output json`** when calling commands programmatically.
Common `uip tm` (Test Manager) commands organized by resource type:

### Project Commands

| Command | Purpose |
|---|---|
| `uip tm project list --filter <NAME_OR_KEY>` | Find a project by name or key. |
| `uip tm project create --name <NAME> --project-key <KEY>` | Create a new Test Manager project. |
| `uip tm project set-default-folder --project-key <KEY> --folder-key <UUID>` | Set the default Orchestrator folder for a project. |

### TestCase Commands

| Command | Purpose |
|---|---|
| `uip tm testcase create --project-key <KEY> --name <NAME>` | Create a new test case in a Test Manager project. |
| `uip tm testcase list --project-key <KEY>` | List all test cases in a Test Manager project. |
| `uip tm testcase delete --project-key <KEY> --test-case-key <KEY>` | Delete a test case by its key. |
| `uip tm testcase link-automation --project-key <KEY> --test-case-key <KEY> --folder-key <UUID> --package-name <NAME> --test-name <NAME>` | Link an Orchestrator package automation to a test case. |
| `uip tm testcase update --project-key <KEY> --test-case-key <KEY>` | Update a test case name or description. |
| `uip tm testcase unlink-automation --project-key <KEY> --test-case-key <KEY>` | Unlink the automation from a test case. |
| `uip tm testcase list-automations --project-key <KEY> --folder-key <UUID>` | List test entry points available in an Orchestrator folder (use with link-automation). |
| `uip tm testcase list-result-history --project-key <KEY> --test-case-id <test-case-id>` | List testcase log result history for a specific test case. |

### TestSet Commands

| Command | Purpose |
|---|---|
| `uip tm testset create --project-key <KEY> --name <NAME>` | Create a new test set in a Test Manager project. |
| `uip tm testset delete --test-set-key <KEY>` | Delete a test set by its key. |
| `uip tm testset add-testcases --test-set-key <KEY> --test-case-keys <KEYS>` | Add test cases to a test set. |
| `uip tm testset update --test-set-key <KEY>` | Update a test set name or description. |
| `uip tm testset remove-testcases --test-set-key <KEY> --test-case-keys <KEYS>` | Remove test cases from a test set. |
| `uip tm testset list-testcases --test-set-key <KEY>` | List test cases assigned to a test set. |
| `uip tm testset execute --test-set-key <KEY>` | Execute a test set and return the execution ID. |
| `uip tm testset list --project-key <KEY>` | List test sets in a Test Manager project. |

### Execution Commands

| Command | Purpose |
|---|---|
| `uip tm execution retry --execution-id <UUID>` | Retry only the failed test cases of a finished execution. |
| `uip tm execution list --project-key <KEY> --test-set-id <UUID>` | List top n executions for a test set. |
| `uip tm execution list-testcaselogs --execution-id <testexecution-id> --project-key <project-key>` | List test case logs of an execution. |

### Testcaselog Commands

| Command | Purpose |
|---|---|
| `uip tm testcaselog list-assertions --project-key <project-key> --test-case-log-id <testcase-log-id>` | List assertions of a testcase log. |
  
### Report Commands

| Command | Purpose |
|---|---|
| `uip tm report get --execution-id <UUID>` | Get a summary report for a completed test execution. |

### Attachment Commands

| Command | Purpose |
|---|---|
| `uip tm attachment download --execution-id <UUID>` | Download attachments for test cases in an execution. |

### Result Commands

| Command | Purpose |
|---|---|
| `uip tm result download --execution-id <UUID>` | Download test execution results as JUnit XML. |

### Wait Commands

| Command | Purpose |
|---|---|
| `uip tm wait --execution-id <UUID>` | Wait for a test execution to reach a terminal state. |

## Critical Rules

1. **Always check login first** — run `uip login status --output json` before any Test Manager operation. Use `uip login`.
2. **Always use `--output json`** on every `uip` command whose output is parsed programmatically.
3. **Cap retries at 3** for any failing API call. After 3 failures, stop and report the error to the user.
4. **Handle empty results** — if a list command returns an empty array, stop and inform the user rather than proceeding with a null key.
5. **Confirm before delete** — always confirm the target resource key with the user before running any `delete` command.
6. **For operations requiring folder key** — use `uip folder list --output json` (run `/uipath-platform` for folder management details).

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
  uip tm project list --filter <project-name or project-key> --output json

  # Get testset
  uip tm testset list --project-key <project-key> --filter <test-set-name or test-set-key> --output json

  # Get testcases in a testset
  uip tm testset list-testcases --test-set-key <test-set-key> --output json

  # Get testexecution
  uip tm execution list --project-key <project-key> --test-set-id <test-set-id> -top 100 --output json

  # Get testcaselogs in a testexecution
  uip tm execution list-testcaselogs --execution-id <testexecution-id> --project-key <project-key> --output json

  # Get testcaselog assertions of a testcaselogs
  uip tm testcaselog list-assertions --project-key <project-key> --test-case-log-id <testcase-log-id> --output json

```

## Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` on REST API | `uip login` to re-authenticate. |
| `404 Not Found` on `/testexecutions/filtered` | Verify `<PROJECT_ID>` — use the `id` field from `uip tm project list --output json` |
| Empty `items` array in response | No executions match the filter — loosen the filter |

## Navigate to a workflow

| I want to... | Start here |
|---|---|
| **Generate a shareable test report** (tester or release manager view) | [references/test-result-report-guide.md](references/test-result-report-guide.md) |


## Anti-patterns

- **Do NOT proceed if authentication fails** — all Test Manager API calls require a valid bearer token. Fail fast rather than surfacing confusing 401 errors later.

