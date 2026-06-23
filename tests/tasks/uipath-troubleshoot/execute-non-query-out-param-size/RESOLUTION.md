# Final Resolution

---

**Root Cause:** The `Execute Non Query` activity in `Main.xaml` invokes
the stored procedure `usp_FinalizeOrder` with
`CommandType=StoredProcedure` over an **ODBC** provider
(`ProviderName="System.Data.Odbc"`). Its `Parameters` collection
contains an **Output** parameter (`@ResultStatus`,
`Direction=Output`) whose `Size` is left at `0`. Over ODBC the driver
cannot infer the memory footprint of the value the stored procedure
returns when the output parameter's `Size` is unset, so it throws
`The Size property has an invalid size of 0`. The failing layer is the
output-parameter sizing, not the SQL, the connection, the driver, or
the choice of activity.

**What went wrong:** The `StoredProcWriteBack` job (started
2026-05-21T09:14:31Z) faulted ~1.6 seconds after launch when the
`Execute Non Query - usp_FinalizeOrder` activity tried to bind its
output parameter through the ODBC layer.

**Why:** A stored procedure invoked with `CommandType: StoredProcedure`
that has an `Output` (or `InputOutput`) parameter, run through an ODBC
driver, needs an explicit buffer size for the returned value. The
`@ResultStatus` output parameter declares `Size="0"`, which the ODBC
driver rejects with `System.ArgumentException: The Size property has an
invalid size of 0` before the command can execute. The input parameter
`@OrderId` (`Direction=Input`, `Size=4`) is sized correctly and is not
the problem.

This maps to **Branch 1** of the Execute Non Query failures playbook
(`execute-non-query-failures.md`) — "Stored-procedure output parameter
with `Size = 0` (ODBC)". The other branches are ruled out:

- **Branch 2 (SQL construction / parameter mapping / wrong type):** the
  `Sql` is the bare procedure name `usp_FinalizeOrder`, not a
  concatenated statement; no syntax/type-cast error is present.
- **Branch 3 (empty `Sql` / `CommandText property has not been
  initialized`):** `Sql` is populated, so this is not it.
- **Branch 4 (driver / client library not loadable / `ErrorCode:
  126`):** no `DllNotFoundException` / load failure — the ODBC layer is
  reached and rejects the *parameter size*, proving the driver loaded.
- **Null / closed connection** (`Object reference not set...`): not the
  signature here.
- **Wrong activity** (Execute Query vs Execute Non Query): the activity
  choice is correct for a data-modifying stored procedure.
- **Database outage:** the error is raised client-side by the ODBC
  parameter binding, before any round-trip to the server.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: StoredProcWriteBack — Faulted at 2026-05-21T09:14:32.870Z (ran for ~1.6 seconds)
- Folder: Finance Automations (key `7b2e9c4d-3a6f-4d1b-8e5c-2f9a1b3c4d5e`)
- Executing robot: `RobotUser1` (Unattended)
- `or jobs get` → `Info`: `Execute Non Query - usp_FinalizeOrder: A database error occurred. The Size property has an invalid size of 0.` with inner `System.ArgumentException: The Size property has an invalid size of 0.` at `System.Data.Odbc.OdbcParameter.GetParameterSize(...)`

### Job Logs (Surface)
- Trace at 2026-05-21T09:14:32.610Z: `Execute Non Query - usp_FinalizeOrder executing stored procedure 'usp_FinalizeOrder' (CommandType=StoredProcedure) over provider 'System.Data.Odbc'`
- Error at 2026-05-21T09:14:32.840Z: `[Execute Non Query - usp_FinalizeOrder] A database error occurred. The Size property has an invalid size of 0.`

### Workflow Source (Root Cause)
- Activity (from `Main.xaml`): `ExecuteNonQuery` (DisplayName "Execute Non Query - usp_FinalizeOrder")
- `CommandType="StoredProcedure"`, `Sql="usp_FinalizeOrder"`
- `ProviderName="System.Data.Odbc"` (ODBC)
- `Parameters`:
  - `@OrderId` — `Direction="Input"`, `ParameterType="Int32"`, `Size="4"` (correctly sized)
  - `@ResultStatus` — `Direction="Output"`, `ParameterType="String"`, **`Size="0"`** (the defect)
- Package (from `project.json`): `UiPath.Database.Activities` `[1.3.2]` — predates the historical `1.4.0` ODBC-sizing fix

---

**Immediate fix:**

The fix is in the `Execute Non Query` activity's `Parameters`
collection in `Main.xaml`.

### Database Activities (Root Cause)

1. **Set the output parameter's `Size` to the column's maximum.**
   - **Why:** Over ODBC the driver needs an explicit buffer size for
     the value a stored-procedure `Output`/`InputOutput` parameter
     returns. `Size=0` is rejected before execution.
   - **Where:** `Main.xaml` → `Execute Non Query - usp_FinalizeOrder` →
     `Parameters` → `@ResultStatus`. Set `Size` to the declared width
     of the procedure's `@ResultStatus` output column (e.g. `50` for a
     `VARCHAR(50)`, `4` for an `INT`). Keep `@OrderId` at `Size=4`.
   - **Who:** RPA developer

2. **Alternatively / additionally, upgrade `UiPath.Database.Activities`.**
   - **Why:** The ODBC output-parameter sizing bug was patched in older
     releases (historically `1.4.0`+); current packages include the
     fix. The project is on `1.3.2`.
   - **Where:** `project.json` → bump `UiPath.Database.Activities` to a
     current version, restore dependencies, retest.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-non-query-failures.md` (Branch 1 — "Stored-procedure output parameter with `Size = 0` (ODBC)")

---

**Preventive fix:**

1. **Studio** — For every stored-procedure `Output`/`InputOutput`
   parameter over ODBC, always set `Size` explicitly to the column
   width.
   - **Why:** `Size=0` is the default and silently passes design-time
     validation but faults at runtime only on ODBC.
   - **Where:** Parameters collection of each `Execute Non Query` /
     `Run Command` that calls a stored procedure.
   - **Who:** RPA developer

2. **Platform** — Pin `UiPath.Database.Activities` to a current,
   patched version across database-touching projects.
   - **Why:** Keeps the ODBC sizing fix in place and avoids
     version-specific regressions.
   - **Who:** Platform / RPA CoE

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Stored-proc Output parameter `@ResultStatus` has `Size=0` over ODBC, so the driver cannot size the returned value | High | Confirmed | Yes | `The Size property has an invalid size of 0` (ODBC `OdbcParameter`) + `CommandType=StoredProcedure` + `ProviderName="System.Data.Odbc"` + `@ResultStatus Direction=Output Size=0` in `Main.xaml` | Set the parameter `Size` to the column max (or upgrade `UiPath.Database.Activities`) |
| H2 | Unsafe / malformed SQL or parameter type mismatch (Branch 2) | Low | Rejected | No | `Sql` is the bare proc name; no syntax / type-cast error in the exception | — |
| H3 | Empty `Sql` / `CommandText` not initialized (Branch 3) | Low | Rejected | No | `Sql="usp_FinalizeOrder"` is populated | — |
| H4 | Driver / client library not loadable (Branch 4) | Low | Rejected | No | No `ErrorCode: 126` / `DllNotFoundException`; ODBC layer reached and rejected the parameter size | — |

---

Would you like help applying the fix — setting the `@ResultStatus`
output parameter's `Size` in `Main.xaml`, or bumping
`UiPath.Database.Activities` in `project.json`? I can also clean up the
`.local/investigations/` folder if you no longer need it.
