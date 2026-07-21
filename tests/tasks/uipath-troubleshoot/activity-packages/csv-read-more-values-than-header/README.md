# Read CSV Failure - "Line X contains more values than the header line"

This scenario reproduces a `Read CSV` parse failure. `data/contacts.csv` has a
3-column header (`Id,Name,Amount`) but a data row's `Amount` value is `1,250` —
an **unquoted comma inside a field**. With `Delimiter=Comma` and
`IgnoreQuotes=True`, that row parses into 4 fields, more than the 3-column
header, so `Read CSV` faults with `Line 4 contains more values than the header
line`.

## What this scenario uncovers

**Root Cause:** An unquoted comma in a data field (or, equivalently, a delimiter
that doesn't match the file) makes a row parse into more fields than the header.
`IgnoreQuotes=True` means quote characters aren't honored, so even a quoted
`"1,250"` would split.

This maps to:
`references/activity-packages/csv-activities/playbooks/read-csv-more-values-than-header.md`

The fix is a workflow/property/data change (correct `Delimiter`, honor quotes,
or Read Text File → Generate Data Table) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Read CSV` (`Delimiter=Comma`, `IgnoreQuotes=True`) and `data/contacts.csv` whose row 4 has an unquoted comma (`1,250`) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the unquoted-comma /
  delimiter-quoting parse cause and recommends the corresponding fix (correct
  `Delimiter`, honor quotes instead of `IgnoreQuotes`, quote the field, or Read
  Text File → Generate Data Table), without fabricating host actions
