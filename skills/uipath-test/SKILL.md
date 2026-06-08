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

UiPath Test Manager is a web application that manages the testing lifecycle of projects, enabling requirements traceability, test planning, and reporting. Its key business objects are:

- **Requirements** - Defines what needs to be tested.
- **Test cases** - Defines the scenarios to be tested. A testcase can have **teststeps**. A testcase can be executed or run directly.
- **Test sets** - Groups of test cases for execution.
- **Test executions** - When a test set or a test case is run, a test execution is created.
- **Test case logs** - Logs of a **test case** in an execution. A **testcase** can be navigated from **testcaselogs**.
- **Test step logs** — Step-level logs within a **test case log**.
- **Test case log assertions** - Assertion steps of a test case log in an execution.

CLI tool for UiPath Test Manager (`uip tm`). Use `uip tm --help` and `uip tm <command> <subcommand> --help` to discover commands and options. **Always pass `--output json`** on every `uip` command.

## Commands

Common `uip tm` commands organized by resource type.

### Project Commands

| Command | Purpose |
|---|---|
| `uip tm project list --filter <NAME_OR_KEY>` | Find a project by name or key. |
| `uip tm project create --name <PROJECT_NAME> --project-key <PROJECT_KEY>` | Create a new Test Manager project. |
| `uip tm project update --project-key <PROJECT_KEY> --name <PROJECT_NAME>` | Update project name or description. |
| `uip tm project delete --project-key <PROJECT_KEY>` | Delete a Test Manager project. |
| `uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` | Set the default Orchestrator folder for a project. |
| `uip tm project clear-default-folder --project-key <PROJECT_KEY>` | Clear the default Orchestrator folder from a project. |
| `uip tm project owners list --project-key <PROJECT_KEY> [<PROJECT_KEY> ...]` | List the owners of one or more Test Manager projects. |

> Get folder keys with `uip or folders list -n <name> --all --output json` — returns all folders visible to the current user.

### Test Cases Commands

| Command | Purpose |
|---|---|
| `uip tm testcases create --project-key <PROJECT_KEY> --name <TEST_CASE_NAME>` | Create a new test case in a Test Manager project. |
| `uip tm testcases list --project-key <PROJECT_KEY>` | List all test cases in a Test Manager project. Optional `--filter <text>` to search by name/key. |
| `uip tm testcases update --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --name <TEST_CASE_NAME>` | Update a test case name or description (at least one of `--name` or `--description` required). |
| `uip tm testcases delete --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Delete a test case by its key. |
| `uip tm testcases link-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME> --test-name <TEST_NAME>` | Link an Orchestrator package automation to a test case. |
| `uip tm testcases unlink-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Unlink the automation from a test case. |
| `uip tm testcases list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` | List test entry points available in an Orchestrator folder (optional: `--package-name <PACKAGE_NAME>` to filter). |
| `uip tm testcases list-testsets --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | List test sets that contain a given test case. |
| `uip tm testcases list-steps --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List test steps for a test case. **Uses `--test-case-id <UUID>`, not `--test-case-key`.** |
| `uip tm testcases list-result-history --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List test case log result history for a specific test case. Optional `--only-failed`, `--filter`, `--limit`, `--offset`. |
| `uip tm testcases run --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | Start a new execution for one or more test cases. **Uses `--test-case-id <UUID>` (space-separated for multiple).** Optional `--async`, `--name`, `--folder-key`, `--robot-user-key`, `--machine-key`. |
| `uip tm testcases add --test-set-key <TEST_SET_KEY> --test-case-keys <KEY1,KEY2,...>` | Add test cases to a test set (comma-separated keys). |
| `uip tm testcases remove --test-set-key <TEST_SET_KEY> --test-case-keys <KEY1,KEY2,...>` | Remove test cases from a test set (comma-separated keys). |

> **Three flag shapes for test case identifiers — do not interchange:**
> - `--test-case-id <UUID>` — used by `run`, `list-steps`, `list-result-history`. Get the UUID from `uip tm testcases list --output json` (`Id` field).
> - `--test-case-key <PROJECT_KEY:NUMBER>` — singular, used by `update`, `delete`, `link-automation`, `unlink-automation`, `list-testsets`. Example: `DEMO:1`.
> - `--test-case-keys <KEY1,KEY2,...>` — **plural**, comma-separated, used by `testcases add` and `testcases remove` for bulk membership changes on a test set.

### Test Sets Commands

