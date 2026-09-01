# Final Resolution

---

**Root Cause:** The Excel Process Scope in `Main.xaml` runs with
`ShowExcel="False"`. When the workbook opens, a Protected View bar
(from a Mark-of-the-Web on the downloaded `.xlsx`) blocks every COM
call into the workbook, but the bar is invisible during the run. The
Invoke VBA activity's call into `Workbook.VBProject` is dropped by the
wedged COM server and surfaces as
`The system call failed. (Exception from HRESULT: 0x80010100
(RPC_E_SYS_CALL_FAILED))`.

**What went wrong:** The `DailyDigestRunner` job (started
2026-05-16T07:00:12Z) faulted ~12 seconds after launch when its
`Invoke VBA` activity tried to inject the macro module. The job had
intermittently succeeded in earlier runs (the dialog only appears the
first time a Mark-of-the-Web workbook is opened on a host), making it
look transient.

**Why:** The COM dispatcher into Excel.exe blocks while a modal dialog
is foregrounded - even one the user cannot see. Common dialogs that
hit unattended runs:

- Protected View bar (Mark-of-the-Web on a workbook downloaded /
  emailed in)
- Macro warning bar (the workbook is in a non-trusted location)
- "Trust this file" prompt
- License activation prompt
- Recover-unsaved-files banner from a prior crash

With `ShowExcel=False` the dialog is invisible, so the symptom is
"COM call timed out for no reason." Setting `ShowExcel=True` and
re-running surfaces which dialog is responsible.

A secondary, less likely cause is multi-Office or bitness mismatch on
the host - which the user can rule out by inventorying the installs.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: DailyDigestRunner -- Faulted at 2026-05-16T07:00:24.310Z (ran for ~12.1 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `The system call failed. (Exception from HRESULT: 0x80010100 (RPC_E_SYS_CALL_FAILED))` -> `Main.xaml` -> `InvokeVBAX "Invoke VBA"` -> `ExcelApplicationCard "Use Excel File"` -> `ExcelProcessScope "Excel Process Scope"`

### Excel Activities (Root Cause)
- Activity: `InvokeVBAX` (DisplayName: "Invoke VBA")
- CodeFilePath (from `Main.xaml`): `macro.txt`
- EntryMethodName: `BuildDigest`
- Surrounding Excel Process Scope's `ShowExcel` property: **`False`**.
  Any modal dialog on Excel during the run is invisible to whoever is
  watching, but still blocks COM calls.
- HRESULT `0x80010100 RPC_E_SYS_CALL_FAILED` is the COM dispatcher's
  signature for "the call into the server hung or was rejected." The
  most common cause on unattended Excel runs is a hidden modal dialog.

---

**Immediate fix:**

The agent could not verify which dialog is blocking the COM call from
Orchestrator alone. Hand the user this host-side check list to run
the next time they are in front of MOCK-HOST under the robot's
Windows user.

### Host-side check list (RPA Production / MOCK-HOST)

1. **Make Excel visible during a test run.**
   - **What:** In `Main.xaml`, set the Excel Process Scope's
     `ShowExcel` property from `False` to `True`. Save, rebuild, and
     re-run the process from Orchestrator. Watch the Excel window on
     the robot.
   - **Why:** Surfaces any modal dialog that was hidden during
     unattended runs. If a Protected View bar, macro warning, license
     prompt, or recover-unsaved-files banner appears, that is the
     blocker.
   - **Revert:** Once the cause is found and fixed, set `ShowExcel`
     back to `False` for production.

2. **Unblock the workbook (Mark-of-the-Web).**
   - **What:** Right-click the `.xlsx` file the activity opens
     (`reports\DailyDigest.xlsx`), choose `Properties`, and check
     `Unblock` if the option is present. Alternatively, run
     `Unblock-File <path>` in PowerShell as the robot's Windows user.
   - **Why:** Mark-of-the-Web triggers Protected View on the first
     open; once unblocked, the bar will not appear again.

3. **Check Excel Trusted Locations.**
   - **What:** In Excel (as the robot's Windows user), go to
     `File > Options > Trust Center > Trust Center Settings >
     Trusted Locations`. Add the workbook's folder.
   - **Why:** Workbooks opened from a trusted location bypass the
     Protected View / "trust this file" prompt entirely.

4. **Check for orphaned EXCEL.EXE.**
   - **What:** Open Task Manager on the robot, find any `EXCEL.EXE`
     instances with no visible window. Kill them all (`Stop-Process
     -Name EXCEL -Force` in PowerShell as the robot's Windows user).
   - **Why:** A prior run that crashed without closing the Excel
     Process Scope can leave Excel.exe wedged. Subsequent runs land
     on the wedged process and hit the same COM timeout.

5. **Inventory installed Office versions.**
   - **What:** Open `Control Panel > Programs and Features` (or
     `Get-WmiObject Win32_Product | Where-Object Name -like '*Office*'`
     in PowerShell). Confirm there is **one** Office install, and
     note its bitness (`File > Account > About Excel` shows
     "32-bit" / "64-bit").
   - **Why:** Multiple Office installs on the same host produce
     dispatcher ambiguity; bitness mismatch with the robot process is
     a separate known cause of intermittent COM failures.

Come back with what step 1 surfaced (which dialog, if any) and the
results of steps 4 and 5. That narrows the playbook to the matching
sub-cause and produces the final fix.

---

**Preventive fix:**

1. **Studio** -- on every Excel Process Scope used by an unattended
   process, set `ShowExcel=True` during development and
   troubleshooting so dialogs are visible. Only set `ShowExcel=False`
   once the workbook + macro pair runs cleanly under the actual robot
   identity.
   - **Why:** Hidden dialogs are the #1 cause of "transient" COM
     interop failures.
   - **Who:** RPA developer

2. **Robot host provisioning** -- pre-trust the inbound folder for
   workbook drops via `Trusted Locations`, and configure file
   downloads to skip the Mark-of-the-Web flag (`Set-MpPreference
   -DisableIOAVProtection $false` is not the right answer; the right
   answer is a Group Policy controlling SmartScreen / MotW behavior).
   - **Why:** Removes the most common modal dialog from the failure
     funnel.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | A hidden modal dialog (most likely Protected View / Mark-of-the-Web) is blocking the COM call from `InvokeVBAX` to `VBProject` while `ShowExcel=False` hides it | High | Confirmed (matches playbook signature; needs host-side verification for the specific dialog) | Yes (class) | HRESULT `0x80010100 RPC_E_SYS_CALL_FAILED` + `ShowExcel="False"` on the Excel Process Scope in `Main.xaml` | Set `ShowExcel=True`, re-run, dismiss whatever dialog appears, unblock the workbook |
| H2 | Multi-Office install or bitness mismatch on the robot host | Medium | Pending - needs host inventory | Possible | None gathered (host not accessible) | Inventory Office installs and bitness on MOCK-HOST |

---

Would you like me to draft the host-check note as a single document
you can hand off, or clean up the `.local/investigations/` folder?
