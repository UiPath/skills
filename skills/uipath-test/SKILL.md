---
name: uipath-test
description: "UiPath Test Manager — manage test projects, cases, sets, executions; generate reports; package and run external Playwright test suites. For Orchestrator→uipath-platform. For Studio/RPA test automation authoring→uipath-rpa."
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
- User wants to **triage a failed run** — which cases failed, which assertion broke, which step it died on
- User asks whether a failure is a **real regression or a flaky test** (result history over past executions)
- User needs **failure evidence** — screenshots and logs pulled off the failed cases for a defect

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
- **External (Playwright) test packages** - A Playwright suite packaged as an external test package and uploaded to Orchestrator. Ingestion auto-creates one test case per Playwright test (no link step) and labels each with `PW_Tag_*`, `PW_Project_*`, `PW_Suite_*`, `PW_File_*`. These run on serverless cloud runtimes — see [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md).

CLI tool for UiPath Test Manager (`uip tm`). Use `uip tm --help` and `uip tm <command> <subcommand> --help` to discover commands and options. **Always pass `--output json`** on every `uip` command.

## Commands

Common `uip tm` commands organized by resource type.

### Naming the project: --project-key or --project-id

Every project-scoped `tm` command takes either flag; pass one.

- `--project-key <KEY>` — the prefix from the Test Manager URL (e.g. `DEMO`). Costs one lookup per command.
- `--project-id <UUID>` — used as-is, no lookup.

**Prefer `--project-id` when you already have the ID** — because it was given to you, or because `project create` just returned it. Reuse it for the rest of the run. Do not call `project list` merely to look an ID up: that spends the request you would have saved. Given only a key, use `--project-key`. Passing both is fine; the ID wins.

The tables below show `--project-key`; substitute `--project-id <UUID>` anywhere you have the ID. Key-only commands: `project create` / `update` / `delete`, `project owners list`, `tm pack`.

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

### Requirements Commands

| Command | Purpose |
|---|---|
| `uip tm requirements list --project-key <PROJECT_KEY>` | List requirements in a Test Manager project. |
| `uip tm requirements list-by-test-execution --project-key <PROJECT_KEY> --execution-id <uuid>` | List requirements covered by a test execution. |
| `uip tm requirements get --project-key <PROJECT_KEY> (--requirement-id <uuid> \| --requirement-key <key>)` | Get a requirement by UUID or key (mutually exclusive). |
| `uip tm requirements create --project-key <PROJECT_KEY> --name <name>` | Create a new requirement. |
| `uip tm requirements update --project-key <PROJECT_KEY> --requirement-id <uuid>` | Update a requirement name or description (at least one of `--name` or `--description` required). |
| `uip tm requirements delete --project-key <PROJECT_KEY> --requirement-ids <uuid...>` | Delete one or more requirements (variadic). |
| `uip tm requirements export --project-key <PROJECT_KEY> --output-file <path>` | Export requirements to an .xlsx file. |
| `uip tm requirements list-testcase-ids --project-key <PROJECT_KEY> --requirement-id <uuid>` | List the test case UUIDs assigned to a requirement. |
| `uip tm requirements testcases --project-key <PROJECT_KEY> --requirement-id <uuid> (--add-testcase-ids <uuid...> \| --remove-testcase-ids <uuid...>)` | Attach or detach test cases on a requirement (mutually exclusive). |

### Test Cases Commands

