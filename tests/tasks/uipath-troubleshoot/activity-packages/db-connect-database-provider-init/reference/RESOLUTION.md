# Final Resolution

---

**Root Cause:** The `LedgerExportXlsx` process opens an Excel workbook as a
database through a `Connect to Database` activity, but the activity's
`ProviderName` is **empty**. The project was migrated from **Windows - Legacy**
to **Windows** (.NET); on the modern runtime an empty `ProviderName` resolves to
the **SqlClient** provider, so the activity initializes
`Microsoft.Data.SqlClient` and faults with
`System.TypeInitializationException: The type initializer for
'Microsoft.Data.SqlClient.SqlConnection' threw an exception.` — even though the
connection string is clearly an **Excel / ACE OLE DB** string
(`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Ledger.xlsx;...`).
The empty provider was tolerated under Windows - Legacy, which is why the
failure began right after the migration. The fix is to set `ProviderName`
explicitly to `System.Data.OleDb` (the source is Excel/Access via ACE OLE DB).

This maps to the **Connect to Database failures** playbook,
**branch 4 (provider init failure after migration / wrong `ProviderName`)**.

> `Connect to Database` is a **Database-package** activity
> (`UiPath.Database.Activities`) — it is NOT in the Excel package. Reading an
> Excel file through it is the deliberate "Excel-as-a-database" pattern (SQL
> over a workbook), distinct from `Read Range` / `Use Excel File`.

**What went wrong:** The `LedgerExportXlsx` job (started 2026-06-01T09:50:00Z)
faulted ~1.1 seconds after launch when the `Connect to Database` activity tried
to open the connection. With an empty `ProviderName`, the .NET runtime defaulted
to the SQL Server provider and the `Microsoft.Data.SqlClient.SqlConnection`
type initializer threw — the connection never opened, so the downstream
`Execute Query` (`SELECT * FROM [Ledger$]`) never ran.

**Why:** The workflow's `DatabaseConnect` activity is configured with
`ProviderName=""` (empty) and the connection string
`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Ledger.xlsx;Extended
Properties="Excel 12.0 Xml;HDR=YES;"`. `project.json` declares
`UiPath.Database.Activities` and `"targetFramework": "Windows"`. On a **Windows**
(.NET) project an empty `ProviderName` resolves toward SqlClient, so the activity
initializes `Microsoft.Data.SqlClient` instead of the OLE DB provider the
connection string requires. The error and the migration timeline line up
exactly: under Windows - Legacy the empty provider was tolerated, and the modern
runtime is the only thing that changed.

**This is NOT a malformed connection string (branch 1)** — the ACE OLE DB string
is well-formed (correct `Provider`, full `Data Source`, quoted `Extended
Properties` matching the `.xlsx` / Excel 12.0 variant). **It is NOT a provider
"not registered" / bitness mismatch (branch 2)** — the error is a SqlClient
type-initializer crash, not "provider is not registered on the local machine".
**It is NOT a file lock (branch 3)** — there is no sharing violation. **And the
fix is NOT to switch the provider to `Microsoft.Data.SqlClient`** — that is for
SQL Server; the target here is an Excel/Access workbook, so the correct provider
is `System.Data.OleDb`. The failing component is the empty `ProviderName`, not
the connection string, the driver, the file, or the query.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `LedgerExportXlsx` — Faulted at 2026-06-01T09:50:01.331Z (ran ~1.1 seconds)
- Folder: Finance Operations (key `a5e6f7b8-9c0d-4e1f-8a2b-4c5d6e7f8091`)
- Executing robot identity: `RobotUser1` on host `MOCK-HOST`
- `or jobs get` `Info`: `Connect to Database: A database error occurred.` →
  `System.TypeInitializationException: The type initializer for
  'Microsoft.Data.SqlClient.SqlConnection' threw an exception.` with frames into
  `Microsoft.Data.SqlClient.SqlConnection..ctor` and
  `UiPath.Database.DatabaseConnection.Connect`, at
  `DatabaseConnect "Connect to Database"`
- `or jobs logs --level Error`: the runtime resolved the empty `ProviderName` to
  the SqlClient provider while the connection string is an ACE/Excel OLE DB
  string

