# Final Resolution

---

**Root Cause:** A **UiPath platform incident** (Orchestrator-side
service disruption) around `08:12–08:17` — **not** a bug in any one
automation. Five distinct processes across three unrelated folders
all faulted within a ~5-minute window, each with an
infrastructure-flavored error returned by Orchestrator (`503 Service
Unavailable`, `Could not obtain the user token from Orchestrator`).
This cross-folder fan-out of unrelated automations with
Orchestrator-side infra errors is the platform-incident fingerprint,
per the `platform-incident-correlation` playbook.

**What went wrong:** In the reported window,
`uip or jobs list --state Faulted` returns five faulted jobs across
**three folders**: `NightlyBilling` (Billing, 503),
`ClaimIntake` (ClaimsOps, could-not-obtain-user-token),
`PayrollSync` (HRBots, 503), `InvoiceMatcher` (Billing, 503-class),
`OnboardingBot` (HRBots, token). The processes share no automation
dependency; the only thing in common is the time window and the
Orchestrator-side error class.

**Why:** Sampled `jobs get` on two unrelated jobs confirms
infrastructure errors, not automation-logic exceptions:
`NightlyBilling` → `The remote server returned an error: (503)
Server Unavailable` (`ErrorCode: Orchestrator`); `ClaimIntake` →
`Could not obtain the user token from Orchestrator` (`ErrorCode:
Orchestrator`). The billing job's log shows an HTTP 503 from the
Orchestrator gateway. Many unrelated automations failing
simultaneously with Orchestrator gateway/token errors points at a
platform-side outage, not per-automation defects.

**Ruled out:**
- **Single-automation bug** — five different processes in three
  folders fail together; no one workflow is common.
- **One robot / one credential / one machine** — the failures span
  different machines (MOCK-HOST, MOCK-HOST-2) and serverless (no
  machine), different accounts, different folders.
- **Shared automation dependency** — the affected processes do not
  share a queue/connection/asset; the common factor is Orchestrator
  itself in a tight window.

---

**Evidence:**

### Orchestrator
- `uip or jobs list --state Faulted` (cross-folder, window
  `08:12–08:17`): 5 faulted jobs — `NightlyBilling` (Billing),
  `ClaimIntake` (ClaimsOps), `PayrollSync` (HRBots),
  `InvoiceMatcher` (Billing), `OnboardingBot` (HRBots)
- `jobs get` NightlyBilling: `Info = The remote server returned an
  error: (503) Server Unavailable`, `ErrorCode: Orchestrator`
- `jobs get` ClaimIntake (different folder/process): `Info = Could
  not obtain the user token from Orchestrator`, `ErrorCode:
  Orchestrator`
- `jobs logs` NightlyBilling: `Received HTTP 503 from Orchestrator
  gateway while requesting job start; upstream service temporarily
  unavailable`
- No shared automation dependency across the five processes; common
  factor is the time window + Orchestrator-side error class

---

**Immediate action (do NOT debug the individual automations):**

1. **Correlate with platform status.**
   - Check **status.uipath.com** for a reported incident overlapping
     `08:12–08:17` (region / Orchestrator / Identity), and the
     customer-portal **known-issues** feed for a matching active
     issue.
   - **Source:**
     `products/orchestrator/playbooks/platform-incident-correlation.md`

2. **Monitor, then rerun after recovery.**
   - Wait for the incident to clear on the status page, then rerun
     the affected jobs (they failed on transient infra errors, not
     logic).

3. **Report + communicate.**
   - If the incident is not already listed, report it via the
     **customer portal** with the correlated evidence (window,
     affected processes/folders, error text). Tell stakeholders this
     is a platform-side outage, not an automation defect.

4. **If status.uipath.com shows NO incident** but the errors remain
   infrastructure-type and fanned out, escalate to UiPath Support
   with the cross-folder fault list rather than filing per-automation
   bugs.

---

**Preventive fix:**

1. **Monitoring** — Alert on cross-folder fault bursts (N distinct
   processes faulting within a short window) — the platform-incident
   signal — so this is recognized immediately.
2. **Resilience** — Add rerun/resume handling so jobs caught in a
   transient platform outage can be replayed cleanly after recovery.
   - **Source:**
     `products/orchestrator/playbooks/platform-incident-correlation.md`
     (Prevention)

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | UiPath platform incident (Orchestrator-side) during 08:12-08:17 | High | Confirmed | Yes | 5 unrelated processes across 3 folders faulted in a 5-min window; jobs get shows 503 / could-not-obtain-token with ErrorCode Orchestrator; no shared automation dependency | Correlate with status.uipath.com / known-issues; monitor, rerun after recovery, report via customer portal |
| H2 | A single automation's logic bug | Low | Refuted | No | Five different processes in three folders fail together; no common workflow | n/a |
| H3 | One robot / credential / machine issue | Low | Refuted | No | Failures span multiple machines, serverless, accounts, folders | n/a |
| H4 | Shared automation dependency (queue/connection/asset) | Low | Refuted | No | Affected processes share no such dependency; common factor is Orchestrator in a tight window | n/a |

---

Would you like help pulling the exact affected-job list for the
incident report, or setting up a cross-folder fault-burst alert?
