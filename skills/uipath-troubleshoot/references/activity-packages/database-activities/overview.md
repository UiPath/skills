# Database Activities

Activities from the `UiPath.Database.Activities` package for querying and modifying relational databases over ADO.NET. Every data activity runs against a `DatabaseConnection` opened by a `Connect to Database` or `Start Transaction` activity, or against an inline `ConnectionString` + `ProviderName` configured on the activity itself. The underlying provider (SQL Server, Oracle, MySQL, ODBC, OLE DB, …) is selected by `ProviderName` and determines connection-string syntax and error text.

## How Database Activities Connect

The package separates **connection** from **execution**:

1. **Open** — `Connect to Database` (`DatabaseConnect`) or `Start Transaction` (`DatabaseTransaction`) takes a `ConnectionString` + `ProviderName` and produces a `DatabaseConnection` object as output.
2. **Execute** — `Execute Query`, `Execute Non Query`, `Run Command`, and the bulk/insert activities consume that connection via their `ExistingDbConnection` input (or carry their own inline `ConnectionString` + `ProviderName` and open a throwaway connection per call).
3. **Close** — `Disconnect`, the end of the `Connect to Database` scope, or the `Start Transaction` commit/rollback releases the connection.

A data activity therefore fails for one of two broad reasons: the **connection** it was handed is missing/invalid/expired (open step), or the **statement** it ran is wrong (execute step). Knowing which step produced the error narrows the investigation.

## Key Activities

- **Connect to Database** (`DatabaseConnect`) — open a connection. Properties: `ConnectionString`, `ProviderName`, output `DatabaseConnection`. The connection variable's scope determines where downstream activities can use it.
- **Start Transaction** (`DatabaseTransaction`) — open a connection inside a transactional scope; child activities run under one transaction, committed at scope end (or rolled back on fault). Properties: `ConnectionString`, `ProviderName`, `UseTransaction`, output `DatabaseConnection`.
- **Disconnect** (`DatabaseDisconnect`) — close a `DatabaseConnection`.
- **Execute Query** (`ExecuteQuery`) — run a `SELECT` and return a `DataTable`. Properties: `ExistingDbConnection` (or inline `ConnectionString`/`ProviderName`), `Sql`, `CommandType`, `Parameters`, `TimeoutMS` (milliseconds; default `30000`), output `DataTable`. See the [Execute Query failures playbook](./playbooks/execute-query-failures.md).
- **Execute Non Query** (`ExecuteNonQuery`) — run `INSERT`/`UPDATE`/`DELETE`/DDL and return the affected-row count. Properties as above, output `AffectedRecords` (`Int32`).
- **Run Command** (`ExecuteCommand`) — run a statement or stored procedure where the result shape is configured via `CommandType` (`Text` vs `StoredProcedure`). Properties: `ExistingDbConnection`/inline connection, `Sql` (command/proc name), `CommandType`, `Parameters`, `TimeoutMS`.
- **Insert / Bulk Update Database** (`BulkUpdate`) — write a `DataTable` to a target table. Properties: `ExistingDbConnection`/inline connection, `TableName`, the source `DataTable`, `TimeoutMS`.

## Common Failure Patterns

`Execute Query` is the most failure-prone surface; its seven branches are catalogued in the [Execute Query failures playbook](./playbooks/execute-query-failures.md). The same connection- and provider-level patterns apply to `Execute Non Query`, `Run Command`, and the bulk activities:

- **Null / expired / out-of-scope connection** — the `DatabaseConnection` handed to a data activity is `Nothing`: the `Connect to Database` / `Start Transaction` did not run first, its output variable was never wired into `ExistingDbConnection`, the connection variable is scoped to an inner `Sequence`, or the connection was already disposed. Surfaces as `Object reference not set to an instance of an object`.
- **Driver / provider mismatch after migration** — after upgrading a project from **Windows - Legacy** (.NET Framework) to **Windows** (.NET 6+), the configured `ProviderName` or connection-string keywords are rejected by the modern provider (`Keyword not supported`), or the required driver is not installed on the Robot host. SQL Server commonly needs `System.Data.SqlClient` → `Microsoft.Data.SqlClient`; MySQL/other engines need their managed or ODBC driver installed.
- **SQL syntax / unsafe concatenation** — malformed `Sql`, or SQL built by string concatenation (`"... WHERE id = " + var`), which breaks parsing and is a SQL-injection risk. Surfaces as `Execute Query: A database error occurred` wrapping the provider's syntax error. Fix: parameterize with named `@parameters` via the `Parameters` collection.
- **Query text in the connection-string field** — the SQL statement was pasted into `ConnectionString` instead of `Sql`, or quotes in the connection string are unbalanced; the parser then chokes, often surfacing as a misleading "database does not exist".
- **Command timeout exceeded** — the statement ran longer than `TimeoutMS` (milliseconds; default `30000` = 30 s). Surfaces as `Timeout expired`. Distinguish a legitimately long query (raise `TimeoutMS`) from a runaway/un-indexed query (fix the index/query).
- **CLR-level crash (`0xE0434352`)** — a managed-runtime fault bypassing the activity exception path: an oversized result set exhausting Robot memory, an incompatible native provider path (notably Oracle `REF CURSOR`), or a stale `UiPath.Database.Activities` build. `0xE0434352` is the generic .NET unhandled-exception code — the DB context narrows it.
- **Wrong activity for the statement type** — `Execute Query` for a `SELECT` (→ `DataTable`); `Execute Non Query` for modifications (→ `AffectedRecords`). Crossing them returns empty/meaningless output or fails the output type binding.

## Package

NuGet: `UiPath.Database.Activities`

Activities target ADO.NET; the active provider is chosen per activity/connection via `ProviderName`. Project compatibility (**Windows** vs **Windows - Legacy**) changes the default provider and is a frequent migration-time failure cause. Version-specific bugs are documented in the relevant playbooks.
