# If Condition Null Reference — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.NullReferenceException` thrown while resolving an **`If` activity
Condition** expression in `Main.xaml`. The agent runs the `uipath-troubleshoot`
skill against a `uip` CLI mock and must reach the same root cause as
`RESOLUTION.md`.

## What the original session uncovered

The `If` activity **Check Status Is Yes** in `Main.xaml` evaluates the condition `status.ToString() == "yes"`, but `status` is `null` — the upstream `Assign` **Set Status** sets it to `null`. Resolving the `If` condition calls `.ToString()` on the null reference, throwing `System.NullReferenceException` before either branch runs.

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
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/null-reference-exception.md`) AND reached the same root cause as `RESOLUTION.md`
