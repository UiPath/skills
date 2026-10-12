# Test executions guide (`uip tm executions`)

Deep reference for the Test Manager execution surface. Load this when a task
touches an execution's lifecycle, filtered reads, export, or reporting date.
Every command is `uip tm executions <verb>`; all take `--project-key <KEY>` or
`--project-id <ID>` (id wins if both are given) and default to `--output json`.

## The surface

| Verb | What it does |
|------|--------------|
| `list` | Top-N executions for a project or `--test-set-id`. |
| `list-filtered` | Full filtered read (status / execution-type / finished-interval / labels / search / updated-by / test-execution-ids), the with-stats DTO. |
| `get-stats` | One execution by `--execution-id`, aggregated pass/fail/none plus `Status` and `ExecutionFinished`. |
| `run` | Re-run an execution (`--execution-id`), optionally `--test-case-log-ids`, `--async`. |
| `retry` | Re-run only the failed cases of a finished execution. |
| `testcaselogs list` | The run's per-case logs (`--only-failed`, `--filter`, `--limit`/`--offset`). Nested, not a top-level verb. |
| `finish` | Close a **manual** run early. |
| `delete` | Soft-delete an execution and its logs/snapshots. Needs `--yes`. |
| `cancel` | Ask Orchestrator to stop a **running automated** run. |
| `export` | Write the filtered executions to an `.xlsx`. `--output-file` required. |
| `set-reporting-date` | Book a **closed** run against a day for reporting. |

There is **no `executions create`**. Open a manual execution with
`uip tm testsets run --test-set-key <KEY> --execution-type manual`; its
`Data.ExecutionId` is the run you then record with `testcaselog start`/`finish`.

## The manual-execution lifecycle

1. `testsets run --test-set-key <KEY> --execution-type manual` → `Data.ExecutionId`.
2. `executions testcaselogs list --execution-id <ID>` → one row per case with
   `TestCaseId` + `TestCase.Name`. This is how you resolve the ids `testcaselog`
   takes — one call for the whole run.
3. `testcaselog start` then `testcaselog finish --result <...> --has-error <...>
   --executed-by <email>` per case.
4. **The run closes itself** once its last *manual* log finishes
   (`ExecutionFinished` is stamped). `executions finish` is only the force-close
   for a run you want to end with logs still open — not the normal last step.

## Traps

- **`finish` stamps `ExecutionFinished`, never `Status`.** An early-closed run
  still reads `Status: Running`; recognise a closed run by the `ExecutionFinished`
  timestamp in `get-stats`. `uip tm wait` therefore does **not** return on an
  early-closed run — it polls to `--timeout` (default 1800s) then reports a
  timeout. `finish` is refused on a not-started run (400) and on an
  already-closed one (400), and on an Orchestrator-sourced run.
- **`cancel`: read `Data.Status`, not the exit code.** `Cancelling` = the stop was
  recorded; `Running` = it was only forwarded to Orchestrator (legacy dispatch or
  no live work left); a terminal status = the run was already over. A manual run
  has no job to stop and is refused — close those with `finish`.
- **`delete` is irreversible and has no state guard** — a running execution
  deletes exactly like a finished one, cascading to its logs and log snapshots,
  so cancel an automated run first if its jobs should stop too. `--yes` is
  required; the CLI never prompts.
- **`export` needs a licensed user**, so a caller who can `list-filtered` may
  still be refused. An empty filter still writes a valid zero-row workbook and
  reports Success — verify the filter, not the exit code. `OutputFile` echoes the
  `--output-file` value verbatim.
- **`set-reporting-date` only works on a closed run** (check `ExecutionFinished`,
  not `Status`). It accepts `2019-01-01` through `9999-12-31`; an earlier date is
  rejected. A value carrying a time must carry an offset, or a local-time reading
  books a different day depending on where the command runs. Setting it again
  overwrites.

## Error contract (how to read failures)

Failures are classified, and the exit code follows the `Result`:

| Server | `Result` | exit |
|--------|----------|------|
| 400 (bad argument / bad date / already-closed) | `ValidationError` | 3 |
| 401 / 403 (scope, licence, permission) | `AuthenticationError` | 2 |
| 404 / 5xx / other | `Failure` | 1 |

Branch on `Result`, not a guessed message. A bad `--reporting-date` (before
2019, or malformed) comes back `Result: ValidationError`, exit 3 — a
deterministic rejection, not something to retry.
