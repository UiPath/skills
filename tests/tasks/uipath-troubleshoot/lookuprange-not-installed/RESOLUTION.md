# Final Resolution

---

**Root Cause:** The classic `Lookup Range` activity in `Main.xaml` runs
inside an `Excel Application Scope`, which drives the Microsoft Excel
Interop API. The new unattended robot host (MOCK-HOST) does not have
Microsoft Excel installed, so the `Excel.Application` COM class cannot
be created and the scope faults at startup with
`REGDB_E_CLASSNOTREG` (0x80040154) before any cell is read.

**What went wrong:** The `VendorLookup` job (started
2026-05-27T08:30:04Z) faulted ~2 seconds after launch when its
`Excel Application Scope` tried to start Excel. The runtime error was
`Retrieving the COM class factory for component with CLSID
{00024500-0000-0000-C000-000000000046} failed due to the following
error: 80040154 Class not registered (REGDB_E_CLASSNOTREG)`. The
process ran successfully on the developer machine (which has Excel)
and only began faulting after it was moved to the new unattended
robot - corroborating a host-environment cause rather than a workflow
defect.

**Why:** Classic Excel activities (`Excel Application Scope`,
`Lookup Range`, `Read Range`, etc.) launch a real Excel.exe through
COM Interop. COM cannot instantiate `Excel.Application` unless a
registered desktop Excel installation is present on the machine and
reachable by the robot's Windows user. Web/online Excel does not
satisfy Interop. On a fresh unattended VM, Linux robot, or container
with no Office installed, every classic Excel activity faults at
startup with `REGDB_E_CLASSNOTREG`.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: VendorLookup -- Faulted at 2026-05-27T08:30:06.140Z (ran for ~2.1 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `Retrieving the COM class factory for component with CLSID {00024500-0000-0000-C000-000000000046} failed ... 0x80040154 (REGDB_E_CLASSNOTREG)` -> `Main.xaml` -> `ExcelApplicationScope "Excel Application Scope"` -> `Sequence "Main Sequence"`

### Excel Activities (Root Cause)
- Activity surface: classic `UiPath.Excel.Activities.LookUpRange` inside `UiPath.Excel.Activities.ExcelApplicationScope` (Interop / COM)
- CLSID `{00024500-0000-0000-C000-000000000046}` is `Excel.Application` - the class COM could not register because Excel is not installed on MOCK-HOST.
- The fault is at scope startup (the `Lookup Range` body never executes), which is the signature of a missing Excel install rather than a sheet/range or lookup-value problem.

---

**Immediate fix:**

The agent could not confirm the host's Excel install from Orchestrator
alone. The cause is unambiguous from the HRESULT, but the remediation
depends on whether Excel can be installed on the robot host. Hand the
user both paths and one host check.

### Host check (RPA Production / MOCK-HOST, as the robot's Windows user)
1. Confirm whether Microsoft Excel (desktop) is installed:
   `Control Panel > Programs and Features` (look for Microsoft Office /
   Microsoft 365), or run
   `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe'`
   in PowerShell. Expect it to be **absent** - that confirms the cause.

### Fix path A -- install Excel (preferred if the host supports it)
- Install Microsoft Excel (or the full Office / Microsoft 365 desktop
  suite) on MOCK-HOST under a license the robot's Windows user can
  activate, then re-run. Interop requires a registered desktop Excel;
  online/web Excel does not satisfy it.
- **Source:** `excel-activities/playbooks/lookup-range-excel-not-installed.md`

### Fix path B -- migrate off Interop (if Excel cannot be installed)
- If MOCK-HOST is a Linux robot, container, or locked-down VM where
  Excel cannot be installed, re-architect the workflow:
  1. Replace the `Excel Application Scope` + `Lookup Range` with the
     **Workbook** `Read Range` activity (under the `Workbook` category,
     not inside a scope) - it reads `.xlsx` via OpenXML with no Excel
     dependency.
  2. Output the sheet into a `DataTable`.
  3. Search it with the **Lookup Data Table** activity, the
     OpenXML-friendly equivalent of `Lookup Range`.
- **Source:** same playbook, "If Excel cannot be installed" branch.

> Note: migrating from classic `Excel Application Scope` to the modern
> `Use Excel File` surface does NOT remove the Excel dependency - the
> modern surface still launches Excel for most operations. Only the
> Workbook (OpenXML) activities are truly Excel-free.

---

**Preventive fix:**

1. **Robot host provisioning** -- standardize the unattended robot image
   to include desktop Excel if any process in the portfolio uses classic
   or modern Excel-scope activities.
   - **Why:** "Works on dev, fails on the robot" is a recurring class of
     failure when the robot image diverges from developer machines.
   - **Who:** Platform / robot host team.

2. **Studio** -- for processes that only read tabular data, prefer the
   Workbook (OpenXML) activities over Excel-scope activities so they run
   on any host regardless of Excel availability.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Microsoft Excel is not installed on the unattended robot host; classic Excel Application Scope cannot create the Excel.Application COM object | High | Confirmed | Yes | `REGDB_E_CLASSNOTREG` on CLSID for `Excel.Application` at scope startup + "worked on dev, broke after move to new robot" | Install Excel on the host, OR migrate to Workbook Read Range + Lookup Data Table |

---

Would you like help converting the workflow to the Workbook Read Range +
Lookup Data Table path so it runs without Excel, or cleaning up the
`.local/investigations/` folder?
