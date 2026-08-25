# Lookup Range Failure - Silent Miss Against a Formula Cell

This scenario reproduces a `Lookup Range` "value not found" failure where the
searched value is physically present in the sheet but the target cell is the
**computed result of an Excel formula** (a cross-sheet VLOOKUP). The classic
Interop read returns the cell's cached calculated value; when the cache is
stale or empty under the unattended robot's headless Excel session, the
lookup returns empty even though the cell visibly displays the SKU when
opened by hand.

## What this scenario uncovers

**Root Cause:** `Main.xaml` runs a classic `Lookup Range`
(`UiPath.Excel.Activities.ExcelLookUpRange`) inside an `Excel Application
Scope` on the `PublishedPrices` sheet of `DailyPrices.xlsx`. There is **no
filter** in the workflow. The `PublishedPrices.SKU` column is built by a
formula -- a VLOOKUP against an upstream `SourceFeed` sheet refreshed by a
separate job. Excel's Interop API returns the cell's *cached* calculated
value; for a freshly-recomputed cross-sheet VLOOKUP the cache can be stale
or empty in the robot's headless session, so the Interop read returns no
value and `Lookup Range` cannot match `SKU-7392`. The workflow's guard then
throws "not found". The value is genuinely present in the sheet -- the
Interop read of the formula's cached value just does not see it.

This maps to:
`references/activity-packages/excel-activities/playbooks/lookup-range-formula-cells.md`

The cause is **partly discoverable in Main.xaml** (absence of any filter
rules out the active-filters playbook) and **partly via the user** (the
persona confirms the SKU column is a VLOOKUP when the agent asks how the
column is populated).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/Main.xaml` | Excel Application Scope -> Lookup Range (SKU-7392) -> Throw-if-empty (no filter) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `lookup-range-formula-cells.md`
- Agent identified the formula/cache cause (cell's calculated value, Interop
  reads cached value that is stale/empty) and recommended either converting
  formulas to static values (Paste Special > Values) OR migrating to the
  Workbook `Read Range` + `Lookup Data Table` (OpenXML) path
