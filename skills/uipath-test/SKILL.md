---
name: uipath-test
description: "UiPath Test Manager — manage test projects, cases, sets, executions; generate reports; package and run external Playwright test suites. For Orchestrator→uipath-platform. For Studio/RPA test automation authoring→uipath-rpa."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Test Assistant

Manage UiPath Test Manager projects, requirements, test cases, test sets, executions, logs, attachments, results, custom fields, labels, and persona-tailored shareable test reports.

## Use For

Test Manager CRUD; execution analysis, coverage, regression trends, failure rates, go/no-go summaries; failed-run triage; flaky-versus-regression analysis; failure evidence; and shareable QA-engineer, developer, or release-manager reports.

## Concepts and CLI

Requirements define what must be tested; test cases define scenarios and may contain **teststeps**; test sets group cases; executions are created when a test set or testcase runs. Testcase logs record a testcase in an execution and provide navigation; test-step logs record steps; testcase-log assertions are assertion steps.

External Playwright packages are suites packaged and uploaded to Orchestrator. Ingestion auto-creates one testcase per Playwright test, without a link step, and labels each `PW_Tag_*`, `PW_Project_*`, `PW_Suite_*`, and `PW_File_*`. They run on serverless cloud runtimes; see [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md).

Use `uip tm`; discover syntax with `uip tm --help` and `uip tm <command> <subcommand> --help`. **Always pass `--output json` to every `uip` command; all commands below require it.**

## Commands

### Projects, folders, and requirements

- Projects: `uip tm project list --filter <NAME_OR_KEY>` finds by name/key; `project create --name <PROJECT_NAME> --project-key <PROJECT_KEY>` creates; `project update --project-key <PROJECT_KEY> --name <PROJECT_NAME>` updates name/description; `project delete --project-key <PROJECT_KEY>` deletes; `project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` sets the default Orchestrator folder; `project clear-default-folder --project-key <PROJECT_KEY>` clears it; `project owners list --project-key <PROJECT_KEY> [<PROJECT_KEY> ...]` lists owners.
- Get folder keys with `uip or folders list -n <name> --all --output json`; it returns all folders visible to the current user.
- Prefix with `uip tm requirements`: `list --project-key <PROJECT_KEY>`; `list-by-test-execution --project-key <PROJECT_KEY> --execution-id <uuid>`; `get --project-key <PROJECT_KEY> (--requirement-id <uuid> | --requirement-key <key>)` (mutually exclusive UUID/key); `create --project-key <PROJECT_KEY> --name <name>`; `update --project-key <PROJECT_KEY> --requirement-id <uuid>` (updates name/description and requires at least one of `--name` or `--description`); `delete --project-key <PROJECT_KEY> --requirement-ids <uuid...>` (variadic IDs); `export --project-key <PROJECT_KEY> --output-file <path>` (exports `.xlsx`); `list-testcase-ids --project-key <PROJECT_KEY> --requirement-id <uuid>`; `testcases --project-key <PROJECT_KEY> --requirement-id <uuid> (--add-testcase-ids <uuid...> | --remove-testcase-ids <uuid...>)` (mutually exclusive attach/detach selectors).

### Test cases

