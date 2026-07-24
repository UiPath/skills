---
confidence: medium
---

# Could Not Start Executor — Workstation In Use (machine slots over-provisioned)

## Context

An unattended job faults at start with:

```
Could not start executor. The workstation is in use by another user. Please retry after the user logs off or disconnects.
```

What this looks like:
- Job state: Faulted, near-zero runtime; the executor never started.
- One job on the machine may succeed while a **concurrent** one fails — the failure correlates with **how many jobs run on the same physical host at once**, not with the user's credential.

What causes it:
- The **machine template allocates more runtime slots than the workstation's OS actually supports as concurrent interactive/RDP sessions.** A Windows **client** OS (Win 10/11) and a non-RDSH Windows Server allow only **one** interactive session. If the template grants 2+ unattended slots on such a host, Orchestrator dispatches a second concurrent job, Windows has no second session to give it, and the executor start is refused with "workstation is in use by another user."
- This is a **template/host capacity mismatch**, not a credential/logon problem (no `Logon failed` / `0x000005..` code) and not a human holding an RDP slot (that is the RDP-slot branch of [job-faulted-logon-failure.md](./job-faulted-logon-failure.md)).

What to look for:
- The **slot counts** on the machine template vs the host OS's real concurrent-session capacity.
- Whether failures coincide with **overlapping** job schedules on the same machine.
- Absence of any Windows logon-failure code in the message (rules out logon-failure).

## Investigation

1. **Get the faulted job:** `uip or jobs get <job-key> --output json` → confirm the `The workstation is in use by another user` message, `HostMachineName`, and near-zero runtime.
2. **Read the machine template slots:** `uip or machines list --all-fields --output json` → for the host that ran the job, read `unattendedSlots` / `headlessSlots` / other slot counts. A count **> 1** on a single-session OS is the fingerprint.
3. **Correlate concurrency:** `uip or jobs list --folder-key <key> --output json` → check whether another job was Running on the same `HostMachineName` in the same window (the "other user" holding the session).
4. **Confirm the host OS class** (ask the user / check the machine description): Windows client or non-RDSH Server → only one interactive session exists.

## Resolution

- **Reduce the template's slot count to the host's real capacity** — for a Windows client / single-session Server, set unattended slots to **1** so Orchestrator never dispatches overlapping jobs to a host that cannot seat them.
- **Or add real session capacity:** move the workload to a **multi-session** host — Windows Server with the Remote Desktop Session Host role and enough RDS CALs, or a High-Density-capable configuration — then size slots to the licensed concurrent-session count.
- **Or serialize** the schedules so two jobs never target the same single-session host at once.
- Do not "fix" this by rerunning blindly or updating credentials — the credential is fine; the host cannot seat the concurrent session the template promised.
