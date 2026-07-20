# Final Resolution

---

**Root Cause:** `Main.xaml` runs a classic `Lookup Range`
(`UiPath.Excel.Activities.ExcelLookUpRange`) inside an `Excel Application
Scope` against the `PublishedPrices` sheet of `DailyPrices.xlsx`, with no
filter or other pre-step that would hide rows. The `PublishedPrices.SKU`
column is populated by a formula -- a VLOOKUP against a separate
`SourceFeed` sheet that an upstream job refreshes -- which the user
confirms when asked how the column is populated. The classic Interop API
reads the *cached* calculated value of each cell. In the unattended
robot's headless Excel session the cross-sheet VLOOKUP's cache can be
stale or empty (Excel has not done a full recalculation pass on the
freshly-refreshed source range), so the Interop read returns no value for
`SKU-7392` and `Lookup Range` cannot match it. The workflow's guard then
throws `Today's published price for SKU-7392 not found in PublishedPrices
sheet`. The value is genuinely present in the sheet -- the Interop read
of the formula's cached value just does not see it.

**What went wrong:** The `DailyPriceSync` job (started
2026-05-27T14:38:12Z) faulted ~5 seconds in. The job error is a
`BusinessRuleException: Today's published price for SKU-7392 not found in
PublishedPrices sheet`, thrown by the workflow after `Lookup Range`
returned an empty cell address. The user confirms SKU-7392 is visibly
present in the `PublishedPrices` sheet with today's price next to it when
the workbook is opened by hand -- so the lookup is not failing because
the data is missing.

**Why:** The classic `Lookup Range` activity reads each cell through the
Microsoft Excel Interop API. When the target cell is a formula, Interop
returns whatever Excel has currently cached as the formula's calculated
value. The `PublishedPrices.SKU` column is built from
`=VLOOKUP(..., SourceFeed!A:C, 1, FALSE)` against an upstream sheet that
is refreshed daily by another job. In the unattended robot's headless
Excel session the cross-sheet formula does not always recompute fully, so
the cached value Interop reads for the SKU-7392 row is empty or stale.
`Lookup Range` therefore cannot match a search value that the cell
visibly displays when the file is opened by hand -- the Interop read
sees a different (cached/empty) value than the screen does.

This is a silent miss at the lookup layer; the only thrown error is the
workflow's own downstream "not found" guard. There is no error from the
`Lookup Range` activity itself.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: DailyPriceSync -- Faulted at 2026-05-27T14:38:17.610Z (ran for ~5.4 seconds)
- Job type: Unattended, triggered by daily schedule on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `BusinessRuleException: Today's published price for SKU-7392 not found in PublishedPrices sheet` -> `Main.xaml` -> `Throw "Throw SKU Not Found"` -> `If "Guard empty result"` -> `ExcelApplicationScope "Excel Application Scope"`

### Excel Activities (Root Cause)
- Activity surface: classic `UiPath.Excel.Activities.ExcelLookUpRange`
  ("Lookup Range") inside `ExcelApplicationScope` on
  `data\DailyPrices.xlsx`, sheet `PublishedPrices`, search value
  `[skuCode]` = `SKU-7392`, whole-sheet `Range` (blank).
- Workflow ordering in `Main.xaml`: `Excel Application Scope` opens
  `DailyPrices.xlsx` -> `Lookup Range` against `PublishedPrices` -> `If`
  guard on empty `cellAddress` -> `Throw` business-rule exception. **No
  filter, no other pre-step that touches the sheet.**
- The `PublishedPrices.SKU` column is the result of a VLOOKUP into a
  separate `SourceFeed` sheet maintained by an upstream job (user-
  confirmed). The cell visibly displays the SKU when the file is opened
  by hand, but the Interop read returns the cell's *cached* calculated
  value which can be stale/empty in the robot's headless session.
- The job log shows the workbook opened, the lookup returning an empty
  result, then the workflow's guard throwing -- no error from the lookup
  itself.

---

**Immediate fix:**

### Excel Activities (Root Cause)

Either of the following resolves the silent miss. Pick the one that fits
the workbook's role best; both are documented migration paths.

