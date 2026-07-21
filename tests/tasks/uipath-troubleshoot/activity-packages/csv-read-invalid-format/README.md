# Read CSV Failure - "The CSV file format for [Path] is invalid"

This scenario reproduces a `Read CSV` failure caused by **leading blank lines**
at the top of the file while `AddHeaders` is enabled. `data/feed.csv` starts with
two empty rows before the `Id,Sku,Qty` header, so `Read CSV` cannot resolve the
tabular structure and faults with `The CSV file format for 'data\feed.csv' is
invalid`.

## What this scenario uncovers

**Root Cause:** Blank initial lines shift header detection — `Read CSV` (with
`AddHeaders=True`) expects the header at the top, but finds empty rows first.

This maps to:
`references/activity-packages/csv-activities/playbooks/read-csv-invalid-format.md`

The fix is a file/property change (strip the leading blank lines; align
`Has headers`/`AddHeaders` with the file) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Read CSV` (`AddHeaders=True`) and `data/feed.csv` that has two blank lines before the header |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the leading-blank-lines
  (and/or `Has headers` mismatch) cause and recommends stripping the leading
  blank lines (and aligning `Has headers`/`AddHeaders`), without fabricating host
  actions
