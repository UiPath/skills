# Final Resolution

---

**Root Cause:** The external code file `macro.txt` referenced by the
`Invoke VBA` activity's `CodeFilePath` contains bare executable
statements at the module level - there is no `Sub RefreshSheets()` /
`End Sub` block around them. `Invoke VBA` injects the file's contents
as a VBA module body, and the VBA compiler rejects the bare statements
with `Compile error: Expected: Sub, Function, Property, or Type` before
any macro logic executes.

**What went wrong:** The `ReportRefresher` job (started
2026-05-13T10:42:18Z) faulted ~4 seconds after launch when its
`Invoke VBA` activity tried to inject `macro.txt` into the open
workbook. The runtime error was the verbatim VBA compile error
above.

**Why:** `Invoke VBA` reads the macro source from an external
`.txt`/`.vba`/`.bas` file and injects it as a new VBA module via
`Workbook.VBProject.VBComponents.Add`. A VBA module body is structurally
a list of procedure declarations - it cannot contain bare executable
statements at the top level. `macro.txt` in this project has
`ActiveWorkbook.RefreshAll` and `Application.Calculate` written directly
at the file scope, so the injected module compile-fails at the first
non-declaration line and the activity faults before calling the named
entry method.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ReportRefresher -- Faulted at 2026-05-13T10:42:22.110Z (ran for ~4.0 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `Cannot run the macro 'RefreshSheets'. Compile error: Expected: Sub, Function, Property, or Type` -> `Main.xaml` -> `InvokeVBAX "Invoke VBA"` -> `ExcelApplicationCard "Use Excel File"` -> `ExcelProcessScope "Excel Process Scope"`

### Excel Activities (Root Cause)
- Activity: `InvokeVBAX` (DisplayName: "Invoke VBA")
- CodeFilePath (from `Main.xaml`): `macro.txt`
- EntryMethodName: `RefreshSheets`
- Contents of `macro.txt` at the project root:

  ```
  ActiveWorkbook.RefreshAll
  Application.Calculate
  ActiveWorkbook.Save
  ```

  No `Sub RefreshSheets()` declaration anywhere in the file. Because
  every statement is at the module top level, the VBA compiler rejects
  the injection before `Application.Run("RefreshSheets", ...)` is
  reached.

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Wrap the contents of `macro.txt` in a `Sub RefreshSheets()` block.
   - **Why:** A VBA module body only accepts procedure declarations at
     the top level. The activity's `EntryMethodName` is `RefreshSheets`,
     so the wrapping `Sub` name must match exactly.
   - **Where:** `macro.txt`. Replace the file contents with:

     ```vb
     Sub RefreshSheets()
         ActiveWorkbook.RefreshAll
         Application.Calculate
         ActiveWorkbook.Save
     End Sub
     ```

   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/invoke-vba-code-file-path.md`
     ("Code not wrapped in a Sub/Function" branch)

After saving, rebuild the project and republish so the corrected
`macro.txt` ships with the package.

---

**Preventive fix:**

1. **Studio** -- when authoring `Invoke VBA` macros, always paste the
   source into the external file inside Excel's VBA editor (`Alt+F11`)
   first, hit `Debug > Compile VBAProject` to validate, then copy the
   compiled `Sub`/`Function` text into the `.txt`/`.vba`/`.bas` file.
   This surfaces missing wrappers and syntax errors at authoring time
   rather than first job run.
   - **Why:** A bare-statement file looks deceptively like working VBA
     until injection fails.
   - **Who:** RPA developer

2. **Orchestrator** -- subscribe to faulted-job alerts on the
   `RPA Production` folder so this class of regression surfaces
   immediately when it happens again on a sibling process.
   - **Why:** The first failure was reported by the end user; alerting
     closes that gap.
   - **Where:** Orchestrator UI -> Alerts -> severity "Error" + folder
     filter for `RPA Production`.
   - **Who:** Admin or platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `macro.txt` body has bare VBA statements at the module top level (no Sub/Function wrapper); VBA compile-fails on injection | High | Confirmed | Yes | Job log compile error + direct Read of `macro.txt` showing no Sub declaration | Wrap the file body in `Sub RefreshSheets() ... End Sub` and republish |

---

Would you like help editing `macro.txt` to add the `Sub RefreshSheets()`
wrapper, or cleaning up the `.local/investigations/` folder?
