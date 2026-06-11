# Final Resolution

---

**Root Cause:** The `Start Transaction` (`DatabaseTransaction`) scope in
`Main.xaml` opened its connection successfully — it connected with
`ProviderName="Microsoft.Data.SqlClient"` and assigned the live
`DatabaseConnection` to the output variable `dbTxn`. But the child
`Execute Query` inside the scope body was **never wired to that
connection**: its `ExistingDbConnection` (Existing Connection) property is
left **empty** — it is not bound to `dbTxn` and the child carries no
inline connection of its own. At runtime that input is `null`, so the
child runs with a null connection and throws:

```
System.NullReferenceException: Object reference not set to an instance of an object.
   at UiPath.Database.DatabaseConnection.ExecuteQuery(...)
```

UiPath surfaces it as `Execute Query: Object reference not set to an
instance of an object.` The transaction's connection was opened fine; it
was simply **never propagated** to the child activity.

This maps to the **Start Transaction failures playbook, BRANCH 4 —
output connection not propagated to child activities**
(`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`).

**What went wrong:** The `OrderSettlementTxn` job (started
2026-05-30T08:35:00Z) faulted ~1.5 seconds after launch. The
`Start Transaction` scope entered and opened its connection without
error; the fault is raised at the child `Execute Query` inside the scope.

**Why:** Every child data activity inside a `Start Transaction` body must
consume the scope's output `DatabaseConnection` via its
`ExistingDbConnection` input so the work is enrolled in the transaction.
Here that binding is missing — the child's `ExistingDbConnection` is
empty — so the child has no connection object to execute against and
dereferences `null`. The scope's own connection (`dbTxn`) is healthy;
the gap is the unbound child.

This is **not** branch 1 (a swallowed rollback / silent `Success` — the
job clearly Faulted), **not** branch 2 (a package-version body-skip bug —
the body ran and the child raised an error), **not** branch 3 (a
post-migration provider / type-initializer crash — the connection opened
fine on `Microsoft.Data.SqlClient`), **not** a bad/rejected connection
string, **not** a SQL syntax error, **not** a provider mismatch, and
**not** a timeout. The connection string is valid and the connection
opened; the failure is purely the unpropagated connection on the child.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `OrderSettlementTxn` — Faulted at 2026-05-30T08:35:01.842Z (ran ~1.5 seconds)
- Folder: `Sales Operations` (key `f5c8e6ab-7b92-4eaf-90c1-5c6d7e8f9012`)
- `uip or jobs get <key> --output json` -> `Info`:
  `Execute Query: Object reference not set to an instance of an object.`
  wrapping `System.NullReferenceException`, with the stack located at
  `ExecuteQuery "Execute Query"` -> `DatabaseTransaction "Start Transaction"`
  -> `Sequence "Main Sequence"` -> `Main "Main"` (the child runs inside
  the scope, but with no connection).

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` (the smoking gun) shows the
  sequence clearly:
  - Trace: `Start Transaction: opened connection ... transaction begun, connection assigned to variable 'dbTxn'` — the scope's connection opened **successfully**.
  - Trace: `Execute Query: executing with ExistingDbConnection = (null) [property is empty - not bound to 'dbTxn']` — the child ran with a **null** connection.
  - Error: `NullReferenceException` at `UiPath.Database.DatabaseConnection.ExecuteQuery`.
- `process/Main.xaml`: the `Start Transaction` scope outputs
  `DatabaseConnection` to `dbTxn`, but the child `ui:ExecuteQuery` has
  **no `ExistingDbConnection` binding** (the property is absent / empty),
  so it is `null` at runtime. The `Sql` is well-formed
  (`SELECT OrderId, Status FROM Orders WHERE Status = 'Pending'`).
- `process/project.json`: `UiPath.Database.Activities` pinned at
  `[1.7.0]` (a healthy build — rules out the branch-2 body-skip defect).

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Bind the scope's output connection (`dbTxn`) into the child's `ExistingDbConnection`.**
   - **Why:** A `Start Transaction` scope opens one connection and exposes
     it as a `DatabaseConnection`; every child data activity must consume
     it via `ExistingDbConnection` to run inside the transaction. The
     child here has an empty `ExistingDbConnection`, so it executes
     against a `null` connection and throws `NullReferenceException`.
   - **Where:** In `Main.xaml`, on the `Execute Query` inside the
     `Start Transaction` body, set `ExistingDbConnection="[dbTxn]"`
     (Existing Connection = `dbTxn`). Do **not** leave it empty, and do
     **not** give the child its own inline `ConnectionString` +
     `ProviderName` — that would open a separate connection that runs
     outside the transaction and auto-commits.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/start-transaction-failures.md` (Branch 4 — output connection not propagated)

---

**Preventive fix:**

1. **Studio** — Thread the `Start Transaction` output `DatabaseConnection`
   into the `ExistingDbConnection` of **every** child data activity in the
   scope, and validate the connection variable is declared at the scope of
   the transaction body so all children can see it.
   - **Why:** An empty or out-of-scope child connection is the canonical
     branch-4 failure; it both breaks the child (null connection) and, if
     a child instead opens its own inline connection, silently runs work
     outside the transaction so it cannot be rolled back.
   - **Who:** RPA developer

2. **Studio / Review** — Add a pre-publish check that no data activity
   inside a `Start Transaction` body has an empty `ExistingDbConnection`
   or its own inline connection.
   - **Why:** Catches unpropagated connections before they reach
     Orchestrator.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Connection not propagated: the `Start Transaction` scope opened `dbTxn` fine, but the child `Execute Query`'s `ExistingDbConnection` is empty, so the child ran with a null connection and threw `NullReferenceException` | High | Confirmed | Yes | `Object reference not set...` / `NullReferenceException` at `ExecuteQuery` inside `DatabaseTransaction` in `jobs get` Info + job-logs Trace showing `dbTxn` opened then child `ExistingDbConnection = (null)` + `Main.xaml` child with no `ExistingDbConnection` binding | Bind `dbTxn` into the child's `ExistingDbConnection`; do not leave it empty or give the child its own inline connection |

---

Would you like help applying the fix — editing `Main.xaml` to bind
`dbTxn` into the child `Execute Query`'s `ExistingDbConnection` so it runs
inside the transaction? I can also clean up the `.local/investigations/`
folder if you no longer need it.
