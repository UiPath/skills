# Final Resolution

---

**Root Cause:** The `Execute Query` activity in `Main.xaml` runs an
**unbounded** statement:

```
SELECT * FROM Transactions
```

`Transactions` is a multi-million-row table and the query has no row
limit and no `WHERE`. The activity materializes the entire result set
into a single in-memory `DataTable`, which exhausts the Robot process
memory. The managed runtime crashes and the **job terminates at the
process level with exit code `0xE0434352`** — and crucially **no clean
activity-level exception** is recorded in the workflow log. The fault
bypasses the normal activity exception path entirely; this
process-level termination (rather than a tidy wrapped `ExecuteQuery`
exception) is the distinguishing evidence shape.

`0xE0434352` is the **generic .NET unhandled-exception SEH code** — it
is not DB-specific on its own. The database context (the huge unbounded
`SELECT *`) is what narrows it to an out-of-memory CLR crash inside the
Database activity.

This maps to the **Execute Query failures playbook, BRANCH 6 — CLR-level
crash (`0xE0434352`)**
(`references/activity-packages/database-activities/playbooks/execute-query-failures.md`).

**What went wrong:** The `TransactionExport` job (started
2026-05-22T02:05:11Z) ran for ~1.5 minutes reading rows into the
`DataTable`, then the Robot process died with `0xE0434352`. The
connection opened fine and the SQL is syntactically valid — the failure
is the **volume of data** the query pulls into memory.

**Why:** Materializing millions of rows into one `DataTable` on a
memory-constrained Robot exhausts the process heap. There is no
activity-level exception because the crash happens at the runtime/process
level, not as a managed exception the activity can catch. The fix is to
bound the result set in SQL so it can never exhaust memory, and to page
through large data rather than loading it all at once.

This is **not** a null / out-of-scope connection, **not** a SQL syntax
error / unsafe concatenation, **not** a provider/driver mismatch,
**not** a command timeout, **not** a wrong-activity-type issue, and
**not** a database outage. The connection succeeded and the statement
parsed; the result set is simply too large to hold in memory.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `TransactionExport` — Faulted at 2026-05-22T02:06:48.913Z (ran ~97 seconds)
- Folder: `Finance Automation` (key `5c7e9a2d-4b8f-4e1c-9a3d-6f2b8c4e1a7d`)
- `uip or jobs get <key> --output json` → `Info`:
  `The job terminated unexpectedly. The robot execution process exited with code 0xE0434352. No activity-level exception was recorded in the workflow log before the process ended.`
  Last logged activity: `Execute Query "Execute Query"` in `Main.xaml`.
  Note the absence of a clean wrapped `DatabaseException` / activity exception — the distinguishing Branch 6 signature.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` shows the connection opened
  successfully, the `Execute Query` started against
  `SELECT * FROM Transactions`, a Trace line noting it was
  `still reading result set into DataTable (no row limit set)...`, and
  then a process-level error:
  `The robot execution process terminated unexpectedly with exit code 0xE0434352. No activity-level exception was caught; the process ended while Execute Query "Execute Query" was materializing its result set.`
- `Main.xaml` `Execute Query` activity `Sql` property is the literal
  `"SELECT * FROM Transactions"` — an unbounded `SELECT *` with no
  `TOP`/`FETCH FIRST`/`LIMIT` and no `WHERE`, over a multi-million-row
  table.
- The connection (`Connect to Database`, `Microsoft.Data.SqlClient`)
  opened successfully — the fault is the data volume, not the
  connection.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Bound the result set in SQL so it cannot exhaust memory.**
   - **Why:** An unbounded `SELECT *` over a multi-million-row table
     materializes the whole table into one `DataTable`, exhausting the
     Robot process memory and crashing the CLR (`0xE0434352`).
   - **Where:** In `Main.xaml`, change the `Execute Query` `Sql` to a
     bounded statement: `SELECT TOP n ...` (SQL Server),
     `... FETCH FIRST n ROWS ONLY` / `ROWNUM <= n` (Oracle), or
     `... LIMIT n` (MySQL/Postgres). Select only the columns needed and
     add a `WHERE` to narrow the rows. For genuinely large data, **page**
     through it (e.g., key-set / `OFFSET ... FETCH` paging) and process
     each page, rather than loading everything into one `DataTable`.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 6 — CLR crash `0xE0434352`)

2. **If a provider-path bug is implicated, update `UiPath.Database.Activities`.**
   - **Why:** Branch 6 also covers provider-path crashes (notably Oracle
     `REF CURSOR` handling) and stale/incompatible package builds.
     `0xE0434352` inside the provider path that persists after bounding
     the data points to a package/driver bug.
   - **Where:** **Manage Packages** → update `UiPath.Database.Activities`
     to the latest stable version. If the crash still reproduces after
     bounding the data and updating, capture the Robot process dump and
     escalate.
   - **Who:** RPA developer

---

**Preventive fix:**

1. **Studio** — Bound every database query with `TOP`/`FETCH FIRST`/`LIMIT`
   and select only required columns; page large extracts.
   - **Why:** A data-volume spike can never crash the Robot if result
     sets are bounded (branch 6).
   - **Who:** RPA developer

2. **Studio** — Add a workflow analyzer / code-review rule flagging
   `SELECT *` without a row limit feeding an `Execute Query`.
   - **Why:** Catches the unbounded-extract anti-pattern before it ships.
   - **Who:** RPA lead

3. **Environment** — Pin and track the `UiPath.Database.Activities`
   version across environments.
   - **Why:** Branch 6 is version-sensitive; pinning keeps
     provider-path crashes reproducible dev-vs-prod.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Execute Query runs an unbounded `SELECT * FROM Transactions` over a multi-million-row table; materializing the full result set into a `DataTable` exhausts Robot memory and crashes the CLR, surfacing as the process-level exit `0xE0434352` with no clean activity exception | High | Confirmed | Yes | `0xE0434352` process termination + "No activity-level exception" in `or jobs get` Info + job-logs Trace "still reading result set into DataTable (no row limit set)" then process death + the unbounded `SELECT *` in `Main.xaml` | Bound the result set (`TOP`/`FETCH FIRST`/`LIMIT`) and page; update `UiPath.Database.Activities` if a provider-path bug is implicated |

---

Would you like help applying the fix — editing `Main.xaml` to bound the
`Execute Query` result set (and add paging for large extracts)? I can
also clean up the `.local/investigations/` folder if you no longer need
it.
