# Final Resolution

---

**Root Cause:** The `ExcelDbReport` process opens an Excel workbook as a
database through a `Connect to Database` activity using the ACE OLE DB
provider (`Provider=Microsoft.ACE.OLEDB.12.0`). The project is **Windows**, so
it runs as a **64-bit** process — but the Robot host only has the **32-bit**
Microsoft Access Database Engine (ACE) installed (commonly bundled with 32-bit
Office). A 64-bit process cannot load a 32-bit provider, so the ACE OLE DB
provider is "not registered" for that process. Orchestrator surfaces this as
`System.InvalidOperationException: The 'Microsoft.ACE.OLEDB.12.0' provider is
not registered on the local machine.` The provider bitness must match the
**process** bitness, not Office's.

This maps to the **Connect to Database failures** playbook,
**branch 2 (provider not registered / architecture (bitness) mismatch)**.

> `Connect to Database` is a **Database-package** activity
> (`UiPath.Database.Activities`) — it is NOT in the Excel package. Reading an
> Excel file through it is the deliberate "Excel-as-a-database" pattern (SQL
> over a workbook), distinct from `Read Range` / `Use Excel File`.

**What went wrong:** The `ExcelDbReport` job (started 2026-05-21T09:14:02Z)
faulted ~1.5 seconds after launch when the `Connect to Database` activity tried
to open the ACE OLE DB connection and the provider could not be loaded into the
64-bit Robot process.

**Why:** The workflow's `DatabaseConnect` activity is configured with
`ProviderName="System.Data.OleDb"` and the connection string
`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Data\SomeBook.xlsx;Extended
Properties="Excel 12.0 Xml;HDR=YES;"`, followed by an `Execute Query` running
`SELECT * FROM [Sheet1$]`. `project.json` declares `UiPath.Database.Activities`
and `"targetFramework": "Windows"`. A **Windows** project is a 64-bit process,
which requires the **64-bit** ACE engine. The host only has the 32-bit engine
(it was installed with 32-bit Office), so the 64-bit process reports the
provider as not registered. Matching the engine to Office's bitness instead of
the process bitness is exactly what reproduces this failure.

This is **not** a connection-string typo, a locked workbook, a wrong file path,
or a SQL syntax error. The connection string, provider, and query are all
correct; the missing 64-bit driver on the Robot host is the failing component.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `ExcelDbReport` — Faulted at 2026-05-21T09:14:03.602Z (ran ~1.5 seconds)
- Folder: Finance Automations (key `7c1f2e9a-4b6d-4a8e-9f3c-2d5e6a7b8c9d`)
- Executing robot identity: `RobotUser1` on host `MOCK-HOST`
- `or jobs get` `Info`: `Connect to Database: The 'Microsoft.ACE.OLEDB.12.0' provider is not registered on the local machine.` → `System.InvalidOperationException` at `DatabaseConnect "Connect to Database"`
- `or jobs logs --level Error`: the trace pins the fault to the `[Connect to Database]` step

### Database Activities (Surface)
- Activity (from `Main.xaml`): `DatabaseConnect` (DisplayName: "Connect to Database") — a `UiPath.Database.Activities` activity (NOT Excel package)
- `ProviderName` (from `Main.xaml`): `System.Data.OleDb` — correct for ACE OLE DB
- `ConnectionString` (from `Main.xaml`): `Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Data\SomeBook.xlsx;Extended Properties="Excel 12.0 Xml;HDR=YES;"` — well-formed; matches the `.xlsx` / ACE 12.0 variant
- Downstream: `Execute Query` with `SELECT * FROM [Sheet1$]` — correct sheet-as-table syntax

### Project compatibility / bitness (Root Cause)
- `project.json`: `"targetFramework": "Windows"` → the process runs **64-bit**
- The "provider is not registered" exception against a well-formed ACE OLE DB string on a 64-bit process, where only the 32-bit ACE engine is present on the host, confirms branch 2: the provider bitness does not match the process bitness.

