# Maestro Stuck Rpa Job — Faithful Replay

This scenario replays a real UiPath diagnostic investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

Root Cause: UI selector mismatch in the child automation caused a cascading failure that left the Maestro BPMN instance permanently stuck.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

This scenario is CLI-only — there's no project source, so no `process/` directory is included. The diagnostic is reproduced entirely from `uip` mock responses.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name maestro-stuck-rpa-job --apply
```
