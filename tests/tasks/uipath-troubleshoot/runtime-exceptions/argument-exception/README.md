# Argument Exception — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.ArgumentException` thrown from an `Assign` expression in
`Main.xaml`. The agent runs the `uipath-troubleshoot` skill against a `uip`
CLI mock and must reach the same root cause as `RESOLUTION.md`.

## What the original session uncovered

The `Assign` **Parse Day Of Week** in `Main.xaml` runs `Enum.Parse(typeof(DayOfWeek), inputDay)` where `inputDay` is `"Funday"`. `"Funday"` is not a defined `DayOfWeek` name, so `Enum.Parse` throws `System.ArgumentException: Requested value 'Funday' was not found.`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project (`Main.xaml`) |
| `fixtures/mocks/responses/*.json` | recorded `uip or` stdout: folder list, faulted job, error logs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/argument-exception.md`) AND reached the same root cause as `RESOLUTION.md`
