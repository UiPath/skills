# Lookup Range Failure - Invalid Range (Empty-String Literal)

This scenario reproduces a classic `Lookup Range` failure caused by the
**`Range` property being set to a literal empty string `""`** instead of
being left blank. For `Lookup Range`, a whole-sheet search is expressed by
leaving the `Range` field **completely empty** (no value at all); a literal
`""` is an *invalid range value* and faults the activity with
`The range '' is not valid` once the workbook is open.

## What this scenario uncovers

**Root Cause:** In `Main.xaml`, the `Lookup Range` activity has
`Range="&quot;&quot;"` - the C# expression `""`, which evaluates to an
empty string. The `Excel Application Scope` opens `Catalog.xlsx`
successfully, then the `Lookup Range` faults at the range parse step
because `""` is not a valid range. The whole-sheet search the workflow
intends requires a **blank** `Range` field, not the empty-string literal.

This maps to:
`references/activity-packages/excel-activities/playbooks/lookup-range-invalid-range.md`

The empty-string-vs-empty-field distinction is the single most common form
of this failure, and it is discoverable in `Main.xaml`: the scope opens
fine (the log shows "Workbook opened"), then the `Lookup Range` errors with
`The range '' is not valid`, and the activity's `Range` is set to the
literal `""`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a classic `Excel Application Scope` + `Lookup Range` whose `Range` is set to `""` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `lookup-range-invalid-range.md`
- Agent identified the `Range` set to a literal empty string `""` (rather
  than left blank) as the cause, found in `Main.xaml`, and recommended
  clearing the `Range` field entirely for a whole-sheet search (or setting
  a valid A1 reference)
