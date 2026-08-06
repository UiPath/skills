# Compress/Extract Files Failure — Corrupt Archive

This scenario replays a real faulted Orchestrator job where the
`Extract/Unzip Files` activity cannot open its input ZIP. Orchestrator
surfaces a `CompressionException: Cannot extract data from archive`, and
the inner exception (`ICSharpCode.SharpZipLib.Zip.ZipException: Cannot
find central directory`) proves the file is not a valid, complete ZIP.

## What this scenario uncovers

**Root Cause:** The file at
`C:\AutomationData\Invoices\batch_2026.zip` is not a valid/complete ZIP —
its central-directory record is missing. `Extract/Unzip Files` cannot
open it, so the `InvoiceIntake` job faults.

This maps to:
`references/activity-packages/system-activities/playbooks/compress-extract-files-failed.md`
(the "Cannot extract data from archive" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | snapshot of the failing UiPath project (`Main.xaml` + `project.json`) |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Specifically, the agent must name the archive as corrupt/incomplete (missing central directory), not a permissions or missing-file problem

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