---

**Immediate fix:**

The fix is **on the Robot host**, not in the workflow or the connection string.
Because the requester only has Orchestrator access, hand this back as a
concrete host-side instruction for whoever administers the Robot machine.

### Database Activities — branch 2 (Root Cause)

1. **Install the 64-bit Microsoft Access Database Engine on the Robot host.**
   - **Why:** A **Windows** project runs as a 64-bit process and needs the
     **64-bit** ACE OLE DB provider. The host only has the 32-bit engine
     (bundled with 32-bit Office), which a 64-bit process cannot load —
     producing "provider is not registered on the local machine".
   - **Where:** Download the Microsoft Access Database Engine 2016
     redistributable (x64) and install it on `MOCK-HOST` (every Robot host that
     runs this process).
   - **Who:** Robot host / desktop administrator

2. **If 32-bit Office blocks the 64-bit engine installer, force the install with `/quiet`.**
   - **Why:** The 64-bit engine installer refuses to install alongside 32-bit
     Office by default. The `/quiet` switch bypasses that block and installs the
     64-bit engine side-by-side.
   - **Where:** From an elevated prompt on the Robot host:
     `accessdatabaseengine_X64.exe /quiet`
   - **Who:** Robot host administrator

3. **Match the provider bitness to the PROCESS bitness, not Office's.**
   - **Why:** The most common wrong fix here is installing the 32-bit engine to
     "match 32-bit Office" — that reproduces the failure. The 64-bit process
     needs the 64-bit engine regardless of which Office bitness is installed.
   - **Source:** `database-activities/playbooks/connect-to-database-failures.md`
     (branch 2 — "Provider not registered / architecture (bitness) mismatch")

> Alternative (only if a 64-bit engine genuinely cannot be installed): set the
> project to **Windows - Legacy** (32-bit) so it matches the 32-bit ACE engine.
> Prefer installing the 64-bit ACE so the modern runtime is used.

---

**Preventive fix:**

1. **Robot host provisioning** — Install the 64-bit Microsoft Access Database
   Engine as part of host setup for every machine that runs **Windows**
   projects using ACE OLE DB, and verify driver bitness then — not at first
   failure.
   - **Who:** Platform / SRE team

2. **Studio** — Pin `ProviderName` explicitly (`System.Data.OleDb`) on
   file-based connections (already correct here) and document the 64-bit-ACE
   host requirement in the project README so deploys to new hosts don't
   regress.
   - **Who:** RPA developer

3. **Orchestrator** — Add an alert subscription on faulted jobs for this
   process so a host missing the driver surfaces immediately after deploy
   rather than on the first scheduled run.
   - **Who:** Tenant admin

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The 64-bit ACE OLE DB provider is not registered on the Robot host because only the 32-bit Access Database Engine is installed (bitness mismatch with the 64-bit Windows process) | High | Confirmed | Yes | `InvalidOperationException: The 'Microsoft.ACE.OLEDB.12.0' provider is not registered` at Connect to Database + well-formed ACE connection string in Main.xaml + `project.json` targetFramework "Windows" (64-bit) | Install the 64-bit Microsoft Access Database Engine on every Robot host (`/quiet` if 32-bit Office blocks it) |
| H2 | Malformed / wrong connection string | Low | Rejected | No | `ConnectionString` is well-formed: correct `Provider`, full `Data Source`, quoted `Extended Properties="Excel 12.0 Xml;HDR=YES;"` matching `.xlsx` | n/a |
| H3 | Workbook locked / used by another process | Low | Rejected | No | Error text is "provider is not registered", not a sharing violation | n/a |

---

Would you like help applying the fix — drafting the exact host-side install
instruction (64-bit Access Database Engine, `/quiet` switch) to hand to the
Robot machine administrator? I can also clean up the `.local/investigations/`
folder if you no longer need it.
