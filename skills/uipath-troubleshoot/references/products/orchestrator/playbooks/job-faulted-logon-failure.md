---
confidence: medium
---

# Could Not Start Executor — Logon Failed for User

## Context

An unattended job faults immediately (typically < 2 seconds) because the Robot could not establish a Windows session on the target machine for the configured user. The Robot service is up and the machine is reachable, but the user credential it tried to use was refused by Windows.

What this looks like:
- Job state: Faulted, near-zero runtime (StartTime ≈ EndTime, often < 1 s)
- Error contains one or more of: `Could not start executor`, `Logon failed for user <DOMAIN>\<USER>`, `RDP connection failed`, Windows codes like `0x0000052E` (logon failure), `0x00000775` (account locked out), `0x00000532` (password expired), `Last error: 131092`
- May be intermittent (some jobs on the same machine succeed) or persistent (every job on that machine/user fails)

What can cause it (cause-branches — pick the right one from evidence):

1. **Session configuration mismatch** — Process has `requiresUserInteraction: true` (needs a desktop session), but no user is logged in AND "Login to Console" is false. The Robot has no session to attach to and no permission to create one.
2. **Account locked in Active Directory** — Repeated bad logons (often from a stale credential — see branch 3) or an admin lockout tripped AD's lockout policy. Windows refuses every logon until the account is unlocked.
3. **Password mismatch (stale credential in Orchestrator)** — User's AD password was rotated, but the credential stored in Orchestrator (Tenant → Credential Stores / robot user) still holds the old one. Each job attempt logs on with the wrong password.
4. **Lockout loop (chained 3 → 2)** — Branch 3 driving branch 2: Orchestrator keeps trying the stale password, each retry counts as a failed logon, and after N attempts the account locks. Unlocking without first fixing the stored password just re-locks on the next job.
5. **MFA / Conditional Access enforced on the service account** — A tenant policy added Multi-Factor Authentication or a Conditional Access rule to the user. Unattended Robots cannot satisfy an interactive MFA challenge, so Windows / Entra rejects the logon.
6. **RDP slot already taken by another user** — Windows Server (non-Terminal-Services) typically allows only one or two concurrent RDP sessions. Another human user (admin, ops, the service-account holder themselves) is logged in via RDP, leaving no slot for the Robot to create a session. Also occurs when a previous RDP session was disconnected without logoff and is still holding the slot.

What to look for:
- **Pattern:** intermittent vs. persistent across recent jobs on the same machine/user
- **Same-user / different-machine:** does the same robot user fail on another machine? (Yes → credential/account problem. No → machine/RDP problem.)
- **Same-machine / different-user:** does a different robot user succeed on the same machine? (Yes → user-specific, not machine. No → machine/session problem.)
- **Lockout pattern:** rapid repeat-failures (every few minutes) followed by an even harder block → branch 4 fingerprint
- **Recent AD password rotation** on this user (ask the user; check AD `PasswordLastSet`) → branch 3 / 4
- **Recent MFA / Conditional Access policy rollout** in the tenant → branch 5
- **Whose session is on the machine** — `query session` / `quser` on the host shows any active or disconnected RDP session that may be holding a slot → branch 6

## Investigation

Go in this order — cheaper checks first, and each step narrows the branch.

1. **Get the faulted job:** `uip or jobs get <job-key> --output json`. Capture `MachineName`, `RobotName` / user, `StartTime`, `EndTime`, `Info` / error message. Look at the exact wording — `Logon failed`, `account is locked`, `password has expired`, `RDP connection failed`, and any `0x000005..` / `131092` codes are the strongest single hint about the branch.
2. **Recent-jobs history on the same machine:**
   `uip or jobs list --folder-path '<folder>' --limit 20 --output json`
   - Mixed success/failure on the same machine/user → branches 1 or 6 (session/RDP availability) more likely than 2/3/5.
   - Every recent job on this user has faulted with the same logon error → branches 2, 3, 4, or 5 (user-side problem).
   - Other users succeed on the same machine → rules out a pure machine/network cause.
3. **Check `requiresUserInteraction`** (Orchestrator UI → Processes → process → Settings → "Requires User Interaction"). Not exposed via `uip` CLI.
4. **If `requiresUserInteraction: true`** — check "Login to Console":
   - `uip or users get <user-key> --output json` and look for `unattendedRobot.executionSettings.LoginToConsole`.
   - If the field/command isn't available, fall back to UI: Tenant → Users → user → Access Rules → Advanced Robot Options.
   - **Login to Console = false** → **branch 1** (session-config mismatch). Stop here.
   - **Login to Console = true** → continue, the Robot is allowed to create its own session, so a logon failure points at the credential or account itself.
