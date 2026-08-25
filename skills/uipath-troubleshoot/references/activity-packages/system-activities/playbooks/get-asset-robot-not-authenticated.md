---
confidence: medium
---

# Get Asset Failed — Robot Not Authenticated

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` activity
failed because the robot's Orchestrator API call was rejected as **not
authenticated** (HTTP 401). This is an identity / API-token failure: the
robot connected and the job started, but the token the activity uses to
call the Orchestrator REST API is rejected.

What this looks like:
- Error message contains `"You are not authenticated! Error code: 0"` with HTTP status `401 (Unauthorized)`
- `UiPath.Core.Activities.OrchestratorCommunicationException` thrown *inside* the running workflow at the asset/credential activity
- The job has a `StartTime` and ran briefly (often ~1s) before faulting — i.e. it **executed**, then the activity's HTTP call failed

> **Distinguish from "not authorized" and from "unlicensed":**
> - "not **authorized**" (HTTP 403) is permission/RBAC — a different playbook (`get-asset-permission-denied.md`), even though it can share `Error code: 0`.
> - An **unlicensed** robot fails at job *start*: it never acquires a runtime, so the job stays Pending or faults immediately without a `StartTime`/without reaching any activity. A 401 thrown *inside* a running workflow is NOT a licensing symptom. Verify the robot is licensed (`IsLicensed: true`) and that the job actually ran before pursuing this playbook.

What can cause it (in a running job that 401s at the activity):
- Machine key or client credentials do not match what is configured in Orchestrator (e.g. the machine key was regenerated, or the robot was provisioned against a different machine template). Dispatch can still succeed from a cached session while fresh API-token requests get 401.
- Robot key authentication is disabled for the tenant ("Allow both user authentication and robot key authentication" is off), so a machine-key-authenticated robot's API token is rejected.
- A `UiPath.System.Activities` package upgrade introduced an authentication regression (historically reported on 20.10.1+ and 2021.10.5) — suspect this when the failure began right after a package change.

What to look for:
- Robot connection + license status in the UiPath Assistant tray icon (must be Connected **and** Licensed) and in `or users list` (`IsLicensed`, `ConnectionState`)
- Whether the job actually started/ran (a `StartTime` + an in-`Main.xaml` activity fault) vs. never starting (licensing) — see the unlicensed note above
- `UiPath.System.Activities` package version in the project, and whether the issue started after a package upgrade

## Investigation

1. Confirm the job **ran** — check for a `StartTime` and that the fault is inside `Main.xaml` at the asset activity. If the job never started (no `StartTime`, stuck Pending, instant fault with a licensing/no-slot message), this is a licensing/runtime-availability issue, not this playbook.
2. Verify the robot is **licensed and connected** in `or users list` (`IsLicensed: true`, a non-null `LicenseType`, `ConnectionState: Connected`). If unlicensed, assign a Runtime license (Orchestrator > Tenant > Licenses) — that is a separate, start-time failure mode.
3. Verify the robot's machine key or client credentials match what is configured in Orchestrator > Tenant > Machines. A regenerated/rotated key the robot still holds is the most common cause of a running-job 401.
4. Check tenant security: confirm "Allow both user authentication and robot key authentication" is enabled (Orchestrator > Tenant > Settings > Security).
5. Check whether the issue started after a `UiPath.System.Activities` package upgrade — a known auth regression can produce this 401.

## Resolution

- **If machine key mismatch:** reconnect the robot using the correct key from Orchestrator > Tenant > Machines, then confirm it returns to `Connected, Licensed`.
- **If robot key authentication disabled:** enable "Allow both user authentication and robot key authentication" in Tenant > Settings > Security.
- **If package regression:** roll back `UiPath.System.Activities` to the last known-good version, or update to the latest stable, then republish.
- **If the robot is actually unlicensed (job never started):** assign a Runtime license to the robot in Orchestrator > Tenant > Licenses. Note this presents as a job-start failure, not an in-activity 401.
