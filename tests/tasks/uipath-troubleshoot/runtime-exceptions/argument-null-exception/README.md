# Argument Null Exception — Faithful Replay

This scenario replays a real UiPath diagnostic investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

Root Cause: An explicit `null` literal is assigned to the variable bound to the Copy File activity's Path (and Destination) in Main.xaml, so the activity passes null to `new DirectoryInfo(...)`, which throws `System.ArgumentNullException`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | frozen snapshot of the failing UiPath project |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name argument-null-exception --apply
```

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
