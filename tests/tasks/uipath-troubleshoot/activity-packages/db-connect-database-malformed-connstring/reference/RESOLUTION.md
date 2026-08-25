# Final Resolution

---

**Root Cause:** The `MonthlyReconImport` process opens an Excel workbook as a
database through a `Connect to Database` activity using the ACE OLE DB provider
(`Provider=Microsoft.ACE.OLEDB.12.0`). Its `ConnectionString` is **malformed**:
the `Extended Properties` value is **not quoted**, so the `;` characters inside
`Excel 12.0 Xml;HDR=YES;` are read by the ADO.NET connection-string parser as
key/value separators rather than as part of the value. The parser cannot make
sense of the resulting fragments and rejects the string with
`System.ArgumentException: Format of the initialization string does not conform
to specification starting at index 47.` The fix is to **quote** the
`Extended Properties` value: `Extended Properties="Excel 12.0 Xml;HDR=YES;"`.

This maps to the **Connect to Database failures** playbook,
**branch 1 (malformed / wrong connection string)**.

> `Connect to Database` is a **Database-package** activity
> (`UiPath.Database.Activities`) — it is NOT in the Excel package. Reading an
> Excel file through it is the deliberate "Excel-as-a-database" pattern (SQL
> over a workbook), distinct from `Read Range` / `Use Excel File`.

**What went wrong:** The `MonthlyReconImport` job (started
2026-06-01T07:05:00Z) faulted ~0.8 seconds after launch when the
`Connect to Database` activity tried to parse the connection string. The fault
is at the parse stage — before any I/O against the workbook — so the downstream
`Execute Query` (`SELECT * FROM [Sheet1$]`) never ran.

**Why:** The workflow's `DatabaseConnect` activity is configured with
`ProviderName="System.Data.OleDb"` and the connection string
`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Recon.xlsx;Extended
Properties=Excel 12.0 Xml;HDR=YES;`. A connection string is parsed as a list of
`keyword=value;` pairs. The provider-correct ACE layout quotes the
`Extended Properties` value because that value itself contains `;`:
`Extended Properties="Excel 12.0 Xml;HDR=YES;"`. Here the quotes are missing,
so after `Extended Properties=Excel 12.0 Xml` the parser hits a bare `;` and
expects a new `keyword=value` pair; `HDR=YES` parses, but the trailing
fragments do not conform, and the parser throws
`System.ArgumentException: Format of the initialization string does not conform
to specification`. The stack shows the failure inside
`System.Data.Common.DbConnectionOptions` (the connection-string parser),
called from `UiPath.Database.DatabaseConnection.Connect` — confirming the
string never reached the OLE DB driver.

This is **not** branch 2 (the ACE provider being "not registered" / a bitness
mismatch), **not** branch 3 (a locked / in-use workbook), and **not** branch 4
(a provider-init failure / wrong `ProviderName` / a `Microsoft.Data.SqlClient`
type-initializer error). It is also **not** a SQL syntax error in the query and
**not** a missing file or sheet — the parser fails on the connection string's
*format* before the provider, the file, or the query are ever touched.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `MonthlyReconImport` — Faulted at 2026-06-01T07:05:00.948Z (ran ~0.8 seconds)
- Folder: Finance Operations (key `c1a2b3d4-5e6f-4a7b-8c9d-0e1f2a3b4c5d`)
- Executing robot identity: `RobotUser1` (`UIPATH\ROBOTUSER1`) on host `MOCK-HOST`
- `or jobs get` `Info`: `Connect to Database: A database error occurred.` → `System.ArgumentException: Format of the initialization string does not conform to specification starting at index 47.` at `DatabaseConnect "Connect to Database"`
- `or jobs logs --level Error`: the trace pins the fault to `[Connect to Database]` with frames into `System.Data.Common.DbConnectionOptions` and `UiPath.Database.DatabaseConnection.Connect`

