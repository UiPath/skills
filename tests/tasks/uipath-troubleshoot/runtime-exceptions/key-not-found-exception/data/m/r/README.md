# Key Not Found Exception — Faithful Replay

This scenario replays a UiPath diagnostic investigation where an Orchestrator
job faulted with `System.Collections.Generic.KeyNotFoundException` thrown from an `Assign` expression in
`Main.xaml`. The agent runs the `uipath-troubleshoot` skill against a `uip`
CLI mock and must reach the same root cause as `RESOLUTION.md`.

## What the original session uncovered

The `Assign` **Read Api Base Url** in `Main.xaml` indexes `config["ApiBaseUrl"]`, but the `config` dictionary only holds the keys `Environment` and `Timeout`. The key `ApiBaseUrl` is absent, so the dictionary indexer throws `System.Collections.Generic.KeyNotFoundException: The given key 'ApiBaseUrl' was not present in the dictionary.`

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
- Agent matched the correct playbook (`references/runtime-exceptions/playbooks/key-not-found-exception.md`) AND reached the same root cause as `RESOLUTION.md`
