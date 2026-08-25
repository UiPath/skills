# Resolution — DailyExtract "workstation is in use by another user"

## Root Cause

Job `a1710001-1111-4111-8111-111111111111` (process `DailyExtract`, folder
Unattended Ops) faulted at executor start, near-zero runtime, with:

```
Could not start executor. The workstation is in use by another user. Please retry after the user logs off or disconnects.
```

The machine template for **WS-CLIENT-07** grants **`unattendedSlots: 3`**, but
WS-CLIENT-07 is a **Windows 11 client** — a single-interactive-session OS that
supports only **one** interactive/RDP session at a time. When Orchestrator
dispatched `DailyExtract` while another unattended job (`HourlySync`) was
already **Running** on the same host, Windows had no second session to seat the
executor, and the start was refused with "the workstation is in use by another
user." The evidence: `machines list --all-fields` shows 3 unattended slots on a
client OS, and `jobs list` shows a concurrent Running job on the same
`HostMachineName` at the fault time. Earlier, non-overlapping DailyExtract runs
on the same host succeeded — the failure tracks **concurrency**, not the
credential.

Matches `products/orchestrator/playbooks/workstation-in-use-machine-slots.md`.

## Fix

Match the template's slot count to the host's real concurrent-session capacity:

- **Reduce `WS-CLIENT-07`'s unattended slots to 1** so Orchestrator never
  dispatches two overlapping jobs to a single-session client OS.
- **Or** move the workload to a **multi-session host** (Windows Server with the
  Remote Desktop Session Host role and enough RDS CALs, or a High-Density
  configuration) and size the slots to the licensed concurrent-session count.
- **Or** serialize the schedules so two jobs never target WS-CLIENT-07 at once.

## Must NOT attribute

Do not attribute this to: a logon/credential failure (there is no `Logon
failed` / `0x000005..` code — the credential is valid and non-overlapping runs
succeed); a human holding the only RDP slot (that is the RDP-slot branch of the
logon-failure playbook — here it is the *template* over-provisioning slots
beyond the OS capacity); a session-creation timeout; a transient blip (a blind
rerun during the same overlap window will fault again); or a licensing/quota
problem. The fix is slot/capacity alignment, not credentials or a rerun.
