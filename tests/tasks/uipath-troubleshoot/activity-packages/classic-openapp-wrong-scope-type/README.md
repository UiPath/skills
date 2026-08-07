# Classic Openapp Wrong Scope Type — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The classic UI Automation scope `Open Application 'msedge.exe Google'` in `Workflow.xaml` is the wrong scope type for its target. It is a **desktop** Open Application (launching `chrome.exe`) but was given a **browser-style** html selector with no application window, so it never produces a usable context window. Its child `Click 'push button'` faults the instant the scope hands it an uninitialized window — before the Click's own (valid) selector is ever evaluated.

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
    --scenario-name classic-openapp-wrong-scope-type --apply
```

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
