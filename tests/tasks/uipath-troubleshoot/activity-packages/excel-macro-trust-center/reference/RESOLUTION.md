# Final Resolution

---

**Root Cause:** Excel's Trust Center policy on the Robot host
(`MOCK-HOST`), under the `UIPATH\AUTOMATION1` user's profile, has
macros set to "Disable all macros without notification" (or
similar restrictive setting), AND the workbook
`C:\Robot\Data\sales-macro.xlsm` is not in a Trusted Location or
signed by a trusted publisher. When the `Execute Macro` activity
attempts to dispatch `Module1.ProcessData`, Excel's macro-security
layer rejects the dispatch and returns the canonical "Cannot run
the macro..." COMException -- the same error wording that fires
when the macro doesn't exist at all (branch 1).

The macro IS present in the workbook (confirmed by the activity's
VBA-module enumeration in job logs). The user's "works on my dev
machine" clue is the canonical per-host Trust Center divergence
fingerprint: developer Excel has permissive Trust Center defaults
or trusted-location coverage for the dev workspace; the Robot
host's Excel under the Robot user's profile does not.

**What went wrong:** Failing job
`cc333333-cccc-dddd-eeee-ffffaaaabbbb` opened the workbook (no
IOException, no FileNotFoundException). The `Execute Macro`
activity enumerated the workbook's VBA modules and confirmed
`Module1.ProcessData` is present (alongside
`Module2.UpdateReport`). The activity then attempted to dispatch
the configured `Module1.ProcessData` via `Application.Run`, and
Excel's macro-security layer rejected the call before the macro
ran.

**Why:** The "Cannot run the macro 'X'. The macro may not be
available in this workbook or all macros may be disabled."
COMException covers two distinct cases:

- **Branch 1:** macro `X` is genuinely not in the workbook.
- **Branch 5:** macro `X` is in the workbook, but Trust Center
  has disabled macro execution.

The error wording is identical; the disambiguation comes from
the VBA-module enumeration. When the enumeration shows the
configured macro IS present in the workbook, branch 1 is ruled
out and branch 5 is the diagnosis. The user's "works on dev"
clue independently supports branch 5 (the divergence is
per-host / per-user Trust Center configuration, not per-workbook
content).

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelMacroProcess` (key `cc333333-...`) -- Faulted
  at `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException: Cannot run the
  macro 'Module1.ProcessData'. The macro may not be available in
  this workbook or all macros may be disabled.`
- Faulting activity: `ExecuteMacro_1` (`Execute Macro:
  Module1.ProcessData`) at `Main.xaml`.

### Job logs -- VBA enumeration (decisive)
- `Execute Macro: Module1.ProcessData -- enumerating VBA modules
  in workbook`
- `Execute Macro: Module1.ProcessData -- VBA modules:
  ['Module1.ProcessData', 'Module2.UpdateReport']`
- The configured macro `Module1.ProcessData` IS in the workbook.
  This rules out branch 1.
- `Execute Macro: Module1.ProcessData -- dispatching macro via
  COM (Application.Run 'Module1.ProcessData')`
- `Execute Macro: Module1.ProcessData -- COMException: Cannot
  run the macro 'Module1.ProcessData'. The macro may not be
  available in this workbook or all macros may be disabled.`

### Workflow source
- `Main.xaml`: `<uix:ExecuteMacro MacroName="Module1.ProcessData"
  .../>` -- the configured name matches an entry in the VBA
  enumeration verbatim.

### User clue (decisive)
- "The macro Module1.ProcessData IS in the workbook -- I just
  opened it in Excel on my dev machine and ran it manually, and
  it worked fine." This is the canonical "works on dev / fails
  on Robot" pattern for Trust Center divergence: the macro and
  workbook are valid; the difference is per-host Trust Center
  configuration.

### Cross-check -- what this is NOT
- Not branch 1 (macro-not-found): VBA enumeration confirms the
  macro is present.
- Not branch 2 (VBA error inside macro): no `DISP_E_EXCEPTION`
  HRESULT and no Run-time error text; the macro never started
  executing.
- Not branch 3 (Excel torn down): the failure is on Execute
  Macro itself, not a subsequent activity.
- Not branch 4 (modal dialog): the job did not hang; it surfaced
  the COMException immediately at dispatch.
- Not branch 6 (concurrent COM): no `0x800AC472`; the failure is
  deterministic and the error is macro-security-related, not
  threading.
- Not branch 7 (missing add-in): the macro wouldn't enumerate
  if it referenced a missing library that prevented compilation.

---

**Recommended Fix (Resolution):**

The agent cannot directly inspect Trust Center settings on the
Robot host via Orchestrator. Ask the user to verify and apply
the fix on MOCK-HOST under the Robot user's profile.

### Step 1 -- Confirm the Trust Center setting

Have the user log in to MOCK-HOST as the Robot user
(`UIPATH\AUTOMATION1`) or use PsExec to run Excel under that
identity:

1. Open Excel.
2. `File -> Options -> Trust Center -> Trust Center Settings -> Macro Settings`.
3. Observe the current setting. If "Disable all macros without
   notification" (or "Disable VBA macros except digitally
   signed") is selected and the workbook is not in Trusted
   Locations, branch 5 is confirmed.

Alternatively, via PowerShell on MOCK-HOST (under Robot user):

```powershell
# Read the Trust Center VBAWarnings registry value
Get-ItemProperty `
  -Path 'HKCU:\Software\Microsoft\Office\16.0\Excel\Security' `
  -Name VBAWarnings -ErrorAction SilentlyContinue
