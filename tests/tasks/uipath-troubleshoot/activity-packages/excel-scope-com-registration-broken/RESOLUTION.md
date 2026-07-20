# Final Resolution

---

**Root Cause:** The workflow uses Classic `Excel Application Scope`,
which is COM-only. Microsoft Excel **is installed** on the Robot host
(`MOCK-HOST`) — Microsoft 365 Apps build 16.0.17928.20114 at
`C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE`, and it
launches interactively — but the `Excel.Application` COM **type-library
registration is broken**. The host was upgraded in place to Microsoft
365 Apps on 2026-05-28 (previously Office 2019 Standard 16.0.10396);
the upgrade left a stale `TypeLib` registration for
`{00020813-0000-0000-C000-000000000046}` (the Microsoft Excel Object
Library) pointing at the removed 2019 build. The COM class factory
creates the `Excel.Application` object, but resolving the
`Microsoft.Office.Interop.Excel` type library fails with
`0x8002801D TYPE_E_LIBNOTREGISTERED` ("Library not registered"). The
scope catches this COM error and rewraps it as the generic
`UiPath.Excel.BusinessException: Error opening workbook. Make sure
Excel is installed.`

> **This is NOT the "Excel not installed" case.** The message says
> "Make sure Excel is installed", but Excel is present and runnable.
> The decisive evidence is the inner HRESULT (`TYPE_E_LIBNOTREGISTERED`,
> not `REGDB_E_CLASSNOTREG`-because-absent), the logged INSTALLED state
> with a concrete build path, and the recent in-place Office upgrade.
> The fix is to repair the COM/type-library registration — NOT to
> install Excel (it is already installed).

**What went wrong:** Failing job
`aa444444-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-30T09:15:02.110Z`. The `Excel Application Scope:
ledger-2026-05.xlsm` activity acquired the `Excel.Application` COM
class factory, but the interop type-library resolution failed because
the upgrade orphaned the Excel Object Library `TypeLib` keys. The
activity surfaced the canonical "Make sure Excel is installed."
BusinessException with inner `COMException 0x8002801D
TYPE_E_LIBNOTREGISTERED`.

**Why:** An in-place Office major-version upgrade (2019 → Microsoft
365 Apps) rewrites the click-to-run install but can leave stale
COM/`TypeLib` registry entries from the previous build. COM activation
of `Excel.Application` then half-succeeds (class factory) and fails at
type-library binding. Because the workflow ran fine before the
upgrade, the deployment didn't change — the host's COM registration
did.

