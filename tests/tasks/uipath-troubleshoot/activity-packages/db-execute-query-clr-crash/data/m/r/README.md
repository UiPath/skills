# Execute Query Failure — CLR-Level Crash (`0xE0434352`) from an Oversized Result Set

This scenario reproduces a runtime `Execute Query` failure that crashes
the **managed runtime** rather than raising a clean activity exception.
The activity runs an unbounded `SELECT * FROM Transactions` over a
multi-million-row table and materializes the whole result set into a
single `DataTable`, exhausting the Robot process memory. The job
terminates at the **process level** with exit code `0xE0434352` and **no
clean activity-level exception** in the workflow log.

## What this scenario uncovers

**Root Cause:** The `Execute Query` activity's `Sql` is the unbounded
literal `"SELECT * FROM Transactions"` — no `TOP`/`FETCH FIRST`/`LIMIT`,
no `WHERE` — over a huge table. Loading every row into one `DataTable`
exhausts memory; the CLR crashes and the job exits with `0xE0434352`.
`0xE0434352` is the **generic .NET unhandled-exception SEH code**, not a
DB-specific code on its own; the database context (the oversized SELECT)
narrows it. The fix is to **bound the result set** in SQL
(`TOP`/`FETCH FIRST`/`LIMIT`) and **page** through large data; update
`UiPath.Database.Activities` if a provider-path bug is implicated.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 6 — CLR-level crash `0xE0434352`).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Query whose `Sql` is an unbounded `SELECT *`, behind a valid Connect/Execute structure |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-6 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Finance Automation` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `TransactionExport` job.
3. `uip or jobs get <job-key> --output json` → `Info` reports a process-level termination with exit code `0xE0434352` and **no activity-level exception** — the distinguishing Branch 6 shape.
4. `uip or jobs logs <job-key> --output json` → the connection opened, `Execute Query` started against `SELECT * FROM Transactions`, a Trace line notes it was "still reading result set into DataTable (no row limit set)", then the process died.
5. `process/Main.xaml` → the `Execute Query` `Sql` is the unbounded `"SELECT * FROM Transactions"` over a multi-million-row table.

## How this differs from sibling branches

| Dimension | branch 1 (null connection) | branch 3 (concatenation) | branch 5 (timeout) | branch 6 (CLR crash) (this) |
|---|---|---|---|---|
| Connection opens? | no | yes | yes | **yes** |
| Error signature | `NullReferenceException` | `A database error occurred` + `Incorrect syntax near ...` | `Timeout expired` | **exit `0xE0434352`, no clean activity exception** |
| Where the fault is | wiring/scope | the SQL text | DB-side duration | **process memory (data volume)** |
| Fix | wire/scope the connection | parameterize the query | raise `TimeoutMS` / fix the query | **bound the result set (`TOP`/`FETCH`/`LIMIT`) + page** |

The failing layer here is the **Robot process memory** driven by the
**data volume**, not the connection, the SQL syntax, the driver, or a
timeout. The crash is process-level (`0xE0434352`) with no clean activity
exception — the distinguishing evidence shape. The agent must recommend
bounding the result set in SQL and paging — not raising a timeout, not
parameterizing, not blaming the database.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (branch 6) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) recognize the unbounded `SELECT *` over a huge table materializing into a `DataTable`, (b) attribute the failure to memory exhaustion surfacing as the `0xE0434352` CLR / process-level crash with no clean activity exception, and (c) recommend bounding the result set with `TOP`/`FETCH FIRST`/`LIMIT` and paging (and updating `UiPath.Database.Activities` where a provider-path bug is implicated).

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-query-clr-crash --apply
```
