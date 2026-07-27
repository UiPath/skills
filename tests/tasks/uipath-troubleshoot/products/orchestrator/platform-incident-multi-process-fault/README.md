# Platform Incident — Many Jobs Fault at Once

Reproduces the `platform-incident-correlation` playbook: a burst of
failures across multiple unrelated processes and folders in a tight
window, with Orchestrator-side infrastructure errors — the
fingerprint of a UiPath platform incident, not a single automation's
bug.

## What this scenario uncovers

**Root Cause:** A platform incident around 08:12–08:17. Five distinct
processes across three folders (`NightlyBilling`/Billing,
`ClaimIntake`/ClaimsOps, `PayrollSync`/HRBots,
`InvoiceMatcher`/Billing, `OnboardingBot`/HRBots) all fault in a
5-minute window with `503 Service Unavailable` / `Could not obtain
the user token from Orchestrator` (`ErrorCode: Orchestrator`). No
shared automation dependency. The correct move is to correlate with
status.uipath.com / known-issues and monitor + rerun + report — not
debug the individual automations.

Maps to:
`references/products/orchestrator/playbooks/platform-incident-correlation.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal project for one victim process (`NightlyBilling`) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses — a cross-folder `jobs list --state Faulted` burst, plus `jobs get` on two unrelated victims showing Orchestrator-side infra errors |
| `data/m/r/manifest.json` | dispatch table (folder NOT pinned — the fault is widespread) |

> Fixtures authored from the playbook signature, not captured from a
> real session. Note the sandbox has no live status.uipath.com; the
> graded deliverable is the **recommendation** to correlate with the
> status page + known-issues and monitor/rerun/report.

## Distinguishing fingerprint

No single Info gives the answer — the diagnosis emerges only from the
**fan-out pattern** (many unrelated processes, three folders, one
short window, Orchestrator-side infra errors). An agent that latches
onto one job's 503 and debugs that automation scores low; one that
recognizes the platform-incident pattern and recommends status-page
correlation + monitor/rerun/report scores full. Inherently
bypass-resistant.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified a platform incident from the cross-folder fan-out
  (not a single-automation bug) and recommended correlating with
  status.uipath.com / known-issues, monitoring, rerunning after
  recovery, and reporting via the customer portal — rather than
  debugging the individual jobs.
