# Execute Query Failure — Failed to Enable Constraints (DataTable schema violation)

This scenario reproduces a runtime `Execute Query` failure where the **query
executes fine** but the returned rows violate the schema `Execute Query`
auto-infers for the result `DataTable`. Orchestrator surfaces
`Execute Query: Failed to enable constraints. One or more rows contain values
violating non-null, unique, or foreign-key constraints.`
(`System.Data.ConstraintException`).

## What this scenario uncovers

**Root Cause:** The `Execute Query 'Customer Orders'` activity's `Sql` is
`SELECT * FROM Customers c INNER JOIN Orders o ON c.CustomerId = o.CustomerId`
— a **one-to-many** join (one customer has many orders). `Execute Query` fills a
`DataTable` whose schema it infers from the source columns, so `CustomerId`
(the primary key of `Customers`) is marked **unique**. The join repeats
`CustomerId` once per order, so `DataTable.EnableConstraints()` throws the
constraint exception. The failure is in the **shape of the result set vs. the
inferred schema**, not in the SQL syntax (the statement parsed and ran).

The fix is to **reshape the query so the returned key column is unique** — stop
using `SELECT *` and select the explicit columns you need at the intended grain
(e.g. project the order key `OrderId`, which is unique, or drop the repeating
`CustomerId`). `SELECT DISTINCT` does **not** help here (rows differ by order),
and disabling constraint enforcement only hides the schema mismatch.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 8 — DataTable constraint enablement fails).

## Why the cause is not one-shot from the log

The error text names the constraint **category** ("non-null, unique, or
foreign-key") but not **which** column or **why**. So the log alone does not
give the diagnosis — the agent must read the workflow `Sql`, recognise the
`SELECT *` over a one-to-many `JOIN`, and connect the repeated `CustomerId` to
the inferred unique constraint. This deliberately mirrors the
`db-execute-query-sql-syntax-error` / `classic-openapp` design so the scenario
exercises the skill rather than being answerable from a single `jobs logs` read.
Plausible wrong turns to avoid: blaming bad data in the database, a connection
problem, a SQL *syntax* error (branch 3), or recommending "set
EnforceConstraints=false" as the fix.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Query whose `Sql` is `SELECT *` over a 1-to-many Customers→Orders JOIN |
| `data/m/r/*.json` | **synthetic** canned `uip` responses authored from the documented branch-8 signature |
| `data/m/r/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list` → the `Reporting` folder.
2. `uip or jobs list` → the single faulted `CustomerOrderReport` job.
3. `uip or jobs get <job-key>` → `Info` carries `Failed to enable constraints ...` wrapping `System.Data.ConstraintException` at `DataTable.EnableConstraints`.
4. `uip or jobs logs <job-key>` → Trace lines show the query started and then faulted at constraint enablement (no provider syntax error).
5. `process/Main.xaml` → the `Execute Query` `Sql` is the `SELECT *` over the one-to-many `Customers`→`Orders` join.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (branch 8) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) recognise the fault is a `DataTable` constraint violation on the auto-inferred schema, (b) tie it to the `SELECT *` over a one-to-many JOIN repeating the inferred key column, and (c) recommend reshaping the query so the returned key is unique (explicit columns at the correct grain) — not disabling constraints, not blaming DB data, not a syntax fix.
