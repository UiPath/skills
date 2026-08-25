# Final Resolution

---

**Root Cause:** `Main.xaml` applies a Filter activity ("Filter Status =
Active") to the `Prices` sheet before the `Lookup Range` runs. The target
`SKU-8842` has Status "Discontinued", so the active filter hides its row.
`Lookup Range` searches only the *visible* cells, finds nothing, and
returns an empty result; the workflow's guard then throws `SKU-8842 not
found in price list`. The value is genuinely present in the sheet - it is
filtered out, not absent.

**What went wrong:** The `PriceUpdater` job (started
2026-05-27T09:12:40Z) faulted ~6 seconds in. The job error is a
`BusinessRuleException: SKU-8842 not found in price list` thrown by the
workflow after `Lookup Range` returned an empty cell address. The user
confirms SKU-8842 is visibly present when the workbook is opened by hand -
so the lookup is not failing because the data is missing.

**Why:** `Lookup Range` evaluates only cells that are currently visible.
When an AutoFilter is active, rows excluded by the filter are not part of
the searched range. `Main.xaml` runs `Filter Status = Active` on the
`Prices` sheet immediately before the `Lookup Range`, narrowing the
visible rows to Status = "Active". SKU-8842's row carries Status =
"Discontinued", so it is filtered out and the lookup cannot see it. This
is a silent miss at the lookup layer; the only thrown error is the
workflow's own downstream "not found" guard.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PriceUpdater -- Faulted at 2026-05-27T09:12:46.330Z (ran for ~5.9 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `BusinessRuleException: SKU-8842 not found in price list` -> `Main.xaml` -> `Throw "SKU Not Found"` -> `If "Guard empty result"` -> `ExcelApplicationCard "Use Excel File"`

### Excel Activities (Root Cause)
- Activity surface: modern `UiPath.Excel.Activities.LookUpRangeX` ("Lookup Range") inside `Use Excel File`
- Workflow ordering in `Main.xaml`: `Filter` ("Filter Status = Active", sheet `Prices`, column `Status`, keep `Active`) runs BEFORE `Lookup Range` (Value = SKU-8842, sheet `Prices`).
- `Lookup Range` searches visible cells only; with the Status = "Active" filter applied, SKU-8842 (Status "Discontinued") is hidden, so the lookup returns empty.
- The job log shows the filter applied, then the lookup returning an empty result, then the workflow's guard throwing - no error from the lookup itself.

---

**Immediate fix:**

### Excel Activities (Root Cause)
1. Clear or reset the filter before the `Lookup Range` runs.
   - **Why:** `Lookup Range` only sees visible rows. With the Status =
     "Active" filter active, the Discontinued SKU is hidden. Removing the
     filter (or running the lookup before the filter) lets the lookup see
     the full data set.
   - **Where (in `Main.xaml`):** insert a filter-reset before the
     `Lookup Range` - a `Clear Sheet/Range/Table` (clear-filters variant)
     or a `Filter` activity configured to clear the `Prices` filter - OR
     reorder so the `Lookup Range` runs before the `Filter Status = Active`
     step. If the filter is only needed for a later step, scope it after
     the lookup.
   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/lookup-range-active-filters.md`

2. If the lookup must consider only "Active" SKUs by design, then SKU-8842
   being Discontinued is a true business "not found" - confirm with the
   process owner whether discontinued SKUs should be matched. (The user's
   report that the SKU "is definitely there" suggests they expect it to be
   matched, which points to the filter being the defect.)

---

**Preventive fix:**

1. **Studio** -- when a workflow both filters and looks up on the same
   sheet, run the `Lookup Range` against the unfiltered data, or clear the
   filter immediately before any lookup, so visible-cells-only behavior
   does not silently drop rows.
   - **Why:** Lookup Range's visible-cells-only semantics are an easy
     silent-miss trap when a filter is applied earlier in the same flow.
   - **Who:** RPA developer

2. **Studio** -- after a `Lookup Range`, guard on an empty result with a
   message that names the *visible-rows* caveat (e.g. "not found in the
   currently visible/filtered rows") so the next failure points at the
   filter rather than reading as "data missing".
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An active filter applied before the Lookup Range hides SKU-8842's (Discontinued) row; the lookup searches visible cells only and returns empty | High | Confirmed | Yes | `Filter Status = Active` precedes `Lookup Range` in `Main.xaml`; user confirms the SKU is physically present; thrown error is the workflow's own "not found" guard | Clear/reset the filter before the lookup, or reorder so the lookup runs on unfiltered data |

---

Would you like help editing `Main.xaml` to clear the filter before the
`Lookup Range` (or reorder the steps), or cleaning up the
`.local/investigations/` folder?
