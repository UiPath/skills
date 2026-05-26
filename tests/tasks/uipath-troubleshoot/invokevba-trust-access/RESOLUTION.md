# Final Resolution

---

**Root Cause:** Excel's "Trust access to the VBA project object model"
Trust Center setting is disabled on the robot machine, under the
Windows user the robot runs as. The `Invoke VBA` activity in
`Main.xaml` cannot inject its macro module because Excel blocks the
`Workbook.VBProject.VBComponents.Add` API on programmatic access, and
the job faults before any macro logic executes.

**What went wrong:** The `InvoiceMacroRunner` job (started
2026-05-12T09:14:02Z) faulted ~3 seconds after launch when its
`Invoke VBA` activity tried to load `macro.txt` into the workbook. The
runtime error was `Programmatic access to Visual Basic Project is not
trusted`.

**Why:** `Invoke VBA` reads its source from an external code file at
`CodeFilePath` and injects the macro into the workbook's `VBProject` at
runtime. That injection step calls
`Workbook.VBProject.VBComponents.Add`, which Excel only allows when the
"Trust access to the VBA project object model" Macro Setting is
checked. When the setting is off (the default for fresh Excel
installs), every Invoke VBA call faults before the macro runs. The
setting is per-Windows-user and per-Office-install, so enabling it on
one developer workstation does not propagate to the robot host.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceMacroRunner -- Faulted at 2026-05-12T09:14:05.310Z (ran for ~3.2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `Programmatic access to Visual Basic Project is not trusted` -> `Main.xaml` -> `InvokeVBAX "Invoke VBA"` -> `ExcelProcessScope "Excel Process Scope"` -> `Sequence "Main Sequence"`

### Excel Activities (Root Cause)
- Activity: `InvokeVBAX` (DisplayName: "Invoke VBA")
- CodeFilePath (from `Main.xaml`): `macro.txt`
- EntryMethodName: `RefreshPivotTables`
- The error message is the verbatim signature of Excel's security block on
  `Workbook.VBProject.VBComponents.Add`. The cause is the disabled
  Trust Center toggle, not the macro source or the entry method.

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Enable the Trust Center toggle on the robot machine, under the Windows
   user the robot runs as.
   - **Why:** `Invoke VBA` cannot inject a macro module unless this
     setting is on. The setting is per-user and per-Office install.
   - **Where (on the robot machine, signed in as the robot's Windows user):**
     1. Open Microsoft Excel.
     2. Go to `File > Options > Trust Center > Trust Center Settings...`.
     3. Select `Macro Settings`.
     4. Check `Trust access to the VBA project object model`.
     5. Also check `Enable VBA macros` (or `Enable all macros` if policy
        permits) so the injected macro is allowed to run.
     6. Close all Excel windows so the setting takes effect on next launch.
   - **Who:** Whoever has desktop access to the robot machine as the
     robot's Windows user (the RPA developer, or the team that manages
     the robot host).
   - **Source:** `excel-activities/playbooks/invoke-vba-trust-access.md`

If the setting is already on but the error persists, verify (a) the
same Windows user the robot runs as has the setting enabled, and (b)
the Excel install the robot binds to is the same one where the setting
was changed (multi-Office hosts can have separate Trust Center stores).
If Group Policy locks the toggle, work with IT to grant the exception
for the robot machine - there is no Studio-side workaround.

---

**Preventive fix:**

1. **Robot host provisioning** -- bake the Trust Center setting into the
   robot machine image (registry value
   `HKCU\Software\Microsoft\Office\<ver>\Excel\Security\AccessVBOM = 1`)
   so every new robot has it enabled out of the box.
   - **Why:** Manual Trust Center configuration drifts across hosts. A
     baseline image with the setting pre-applied removes a class of
     intermittent Invoke VBA failures.
   - **Who:** Platform / robot host team.

2. **Orchestrator alerts** -- subscribe to faulted-job alerts on the
   `RPA Production` folder so future Trust Center regressions surface
   immediately.
   - **Why:** The first failure should not have to be reported by the
     end user.
   - **Where:** Orchestrator UI -> Alerts -> severity "Error" + folder
     filter for `RPA Production`.
   - **Who:** Admin or platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Trust access to VBA project object model is disabled on the robot machine | High | Confirmed | Yes | Runtime error `Programmatic access to Visual Basic Project is not trusted` from the Invoke VBA activity | Enable the Trust Center toggle on the robot host under the robot's Windows user |

---

Would you like help drafting the host-check note for whoever will sit at
the robot machine, or cleaning up the `.local/investigations/` folder?
