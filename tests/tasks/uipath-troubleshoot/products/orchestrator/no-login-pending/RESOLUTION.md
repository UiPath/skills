# Final Resolution

**Matched playbook:** `references/products/orchestrator/playbooks/robot-credentials.md` (high confidence, single match — the host-family `Pending` playbooks do not fit because no host-family `ErrorCode` is present).

**Scope:** orchestrator → process

## Root cause

Job `0fd7bea5-4182-43ed-8273-9c43410add3c` (process **ERN**, entry-point `Ofsb.xaml`, runtime type Unattended) in the **Shared** folder has been stuck in `Pending` since `2026-05-27T16:24:24Z` because Orchestrator's eligibility evaluator refused to dispatch the job — `PendingReasons.ErrorCodes` is `["RobotNoMatchingUsernames"]`.

The robot user account assigned to this folder/process exists, but its credential-store username does not match any machine-user mapping on the eligible machine template (`DanLaptopNew`). The job has `StartTime` empty, `MachineKey` empty, and a single Pending entry in `JobHistory` — Orchestrator never re-evaluated.

## Eliminated sub-causes

| Sub-cause | Why eliminated |
|----------|----------------|
| Machine template has zero Unattended slots | `or machines list` shows `DanLaptopNew` (Scope=Default, Key `b8d82bd0-…`) with `UnattendedSlots: 1`. Slot is allocated. |
| Tenant Unattended licenses exhausted | `or licenses info` reports Unattended `Allowed=1`, `Used=1`, `IsExpired=false` on the ENTERPRISE plan — entitlement provisioned. Orchestrator would emit a license-family `ErrorCode` on exhaustion, not `RobotNoMatchingUsernames`. |

**Open gap:** the "no robot user assigned to the folder" sub-cause cannot be fully ruled out via the documented `uip` CLI (no `robots list` or `robot-accounts list` command). The literal `RobotNoMatchingUsernames` code indicates a robot account *is* being compared but no machine-user row carries the same username — which points to the credential-mismatch sub-cause rather than no-robot-assigned.

## Recommended fix

Per `robot-credentials.md`'s Resolution branch for `RobotNoMatchingUsernames`, any one of the following resolves the constraint:

1. **Update the robot user's credential store username** so it matches the Windows username the machine is configured to log in with on `DanLaptopNew`.
2. **Assign the correct robot user account to the Shared folder** (Manage Accounts on the folder → create or pick an account whose username matches the machine's configured user).
3. **Run the job under a different account** whose unattended-robot credentials already match a machine user.

After applying one of these, re-trigger the job; Orchestrator's next eligibility pass will dispatch it.

## Symptoms / signature

- Job `state = Pending`, no `StartTime`, empty `MachineKey`, `JobHistory` shows only the original Pending entry.
- `PendingReasons.ErrorCodes` is exactly `["RobotNoMatchingUsernames"]` — the host-family codes (`TemplateNoHostsAvailable`, `DynamicJobConnectedMachinesInvalid`, `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`) are absent. This is not a no-host or stale-dispatch case.
- The folder's eligible machine template has `UnattendedSlots > 0`, and the tenant Unattended license is not exhausted — so the failure is the credential-match constraint specifically.
