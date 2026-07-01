# Final Resolution

**Matched playbook:** `references/products/orchestrator/playbooks/job-pending-no-host.md` (high confidence — host-family `PendingReasons` with no connected runtime on the eligible template).

**Scope:** orchestrator → process

## Root cause

The job (process **NewBlankTask**, runtime type Unattended) in the **Shared** folder has been stuck in `Pending` since `2026-05-28T08:48:18Z` because **no host is available to run it**. The eligible machine template for the folder — **DanLaptopNew** (Default scope) — has **no connected runtime** (`robotVersions` is empty): no robot is signed in / connected to it, so Orchestrator has no host to dispatch the Unattended job to.

The host-family `PendingReasons.ErrorCodes` (`TemplateNoHostsAvailable`, `DynamicJobConnectedMachinesInvalid`, `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`) and the message *"…there is none connected to this folder"* describe the real condition. `StartTime` is empty and `JobHistory` has only the original `Pending` entry — the job never started because nothing could accept it.

## Eliminated sub-causes

| Sub-cause | Why eliminated |
|----------|----------------|
| Unattended license exhausted / no free slot | `or licenses info`: Unattended `Allowed=1`, `Used=0`, `IsExpired=false`. The slot is free — license is not the blocker. |
| Stale dispatch-time snapshot (a re-trigger would fix it) | `or machines list --all-fields` shows **DanLaptopNew `robotVersions: []`** — no runtime is connected. There is no host for a fresh dispatch to land on, so re-triggering reproduces the same Pending state. This is a live no-host condition, not a stale snapshot. |
| Robot credential / username mismatch | `PendingReasons.ErrorCodes` does not contain `RobotNoMatchingUsernames` — this is the host family, not the credential family. |

## Recommended fix

Per `job-pending-no-host.md`, make a host available to the Shared folder's template:

1. **Connect a robot to the DanLaptopNew template** — sign a robot into a machine that belongs to the template (Assistant in Service / Unattended mode, connected to this Orchestrator URL + tenant) so a runtime registers and can accept the job.
2. **Or assign a machine template that already has a connected host** to the Shared folder.

Once a host is connected to the folder's template, Orchestrator dispatches the Pending job. Re-triggering alone does **not** help while no host is connected.

## Evidence — Orchestrator

- Job (process `NewBlankTask`) in folder **Shared**: `State=Pending`, `StartTime=null`, `Type=Unattended`, created `2026-05-28T08:48:18Z`.
- `PendingReasons.ErrorCodes = [TemplateNoHostsAvailable, DynamicJobConnectedMachinesInvalid, DynamicJobConnectedMachinesWindowsRobotVersionInvalid]`; message *"…there is none connected to this folder."*
- `JobHistory`: a single `Pending` entry; no later events.
- `or machines list --all-fields`: **DanLaptopNew** (Default scope, the eligible template) has `robotVersions: []` — no connected runtime. Other templates are Serverless / PersonalWorkspace scope and not eligible for this Default-scope folder job.
- `or licenses info`: Unattended `Allowed=1`, `Used=0` — the slot is free.
- Running Unattended jobs in **Shared**: zero.
