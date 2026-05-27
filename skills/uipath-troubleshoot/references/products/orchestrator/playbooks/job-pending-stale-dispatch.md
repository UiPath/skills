---
confidence: high
---

# Job Pending — Stale Dispatch-Time PendingReasons

## Context

A job is stuck in `Pending` state with `PendingReasons.Errors` codes that no longer describe the current state. Orchestrator captured these reasons at dispatch time and does NOT re-evaluate them while the job remains Pending — even when the underlying conditions have since been resolved.

What this looks like:
- Job `state = Pending`, no state transitions in `JobHistory`
- `PendingReasons.Errors` includes one or more of: `TemplateNoHostsAvailable`, `DynamicJobConnectedMachinesInvalid`, `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`
- BUT the machine template assigned to the job currently reports a connected runtime (`robotVersions` populated)
- AND the robot account has a Windows credential configured
- AND the Assistant on the host is in Machine Key / Service Mode (Unattended)
- AND an Unattended runtime is licensed and idle — the template's own connected runtime holds the slot, so `Used.Unattended == Allowed` is the *healthy* reading here, NOT exhaustion (see Investigation step 3)
- AND `JobHistory` contains only the single original Pending entry — no later events

The contradiction between the stale error codes and the now-eligible runtime is the signature. The job is technically dispatchable right now; Orchestrator just hasn't re-checked since the initial dispatch failed.

What can cause it:
- At dispatch time no Unattended runtime was connected, or the connected runtime didn't have a Windows credential, or the license slot was occupied, etc. — any of the `job-pending-no-host` causes could have produced the original PendingReasons.
- Since dispatch, the underlying issue was fixed (runtime reconnected, credential added, license freed), but the job was never stopped + re-triggered, so Orchestrator never re-evaluated.

## Investigation

1. **Read `PendingReasons.Errors`** on the job — `uip or jobs get <job-key> --output json`. Confirm the codes are no-host-family (`TemplateNoHostsAvailable` etc.).
2. **Read `JobHistory`** for the job — `uip or jobs history <job-key> --output json`. If only the original Pending entry exists with no later events, Orchestrator has not re-evaluated since dispatch.
3. **Verify each documented cause is currently resolved** so the discriminator vs `job-pending-no-host.md` holds:
   - Machine template has a connected runtime — `uip or machines list --all-fields` should show `robotVersions` populated on the assigned template.
   - Robot account has a Windows credential — confirm with the user (or via the robot-account details if available).
   - Assistant is in Machine Key / Service Mode (Unattended) — confirm with the user.
   - An Unattended runtime is licensed and free to take the job. `uip or licenses info` reports `Used.Unattended` = the count of **connected/allocated** Unattended runtimes, NOT the count of running jobs. The template's connected idle runtime holds its slot, so `Used == Allowed` is *expected and healthy* when that slot belongs to the assigned template — it is NOT exhaustion. Confirm the runtime is idle rather than busy with a different job: `uip or jobs list --folder-key <key> --state Running --output json`. If no OTHER Unattended job is Running, the licensed runtime is available for this job. Treat the license as the blocker ONLY when a *different* Running Unattended job holds the slot.
4. **All four prerequisites confirmed AND PendingReasons.Errors unchanged AND JobHistory shows no re-evaluation** → the conclusion is stale-dispatch.

> **Do not invent a folder-assignment cause.** The PendingReasons text "…there is none connected to this folder" is Orchestrator's eligibility verdict **captured at dispatch time** — not live proof that the machine template is unassigned from the folder. No `uip` command enumerates folder→machine-template assignments, so a "template not assigned to the folder" root cause cannot be evidenced and MUST NOT be confirmed (shared.md invariants #1, #9). If `machines list` shows the assigned template currently has a connected runtime AND `JobHistory` has only the original Pending entry, the codes are stale: this playbook applies and the fix is stop + re-trigger — not a folder reconfiguration.

## Resolution

**Stop the Pending job and re-trigger the process.**

- In Orchestrator: Jobs → select the Pending job → Stop / Kill.
- Re-trigger the process from the same folder. The fresh dispatch performs a new eligibility check against the current state (host connected, credential present, license slot free) and the job should transition to Running.
- If a re-triggered job is also Pending with the same `ErrorCodes`, the underlying cause was NOT actually resolved — switch to [job-pending-no-host.md](./job-pending-no-host.md) and walk its sub-cause list.

Do NOT attempt to "fix" the stale codes by reassigning the template, adding the template to the folder's machine list, freeing a license, restarting the Robot Service, or signing in to Assistant — those remediations apply to `job-pending-no-host.md`. In this scenario the runtime is already connected and licensed; the only action that matters is forcing Orchestrator to re-evaluate via a new dispatch.

## Discriminator vs job-pending-no-host

| Signal | `job-pending-no-host` | `job-pending-stale-dispatch` |
|---|---|---|
| `PendingReasons.Errors` | Host-family codes | Host-family codes |
| Template has connected runtime (`robotVersions` populated) | No | Yes |
| Robot account Windows credential present | Maybe | Yes |
| Assistant in Service Mode | Maybe | Yes |
| Unattended runtime licensed & idle (`Used == Allowed`, no other Running job) | Maybe | Yes |
| `JobHistory` past the original entry | Maybe | No (only the original Pending entry) |
| Remediation | Provision the missing prerequisite | Stop + re-trigger |

Both playbooks can match in triage. Triage records both; the hypothesis tester resolves which one applies by checking the four "currently resolved" signals plus `JobHistory` shape. If all four are resolved AND `JobHistory` is unchanged, this playbook wins.

> Common misreads that wrongly eliminate this playbook: (1) reading `Used.Unattended == Allowed` as license exhaustion when the slot is held by the assigned template's own idle runtime; (2) reading "none connected to this folder" as a current folder-assignment gap. Both are addressed above — neither moves the verdict toward `job-pending-no-host` when a connected runtime is present.
