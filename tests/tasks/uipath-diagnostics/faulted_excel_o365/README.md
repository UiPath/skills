# Faulted ExcelO365 Diagnostic — Faithful Replay

This scenario replays a real UiPath diagnostic investigation (Claude Code
session `2d419eb2-70da-46d0-9c20-770bd5c5dc03.jsonl`) where an Excel-O365
RPA Workflow process was failing in Orchestrator.

## What the original session uncovered

The user reported a failing job in their personal Orchestrator folder
(numeric ID `1321239`). The agent — using the `uipath-diagnostics` skill
— iterated through several `uip` invocations:

1. `uip or jobs list --folder-id 1321239 …` → `ValidationError: unknown option '--folder-id'`
2. Corrected to `--folder-key 1321239` → `Failure: Invalid folder key: '1321239'. Expected a UUID …`
3. Tried `uip or folders get 1321239` → `Failure: Folder not found`
4. Tried filtering `folders list` by `Id`, `ID`, by name "personal", and the runner's username → no match
5. Tried `--folder-path "Personal/1321239"`, `"My Workspace"` → all fail

The agent's eventual conclusion: **personal-workspace folders aren't
returned by the standard `folders list` API**, so a numeric folder ID
isn't enough — the agent needs the folder's GUID key from the user.

The session ended with the agent stating it needed the user to supply
the personal-folder GUID before the investigation could proceed.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../mock_template/` (manifest-driven Python dispatcher) |
| `RPA Workflow/`, `ExcelO365.uipx`, `SolutionStorage.json`, `resources/`, `userProfile/` | frozen snapshot of the failing process (in `process/`) |
| `mocks/responses/*.txt` | **real** stdout extracted verbatim from the JSONL transcript (33 fixtures) |
| `mocks/responses/manifest.json` | dispatch table mapping each command pattern to its real-recorded fixture |

The `uip` mock returns the exact stdout (and exit code) that the real
`uip` returned during the original session — including the
`[ERROR] Failed to load tool test-manager-tool …` stderr noise the
real CLI was emitting, and the genuine Orchestrator error envelopes
(`{"Result": "ValidationError", …}`).

## Success criteria

The test scores the **conclusion**, not the trajectory:

- `diagnosis.md` exists (the agent reached *some* terminal state)
- It mentions `personal` and `folder` (correctly identified the locus)
- It mentions `GUID` (correctly identified what's needed)
- `.investigation/state.json` exists (the diagnostic skill actually ran)
- The agent invoked the `uipath-diagnostics` skill

## Re-running the extraction

If the source transcript is updated, regenerate the fixtures:

```bash
python tmp/extract_uip_fixtures.py
```

This rewrites `fixtures/mocks/responses/*.txt` and `_exit_codes.json`.
The manifest is hand-curated; revisit `manifest.json` after a re-extract.

## Adding new scenarios

This scenario shows the per-folder pattern: `mocks/responses/manifest.json`
plus per-fixture files, layered with the shared dispatcher and a process
snapshot. To add a new scenario, copy the folder structure and edit the
manifest, fixtures, and prompt.
