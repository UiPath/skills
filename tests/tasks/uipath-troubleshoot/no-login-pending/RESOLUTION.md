# Final Resolution

**Matched playbook:** `references/products/orchestrator/playbooks/job-pending-stale-dispatch.md` (with `job-pending-no-host.md` as the co-matched sibling, eliminated by the discriminator below)

**Scope:** orchestrator → process

**Job discovery:** the user gave no job key. The job is found by listing
Pending jobs in the Shared folder (`uip or folders list` → Shared key, then
`uip or jobs list --folder-key <key> --state Pending --output json`), which
returns exactly one: `0f9d854e-221e-487d-bb2b-fcc76a7d7461` (process **ERN**,
entry-point `Google.xaml`, runtime type Unattended).

## Root cause

Job `0f9d854e-221e-487d-bb2b-fcc76a7d7461` in the **Shared** folder is stuck
in `Pending` since 2026-05-14T11:07:13Z because of **stale dispatch-time
PendingReasons**:

1. **Originating cause (confirmed):** At dispatch time no Unattended host was
   connected to the `danVM` machine template. Orchestrator captured these
   `PendingReasons.Errors` on the job and never re-evaluated them:
   - `TemplateNoHostsAvailable`
   - `DynamicJobConnectedMachinesInvalid`
   - `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`

2. **Why it is still Pending (active root cause):** A Windows Unattended
   runtime (robot version `26.0.193-cloud.23059`) has since connected to the
   `danVM` template, the robot account has a Windows credential, the Assistant
   is in Machine Key / Service Mode, and an Unattended license slot is
   available. The job's `PendingReasons` are a **frozen snapshot** from
   dispatch time — Orchestrator does NOT re-evaluate them on a still-Pending
   job. `JobHistory` contains only the single original Pending entry, proving
   no re-evaluation occurred. The job will stay Pending until it is stopped
   and re-triggered.

## How the confounding evidence resolves

- **`machines list`** shows `danVM` with `robotVersions` populated — a runtime
  IS connected. The PendingReasons text "…there is none connected to this
  folder" is the *dispatch-time* verdict, NOT current proof the template is
  unassigned from the folder (no `uip` command can verify folder→template
  assignment).
- **`licenses info`** shows Unattended `Used = 1 / Allowed = 1`. This is the
  *healthy* reading: the single used slot is held by `danVM`'s own connected,
  idle runtime — the very runtime that will execute the job — not a competing
  consumer. No other Unattended job is Running, so the runtime is free.
  `Used == Allowed` here is NOT license exhaustion.

## Eliminated hypotheses

| ID | Hypothesis | Why eliminated |
|----|------------|----------------|
| H2 | Robot connected in Attended (User) mode | User confirmed Machine Key / Service Mode (Unattended). |
| H3 | Robot account missing Windows credential | User confirmed the Windows credential is saved on the danVM robot account. |
| H4 | Unattended license exhausted / no free slot | `licenses info` Used=1/Allowed=1 is danVM's own idle runtime holding its slot; no other Unattended job is Running, so the runtime is available. Not exhaustion. |
| H5 | `danVM` template not assigned to the Shared folder | Unverifiable — no `uip` command lists folder→template assignment. `machines list` shows danVM currently has a connected runtime; with stale no-host codes + a single JobHistory entry, the codes are stale, not a live assignment gap. |

## Recommended fix

**Stop job `0f9d854e-221e-487d-bb2b-fcc76a7d7461` in Orchestrator (Jobs →
select → Stop / Kill) and re-trigger the ERN process from the Shared folder.**
A fresh dispatch performs a new eligibility check against the current state
(runtime connected, credential present, license slot held by the idle runtime)
and the job should transition to Running on `danVM`.

Do NOT reconfigure folder machine assignments, free a license, restart the
Robot Service, or sign in to Assistant — the runtime is already connected and
licensed; the only action that matters is forcing a re-evaluation via a new
dispatch.

If a re-triggered job is also Pending with the same `ErrorCodes`, the
underlying cause was not actually resolved — escalate to a deeper
folder/template-to-runtime binding investigation (`job-pending-no-host.md`).

## Symptoms / signature

- Job `state = Pending`, no state transitions in JobHistory.
- `PendingReasons.Errors` includes `TemplateNoHostsAvailable` (and optionally
  `DynamicJobConnectedMachinesInvalid` /
  `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`).
- Machine template (`danVM`) currently reports a connected runtime
  (`robotVersions` populated).
- Unattended license `Used == Allowed`, consumed by the connected idle runtime
  (not by a competing Running job).
- JobHistory contains only the single original Pending entry — proving
  Orchestrator did not re-evaluate.
