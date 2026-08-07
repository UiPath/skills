# Copy File Failure — Destination Already Exists

This scenario replays a real faulted Orchestrator job where the
`Copy File` activity targets a destination path that already exists and
its Overwrite option is off. The modern file activity surfaces the raw
`System.IO.IOException: The file '...' already exists.` instead of a
UiPath `FileSystemException`.

## What this scenario uncovers

**Root Cause:** `Copy File` writes to
`C:\AutomationData\Ledger\archive\ledger_2026.txt`, which already exists,
and Overwrite is off. `System.IO.File.Copy` throws
`IOException: ... already exists.` The failure is a destination conflict,
not a missing source or a permissions problem.

This maps to:
`references/activity-packages/system-activities/playbooks/file-folder-operation-failed.md`
(the "Destination already exists" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | snapshot of the failing UiPath project (`Main.xaml` + `project.json`) |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Specifically, the agent must name the destination-exists + Overwrite-off conflict, not a source-missing or permissions failure

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
