# O365 Download File Folder Item — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_DownloadConversion` (key `64580780-4aa1-4ec2-b5f2-abd5439ea200`),
faulted with `UiPath.MicrosoftOffice365.Office365Exception: Folders cannot be
downloaded with this activity. Please input a different DriveItem.` thrown by
the legacy O365 `DownloadFile` activity. Job trace spans proved the binding
chain: an upstream `FindFilesAndFolders` ("Find a folder by name", query
`Documents`, `First` output bound to `foundFolder`) found the OneDrive folder
'Documents'; `DownloadFile` was invoked with `File = foundFolder`,
`LocalFilePath = C:\Temp` — a folder bound where a file is required. The
scope and the find activity completed normally (auth and permissions fine).
Fix: point the activity at a file DriveItem, and/or iterate the folder's
contents (For Each File/Folder) downloading per file; a type guard between
the search and the download prevents recurrence.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job traces carried the variable-binding chain).

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

If the source investigation changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-download-folder-item --apply
```
