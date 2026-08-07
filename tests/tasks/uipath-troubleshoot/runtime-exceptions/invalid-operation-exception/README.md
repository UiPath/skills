# Invalid Operation Exception — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.InvalidOperationException` thrown from an `Assign` expression in
`Main.xaml`. The agent runs the `uipath-troubleshoot` skill against a `uip`
CLI mock and must reach the same root cause as `RESOLUTION.md`.

## What the original session uncovered

The `Assign` **Find First Over 100** in `Main.xaml` runs the LINQ expression `numbers.First(n => n > 100)`, but no element of `numbers` (`{1, 2, 3}`) is greater than 100, so `First(predicate)` throws `System.InvalidOperationException: Sequence contains no matching element.`

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | frozen snapshot of the failing UiPath project (`Main.xaml`) |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/invalid-operation-exception.md`) AND reached the same root cause as `RESOLUTION.md`

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
