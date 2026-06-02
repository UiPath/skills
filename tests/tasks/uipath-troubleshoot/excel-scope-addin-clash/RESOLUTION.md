# Final Resolution

---

**Root Cause:** The Classic `Excel Application Scope` instantiates an
`Excel.Application` COM object, but a **COM add-in loaded into that
Excel instance corrupts the interop interface negotiation**, so the
`QueryInterface` for `Microsoft.Office.Interop.Excel._Application`
(IID `{000208D5-0000-0000-C000-000000000046}`) returns
`0x80004002 E_NOINTERFACE`. The marshaled `System.__ComObject` can't be
cast to the expected interop interface and the scope throws
`System.InvalidCastException: Unable to cast COM object of type
'System.__ComObject' to interface type
'Microsoft.Office.Interop.Excel._Application'`. The offending add-in is
`UiPath.Integration.ExcelAddin` — the Studio **design-time** Excel
Add-in — which is registered (`LoadBehavior=3`, HKLM) on this **runtime**
Robot host where it shouldn't be. (A third-party add-in,
`AcmeBudgetTools.Connect`, is also loaded.) The decisive diagnostic:
launching `excel.exe /safe` (all add-ins disabled) on the host succeeds
and a manual COM bind to `_Application` works.

**What went wrong:** Failing job
`gg666666-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-30T07:30:01.500Z`. The `Excel Application Scope:
recon-daily.xlsx` activity created the `Excel.Application` object;
during interface binding, the loaded COM add-ins corrupted the
QueryInterface result and the cast to `_Application` failed with
`E_NOINTERFACE`.

**Why:** When the scope launches `EXCEL.EXE`, Excel auto-loads every
registered COM add-in with `LoadBehavior=3`. A misbehaving add-in can
interfere with the interop proxy so the QueryInterface for the Excel
interop interface fails. The `UiPath.Integration.ExcelAddin` is meant
for design-time recording in Studio, not for runtime Robot hosts — it
should not be loaded where unattended jobs drive Excel via COM.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelReconExport` (key `gg666666-...`) — Faulted at
  `2026-05-30T07:30:02.640Z`.
- Folder: `ReconReports` (key `f0066666-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.InvalidCastException: Unable to cast COM object of type
  'System.__ComObject' to interface type
  'Microsoft.Office.Interop.Excel._Application'. This operation failed
  because the QueryInterface call on the COM component for the interface
  with IID '{000208D5-0000-0000-C000-000000000046}' failed due to the
  following error: No such interface supported (Exception from HRESULT:
  0x80004002 (E_NOINTERFACE)).` Stack through
  `UiPath.Excel.Activities.ExcelApplicationScope.AcquireExcelComServer()`.
- Faulting activity: `ExcelApplicationScope_1`
  (`Excel Application Scope: recon-daily.xlsx`) at `Main.xaml`.

### Job logs (decisive)
- `Excel Application Scope: recon-daily.xlsx — surface: Classic ExcelApplicationScope (COM-only). Attempting to acquire Excel.Application COM server.`
- `Excel Application Scope: recon-daily.xlsx — Excel.Application object instantiated, but QueryInterface for Microsoft.Office.Interop.Excel._Application (IID {000208D5-...}) returned E_NOINTERFACE. ... Excel install state: INSTALLED (Microsoft 365 Apps, launches interactively). COM add-ins auto-loaded into this Excel instance at startup: 'UiPath.Integration.ExcelAddin' (LoadBehavior=3, HKLM — the Studio design-time Excel Add-in, present on this runtime host) and 'AcmeBudgetTools.Connect' (LoadBehavior=3). Diagnostic: launching 'excel.exe /safe' (all add-ins disabled) on the host succeeds and a manual COM bind to _Application works.`
- `Excel Application Scope: recon-daily.xlsx — System.InvalidCastException: ... QueryInterface for IID {000208D5-...} failed: 0x80004002 E_NOINTERFACE (No such interface supported).`

The decisive evidence: the inner HRESULT is `E_NOINTERFACE` inside an
`InvalidCastException` on `System.__ComObject` (an interface-cast fault,
not a registration or lock fault); the logs enumerate the loaded COM
add-ins (including the misplaced `UiPath.Integration.ExcelAddin`); and
`excel.exe /safe` succeeds, proving an add-in is the culprit.

### Workflow source
- `Main.xaml` uses a SINGLE Classic `<uix:ExcelApplicationScope>`
  wrapping a `Read Range`. Nothing in the workflow logic is at fault.
- `project.json`: `UiPath.Excel.Activities` `[2.24.7]`.

### Cross-check — what this is NOT
- NOT "Excel not installed" / registration corruption: Excel is
  installed and launches; the inner HRESULT is `E_NOINTERFACE`
  (interface cast), not `REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED`.
  Also, `excel.exe /safe` succeeds — the COM stack is healthy without
  add-ins.
- NOT a workbook lock ("Failed opening the Excel file…"): the failure
  is at COM interface binding, before any file open; no lock holder.
- NOT a multi-scope RPC race: only one scope.

---

**Recommended Fix (Resolution):**

This maps to branch 3 (COM add-in interface clash) of
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`.

### Primary fix — disable the offending COM add-in

**Path 1 — via the Excel UI:**
1. On the host, open Excel manually → File → Options → Add-ins.
2. Set the **Manage** dropdown to **COM Add-ins** → **Go**.
3. Uncheck `UiPath.Integration.ExcelAddin` (and the suspect
   `AcmeBudgetTools.Connect` if needed) → OK.
4. Re-run the automation.

**Path 2 — via the registry (for unattended provisioning):**
1. Set `LoadBehavior` to `0` under
   `HKLM:\Software\Microsoft\Office\Excel\Addins\UiPath.Integration.ExcelAddin`
   (and the `HKCU` hive for the Robot user). This stops the add-in from
   loading at Excel startup across jobs without manual UI steps — bake
   it into the host-provisioning runbook.

**Confirm the fix:** launch `excel.exe /safe`, verify a manual COM
open works, then re-run the job with the add-in disabled.

### If a clashing add-in must stay loaded
Isolate Excel automation to a host without it, or migrate the workflow
to the Workbook surface (no `EXCEL.EXE`, so no add-in loads at all) if
it doesn't need Excel COM features.

### Anti-patterns (do NOT use)
- Do NOT conclude "Excel isn't installed" — it is, and `excel.exe
  /safe` proves the COM stack is healthy.
- Do NOT add a `Delay` — the add-in loads identically on the next run.
- Do NOT wrap the scope in a bare `Try Catch` that continues — the
  recon export would run on missing data.

### Prevention
- Strip the Studio Excel Add-in from runtime Robot hosts
  (`LoadBehavior=0` or don't install it); it's a design-time tool.
- Vet third-party Excel COM add-ins on Robot hosts; each one loads into
  every `Excel Application Scope` and can break interop.
- For workflows that don't need Excel features, prefer the Workbook
  surface so no add-ins load at all.
