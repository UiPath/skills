---
confidence: medium
---

# Connect to Database Failures (Excel / Access via OLE DB / ODBC)

## Context

A `UiPath.Database.Activities` `Connect to Database` (`DatabaseConnect`) activity opens an ADO.NET connection from a `ConnectionString` + `ProviderName` and outputs a `DatabaseConnection` for downstream `Execute Query` / `Execute Non Query` / `Run Command` activities. Connection-open failures cluster heavily around **file-based providers** — using an Excel workbook (or Access database) as the data source through the ACE OLE DB or an ODBC driver — where the connection string, driver registration, process bitness, and file locking all have to line up.

Rule out the package confusion first: **`Connect to Database` lives in `UiPath.Database.Activities`, not `UiPath.Excel.Activities`.** Reading an Excel file through database activities is the deliberate "Excel-as-a-database" pattern (SQL over a workbook), distinct from the Excel package's `Read Range` / `Use Excel File`. If the user went looking for `Connect to Database` in the Excel package, clearing up that mismatch is step zero.

What this looks like — Connect to Database faults surface as one of these signatures:

- `System.ArgumentException` / `Format of the initialization string does not conform to specification starting at index N` / a generic "Invalid connection string" — branch 1.
- `System.InvalidOperationException: The 'Microsoft.ACE.OLEDB.12.0' provider is not registered on the local machine` (or `Microsoft.Jet.OLEDB.4.0` for legacy `.xls`) — branch 2.
- `The process cannot access the file '<path>' because it is being used by another process` / a sharing violation from the engine — branch 3.
- `The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception` (or another provider type-initializer / driver-init failure) on a project moved to **Windows** (.NET) — branch 4.

What can cause it (cause-branches — pick the right one from evidence):

1. **Malformed / wrong connection string** — the `ConnectionString` does not match the provider's required layout. The correct ACE OLE DB shape for a modern `.xlsx` is:

   ```text
   Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Path\To\File.xlsx;Extended Properties="Excel 12.0 Xml;HDR=YES;"
   ```

   `HDR=YES` treats the first row as column headers; use `HDR=NO` when the sheet has no header row. Common mistakes: unquoted or missing `Extended Properties`, missing `Data Source`, using the `Excel 12.0 Xml` variant against a legacy `.xls` (which needs `Excel 8.0` and the `Microsoft.Jet.OLEDB.4.0` provider), or SQL text accidentally pasted into the connection string (that variant routes to [execute-query-failures.md](./execute-query-failures.md) branch 4).
2. **Provider not registered / architecture (bitness) mismatch** — the ACE OLE DB / ODBC driver named in the connection string is not installed, or its bitness does not match the process. A **Windows** project runs as a **64-bit** process and needs the **64-bit** Microsoft Access Database Engine (ACE); a 32-bit-only ACE install (commonly bundled with 32-bit Office) produces "provider is not registered on the local machine". Mixed Office bitness on the host complicates the install (the 64-bit engine may refuse to install alongside 32-bit Office without the `/quiet` workaround).
3. **File lock / sharing violation** — the workbook is open in Excel or held by another process (an orphaned process from a prior run, a concurrent job, a OneDrive/sync or AV client), so the engine cannot acquire the file. File-based providers request a write lock by default, so even a read-only SELECT fails while the file is held.
4. **Provider init failure after migration / wrong `ProviderName`** — on a project switched from **Windows - Legacy** to **Windows** (.NET), leaving `ProviderName` empty (or defaulted to a SqlClient value) makes the activity initialize the SQL Server provider, which throws a type-initializer exception in the .NET runtime — even though the intended target is Excel. The provider must be set explicitly: `System.Data.OleDb` for ACE OLE DB, or `System.Data.Odbc` for an ODBC DSN/driver.

What to look for:

