# Test executions guide (`uip tm executions`)

Deep reference for the execution lifecycle, filtered reads, export, and reporting
date. Every verb is `uip tm executions <verb>`; all take `--project-key <KEY>` (or
`--project-id`, which wins if both are given) and default to `--output json`.

## The surface

`list` (top-N, or `--test-set-id`) · `list-filtered` (status / execution-type /
finished-interval / labels / `--search` / updated-by / test-execution-ids) ·
`get-stats` (one run by `--execution-id`, aggregated pass/fail/none + `Status` +
`ExecutionFinished`) · `run` / `retry` (re-run all / only the failed cases) ·
`testcaselogs list` (per-case logs, `--only-failed`/`--filter`/`--limit`/`--offset`;
nested, not a top-level verb) · `finish` (force-close a manual run) · `delete`
(soft-delete + logs/snapshots, `--yes`) · `cancel` (stop a running automated run) ·
`export` (filtered → `.xlsx`, `--output-file` required) · `set-reporting-date`
(book a closed run against a day).

There is **no `executions create`** — open a manual run with
`uip tm testsets run --test-set-key <KEY> --execution-type manual`; its
`Data.ExecutionId` is what you record with `testcaselog start`/`finish`.

## Manual-execution lifecycle

1. `testsets run --test-set-key <KEY> --execution-type manual` → `Data.ExecutionId`.
   Every log the run creates is Manual even for automated cases; the default
   `--execution-type automated` instead dispatches the automations.
2. `executions testcaselogs list --execution-id <ID>` → one row per case with
   `TestCaseId` + `TestCase.Name`; resolves every id in one call.
3. `testcaselog start` then `testcaselog finish --result <...> --has-error <...>
   --executed-by <EMAIL>` per case. **All three finish flags are required** — omit
   any and it is a `ValidationError`/exit 3 with an empty message. `--executed-by` is
   stored as the authenticated caller whatever you pass, so pass your own login email
   (`uip login status` → `Data.UserEmail`) when the session names no executor.
4. **The run closes itself** once its *last* manual log finishes (`ExecutionFinished`
   is stamped); finishing only some logs of a multi-case run leaves it open. To close
   an open run on purpose, first `start` at least one log — a run with no started log
   cannot be closed at all — then either `finish` every log or `executions finish` to
   force-close the rest. `executions finish` is the only force-close and is **refused
   on a run with no started log**.
5. Report the run's totals with `get-stats --execution-id <ID>` (its own
   `Passed`/`Failed`/`None` aggregate), never by hand-counting the results you recorded.

## Traps

- **`finish` stamps `ExecutionFinished`, never `Status`.** An early-closed run still
  reads `Status: Running`; recognise a closed run by the `ExecutionFinished` timestamp.
  `uip tm wait` therefore does not return on it — it polls to `--timeout` (default
  1800s) then reports a timeout. `finish` is refused (400) on a not-started run, an
  already-closed one, and an Orchestrator-sourced run.
- **`set-reporting-date` only works on a closed run** (check `ExecutionFinished`, not
  `Status`). Range `2019-01-01`–`9999-12-31`; a value carrying a time must carry an
  offset, or the booked day shifts with the command's local time. Setting it again
  overwrites.
- **`export` needs a licensed user** — a caller who can `list-filtered` may still be
  refused — and an empty filter still writes a valid zero-row workbook reporting
  Success, so verify the filter, not the exit code.
- **`cancel`: read `Data.Status`, not the exit code.** `Cancelling` = the stop was
  recorded; `Running` = only forwarded to Orchestrator (legacy dispatch or no live work
  left); terminal = already over. A manual run has no job to stop and is refused — close
  those with `finish`.
- **`delete` is irreversible and has no state guard** — a running execution deletes
  like a finished one, cascading to logs and snapshots, so cancel an automated run
  first if its jobs should stop too. `--yes` required; never prompts.

## Error contract

Exit code follows `Result`: `ValidationError` → 3 (400: bad argument/date,
already-closed), `AuthenticationError` → 2 (401/403: scope, licence, permission),
`Failure` → 1 (404 / 5xx / other). Branch on `Result`, not a guessed message — a bad
`--reporting-date` (before 2019, or malformed) is `ValidationError`/exit 3, a
deterministic rejection, not something to retry.
