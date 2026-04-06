---
confidence: medium
---

# Job Faulted — Logon / RDP Session Failure

## Context

An unattended job faults immediately (typically < 2 seconds) with a logon-related error. The robot could not establish a Windows session on the target machine.

What this looks like:
- Job state: Faulted, with near-zero runtime (StartTime ≈ EndTime)
- Error contains one of: `ERROR_LOGON_FAILURE (0x0000052E)`, `RDP connection failed`, `Last error: 131092`, `Logon failed for user`, `Could not start executor`
- Error originates from `LsaApi.LogonUser`, `UiPath.Rdp.NativeInterface.RdpLogon`, or similar session/auth stack

What can cause it:
- Session configuration mismatch — process requires user interaction (needs a desktop session), but the user is not logged in AND "Login to Console" is false — the robot has no session to use and no permission to create one
- Incorrect or expired credentials — the password stored in Orchestrator for the robot account no longer matches the Windows account password
- Account locked, disabled, or expired on the target machine
- Group Policy restriction — policy blocks the account from interactive or RDP logon

What to look for:
- Whether the process has `requiresUserInteraction: true` — this is the critical fork. If true, the robot needs an active Windows desktop session
- If `requiresUserInteraction: true`: whether the user was logged in on the machine, and what the "Login to Console" setting is. When Login to Console is false and the user is not logged in, failures are **intermittent by nature** — jobs succeed when the user happens to be logged in (the robot reuses their session) and fail when the user is logged out (no session exists, robot cannot create one). A mix of successful and failed jobs on the same machine with the same config is the expected pattern, not evidence against this cause.
- If `requiresUserInteraction: false`: the process can run in Session 0 (background) without a desktop, so a logon failure points to credentials or account issues
- Job history on the same machine — if other recent jobs (succeeded or failed with different errors) did not hit logon errors, credentials are likely correct — investigate session configuration instead

## Investigation

1. Get the faulted job details: `uip or jobs get <job-key> --output json`. Note `type`, error message, machine name, start/end time.
2. Check `requiresUserInteraction` — this field is NOT available via the `uip` CLI (not on jobs, processes, or releases). Ask the user to check it in the Orchestrator UI: Processes → select the process → Settings → "Requires User Interaction".
3. Check recent job history on the same machine: `uip or jobs list --folder-path '<folder>' --top 20 --output json`. Compare error messages — if other recent jobs on the same machine either succeeded or failed with different (non-logon) errors, credentials are likely correct — investigate session configuration instead.
4. **If `requiresUserInteraction` is true:** check whether the user was logged into the machine at the time of the failure, and what the "Login to Console" setting is (Orchestrator → Tenant → Users → select user → Access Rules → Advanced Robot Options). This setting is only visible in the Orchestrator UI — not queryable via CLI.
   - If not logged in AND Login to Console = false → session configuration mismatch (root cause)
   - If not logged in AND Login to Console = true → the robot should have created a session; investigate credential/account issues instead
5. **If `requiresUserInteraction` is false:** the process runs in Session 0 without needing a desktop session. A logon failure here points to credentials or account issues.

## Resolution

- **If session configuration mismatch** (requires user interaction + not logged in + Login to Console = false):
  - Option A: Set "Login to Console" to true in Orchestrator (Tenant → Users → Access Rules → Advanced Robot Options) so the robot can create a console session when the user isn't logged in
  - Option B: Ensure the user is logged into the machine before running the job
  - Prevention: For processes that require user interaction, always configure Login to Console = true for the robot account, or use a scheduled trigger paired with auto-login
- **If incorrect/expired credentials**: Update the password in Orchestrator to match the current Windows password
- **If account locked/disabled**: Unlock or re-enable the account on the target machine
- **If Group Policy restriction**: Review GPO settings (gpresult /r) for logon restrictions on the robot account
