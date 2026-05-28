# No Login Pending — Faithful Replay

This scenario replays a real UiPath diagnostic investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

A user reported that their `ERN` process in the Shared folder was stuck in
`Pending` and would not start. The job's `PendingReasons` carried no-host
error codes (`TemplateNoHostsAvailable` etc.), but the `danVM` machine
template already had a connected, licensed, idle Unattended runtime and
`JobHistory` showed only the original Pending entry. The codes were a **stale
snapshot** captured at dispatch time that Orchestrator never re-evaluated —
the fix is to stop and re-trigger the job. The scenario deliberately includes
two traps: `licenses info` reads `Used == Allowed` (the connected runtime's own
slot, not exhaustion) and the PendingReasons text says "none connected to this
folder" (the dispatch-time verdict, not a folder-assignment gap).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- The agent's presented resolution reaches the same root cause (stale
  dispatch-time PendingReasons) and fix (stop + re-trigger) as `RESOLUTION.md`,
  without falling for the license-exhaustion or folder-assignment traps

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name no-login-pending --apply
```