# 1 = Enable all macros (relaxed, not recommended for general use)
# 2 = Disable all macros with notification
# 3 = Disable all macros except digitally signed
# 4 = Disable all macros without notification (the strictest)
```

(Adjust the version number `16.0` to match the installed Excel:
14.0=2010, 15.0=2013, 16.0=2016/2019/365.)

### Step 2 -- Apply the fix

**Option A (preferred): Add the workbook's folder to Excel's
Trusted Locations.**

On MOCK-HOST as the Robot user:

1. Excel -> `File -> Options -> Trust Center -> Trust Center
   Settings -> Trusted Locations -> Add new location`.
2. Add `C:\Robot\Data\` (or the workbook's parent directory).
3. Check "Subfolders of this location are also trusted" if the
   data is organized hierarchically.
4. OK + close Excel.

Persistent under the Robot user's HKCU profile. Robot will
re-launch Excel for the next job and pick up the setting.

**Option B: Sign the macro with a code-signing certificate**
trusted on the Robot host.

1. Obtain a code-signing certificate (corporate CA preferred).
2. In Excel VBE: `Tools -> Digital Signature -> Choose -> select
   certificate -> OK`.
3. Save the workbook.
4. On MOCK-HOST: install the signing certificate into "Trusted
   Publishers" under the Robot user's certificate store.
5. Set Trust Center to "Disable VBA macros except digitally
   signed macros".

**Option C (last resort, security-relaxed): Set Trust Center to
"Enable VBA macros".** Acceptable only when the Robot host is
dedicated to trusted automation and not used for general Office
work. Document the security exception.

### Step 3 -- Provision other Robot hosts

If multiple Robot hosts run this workflow, apply the same
Trust Center / Trusted Locations configuration to each. Common
options:

- **Group Policy (GPO)**: Microsoft Office Administrative
  Template -> Excel -> Security -> Trust Center -> Trusted
  Locations / VBA Macro Notification. Pushes consistent config
  to all Robot hosts in the OU.
- **Robot host build script**: include a one-time PowerShell
  step that writes the Trusted Locations registry keys for the
  Robot user.

### Prevention

- When provisioning Robot hosts, include Excel Trusted Locations
  setup as part of the build process. Document the location list
  in the host build runbook.
- Do not assume developer-machine Trust Center settings apply
  to Robot hosts. The Robot user has its own HKCU and its own
  Trust Center configuration; what worked interactively does not
  automatically work unattended.
- Audit Trust Center configuration after Office updates --
  major version upgrades occasionally reset macro-security
  defaults.
- Prefer Trusted Locations over relaxing Trust Center macro
  settings broadly. Per-location trust is more secure than
  enabling all macros globally.
