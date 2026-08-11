# Final Resolution

---

**Root Cause:** The `DailyInvoiceLoad` process opens an Excel workbook as a
database through a `Connect to Database` activity using the ACE OLE DB provider
(`Provider=Microsoft.ACE.OLEDB.12.0`). The connection string and provider are
**correct** — the failure is a **file lock / sharing violation**: the target
workbook `C:\Finance\Invoices.xlsx` is held open by another process at run time
(the Excel UI, an orphaned `EXCEL.EXE` from a prior run, a concurrent job
touching the same file, or a OneDrive / sync / AV client). File-based providers
request a write lock by default, so the ACE provider cannot acquire the file and
the connect throws
`System.IO.IOException: The process cannot access the file
'C:\Finance\Invoices.xlsx' because it is being used by another process.`

This maps to the **Connect to Database failures** playbook,
**branch 3 (file lock / sharing violation)**.

> `Connect to Database` is a **Database-package** activity
> (`UiPath.Database.Activities`) — it is NOT in the Excel package. Reading an
> Excel file through it is the deliberate "Excel-as-a-database" pattern (SQL
> over a workbook), distinct from `Read Range` / `Use Excel File`.

**What went wrong:** The `DailyInvoiceLoad` job (started 2026-06-01T05:40:01Z)
faulted ~1.1 seconds after launch when the `Connect to Database` activity tried
to open the ACE OLE DB connection and the OLE DB provider could not acquire the
workbook file because another process already held it open.

**Why:** The workflow's `DatabaseConnect` activity is configured with
`ProviderName="System.Data.OleDb"` and the connection string
`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Invoices.xlsx;Extended
Properties="Excel 12.0 Xml;HDR=YES;"`, followed by an `Execute Query` running
`SELECT * FROM [Invoices$]`. The connection string is well-formed (correct
`Provider`, full `Data Source`, quoted `Extended Properties` matching the
`.xlsx` / ACE 12.0 variant), the provider name is the correct
`System.Data.OleDb`, and the SQL is valid sheet-as-table syntax. The exception
class is `System.IO.IOException` with the "used by another process" text and a
stack into the OLE DB provider open path and
`UiPath.Database.DatabaseConnection.Connect` — a sharing violation while
acquiring the file, not a configuration error.

This is **NOT** branch 1 (the connection string is well-formed), **NOT** branch
2 (the error is "used by another process", not "provider is not registered" —
the provider loads fine), **NOT** branch 4 (the provider is the correct
`System.Data.OleDb`, there is no `Microsoft.Data.SqlClient` type-initializer
error), **NOT** a SQL syntax error (the connect fails before the query runs),
and **NOT** a "file not found / wrong path / missing sheet" — the file exists,
it is **locked**.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `DailyInvoiceLoad` — Faulted at 2026-06-01T05:40:02.337Z (ran ~1.1 seconds)
- Folder: Finance Operations (key `e3c4d5f6-7a8b-4c9d-8e0f-2a3b4c5d6e7f`)
- Executing robot identity: `RobotUser1` on host `MOCK-HOST`
- `or jobs get` `Info`: `Connect to Database: A database error occurred.` →
  `System.IO.IOException: The process cannot access the file
  'C:\Finance\Invoices.xlsx' because it is being used by another process.` with
  frames into `System.Data.OleDb.OleDbConnection.Open` and
  `UiPath.Database.DatabaseConnection.Connect`, at `DatabaseConnect "Connect to
  Database"`
- `or jobs logs --level Error`: the trace pins the fault to the
  `[Connect to Database]` step with the same "used by another process" message

