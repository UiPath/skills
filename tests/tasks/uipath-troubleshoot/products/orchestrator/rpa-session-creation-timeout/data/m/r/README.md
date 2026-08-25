# Session-Creation Timeout — Host Latency Exceeds the Window

This scenario reproduces the **"Could Not Start Executor — Creating User
Session Timed Out"** playbook: an unattended job enters Running, the Robot
begins creating the Windows session, the create-session call **times out
(~120s)**, and the job faults with:

```
Could not start executor. Creating user session timed out.
```

Nothing refused the credential — session creation simply took longer than the
timeout window (a host-side latency / resource / infrastructure condition).

## What this scenario uncovers

**Root Cause:** Three identical `NightlyReconciler` runs faulted on
`RECON-BOT-01` (keys `c0ffee01-...` at 02:00Z, `c0ffee02-...` at 01:00Z,
`c0ffee03-...` at 00:00Z), each after ~120s in Running. The robot log states
the create-session call timed out and that LSA returned **no** logon rejection
— a pure session-creation timeout, not a credential or no-host fault. The fix
is to raise the session-creation timeout (`UIPATH_SESSION_TIMEOUT`) and reduce
host-side logon/resource latency — **not** a Robot-version upgrade (there is no
version-specific fix for this error).

Maps to:
`references/products/orchestrator/playbooks/job-faulted-session-timeout.md`.

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
| Discriminating fix | credential / account / RDP | raise `UIPATH_SESSION_TIMEOUT` + reduce host latency |

`no-host` / stuck-Pending is also ruled out: `jobs history` shows the job
reached **Running** before faulting, and a runtime is connected on the host.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `orchestrator/playbooks/job-faulted-session-timeout.md` and
  identified a **session-creation timeout** (create-session exceeded the ~120s
  window; LSA returned no rejection) as the root cause — not a logon failure,
  not no-host, and not a Robot-version defect.
- Conclusion proposes the playbook's resolution: **raise `UIPATH_SESSION_TIMEOUT`
  and reduce host-side logon/resource latency** (re-run as interim mitigation) —
  not a Robot-version upgrade.
