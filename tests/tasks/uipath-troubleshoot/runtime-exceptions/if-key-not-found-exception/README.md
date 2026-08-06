# If Condition Key Not Found — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.Collections.Generic.KeyNotFoundException` thrown while resolving an **`If` activity
Condition** expression in `Main.xaml`. The agent runs the `uipath-troubleshoot`
skill against a `uip` CLI mock and must reach the same root cause as
`RESOLUTION.md`.

## What the original session uncovered

The `If` activity **Check Feature Enabled** in `Main.xaml` evaluates the condition `config["FeatureEnabled"] == "true"`, but the `config` dictionary only holds the key `Environment`. The key `FeatureEnabled` is absent, so resolving the `If` condition throws `System.Collections.Generic.KeyNotFoundException: The given key 'FeatureEnabled' was not present in the dictionary.` before either branch runs.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | frozen snapshot of the failing UiPath project (`Main.xaml`) |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/key-not-found-exception.md`) AND reached the same root cause as `RESOLUTION.md`

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