### Database Activities (Surface)
- Activity (from `Main.xaml`): `DatabaseConnect` (DisplayName: "Connect to
  Database") — a `UiPath.Database.Activities` activity (NOT Excel package)
- `ProviderName` (from `Main.xaml`): `System.Data.OleDb` — correct for ACE OLE DB
- `ConnectionString` (from `Main.xaml`):
  `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Invoices.xlsx;Extended Properties="Excel 12.0 Xml;HDR=YES;"`
  — well-formed; matches the `.xlsx` / ACE 12.0 variant
- Downstream: `Execute Query` with `SELECT * FROM [Invoices$]` and
  `ExistingDbConnection="[dbConn]"` — correct sheet-as-table syntax; never runs
  because the connect faults first

### File lock (Root Cause)
- The exception is `System.IO.IOException` with "because it is being used by
  another process" — a sharing violation, not a configuration error. The message
  names the exact file the connection targets (`C:\Finance\Invoices.xlsx`),
  confirming the locked file is the workbook the activity opens.

---

**Immediate fix:**

The fix is **on the Robot host / workbook**, not in the workflow's connection
string or provider. Because the requester only has Orchestrator access, hand
this back as a concrete instruction for whoever administers the Robot machine.

### Database Activities — branch 3 (Root Cause)

1. **Ensure the workbook is closed and no orphaned process holds it before the run.**
   - **Why:** A file-based ACE OLE DB connection requests a write lock by
     default. If `C:\Finance\Invoices.xlsx` is open in the Excel UI, held by an
     orphaned `EXCEL.EXE` from a prior run, touched by a concurrent job, or
     locked by a OneDrive / sync / AV client, the provider cannot acquire it and
     the connect throws the "used by another process" sharing violation.
   - **Where:** On `MOCK-HOST` (every Robot host that runs this process), close
     the workbook and kill any stray `EXCEL.EXE` process holding the handle.
     Add a kill-orphan-process hygiene step at job start so a leaked handle from
     a prior run does not block the next run.
   - **Who:** Robot host administrator

2. **For read-only SELECTs, open the connection read-only (`Mode=Read`).**
   - **Why:** This workload only runs `SELECT * FROM [Invoices$]`, so it does
     not need a write lock. Opening read-only stops the engine from requesting a
     write lock, reducing lock contention with other readers of the workbook.
   - **Where:** In Studio, add `Mode=Read` to the connection string on the
     `Connect to Database` activity:
     `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Invoices.xlsx;Mode=Read;Extended Properties="Excel 12.0 Xml;HDR=YES;"`
     (some provider versions instead carry a read flag in `Extended Properties`;
     verify against your ACE version).
   - **Who:** RPA developer

3. **Do NOT "fix" the connection string or provider.**
   - **Why:** The connection string, provider (`System.Data.OleDb`), and SQL are
     all correct. Rewriting them does not release a held file handle and only
     masks the real cause.
   - **Source:** `database-activities/playbooks/connect-to-database-failures.md`
     (branch 3 — "File lock / sharing violation")

---

**Preventive fix:**

1. **Robot host hygiene** — Add a "kill stray `EXCEL.EXE`" cleanup step at job
   start for every host that runs this process, so a leaked handle from a prior
   run cannot block the next run.
   - **Who:** Platform / SRE team

2. **Studio** — Open file-based connections read-only (`Mode=Read`) for
   SELECT-only workloads to avoid taking a write lock, and keep the target
   workbook off interactive desktops and sync-backed paths during runs.
   - **Who:** RPA developer

3. **Orchestrator** — Avoid scheduling concurrent jobs that touch the same
   workbook, and add a faulted-job alert subscription on this process so a lock
   contention surfaces immediately rather than silently failing each run.
   - **Who:** Tenant admin

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The target workbook `C:\Finance\Invoices.xlsx` is held open by another process (Excel UI / orphan EXCEL.EXE / concurrent job / sync client), so the file-based ACE provider cannot acquire it (sharing violation) | High | Confirmed | Yes | `System.IO.IOException: The process cannot access the file 'C:\Finance\Invoices.xlsx' because it is being used by another process` at Connect to Database, with frames into `OleDbConnection.Open` / `DatabaseConnection.Connect` + well-formed ACE connection string and correct provider in Main.xaml | Close the workbook / kill orphan processes before the run; open read-only (`Mode=Read`) for SELECT-only workloads |
| H2 | Malformed / wrong connection string (branch 1) | Low | Rejected | No | `ConnectionString` is well-formed: correct `Provider`, full `Data Source`, quoted `Extended Properties="Excel 12.0 Xml;HDR=YES;"` matching `.xlsx` | n/a |
| H3 | Provider not registered / bitness mismatch (branch 2) | Low | Rejected | No | Error is "used by another process", not "provider is not registered" — the provider loads fine | n/a |
| H4 | Provider init / wrong ProviderName (branch 4) | Low | Rejected | No | `ProviderName` is the correct `System.Data.OleDb`; no `Microsoft.Data.SqlClient` type-initializer error | n/a |

---

Would you like help applying the fix — drafting the exact host-side cleanup step
(close the workbook / kill orphan `EXCEL.EXE`) and the read-only (`Mode=Read`)
connection-string change to hand to the Robot machine administrator? I can also
clean up the `.local/investigations/` folder if you no longer need it.
