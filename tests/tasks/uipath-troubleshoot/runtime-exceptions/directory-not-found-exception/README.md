# Directory Not Found Exception — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.IO.DirectoryNotFoundException` thrown from an `Assign` expression in
`Main.xaml`. The agent runs the `uipath-troubleshoot` skill against a `uip`
CLI mock and must reach the same root cause as `RESOLUTION.md`.

## What the original session uncovered

The `Assign` **List Inbound Files** in `Main.xaml` runs `Directory.GetFiles(folderPath)` with `folderPath = "D:\Reports\2026\Inbound"`. That directory does not exist on the unattended robot host (host `MOCK-HOST`), so `Directory.GetFiles` throws `System.IO.DirectoryNotFoundException: Could not find a part of the path 'D:\Reports\2026\Inbound'.`

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | frozen snapshot of the failing UiPath project (`Main.xaml`) |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/directory-not-found-exception.md`) AND reached the same root cause as `RESOLUTION.md`

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
