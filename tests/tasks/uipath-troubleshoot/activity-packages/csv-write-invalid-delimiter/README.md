# Write CSV Failure - "Failed to create a 'Delimitator' from the text 'Tab'"

This scenario reproduces a `Write CSV` failure where the `Delimiter` property is
bound to a string variable holding the **word** `"Tab"` instead of the enum value
or a character literal. The activity can't map the word to a real delimiter and
faults with `Failed to create a 'Delimitator' from the text 'Tab'`.

## What this scenario uncovers

**Root Cause:** `Delimiter="[delimiterName]"` where `delimiterName` is a `String`
= `"Tab"`. The activity expects the delimiter enum / a character, not the
localized word.

This maps to:
`references/activity-packages/csv-activities/playbooks/write-csv-invalid-delimiter.md`

The fix is a property change (pick from the dropdown, or pass the character
literal `vbTab`/`"\t"`) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project with a `Write CSV` whose `Delimiter` is bound to a `String` variable `delimiterName = "Tab"` |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the Delimiter set from a
  string/word (`"Tab"`) rather than the enum/character literal, and recommends
  selecting the delimiter from the dropdown or passing the character literal
  (`vbTab` / `"\t"`), without fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