| Command | Purpose |
|---|---|
| `uip tm testsets create --project-key <PROJECT_KEY> --name <TEST_SET_NAME>` | Create a new test set in a Test Manager project. |
| `uip tm testsets list --project-key <PROJECT_KEY>` | List test sets in a Test Manager project. Optional `--filter <text>`, `--folder-key`, `--include-last-execution`. |
| `uip tm testsets update --test-set-key <TEST_SET_KEY> --name <TEST_SET_NAME>` | Update a test set name or description. |
| `uip tm testsets delete --test-set-key <TEST_SET_KEY>` | Delete a test set by its key. |
| `uip tm testsets list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY>` | List test cases assigned to a test set. |
| `uip tm testsets run --test-set-key <TEST_SET_KEY>` | Run a test set and return the execution ID. Optional `--execution-type <automated\|manual\|mixed\|none>` (default `automated`), `--input-path <FILE>` for parameter overrides. |

> Keys use the format `PROJECT_KEY:NUMBER` (e.g., `INV:42`). To add or remove test cases in a test set, use `uip tm testcases add` / `uip tm testcases remove` — those verbs live under the `testcases` group, not under `testsets`.

### Executions Commands

| Command | Purpose |
|---|---|
| `uip tm executions list --project-key <PROJECT_KEY>` | List top n executions for a project. Optional `--test-set-id <UUID>` to scope to a test set, `--filter <text>`, `--limit`, `--offset`. **Use this for the common case** (one test set or a single project query). |
| `uip tm executions list-filtered --project-key <PROJECT_KEY>` | Rich-filter variant: `--test-set-id`, `--updated-by`, `--search`, `--labels`, `--test-execution-ids`, `--sort-by`, `--limit`, `--offset`. **Use only when you need label filtering, multi-execution-id lookup, custom ordering, or `--updated-by` filtering** — features `list` does not expose. |
| `uip tm executions get-stats --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | Get aggregated statistics for a single test execution. |
| `uip tm executions run --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --execution-type <TYPE>` | Re-run an existing test execution. Optional `--test-case-log-ids <UUID...>` to re-run only specific test case logs (space-separated), `--async`. |
| `uip tm executions retry --execution-id <EXECUTION_ID>` | Retry only the failed test cases of a finished execution. Optional `--project-key`, `--test-set-key`, `--execution-type`. |
| `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` | List test case logs of an execution. Optional `--only-failed`, `--filter`, `--limit`, `--offset`. **Note the nested subcommand path — this is not a top-level `executions` verb.** |

> **`run` lives under three groups, all distinct:**
> - `uip tm testcases run` — start a new execution for one or more **test cases** (`--test-case-id` UUIDs, space-separated).
> - `uip tm testsets run` — start a new execution for an entire **test set** (`--test-set-key`).
> - `uip tm executions run` — **re-run an existing** execution by `--execution-id`, optionally narrowed to specific `--test-case-log-ids`.

### Test Case Log Commands

| Command | Purpose |
|---|---|
| `uip tm testcaselog start --project-key <PROJECT_KEY> --execution-id <EXECUTION_ID> --test-case-id <TEST_CASE_ID>` | Start a test case execution within a running test execution. Optional `--run-id <NUMBER>`. |
| `uip tm testcaselog finish --project-key <PROJECT_KEY> --execution-id <EXECUTION_ID> --test-case-id <TEST_CASE_ID> --has-error <true\|false> --executed-by <USER_ID>` | Finish a started test case execution. Optional `--detail-link <URL>`, `--run-id`, `--is-post-condition-met`. |
| `uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID>` | List assertions of a test case log. |

### Test Step Log Commands

| Command | Purpose |
|---|---|
| `uip tm teststeplog list --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID>` | List test step logs for a test case log. |

### Report Commands

| Command | Purpose |
|---|---|
| `uip tm report get --execution-id <EXECUTION_ID>` | Get a summary report for a completed test execution. Optional `--project-key`, `--test-set-key`, `--query`. |

### Attachment Commands

| Command | Purpose |
|---|---|
| `uip tm attachment download --execution-id <EXECUTION_ID>` | Download attachments for test cases in an execution. Optional `--project-key`, `--test-set-key`, `--test-case-name`, `--only-failed`, `--result-path <DIR>`. |

### Result Commands

| Command | Purpose |
|---|---|
| `uip tm result download --execution-id <EXECUTION_ID>` | Download test execution results as JUnit XML. Optional `--project-key`, `--test-set-key`, `--result-path <DIR>`. |

### Wait Commands

| Command | Purpose |
|---|---|
| `uip tm wait --execution-id <EXECUTION_ID>` | Wait for a test execution to reach a terminal state. Optional `--project-key`, `--test-set-key`, `--timeout <SECONDS>`. |

### User Commands

| Command | Purpose |
|---|---|
| `uip tm user get` | Get profile data for the currently authenticated user. |

### Custom Field Commands

Custom fields are project-scoped field definitions you attach to **Requirement**, **TestCase**, or **TestSet** objects. The top-level customfield commands manage these definitions. The nested `label` and `value` subgroups operate on the **per-object rows** that fill in those fields. The `--object-type` flag is case-sensitive and accepts only `Requirement`, `TestCase`, or `TestSet`. The `--data-type` flag accepts only `Text` or `Label` (also PascalCase).

| Command | Purpose |
|---|---|
| `uip tm customfield list --project-key <PROJECT_KEY>` | List custom field definitions. Optional `--object-types <type...>`, `--data-types <type...>` (filter; both variadic, PascalCase), `--name <NAME>` (exact match), `--filter <text>` (substring), `--sort-by <expr>`, `--limit <N>`, `--offset <N>`. |
| `uip tm customfield get --project-key <PROJECT_KEY> --field-id <UUID>` | Get a custom field definition by UUID, OR identify by `--name <NAME> --object-type <TYPE>`. |
| `uip tm customfield create --project-key <PROJECT_KEY> --name <NAME> --data-type <Text\|Label> (--object-type <Requirement\|TestCase\|TestSet> \| --scope-list <type...>)` | Create a new custom field definition. Pass `--object-type` for a single-scope field, OR `--scope-list <Requirement TestCase TestSet>` (variadic, mutually exclusive) for multi-scope. Optional `--description <text>`, `--value-hints <text>`, `--default-value <text>`. |
| `uip tm customfield update --project-key <PROJECT_KEY> --field-id <UUID>` | Update a custom field definition. Identify by `--field-id` OR by `--name + --object-type`. Optional `--rename-to <name>`, `--description`, `--default-value`, `--value-hints`. Unspecified fields keep current values. |
| `uip tm customfield delete --project-key <PROJECT_KEY> --field-ids <UUID...>` | Delete one or more custom field definitions by UUID (variadic), OR singleton by `--name + --object-type`. |

#### Custom Field — Label-type rows

All `customfield label` verbs require `--object-type <Requirement\|TestCase\|TestSet>`.

| Command | Purpose |
|---|---|
| `uip tm customfield label list --project-key <PROJECT_KEY> --object-type <TYPE>` | List label rows. Optional `--object-id <UUID>` to scope to a single object, `--filter <text>`, `--sort-by`, `--limit`, `--offset`. |
| `uip tm customfield label get --project-key <PROJECT_KEY> --object-type <TYPE> --label-id <UUID>` | Get a single label row by UUID. |
| `uip tm customfield label create --project-key <PROJECT_KEY> --object-type <TYPE> --object-id <UUID> --values '{"Field":["v1","v2"]}'` | Upsert a label row on one object. `--values` is a JSON object mapping field names to string arrays. |
| `uip tm customfield label add --project-key <PROJECT_KEY> --object-type <TYPE> --custom-field-name <NAME> --object-ids <UUID...> --values <value...>` | Append values to a label field across multiple objects. Optional `--replace-existing-values` for authoritative-set semantics. |
| `uip tm customfield label remove --project-key <PROJECT_KEY> --object-type <TYPE> --custom-field-name <NAME> --object-ids <UUID...> (--values <value...> \| --remove-all-values)` | Remove values from a label field across multiple objects. |

#### Custom Field — Text-type rows

All `customfield value` verbs require `--object-type <Requirement\|TestCase\|TestSet>`. `create` additionally requires `--data-type <Text\|Label>` (must match the field's definition).

| Command | Purpose |
|---|---|
| `uip tm customfield value list --project-key <PROJECT_KEY> --object-type <TYPE>` | List value rows. Results are empty unless `--object-id <UUID>` is provided. Optional `--filter <text>`, `--sort-by`, `--limit`, `--offset`. |
| `uip tm customfield value get --project-key <PROJECT_KEY> --object-type <TYPE> --value-id <UUID>` | Get a value row by UUID, OR by `--name + --object-id`. |
| `uip tm customfield value create --project-key <PROJECT_KEY> --object-type <TYPE> --name <FIELD_NAME> --object-id <UUID> --data-type <Text\|Label>` | Create a value row. Optional `--value <text>` for the initial content. The `--data-type` must match the existing field definition. |
| `uip tm customfield value update --project-key <PROJECT_KEY> --object-type <TYPE> --value-id <UUID> --value <text>` | Update a value row by UUID, OR by `--name + --object-id`. Use `--clear` to set the value to empty. |
| `uip tm customfield value delete --project-key <PROJECT_KEY> --object-type <TYPE> --value-id <UUID>` | Delete a value row by UUID, OR by `--name + --object-id`. |

### Object Label Commands

Object labels are tag-style metadata applied to Requirement, TestCase, TestSet, TestExecution, TestCaseLog. Use `--object-type` for the parent kind and `--object-ids` for the target objects.

| Command | Purpose |
|---|---|
| `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type <Requirement\|TestCase\|TestSet\|TestExecution\|TestCaseLog>` | List distinct label names for one `--object-type` (paginated). Optional `--object-ids <UUID...>`, `--label-types <UserLabel\|SystemLabel\|InternalLabel ...>`, `--filter <text>`, `--sort-by`, `--limit`, `--offset`. |
| `uip tm objectlabel get --project-key <PROJECT_KEY> --label-id <UUID>` | Get a single label-assignment row by UUID. |
| `uip tm objectlabel add --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> --labels <name...>` | Attach labels to objects (variadic; one-to-one, one-to-many, many-to-many). Optional `--remove-other-labels` for authoritative-set semantics. |
| `uip tm objectlabel remove --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> (--labels <name...> \| --remove-all-labels)` | Detach labels from objects. `--labels` and `--remove-all-labels` are mutually exclusive. |

## Critical Rules

1. **Always check login first** — run `uip login status --output json` before any Test Manager operation. If not authenticated, run `uip login` to sign in.
2. **Probe the CLI surface once per session, before the first `uip tm` command.** Run `uip tm testcases --help --output json` (any flags accepted). Result `Success` → post-rename CLI; use the command tables above as-is. `unknown command` / non-zero exit → pre-rename CLI; translate via the [Pre-rename fallbacks](#pre-rename-fallbacks) table before each call. Re-probe on any later `unknown command` error.
3. **Always pass `--output json`** to every `uip` command — no exceptions. Structured JSON output is what you need to reason about results reliably, even when you only plan to summarize them back to the user.
4. **Cap retries at 3** for any failing `uip` CLI command. After 3 failures, stop and report the error to the user (see Rule — never fall back to direct REST APIs).
5. **Handle empty results** — if a list command returns an empty array, stop and inform the user rather than proceeding with a null key.
6. **Confirm before delete** — always confirm the target resource key with the user before running any `delete` command.
7. **For operations requiring folder key** — use `uip or folders list -n <folder-name> --all --output json` (run `/uipath-platform` for folder management details).
8. **Discover before assuming** — never guess automation names, folder keys, project IDs, or test case keys. Always run the matching `list` command first (e.g., `uip tm testcases list-automations`, `uip or folders list -n <folder-name> --all`).
9. **Narrow `list` calls server-side when the user names an entity.** When the user provides a name, key, label, or tag, check `uip tm <resource> list --help` (or `uip or <resource> list --help`) for the narrowing flag the command exposes and pass it on the `list` call. Never list all results and filter client-side — it wastes tokens and misses paginated entries. Applies to every entity across `uip tm` and `uip or`.
10. **Set default folder before any `run` command** — `uip tm testcases run` and `uip tm testsets run` both require a default Orchestrator folder on the project. Run `uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json` first. Get folder keys with `uip or folders list -n <folder-name> --all --output json`.
11. **On any `uip` command failure or ambiguity, STOP and ask the user — do NOT fall back to direct REST API calls.** When a `uip` command errors, returns malformed output, or the right flag/value is unclear (e.g., multiple matching entities, missing identifier, unexpected schema), interrupt and ask the user before proceeding. This overrides any instinct to "try the underlying API instead."

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

### Confirm project scope
  Ask the user for the project name or key before any Test Manager call. For multi-project scenarios, collect ALL names or keys in one prompt. Resolve each to a `PROJECT_KEY`:
  ```bash
  uip tm project list --filter <NAME_OR_KEY> --output json
  ```
  Zero matches → stop and ask the user. Multiple matches → list candidates and ask the user to pick. Reuse the confirmed `PROJECT_KEY` for every downstream command.

```bash
  # Get project
  uip tm project list --filter <PROJECT_NAME_OR_KEY> --output json

  # List test sets in a project
  uip tm testsets list --project-key <PROJECT_KEY> --filter <TEST_SET_NAME_OR_KEY> --output json

  # List test cases assigned to a test set
  uip tm testsets list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY> --output json

  # List recent executions for a test set
  uip tm executions list --project-key <PROJECT_KEY> --test-set-id <TEST_SET_ID> --limit 100 --output json

  # List test case logs for an execution (nested subcommand under `executions`)
  uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json

  # List assertions of a test case log
  uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID> --output json

  # List step-level logs of a test case log
  uip tm teststeplog list --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID> --output json
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
- **Do NOT guess command names — verb-noun composites are required.** The CLI uses explicit verb-noun forms; bare verbs do not exist. Confirm with `uip tm <resource> --help --output json`.
