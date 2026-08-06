# Maestro Stuck Rpa Job — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

Root Cause: UI selector mismatch in the child automation caused a cascading failure that left the Maestro BPMN instance permanently stuck.

## How this test reproduces it

| Layer | Source |
|---|---|

This scenario is CLI-only — there's no project source, so no `process/` directory is included. The troubleshooting is reproduced entirely from `uip` mock responses.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name maestro-stuck-rpa-job --apply
```

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
