# rpa-is-connection-disabled-dap — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim `uip` CLI
responses captured from that session.

## What the original session uncovered

An Orchestrator unattended job (`TokenRefreshFailedJob`) in the Solution folder
`Shared/uipath-rpa-isActivities/TokenRefreshFailed_DAPRuntime` faulted with
Integration Service error **`DAP-GE-3005` (ConnectionDisabled)** at the
`ConnectorActivity "Create Folder"` in `Main.xaml`. Despite the folder's name
("TokenRefreshFailed"), the emitted runtime code is `DAP-GE-3005`, **not**
`DAP-GE-3004` — the diagnosis must follow the evidence, not the label. The root
cause was the **Box** connection bound to that activity
(`989fd9d2-...`, in folder `b262689d-...`), which pinged as **`Failed` /
not enabled** — auto-disabled following an OAuth re-authentication failure. The
fix (re-authenticating the connection) was verified: a re-run completed
Successfully. See `RESOLUTION.md` for the full ground truth.

The test exercises the agent's ability to (a) trust the emitted DAP code over
the folder name, (b) recover the connection ID from the job's
`ResourceOverwrites`, and (c) confirm the disabled/failed connection state and
recommend re-authentication.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real `uip` stdout captured verbatim from the session |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

This investigation was purely CLI-driven (the project is a Studio Web project,
no local source), so there is **no** `process/` snapshot.

> Note: connection-state-dependent fixtures (`is connections ping 989fd9d2-...`
> and the bound-folder `is connections list --folder-key b262689d-...`) capture
> the **pre-fix `Failed` state** at investigation time — not the post-fix
> `Enabled` state the live tenant shows now.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- An LLM judge grades the agent's final answer against `RESOLUTION.md`: correct
  root cause (disabled/`Failed` Box connection → `DAP-GE-3005`) **and** correct
  fix (re-authenticate / re-enable the connection).

## Re-running the extraction

If the source transcript changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <.local/investigations dir> --transcript <session.jsonl> \
    --resolution RESOLUTION.md --scenario-name rpa-is-connection-disabled-dap --apply
```