The fix is to re-register Excel's COM components on the host. It does
NOT branch on "needs COM features vs. doesn't" the way the
Excel-not-installed case does — the registration must be repaired
regardless (or the workflow migrated off COM entirely if Excel
features aren't needed).

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelLedgerReport` (key `aa444444-...`) — Faulted at
  `2026-05-30T09:15:03.402Z`.
- Folder: `LedgerReports` (key `f00eeeee-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: Error opening workbook. Make sure
  Excel is installed.` with inner
  `System.Runtime.InteropServices.COMException (0x8002801D): Library
  not registered. (Exception from HRESULT: 0x8002801D
  (TYPE_E_LIBNOTREGISTERED))`. Stack through
  `UiPath.Excel.Activities.ExcelApplicationScope.AcquireExcelComServer()`.
- Faulting activity: `ExcelApplicationScope_1`
  (`Excel Application Scope: ledger-2026-05.xlsm`) at `Main.xaml`.

### Job logs (decisive)
- `Excel Application Scope: ledger-2026-05.xlsm — surface: Classic ExcelApplicationScope (COM-only). Attempting to acquire Excel.Application COM server.`
- `Excel Application Scope: ledger-2026-05.xlsm — Excel.Application class factory created, but Microsoft.Office.Interop.Excel type-library resolution FAILED. ... Excel install state: INSTALLED — Microsoft 365 Apps build 16.0.17928.20114 at C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE (launches interactively). Office was upgraded in place to Microsoft 365 Apps on 2026-05-28 (previous build: Office 2019 Standard 16.0.10396). Stale TypeLib registration detected for {00020813-0000-0000-C000-000000000046} (Microsoft Excel Object Library) pointing at the removed 2019 build.`
- `Excel Application Scope: ledger-2026-05.xlsm — UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed. Inner: COMException 0x8002801D TYPE_E_LIBNOTREGISTERED (Library not registered).`

The decisive triad: (a) surface is Classic (COM-only), (b) Excel is
INSTALLED (concrete build path, launches interactively) — so this is
NOT not-installed, and (c) inner HRESULT is `TYPE_E_LIBNOTREGISTERED`
with a recent in-place Office upgrade and a stale `TypeLib` key → COM
registration corruption.

### Workflow source
- `Main.xaml` uses `<uix:ExcelApplicationScope>` (Classic, COM-only),
  a SINGLE scope (no multi-scope race), wrapping a `Read Range`.
- `project.json`: `UiPath.Excel.Activities` `[2.24.7]`.

### Cross-check — what this is NOT
- NOT "Excel not installed" (the `excel-application-card-failures.md`
  branch 1 / the `excel-card-excel-not-installed` scenario): Excel is
  present and launches. Recommending "install Excel" is wrong here.
- NOT a workbook lock ("Failed opening the Excel file…"): the failure
  is at COM server acquisition, before any file open.
- NOT a COM add-in clash (`InvalidCastException` / `E_NOINTERFACE`):
  the inner HRESULT is `TYPE_E_LIBNOTREGISTERED`, a registration
  fault, not an interface-cast fault.
- NOT a multi-scope RPC race: only one scope in the workflow.

---

**Recommended Fix (Resolution):**

This maps to branch 1 (COM registration corruption) of
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`.

### Primary fix — repair Excel's COM / type-library registration

**Path 1 — Office Online Repair (canonical):**
1. On the Robot host: Windows Settings → Apps → Installed Apps →
   Microsoft 365 Apps → Modify → **Online Repair**.
2. This re-registers the Excel COM classes and type libraries from the
   current build and clears the stale 2019 `TypeLib` entries. Requires
   admin rights on the host.
3. Re-run the job.

**Path 2 — UiPath "Repair Tool for Microsoft Office":**
1. UiPath Studio → Tools → "Repair Tool for Microsoft Office".
2. Lighter than Online Repair; re-registers the Excel interop
   components. Try first if admin rights for Online Repair aren't
   available.

**Path 3 — Targeted TypeLib cleanup (only if repair doesn't resolve it):**
1. **Back up the registry key first.**
2. In `regedit`, under `HKCR\TypeLib\{00020813-0000-0000-C000-000000000046}`,
   ensure the version subkeys point to the current Microsoft 365 build's
   Excel type library and remove orphaned subkeys referencing the
   removed 2019 build.
3. Prefer Online Repair, which does this safely and completely.

### Alternative — drop the COM dependency

If the workflow doesn't actually need Excel COM features (formula
recalc, macros, formatting interaction), migrate off the Classic scope
to Workbook activities or a Modern OpenXML `Use Excel File` card (see
`excel-application-card-failures.md` branch 1 resolution). This
sidesteps the COM-registration surface entirely. (Note: this ledger
workflow recalculates the ledger, which may need Excel's formula
engine — confirm before choosing this path.)

### Anti-patterns (do NOT use)
- Do NOT recommend "install Excel" — it is already installed.
- Do NOT add a `Delay` before the scope — the registration is broken
  identically a few seconds later.
- Do NOT do a full Office uninstall/reinstall as the first move —
  Online Repair re-registers COM without the downtime.

### Prevention
- Route Office upgrades on Robot hosts through a change process that
  runs an Excel-COM smoke test after every Office update; in-place
  major-version upgrades are a known source of stale COM/TypeLib
  registration.
- For workflows that don't need Excel features, prefer the Workbook
  surface so an Office upgrade can't break them.
