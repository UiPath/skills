---
confidence: high
---

# Lookup Range — Excel Is Not Installed / Activity Fails to Initialize

## Context

What this looks like:
- Activity `Lookup Range` (classic `UiPath.Excel.Activities.ExcelLookUpRange`) faults at initialization, before it reads any cell
- Error message contains one of: `Excel is not installed`, `Could not load file or assembly 'Microsoft.Office.Interop.Excel'`, `Retrieving the COM class factory for component with CLSID {00024500-0000-0000-C000-000000000046} failed`, `80040154 (REGDB_E_CLASSNOTREG)`, or `Cannot create an instance of Microsoft.Office.Interop.Excel.ApplicationClass`
- The job faults synchronously the moment the activity (or its surrounding `Excel Application Scope`) tries to launch Excel

What can cause it:
- The classic `Lookup Range` activity drives the **Microsoft Excel Interop API** — it launches a real Excel.exe via COM. If Microsoft Excel is not installed on the execution machine (a Linux robot, a stripped-down VM, a container image, or a freshly-provisioned unattended host), the COM class factory for `Excel.Application` cannot be created and the activity faults at startup. This is the only cause of the `REGDB_E_CLASSNOTREG` / `Excel is not installed` signature — Interop cannot run without a registered Excel installation.

Notes:
- Classic `Lookup Range` (`UiPath.Excel.Activities.ExcelLookUpRange`) and any other classic Excel activity inside an `Excel Application Scope` share this dependency. The modern `Lookup Range` (`LookUpRangeX`) inside a `Use Excel File` / `Excel Process Scope` *also* requires Excel installed for most operations.
- The **Workbook** family of activities (`Read Range` under `Workbook`, not under a scope) reads `.xlsx` via OpenXML and does **not** require Excel — that is the migration target below.

## Investigation

1. Read the faulted activity from the workflow `.xaml` and confirm it is a `Lookup Range` (classic `ExcelLookUpRange` or modern `LookUpRangeX`) inside an `Excel Application Scope` / `Use Excel File` container.
2. Confirm whether Microsoft Excel is installed on the execution machine. Ask the user (or someone with access to the robot host) to check `Control Panel > Programs and Features` for a Microsoft Office / Microsoft 365 entry, or run `Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe` in PowerShell as the robot's Windows user.
3. Confirm the robot type. Linux robots and many cloud/container unattended hosts have no Excel and cannot run Interop-based activities at all.

## Resolution

- **If Excel can be installed on the host** — install Microsoft Excel (or the full Office / Microsoft 365 desktop suite) on the execution machine under a license the robot's Windows user can activate, then re-run. Interop requires a registered desktop Excel; web/online Excel does not satisfy it.
- **If Excel cannot be installed** (Linux robot, locked-down VM, container) — re-architect the workflow to avoid Interop:
  1. Replace the `Lookup Range` + `Excel Application Scope` with the **Workbook** `Read Range` activity (the one under the `Workbook` category, not inside a scope). It reads `.xlsx` through OpenXML with no Excel dependency.
  2. Output the sheet into a `DataTable` variable.
  3. Search the `DataTable` with the **Lookup Data Table** activity (returns the matching row index and/or a target-column cell value), which is the OpenXML-friendly equivalent of `Lookup Range`.
  - **Source:** this is the documented migration path when Excel is unavailable; the classic Interop activity has no in-place workaround on an Excel-less host.

> The modern `Use Excel File` surface still launches Excel for most write/format/macro operations, so migrating from classic `Excel Application Scope` to `Use Excel File` does **not** remove the Excel dependency. Only the `Workbook` (OpenXML) activities are truly Excel-free.
