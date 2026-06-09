---
confidence: medium
---

# Start Transaction Failures

## Context

A `UiPath.Database.Activities` `Start Transaction` (`DatabaseTransaction`) activity is a **scope**: it opens a connection from a `ConnectionString` + `ProviderName`, begins a database transaction, runs the child activities in its body under that single transaction, and on normal scope exit **commits** — or, when an exception propagates out of the scope, **rolls back**. It outputs a `DatabaseConnection` that every child data activity (`Execute Query`, `Execute Non Query`, `Run Command`, bulk activities) must consume via its `ExistingDbConnection` input so the work is enrolled in the transaction.

Start Transaction shares the connection/provider surface with `Connect to Database` (see [connect-to-database-failures.md](./connect-to-database-failures.md)) and the statement surface with the data activities (see [execute-query-failures.md](./execute-query-failures.md) / [execute-non-query-failures.md](./execute-non-query-failures.md)). What is **specific** to Start Transaction is the commit/rollback lifecycle and the requirement to thread its output connection into every child — that is where its distinct failure modes live. SQL-syntax, parameter, and command-timeout faults raised by a child statement are not transaction bugs; route those to the data-activity playbooks.

What this looks like — Start Transaction faults surface as one of these signatures:

- Job reports **Success**, but the database is unchanged (or partially changed) and a child activity's error never surfaced — the transaction did not roll back or re-raise. The most visible symptom is downstream logic proceeding on data that was never committed — branch 1.
- Job reports **Success**, but **none** of the child activities ran — the transaction body was skipped with no error and no logs from inside the scope — branch 2.
- `The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception` (or another provider type-initializer crash), or a design-time validation/compile error that the `DatabaseConnection` type is **missing / unresolvable**, appearing right after a **Windows - Legacy → Windows** migration — branch 3.
- A child `Execute Query` / `Execute Non Query` faults with `Object reference not set to an instance of an object` (null connection) or an instant `Timeout expired`, or the writes succeed but are **not transactional** (committed independently, so a later failure cannot roll them back) — branch 4.

What can cause it (cause-branches — pick the right one from evidence):

1. **Silent success — a failing child does not roll back or re-raise.** On some package versions / configurations, when a child activity inside the scope hits a database error, the `Start Transaction` scope still completes as **Success** instead of rolling back and surfacing the fault. The child exception is absorbed by the scope, so the workflow neither rolls back the partial work nor registers a failure — downstream activities then operate on data that was never committed. This is the most dangerous branch because the job looks green.
2. **Transaction scope skips its body (package-version bug).** A specific legacy build — notably `UiPath.Database.Activities` **v1.5.0** — fails to execute the activities inside the `Start Transaction` body at all. The scope enters and exits cleanly with **no error**, but every child database activity is skipped, so nothing is read or written. It is a package defect, not a workflow-configuration problem.
3. **Post-migration provider / type breakage (Windows - Legacy → Windows).** After converting the project to the modern .NET runtime, the transaction's connection step crashes — a project still on `System.Data.SqlClient` throws a `Microsoft.Data.SqlClient` type-initializer / execution error — and/or the `DatabaseConnection` variable type appears **missing or unresolvable** at design time (broken type reference after the upgrade). Same provider surface as the connect/query playbooks, reached through the transaction scope.
4. **Output connection not propagated to child activities.** The scope produces a `DatabaseConnection`, but a child `Execute Query` / `Execute Non Query` does not consume it: it is left with an empty/`Nothing` connection (→ null-reference, or instant `Timeout expired` while it waits on an unopened/throwaway connection), or it carries its **own** inline `ConnectionString` + `ProviderName` and opens a separate connection — running **outside** the transaction so its writes auto-commit and cannot be rolled back with the rest. Either way the transaction's guarantee is lost.

What to look for:

- **Job final state vs. database state** — a `Success` job with no committed data (branch 1) or with no child-activity log lines at all (branch 2). Branch 1 has child error evidence that was swallowed; branch 2 has an empty, errorless scope.
- **`UiPath.Database.Activities` package version** — from `project.json`. `v1.5.0` is the known body-skip build (branch 2); branches 1 and 3 are also version- and runtime-sensitive.
- **Project compatibility** — `Windows` vs `Windows - Legacy`, and whether the failure began right after a migration. Load-bearing for branch 3.
- **Child connection wiring** — for every data activity inside the scope, whether `ExistingDbConnection` is bound to the **scope's** output `DatabaseConnection`, or whether the child carries its own inline connection. Load-bearing for branch 4.
- **Whether child errors are handled** — the presence (or absence) of a `Try Catch` / `Throw` around the in-scope statements, which determines whether a child fault rolls the transaction back (branch 1).

## Investigation

Go in this order — cheaper checks first.

1. **Establish job state vs. expected database effect.** From `uip or jobs get <job-key> --output json` → `State` and `Info`, and `uip or jobs logs <key> --output json`: did the job report `Success` or `Faulted`? Did the expected rows actually commit? List the activity log lines emitted from inside the scope. A green job with no committed data — or with no in-scope activity logs — is the primary signal that separates the transaction-specific branches (1, 2) from a normal child-statement fault.
2. **Read the package version and project compatibility.** From `project.json`: the pinned `UiPath.Database.Activities` version and `targetFramework` (`Windows` vs `Windows-Legacy`). `v1.5.0` → suspect branch 2; a recent migration to `Windows` → suspect branch 3.
3. **Branch the diagnostic on the signature.**
   - `Success` with a swallowed child error and no rollback → branch 1; go to step 4.
   - `Success` with an empty scope (no child ran) on `v1.5.0` → branch 2; go to step 5.
   - SqlClient type-initializer crash, or `DatabaseConnection` type unresolvable, post-migration → branch 3; go to step 6.
   - Child null-connection / instant timeout, or non-transactional writes → branch 4; go to step 7.
4. **Confirm branch 1 (silent success / no rollback).** In the workflow source, check whether the in-scope statements are wrapped so a child fault propagates out of the scope. If a child clearly errored (inner provider exception in the logs) yet the job is `Success` and the data is unchanged/partial, the scope absorbed the fault instead of rolling back and re-raising — branch 1 confirmed.
5. **Confirm branch 2 (scope skips body).** Confirm the package is `v1.5.0` (or another build with the documented body-skip defect) and that the scope produced **no** in-scope activity logs and **no** error. A clean, instantaneous, empty transaction on that version confirms the package bug rather than a config error.
6. **Confirm branch 3 (post-migration provider / type).** Confirm the project is now `Windows` and the failure began at migration. A `Microsoft.Data.SqlClient` type-initializer / SqlClient error on connect, or a design-time error that `DatabaseConnection` (or the activity) is unresolvable, confirms the branch. Cross-check [connect-to-database-failures.md](./connect-to-database-failures.md) branch 4 and [execute-query-failures.md](./execute-query-failures.md) branch 2 — the provider surface is shared.
7. **Confirm branch 4 (connection not propagated).** For each child data activity in the scope, read whether `ExistingDbConnection` is the scope's output variable. An empty connection input (→ `Object reference not set` / instant `Timeout expired`) or a child carrying its own inline `ConnectionString`/`ProviderName` (→ writes that committed outside the transaction) confirms the branch.

The root cause must name **which of the four surfaces** the failure maps to, with the specific evidence: the job state vs. committed data, the package version, the project compatibility, and the child connection wiring. A generic "the transaction failed" is not a confirmed finding — and a child SQL-syntax or command-timeout error is a data-activity fault, not a transaction fault.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Silent success / no rollback:**
  - Wrap the in-scope database statements in a `Try Catch`. In the catch, **re-raise** with a `Throw` (or throw a domain exception) so the fault propagates out of the `Start Transaction` scope and triggers the rollback — do not log-and-continue.
  - If a multi-step unit must be all-or-nothing, ensure any child failure leaves the scope via an exception so the transaction rolls back as a whole; only commit (let the scope exit normally) when every step succeeded.
  - For broad coverage across processes, add a **Global Exception Handler** so hidden database exceptions are caught and routed rather than absorbed.

- **Branch 2 — Scope skips its body (package bug):**
  - Open **Manage Packages** in Studio and move `UiPath.Database.Activities` off the defective build: upgrade to the latest stable (**v1.7.1** or newer), or downgrade to a known-good older release (**v1.4.0**). This is a package-version fix, not a workflow change.