- `uip tm testcases create --project-key <PROJECT_KEY> --name <TEST_CASE_NAME>`; `list --project-key <PROJECT_KEY>` optionally `--filter <text>` matching name/key by **PREFIX**, not substring; `update --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --name <TEST_CASE_NAME>` updates name, description, precondition, or postcondition and requires at least one field; `delete --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` deletes by key.
- `link-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY> --folder-key <FOLDER_KEY> --package-name <PACKAGE_NAME> --test-name <TEST_NAME>` links Orchestrator package automation; `unlink-automation --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` unlinks; `list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY>` lists folder test entry points, optionally `--package-name <PACKAGE_NAME>`; `list-testsets --project-key <PROJECT_KEY> --test-case-key <TEST_CASE_KEY>` lists containing sets.
- Steps: `uip tm testcases steps list --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` lists manual steps using `--test-case-id <UUID>`, not `--test-case-key`; `uip tm testcases list-steps` is an alias. `steps get --project-key <PROJECT_KEY> --step-id <UUID>` gets; `steps add --project-key <PROJECT_KEY> --test-case-id <UUID> --description <text>` adds flag-mode steps (`--description` required), or `steps add --project-key <PROJECT_KEY> --test-case-id <UUID> --step '<json>' [--step '<json>' ...]` adds repeated JSON steps (mutually exclusive with flag mode and **not atomic**: earlier steps persist if a later one fails); `steps update --project-key <PROJECT_KEY> --step-id <UUID>` updates passed fields only; `steps move --project-key <PROJECT_KEY> --step-id <UUID> --target-position <n>` moves to 0-based position; `steps delete --project-key <PROJECT_KEY> --step-id <UUID> --yes` deletes.
- `list-result-history --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID>` lists history, optionally `--only-failed`, `--filter`, `--limit`, `--offset`. `run --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_ID> --name <EXECUTION_NAME> --execution-type <manual|automated|none|mixed>` starts an execution for one or more space-separated testcase UUIDs; optionally `--async`, `--folder-key`, `--robot-user-key`, `--machine-key`.
- `uip tm testcases add --test-set-key <TEST_SET_KEY> (--test-case-keys <KEY1> <KEY2> … | --labels <Label1> <Label2> …)` adds by explicit keys or every testcase carrying at least one label; selectors are mutually exclusive and variadic space-separated. Keys also accept comma form (`DEMO:1,DEMO:2`), labels do not (`--labels A,B` is one label). Label matching is OR, exact, and case-sensitive; quote labels containing spaces. `uip tm testcases remove --test-set-key <TEST_SET_KEY> --test-case-keys <KEY1,KEY2,...>` removes comma-separated keys.
- Use `--test-case-id <UUID>` with `run`, `steps list`, `steps add`, and `list-result-history`; obtain it from `uip tm testcases list --output json` (`Id`). Use singular `--test-case-key <PROJECT_KEY:NUMBER>` with `update`, `delete`, `link-automation`, `unlink-automation`, and `list-testsets`. Use plural `--test-case-keys <KEY1,KEY2,...>` for comma-separated test-set bulk membership. Use `--step-id <UUID>` with all `steps` commands except `list` and `add`; obtain it from `steps list` (`Id`).

### Test sets and executions

- `uip tm testsets create --project-key <PROJECT_KEY> --name <TEST_SET_NAME>`; `list --project-key <PROJECT_KEY>` optionally `--filter <text>`, `--folder-key`, `--include-last-execution`; `update --test-set-key <TEST_SET_KEY> --name <TEST_SET_NAME>` updates name/description; `delete --test-set-key <TEST_SET_KEY>`; `list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY>` lists assigned cases.
- `uip tm testsets run --test-set-key <TEST_SET_KEY>` runs and returns an execution ID; optionally `--execution-type <automated|manual|mixed|none>` (default `automated`), `--input-path <FILE>`, and for Playwright `--playwright-projects <names...>`. `uip tm testsets playwright-context --test-set-key <TEST_SET_KEY>` probes status and returns `IsPlaywright`, available projects, and selected projects.
- Keys are `PROJECT_KEY:NUMBER`. Add/remove membership with `uip tm testcases add`/`uip tm testcases remove`, not `testsets` verbs. For Playwright sets, `--playwright-projects <names...>` is space-separated and case-sensitive to `playwright.config` names; it runs only selected projects and persists selection. Every testcase must come from one Playwright package; unknown names fail fast with valid names. Probe first with `playwright-context` and branch on `IsPlaywright`. Both require Test Manager Playwright support and a CLI carrying external-package commands. See [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md), which begins with the availability check and absent-support action.
- `uip tm executions list --project-key <PROJECT_KEY>` lists top n, optionally `--test-set-id <UUID>`, `--filter <text>`, `--limit`, `--offset`; use for the common one-test-set or single-project query. `list-filtered --project-key <PROJECT_KEY>` supports `--test-set-id`, `--updated-by`, `--search`, `--labels`, `--test-execution-ids`, `--sort-by`, `--limit`, `--offset`; use only for label filtering, multiple execution IDs, custom ordering, or `--updated-by`.
- `get-stats --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` returns aggregate statistics; `run --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --execution-type <TYPE>` reruns, optionally `--test-case-log-ids <UUID...>` (space-separated) and `--async`; `retry --execution-id <EXECUTION_ID>` retries only failed cases, optionally `--project-key`, `--test-set-key`, `--execution-type`; `testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY>` lists case logs, optionally `--only-failed`, `--filter`, `--limit`, `--offset`; this nested path is not a top-level `executions` verb. Use `uip tm testcases run` for testcase UUIDs, `uip tm testsets run` for a test-set key, and `uip tm executions run` to rerun an execution, optionally narrowed by case-log IDs.

