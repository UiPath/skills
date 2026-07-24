---
confidence: medium
---

# Known-Issue Robot Defect — Match Before Root-Causing

## Context

Some `Could not start executor` faults are **documented known Robot defects** already fixed in a specific Robot version — not a configuration problem to root-cause. When a fault's signature matches a known issue, the fastest resolution is: correlate with the customer-portal known-issues feed, check the host's Robot version, and upgrade to the fix version. Do not burn an investigation on a bug that is already fixed.

What this looks like — signatures commonly tied to known Robot defects:
- `Could not start executor. Could not find a part of the path 'C:\Windows\TEMP\UiPath\CredProvider'.` — fixed in Robot **23.10.9** (ROBO-4022)
- `Could not start executor. ERROR_INVALID_PARAMETER=0x00000057 : The parameter is incorrect.` — known issue, robot-version-sensitive
- `Rdp connection failed ... Last error: 131085` / `... 65548` — RDP-transport codes that, when they recur, are often known Robot/RDP-stack defects (distinct from the credential-side RDP handling in `job-faulted-logon-failure.md`)
- Faults that appear only below a certain Robot version and vanish after upgrade

What can cause it:
- A defect in the Robot/executor build on the host, corrected in a later release
- Host running an outdated Robot version that predates the fix

## Investigation

1. Get the failing job and capture the exact `Info` signature + code:
   `uip or jobs get <job-key> --output json`.
2. Identify the Robot version on the host:
   `uip or machines list --output json` — read the template/host Robot version. Correlate with `HostMachineName` from the job.
3. **Correlate with known issues** — check the customer-portal known-issues feed (https://customerportal.uipath.com/known-issues/) for a matching signature and its fix version. If the running version predates the fix version, this is the known defect.
4. Rule out a live config cause: if the signature is NOT in the known-issues feed and the Robot is already current, treat it as a real fault and fall back to the matching `Could not start executor` playbook (logon / session / credential-store) instead.

## Resolution

- **Signature matches a known issue AND the host Robot predates the fix version:** upgrade the Robot on the affected host(s) to the fix version (e.g. ≥ 23.10.9 for the `CredProvider` path defect), then rerun. No further root-causing needed — the defect is in the Robot build.
- **CredProvider path (`C:\Windows\TEMP\UiPath\CredProvider`):** fixed in 23.10.9 (ROBO-4022) — upgrade the Robot.
- **`ERROR_INVALID_PARAMETER` / `0x00000057`:** if it matches a known issue for the running version, upgrade; otherwise rerun once (some occurrences are transient) and escalate with the job evidence if it persists.
- **RDP `131085` / `65548`:** if recurring and matching a known RDP-stack issue for the version, upgrade the Robot; also verify RDP session stability on the host (see `job-faulted-session-console-contention.md`).
- **No matching known issue / already on the fix version:** do NOT treat as a known defect — fall back to the specific `Could not start executor` playbook (logon, session/console, or credential-store) for a real root cause.

Prevention:
- Keep robots on a current, patched version — most executor-start defects are fixed in later releases.
- Before deep-diagnosing a `Could not start executor` fault, spend 2 minutes matching it against the known-issues feed + the host Robot version; a known-and-fixed defect is a version bump, not an investigation.
