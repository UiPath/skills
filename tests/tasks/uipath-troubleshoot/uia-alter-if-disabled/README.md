# UIA AlterIfDisabled — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the agent reached a verified resolution. The fixtures are the verbatim `uip` CLI responses captured from that session.

## What the original session uncovered

`NClick "Click 'Simt că am noroc(1)'"` in `ClickCase.xaml` (process `ERN`, folder `Shared`) faulted with `UiPath.UIAutomationNext.Exceptions.UiNodeDisabledElementException` ("The target element is disabled. Operation canceled.") on host `MOCK-HOST`. The selector resolved (no `NodeNotFoundException` / timeout) — the driver found the element and aborted on its own `disabled` property.

Per the `disabled-element.md` playbook decision tree:
- Branch (A) HardwareEvents — eliminated: `InteractionMode=DebuggerApi` honors `AlterIfDisabled`.
- Branch (B) HA self-healing detected and failed to dismiss a popup — eliminated: Healing Agent was disabled on this job.
- Branch (C) HA recommendation-only inferred a popup — eliminated: Healing Agent was disabled on this job.
- Branch (D) Default — applies.

Correct fix: set `AlterIfDisabled = True` on the failing `NClick` in `ClickCase.xaml`. The leaf element's `disabled` property is the abort cause; `InputMode` honors the property, and there is no HA popup detection that would override the default.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project (`ClickCase.xaml`, `Main.xaml`, etc.) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`disabled-element.md`) AND recommended `AlterIfDisabled = True` as the primary fix per branch (D) of the decision tree (with HardwareEvents and HA-popup branches eliminated)

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name uia-alter-if-disabled --apply
```
