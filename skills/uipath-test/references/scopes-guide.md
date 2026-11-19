# Scopes for `uip tm`

Which OAuth scopes each `uip tm` command needs, and how to log in an external application with them.

## When Scopes Matter

| Login | What Test Manager checks | Action |
|---|---|---|
| User (`uip login`, browser) | Your project roles and tenant permissions. No scope list. | None. Use this guide only to explain a `403`. |
| External application (`uip login --client-id <CLIENT_ID> --client-secret env.<SECRET_VAR>` or `--client-assertion env.<TOKEN_VAR>`) | The application scopes in the token. | Grant the scopes below to the app (Admin → External Applications), then log in with an explicit `--scope` list. |

Without `--scope`, Identity puts every scope the app holds into the token. A long list makes the login fail, so always pass `--scope`. Every scope in it must be granted to the app.

## Rules

1. Before an app login, collect the scopes for every command you will run from the tables below, union them, and pass one list: `uip login --client-id <CLIENT_ID> --client-secret env.<SECRET_VAR> --scope "<SCOPES>" --tenant <TENANT_NAME> --output json`.
2. Grant and request the full scope (`TM.TestCases`), not `TM.TestCases.Read`. A `.Read` scope covers only GET requests; many list, filter, and search commands send POST and need `TM.X` or `TM.X.Write`.
3. Every command that takes `--project-key`, `--project-id`, or `--test-set-key`, or that falls back to the default project, also needs `TM.Projects`.
4. On `403`, `permission_denied`, or a `401` saying the token carries no scope for this API: run `uip login status --detailed --output json` and compare `Data.Scopes` with the tables. If a scope is missing, name it and tell the user to grant it to the app and log in again with it in `--scope`. Do not retry the command (Critical Rule 10). If every scope is present, the cause is a project role, licence, or feature flag: report `Message` and stop.
5. A user login never needs this list. Do not ask a user who signed in through the browser to add scopes.

## Test Manager Scopes

Base scope applies to every command in the group. "Also" lists extra scopes for specific commands; an extra named with a flag applies only when that flag is passed.

| Commands | Base scope | Also |
|---|---|---|
| `project` (`list`, `get-default`, `create`, `update`, `delete`, `export`, `import`, `set-default-folder`, `clear-default-folder`, `owners list`, `settings get`/`update`), `project-permissions get`, `migration get`/`list`/`download`, `export-jobs get` | `TM.Projects` | `project update --set-default`: `TM.Administration` |
| `migration schemas list`/`download` | `TM.Users` (or `TM.Users.Read`) | — |
| `testcases` (CRUD, `clone`, `export`, `steps`, `parameters`, `list-*`, `group-by`, `bulk-create`) | `TM.TestCases` | `run`: `TM.TestSets`, `TM.TestExecutions`. `add`, `remove`, `list-testsets`: `TM.TestSets`. `link-automation`, `link-package`: `TM.TestExecutions`. `list-automations`, `list-result-history`: `TM.TestExecutions` in place of `TM.TestCases`. `bulk-create`: `TM.CustomFieldDefinitions` (custom fields in the file), `TM.Requirements` (requirement links in the file). `group-by --field` on a custom field: `TM.CustomFieldDefinitions`. `export --wait`: `TM.Attachments` |
| `testsets` (all verbs), `schedules` | `TM.TestSets` | `run --wait`, `list --include-last-execution`: `TM.TestExecutions`. `create --dynamic-labels`, `list-testcases`, `get-dynamic-assignment`, `set-execution-order`, `assign-user`: `TM.TestCases` |
| `executions`, `testcaselog`, `teststeplog list`, `report get`, `wait` | `TM.TestExecutions` | `executions export --wait`, `report export --wait`: `TM.Attachments` |
| `result download` | `TM.TestExecutions` | `TM.TestSets` |
| `run --type package` | `TM.TestSets`, `TM.TestExecutions` | Orchestrator scopes below |
| `requirements` | `TM.Requirements` | `generate-testcases`, `evaluate`, `find-obsolete-testcases` with `--attachment-ids`, and `export --wait`: `TM.Attachments`. `generate-testcases --create`, `find-obsolete-testcases --delete`: `TM.TestCases` |
| `attachment` | `TM.Attachments` | `list --test-case-keys` or `--all --object-type TestCase`: `TM.TestCases`. `list --requirement-keys` or `--all --object-type Requirement`: `TM.Requirements`. `list --all --object-type TestSet`: `TM.TestSets`. `download --execution-id`: `TM.TestExecutions` |
| `customfield` (definitions) | `TM.CustomFieldDefinitions` | — |
| `customfield label`, `customfield value` | `TM.CustomFieldValues` | — |
| `objectlabel` | `TM.ObjectLabels` | — |
| `defects` | `TM.Defects` | `create`: `TM.TestCases` |
| `prompts` | `TM.Prompts` | — |
| `perf-scenario` | `TM.PerformanceScenarios` | `execute`, `executions list`, `load-groups get`/`list`, `jobs list`, `robot-logs list`: `TM.PerformanceScenarioExecutions`. `load-groups add --test-case-key`: `TM.TestCases`. `load-groups add` without `--package-version`: `TM.TestExecutions` |

No scope is checked for: `pack` (offline), `user get`, polling a requirement AI job (`--wait`, `--activity-id`), and the performance service commands `results get`, `http-errors list`, `automation-errors list`, `transaction-metrics list`, `report generate`/`compare`, and `stop`, which check sign-in only.

## Orchestrator Scopes

Commands that resolve folders, packages, users, or machines in Orchestrator need Orchestrator scopes too.

| Commands | Scopes |
|---|---|
| `run --type package` | `OR.Folders.Read`, `OR.Execution.Read`. With `--project-path` (uploads the package): `OR.Execution` |
| `testcases link-automation`, `link-package`; `testcases list --automated` with a folder; `testsets set-folder`, `autoselect-packages` with `--folder-path`; `testsets set-robot`, `set-execution-target` with `--robot-name` | `OR.Folders.Read` |
| `testsets set-robot`, `set-execution-target` with `--robot-user-key`, or with `--robot-name` on a test set that has no folder | `OR.Users.Read` |
| `testsets set-execution-target --machine-name` | `OR.Machines.Read` |
| `testsets assign-user`, `testcaselog assign` with `--assignee-email` | `OR.Users.Read` |

An app cannot use the personal-workspace fallback for `--folder-path`: pass the full folder path or `--folder-key`.

## Copy-ready `--scope` Lists

CI run of an uploaded package (`uip tm run --type package`):

```text
TM.Projects TM.TestSets TM.TestExecutions OR.Folders.Read OR.Execution.Read
```

Same with `--project-path` (pack and upload in the same command): replace `OR.Execution.Read` with `OR.Execution`.

Every `uip tm` command group:

```text
TM.Projects TM.TestCases TM.TestSets TM.TestExecutions TM.Requirements TM.Attachments TM.ObjectLabels TM.CustomFieldDefinitions TM.CustomFieldValues TM.Defects TM.Prompts TM.PerformanceScenarios TM.PerformanceScenarioExecutions OR.Folders.Read OR.Execution OR.Users.Read OR.Machines.Read
```

Add `TM.Users` for `migration schemas` and `TM.Administration` for `project update --set-default` only when those commands run.
