# Test executions guide (`uip tm executions`)

Reference for execution lifecycle, filtered reads, export, and reporting date. Every verb is `uip tm executions <verb>`; all take `--project-key <KEY>` (or `--project-id`, which wins if both are given) and default to `--output json`.

## The surface

`list` (top-N or `--test-set-id`); `list-filtered` (status, execution-type, finished-interval, labels, `--search`, updated-by, test-execution-ids); `get-stats` (one run via `--execution-id`, aggregated pass/fail/none plus `Status` and `ExecutionFinished`); `run`/`retry` (all or failed cases); nested `testcaselogs list` (per-case logs; `--only-failed`, `--filter`, `--limit`, `--offset`); `finish` (force-close a manual run); `delete` (soft-delete with logs/snapshots; `--yes`); `cancel` (stop a running automated run); `export` (filtered `.xlsx`; `--output-file` required); `set-reporting-date` (book a closed run against a day).

There is **no `executions create`**. Run `uip tm testsets run --test-set-key <KEY> --execution-type manual` to open a manual run; record its `Data.ExecutionId` for `testcaselog start`/`finish`.

## Manual-execution lifecycle

1. Run `testsets run --test-set-key <KEY> --execution-type manual` and use `Data.ExecutionId`. Every log it creates is Manual, including automated cases; the default `--execution-type automated` instead dispatches automations.
2. Run `executions testcaselogs list --execution-id <ID>` to get one row per case with `TestCaseId` and `TestCase.Name`; it resolves every id in one call.
3. Run `testcaselog start`, then `testcaselog finish --result <...> --has-error <...>` for each case.
4. The run closes when its last manual log finishes and stamps `ExecutionFinished`. Run `executions finish` only to force-close a run with logs still open.

## Traps

- **`finish` stamps `ExecutionFinished`, never `Status`.** An early-closed run still reads `Status: Running`; recognise a closed run by the `ExecutionFinished` timestamp. `uip tm wait` therefore polls until `--timeout` (default `1800s`) and reports a timeout. `finish` is refused (400) for a not-started, already-closed, or Orchestrator-sourced run.
- **`set-reporting-date` requires a closed run**: check `ExecutionFinished`, not `Status`. The range is `2019-01-01`–`9999-12-31`; a value with a time must include an offset or the booked day can shift with command local time. Re-setting overwrites.
- **`export` requires a licensed user**; `list-filtered` access is insufficient. An empty filter still writes a valid zero-row workbook reporting `Success`; verify the filter rather than the exit code.
- **`cancel`: read `Data.Status`, not the exit code.** `Cancelling` means the stop was recorded; `Running` means it was only forwarded to Orchestrator (legacy dispatch or no live work left); terminal means already over. A manual run has no job to stop and is refused; close it with `finish`.
- **`delete` is irreversible and has no state guard.** It deletes running executions like finished ones, cascading to logs and snapshots. Cancel an automated run first if its jobs must also stop. `--yes` is required; it never prompts.

## Error contract

Exit code follows `Result`: `ValidationError` → 3 (400: bad argument/date, already-closed), `AuthenticationError` → 2 (401/403: scope, licence, permission), `Failure` → 1 (404 / 5xx / other). Branch on `Result`, not a guessed message. A bad `--reporting-date` (before 2019 or malformed) is `ValidationError`/exit 3: deterministic rejection, not retryable.