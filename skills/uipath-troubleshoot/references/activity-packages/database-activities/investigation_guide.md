# Database Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's class matches the reported failure (`UiPath.Database.Activities.ExecuteQuery`, `ExecuteNonQuery`, `ExecuteCommand`, `DatabaseConnect`, `DatabaseTransaction`, `BulkUpdate`). `Execute Query` (SELECT → `DataTable`) and `Execute Non Query` (modification → `AffectedRecords`) share a connection model but differ in output type — treat a wrong-activity report as its own branch.
- **Database / connection** — the `ProviderName` and the server/database in the `ConnectionString` match the database the user is asking about. A connection string pointing at a different server, database, or provider is unrelated data.
- **SQL statement** — the `Sql` in evidence is the statement the user reports running. Do not substitute a similar query from another activity in the same workflow.
- **Project compatibility** — whether the project is **Windows** or **Windows - Legacy**, and whether the failure began right after a migration. Load-bearing for provider/driver-mismatch findings.
- **Robot / machine identity** — the Robot host where the job ran matches the one the user reports. Installed database drivers (ODBC/managed providers) are per-host; evidence from a different host is not transferable.
- **Package version** — the `UiPath.Database.Activities` version on the Robot matches the one the user reports. Provider-path behaviour and exception text shift across major versions.
- **Timestamp** — the failure occurred during the window the user reported. Load-bearing for timeout and CLR-crash investigations (transient blocking / memory pressure may not reproduce on demand).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

### Execute Query / Execute Non Query / Run Command

1. **Workflow source** — read the data-activity node from the `.xaml` to capture: how the connection is supplied (`ExistingDbConnection` variable vs inline `ConnectionString` + `ProviderName`), the literal `Sql` or bound expression, `CommandType`, `Parameters`, and `TimeoutMS`. For `ExistingDbConnection`, trace the variable back to the `Connect to Database` / `Start Transaction` that produces it and confirm scope and ordering.
2. **Inner provider exception** — from `uip or jobs get <job-key> --output json` → `Info`. UiPath wraps the provider error as `A database error occurred` / `Execute Query: <message>`; read the **inner** exception — it carries the real syntax error, provider code (`ORA-…`, SQL Server error number), or `Keyword not supported` text.
3. **Project compatibility + package version** — `project.json` (`targetFramework` / `Windows` vs `Windows-Legacy`) and the pinned `UiPath.Database.Activities` version. Required for provider-mismatch and CLR-crash branches.
4. **Property placement** — confirm the `SELECT` text is in the `Sql` property and the connection string is in `ConnectionString` (not crossed), and that the connection string's quotes are balanced.
5. **Result-set size / provider** — the expected row count the query materializes into a `DataTable`, and whether the engine is Oracle returning a `REF CURSOR`. Required for the `0xE0434352` CLR-crash branch.

### Connect to Database / Start Transaction

1. **Connection configuration** — the literal `ConnectionString` and `ProviderName` on the activity, and whether the matching driver is installed on the Robot host.
2. **Output variable wiring and scope** — the `DatabaseConnection` output variable name, the scope it is declared in, and every downstream data activity that reads it. A connection declared inside a nested `Sequence` is out of scope (and `Nothing`) for activities outside it.
3. **Transaction commit/rollback outcome (Start Transaction only)** — correlate the **job final state** with the **actual database effect** and the in-scope activity logs: a `Success` job with no committed data, or with no child-activity log lines at all, points to a transaction-specific fault (swallowed rollback or a body-skip package bug) rather than a child-statement error. Capture the `UiPath.Database.Activities` version (v1.5.0 is the known body-skip build) and confirm whether each child activity binds the scope's output connection to its `ExistingDbConnection` (a child on its own inline connection runs outside the transaction). See [start-transaction-failures.md](./playbooks/start-transaction-failures.md).

## Testing Prerequisites

When testing hypotheses for Database Activities issues, gather and verify these before drawing conclusions:

1. **Activity identity** — the exact faulted class and its display name; whether the statement verb matches the activity (SELECT→Execute Query, modification→Execute Non Query).
2. **Connection provenance** — inline connection vs `ExistingDbConnection`; if the latter, the producing `Connect`/`Start Transaction`, its output variable, scope, and execution order relative to the faulted activity.
3. **Inner provider message** — the unwrapped provider exception text and code, not just the UiPath `A database error occurred` wrapper.
4. **`Sql` and `Parameters`** — the resolved statement (log it if built from an expression) and whether values are parameterized (`@name` via `Parameters`) or concatenated into the string.
5. **`ProviderName` + driver availability** — the configured provider and whether its driver is installed on every Robot host that runs the process.
6. **Project compatibility** — Windows vs Windows-Legacy, and whether the failure coincided with a migration.
7. **`TimeoutMS` + DB-side duration** — the configured timeout (milliseconds) and the query's real runtime measured independently against the database.
8. **Package version** — the `UiPath.Database.Activities` version (provider-path and CLR-crash branches are version-sensitive).