### Logs, reports, attachments, and results

- `uip tm testcaselog start --project-key <PROJECT_KEY> --execution-id <EXECUTION_ID> --test-case-id <TEST_CASE_ID>` starts, optionally `--run-id <NUMBER>`. `finish --project-key <PROJECT_KEY> --execution-id <EXECUTION_ID> --test-case-id <TEST_CASE_ID> --has-error <true|false> --executed-by <USER_ID>` finishes, optionally `--detail-link <URL>`, `--run-id`, `--is-post-condition-met`.
- `uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID>` lists assertions; `uip tm teststeplog list --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID>` lists step logs.
- `uip tm report get --execution-id <EXECUTION_ID> (--project-key <KEY> | --test-set-key <KEY>)` summarizes a completed execution; exactly one project-identifying option is required. Passing only `--execution-id` exits with `Provide --project-key or --test-set-key`.
- `uip tm attachment download --execution-id <EXECUTION_ID>` downloads testcase attachments; `attachment upload --object-id <UUID> --object-type <type> --file <path>` uploads to a Test Manager object, such as `--object-type testCaseLog`; `uip tm result download --execution-id <EXECUTION_ID>` downloads JUnit XML, optionally `--project-key`, `--test-set-key`, `--result-path <DIR>`.

### Playwright pack

`uip tm pack --project-path <dir> --type playwright --project-key <PROJECT_KEY> --name <PackageName> --package-version <ver> -o <out-dir>` packs a Playwright suite into a `.nupkg`; a lockfile and `@playwright/test` are required. `--package-version` is NuGet/SemVer-style with three numeric parts and optional prerelease suffix (`1.0.0`, `1.0.1-beta.1`); `1.0` and nonnumeric values are rejected. `--project-key` targets the Test Manager project for automatic testcase ingestion; `--no-create-test-cases` skips it; `--dry-run` previews. Upload with `uip or packages upload <nupkg>`. Packing is offline and needs no auth. The upload → ingestion → label-fill → run pipeline is in [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md).

### Wait and user

`uip tm wait --execution-id <EXECUTION_ID>` waits for terminal state; optionally `--project-key`, `--test-set-key`, `--timeout <SECONDS>`. `uip tm user get` gets the authenticated user's profile.

### Custom fields

Project-scoped custom-field **definitions** (attach to Requirement/TestCase/TestSet) plus per-object `label` and `value` rows, via `uip tm customfield …`. Full command surface — scopes, `--object-type`/`--data-type` enums (case-sensitive: `Requirement|TestCase|TestSet`, `Text|Label`), `--values` JSON semantics, and every label/value verb: [references/custom-fields-guide.md](references/custom-fields-guide.md).

### Object labels

Tag metadata via `uip tm objectlabel …` on `Requirement`, `TestCase`, `TestSet`, `TestExecution`, or `TestCaseLog`. Full list/get/add/remove surface, `--label-types`, and authoritative-set (`--remove-other-labels`) semantics: [references/object-labels-guide.md](references/object-labels-guide.md).

## Critical Rules

