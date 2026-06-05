---
confidence: high
---

# Invoke VBA — Trust Access to VBA Project Denied

## Context

What this looks like:
- Activity `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) faults the first time it tries to inject the macro module into the workbook
- Error message contains one of: `Programmatic access to Visual Basic Project is not trusted`, `Programmatic access to Office VBA project is denied`, or a wrapped form referencing `VBProject`/`VBComponents.Add`
- Job faults synchronously the moment `Invoke VBA` runs; the surrounding `Excel Process Scope` did not fault

What can cause it:
- Excel's "Trust access to the VBA project object model" setting is disabled on the robot machine, under the Windows user the robot runs as. `Invoke VBA` injects a new VBA module into the workbook via `Workbook.VBProject.VBComponents.Add` — that API call requires this setting to be enabled. This is the only cause — Excel returns the security block authoritatively before any macro source is read.

Notes:
- The setting is **per-user, per-machine, and per Office install**. Enabling it on a developer workstation does not propagate to the robot host; enabling it for one Windows user does not enable it for another.
- The setting is not visible from Orchestrator, job logs, or trace evidence — confirmation requires desktop access to the robot machine under the correct user.

## Investigation

1. Read the activity stack/error from job evidence and confirm the faulted activity is `InvokeVBAX` and the message references trust, programmatic access, or `VBProject`.
2. Confirm the `Excel Process Scope` around `Invoke VBA` opened successfully — if the scope itself faulted, this is a different problem (see the COM interop playbook).
3. Ask the user (or someone with desktop access to the robot machine, signed in as the robot's Windows user) to check the Trust Center setting at:
   `File > Options > Trust Center > Trust Center Settings... > Macro Settings > "Trust access to the VBA project object model"`.

## Resolution

- **If the setting is unchecked** — ask the user to enable it on the robot machine under the Windows user the robot runs as:
  1. Open Microsoft Excel.
  2. Go to `File > Options > Trust Center > Trust Center Settings...`.
  3. Select `Macro Settings`.
  4. Check `Trust access to the VBA project object model`.
  5. Also check `Enable VBA macros` (or `Enable all macros` if the policy permits) so the injected macro is allowed to run.
  6. Close all Excel windows so the setting takes effect on the next launch, then re-run the job.
- **If the setting is checked but the error persists** — the setting is enforced per Office install and per Windows user. Verify (a) the same Windows user the robot runs as has the setting enabled (not just the interactive user who checked), and (b) the Excel version `Invoke VBA` is binding to is the same Office install where the setting was changed (see the COM interop playbook for multi-Office hosts). If still failing after both, treat this as a different cause and escalate.
- **If Group Policy locks the setting** — the toggle is managed by the `VBAWarnings` / `AccessVBOM` registry policy and may be locked by a domain administrator. The user needs to work with IT to grant the exception for the robot machine; there is no workaround inside Studio.
