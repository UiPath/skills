# No Login Pending — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim `uip`
CLI responses captured from that session.

## What the original session uncovered

A user reported their last job in the Shared folder was stuck in `Pending`
and never started. The agent discovered exactly one Pending job there
(`0fd7bea5-…`, process ERN, Unattended) whose `PendingReasons.ErrorCodes`
was `["RobotNoMatchingUsernames"]` — the robot account's credential-store
username did not match any machine-user mapping on the eligible machine
template (`DanLaptopNew`). The fix is to align the robot credentials with
the machine user, assign a matching account to the folder, or run the job
under a different account.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

(No `process/` snapshot — this investigation is purely CLI-driven; no
project source was read.)

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- The agent's presented resolution names `RobotNoMatchingUsernames` /
  credential-mismatch as the root cause and recommends one of the three
  documented remediations in `robot-credentials.md`, without falling for
  the no-host / stale-dispatch / license-exhaustion misreads

## Re-running the extraction

If the source transcript changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> \
    --scenario-name no-login-pending --apply
```
