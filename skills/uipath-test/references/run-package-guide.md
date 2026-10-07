# Run an Uploaded Test Package (CI)

`uip tm run --type package` runs every test in a package that is already uploaded to Orchestrator, waits for the results, re-runs failures, writes a JUnit or UiPath JSON report, and sets the exit code a CI step reads. It replaces `uipcli test run`. Use it whenever the user wants "all the tests in this package" run, instead of chaining `link-package` → `testsets create` → `testsets run` → `wait` → `result download` by hand.

Packing and uploading are separate (`uip rpa pack`, `uip or packages upload`); this command starts from the uploaded package.

## Command

```bash
uip tm run --type package --package-name <PACKAGE_NAME> --package-version <VERSION> --folder-path <FOLDER_PATH> --project-key <PROJECT_KEY> --result-path <DIR> --output json
```

| Option | Required | Notes |
|---|---|---|
| `--type package` | Yes | What to run. `package` is the only type today. |
| `--package-name` | Yes | Package id as uploaded to Orchestrator. |
| `--package-version` | Yes | `1.0` (app version) runs the latest `1.0.x` patch. An exact version (`1.0.244878764`) must be the latest patch of its app version; an older one is refused. After a fresh upload in CI, pass the exact version just published so the command waits for that build. |
| `--folder-path` / `--folder-key` | One of them | Orchestrator folder the tests run in. Get the key with `uip or folders list -n <folder-name> --all --output json` when only the name is known. |
| `--project-key` / `--project-id` | One of them | Test Manager project the tests run in. Get keys with `uip tm project list --output json`. |
| `--input-path <file>` | No | JSON array `[{"name": "Param", "value": "v"}]`, optional `"type"`. One file for the whole test set; applied to every test that declares the name. |
| `--max-retries <n>` | No | Re-run only failed tests, in the same execution. Default 0. |
| `--format junit\|uipath` | No | Report format. Default `junit`. |
| `--result-path <path>` | No | Report file or directory. Default: current directory. |
| `--include-passed-assertions` | No | Also read passed tests' assertions; by default only failed and cancelled tests get them. |
| `--timeout <s>` | No | One budget for the whole run, retries included. Default 7200; 0 means none. |

The command creates a hidden, one-off test set. It does not need, and should not be preceded by, `testcases link-package`, `testsets create`, or `testcases add`.

## Reading the result

| Exit | `Result` / `Code` | Meaning |
|---|---|---|
| 0 | `Success` / `RunPackage` | Every test passed. `Data` has `ExecutionId`, `ExecutionUrl`, `PackageVersion` (the exact version that ran), counts and `OutputPath`. |
| 1 | `Failure` / `RunPackageTestsFailed` or `RunPackageCancelled`, `ErrorCode: execution_failed` | The run finished but a test failed or no tests ran (`RunPackageTestsFailed`), or the execution was cancelled (`RunPackageCancelled`). `Data` still carries the full summary, and the report was written. This is a test result, not a CLI error: report it, do not retry. |
| 1 | `Failure`, other `ErrorCode` | The run could not start or finish (version or folder not found, service error). `Message` says what, `Instructions` what to do. |
| 2 | `AuthenticationError`, `ErrorCode: permission_denied` or `authentication_required` | The login or a permission is the problem (401/403, missing scope, no role on the folder or project). Fix the login; do not retry. |
| 3 | `ValidationError`, `ErrorCode: invalid_argument` | A bad option or input: missing project, malformed version, an older patch, a bad `--input-path` file. Nothing was created. |
| 4 | `TimeoutError`, `ErrorCode: timeout` | `--timeout` ran out, or Test Manager did not index the package within 5 minutes. The execution may still be running. If the tests had started, `Data.OutputPath` holds a report of what finished, with unfinished tests marked skipped. Report the timeout; do not treat skipped tests as passed. |

A failed test's JUnit `<testcase>` has `<failure type="AssertionError">` when an assertion failed, or `<error type="Fault">` when the job or robot faulted (for example a package that cannot be installed).

## Common errors

| `Message` starts with | Fix |
|---|---|
| `… is not the latest 1.0.x patch (… is)` | Pass the latest patch it names, or the app version (`1.0`). |
| `Version … of … is not uploaded` / `No 1.0.x version of …` | Check `uip or packages versions <PACKAGE_NAME> --output json`. |
| `Folder '…' not found.` | Use `uip or folders list -n <folder-name> --all --output json`. |
| `Input file '…'` / `Entry N in '…'` | Fix the `--input-path` file; nothing was created. |
| `Orchestrator refused to …(403)` | Exit 2. The login needs `OrchestratorApiUserAccess`, or `OR.Folders.Read` and `OR.Execution`, and a role on the folder. |
| `No project was given.` | Pass `--project-key` or `--project-id`. |

## Requirements

A user login or an external app with `TM.Projects`, `TM.TestSets`, `TM.TestExecutions`, `OR.Folders.Read` and `OR.Execution` (or `.Read`). Check with `uip login status --output json`.
