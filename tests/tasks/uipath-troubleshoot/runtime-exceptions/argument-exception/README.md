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
| `process/` | frozen snapshot of the failing UiPath project (`Main.xaml`) |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/argument-exception.md`) AND reached the same root cause as `RESOLUTION.md`

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
