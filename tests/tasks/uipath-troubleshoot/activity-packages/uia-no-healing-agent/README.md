# No Healing Agent — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** Authoring-time corruption of the click target's `aria-label` selector attribute — the value `'Simt că am noroccccccccccc'` (ten extra `c` characters appended) does not match any real element on the Google homepage, so the Click activity cannot resolve its target and faults.

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
    --scenario-name no-healing-agent --apply
```

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
