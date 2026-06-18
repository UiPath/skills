# Execute Query Failure — SQL Syntax Error from Unsafe Concatenation

This scenario reproduces a runtime `Execute Query` failure caused by
**building SQL with string concatenation**. The activity concatenates a
UiPath variable straight into the statement; at runtime the variable
holds a value with an apostrophe (`O'Brien`), the apostrophe closes the
SQL string literal early, and the provider rejects the malformed
statement. Orchestrator surfaces `Execute Query: A database error
occurred` wrapping a `Microsoft.Data.SqlClient` `SqlException`:
`Incorrect syntax near 'Brien'.`

## What this scenario uncovers

**Root Cause:** The `Execute Query` activity's `Sql` is built as
`"SELECT * FROM Customers WHERE LastName = '" + in_LastName + "'"`.
With `in_LastName = "O'Brien"` the resolved SQL becomes
`SELECT * FROM Customers WHERE LastName = 'O'Brien'` — the embedded
apostrophe breaks the literal, so SQL Server fails to parse it. The fix
is to **parameterize**: use a static `SELECT ... WHERE LastName =
@lastName` and map `in_LastName` to `@lastName` via the activity's
Parameters collection. This also closes the SQL-injection risk.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 3 — SQL syntax error / unsafe string concatenation).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Query whose `Sql` is a concatenation expression, behind a valid Connect/Execute structure |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-3 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Sales Automation` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `CustomerLookup` job.
3. `uip or jobs get <job-key> --output json` → `Info` carries `Execute Query: A database error occurred` wrapping `Incorrect syntax near 'Brien'. Unclosed quotation mark after the character string ''.`
4. `uip or jobs logs <job-key> --output json` → a Trace line showing the **resolved** SQL `... LastName = 'O'Brien'` — the smoking gun proving the apostrophe broke the literal.
5. `process/Main.xaml` → the `Execute Query` `Sql` is the concatenation expression `"...'" + in_LastName + "'"` with `in_LastName` defaulting to `O'Brien`.

## How this differs from sibling branches

| Dimension | branch 1 (null connection) | branch 2 (provider mismatch) | branch 3 (concatenation) (this) | branch 5 (timeout) |
|---|---|---|---|---|
| Connection opens? | no | no/garbled | **yes** | yes |
| Error signature | `NullReferenceException` | `Keyword not supported` | **`A database error occurred` + `Incorrect syntax near ...`** | `Timeout expired` |
| Where the fault is | wiring/scope | provider/driver | **the SQL text** | DB-side duration |
| Fix | wire/scope the connection | switch provider | **parameterize the query** | raise `TimeoutMS` / fix the query |

The failing layer here is the **statement text**, not the connection,
the driver, the table, or a timeout. The agent must recommend
parameterizing with a named `@parameter` — not escaping the quote, not
blaming the database, not adjusting a timeout.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (branch 3) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) recognize the SQL is built by concatenating `in_LastName`, (b) explain the apostrophe in `O'Brien` breaks the string literal, and (c) recommend parameterizing with a named `@parameter` via the Parameters collection.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-query-sql-syntax-error --apply
```
