# Uia Application Open Failed — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The "GitHub Desktop" Use Application/Browser scope in `DesktopApp.xaml` has a hard-coded `File path` pointing at a developer-machine install location — `C:\Users\original_user\AppData\Local\GitHubDesktop\app-3.5.12\githubdesktop.exe` — that does not exist on the robot machine MOCK-HOST. Because the scope is set to open the app (no `Open` mode set, so it defaults to "If not open"), it tried to launch that exact executable, the file was not there, and the scope threw `ApplicationOpenException` before any activity inside it could run.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | frozen snapshot of the failing UiPath project |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name uia-application-open-failed --apply
```

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