1. **Always check login first:** run `uip login status --output json` before any Test Manager operation. If unauthenticated, run `uip login`.
2. **Always pass `--output json`** to every `uip` command, without exception.
3. **Cap retries at 3** for any failing `uip` command. After three failures, stop and report the error; never use direct REST APIs.
4. An empty list stops the operation and informs the user rather than proceeding with a null key. Exception: empty `tm testcases list --filter` may be a prefix miss; use Rule 8's prefix fallback and stop only if it also finds nothing. Empty filtered project or customfield lookups are real empty results and stop normally.
5. **Confirm before delete:** confirm the target resource key unless the user already authorized that exact delete. Every delete requires `--yes` or `-y`; omission exits without deleting.
6. For a required folder key, use `uip or folders list -n <folder-name> --all --output json` when the user named the folder; when choosing one yourself, omit `--all` to list only member folders. Run `/uipath-platform` for folder-management details.
7. **Discover before assuming:** never guess automation names, folder keys, project IDs, or testcase keys; run the matching list first, such as `uip tm testcases list-automations` or `uip or folders list -n <folder-name> --all`.
8. **Narrow named-entity list calls server-side:** when given a name, key, label, or tag, inspect `uip tm <resource> list --help` or `uip or <resource> list --help` for its narrowing flag and use it. Never list all then filter client-side; this applies to every entity across `uip tm` and `uip or`. Exception: `tm testcases list --filter` is prefix matching. If a mid-name term returns zero, retry with a broader contextual prefix; relist without `--filter` only if no workable prefix exists, paging through all results with `--limit`/`--offset` before concluding absence.
9. **Default-folder recovery:** `uip tm testcases run` and `uip tm testsets run` require a project default folder. Attempt the run first. Only when failure text exactly includes `"Message": "HTTP 400: Please assign folder to project level before executing testcases."` and `errorCode: itemNotFound`, run `uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json`, then retry once. Get keys with `uip or folders list -n <folder-name> --all --output json`. Do not interpret other errors as missing folders: an unusable default gives opaque `HTTP 5xx`; a nonexistent folder key gives `"HTTP 400: Internal Server Error."` with `errorCode: unknown`. Both stop under Rule 10. Never overwrite a working default folder; an arbitrary folder may be rejected by Test Manager and break later runs. This is the only named run exception to Rule 10; all other run failures stop.
10. **Any `uip` failure or ambiguity stops and asks the user:** this includes command errors, malformed output, unclear flags/values, multiple matches, missing identifiers, or unexpected schemas. Never fall back to REST. Exceptions are expected outcomes identified exactly: (a) the Rule 9 missing-folder error, handled there; (b) `uip tm wait` exit code 2 with `Timed out after <N>s waiting for execution '<EXECUTION_ID>'. Last status: <status>.`, which means bounded timeout worked—report non-finish and continue remaining steps. `Polling failed/interrupted/aborted ...` and exit code 1 are real wait failures; every other failure stops.

## Quick Start

1. Verify auth: run `uip login status --output json`; if unauthenticated, run `uip login`. If needed, set the tenant with `uip login tenant set <TENANT_NAME> --output json`. Run `/uipath-platform` for more authentication details.
2. Ask for the project name/key before any Test Manager call; for multiple projects collect all names/keys in one prompt. Resolve each with `uip tm project list --filter <NAME_OR_KEY> --output json`. Zero matches stop and ask; multiple matches require presenting candidates and asking the user to choose. Reuse the confirmed `PROJECT_KEY` downstream.
3. Use as needed: `uip tm testsets list --project-key <PROJECT_KEY> --filter <TEST_SET_NAME_OR_KEY> --output json`; `uip tm testsets list-testcases --project-key <PROJECT_KEY> --test-set-key <TEST_SET_KEY> --output json`; `uip tm executions list --project-key <PROJECT_KEY> --test-set-id <TEST_SET_ID> --limit 100 --output json`; `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json`; `uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID> --output json`; `uip tm teststeplog list --project-key <PROJECT_KEY> --test-case-log-id <TEST_CASE_LOG_ID> --output json`.

## Troubleshooting

For `401 Unauthorized` on a REST API, run `uip login` to re-authenticate. For an unexpected command failure, first verify syntax with `uip tm <command> --help`, then authentication with `uip login status --output json`; Critical Rule 10 still governs whether to proceed.

## Navigate to a Workflow

- Failed-run root cause, assertions, step logs, evidence, and flaky-versus-regression analysis: [references/failure-triage-guide.md](references/failure-triage-guide.md)
- Shareable tester or release-manager report: [references/test-result-report-guide.md](references/test-result-report-guide.md)
- Publish a project and link it to a Test Manager testcase (Studio/RPA): [references/publish-and-link-guide.md](references/publish-and-link-guide.md)
- Pack, ingest, label, and run Playwright on serverless: [references/playwright-first-mile-guide.md](references/playwright-first-mile-guide.md)
- Custom-field definitions, labels, and values (`uip tm customfield`): [references/custom-fields-guide.md](references/custom-fields-guide.md)
- Object labels / tag metadata on test entities (`uip tm objectlabel`): [references/object-labels-guide.md](references/object-labels-guide.md)

## Anti-patterns

- **Do not proceed if authentication fails:** all Test Manager API calls require a valid bearer token; fail fast rather than causing later 401s.
- **Do not guess command names:** verb-noun composites are required; bare verbs do not exist. Confirm with `uip tm <resource> --help --output json`.
- **Do not `link-automation` Playwright test cases:** ingestion links them automatically; manual linking is only for the Studio/RPA pipeline.
