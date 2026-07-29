# Write CSV Failure - "Unsupported encoding name"

This scenario reproduces a `Write CSV` failure where the `Encoding` property is
set to a string .NET does not recognize (`utf8-bom`), so the activity faults with
`'utf8-bom' is not a supported encoding name` (`ArgumentException`).

## What this scenario uncovers

**Root Cause:** `Encoding="utf8-bom"` is not a valid .NET encoding name. The
activity calls `Encoding.GetEncoding("utf8-bom")`, which throws.

This maps to:
`references/activity-packages/csv-activities/playbooks/write-csv-unsupported-encoding.md`

The fix is a property change (use a valid .NET encoding name, leave it default,
or use Output Data Table → Write Text File) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Write CSV` whose `Encoding=utf8-bom` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the invalid `Encoding`
  string and recommends using a valid .NET encoding name (`UTF-8` /
  `Windows-1252`), leaving it default, or Output Data Table → Write Text File,
  without fabricating host actions
