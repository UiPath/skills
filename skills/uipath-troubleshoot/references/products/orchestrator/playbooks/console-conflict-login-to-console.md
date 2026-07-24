---
confidence: medium
---

# Could Not Start Executor — Interactive Job Using the Console (HD + Login to Console)

## Context

An unattended job faults at start with:

```
Another interactive job is using the machine's console. Only one interactive job can use the console at a time.
```

What this looks like:
- Job state: Faulted at start; a **concurrent** interactive job on the same host is already attached to the console.
- The affected robots are **High-Density (HD)** — multiple robot users on one machine — configured with **"Login to Console = True."**

What causes it:
- With **Login to Console = True**, the Robot Service attaches the job to the machine's **single physical console session** instead of creating its own RDP/virtual session. A Windows host has **exactly one console session**, so only one console-attached interactive job can run at a time. On an HD robot (designed for *many* concurrent sessions), forcing every job onto the console serializes them to one — the second concurrent job is refused.
- Per UiPath guidance, **Login to Console is not recommended for HD robots** precisely because there can only be one active console session at a time.
- This is distinct from **Foreground Process Already Running** ([foreground-already-running.md](./foreground-already-running.md) — Assistant-started foreground concurrency on one user) and from **Workstation In Use** ([workstation-in-use-machine-slots.md](./workstation-in-use-machine-slots.md) — OS session capacity vs over-provisioned slots).

What to look for:
- The message names the **console** specifically (not "workstation," not "foreground process").
- The host runs **HD robots** (multiple robot users / several slots) — check the machine template.
- **Login to Console = True** on the robot user's execution settings (Tenant → Users → user → Access Rules → Advanced Robot Options; the setting may not be exposed via `uip`).

## Investigation

1. **Get the faulted job:** `uip or jobs get <job-key> --output json` → confirm the `Another interactive job is using the machine's console` message and the `HostMachineName`.
2. **Confirm HD context:** `uip or machines list --all-fields --output json` → the host template has multiple robot users / several slots (HD), not a single dedicated unattended slot.
3. **Correlate concurrency:** `uip or jobs list --folder-key <key> --output json` → a second interactive job was Running on the same host in the same window.
4. **Confirm the setting:** check **Login to Console** for the robot user (Tenant → Users → user → Advanced Robot Options). `True` on an HD robot is the root cause.

## Resolution

- **Disable "Login to Console"** for the HD robot user(s) on that host, so each job gets its own RDP/virtual session instead of competing for the single console session. This is the recommended configuration for HD robots.
- After disabling, re-run — concurrent interactive jobs will each seat in their own session up to the licensed slot count.
- Do not treat this as a credential or transient issue — rerunning with Login to Console still True just re-hits the single-console limit whenever two jobs overlap.