- **The exception class and message** — first signal, maps directly to a branch per the signature list. "provider is not registered" → branch 2; "initialization string" / `ArgumentException` → branch 1; "used by another process" → branch 3; "type initializer for 'Microsoft.Data.SqlClient...'" → branch 4.
- **`ConnectionString` + `ProviderName`** (literal values) from the workflow source — the provider name, the `Data Source` path and its extension (`.xlsx` vs `.xls`), and the `Extended Properties` block.
- **Project compatibility and process bitness** — `project.json` (`Windows` vs `Windows-Legacy`); a **Windows** project is a 64-bit process. Load-bearing for branches 2 and 4.
- **Driver inventory on the Robot host** — whether the Microsoft Access Database Engine (ACE) or the ODBC driver is installed, and its **bitness**, on the machine that ran the job (not the dev machine).
- **Workbook lock state at run time** — whether the file was open in Excel, held by an orphaned process, or on a sync-backed path.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and full message (including inner exception). From workflow source (`.xaml`): the `Connect to Database` node's literal `ConnectionString` and `ProviderName`, and the `Data Source` path/extension inside the connection string. From `project.json`: the project compatibility (`Windows` vs `Windows-Legacy`).

2. **Branch the diagnostic on the signature.**
   - `ArgumentException` / "initialization string" / "Invalid connection string" → branch 1; go to step 3.
   - "provider is not registered on the local machine" → branch 2; go to step 4.
   - "used by another process" / sharing violation → branch 3; go to step 5.
   - "type initializer for 'Microsoft.Data.SqlClient...'" / driver-init on a Windows project → branch 4; go to step 6.

3. **Confirm branch 1 (connection string).** Compare the literal `ConnectionString` against the provider's required layout. For Excel/ACE: `Provider=`, `Data Source=<full path>`, and a quoted `Extended Properties="Excel 12.0 Xml;HDR=YES;"`. Check the file extension matches the variant (`.xlsx` → `Excel 12.0 Xml` + ACE 12.0; `.xls` → `Excel 8.0` + Jet 4.0). Confirm no SQL text leaked into the connection string and that all quotes are balanced.

4. **Confirm branch 2 (provider not registered / bitness).** Determine the process bitness from project compatibility (**Windows** = 64-bit). Check whether the ACE/ODBC driver is installed on the Robot host and its bitness (Control Panel → Programs, or the registry under `HKLM\SOFTWARE\...\Microsoft.ACE.OLEDB.12.0` vs the `WOW6432Node` 32-bit hive). "Not registered" with a 64-bit process and only a 32-bit ACE present confirms the mismatch.

5. **Confirm branch 3 (file lock).** Check whether the workbook was open in Excel or held by another process at the failure time: an orphaned process holding the handle, a concurrent job touching the same file, or a sync/AV client. The message names the file path — confirm it is the workbook the connection targets.

6. **Confirm branch 4 (provider init / wrong ProviderName).** Confirm the project is **Windows** (.NET) and read `ProviderName` on the activity. Empty or a SqlClient value while the `ConnectionString` is clearly an Excel/ACE OLE DB string confirms the branch — the runtime is initializing SqlClient instead of OLE DB.

The root cause must name **which of the four surfaces** the failure maps to, with the specific evidence: the exception text, the literal `ConnectionString`/`ProviderName`, the project compatibility/bitness, and the host's driver inventory. A generic "could not connect" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Connection string:**
  - Use the provider-correct layout. Excel `.xlsx` via ACE OLE DB: `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=<full path>.xlsx;Extended Properties="Excel 12.0 Xml;HDR=YES;"` (`HDR=NO` if the sheet has no header row). Legacy `.xls`: `Provider=Microsoft.Jet.OLEDB.4.0;...;Extended Properties="Excel 8.0;HDR=YES;"`.
  - Quote the `Extended Properties` value, supply a full `Data Source` path, and keep SQL out of the connection string (the `SELECT` belongs in the `Execute Query` `Sql` property).

