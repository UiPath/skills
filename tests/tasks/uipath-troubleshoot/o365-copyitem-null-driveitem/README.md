# O365 Copy Item Null DriveItem — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_CopyItemArgNull` (key `909ed39c-08a1-48fb-921a-06d332f8f5fb`),
faulted with a raw `System.ArgumentNullException: Value cannot be null.
(Parameter 'DriveItem')` thrown by the legacy O365 `CopyItem` activity. Job
trace spans proved the binding chain: an upstream `FindFilesAndFolders`
(query `no-such-file-zzz-repro`, `First` output bound to `foundItem`) matched
nothing and left `foundItem` null; `CopyItem`'s `DriveItem` input is bound to
that same variable. Fix: correct the search criteria and/or add a null guard
between the search and the copy.

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
    --scenario-name o365-copyitem-null-driveitem --apply
```
