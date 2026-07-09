---
confidence: medium
---

# Execute Query Failures

## Context

A `UiPath.Database.Activities` `Execute Query` activity runs a SQL `SELECT` against a database and returns the result set as a `DataTable`. It needs a live connection, supplied one of two ways: an `ExistingDbConnection` produced by a preceding `Connect to Database` activity (or a `Start Transaction` block), or an inline `ConnectionString` + `ProviderName` set on the activity itself. Failures originate at one of seven surfaces: connection handle (null / expired / out of scope), driver provider (post-migration keyword/driver mismatch), SQL text (syntax error or unsafe concatenation), property misplacement (query pasted into the connection-string field), command timeout, CLR-level crash (oversized result set or incompatible native provider), or wrong activity for the statement type.

What this looks like — Execute Query faults surface as one of these signatures:

- `Object reference not set to an instance of an object` (`System.NullReferenceException`) raised at the activity — branch 1.
- `Keyword not supported: '<keyword>'` / `System.ArgumentException` from the connection-string parser, or a SqlClient native crash, typically right after a Windows-Legacy → Windows project migration — branch 2.
- `Execute Query: A database error occurred` wrapping a provider exception with `Incorrect syntax near ...` (SQL Server), `ORA-00900: invalid SQL statement` (Oracle), or `You have an error in your SQL syntax` (MySQL) — branch 3.
- A provider error naming a database that does not exist, or a connection-string parse failure where the offending value is clearly SQL text (`SELECT ...`) — branch 4.
- `Execute Query: Timeout expired` / `... Timeout period elapsed prior to completion of the operation` — branch 5.
- The job terminates with exit code `0xE0434352` and no clean activity-level exception in the workflow log — branch 6.
- An `Execute Non Query` result assigned to a `DataTable` (design-time/cast error), or `Execute Query` used for an `INSERT`/`UPDATE`/`DELETE` (runs but returns an empty/unexpected `DataTable`) — branch 7.

What can cause it (cause-branches — pick the right one from evidence):

