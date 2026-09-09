# Final Resolution

---

**Root Cause:** The `Execute Query` activity in `Main.xaml` reads its
`ExistingDbConnection` from the variable `dbConnection`, but that
variable is declared inside a nested `Sequence` ("Open Connection")
where the `Connect to Database` activity runs. `Execute Query` sits
*outside* that inner sequence, so by the time it executes the
`dbConnection` variable is **out of scope** — it has been disposed and
is `Nothing`. Passing a null `DatabaseConnection` into `Execute Query`
raises `System.NullReferenceException` ("Object reference not set to an
instance of an object"). The failing layer is the **connection
handle**, not the SQL, the driver, or the database.

This maps to the **Execute Query failures** playbook, **Branch 1 —
null / out-of-scope connection**:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`.

**What went wrong:** The `CustomerQuery` job (started
2026-05-21T09:14:02Z) faulted ~0.6 seconds after launch with a
`System.NullReferenceException` thrown at the `Execute Query` activity.

**Why:** The workflow opens a connection correctly — `Connect to
Database` runs and assigns the open `DatabaseConnection` to the
`dbConnection` variable. But `dbConnection` is scoped to the inner
`Sequence` "Open Connection". When execution leaves that sequence the
connection variable goes out of scope (and the connection is disposed).
The `Execute Query` activity, which lives in the parent "Main Sequence"
after the inner sequence, still binds its `ExistingDbConnection` to
`dbConnection` — but at that point the variable resolves to `Nothing`.
The activity dereferences the null connection and throws
`NullReferenceException`.

This is **not** a SQL syntax error (branch 3), **not** a driver/
provider mismatch (branch 2 — the provider is already
`Microsoft.Data.SqlClient` on a Windows project), **not** a query in
the connection-string field (branch 4), **not** a timeout (branch 5),
**not** a CLR crash `0xE0434352` (branch 6), and **not** a wrong
activity for the statement type (branch 7 — `SELECT` correctly uses
`Execute Query`). The `Connect to Database` activity *did* run; the
problem is purely the **scope** of the connection variable.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CustomerQuery — Faulted at 2026-05-21T09:14:02.701Z (ran ~0.6 s)
- Folder: Finance (key `a1b2c3d4-2e8c-4f6b-9d5a-1c2b3d4e5f6a`)
- Executing robot identity: `RobotUser1`

### Database Activities (Surface)
- Exception (from `uip or jobs get <key>` → `Info`): `System.NullReferenceException: Object reference not set to an instance of an object.` thrown `at ExecuteQuery "Execute Query"`.
- Job logs Trace sequence (from `uip or jobs logs <key> --output json`):
  1. `Connect to Database` started, then ended — connection opened, assigned to `dbConnection` scoped to Sequence "Open Connection".
  2. Sequence "Open Connection" ended — scope closed, `dbConnection` disposed and out of scope.
  3. `Execute Query` started — `ExistingDbConnection` bound to `dbConnection`.
  4. `Execute Query` raised `NullReferenceException`.

### Workflow Source (Root Cause)
- `Main.xaml`: the `dbConnection` variable (type `UiPath.Database.DatabaseConnection`) is declared on the nested `Sequence DisplayName="Open Connection"`.
- `Connect to Database` (`uddb:DatabaseConnect`, provider `Microsoft.Data.SqlClient`) runs *inside* that nested sequence and outputs to `dbConnection`.
- `Execute Query` (`uddb:ExecuteQuery`, `Sql="SELECT CustomerId, Name FROM Customers"`) runs in the parent "Main Sequence" *after* the nested sequence and binds `ExistingDbConnection` to `dbConnection` — which is null at that point because the inner scope has closed.
- `project.json` declares `UiPath.Database.Activities` `[1.7.0]`, `targetFramework: "Windows"`.

---

**Immediate fix:**

The fix is in the **workflow** — correct the connection variable's
scope (or the activity placement) so the connection is live where
`Execute Query` runs.

### Database Activities (Root Cause)

1. **Declare the `dbConnection` variable at a scope that encloses both `Connect to Database` and `Execute Query`.**
   - **Why:** A connection created inside a nested `Sequence` is `Nothing` once execution leaves that sequence (Branch 1 of the Execute Query playbook). Moving the variable up to the "Main Sequence" keeps it in scope for the query.
   - **Where:** `Main.xaml` → move the `dbConnection` `Variable` declaration from the nested `Sequence "Open Connection"` up to the parent `Sequence "Main Sequence"` `Variables` collection.

2. **Alternatively, keep `Execute Query` inside the same scope as `Connect to Database`.**
   - **Why:** If the connection should not outlive the open scope, run the query inside that scope instead of after it.
   - **Where:** `Main.xaml` → move the `Execute Query` (and the downstream `Log Message`) inside the `Sequence "Open Connection"` so they execute while `dbConnection` is live.

3. **Confirm the wiring:** the `Connect to Database` output variable must be the exact same variable bound to the query's `ExistingDbConnection`.
   - **Where:** `Main.xaml` → `Connect to Database` `DatabaseConnection` output = `dbConnection`; `Execute Query` `ExistingDbConnection` = `dbConnection`. They already match — only the scope is wrong.
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 1 — null / out-of-scope connection).

---

**Preventive fix:**

1. **Studio** — Always declare the connection variable at a scope that encloses every Database activity that consumes it; verify the wiring at design time.
   - **Why:** Out-of-scope connections are the most common `Execute Query` failure and surface only at runtime as a generic `NullReferenceException`.
   - **Who:** RPA developer

2. **Studio** — Prefer the `Connect to Database` activity's own scope (or `Start Transaction`) to bracket all dependent queries, so the connection lifetime visibly matches its usage.
   - **Why:** Keeping the open/use/close lifecycle inside one container removes the scope-mismatch class of bug entirely.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Execute Query` receives a null/out-of-scope `DatabaseConnection` because `dbConnection` is declared inside a nested Sequence (Branch 1) | High | Confirmed | Yes | `NullReferenceException` at `ExecuteQuery` + Trace shows Connect ran, inner scope closed, then Execute Query bound the now-disposed `dbConnection`; `Main.xaml` shows the variable scoped to the inner sequence | Declare `dbConnection` at the enclosing scope (or move `Execute Query` inside the connect scope); confirm `ExistingDbConnection` wiring |
| H2 | SQL syntax error / unsafe concatenation (Branch 3) | Low | Rejected | No | Exception is `NullReferenceException`, not `A database error occurred`; `Sql` is a literal `SELECT` | — |
| H3 | Driver/provider mismatch after migration (Branch 2) | Low | Rejected | No | Provider is `Microsoft.Data.SqlClient` on a Windows project; no `Keyword not supported` error | — |

---

Would you like help applying the fix — moving the `dbConnection`
variable declaration up to the "Main Sequence" scope in `Main.xaml`, or
restructuring so `Execute Query` runs inside the connect scope? I can
also clean up the `.local/investigations/` folder if you no longer need
it.
