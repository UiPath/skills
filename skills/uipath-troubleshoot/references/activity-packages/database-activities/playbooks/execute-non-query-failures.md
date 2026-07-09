---
confidence: medium
---

# Execute Non Query Failures

## Context

A `UiPath.Database.Activities` `Execute Non Query` (`ExecuteNonQuery`) activity runs a data-modifying statement — `INSERT` / `UPDATE` / `DELETE` / DDL (`CREATE`/`ALTER`) — or a stored procedure, and returns the affected-row count in its `AffectedRecords` output (`Int32`). Like `Execute Query` it takes a connection via `ExistingDbConnection` (from `Connect to Database` / `Start Transaction`) or an inline `ConnectionString` + `ProviderName`, plus `Sql`, `CommandType` (`Text` / `StoredProcedure`), `Parameters`, and `TimeoutMS`. Failures cluster around four surfaces: stored-procedure output-parameter sizing, statement/parameter construction, an empty command, and missing/mismatched database drivers.

Rule out the wrong-activity case first: **`Execute Non Query` is for modifications; `Execute Query` is for `SELECT`** (→ `DataTable`). Using `Execute Non Query` to pull data, or `Execute Query` to modify, is a category error — see [execute-query-failures.md](./execute-query-failures.md) branch 7.

What this looks like — Execute Non Query faults surface as one of these signatures:

- `The Size property has an invalid size of 0` (from the ODBC/ADO.NET layer) — branch 1.
- `Execute Non Query: A database error occurred` wrapping a provider syntax error (`Incorrect syntax near ...`, `ORA-…`), or a type/cast error mapping a value into a column — branch 2.
- `CommandText property has not been initialized` (ADO.NET) — branch 3.
- `Failed to load library (ErrorCode: 126)` / `System.DllNotFoundException` / a provider that "is not registered" or fails to load — branch 4.

What can cause it (cause-branches — pick the right one from evidence):

1. **Stored-procedure output parameter with `Size = 0` (ODBC)** — a stored procedure invoked with `CommandType: StoredProcedure` that has an `Output` / `InputOutput` parameter, run through an ODBC driver (e.g. SQL Server over ODBC). The driver cannot infer the memory footprint of the returned value when the parameter's `Size` is left at `0`, so it throws `The Size property has an invalid size of 0`.
2. **Unsafe SQL construction / parameter mapping / wrong type** — the `Sql` is built by concatenating values (`"INSERT INTO Users VALUES ('" + strName + "')"`), which breaks on quotes/symbols and is a SQL-injection vector; or a parameter's `Type`/`Direction` is wrong; or the workflow tries to push a whole `DataTable` into a single column. The provider rejects the statement with a syntax or type/cast error wrapped as `A database error occurred`.
3. **Empty `Sql` (`CommandText property has not been initialized`)** — the `Sql` property is blank, an expression that resolved to `""`, or a variable that was never set / went out of scope. ADO.NET refuses to execute a command with no `CommandText`.
4. **Driver / client library not loadable (`ErrorCode: 126`)** — the Robot host lacks the database driver or client the connection string needs (Oracle Client, an OLE DB provider, a specific ODBC system driver), or the installed driver's bitness does not match the process. The native load fails with `Failed to load library (ErrorCode: 126)` / `DllNotFoundException`.

What to look for:

- **The exception text** — first signal, maps directly to a branch per the list above. Read the **inner** provider/driver exception, not just the UiPath `A database error occurred` wrapper.
- **`CommandType` and the `Parameters` collection** — whether the statement is a `StoredProcedure` with `Output`/`InputOutput` parameters, and each parameter's `Name`, `Direction`, `Type`, `Value`, and **`Size`**. Branch 1 is specifically an output parameter with `Size = 0` over ODBC.
- **How `Sql` is constructed** — literal vs concatenation vs an expression that can resolve empty (branches 2 and 3).
- **`ProviderName` + driver inventory on the Robot host** — the provider invariant name and whether the matching driver/client is installed at the right bitness (branch 4).
- **Connection provenance** — inline vs `ExistingDbConnection`, and whether that connection is live (a closed/expired/null connection routes to [execute-query-failures.md](./execute-query-failures.md) branch 1).
- **`UiPath.Database.Activities` version** — branch 1's ODBC sizing bug was patched in older releases (historically 1.4.0+); branch 4 driver behaviour is also version/host-sensitive.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and full message, including the inner exception. From workflow source (`.xaml`): the `Execute Non Query` node — connection source, `Sql`, `CommandType`, the `Parameters` collection (per-parameter `Direction`/`Type`/`Size`), and `ProviderName`. From job logs (`uip or jobs logs <key> --output json`): the resolved values at the failing step.

2. **Branch the diagnostic on the signature.**
   - `The Size property has an invalid size of 0` → branch 1; go to step 3.
   - `A database error occurred` wrapping a syntax / type-cast error → branch 2; go to step 4.
   - `CommandText property has not been initialized` → branch 3; go to step 5.
   - `Failed to load library (ErrorCode: 126)` / `DllNotFoundException` / provider load failure → branch 4; go to step 6.

3. **Confirm branch 1 (output-parameter size).** Confirm `CommandType: StoredProcedure`, an `Output`/`InputOutput` parameter, and an ODBC `ProviderName`. Check that parameter's `Size` — `0` (unset) confirms the branch. Note the `UiPath.Database.Activities` version.

