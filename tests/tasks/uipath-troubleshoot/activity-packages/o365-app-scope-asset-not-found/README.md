# O365 App Scope Asset Not Found — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The Microsoft 365 Scope activity in process "ERN" is configured to read its connection from an Orchestrator asset, and that asset does not resolve when the job runs in folder "Shared". The asset identifier comes back null, so connection resolution throws before any Microsoft 365 (Graph) call is ever made.

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
    --scenario-name o365-app-scope-asset-not-found --apply
```

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
