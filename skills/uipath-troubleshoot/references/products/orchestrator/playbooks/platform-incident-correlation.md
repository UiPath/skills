---
confidence: medium
---

# Platform Incident Correlation — Many Jobs Fault at Once

## Context

Applies to **any** job type (RPA, Agent, Maestro, AgentHub, API Workflow). When a burst of failures hits **multiple unrelated processes across multiple folders in a tight time window** — especially with infrastructure-flavored errors and often self-recovering — the cause is usually a **UiPath platform incident**, not a bug in any one automation. Chasing a single job's root cause here wastes the investigation.

What this looks like (the fan-out fingerprint):
- Many DISTINCT processes / DIFFERENT folders fault inside a short window (minutes), not one process failing repeatedly
- Infrastructure-flavored errors, e.g.:
  - `503 Service Unavailable` / `The remote server returned an error: (503)`
  - `Could not obtain the user token from Orchestrator`
  - `connection reset` / gateway / timeout talking to Orchestrator or a shared service
- Failures start and stop together; jobs succeed again after the window
- No common automation dependency links the affected processes

What can cause it:
- A UiPath cloud/Orchestrator platform incident (identity, gateway, storage, or regional outage)
- A tenant-wide dependency blip (Identity Server, LLM Gateway, Integration Service)

Do NOT mistake this for: a single automation's logic bug, one robot's credential problem, or one machine's session issue — those are scoped to one process/robot/folder, not fanned out across many.

## Investigation

1. Establish the fan-out — list faulted jobs across folders in the reported window:
   `uip or jobs list --state Faulted --output json` (cross-folder; add `--created-after/--created-before` to bound the window). Count DISTINCT `ProcessName` / `FolderName`. Many unrelated automations in a tight window ⇒ suspect platform.
2. Confirm the error shape on a sample:
   `uip or jobs get <job-key> --output json` on two or three of the affected jobs — infrastructure errors (503 / token / gateway), not automation-logic exceptions, and different processes carrying the SAME class of error.
3. Correlate with platform status:
   - Check **status.uipath.com** for a reported incident overlapping the failure window (region/service).
   - Check the customer-portal **known-issues** feed for a matching active issue.
4. Rule out a shared automation dependency: if all affected processes DO share one dependency (same queue, same connection, same asset), that shared dependency — not a platform incident — may be the cause; investigate it instead.

## Resolution

- **If a platform incident overlaps the window:** do NOT debug the individual automations. Monitor status.uipath.com for resolution, rerun the affected jobs after the incident clears, and — if the incident is not already listed — report it via the customer portal with the correlated job evidence (timestamps, affected processes, error text). Communicate to stakeholders that this is a platform-side outage, not an automation defect.
- **If NO incident is listed but the errors are infrastructure-type and fanned out:** escalate to UiPath Support with the correlated evidence (the cross-folder fault list + sample errors + window) rather than filing per-automation bugs.
- **If the failures actually share one automation dependency:** drop the platform hypothesis and investigate that dependency (queue/connection/asset) with the relevant playbook.

Prevention:
- Alert on cross-folder fault bursts (N distinct processes faulting within a short window) — this is the platform-incident signal.
- Build rerun/resume handling so jobs caught in a transient platform outage can be replayed cleanly after recovery.
