# Final Resolution

---

**Root Cause:** The `Invoke VBA` activity in `Main.xaml` sets
`EntryMethodName="ProcessInvoces"` (typo - missing an "i"). The
external code file `macro.txt` declares `Sub ProcessInvoices()`
(correctly spelled, top-level, Public). `Application.Run` matches names
exactly against the injected module, so the typo'd name has no match
and the activity faults with `Cannot run the macro 'ProcessInvoces'.
The macro may not be available in this workbook`.

**What went wrong:** The `InvoiceImporter` job (started
2026-05-14T08:05:11Z) faulted ~5 seconds after launch when its
`Invoke VBA` activity called `Application.Run("ProcessInvoces", ...)`.
The macro source compiles cleanly; the entry method name is what does
not resolve.

**Why:** `Invoke VBA` reads the macro source from `CodeFilePath`,
injects it as a new VBA module, then calls
`Application.Run(EntryMethodName, EntryMethodParameters)`. The lookup
is verbatim against the declared procedure names in the injected
module. A one-character mismatch produces a hard miss - VBA does not
fall back to fuzzy matching. The code file's `Sub ProcessInvoices()`
exists and would run if called by name, but the activity passes a
different string.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceImporter -- Faulted at 2026-05-14T08:05:16.420Z (ran for ~5.3 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `Cannot run the macro 'ProcessInvoces'. The macro may not be available in this workbook` -> `Main.xaml` -> `InvokeVBAX "Invoke VBA"` -> `ExcelApplicationCard "Use Excel File"` -> `ExcelProcessScope "Excel Process Scope"`

### Excel Activities (Root Cause)
- Activity: `InvokeVBAX` (DisplayName: "Invoke VBA")
- CodeFilePath (from `Main.xaml`): `macro.txt`
- EntryMethodName referenced (from `Main.xaml`): **`ProcessInvoces`** (typo)
- Declaration in `macro.txt`: `Sub ProcessInvoices()` (correctly spelled, top-level)
- Exact-match lookup by Application.Run returned "macro not available" because of the missing "i".

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Correct the typo in `Main.xaml`.
   - **Why:** `EntryMethodName` must match a `Sub`/`Function` declared
     in the code file exactly. `ProcessInvoces` has no match;
     `ProcessInvoices` exists.
   - **Where:** `Main.xaml` -> `<uix:InvokeVBAX ... EntryMethodName="ProcessInvoces" ...>` -> change to `EntryMethodName="ProcessInvoices"`. Save, rebuild, republish the process.
   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/invoke-vba-entry-method-name.md` ("typo or whitespace mismatch" branch)

Alternative: rename the Sub in `macro.txt` from `ProcessInvoices` to
`ProcessInvoces` to match the workflow. Only do this if the typo'd
name is the intentional convention (very unlikely - the spelling in
the code file is the correct one).

---

**Preventive fix:**

1. **Studio** -- bind `EntryMethodName` to a project constant rather
   than a string literal.
   - **Why:** A typo in a string literal is silent at design time. A
     constant centralizes the macro name and surfaces a compile-time
     error if the wrong constant is referenced.
   - **Where:** Define `InvoiceMacroEntry = "ProcessInvoices"` as a
     project constant, then reference that constant from the
     `EntryMethodName` property of every Invoke VBA activity that
     calls it.
   - **Who:** RPA developer

2. **Studio** -- add a project-level check (script or pre-publish
   validator) that diffs every `Invoke VBA` activity's
   `EntryMethodName` against the `Sub`/`Function` declarations in its
   `CodeFilePath`.
   - **Why:** Catches future near-misses before they ship.
   - **Who:** RPA platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `EntryMethodName` in `Main.xaml` is misspelled (`ProcessInvoces`); declared Sub in `macro.txt` is `ProcessInvoices` | High | Confirmed | Yes | Runtime "macro not available" error + exact-spelling near-miss in the code file | Fix `EntryMethodName` in `Main.xaml`, rebuild, republish |

---

Would you like help applying the fix - updating `Main.xaml` to
reference `ProcessInvoices` and republishing the package? I can also
clean up the `.local/investigations/` folder if you no longer need it.
