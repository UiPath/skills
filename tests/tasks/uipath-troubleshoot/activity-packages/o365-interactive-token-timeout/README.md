# O365 Interactive Token Timeout — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The Microsoft 365 Scope in the **ERN** process is configured for **Interactive Token** authentication (no account bound — the Account field still reads "Please select an account.", Integration Service off), which is the wrong and fragile auth choice for this Agent/StudioPro execution context. Interactive Token requires a human to complete a browser sign-in within a 30-second window; in this no-bound-account agent run nobody completed it, so authentication timed out and the job faulted. Switch the scope to app-only authentication (Application ID + Client Secret, or Application ID + Certificate).

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
    --scenario-name o365-interactive-token-timeout --apply
```
