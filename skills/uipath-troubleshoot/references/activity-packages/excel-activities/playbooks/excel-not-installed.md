---
confidence: high
---

# Excel Not Installed / Interop Unavailable

## Context

An Excel activity or scope requires the Microsoft Excel COM server, but the Robot host has no registered desktop Excel installation. The failure occurs while acquiring `Excel.Application`, before the workbook, sheet, range, or lookup operation runs.

What this looks like:

- Raw Interop signatures: `Excel is not installed`, `Could not load file or assembly 'Microsoft.Office.Interop.Excel'`, `Retrieving the COM class factory for component with CLSID {00024500-0000-0000-C000-000000000046} failed`, `80040154 (REGDB_E_CLASSNOTREG)`, or `Cannot create an instance of Microsoft.Office.Interop.Excel.ApplicationClass`.
- Wrapped scope/card signature: `UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed.` with an inner `COMException 0x80040154 REGDB_E_CLASSNOTREG`.
- The job faults synchronously when the activity or its container tries to launch Excel. No sheet name, range address, cell value, or workbook-content error appears because content processing never starts.

Per-activity discriminators:

| Faulted surface | Why COM is required | Typical wrapper | Activity-specific resolution |
|---|---|---|---|
| Classic activity such as `ExcelLookUpRange`, inside `Excel Application Scope` | Classic Excel activities are COM-only | Raw Interop class-factory error or the scope's wrapped `BusinessException` | If the operation is lookup-only, use Workbook `Read Range` + `Lookup Data Table`; otherwise use the corresponding Workbook activity when it supports the operation |
| Classic `Excel Application Scope` | The container is COM-only, regardless of its children | `BusinessException: Error opening workbook. Make sure Excel is installed.` with inner `0x80040154` | Install desktop Excel when COM features are required; otherwise migrate the children to Workbook activities or a Modern OpenXML card |
| Modern `Use Excel File` / `ExcelApplicationCard` | A COM-forcing property (`Read Formatting`, `Edit Password`, `Visible`, or some `Auto Save` combinations) or a legacy `.xls` / `.xlsb` file selected COM instead of OpenXML | Wrapped `BusinessException`, often with inner `0x80040154` | Remove the unnecessary COM-forcing property or convert the file to `.xlsx`; install Excel only when the workflow truly needs COM-only behavior |
| Workbook activity (`Read Range Workbook`, `Write Range Workbook`, `Append Range Workbook`) | It does not require COM for `.xlsx` OpenXML workbooks | An Excel-install signature does not fit this surface | Re-route: verify the actual faulting activity or enclosing scope; do not diagnose missing Excel from a Workbook activity alone |

What can cause it:

1. **Desktop Excel is not installed on the Robot host** - common on a newly provisioned unattended VM, Linux Robot, container, or locked-down image. Web/online Excel does not register the local `Excel.Application` COM class.
2. **The workflow unnecessarily selected a COM-dependent surface** - a Classic scope/activity was used for a data-only operation, or a Modern card enabled a COM-forcing property even though OpenXML would be sufficient. The host gap is real; the activity discriminator determines whether to install Excel or remove the dependency.

NOT for a host where desktop Excel is present but COM registration, bitness, DCOM activation, add-ins, or first-launch state prevents acquisition. That is [excel-application-scope-failures.md](./excel-application-scope-failures.md). `REGDB_E_CLASSNOTREG` without host install-state evidence leaves both missing installation and broken registration viable; verify the host before choosing.

## Investigation

1. **Capture the runtime signature and faulted surface.** From `uip or jobs get <job-key> --output json` and the workflow source, record the exact exception/inner exception, activity class, enclosing scope/card, file extension, and package version. Confirm the failure occurs at COM acquisition rather than after workbook processing begins.

2. **Apply the activity discriminator.** Classic `Excel Application Scope` and its Classic child activities are always COM-dependent. For Modern `Use Excel File`, inspect `Read Formatting`, `Edit Password`, `Visible`, `Auto Save`, and the workbook extension to identify what forced COM. A standalone Workbook activity does not fit this playbook.

3. **Verify the host's install state.** On the failing Robot host, as the Robot user or an administrator, check both:

   ```powershell
   Get-ItemProperty 'HKLM:\Software\Microsoft\Office\*\Excel\InstallRoot' -ErrorAction SilentlyContinue
   Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe' -ErrorAction SilentlyContinue
   ```

   Also verify whether `excel.exe` exists under the installed Office directory. No registry entry and no executable confirms branch 1. If Excel is present, stop and use [excel-application-scope-failures.md](./excel-application-scope-failures.md) to diagnose registration or activation instead.

4. **Confirm the deployment fork.** Determine whether the workflow needs formula recalculation, macros, interactive formatting, or another COM-only feature. If not, the source chose an avoidable COM dependency; use the matching row in the discriminator table. If it does, the host must provide a licensed desktop Excel installation.

The root cause is confirmed only when runtime evidence identifies COM acquisition and host evidence shows that desktop Excel is absent. Name both the faulted activity/scope and the property or surface choice that made COM necessary.

## Resolution

- **If COM features are required:** install Microsoft Excel (or the full Microsoft 365 / Office desktop suite) on the execution machine under a license the Robot's Windows user can activate, then re-run. Web/online Excel does not satisfy Interop.
- **If the workflow only reads or writes tabular `.xlsx` data:** remove the COM dependency using the activity-specific discriminator:
  - Classic `Lookup Range` -> Workbook `Read Range` into a `DataTable`, then `Lookup Data Table`.
  - Other Classic read/write activities -> their Workbook equivalents where supported.
  - Classic scope around data-only Modern-compatible children -> Modern `Use Excel File` with no COM-forcing properties, or standalone Workbook activities.
  - Modern card -> remove unnecessary COM-forcing properties and convert `.xls` / `.xlsb` to `.xlsx` when acceptable.
- **If Excel is already installed:** do not reinstall blindly. Use [excel-application-scope-failures.md](./excel-application-scope-failures.md) to distinguish broken registration, DCOM/identity issues, add-in interference, bitness mismatch, and first-launch state.

## Prevention

- Record the Excel desktop prerequisite in Robot-host provisioning for every process that intentionally uses COM.
- Prefer Workbook activities for data-only `.xlsx` automation and audit Modern cards for accidental COM-forcing properties before deployment.
- Smoke-test the Excel acquisition path when moving a workflow from a developer workstation to a new unattended host.

## Related

- [excel-application-card-failures.md](./excel-application-card-failures.md) - the remaining path, RPC lifecycle, child-placement, and sensitivity-label failures on the card/scope surface.
- [excel-application-scope-failures.md](./excel-application-scope-failures.md) - Excel is installed but Classic COM acquisition still fails.
- [../overview.md](../overview.md) - Excel provider and scope model.
