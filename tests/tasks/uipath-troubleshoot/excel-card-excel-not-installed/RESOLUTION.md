# Final Resolution

---

**Root Cause:** The workflow uses Classic `Excel Application Scope`,
which is COM-only — it requires Microsoft Excel installed on the
Robot host to acquire the `Excel.Application` COM server. The Robot
host (`MOCK-HOST`) is an unattended deployment with NO Excel
installed: there is no entry under
`HKLM:\Software\Microsoft\Office\*\Excel\InstallRoot`, no `excel.exe`
on PATH or under Program Files, and the COM class registration for
`CLSID {00024500-0000-0000-C000-000000000046}` (Excel.Application)
returns `REGDB_E_CLASSNOTREG`. The scope throws
`UiPath.Excel.BusinessException: Error opening workbook. Make sure
Excel is installed.` at acquisition, before any workbook open.

**What went wrong:** Failing job
`aa111111-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-30T08:00:01.300Z`. The `Excel Application Scope:
invoice-report.xlsm` activity attempted to acquire the Excel COM
server (Classic surface is COM-only — there's no OpenXML fallback
path). The host's COM registry has no Excel.Application class
registration. `CoCreateInstance` returned `0x80040154
REGDB_E_CLASSNOTREG`, which the activity caught and rewrapped as
the canonical `Error opening workbook. Make sure Excel is
installed.` BusinessException.

**Why:** The Classic `Excel Application Scope` activity is built on
COM Interop with `Excel.Application` — there is no alternative
provider. Unlike the Modern `Use Excel File` card (which defaults
to OpenXML and only falls back to COM when COM-forcing properties
are set), Classic ALWAYS needs Excel installed. Deploying a Classic-
scope workflow to a host without Excel is a deployment-environment
mismatch — the workflow was authored on a developer machine with
Excel and shipped to an unattended Robot host that doesn't have it.

The fix branches based on the workflow's actual requirements:
- If Excel features (formula recalc, macros, formatting) ARE needed
  → install or repair Excel on the host.
