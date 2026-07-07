# Execute Query Failure — Query Text in the Connection-String Property

This scenario reproduces a runtime `Connect to Database` / `Execute
Query` failure caused by **crossed fields**: the SQL `SELECT` was pasted
into the `Connect to Database` activity's `ConnectionString` property,
and the real connection string was pasted into the `Execute Query`
activity's `Sql` property. When the connect step runs, the
`Microsoft.Data.SqlClient` connection-string parser tries to parse the
`SELECT` as a connection string and throws
`System.ArgumentException: Format of the initialization string does not
conform to specification starting at index 0`, which Orchestrator
surfaces as `Connect to Database: A database error occurred`.

## What this scenario uncovers

**Root Cause:** The two field values are swapped between the two
activities. `ConnectionString` holds the SELECT; `Sql` holds the
`Server=...;Database=...;...` connection string. The connection-string
parser rejects the SELECT at index 0 because it is not a `keyword=value;`
list. The fault is a **connection-string parse failure** at the connect
step — before any SQL ever runs. The fix is to **move the SELECT to the
`Sql` property and the connection string to the `ConnectionString`
property** (and balance the quotes).

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 4 — query text in the connection-string property).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — a `Connect to Database` whose `ConnectionString` is a SQL SELECT, feeding an `Execute Query` whose `Sql` is a connection string |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-4 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` -> the `Finance Automation` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` -> the single faulted `CustomerLedgerSync` job.
3. `uip or jobs get <job-key> --output json` -> `Info` carries `Connect to Database: A database error occurred` wrapping `System.ArgumentException: Format of the initialization string does not conform to specification starting at index 0.` raised in the `Microsoft.Data.SqlClient` connection-string parser at `Connect to Database`.
4. `uip or jobs logs <job-key> --output json` -> a Trace line showing the connect attempt opening a connection with the connection string set to the `SELECT ...` text.
5. `process/Main.xaml` -> `Connect to Database` `ConnectionString` = the SELECT; `Execute Query` `Sql` = the connection string (fields crossed).

## How this differs from sibling branches

| Branch | Signature | Where the fault is | Fix |
|---|---|---|---|
| 1 (null connection) | `NullReferenceException` at the activity | connection wiring / scope | wire/scope the connection |
| 2 (provider mismatch) | `Keyword not supported: '<kw>'` (ArgumentException) post-migration | provider/driver after migration | switch provider, fix keyword, install driver |
| 3 (SQL syntax / concatenation) | `A database error occurred` + `Incorrect syntax near ...` | the SQL text sent to the engine | parameterize / fix the SQL |
| **4 (query in connection string) (this)** | **`A database error occurred` + `Format of the initialization string does not conform to specification`** | **crossed fields — SELECT in `ConnectionString`** | **swap SELECT to `Sql`, connection string to `ConnectionString`** |
| 5 (timeout) | `Timeout expired` | DB-side duration | raise `TimeoutMS` / fix the query |
| 6 (CLR crash) | job exit `0xE0434352`, no activity exception | process-level fault | bound result set / update package |
| 7 (wrong activity) | empty/meaningless `DataTable`, or cast error | activity choice vs statement verb | use Execute Non Query for INSERT/UPDATE/DELETE |

Critically, this is **NOT branch 3**. Branch 3 is a SQL parse failure
(`Incorrect syntax near ...`) raised by the database engine after a
connection opens. Branch 4 is a **connection-string** parse failure
(`Format of the initialization string does not conform to
specification`) raised by the connection-string parser **before** any
SQL is sent and before any connection opens. The agent must distinguish
the two and not read the error as a SQL syntax problem or as "the
database does not exist".

## Success criteria

The test scores the **conclusion, not the trajectory**:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (branch 4) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) name the connection-string parse failure (`Format of the initialization string does not conform to specification`), (b) attribute it to the SQL SELECT being in the `ConnectionString` field (crossed fields), and (c) recommend moving the SELECT to `Sql` and the connection string to `ConnectionString` (and balancing quotes).

## A note on the fixtures

The fixtures here are **synthetic / hand-authored** from the documented
branch-4 signature in the playbook — not captured from a real
`.local/investigations/` run. Replace them with verbatim captures from a
real investigation before treating this scenario as a strict regression
signal.
