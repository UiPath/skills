# Final Resolution

---

**Root Cause:** The Invoke VBA activity in `Main.xaml` passes a
one-element `EntryMethodParameters` array (`new Object[] { 125.50 }`)
to a macro whose signature in `macro.txt` requires two arguments
(`Sub PostRow(amount As Double, vendor As String)`). `Application.Run`
rejects the arity mismatch with `Wrong number of arguments or invalid
property assignment` and the activity faults before the macro
executes.

**What went wrong:** The `LedgerPoster` job (started
2026-05-15T11:18:30Z) faulted ~5 seconds after launch when its
`Invoke VBA` activity called
`Application.Run("PostRow", { 125.50 })`. The macro source compiles
cleanly and `EntryMethodName` resolves correctly; only the parameter
array is shaped wrong.

**Why:** VBA's `Application.Run` marshals each element of the supplied
`IEnumerable<Object>` into the macro's positional parameters. A
mismatch in element count between the array and the declared `Sub`
signature is rejected at the marshal step. The `vendor` parameter on
the Sub has no `Optional` keyword, so it must be supplied - leaving it
off makes the call illegal.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: LedgerPoster -- Faulted at 2026-05-15T11:18:34.715Z (ran for ~4.8 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `Wrong number of arguments or invalid property assignment` -> `Main.xaml` -> `InvokeVBAX "Invoke VBA"` -> `ExcelApplicationCard "Use Excel File"` -> `ExcelProcessScope "Excel Process Scope"`

### Excel Activities (Root Cause)
- Activity: `InvokeVBAX` (DisplayName: "Invoke VBA")
- CodeFilePath (from `Main.xaml`): `macro.txt`
- EntryMethodName: `PostRow`
- EntryMethodParameters expression (from `Main.xaml`): `new Object[] { 125.50 }` (one element)
- Sub signature in `macro.txt`: `Sub PostRow(amount As Double, vendor As String)` (two required parameters)
- Element count in the XAML array: 1. Required parameters in the Sub: 2. The second parameter `vendor` has no `Optional` keyword and is missing.

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Pass a 2-element array matching the macro signature.
   - **Why:** The Sub's `vendor` parameter is non-optional. Every call
     must supply both `amount` and `vendor`.
   - **Where:** Add an `Assign` activity before `Invoke VBA`:

     ```
     macroParams = new Object[] { 125.50, "ACME Corp" }
     ```

     Then bind `EntryMethodParameters` on the Invoke VBA activity to
     `macroParams`. Save, rebuild, republish the process.
   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/invoke-vba-parameter-formatting.md` ("arity mismatch" branch)

If `vendor` should actually default to something when the workflow
does not have it, modify the Sub instead: declare
`vendor As String` as `Optional vendor As String = "Unknown"` so a
1-element call becomes valid.

---

**Preventive fix:**

1. **Studio** -- always construct `EntryMethodParameters` via an
   `Assign` activity placed before the Invoke VBA, not inline in the
   property panel.
   - **Why:** Inline editing in the property window can freeze Studio
     while parsing complex expressions, and the array shape is hard to
     review at a glance from the panel. An Assign-built variable is
     greppable, testable, and shows the array length at the
     declaration site.
   - **Who:** RPA developer

2. **Studio** -- bind the macro's required parameters to project
   variables with strong types, so a missing variable surfaces a
   compile-time error rather than a runtime arity mismatch.
   - **Why:** Catches future shape regressions before the package is
     published.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `EntryMethodParameters` in `Main.xaml` is a 1-element array; the Sub in `macro.txt` requires 2 arguments | High | Confirmed | Yes | Job log "Wrong number of arguments" + direct comparison of XAML array length vs Sub signature | Build a 2-element array in an Assign and bind it; or make the vendor parameter Optional |

---

Would you like help editing `Main.xaml` to construct the 2-element
parameter array via an Assign activity, or cleaning up the
`.local/investigations/` folder?