- **Branch 2 — Provider not registered / bitness mismatch:**
  - Match the **process** bitness, not Office's. A **Windows** project is 64-bit → install the **64-bit** Microsoft Access Database Engine (ACE) on every Robot host.
  - If 32-bit Office is installed and blocks the 64-bit engine installer, run the engine installer with the `/quiet` switch to force the install alongside it.
  - Alternative: set the project to **Windows - Legacy** (32-bit) only if a 64-bit engine genuinely cannot be installed — but prefer installing the 64-bit ACE so the modern runtime is used.

- **Branch 3 — File lock:**
  - Ensure the workbook is closed (and no orphaned process holds it) before the robot runs; kill stray processes as a hygiene step at job start if a prior run can leak a handle.
  - For read-only workloads (SELECT only), open the connection read-only so the engine does not request a write lock — for ACE OLE DB add `Mode=Read` to the connection string. (Some setups instead carry a read flag in `Extended Properties`; verify against your provider version.)

- **Branch 4 — Provider init / wrong ProviderName:**
  - Set `ProviderName` explicitly on the activity. For Excel/Access via ACE OLE DB: `System.Data.OleDb`. For an ODBC DSN/driver: `System.Data.Odbc`. Do **not** leave it empty or set to a SqlClient value when the target is a file-based source.
  - This is the canonical fix when a working Windows-Legacy project starts failing with a `Microsoft.Data.SqlClient` type-initializer error after migration to **Windows** — the empty provider was implicitly resolving to SqlClient.

### Querying the workbook (after a successful connect)

Once connected, address each sheet as a table by appending `$` to the sheet name and wrapping it in brackets: `SELECT * FROM [Sheet1$]`. A named range is addressed as `[RangeName]`. Query-side failures (syntax, parameters, timeouts) are covered in [execute-query-failures.md](./execute-query-failures.md).

## Anti-patterns (what NOT to do)

- **"Install the 32-bit Access Database Engine to match 32-bit Office."** The driver bitness must match the **process** bitness, not the installed Office bitness. A **Windows** project is a 64-bit process and needs the 64-bit ACE even when Office is 32-bit. Matching Office instead reproduces branch 2.
- **"Leave `ProviderName` empty and let it auto-detect."** On a **Windows** (.NET) project an empty provider resolves toward SqlClient and throws a type-initializer error against an Excel source (branch 4). Always set the provider explicitly for file-based sources.
- **"Wrap Connect in a Try Catch that catches `System.Exception` and continues."** A bare catch that logs and swallows turns a failed connection into a downstream null-connection fault (`Object reference not set` in the next `Execute Query` — see [execute-query-failures.md](./execute-query-failures.md) branch 1), which is harder to diagnose than the original connect error. Use Try-Catch only with a real recovery path (retry a transient lock, mark the queue item Failed, notify, or re-throw a domain-specific exception) — and catch the specific provider/`DataException`, not bare `System.Exception`, so unrelated faults still surface.

## Prevention (cross-branch)

- Confirm the activity is `Connect to Database` from `UiPath.Database.Activities` (the Excel package has no such activity), and that "Excel-as-a-database" is the intended pattern rather than `Read Range` / `Use Excel File`.
- Provision every Robot host with the **64-bit** Microsoft Access Database Engine when the project is **Windows**, and verify the driver bitness as part of host setup — not at first failure.
- Set `ProviderName` explicitly (`System.Data.OleDb` / `System.Data.Odbc`) on file-based connections and pin it in the workflow rather than relying on defaults.
- Keep the target workbook closed during runs and address sheets as `[Sheet$]`; for read-only flows open the connection read-only (`Mode=Read`) to avoid lock contention.

## Related

- [execute-query-failures.md](./execute-query-failures.md) — the query-side surface (null-connection from a failed connect, SQL syntax, query-in-connection-string, timeouts).
- [`../overview.md`](../overview.md) — the package connection model (Connect → `DatabaseConnection` → data activities).