| Command | Purpose |
|---|---|
| `uip tm testcases create --project-key <PROJECT_KEY> --name <TEST_CASE_NAME>` | Create a new test case in a Test Manager project. |
| `uip tm testcases list --project-key <PROJECT_KEY>` | List all test cases in a Test Manager project. Optional `--filter <text>` — matches name or key by PREFIX, not substring. |
| `uip tm testcases update --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --name <TEST_CASE_NAME>` | Update a test case name, description, precondition, or postcondition (at least one field required). |
| `uip tm testcases delete --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Delete a test case by its key. |
| `uip tm testcases link-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME> --test-name <TEST_NAME>` | Link an Orchestrator package automation to a test case. |
| `uip tm testcases unlink-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | Unlink the automation from a test case. |
| `uip tm testcases list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` | List test entry points available in an Orchestrator folder (optional: `--package-name <PACKAGE_NAME>` to filter). |
| `uip tm testcases list-testsets --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` | List test sets that contain a given test case. |
| `uip tm testcases steps list --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List manual test steps for a test case. **Uses `--test-case-id <UUID>`, not `--test-case-key`.** `uip tm testcases list-steps` is a supported alias. |
| `uip tm testcases steps get --project-key <PROJECT_KEY> --step-id <UUID>` | Get a single test step by its UUID. |
| `uip tm testcases steps add --project-key <PROJECT_KEY> --test-case-id <UUID> --description <text>` | Add a step using flags (`--description` required). |
| `uip tm testcases steps add --project-key <PROJECT_KEY> --test-case-id <UUID> --step '<json>' [--step '<json>' ...]` | Add multiple steps by repeating `--step '<json>'`. Mutually exclusive with flag mode. **Not atomic** — earlier steps persist if a later one fails. |
| `uip tm testcases steps update --project-key <PROJECT_KEY> --step-id <UUID>` | Update a step's fields. Only fields you pass change; the rest stay. |
| `uip tm testcases steps move --project-key <PROJECT_KEY> --step-id <UUID> --target-position <n>` | Move a step to a new 0-based position. |
| `uip tm testcases steps delete --project-key <PROJECT_KEY> --step-id <UUID> --yes` | Delete a step. |
| `uip tm testcases list-result-history --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` | List test case log result history for a specific test case. Optional `--only-failed`, `--filter`, `--limit`, `--offset`. |
| `uip tm testcases run --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID> --name <EXECUTION_NAME> --execution-type <manual\|automated\|none\|mixed>` | Start a new execution for one or more test cases. **Uses `--test-case-id <UUID>` (space-separated for multiple).** Optional `--async`, `--folder-key`, `--robot-user-key`, `--machine-key`. |
| `uip tm testcases add --test-set-key <TEST_SET_KEY> (--test-case-keys <KEY1> <KEY2> … \| --labels <Label1> <Label2> …)` | Add test cases to a test set — by explicit keys, OR every test case carrying at least one of the given labels. Both selectors are variadic and **space-separated**: `--test-case-keys DEMO:1 DEMO:2`, `--labels PW_Tag_smoke "PW_Suite_Checkout flow"` (quote names containing spaces). Keys additionally accept the comma form (`DEMO:1,DEMO:2`); **labels do not** — `--labels A,B` is read as one label named `A,B` and matches nothing. Label matching is OR, exact and case-sensitive. The two selectors are mutually exclusive. |
| `uip tm testcases remove --test-set-key <TEST_SET_KEY> --test-case-keys <KEY1,KEY2,...>` | Remove test cases from a test set (comma-separated keys). |

> **Flag shapes for test case and step identifiers — do not interchange:**
> - `--test-case-id <UUID>` — used by `run`, `steps list`, `steps add`, `list-result-history`. Get the UUID from `uip tm testcases list --output json` (`Id` field).
> - `--test-case-key <PROJECT_KEY:NUMBER>` — singular, used by `update`, `delete`, `link-automation`, `unlink-automation`, `list-testsets`. Example: `DEMO:1`.
> - `--test-case-keys <KEY1,KEY2,...>` — **plural**, comma-separated, used by `testcases add` and `testcases remove` for bulk membership changes on a test set.
> - `--step-id <UUID>` — used by all `steps` subcommands except `list` and `add`. Get the UUID from `steps list` (`Id` field).

### Test Sets Commands

| Command | Purpose |
|---|---|
| `uip tm testsets create --project-key <PROJECT_KEY> --name <TEST_SET_NAME>` | Create a new test set in a Test Manager project. |
| `uip tm testsets list --project-key <PROJECT_KEY>` | List test sets in a Test Manager project. Optional `--filter <text>`, `--folder-key`, `--include-last-execution`. |
| `uip tm testsets update --test-set-key <TEST_SET_KEY> --name <TEST_SET_NAME>` | Update a test set name or description. |
| `uip tm testsets delete --test-set-key <TEST_SET_KEY>` | Delete a test set by its key. |
| `uip tm testsets list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY>` | List test cases assigned to a test set. |
| `uip tm testsets run --test-set-key <TEST_SET_KEY>` | Run a test set and return the execution ID. Optional `--execution-type <automated\|manual\|mixed\|none>` (default `automated`), `--input-path <FILE>` for parameter overrides. For Playwright test sets, optional `--playwright-projects <names...>` — see the note below. |
| `uip tm testsets playwright-context --test-set-key <TEST_SET_KEY>` | Probe whether a test set is a Playwright test set: returns `IsPlaywright` plus the available and selected Playwright project names. |

> Keys use the format `PROJECT_KEY:NUMBER` (e.g., `INV:42`). To add or remove test cases in a test set, use `uip tm testcases add` / `uip tm testcases remove` — those verbs live under the `testcases` group, not under `testsets`.

> **Playwright test sets:** `--playwright-projects <names...>` (space-separated, case-sensitive `playwright.config` project names) runs only the selected projects and persists the selection on the test set. It requires every test case in the set to come from one Playwright package; unknown names fail fast listing the valid ones. Probe first with `playwright-context` and branch on `IsPlaywright`. Both need a Test Manager with Playwright support and a CLI carrying the external-package commands — [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md) opens with the check to run and what to do when they are absent.

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
| `uip tm report get --execution-id <EXECUTION_ID> (--project-key <KEY> \| --test-set-key <KEY>)` | Get a summary report for a completed test execution. One of `--project-key`/`--test-set-key` is required to identify the project (verified: passing only `--execution-id` exits with "Provide --project-key or --test-set-key"). |

### Attachment Commands

| Command | Purpose |
|---|---|
| `uip tm attachment download --execution-id <EXECUTION_ID>` | Download attachments for test cases in an execution. |
| `uip tm attachment upload --object-id <UUID> --object-type <type> --file <path>` | Upload a file as an attachment to a Test Manager object (e.g. `--object-type testCaseLog`). |

### Result Commands

| Command | Purpose |
|---|---|
| `uip tm result download --execution-id <EXECUTION_ID>` | Download test execution results as JUnit XML. Optional `--project-key`, `--test-set-key`, `--result-path <DIR>`. |

### Pack Commands (Playwright)

| Command | Purpose |
|---|---|
| `uip tm pack --project-path <dir> --type playwright --project-key <PROJECT_KEY> --name <PackageName> --package-version <ver> -o <out-dir>` | Pack a Playwright suite into a `.nupkg` external test package. Requires a lockfile and `@playwright/test` in the project. `--package-version` takes a NuGet/SemVer-style version — three numeric parts, optional prerelease suffix (`1.0.0`, `1.0.1-beta.1`); `1.0` or a non-numeric string is rejected. `--project-key` targets the Test Manager project where ingestion auto-creates the test cases; `--no-create-test-cases` skips that; `--dry-run` previews. Upload with `uip or packages upload <nupkg>`. |

> Packing is offline — no auth needed. The upload → ingestion → label-fill → run pipeline is in [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md).

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
2. **Always pass `--output json`** to every `uip` command — no exceptions. Structured JSON output is what you need to reason about results reliably, even when you only plan to summarize them back to the user.
3. **Cap retries at 3** for any failing `uip` CLI command. After 3 failures, stop and report the error to the user (see Rule — never fall back to direct REST APIs).
4. **Handle empty results** — if a list command returns an empty array, stop and inform the user rather than proceeding with a null key. Exception: a zero-result `tm testcases list --filter` call may be a prefix miss rather than a truly empty dataset — apply Rule 8's prefix fallback to disambiguate; stop only when the fallback also finds nothing. Filtered lookups on other resources (project, customfield) returning empty are real empty results — stop as usual.
5. **Confirm before delete** — always confirm the target resource key with the user before running any `delete` command — unless the user already authorized this exact delete. All delete commands require `--yes` (or `-y`) to proceed; omitting it exits without deleting.
6. **For operations requiring folder key** — use `uip or folders list -n <folder-name> --all --output json` when the user named a folder; when picking one yourself, list without `--all` so you only get folders you are a member of (run `/uipath-platform` for folder management details).
7. **Discover before assuming** — never guess automation names, folder keys, project IDs, or test case keys. Always run the matching `list` command first (e.g., `uip tm testcases list-automations`, `uip or folders list -n <folder-name> --all`).
8. **Narrow `list` calls server-side when the user names an entity.** When the user provides a name, key, label, or tag, check `uip tm <resource> list --help` (or `uip or <resource> list --help`) for the narrowing flag the command exposes and pass it on the `list` call. Never list all results and filter client-side — it wastes tokens and misses paginated entries. Applies to every entity across `uip tm` and `uip or`. Exception: `tm testcases list --filter` matches by prefix. A mid-name term returns zero — retry `--filter` with a broader name prefix from context; re-list without `--filter` only when no workable prefix exists, paging through ALL results (`--limit`/`--offset`) before concluding the target is absent.
9. **`run` needs a default Orchestrator folder — set one only on the exact missing-folder error.** `uip tm testcases run` and `uip tm testsets run` both require a default folder on the project. Attempt the `run` first and match the failure text exactly: a project with **no** default folder fails with `"Message": "HTTP 400: Please assign folder to project level before executing testcases."` (`errorCode: itemNotFound`). Only on that error, set one with `uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json`, then retry once. Get folder keys with `uip or folders list -n <folder-name> --all --output json`. Do NOT treat other errors as folder problems: an unusable default folder surfaces as an opaque `HTTP 5xx` on the run, and `set-default-folder` with a nonexistent folder key fails with `"HTTP 400: Internal Server Error."` (`errorCode: unknown`) — both stop under Rule 10 rather than triggering a folder overwrite. Never overwrite a default folder that is already working — an arbitrary folder picked off `or folders list` may be one Test Manager rejects, breaking every subsequent run on that project. This recovery is the one named run exception to Rule 10; any other run failure still stops.
10. **On any `uip` command failure or ambiguity, STOP and ask the user — do NOT fall back to direct REST API calls.** When a `uip` command errors, returns malformed output, or the right flag/value is unclear (e.g., multiple matching entities, missing identifier, unexpected schema), interrupt and ask the user before proceeding. This overrides any instinct to "try the underlying API instead." **Two exceptions, both expected outcomes rather than faults, each identified by its exact error:** (a) a `run` failing with `"HTTP 400: Please assign folder to project level before executing testcases."` — the missing-default-folder signal; set the folder per Rule 9 and retry once. (b) `uip tm wait` exiting with code 2 and `"Timed out after <N>s waiting for execution '<EXECUTION_ID>'. Last status: <status>."` — the bounded `--timeout` working as designed; report the non-finish and carry on with the remaining steps. Other `wait` failures (`Polling failed/interrupted/aborted ...`, exit code 1) are real faults, not timeouts. Every other failure still stops here.

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
| **Triage a failed run to a root cause** (failed logs → assertions → step logs → evidence; flaky vs regression) | [references/failure-triage-guide.md](references/failure-triage-guide.md) |
| **Generate a shareable test report** (tester or release manager view) | [references/test-result-report-guide.md](references/test-result-report-guide.md) |
| **Publish a project and link it to a Test Manager test case** (Studio/RPA) | [references/publish-and-link-guide.md](references/publish-and-link-guide.md) |
| **Pack, ingest, and run a Playwright suite on serverless** (pack → upload → labels → run) | [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md) |


## Anti-patterns

- **Do NOT proceed if authentication fails** — all Test Manager API calls require a valid bearer token. Fail fast rather than surfacing confusing 401 errors later.
- **Do NOT guess command names — verb-noun composites are required.** The CLI uses explicit verb-noun forms; bare verbs do not exist. Confirm with `uip tm <resource> --help --output json`.
- **Do NOT `link-automation` Playwright test cases.** Playwright ingestion links them to the package automatically; the manual link step belongs to the Studio/RPA pipeline only.
