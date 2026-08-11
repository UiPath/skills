# Execute Query Failure — Wrong Activity for the Statement Type

This scenario reproduces a runtime failure where an **`Execute Query`**
activity (which is for `SELECT` and returns a `DataTable`) is used to run
a **modification** statement — a `DELETE`. A modification produces no
result set, so `Execute Query` returns an **empty `DataTable`**. A
downstream `Assign` that reads `dt_Deleted.Rows(0)(0)` then throws
`System.ArgumentOutOfRangeException: There is no row at position 0`,
which Orchestrator surfaces as `Assign: There is no row at position 0.`

The surface symptom is an `ArgumentOutOfRangeException` at the `Assign`.
The root cause is the **wrong activity choice** at the `Execute Query` —
the empty `DataTable` is the structural consequence of running a `DELETE`
through a `SELECT` activity. The differential is the whole point of this
scenario.

## What this scenario uncovers

**Root Cause:** `Execute Query` was used to run
`DELETE FROM TempStaging WHERE LoadDate < '2026-05-01'`. The correct
activity for a modification is `Execute Non Query`, whose `AffectedRecords`
output (an `Int32`) carries the affected-row count. The fix is to
**switch to `Execute Non Query`** and read `AffectedRecords` — **not** to
add an empty-`DataTable` guard / `Try-Catch` around the existing
`Execute Query` (the playbook's named anti-pattern, which hides the bug
and leaves the count unobtainable).

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 7 — wrong activity for the statement type).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — `targetFramework: "Windows"`, a clean `Connect to Database` (`Microsoft.Data.SqlClient`), an `Execute Query` running a `DELETE` into `dt_Deleted`, and an `Assign` reading `CInt(dt_Deleted.Rows(0)(0))` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-7 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Data Operations` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `StagingCleanup` job.
3. `uip or jobs get <job-key> --output json` → `Info` carries `Assign: There is no row at position 0.` wrapping `System.ArgumentOutOfRangeException: There is no row at position 0.` at `Assign "Compute deleted count"`.
4. `uip or jobs logs <job-key> --output json` → the smoking-gun Trace lines: `Execute Query: executing 'DELETE FROM TempStaging WHERE LoadDate < ''2026-05-01''' (CommandType=Text); result set returned 0 rows`, then `Assign 'Compute deleted count': evaluating CInt(dt_Deleted.Rows(0)(0)) against an empty DataTable (0 rows)`.
5. `process/Main.xaml` → the `Execute Query` running a `DELETE` feeding an `Assign` that reads `Rows(0)`; `Connect to Database` is clean (`Microsoft.Data.SqlClient`).

This Trace is what lets the agent connect "empty `DataTable`" → "Execute
Query was used for a `DELETE`" → Branch 7. Without it, the failure looks
like a generic downstream null/empty bug.

## How this differs from sibling branches

| Dimension | branch 1 (null connection) | branch 2 (provider mismatch) | branch 3 (concatenation) | branch 4 (query in conn string) | branch 5 (timeout) | branch 6 (CLR crash) | branch 7 (wrong activity) (this) |
|---|---|---|---|---|---|---|---|
| Connection opens? | no | no | yes | no | yes | yes | **yes** |
| Statement runs? | no | no | rejected | no | times out | crashes process | **yes — DELETE runs fine** |
| Error signature | `NullReferenceException` | `Keyword not supported` | `A database error occurred` + syntax | conn-string parse error | `Timeout expired` | exit `0xE0434352` | **`ArgumentOutOfRangeException: There is no row at position 0` at the Assign** |
| Where the fault is | wiring/scope | provider/driver | the SQL text | property misplacement | DB-side duration | managed runtime | **wrong activity choice; empty DataTable downstream** |
| Fix | wire/scope the connection | switch to Microsoft.Data.SqlClient | parameterize the query | move SQL to the Sql property | raise `TimeoutMS` / fix the query | bound the result set / update package | **switch to Execute Non Query, read AffectedRecords** |

The failing layer here is the **activity choice**, not the connection,
the SQL text, a timeout, or the database. The `DELETE` ran successfully;
the empty `DataTable` is structural (a modification never returns rows),
so the `Rows(0)` fault is **not a data problem**. The agent must
recommend switching to `Execute Non Query` and reading `AffectedRecords`
— not adding an empty-`DataTable` guard / `Try-Catch`, and not blaming a
data problem, a null connection, a provider mismatch, a SQL syntax error,
a timeout, a CLR crash, or a DB outage.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (branch 7) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) identify that `Execute Query` was used for a `DELETE` (wrong activity for a modification), (b) explain the empty `DataTable` → `Rows(0)` fault is the structural consequence, and (c) recommend switching to `Execute Non Query` and reading `AffectedRecords` (NOT adding an empty-row guard / Try-Catch).

> Fixtures are **synthetic** — hand-authored from the documented branch-7
> signature, not captured from a real tenant.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-query-wrong-activity --apply
```
