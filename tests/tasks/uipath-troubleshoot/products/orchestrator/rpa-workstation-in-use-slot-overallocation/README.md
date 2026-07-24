# Workstation In Use — Machine-Template Slot Over-Allocation

Reproduces branch 3 of the **Could Not Start Executor — Session /
Console / Slot Contention** playbook: a machine template exposes
more unattended runtime slots than the host can physically seat as
concurrent RDP sessions. Under peak concurrency the extra job faults
with:

```
Could not start executor. The workstation is in use by another user.
Please retry after the user logs off or disconnects.
```

## What this scenario uncovers

**Root Cause:** `ClaimsRuntimeTemplate` is configured with 4
unattended runtime slots but is bound to a single workstation
(`MOCK-HOST`) that seats only 2 concurrent RDP sessions. During the
09:00–09:30 peak, two other jobs (`InvoiceMatcher`,
`MailDispatcher`, distinct accounts) hold both slots; the third
concurrent dispatch — `PolicyRenewalWorker` — is refused a session
and faults ~1s after start. Two PolicyRenewalWorker runs faulted
identically at 09:05 and 09:12.

Maps to:
`references/products/orchestrator/playbooks/job-faulted-session-console-contention.md`
(branch 3 — machine-template slot over-allocation).

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` (manifest-driven dispatcher) |
| `process/` | minimal unattended UiPath project (LogMessage + Delay) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `data/m/r/manifest.json` | dispatch table mapping each command to its fixture |

> Fixtures are authored from the documented playbook signature, not
> captured from a real `.local/investigations/` session. Regenerate
> via `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating the score as a strict regression signal.

## Distinguishing fingerprints

| Branch / playbook | Fingerprint that rules it out here |
|---|---|
| Logon failure | No `Logon failed` / `0x0000052E` / locked code; log says credential validated. |
| Session-creation timeout | Two sessions WERE created on the same host at the same moment — host is out of seats, not slow. |
| **Slot over-allocation (branch 3)** *(this scenario)* | Template `Runtimes: 4` on a host that seats 2; 2 jobs Running when the 3rd faults. |
| Console contention (branch 2) | `LoginToConsole: false` on the robot user. |
| Single-interactive-job-per-user (branch 1) | Concurrent seated jobs run as different accounts, not the failing account. |

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified machine-template slot over-allocation (4 slots vs
  2 seatable sessions on MOCK-HOST) as the root cause and
  recommended reducing the template slot count (or scaling out
  hosts), then rerunning.
