# Final Resolution

---

**Root Cause:** The classic `Lookup Range` activity in `Main.xaml` is
placed directly in the Main `Sequence` with **no surrounding
`Excel Application Scope`** (or `Use Excel File`). The classic
`Lookup Range` depends on a scope to supply its workbook context object;
without one there is no workbook to resolve the sheet/range against, so the
activity dereferences null and faults immediately with
`System.NullReferenceException: Object reference not set to an instance of
an object`.

**What went wrong:** The `OrderLookup` job (started
2026-05-27T08:18:55Z) faulted ~2 seconds in. The runtime error was a
`NullReferenceException` thrown by the `Lookup Range`. The job log shows
execution start, then the null fault at the lookup, with no "workbook
opened" line - because nothing ever opened a workbook. The fault stack is
`LookUpRange "Lookup Range"` -> `Sequence "Main Sequence"` -> `Main`, with
no scope between the activity and the Sequence.

**Why:** A classic `Lookup Range` reads its target sheet/range through the
`WorkbookApplication` context that an `Excel Application Scope` provides.
When the activity is dropped outside any scope, that context is null, so
the moment it tries to resolve its target it dereferences null and raises a
`NullReferenceException`. (The same NRE can also come from a sheet/range
that does not resolve, but here the activity has no workbook context at all
- the stack and `Main.xaml` both show no enclosing scope.)

---

**Evidence:**

### Orchestrator (Propagation)
- Job: OrderLookup -- Faulted at 2026-05-27T08:18:57.900Z (ran for ~2.3 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `System.NullReferenceException: Object reference not set to an instance of an object` -> `Main.xaml` -> `LookUpRange "Lookup Range"` -> `Sequence "Main Sequence"` -> `Main`
- The stack has **no Excel scope** between the `Lookup Range` and the `Sequence`, and the log shows no "workbook opened" line.

### Excel Activities (Root Cause)
- Activity surface: classic `UiPath.Excel.Activities.LookUpRange`
- Placement in `Main.xaml`: the `LookUpRange "Lookup Range"` is a direct child of `Sequence "Main Sequence"` - it is **not** inside an `ExcelApplicationScope` (nor a `Use Excel File` card).
- With no scope, the activity has no workbook context object; resolving its sheet/range dereferences null, producing the `NullReferenceException`.

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Wrap the `Lookup Range` in an `Excel Application Scope` (classic) bound
   to the target workbook, so the activity has a workbook context.
   - **Why:** the classic `Lookup Range` needs the scope's
     `WorkbookApplication`; without it the context is null and the activity
     throws `NullReferenceException` immediately.
   - **Where (in `Main.xaml`):** add an `Excel Application Scope` with the
     correct `WorkbookPath` around the `LookUpRange "Lookup Range"` (on the
     modern surface, use `Use Excel File` / `Excel Process Scope` with
     `LookUpRangeX`).
   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/lookup-range-null-reference.md`
2. After adding the scope, confirm the scope opens the intended workbook and
   the `SheetName` ("Orders") exists in it - if the NRE persists after the
   scope is in place, check for a missing/renamed sheet or an undefined
   named range (the other causes in the same playbook).

---

**Preventive fix:**

1. **Studio** -- always place `Lookup Range` (and other Excel activities)
   inside an `Excel Application Scope` / `Use Excel File`; never drop them
   into a bare `Sequence`.
   - **Why:** an Excel activity with no scope has no workbook context and
     fails only at runtime with a generic `NullReferenceException`.
   - **Who:** RPA developer.

2. **Studio** -- validate the workflow before publishing; a `Lookup Range`
   outside a scope is a structural mistake that is cheap to catch in design.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Lookup Range is placed outside any Excel Application Scope, so it has no workbook context and faults with NullReferenceException | High | Confirmed | Yes | `NullReferenceException` at `LookUpRange`; fault stack and `Main.xaml` show no enclosing Excel scope; no "workbook opened" log line | Wrap the Lookup Range in an Excel Application Scope (or Use Excel File) bound to the workbook |

---

Would you like help editing `Main.xaml` to wrap the `Lookup Range` in an
`Excel Application Scope`, or cleaning up the `.local/investigations/`
folder?
