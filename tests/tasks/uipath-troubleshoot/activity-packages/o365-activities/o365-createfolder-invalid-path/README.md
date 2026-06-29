# O365 Create Folder Invalid Path — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_CreateFolderInvalidPath` (key
`a04406a9-4c64-40d0-a7f3-042c3224c13b`), faulted with
`UiPath.MicrosoftOffice365.Office365Exception: Folder path segment
' Quarterly' cannot have leading or trailing whitespace. (Parameter
'FolderPath')` thrown by the Create Folder (`CreateFolderConnections`)
activity in `O365_CreateFolderInvalidPath.xaml`. The package's own pre-flight
path validation in `GraphServiceClientProxy.CreateFolderByPathAsync` threw
(exception chain `Office365Exception → Office365InternalException →
ArgumentException`) before any Microsoft Graph folder operation ran — a
deterministic configuration error, not auth, not a name conflict, not a
parent-not-found. Fix: trim the whitespace-padded segment in the configured
`FolderPath` (e.g. `Reports/Quarterly`).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info/logs carry the full fault stack).

No trace spans were recorded for this job, so both trace forms (`or jobs
traces <key>` and `traces spans get --job-key <key>`) are mocked with a
well-formed empty `JobTraces` response so the agent reads "no spans" instead
of misreading a bare `[]`.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

This scenario was hand-built from the investigation's `raw/` verbatim CLI
outputs (the generator's transcript pass is unreliable for this session). If
the source investigation changes, update the fixture JSONs directly and re-run
the scrub checks, or regenerate with:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-createfolder-invalid-path --apply
```
