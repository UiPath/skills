# Write CSV Failure - "Access to the path is denied"

This scenario reproduces a `Write CSV` failure with `Access to the path
'...published.csv' is denied` (`UnauthorizedAccessException`). The output file is
read-only, open in Microsoft Excel, or in a folder the robot user cannot write
to.

## What this scenario uncovers

**Root Cause:** The robot cannot write the output file — permissions / read-only
attribute / an open Excel handle.

This maps to:
`references/activity-packages/csv-activities/playbooks/write-csv-access-denied.md`

The discriminator vs the file-lock playbook: this is `Access ... is denied`
(permissions/read-only/open-in-Excel), **not** `being used by another process`.
The fix is closing Excel / clearing read-only / granting write — not a host
command run by the agent.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project that reads a staging CSV and `Write CSV` to `data\published.csv` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the access-denied cause
  (permissions / read-only / open in Excel) and recommends closing/Kill Process
  EXCEL, clearing read-only, or granting the robot Read/Write (or writing to a
  writable path), without fabricating host actions
