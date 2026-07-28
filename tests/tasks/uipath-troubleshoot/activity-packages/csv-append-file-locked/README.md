# Append To CSV Failure - File Locked (Open in Excel)

This scenario reproduces an `Append To CSV` failure caused by a **file lock**.
The target `daily.csv` is open in Microsoft Excel on the robot host, so the
append cannot acquire exclusive write access and faults with `The process cannot
access the file ... because it is being used by another process`.

## What this scenario uncovers

**Root Cause:** `daily.csv` is held by another process (open in Excel / another
session), so `Append To CSV` cannot write to it (`System.IO.IOException`).

This maps to:
`references/activity-packages/csv-activities/playbooks/csv-file-locked-or-invalid-path.md`

The discriminator vs the other CSV playbooks: the error is a **lock**
(`being used by another process`), not a `CsvHelper` `Method not found` and not a
`DataTable` shape problem. The user is framed as **off-host**, so the correct
agent behavior is to recommend closing/killing the Excel lock holder (and/or
serializing access) - not to run host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project that Reads a CSV then `Append To CSV` to `data\daily.csv` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `csv-file-locked-or-invalid-path.md`
- Agent identified the file lock (open in Excel / held by another process) and
  recommended closing or killing the lock holder (e.g. Kill Process EXCEL before
  the append) and/or serializing access, without fabricating host actions
