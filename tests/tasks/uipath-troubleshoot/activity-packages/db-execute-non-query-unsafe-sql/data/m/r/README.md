# Execute Non Query Failure — Unsafe SQL Construction (Branch 2)

This scenario reproduces a runtime `Execute Non Query` failure caused by
**building SQL with string concatenation**. The activity concatenates
UiPath variables straight into an `INSERT`; at runtime one variable holds
a value with an apostrophe (`O'Brien`), the apostrophe closes the SQL
string literal early, and the provider rejects the malformed statement.
Orchestrator surfaces `Execute Non Query: A database error occurred`
wrapping a `Microsoft.Data.SqlClient` `SqlException`:
`Unclosed quotation mark after the character string ')'.` /
`Incorrect syntax near 'Brien'.`

## What this scenario uncovers

**Root Cause:** The `Execute Non Query` activity's `Sql` is built as
`"INSERT INTO Customers (Name, City) VALUES ('" + in_CustomerName + "', '" + in_City + "')"`.
With `in_CustomerName = "O'Brien"` the resolved SQL becomes
`INSERT INTO Customers (Name, City) VALUES ('O'Brien', 'Austin')` — the
embedded apostrophe breaks the literal, so SQL Server fails to parse it.
The fix is to **parameterize**: use a static
`INSERT INTO Customers (Name, City) VALUES (@name, @city)` and map
`in_CustomerName` → `@name`, `in_City` → `@city` via the activity's
Parameters collection (the provider handles quoting/typing). This also
closes the SQL-injection risk. Escaping/doubling the apostrophe is **not**
the correct fix.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-non-query-failures.md`
(BRANCH 2 — unsafe SQL construction / parameter mapping).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Non Query whose `Sql` is a concatenation expression, behind a valid Connect/Assign structure, with no Parameters collection |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Sales Operations` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `CustomerUpsert` job.
3. `uip or jobs get <job-key> --output json` → `Info` carries `Execute Non Query: A database error occurred` wrapping `Unclosed quotation mark after the character string ')'. Incorrect syntax near 'Brien'.`
4. `uip or jobs logs <job-key> --output json` → a Trace line showing the **resolved** SQL `... VALUES ('O'Brien', 'Austin')` — the smoking gun proving the apostrophe broke the literal.
5. `process/Main.xaml` → the `Execute Non Query` `Sql` is the concatenation expression `"...VALUES ('" + in_CustomerName + "', '" + in_City + "')"` with `in_CustomerName` assigned `O'Brien`, and no Parameters collection.

## How this differs from sibling branches

| Dimension | branch 1 (output param Size=0) | branch 2 (concatenation) (this) | branch 3 (empty Sql) | branch 4 (driver load) |
|---|---|---|---|---|
| Connection opens? | yes | **yes** | yes | n/a |
| Error signature | `The Size property has an invalid size of 0` | **`A database error occurred` + `Unclosed quotation mark` / `Incorrect syntax near ...`** | `CommandText property has not been initialized` | `Failed to load library (ErrorCode: 126)` / `DllNotFoundException` |
| Where the fault is | output-parameter sizing (ODBC) | **the SQL text** | blank/`""` Sql expression | host driver/client + bitness |
| Fix | set output param `Size` | **parameterize via Parameters collection** | populate the Sql / guard empty | install the driver at matching bitness |

The failing layer here is the **statement text**, not the connection, a
driver, an empty command, or an output-parameter size. The agent must
recommend parameterizing with named `@parameters` via the Parameters
collection — not escaping/doubling the apostrophe, not switching to
`Execute Query`, not blaming the connection or the database.

## Synthetic note

The fixtures under `fixtures/mocks/responses/` are **hand-authored** from
the documented branch-2 signature in `execute-non-query-failures.md`, not
captured from a real tenant. All identifiers (folder key, job key,
hostname, account) are synthetic. Replace with verbatim captures from a
real `.local/investigations/` before treating this as a regression signal.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-non-query-failures playbook (branch 2) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) name the unclosed-quote / syntax error from string concatenation, (b) attribute it to building the Sql by concatenating an apostrophe-bearing value (`O'Brien`) and note the injection risk, and (c) recommend parameterizing with named `@parameters` via the Parameters collection.

The `llm_judge` grades only the agent's final response and tool-call
summary against `RESOLUTION.md`. It does **not** inspect internal
investigation state (`.local/investigations/`, `state.json`,
`hypotheses.json`).

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-non-query-unsafe-sql --apply
```