- If Excel features are NOT needed (the workflow just reads /
  writes data) → migrate to Workbook activities OR Modern `Use
  Excel File` (OpenXML default) instead of Classic scope.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelInvoiceReport` (key `aa111111-...`) — Faulted
  at `2026-05-30T08:00:02.512Z`.
- Folder: `InvoiceReports` (key `f00bbbbb-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: Error opening workbook. Make
  sure Excel is installed.` with inner
  `System.Runtime.InteropServices.COMException (0x80040154):
  Retrieving the COM class factory for component with CLSID
  {00024500-0000-0000-C000-000000000046} failed due to the
  following error: 80040154 Class not registered.` Stack trace
  through
  `UiPath.Excel.Activities.ExcelApplicationScope.AcquireExcelComServer()`
  and `ExcelApplicationScope.OnExecute(NativeActivityContext)`.
- Faulting activity: `ExcelApplicationScope_1`
  (`Excel Application Scope: invoice-report.xlsm`) at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `<uix:ExcelApplicationScope WorkbookPath="C:\Robot\Data\invoice-report.xlsm" Visible="False" AutoSave="True" ...>` —
    this is the **Classic** Excel Application Scope element
    (`<uix:ExcelApplicationScope>`), NOT the Modern `<uix:UseExcelFile>`
    element. Classic is COM-only.
  - Body contains a single `ExcelReadRange` activity. The workflow
    doesn't need macros, formulas, or formatting interaction —
    it just reads data, so the COM dependency is unnecessary for
    its actual purpose.

### Job logs (decisive)
- `Excel Application Scope: invoice-report.xlsm — surface: Classic ExcelApplicationScope (COM-only). Attempting to acquire Excel.Application COM server.`
- `Excel Application Scope: invoice-report.xlsm — CLSID {00024500-0000-0000-C000-000000000046} (Excel.Application) not registered on host. Host: MOCK-HOST. Robot user: UIPATH\AUTOMATION1. Excel install state: NOT INSTALLED (no entry under HKLM:\Software\Microsoft\Office\*\Excel\InstallRoot, no excel.exe on PATH or under Program Files).`
- `Excel Application Scope: invoice-report.xlsm — UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed. Inner: COMException 0x80040154 REGDB_E_CLASSNOTREG (Class not registered).`

The decisive log lines name (a) the surface (Classic, COM-only), (b)
the host's install state (NOT INSTALLED with the specific registry
and filesystem evidence), and (c) the canonical COM error
(REGDB_E_CLASSNOTREG = Excel.Application class isn't registered).
Three pieces together pin the failure to branch 1 unambiguously.

### Cross-check — what this is NOT
- Not branch 2 (empty / illegal WorkbookPath): the path is a
  well-formed absolute path; the BusinessException is about Excel
  installation, not path validity.
- Not branch 3 (COM/RPC across scopes): only ONE scope in the
  workflow; no race condition possible.
- Not branch 4 (child activity outside scope): the Read Range is
  correctly nested inside the scope. The scope itself fails before
  any child runs.
- Not branch 5 (sensitivity label): no `BusinessException` /
  `COMException` referencing sensitivity / Purview / AIP; the
  failure is at COM acquisition, before any workbook-content
  inspection.

---

**Recommended Fix (Resolution):**

The fix branches based on whether the workflow actually needs
Excel COM features. Walk through the options in order.

### Primary fix (workflow doesn't need Excel features) — migrate to Workbook activities or Modern card

The workflow reads invoice data with no formula evaluation, no
macros, no formatting interaction. It doesn't NEED Excel COM. The
cheapest fix is to remove the COM dependency entirely:

**Option A — Workbook activities (zero Excel dependency):**
1. Open `Main.xaml`.
2. Replace `<uix:ExcelApplicationScope>` and the nested `Read Range`
   with the standalone `Read Range Workbook` activity (toolbox:
   System → File → Workbook → Read Range).
3. Configure the Workbook activity with the same WorkbookPath,
   SheetName, and Range.
4. Save and re-run. The Workbook surface uses OpenXML directly —
   no Excel needed on the host.

**Option B — Modern `Use Excel File` (OpenXML default):**
1. Replace `<uix:ExcelApplicationScope>` with `<uix:UseExcelFile>`
   (Modern). Configure WorkbookPath on the scope.
2. Keep the nested Read Range activity — but switch it from the
   Classic `ExcelReadRange` to the Modern `ExcelReadRange` (the
   Modern variant inside `Use Excel File`).
3. Audit the Modern card for COM-forcing properties (`Read
   Formatting`, `Edit Password`, `Visible: True`, etc.). If any
   are set, REMOVE them — they force OpenXML→COM fallback and
   reintroduce the install requirement.

Both options eliminate the Excel install requirement for this
workflow. Option A is the simplest if Workbook surface meets the
workflow's needs.

### Primary fix (workflow DOES need Excel features) — install or repair Excel on the host

If the workflow legitimately needs Excel COM (formula recalc, macro
invocation, COM-specific formatting interaction), the host MUST
have Excel installed:

**Path 1 — Repair the existing install:**
1. UiPath Studio → Tools → "Repair Tool for Microsoft Office".
   Lightweight; re-registers Excel COM components.

**Path 2 — Office Online Repair:**
1. Windows Control Panel → Programs and Features → Microsoft Office
   → Change → Online Repair.
2. Heavier; addresses registry corruption from interrupted
   installs / upgrades. Requires admin rights on the Robot host.

**Path 3 — Fresh Excel install:**
1. Install Microsoft 365 / Office 2019/2021 on the Robot host
   under the Robot user's profile.
2. Activate the license (Robot user must have a valid Microsoft
   365 / Office license assigned).
3. Re-run the workflow.

### Anti-pattern (do NOT use)

Do NOT set `Visible: True` on the Excel Application Scope as a
diagnostic step. On unattended Robot hosts the desktop session
often isn't rendered; the property has no effect on the COM
acquisition. Worse, on Modern `Use Excel File` cards, `Visible:
True` is a COM-forcing property that turns an otherwise-OpenXML
workflow into a COM workflow — reintroducing the Excel-install
requirement that's currently the root cause. This is the playbook's
anti-pattern #3.

### Prevention

- For Robot hosts without Excel installed, prefer the Workbook
  surface (`Read Range Workbook`, `Write Range Workbook`, etc.)
  for any workflow that doesn't need COM features.
- For workflows on Modern `Use Excel File`, audit the card's
  properties at design time. Document which properties force COM
  (`Read Formatting`, `Edit Password`, certain `Visible`/`AutoSave`
  combinations) so future contributors don't accidentally
  reintroduce the COM dependency.
- When deploying to a new host, run a smoke-test workflow that
  exercises the Excel acquisition path before scheduling production
  jobs. The smoke test catches Excel-install issues before they
  affect business workflows.
- For host-provisioning runbooks: document the Excel install
  requirement explicitly for any team that runs Classic
  `Excel Application Scope` workflows. The "install Excel"
  prerequisite is easy to overlook when migrating workflows from
  developer machines (where Excel is present) to unattended Robot
  hosts (where it often isn't).
