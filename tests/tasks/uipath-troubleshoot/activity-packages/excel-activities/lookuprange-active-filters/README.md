# Lookup Range Failure - Value Not Found Behind an Active Filter

This scenario reproduces a `Lookup Range` "value not found" failure where
the searched value is physically present in the sheet but hidden by an
**active AutoFilter** that the workflow applied earlier. Lookup Range
searches only visible cells, so the filtered-out row is invisible to it.

## What this scenario uncovers

**Root Cause:** `Main.xaml` applies a Filter activity ("Filter Status =
Active") to the `Prices` sheet before the `Lookup Range` runs. The target
`SKU-8842` has Status "Discontinued", so the active filter hides its row.
Lookup Range returns empty, and the workflow's guard throws
`SKU-8842 not found in price list`. The value is genuinely present - it
is filtered out, not absent.

This maps to:
`references/activity-packages/excel-activities/playbooks/lookup-range-active-filters.md`

The Filter-before-Lookup ordering is **discoverable in Main.xaml**, so
this is a local investigation with a definite answer (no need to read the
binary workbook).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/Main.xaml` | Use Excel File -> Filter (Status = Active) -> Lookup Range (SKU-8842) -> Throw-if-empty |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `lookup-range-active-filters.md`
- Agent identified the active filter (applied before the lookup) as why a
  present value is not matched, and recommended clearing/resetting the
  filter before the lookup
