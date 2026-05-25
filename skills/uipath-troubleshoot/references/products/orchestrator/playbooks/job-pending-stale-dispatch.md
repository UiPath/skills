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
- AND the tenant Unattended license slot is free (`Used < Allowed`)
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
   - Tenant Unattended license slot is free — `uip or licenses info` should show `Used < Allowed`.
4. **All four prerequisites confirmed AND PendingReasons.Errors unchanged AND JobHistory shows no re-evaluation** → the conclusion is stale-dispatch.

## Resolution

**Stop the Pending job and re-trigger the process.**

- In Orchestrator: Jobs → select the Pending job → Stop / Kill.
- Re-trigger the process from the same folder. The fresh dispatch performs a new eligibility check against the current state (host connected, credential present, license slot free) and the job should transition to Running.
- If a re-triggered job is also Pending with the same `ErrorCodes`, the underlying cause was NOT actually resolved — switch to [job-pending-no-host.md](./job-pending-no-host.md) and walk its sub-cause list.

Do NOT attempt to "fix" the stale codes by reassigning the template, restarting the Robot Service, or signing in to Assistant — those remediations apply to `job-pending-no-host.md`. In this scenario the runtime is already connected; the only action that matters is forcing Orchestrator to re-evaluate via a new dispatch.

## Discriminator vs job-pending-no-host

| Signal | `job-pending-no-host` | `job-pending-stale-dispatch` |
|---|---|---|
| `PendingReasons.Errors` | Host-family codes | Host-family codes |
| Template has connected runtime (`robotVersions` populated) | No | Yes |
| Robot account Windows credential present | Maybe | Yes |
| Assistant in Service Mode | Maybe | Yes |
| Unattended license slot free | Maybe | Yes |
| `JobHistory` past the original entry | Maybe | No (only the original Pending entry) |
| Remediation | Provision the missing prerequisite | Stop + re-trigger |

Both playbooks can match in triage. Triage records both; the hypothesis tester resolves which one applies by checking the four "currently resolved" signals plus `JobHistory` shape. If all four are resolved AND `JobHistory` is unchanged, this playbook wins.
