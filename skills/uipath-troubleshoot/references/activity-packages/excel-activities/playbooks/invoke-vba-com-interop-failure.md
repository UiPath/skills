---
confidence: medium
---

# Invoke VBA — COM Interop Failure (0x80010100 and related HRESULTs)

## Context

What this looks like:
- Activity `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) — or another activity inside the surrounding `Excel Process Scope` — faults with an HRESULT from the COM layer
- Error message contains one of:
  - `The system call failed. (Exception from HRESULT: 0x80010100 (RPC_E_SYS_CALL_FAILED))`
  - `Call was rejected by callee. (Exception from HRESULT: 0x80010001 (RPC_E_CALL_REJECTED))`
  - `The message filter indicated that the application is busy. (Exception from HRESULT: 0x8001010A (RPC_E_SERVERCALL_RETRYLATER))`
  - `Retrieving the COM class factory for component with CLSID {...} failed due to the following error: 80080005`
  - `The remote procedure call failed. (Exception from HRESULT: 0x800706BE)`
- Failures are often intermittent — the same workflow succeeds on one run and faults on the next
- The job may have been running for some time before this activity faulted (Excel was in a degraded state before the macro tried to execute)

What can cause it (more than one may apply):
- **Excel busy with a modal dialog** — Excel.exe is foregrounded on a license activation prompt, a "recover unsaved files" banner, a macro-warning bar, a "trust this file" prompt, or a "this file came from the internet" Protected View bar. COM calls into Excel are blocked until the dialog is dismissed. If `Excel Process Scope` was opened with `Visible = False` (the default for unattended), the dialog is invisible to whoever is watching the robot but still blocks the macro.
- **Excel.exe hung or unresponsive** — a previous run left Excel.exe orphaned (e.g., the workflow crashed without closing the scope), and the new run's COM call lands on the wedged process.
- **Multiple Office versions installed** — the host has both Microsoft 365 Apps and a perpetual Office install (2016/2019/2021), or both click-to-run and MSI installs. The COM dispatcher cannot deterministically resolve which Excel is the target, leading to intermittent `0x80010100` / `0x80080005` errors.
- **Bitness mismatch** — the installed Office is 32-bit but the robot process is 64-bit (or vice versa). COM interop will sometimes succeed (in-proc translation) and sometimes fault (cross-bitness marshaling), depending on which APIs the activity hits.
- **Resource contention on the host** — Excel was launched concurrently by a user, another robot, or a scheduled task while the macro was running, causing the COM server to drop the active call.

## Investigation

1. Read the error message and HRESULT code from job evidence. Capture the exact HRESULT — `0x80010100`, `0x80010001`, etc. — and the activity that faulted.
2. Confirm the faulted activity is inside an `Excel Process Scope` and read the scope's `Visible` property from the workflow `.xaml`. If `Visible = False`, modal dialogs are invisible during the run.
3. Ask the user (or someone with desktop access to the robot machine, signed in as the robot's Windows user) to:
   - Re-run the workflow with the `Excel Process Scope`'s `Visible` set to `True`.
   - Observe Excel during the run. Note any dialog, banner, or prompt that appears: license activation, recover unsaved files, macro warning, Protected View, file lock notice, trust-this-file prompt.
4. Check the robot machine for orphaned Excel processes before the next run (Task Manager → look for `EXCEL.EXE` instances with no visible window).
5. Capture the Office installation inventory on the robot machine: number of Office installs, edition (Microsoft 365 / Office 2019 / Office 2021), install channel (click-to-run vs. MSI), and bitness (32-bit vs. 64-bit). The bitness is shown under `File > Account > About Excel`.

## Resolution

- **If a modal dialog was blocking** — dismiss the dialog source before the macro runs. Options:
  - **Recover unsaved files / yellow Protected View bar:** open the workbook once interactively on the robot machine, dismiss the prompt, save and close cleanly so the recovery state is cleared.
  - **License activation prompt:** complete Office activation on the robot machine under the Windows user the robot runs as.
  - **Macro-warning bar / "trust this file" prompt:** add the workbook's folder to Excel Trusted Locations (`File > Options > Trust Center > Trust Center Settings > Trusted Locations`), or sign the macro with a certificate the host trusts.
  - **File from the internet / Mark-of-the-Web:** unblock the file (`Right-click > Properties > Unblock`) or pre-process it with `Unblock-File <path>` in PowerShell before the workflow runs.
- **If Excel.exe was orphaned from a previous run** — wrap every Excel automation in an `Excel Process Scope` (so the scope's `Dispose` always closes Excel) and ensure no `Try/Catch` swallows the scope's exit. As a one-time cleanup, kill orphaned `EXCEL.EXE` processes on the robot machine via Task Manager or `Stop-Process -Name EXCEL -Force`.
- **If multiple Office versions are installed** — uninstall the redundant Office install (typically the older perpetual edition, leaving Microsoft 365 Apps). Two coexisting Office installs are unsupported by Microsoft for COM automation and will continue to produce intermittent errors until consolidated.
- **If Office bitness does not match the robot process bitness** — reinstall Office at the same bitness as the robot (preferred: 64-bit Office for 64-bit robots), or run the robot under the matching bitness. Mixed bitness is supported by Office in general but is a known source of COM-interop instability for `Invoke VBA`.
- **If the host has concurrent Excel use** — schedule the workflow off-hours, dedicate the robot machine to unattended execution, or use a different host where Excel will not be opened interactively during the run.

If the HRESULT persists after all environmental causes are ruled out, capture a full robot log (`Verbose` level) plus a Process Monitor trace of `EXCEL.EXE` during the failure and open a UiPath support case — the residual cases are package or Office-version-specific bugs that need vendor diagnosis.
