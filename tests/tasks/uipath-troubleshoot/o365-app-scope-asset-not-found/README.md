# O365 App Scope Asset Not Found — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The Microsoft 365 Scope activity in process "ERN" is configured to read its connection from an Orchestrator asset, and that asset does not resolve when the job runs in folder "Shared". The asset identifier comes back null, so connection resolution throws before any Microsoft 365 (Graph) call is ever made.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

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