5. **Distinguish branches 2 / 3 / 4 (account + password problems):**
   - Ask the user (or check AD): when was `PasswordLastSet` for this user? Was it changed recently and **not updated in Orchestrator**? → branch 3.
   - On a domain controller: `Get-ADUser <user> -Properties LockedOut, badPwdCount, lastBadPasswordAttempt` (or AD Users & Computers → Account tab → "Unlock account" checkbox state). LockedOut = true → branch 2 surface.
   - `badPwdCount` climbing fast around job-trigger times **plus** LockedOut = true → **branch 4** (lockout loop). This is critical: unlocking without fixing the Orchestrator credential just re-arms the loop.
   - Have an admin try the stored credential **manually** (log on to the VM with it once). If it fails with "wrong password" → branch 3. If it fails with "account is locked" → branch 2. If it prompts for MFA → branch 5.
6. **Check for MFA / Conditional Access (branch 5):**
   - Entra/Azure AD admin center → Users → service account → Authentication methods, and Conditional Access → Policies → filter by this user/group.
   - Robot/Windows logs typically show an interactive-auth requirement that the unattended logon could not satisfy.
7. **Check RDP slot (branch 6):**
   - On the host: `query session` or `quser` (run as admin) — list all sessions including Active and Disconnected.
   - In Orchestrator, only one Active RDP session is generally available for an unattended Robot. A disconnected-but-not-logged-off session still holds the slot.
   - Cross-check the job's `MachineName` and `StartTime` against who was on the host at that moment.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Session configuration mismatch:**
  - Option A: Set "Login to Console" to true on the robot user (Orchestrator → Tenant → Users → user → Access Rules → Advanced Robot Options), so the Robot creates its own console session when no one is logged in.
  - Option B: Ensure a robot is logged into the machine before jobs run.
  - Prevention: For processes with `requiresUserInteraction: true`, default Login to Console to true.
- **Branch 2 — Account locked:**
  - Have a domain admin unlock the account in Active Directory (AD Users & Computers → user → Account → "Unlock account", or `Unlock-ADAccount -Identity <user>`).
  - **Do not unlock blindly** — first confirm whether branch 3 / 4 is driving the lockout (next bullet), or you'll re-lock immediately.
- **Branch 3 — Password mismatch:**
  - Update the password stored in Orchestrator to match the current AD password. Location depends on how the robot user is set up:
    - Tenant Users: Tenant → Users → user → Robot password
    - Folder-scoped robot account: edit the robot's credential
    - Credential Store: edit the asset that holds the password
  - Then have an admin unlock the AD account (branch 2 fix) so the next job can attempt with the correct password.
  - Verify by **manually logging on** to the VM with the new credential before re-triggering.
- **Branch 4 — Lockout loop (always treat as a sequence):**
  1. Disable triggers / pause the schedule for this process and any others using the same robot user.
  2. Update the password in Orchestrator (branch 3 fix).
  3. Unlock the AD account (branch 2 fix).
  4. Manually verify the credential by logging into the VM once.
  5. Re-enable triggers.
  - Prevention: rotate AD passwords for robot service accounts in lockstep with Orchestrator. If feasible, exempt the service account from interactive password expiry (with compensating controls), or use a non-expiring managed service account / gMSA-style pattern.
- **Branch 5 — MFA / Conditional Access:**
  - Exclude the service account from MFA and from interactive-auth-requiring Conditional Access policies. In Entra: Conditional Access → policy → Users → Exclude → add the service account or a "Service Accounts" group.
  - If org policy forbids MFA exclusion, move the workload to a non-interactive auth model (e.g., Modern Folders with a registered application using app-only auth, where supported), or to UiPath Cloud Robots which sidestep the interactive Windows logon entirely.
  - Prevention: keep robot service accounts in a dedicated group with a documented MFA/CA exemption.
- **Branch 6 — RDP slot conflict:**
  - On the host (as admin): `logoff <session-id>` for the disconnected session that's holding the slot, or have the current user disconnect properly.
  - For ongoing risk: enable "Login to Console" so the Robot uses the console session instead of competing for RDP slots; or upgrade the host to Windows Server with the Remote Desktop Session Host role and a Remote Desktop CAL pool sized for concurrent sessions.
  - Prevention: dedicate the unattended host to the Robot — humans should not RDP into it during business hours, or should always log off (not disconnect) after admin work.

## Prevention (cross-branch)

- Use a dedicated service account per environment for unattended Robots; don't share with admin users.
- Rotate the service-account password in Orchestrator **at the same time** as in AD (or just before, then unlock).
- Exempt service accounts from MFA / interactive Conditional Access policies via a documented group.
- Default `Login to Console = true` for unattended robot users whose processes require user interaction.
- Monitor `badPwdCount` and account-lockout events for robot service accounts; alert on the climbing pattern that precedes branch 4.
