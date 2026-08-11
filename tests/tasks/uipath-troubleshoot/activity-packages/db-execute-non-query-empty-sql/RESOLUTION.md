# Final Resolution

---

**Root Cause:** The `Execute Non Query` activity in `Main.xaml` runs with
an **empty `Sql`**. Its `Sql` property is bound to the expression
`[sqlText]`, and `sqlText` resolves to `""` at runtime because the
upstream Assign builds it from a `DataRow` field of a `DataTable`
(`dt_Config`) that has **zero rows** — the ternary falls through to its
`""` branch. ADO.NET refuses to execute a command whose `CommandText` is
blank, so it throws `CommandText property has not been initialized`,
wrapped by the activity as `A database error occurred`. The failing
layer is the **empty/unset `Sql` expression**, not the database, the
connection, the driver, or the SQL syntax.

This maps to
`references/activity-packages/database-activities/playbooks/execute-non-query-failures.md`
**Branch 3 — Empty `Sql` (`CommandText property has not been initialized`)**.

**What went wrong:** The `ConfigSyncProcess` job (started
2026-05-20T08:15:03Z) faulted ~1.5 seconds after launch when the
`Execute Non Query` activity tried to run with no command text.

**Why:** The workflow opens a connection (`Connect to Database`,
`Microsoft.Data.SqlClient`), then in the "Build SQL from config row"
Sequence assigns `sqlText` from
`dt_Config.Rows[0]["UpdateStatement"]` — but only when
`dt_Config.Rows.Count > 0`; otherwise it assigns `""`. At runtime
`dt_Config` is empty (the upstream population step never ran / returned
no rows), so `sqlText` stays empty. The job log makes this explicit: the
`Log Message` immediately before the activity printed `SQL: ''` and the
preceding line recorded `dt_Config row count: 0`. The `Execute Non
Query` then faulted with `CommandText property has not been
initialized`.

This is **not** a SQL-syntax error (there is no statement to be
malformed), **not** a stored-procedure output-parameter sizing problem
(Branch 1 — `CommandType` is `Text`, no parameters), **not** a
driver-load failure (Branch 4 — the connection opened fine), **not** a
null/closed connection (the connection is live), and **not** the
wrong-activity case.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ConfigSyncProcess — Faulted at 2026-05-20T08:15:04.602Z (ran ~1.5 s)
- Folder: Finance Automation (key `7c1e9a2b-3d4f-4a5b-8c6d-9e0f1a2b3c4d`) — folder exists
- Trigger: Schedule; executing robot `RobotUser1`

### Database Activities (Surface)
- Activity (from `Main.xaml`): `ExecuteNonQuery` (DisplayName: "Execute Non Query"), `CommandType: Text`, `Sql="[sqlText]"`, `Parameters` empty
- `Sql` is an **expression bound to the `sqlText` variable**, not a literal
- Upstream Assign: `sqlText = dt_Config.Rows.Count > 0 ? dt_Config.Rows[0]["UpdateStatement"].ToString() : ""`
- Error in `or jobs get` Info: `Execute Non Query: A database error occurred. CommandText property has not been initialized.` (inner `System.InvalidOperationException: CommandText property has not been initialized.`)

### Database Activities (Root Cause — the smoking gun)
- `or jobs logs` trace: `[Build SQL from config row] dt_Config row count: 0`
- `or jobs logs` trace: `About to run Execute Non Query. SQL: ''` — the resolved `Sql` is empty
- `project.json` declares `UiPath.Database.Activities` `[1.7.0]`
- The empty resolved `Sql` + the `CommandText` error + the expression-bound `Sql` in source together confirm Branch 3

---

**Immediate fix:**

The fix is on the **`Sql` expression and its upstream source** — not the
database, driver, or connection.

### Database Activities (Root Cause)

1. **Ensure `Sql` resolves to a valid, non-empty statement before the activity runs.**
   - **Why:** ADO.NET rejects a command with blank `CommandText`. The activity cannot run until `sqlText` holds a real `INSERT`/`UPDATE`/`DELETE`.
   - **Where:** `Main.xaml` → the "Build SQL from config row" Sequence. Fix the upstream assignment so `dt_Config` is actually populated (the step that fills it from the source must run and return rows), or supply the statement directly.

2. **Log the resolved `Sql` immediately before the activity and guard against empty.**
   - **Why:** Confirms the value at runtime and prevents a silent empty-command fault.
   - **Where:** Keep the `Log Message` (`SQL: '...'`); add an `If` that throws a meaningful Business Exception (or skips) when `String.IsNullOrWhiteSpace(sqlText)`, instead of handing an empty string to `Execute Non Query`.
   - **Source:** `database-activities/playbooks/execute-non-query-failures.md` (Branch 3 — Empty `Sql`).

3. **Fix the variable scope / population order that left `sqlText` blank.**
   - **Why:** The DataRow-derived value was empty because `dt_Config` had no rows when the Assign ran. Ensure the population activity precedes the Assign and that `dt_Config` (and any row variable) is scoped so the value survives to the `Execute Non Query`.
   - **Where:** `Main.xaml` → reorder/repair so the table is filled before the SQL is built; verify variable scope spans both sequences.

---

**Preventive fix:**

1. **Studio** — Guard every expression-built `Sql` with a non-empty check before `Execute Non Query` / `Execute Query`.
   - **Why:** Expression-bound command text can silently resolve to `""` when an upstream source returns nothing; an explicit guard turns a cryptic `CommandText` fault into a clear, early failure.
   - **Where:** Wrap the data activity in an `If String.IsNullOrWhiteSpace(sqlText)` → throw/skip pattern.

2. **Studio** — Prefer literal or parameterized statements over values stitched together from optional data sources.
   - **Why:** A static statement with named `@parameters` cannot resolve to an empty command; only the parameter values vary.
   - **Where:** Keep the `INSERT`/`UPDATE` text constant in `Sql`; pass row values via the `Parameters` collection.

3. **Orchestrator** — Alert on faulted jobs for scheduled processes.
   - **Why:** This process runs on a Schedule; a job-level alert surfaces the empty-SQL fault on the first run instead of on the next manual check.
   - **Where:** Orchestrator UI → Alerts → faulted-job subscription for `ConfigSyncProcess`.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Execute Non Query` ran with an empty `Sql` — the expression-bound `sqlText` resolved to `""` from an empty `dt_Config` row | High | Confirmed | Yes | `CommandText property has not been initialized` + log `SQL: ''` + `dt_Config row count: 0` + `Sql="[sqlText]"` in source | Ensure `Sql` resolves non-empty; log + guard; fix upstream population/scope |
| H2 | SQL syntax error in the statement | Low | Rejected | No | No statement text exists to be malformed; error is `CommandText ... not been initialized`, not a provider syntax error | — |
| H3 | Stored-procedure output parameter `Size = 0` (Branch 1) | Low | Rejected | No | `CommandType: Text`, no parameters, not a stored proc | — |
| H4 | Database driver not loadable (Branch 4) | Low | Rejected | No | `Connect to Database` opened successfully before the fault | — |
| H5 | Null / closed connection | Low | Rejected | No | Connection is live; error is about command text, not the connection | — |

---

Would you like help applying the fix — adding the empty-`Sql` guard and
repairing the upstream `dt_Config` population in `Main.xaml`? I can also
clean up the `.local/investigations/` folder if you no longer need it.