1. **Null / expired / out-of-scope connection** — the `DatabaseConnection` passed to `Execute Query` is `Nothing`. Causes: the `Connect to Database` / `Start Transaction` activity did not run before `Execute Query` (wrong ordering, or it sits on a branch that was skipped); the connect activity's output variable does not match the `ExistingDbConnection` input on the query (different variable, or never wired); the connection variable is scoped to an inner `Sequence` and is out of scope where `Execute Query` runs; or the connection was opened, used, and disposed (e.g., the `Connect` was inside a `Using`/scope that already closed) so the handle is expired.
2. **Driver provider mismatch after migration** — surfaces after upgrading the project from **Windows - Legacy** (.NET Framework) to **Windows** (.NET 6+). The legacy `System.Data.SqlClient` provider is not the modern default; connection-string keywords valid under one provider are rejected by the other (`Keyword not supported`). MySQL/other engines need an explicitly installed managed/ODBC driver that the legacy runtime bundled implicitly.
3. **SQL syntax error / unsafe concatenation** — the `Sql` text is malformed, or the workflow builds it by concatenating variables into the string (`"... WHERE id = " + myVar`). Concatenation breaks on quotes/types, fails to parse, and is a SQL-injection vector. The provider rejects the statement with its own syntax error, wrapped by UiPath as `A database error occurred`.
4. **Query text in the connection-string property** — the SQL statement was pasted into the `ConnectionString` property (or the `Connect` activity's connection field) instead of the `Sql` / query property; or the connection string has unbalanced quotes. The connection-string parser then chokes on the SQL text, often surfacing as a truncated/garbled "database does not exist" because it reads the first token as a database name.
5. **Command timeout exceeded** — the query ran longer than the activity's `TimeoutMS` (milliseconds; default `30000` = 30 s). Causes: an un-indexed scan, a lock/blocking on the DB side, or a genuinely large/expensive query. The provider aborts and UiPath surfaces `Timeout expired`.
6. **CLR-level crash (`0xE0434352`)** — a low-level managed-runtime fault that bypasses the normal activity exception path. For `Execute Query` the DB-specific triggers are: a result set large enough to exhaust the Robot process memory (materializing millions of rows into a `DataTable`), an incompatible native provider path (notably Oracle `REF CURSOR` handling), or a stale/incompatible `UiPath.Database.Activities` build. `0xE0434352` is the generic .NET unhandled-exception SEH code — it is not DB-specific on its own; the DB context narrows it.
7. **Wrong activity for the statement type** — `Execute Query` is for `SELECT` (returns a `DataTable`); `Execute Non Query` is for `INSERT`/`UPDATE`/`DELETE`/DDL (returns the affected-row count in its `AffectedRecords` output, an `Int32`). Using `Execute Query` for a modification returns an empty/meaningless `DataTable` and may error on statements that produce no result set; assigning an `Execute Non Query` `AffectedRecords` result to a `DataTable` fails to compile / casts wrong.

What to look for:

- **The exception class and message** — first signal, maps directly to a branch per the signature list above. A bare `A database error occurred` always wraps an inner provider exception — read the inner message (it carries the real syntax error or provider code).
- **How the connection is supplied** — from workflow source: whether `Execute Query` reads an `ExistingDbConnection` variable (and which `Connect`/`Start Transaction` activity produces it) or carries an inline `ConnectionString` + `ProviderName`. Trace the variable's producer and scope. This separates branch 1 (broken wiring/scope) from branches 2/4 (inline config problems).
- **Project compatibility** — whether the project is **Windows** or **Windows - Legacy**, and whether the failure started immediately after a migration. Load-bearing for branch 2.
- **The `Sql` value** — literal vs expression; whether it is built by concatenation (branch 3) and whether it actually landed in the `Sql` property rather than the connection field (branch 4).
- **`TimeoutMS` property** (milliseconds) and the DB-side duration of the query — branch 5.
- **Result-set size and provider** — expected row count, and whether the engine is Oracle with `REF CURSOR` output — branch 6.
- **`UiPath.Database.Activities` package version** — branches 2 and 6 are version-sensitive.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and full message, *including the inner exception* (the provider's real error). From workflow source (`.xaml`): the `Execute Query` node — whether it uses `ExistingDbConnection` or inline `ConnectionString`/`ProviderName`, the literal `Sql` text or bound expression, and `TimeoutMS`. From job logs (`uip or jobs logs <key> --output json`): Trace lines showing the resolved connection state and the activity that ran immediately before.

2. **Branch the diagnostic on the signature.**
   - `NullReferenceException` at the activity → branch 1; go to step 3.
   - `Keyword not supported` / connection-string `ArgumentException` / SqlClient crash, post-migration → branch 2; go to step 4.
   - `A database error occurred` wrapping a provider syntax error → branch 3; go to step 5.
   - Connection error naming a non-existent database / SQL-looking text in the connection string → branch 4; go to step 6.
   - `Timeout expired` → branch 5; go to step 7.
   - Job exit `0xE0434352`, no activity-level exception → branch 6; go to step 8.
   - Modification statement in `Execute Query`, or `Execute Non Query` result bound to a `DataTable` → branch 7; go to step 9.

3. **Confirm branch 1 (null/out-of-scope connection).** In the workflow source, trace the variable bound to the query's `ExistingDbConnection` back to its producer:
   - Confirm a `Connect to Database` or `Start Transaction` activity assigns that exact variable, and that it executes on the same path *before* `Execute Query` (not on a sibling `If`/`Catch` branch that was skipped).
   - Confirm variable **scope**: the connection variable must be declared at or above the scope containing `Execute Query`. A connection created inside a nested `Sequence` is `Nothing` once execution leaves it.
   - Confirm the connection was not already disposed — a `Connect` placed inside a scope/`Using` that closed before the query leaves an expired handle.

4. **Confirm branch 2 (provider mismatch).** Check the project compatibility (`project.json` → `targetFramework`/`Windows` vs `Windows-Legacy`) and whether the failure began right after a migration. Inspect the `ProviderName` and `ConnectionString` on the `Connect`/`Execute Query` activity. SQL Server still on `System.Data.SqlClient` after a move to **Windows** is the canonical case; for MySQL, confirm the configured provider and whether the matching ODBC/managed driver is installed on the Robot host.

5. **Confirm branch 3 (SQL syntax / concatenation).** Read the inner provider message — it names the syntax error and (often) the offending token. In the source, check whether `Sql` is a literal or built by string concatenation. If concatenation, log the fully resolved statement immediately before the activity (`Log Message Level=Info Message=$"SQL: {sqlText}"`) and rerun — the resolved text usually shows the broken quoting or a value injected mid-keyword.

6. **Confirm branch 4 (query in the wrong property).** Inspect the activity properties: the `ConnectionString` field should contain `Server=...;Database=...;...` (or a provider DSN), and the `Sql` field should contain the `SELECT`. If the `SELECT` text is in the connection field, or the connection string has unbalanced quotes, branch 4 is confirmed.

7. **Confirm branch 5 (timeout).** Read `TimeoutMS` (milliseconds; default `30000` = 30 s). Time the query independently against the DB (e.g., run it in the DB client) to learn its real duration, and check for blocking/locks at the failure time. Distinguish a query that is *legitimately* slow (needs a bigger timeout) from a *runaway* query (needs an index or a narrower result set) — see Resolution.

8. **Confirm branch 6 (CLR crash).** `0xE0434352` is a process-level exit, so correlate the job's last activity (job logs) with the `Execute Query`. Estimate the result-set size the query would materialize, check whether the engine is Oracle returning a `REF CURSOR`, and read the `UiPath.Database.Activities` version. A multi-million-row `SELECT *` into a `DataTable` on a memory-constrained Robot is the prototypical trigger.

9. **Confirm branch 7 (wrong activity).** Check the statement verb against the activity: `SELECT` → `Execute Query`; `INSERT`/`UPDATE`/`DELETE`/DDL → `Execute Non Query`. Check the output binding: an `Execute Query` output must be a `DataTable`; an `Execute Non Query` exposes an `AffectedRecords` output of type `Int32`.

The root cause must name **which of the seven surfaces** the failure maps to, with the specific evidence: the inner provider exception, how the connection is supplied and scoped, the `Sql`/`ConnectionString`/`ProviderName`/`TimeoutMS` values, and (for branches 2/6) the project compatibility and package version. A generic "Execute Query failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Null / out-of-scope connection:**
  - Ensure a `Connect to Database` (or `Start Transaction`) activity runs on the same path **before** `Execute Query`.
  - Wire the connect activity's output variable to the query's `ExistingDbConnection` input — same variable, exact match.
  - Declare the connection variable at a scope that encloses both activities. Do not create it inside a nested `Sequence` that `Execute Query` sits outside of.
  - If the connection lives in a scope/`Using` that closes before the query, restructure so the query runs inside that scope, or open a connection that outlives it.

- **Branch 2 — Driver provider mismatch after migration:**
  - For SQL Server on a **Windows** (.NET 6+) project, switch the provider from `System.Data.SqlClient` to `Microsoft.Data.SqlClient` in the activity's provider/connection configuration, and adjust any connection-string keyword the new provider rejects.
  - For MySQL, use the appropriate driver (e.g., `System.Data.Odbc` with the MySQL ODBC driver installed via the Windows ODBC Data Source Administrator on the Robot host, or the MySQL managed provider) and set the `ProviderName` accordingly.
  - Verify the chosen provider's driver is actually installed on every Robot host that runs the process — not just the developer machine.

- **Branch 3 — SQL syntax / unsafe concatenation:**
  - Do **not** build SQL by concatenating variables into the statement (`"... WHERE id = " + myVar`) — it breaks parsing and is a SQL-injection risk.
  - Use the activity's **Parameters** collection: reference a named parameter in the `Sql` (`SELECT * FROM t WHERE id = @id`) and map the UiPath variable to `@id` in the Parameters property. The provider handles quoting and typing.
  - Fix any genuine syntax error reported by the inner provider message (the engine names the offending token).

- **Branch 4 — Query in the wrong property:**
  - Put the connection string (`Server=...;Database=...;...` or DSN) in the `ConnectionString` property, and the `SELECT` in the `Sql` / query property. They are different fields — do not cross them.
  - Balance any quotes in the connection string; a stray quote truncates the parsed value and produces the misleading "database does not exist".

- **Branch 5 — Command timeout exceeded:**
  - If the query is *legitimately* long-running, raise `TimeoutMS` on the activity to a value above its worst observed duration. The property is in **milliseconds**: `60000` = 60 s (the default is `30000` = 30 s).
  - If the query is a *runaway* (full scan, missing index), fix the root cause on the DB side — add an index, narrow the `WHERE`, or reduce the columns/rows — rather than only enlarging the timeout. Increasing the timeout on a runaway query just delays the same failure and ties up the Robot longer.

- **Branch 6 — CLR crash (`0xE0434352`):**
  - Bound the result set in SQL so it cannot exhaust memory: `SELECT TOP n ...` (SQL Server), `... WHERE ROWNUM <= n` / `FETCH FIRST n ROWS ONLY` (Oracle), `... LIMIT n` (MySQL/Postgres). Page through large data instead of materializing it all into one `DataTable`.
  - For Oracle `REF CURSOR` output, verify the activity/version supports the cursor shape; update `UiPath.Database.Activities` to the latest stable version via **Manage Packages** if the crash is in the provider path.
  - If the crash persists after bounding the data and updating the package, capture the Robot process dump and escalate — a reproducible `0xE0434352` inside the provider is a package/driver bug, not a workflow misconfiguration.

- **Branch 7 — Wrong activity for the statement type:**
  - Use `Execute Query` only for `SELECT` (output → `DataTable`).
  - Use `Execute Non Query` for `INSERT`/`UPDATE`/`DELETE`/DDL (output → `AffectedRecords`, an `Int32` row count). Do not assign its result to a `DataTable`.
  - For a stored procedure that both modifies and returns rows, pick the activity that matches the result you consume, and confirm the output type binding compiles.

## Anti-patterns (what NOT to do)

Common advice for Execute Query failures contains workarounds that hide bugs rather than fix them. The agent should NOT recommend any of these as a primary resolution.

- **"Concatenate the variable straight into the SQL string."** (`"SELECT * FROM t WHERE id = " + myVar`) — breaks on quotes and non-string types, produces branch-3 syntax errors, and is a SQL-injection vulnerability. Always use named parameters (`@id`) mapped via the Parameters property.
- **"Wrap Execute Query in a Try Catch and continue on error."** A bare catch that logs and swallows the exception turns a failed query into a silent empty `DataTable`; downstream activities then process zero rows as if the query succeeded, producing wrong results that are harder to diagnose than the original fault. Use Try-Catch only with a real recovery path (retry the transient connection, mark the queue item Failed, re-throw a domain exception).
- **"Just set the timeout to a huge value."** Enlarging `TimeoutMS` is correct only for a query that is genuinely long-running. For a runaway/un-indexed query (branch 5) it masks the real problem, holds the Robot hostage for minutes, and the query still eventually fails or degrades the DB. Fix the query/index instead.
- **"Update the package and hope."** Updating `UiPath.Database.Activities` resolves specific provider-path bugs (branch 2, branch 6), but is not a remedy for connection-wiring (branch 1), SQL syntax (branch 3), or property-misplacement (branch 4) failures. Confirm the branch first.

## Prevention (cross-branch)

- Always supply `Execute Query` from a `Connect to Database` / `Start Transaction` whose connection variable is scoped to enclose the query; verify the wiring at design time.
- Parameterize every query with named parameters — never concatenate. This prevents branch 3 and closes the injection risk in one move.
- After migrating a project from **Windows - Legacy** to **Windows**, audit every Database activity's `ProviderName`/`ConnectionString` and confirm the matching driver is installed on all Robot hosts (branch 2).
- Bound result sets in SQL (`TOP`/`ROWNUM`/`FETCH FIRST`/`LIMIT`) for any query that could return large data, so a data-volume spike cannot crash the Robot (branch 6).
- Choose the activity by statement verb up front — `Execute Query` for `SELECT`, `Execute Non Query` for modifications — and bind the output to the matching type (branch 7).
- Pin and track the `UiPath.Database.Activities` version across environments so version-sensitive failures (branches 2, 6) reproduce consistently rather than differing dev-vs-prod.

## Related

- `Execute Non Query` failures share the connection (branch 1), provider (branch 2), and syntax (branch 3) surfaces — the diagnostic for those branches is identical; only the statement verb and output type differ (branch 7).
- For job exit code `0xE0434352` originating outside a Database activity, treat it as a generic CLR-crash investigation (memory, native dependency, or package incompatibility) rather than a SQL problem.