- **Branch 3 — Post-migration provider / type breakage:**
  - For SQL Server on a **Windows** (.NET) project, change the provider from `System.Data.SqlClient` to `Microsoft.Data.SqlClient` on the transaction's connection configuration, and adjust any rejected connection-string keyword (same fix as [execute-query-failures.md](./execute-query-failures.md) branch 2).
  - For MySQL, switch the configuration to `System.Data.Odbc` with the MySQL ODBC driver installed on every Robot host.
  - If the `DatabaseConnection` type (or the activity) shows as missing/unresolvable after the upgrade, close Studio and clear the local cache at `%LOCALAPPDATA%\UiPath\Studio\Cache`, then reopen so the package types re-resolve.

- **Branch 4 — Output connection not propagated:**
  - Pass the `Start Transaction` output `DatabaseConnection` into the **`ExistingDbConnection`** (Existing Connection) property of **every** child data activity. Do not give the child its own inline `ConnectionString` + `ProviderName` — that opens a separate connection that runs outside the transaction.
  - Verify the connection variable is declared at the scope of the `Start Transaction` body so every child can see it (a connection scoped to an inner `Sequence` is `Nothing` for siblings — see [execute-query-failures.md](./execute-query-failures.md) branch 1).

## Anti-patterns (what NOT to do)

- **"Wrap each in-scope query in a Try Catch that logs and continues."** A bare catch that swallows the child exception is exactly what produces branch 1: the scope completes `Success`, nothing rolls back, and downstream logic runs on uncommitted/partial data. Catch only to **re-raise** (or to run a real recovery path), so the transaction still rolls back on failure.
- **"Give each in-scope activity its own connection string so they're independent."** Per-child inline connections run **outside** the transaction (branch 4) — their writes auto-commit and cannot be rolled back with the batch, defeating the entire point of `Start Transaction`. Thread the scope's `DatabaseConnection` into every child instead.
- **"Add a Delay or a Retry Scope around the whole transaction to make it stick."** Neither addresses a body-skip package bug (branch 2 — fix the version) or a swallowed-rollback (branch 1 — fix the exception flow); they only hide the symptom and hold locks longer.
- **"Downgrade/upgrade the package on a hunch."** A version change is the fix only for the documented body-skip defect (branch 2). For branches 1, 3, and 4 it changes nothing — confirm the branch from evidence first.

## Prevention (cross-branch)

- Let child faults **propagate** out of the `Start Transaction` scope (re-throw in any in-scope catch) so commit happens only on full success and any failure rolls the whole unit back.
- Thread the scope's output `DatabaseConnection` into the `ExistingDbConnection` of every child activity at design time; never let an in-scope activity open its own connection.
- Pin and track the `UiPath.Database.Activities` version across environments and avoid known-defective builds (e.g. v1.5.0); validate the transaction body actually executes after any version change.
- After migrating a project from **Windows - Legacy** to **Windows**, set the provider explicitly (`Microsoft.Data.SqlClient` / `System.Data.Odbc`), re-validate every Database activity, and clear the Studio cache if package types fail to resolve.
- Keep transactions short and commit promptly to limit lock duration; command-timeout and runaway-query tuning inside the transaction follow [execute-query-failures.md](./execute-query-failures.md) branch 5.

## Related

- [connect-to-database-failures.md](./connect-to-database-failures.md) — the non-transactional connection-open surface (connection string, provider registration/bitness, file lock, provider init after migration); branch 3 here shares its provider-init fix.
- [execute-query-failures.md](./execute-query-failures.md) — child-statement faults inside the scope (null/out-of-scope connection, provider mismatch, SQL syntax, command timeout); a child SQL/timeout error is a query fault, not a transaction fault.
- [execute-non-query-failures.md](./execute-non-query-failures.md) — modification-statement faults (output-parameter sizing, parameter mapping, empty `Sql`, driver load) raised by an in-scope `Execute Non Query`.
- [`../overview.md`](../overview.md) — the package connection model (Connect / Start Transaction → `DatabaseConnection` → data activities → commit/rollback or Disconnect).