4. **Confirm branch 2 (SQL construction / parameters).** Read the inner provider message (it names the offending token or type). In source, check whether `Sql` is concatenated, whether any parameter's `Type`/`Direction` mismatches the column, and whether a `DataTable` is being mapped into a scalar column.

5. **Confirm branch 3 (empty Sql).** Inspect the `Sql` property. If literal, confirm it is non-empty. If an expression, log the resolved value immediately before the activity (`Log Message Level=Info Message=$"SQL: '{sqlText}'"`) and rerun — an empty/`Nothing` result confirms the branch.

6. **Confirm branch 4 (driver load).** Read `ProviderName` and the connection string's driver/client requirement. Check the Robot host for the matching driver/client and its bitness (a **Windows** project is a 64-bit process and needs the 64-bit driver). `ErrorCode: 126` ("module not found") with the required client absent or wrong-bitness confirms the branch. This is the same driver/bitness family as [connect-to-database-failures.md](./connect-to-database-failures.md) branch 2.

The root cause must name **which of the four surfaces** the failure maps to, with the specific evidence: the inner exception, the `CommandType`/`Parameters`/`Sql`/`ProviderName` values, and (branches 1/4) the package version and host driver inventory. A generic "Execute Non Query failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Output parameter `Size = 0` (ODBC stored proc):**
  - In the `Parameters` collection, set the output parameter's `Size` to the column's maximum (e.g. `50` for `VARCHAR(50)`, `4` for an `INT`). The driver needs an explicit buffer size for the returned value.
  - Alternatively / additionally, update `UiPath.Database.Activities` to a version where the ODBC sizing bug was patched (historically `1.4.0`+); current packages include the fix.

- **Branch 2 — SQL construction / parameter mapping:**
  - Do **not** concatenate values into the `Sql`. Use named parameters: `INSERT INTO Users (Name, Age) VALUES (@ParamName, @ParamAge)`, and map each in the `Parameters` collection (`Name: @ParamName`, `Direction: In`, `Type: String`, `Value: strName`). The provider handles quoting/typing and the injection risk goes away.
  - Match each parameter's `Type`/`Direction` to its column. Do not map a `DataTable` into a scalar column.
  - To write an entire `DataTable` to a table in one shot, use **Bulk Insert** or **Bulk Update Database** (both in `UiPath.Database.Activities`), not a per-row `Execute Non Query`.

- **Branch 3 — Empty `Sql`:**
  - Ensure the `Sql` property contains a valid non-empty statement. For expression-built SQL, guard against empty (`If` skip when blank) and log the resolved value before the activity. Fix the upstream assignment / scope so the variable is populated when the activity runs.

- **Branch 4 — Driver / client library not loadable:**
  - Install the database driver/client the connection string requires (Oracle Client, the OLE DB provider, the ODBC system driver) on every Robot host, at the **bitness matching the process** (64-bit for a **Windows** project — not Office's or the dev machine's bitness).
  - Verify connectivity with **Configure Connection** on the activity from the host. For the OLE-DB-provider-not-registered variant, see [connect-to-database-failures.md](./connect-to-database-failures.md) branch 2.

## Anti-patterns (what NOT to do)

- **"Concatenate the values into the INSERT/UPDATE string."** (`"INSERT INTO Users VALUES ('" + strName + "')"`) — breaks on quotes/symbols, throws branch-2 syntax errors, and is a SQL-injection hole. Always use named parameters via the `Parameters` collection.
- **"Loop Execute Non Query once per DataTable row."** For bulk writes this is slow and error-prone; use **Bulk Insert** / **Bulk Update Database**. A per-row loop also tends to surface branch-2 type mismatches one row at a time.
- **"Wrap Execute Non Query in a Try Catch and continue on error."** A bare catch that swallows the exception leaves the database half-modified and the workflow proceeding as if the write succeeded — worse than failing loudly. Use Try-Catch only with a real recovery path (roll back the transaction, mark the queue item Failed, re-throw a domain exception), and prefer `Start Transaction` so a mid-batch failure rolls back cleanly.
- **"Use Execute Non Query to read data."** It returns an affected-row count, not rows. For `SELECT`, use `Execute Query` (→ `DataTable`).

## Prevention (cross-branch)

- Parameterize every statement with named parameters; never concatenate. This prevents branch 2 and closes the injection risk.
- For stored procedures with output parameters over ODBC, always set each output parameter's `Size` explicitly (branch 1).
- Choose the activity by intent: `Execute Non Query` for modifications, `Execute Query` for `SELECT`, **Bulk Insert/Update** for whole-`DataTable` writes.
- Provision Robot hosts with the required DB driver/client at the correct bitness, and verify with Configure Connection during host setup (branch 4).
- Wrap multi-statement modifications in `Start Transaction` so a failure rolls back rather than leaving partial writes.

## Related

- [execute-query-failures.md](./execute-query-failures.md) — the read-side activity; shares the connection (null/expired), SQL-syntax, and timeout surfaces, and owns the wrong-activity branch (Execute Query vs Execute Non Query).
- [connect-to-database-failures.md](./connect-to-database-failures.md) — branch 4 here (driver/bitness) is the same family as that playbook's provider-not-registered branch.
- [`../overview.md`](../overview.md) — package connection model and the Bulk Insert / Bulk Update Database activities.