### Database Activities (Surface)
- Activity (from `Main.xaml`): `DatabaseConnect` (DisplayName: "Connect to
  Database") — a `UiPath.Database.Activities` activity (NOT the Excel package)
- `ProviderName` (from `Main.xaml`): **empty** (`ProviderName=""`) — the bug
- `ConnectionString` (from `Main.xaml`):
  `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Ledger.xlsx;Extended
  Properties="Excel 12.0 Xml;HDR=YES;"` — well-formed Excel/ACE OLE DB string
- Downstream: `Execute Query` with `SELECT * FROM [Ledger$]` against `[dbConn]`
  — correct sheet-as-table syntax; never ran because the connect faulted

### Project compatibility (Root Cause)
- `project.json`: `"targetFramework": "Windows"` → migrated off Windows - Legacy
- A SqlClient type-initializer crash against a well-formed Excel/ACE OLE DB
  connection string, on a project just moved to **Windows**, where
  `ProviderName` is empty, confirms branch 4: the empty provider resolved to
  SqlClient on the modern runtime.

---

**Immediate fix:**

The fix is **in the workflow**, not the connection string or the host.

### Database Activities — branch 4 (Root Cause)

1. **Set `ProviderName` explicitly to `System.Data.OleDb` on the Connect to Database activity.**
   - **Why:** The connection string targets Excel through ACE OLE DB. On a
     **Windows** (.NET) project an empty `ProviderName` resolves to the SQL
     Server provider (SqlClient), which throws the type-initializer exception.
     Setting the provider explicitly to `System.Data.OleDb` routes the
     connection through OLE DB, matching the ACE/Excel connection string.
   - **Where:** `Main.xaml` → `Connect to Database` activity → `ProviderName`
     property (currently empty). Set to `System.Data.OleDb`.
   - **Who:** RPA developer

2. **Do NOT switch the provider to `Microsoft.Data.SqlClient`.**
   - **Why:** `Microsoft.Data.SqlClient` is the **SQL Server** provider. The
     target here is an Excel/Access workbook, so SqlClient is the wrong provider
     — it is exactly what the empty value resolved to and what threw. For an
     ODBC DSN/driver the value would be `System.Data.Odbc`; for ACE OLE DB it is
     `System.Data.OleDb`.
   - **Source:** `database-activities/playbooks/connect-to-database-failures.md`
     (branch 4 — "Provider init failure after migration / wrong `ProviderName`")

3. **Re-publish and re-run the migrated process.**
   - **Why:** Confirm the explicit OLE DB provider opens the connection and the
     downstream `Execute Query` (`SELECT * FROM [Ledger$]`) returns rows.
   - **Who:** RPA developer

---

**Preventive fix:**

1. **Migration audit** — After switching any project from Windows - Legacy to
   Windows, audit every `Connect to Database` activity and set `ProviderName`
   explicitly. Empty providers that "worked" under Windows - Legacy fault on the
   modern runtime.
   - **Who:** RPA developer / migration lead

2. **Studio** — Always set `ProviderName` explicitly for file-based sources
   (`System.Data.OleDb` for ACE OLE DB, `System.Data.Odbc` for ODBC) rather than
   relying on a default. Pin it in the workflow.
   - **Who:** RPA developer

3. **Orchestrator** — Add an alert subscription on faulted jobs for this process
   so a provider regression surfaces immediately after a migration deploy rather
   than on the first scheduled run.
   - **Who:** Tenant admin

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Empty `ProviderName` on the migrated Windows project resolves to SqlClient, so Connect to Database initializes Microsoft.Data.SqlClient and throws a type-initializer exception against an Excel/ACE OLE DB source | High | Confirmed | Yes | `TypeInitializationException` for `Microsoft.Data.SqlClient.SqlConnection` at Connect to Database + empty `ProviderName` in Main.xaml + well-formed ACE connection string + `project.json` targetFramework "Windows" + failure began right after the migration | Set `ProviderName="System.Data.OleDb"` on the Connect to Database activity |
| H2 | Malformed / wrong connection string | Low | Rejected | No | `ConnectionString` is well-formed: correct `Provider`, full `Data Source`, quoted `Extended Properties="Excel 12.0 Xml;HDR=YES;"` matching `.xlsx` | n/a |
| H3 | Provider not registered / bitness mismatch | Low | Rejected | No | Error is a SqlClient type-initializer crash, not "provider is not registered on the local machine" | n/a |
| H4 | Workbook locked / used by another process | Low | Rejected | No | No sharing violation in the error text | n/a |

---

Would you like help applying the fix — drafting the exact `ProviderName`
(`System.Data.OleDb`) change for the `Connect to Database` activity in
`Main.xaml`, plus a checklist to audit the other migrated projects? I can also
clean up the `.local/investigations/` folder if you no longer need it.
