# rpa-is-connection-missing-dap — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim `uip` CLI
responses captured from that session.

## What the original session uncovered

An Orchestrator unattended job (`TokenRefreshFailedJob`) in the Solution folder
`Shared/uipath-rpa-isActivities/TokenRefreshFailed_DAPRuntime` faulted with
Integration Service error **`DAP-GE-3000` (FailedToGetConnection)** at the
`ConnectorActivity "Create Folder"` in `Main.xaml`. The root cause: the **Box**
connection the process is bound to (`989fd9d2-…`, in folder `b262689d-…`) had
been **deleted** — `ping` returns **HTTP 404**, the bound folder now contains
only the Freshdesk connection, and no Box connection exists tenant-wide. Because
the published process still references the deleted connection ID, IS cannot
resolve it.

This is the *deleted-connection* variant of the connection-not-resolved family —
distinct from a *disabled* connection (`DAP-GE-3005`): there the connection still
exists and can be re-authenticated; here it is gone, so the fix is to **create a
new connection** and **re-bind + republish** the process. (See the sibling
scenario `rpa-is-connection-disabled-dap` for the `DAP-GE-3005` case.) Per the
ground truth, after creating the new Box connection and re-binding, the re-run
completes Successfully. See `RESOLUTION.md`.

The test exercises the agent's ability to (a) trust the emitted DAP code over the
folder name, (b) recover the connection ID from the job's `ResourceOverwrites`,
(c) distinguish *deleted* (404) from merely *disabled*, and (d) recommend
create-new + rebind rather than re-authenticate.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real `uip` stdout captured verbatim from the session |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

This investigation was CLI-driven against a Studio Web project (no local source),
so there is **no** `process/` snapshot.

> Note: state-dependent fixtures (`jobs list`, `is connections ping 989fd9d2-…`,
> the bound-folder `is connections list --folder-key b262689d-…`, and the
> tenant-wide `is connections list`) capture the **pre-fix** state at
> investigation time: connection `989fd9d2-…` deleted (404), no Box connection
> present, and `c3a00022-…` as the latest faulted job.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- An LLM judge grades the agent's final answer against `RESOLUTION.md`: correct
  root cause (deleted/missing Box connection → `DAP-GE-3000`, not merely
  disabled) **and** correct fix (create a new connection + re-bind + republish).

## Re-running the extraction

If the source transcript changes, regenerate the scaffold, then re-apply the
scenario-scoped manifest and the pre-fix state-dependent fixtures:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <.local/investigations dir> --transcript <session.jsonl> \
    --resolution RESOLUTION.md --scenario-name rpa-is-connection-missing-dap --apply
```
