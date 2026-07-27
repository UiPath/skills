# Session-Creation Timeout — Known Robot Defect (< 23.10)

This scenario reproduces the **"Could Not Start Executor — Creating User
Session Timed Out"** playbook's **cause 1**: the unattended Robot on the
host runs a version earlier than 23.10, which carries a known
session-creation-timeout defect (fixed in Robot 23.10). Every job enters
Running, the Robot begins creating the Windows session, the create-session
call times out (~120s), and the job faults with:

```
Could not start executor. Creating user session timed out.
```

## What this scenario uncovers

**Root Cause:** Three identical `NightlyReconciler` runs faulted on
`RECON-BOT-01` (keys `c0ffee01-...` at 02:00Z, `c0ffee02-...` at 01:00Z,
`c0ffee03-...` at 00:00Z), each after ~120s in Running. `machines list`
shows `RECON-BOT-01` has one connected Robot at `robotVersions.version =
23.4.7` — earlier than the 23.10 fix. The robot log states the create-session
call timed out and that LSA returned **no** logon rejection.

Maps to:
`references/products/orchestrator/playbooks/job-faulted-session-timeout.md`
(cause 1 — known Robot defect on versions < 23.10).

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | minimal background-unattended UiPath project (LogMessage + Delay) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `data/m/r/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** These fixtures were authored from the documented
> playbook signature, not captured from a real `.local/investigations/`
> session. Regenerate from a real failed-job session before treating this
> test's score as a hard regression signal.

## How this differs from the sibling "Could not start executor" playbook

`job-faulted-logon-failure` and this playbook both start with
`Could not start executor`. The agent must pick the right one:

| Signal | `job-faulted-logon-failure` | `job-faulted-session-timeout` *(this)* |
|---|---|---|
| Error phrasing | `Logon failed for user` / `account is locked` / `RDP connection failed` | `Creating user session timed out` |
| Windows code | `0x0000052E` / `0x00000775` / `0x00000532` / `131092` | none — a pure timeout |
| LSA verdict | active rejection | no rejection; create-session call timed out |
| Duration | sub-second (immediate refusal) | ~ the session-creation timeout (~120s) |
| Discriminating fix | credential / account / RDP | upgrade Robot to ≥ 23.10 |

`no-host` / stuck-Pending is also ruled out: `jobs history` shows the job
reached **Running** before faulting, and a runtime is connected on the host.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `orchestrator/playbooks/job-faulted-session-timeout.md` and
  named the **Robot version < 23.10 defect (23.4.7 on RECON-BOT-01)** as the
  root cause — not a logon failure, not no-host.
- Conclusion proposes the playbook's resolution: **upgrade the Robot to
  ≥ 23.10** (with re-run as interim mitigation).