### Database Activities (Root Cause)
- Activity (from `Main.xaml`): `DatabaseConnect` (DisplayName: "Connect to Database") — a `UiPath.Database.Activities` activity (NOT Excel package)
- `ProviderName` (from `Main.xaml`): `System.Data.OleDb` — correct for ACE OLE DB; the failure is not a provider/init issue
- `ConnectionString` (from `Main.xaml`): `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Recon.xlsx;Extended Properties=Excel 12.0 Xml;HDR=YES;` — the `Extended Properties` value is **unquoted**; the embedded `;` breaks the `keyword=value;` layout
- The exception originates in the connection-string parser (`DbConnectionOptions`), confirming a format error rather than a driver, file, or query error
- Downstream: `Execute Query` with `SELECT * FROM [Sheet1$]` — well-formed and never reached

---

**Immediate fix:**

The fix is **in the workflow's connection string**, not on the Robot host and
not in the query.

### Database Activities — branch 1 (Root Cause)

1. **Quote the `Extended Properties` value in the `Connect to Database` ConnectionString.**
   - **Why:** A connection string is a list of `keyword=value;` pairs. The
     `Extended Properties` value contains `;`, so it must be wrapped in double
     quotes; otherwise the parser treats the embedded `;` as a separator and
     rejects the string with "Format of the initialization string does not
     conform to specification".
   - **What:** Change the `ConnectionString` on the `DatabaseConnect` activity
     in `Main.xaml` from
     `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Recon.xlsx;Extended Properties=Excel 12.0 Xml;HDR=YES;`
     to
     `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Recon.xlsx;Extended Properties="Excel 12.0 Xml;HDR=YES;"`.
   - **Who:** RPA developer (Studio)

2. **Keep the SQL in `Execute Query`, not in the connection string.**
   - **Why:** The connection string must contain only provider/connection
     keywords. The `SELECT * FROM [Sheet1$]` belongs in the `Execute Query`
     `Sql` property (it already does here) — do not paste SQL into the
     connection string.
   - **Source:** `database-activities/playbooks/connect-to-database-failures.md`
     (branch 1 — "Malformed / wrong connection string")

---

**Preventive fix:**

1. **Studio** — Author file-based connection strings from the provider-correct
   template and always quote `Extended Properties`:
   `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=<full path>.xlsx;Extended Properties="Excel 12.0 Xml;HDR=YES;"`
   (`HDR=NO` when the sheet has no header row). For legacy `.xls`, use
   `Microsoft.Jet.OLEDB.4.0` + `Extended Properties="Excel 8.0;HDR=YES;"`.
   - **Who:** RPA developer

2. **Review** — Add a pre-merge check that the `Connect to Database`
   `ConnectionString` parses (balanced quotes, quoted `Extended Properties`,
   no SQL text leaked in) so a malformed string is caught before deploy.
   - **Who:** RPA lead / reviewer

3. **Orchestrator** — Add an alert subscription on faulted jobs for this
   process so a connection-string regression surfaces on the first run after
   deploy rather than silently.
   - **Who:** Tenant admin

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The `Connect to Database` ConnectionString is malformed — the `Extended Properties` value is unquoted, so the embedded `;` breaks the `keyword=value;` layout and the parser rejects the string | High | Confirmed | Yes | `System.ArgumentException: Format of the initialization string does not conform to specification starting at index 47` at Connect to Database, with frames in `DbConnectionOptions` + the unquoted `Extended Properties=Excel 12.0 Xml;HDR=YES;` in Main.xaml | Quote the value: `Extended Properties="Excel 12.0 Xml;HDR=YES;"` |
| H2 | The ACE OLE DB provider is not registered / bitness mismatch (branch 2) | Low | Rejected | No | Error is an `ArgumentException` parse failure, not `InvalidOperationException: provider is not registered`; the string never reached the driver | n/a |
| H3 | Workbook locked / used by another process (branch 3) | Low | Rejected | No | No sharing violation; fault is at connection-string parse, before any file I/O | n/a |
| H4 | Provider-init failure / wrong `ProviderName` (branch 4) | Low | Rejected | No | `ProviderName="System.Data.OleDb"` is correct; no `Microsoft.Data.SqlClient` type-initializer error | n/a |

---

Would you like help applying the fix — editing the `Connect to Database`
`ConnectionString` in `Main.xaml` to quote the `Extended Properties` value? I
can also clean up the `.local/investigations/` folder if you no longer need it.