1. **Convert the SKU formula cells to static values before the lookup**
   so the Interop read sees a literal-text cell rather than a
   freshly-recomputed formula.
   - **How (one-time, in the source workbook):** open `DailyPrices.xlsx`,
     select the `PublishedPrices.SKU` column, `Copy > Paste Special >
     Values`, save. The lookup then matches a static text cell.
   - **How (in the workflow, if the column must stay formula-driven on
     disk):** read the `PublishedPrices` range into a `DataTable` first
     (Workbook `Read Range` -- see option 2), or write the calculated
     values back as static text before the lookup runs.
   - **Why:** the Interop read returns the cell's cached calculated
     value, which can be stale/empty in the unattended robot's headless
     session. A static text cell has no cache to be stale.
   - **Where (in `Main.xaml`):** the change is in the source workbook
     (or upstream of `Lookup Range`); the activity itself stays as-is.
   - **Who:** RPA developer + data owner of the workbook
   - **Source:** `excel-activities/playbooks/lookup-range-formula-cells.md`

2. **Migrate the lookup off classic Interop to the Workbook (OpenXML)
   path,** which reads the workbook's last-saved cached calculated
   values without re-evaluating formulas through Interop.
   - **How:** replace the classic `Lookup Range` + `Excel Application
     Scope` with the Workbook `Read Range` activity (under the
     `Workbook` category, NOT inside any Excel scope), output to a
     `DataTable`, then search the `DataTable` with the `Lookup Data
     Table` activity -- the OpenXML-friendly equivalent of `Lookup
     Range`.
   - **Why:** the Workbook (OpenXML) path reads the cached values that
     Excel wrote to the .xlsx on its last save, deterministically and
     without launching Excel. The freshness then depends on when the
     upstream job last saved the workbook, not on whether the robot's
     headless Excel session managed to recalculate formulas.
   - **Where (in `Main.xaml`):** the `ExcelApplicationScope` and the
     classic `ExcelLookUpRange` are removed; the new chain is
     `Workbook Read Range` -> (existing guard against empty DataTable
     hit) -> `Lookup Data Table` -> existing guard against empty result.
   - **Who:** RPA developer
   - **Source:** `excel-activities/playbooks/lookup-range-formula-cells.md`
     (Resolution, second bullet)

---

**Preventive fix:**

1. **Studio** -- when a workflow looks up a value on a sheet whose target
   column is computed from formulas (especially cross-sheet VLOOKUPs or
   add-in-dependent calculations), use the Workbook `Read Range` +
   `Lookup Data Table` path by default rather than classic Interop. This
   removes the Interop cache-staleness class of failures entirely.
   - **Why:** the Workbook path reads what Excel last *saved*, not what
     a headless Excel session can currently *re-evaluate*. The latter is
     fragile under unattended runs.
   - **Who:** RPA developer

2. **Studio** -- after a `Lookup Range`, guard on an empty result with a
   message that names the *Interop cached value* caveat (e.g. "not found
   in cached cell values") so the next failure points at the formula
   cache rather than reading as "data missing".
   - **Who:** RPA developer

3. **Process scheduling** -- if the workbook is updated by an upstream
   job, schedule `DailyPriceSync` to run only after that job has not just
   refreshed but also *saved* the workbook with the recomputed values
   (so the OpenXML cache reflects the latest data). Stale cached values
   are the upstream-refresh-then-headless-read race condition this
   playbook exists to catch.
   - **Who:** RPA developer / scheduler owner

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The `PublishedPrices.SKU` cell is a formula (VLOOKUP into the upstream `SourceFeed` sheet); the unattended robot's Excel Interop session reads a stale/empty cached value, so Lookup Range cannot match a value the cell visibly displays | High | Confirmed | Yes | `Main.xaml` has no filter; the lookup ran without throwing and returned empty; user confirms the SKU column is built by a VLOOKUP against a separate SourceFeed sheet; the user can see SKU-7392 with today's price when opening the file by hand | Convert the SKU formula column to static values (Paste Special > Values) OR migrate the lookup to Workbook `Read Range` + `Lookup Data Table` (OpenXML) |
| H2 | An active filter hides the row | Low | Rejected | No | `Main.xaml` contains no `Filter`/`FilterX` activity and no pre-step that would hide rows; user reports no filters applied | n/a |
| H3 | Wildcard / type / whitespace mismatch in the search value | Low | Rejected | No | Search value is a plain SKU literal `SKU-7392`; user confirms no extra characters; cell visibly displays the SKU when opened | n/a |

---

Would you like help editing `Main.xaml` to migrate the lookup to the
Workbook `Read Range` + `Lookup Data Table` path, or drafting the
Paste-Special-Values change in the source workbook?
