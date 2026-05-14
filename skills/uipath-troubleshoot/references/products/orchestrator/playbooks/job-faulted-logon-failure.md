---
confidence: medium
---

# Job Faulted — Logon / RDP Session Failure

## Context

An unattended job faults immediately (typically < 2 seconds) because the robot could not establish a Windows session on the target machine.

What this looks like:
- Job state: Faulted, with near-zero runtime (StartTime ≈ EndTime)
- Error contains: `RDP connection failed`, `Last error: 131092`, `Could not start executor`
- Possibly Intermittent — jobs on the same machine with the same config sometimes succeed, sometimes fail

What can cause it:
- Session configuration mismatch — process has `requiresUserInteraction: true` (needs a desktop session), but the user is not logged in AND "Login to Console" is false — the robot has no session to use and no permission to create one. 

What to look for:
- Intermittent pattern (mix of success and failure on the same machine/config) — jobs succeed when the user is logged in (robot reuses their session) and fail when logged out. This is the expected behavior for this cause, not evidence against it.
- Persistent failure (every job fails) — also consistent if the user was never logged in on that machine. Do not assume persistent failure means credential issues — check `requiresUserInteraction` and Login to Console first regardless of the pattern.

## Investigation

1. Get the faulted job details: `uip or jobs get <job-key> --output json`. Note `type`, error message, machine name, start/end time.
2. Check `requiresUserInteraction` — NOT available via the `uip` CLI. Only visible in the Orchestrator UI: Processes → select the process → Settings → "Requires User Interaction".
3. Check recent job history on the same machine: `uip or jobs list --folder-path '<folder>' --top 20 --output json`. If other recent jobs succeeded or failed with different (non-logon) errors, credentials are valid — session configuration is the cause.
4. **If `requiresUserInteraction` is true:** check "Login to Console". First try: `uip or users get <user-key> --output json` — look for `unattendedRobot.executionSettings.LoginToConsole`. If the `users` command is not available, check the Orchestrator UI: Tenant → Users → select user → Access Rules → Advanced Robot Options.
   - If Login to Console = false → session configuration mismatch (root cause)
   - If Login to Console = true → the robot should have created a session; investigate credential or account issues instead
5. **If `requiresUserInteraction` is false:** the process runs in Session 0 without needing a desktop. A logon failure here points to credential or account issues.

## Resolution

- **If session configuration mismatch** (requires user interaction + Login to Console = false):
  - Option A: Set "Login to Console" to true so the robot can create a console session when the user isn't logged in
  - Option B: Ensure the user is logged into the machine before running the job
  - Prevention: For processes that require user interaction, always configure Login to Console = true
- **If credential issue** (requiresUserInteraction is false, or Login to Console is true): Update the password in Orchestrator to match the current Windows password
