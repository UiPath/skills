---
confidence: medium
---

# Send Outlook Mail Message Failures

## Context

A `UiPath.Mail.Outlook.Activities` `Send Outlook Mail Message` (`SendOutlookMail`) activity does **not** call a mail API — it drives the locally installed **Outlook desktop application** through COM interop. It attaches to (or launches) `OUTLOOK.EXE` under the Windows user the Robot runs as, composes the message through the Outlook Object Model using that user's mail profile, and returns once Outlook accepts the item. Failures therefore originate at one of three surfaces: the **COM layer** (Outlook installed/registered, process bitness, orphaned process), the **session/UI** (a prompt or Work Offline state blocking the call), or the **inputs** (uninitialized `To`/`Subject`/`Body`, or a bad attachment path).

Because the call goes through a desktop application, the Outlook COM activities are fragile on **unattended** Robots, where there is no interactive desktop to dismiss a prompt and the profile may not be configured for the Robot's Windows user. When Outlook is not a hard requirement, the **Send SMTP Mail Message** activity (`UiPath.Mail.SMTP.Activities`) or the modern Graph **o365-activities** are the more reliable path (see Resolution → alternative).

What this looks like — Send Outlook Mail faults surface as one of these signatures:

- `System.InvalidCastException: Unable to cast COM object of type '...' to interface type '...'` or `System.Runtime.InteropServices.COMException: Library not registered. (REGDB_E_CLASSNOTREG / TYPE_E_LIBNOTREGISTERED)` — branch 1.
- The activity blocks and then fails with a **timeout** (`TimeoutMS` elapsed), or the job hangs with no exception — branch 2.
- `System.NullReferenceException: Object reference not set to an instance of an object` raised at the activity — branch 3.

What can cause it (cause-branches — pick the right one from evidence):

1. **COM cast / library not registered.** The Outlook COM server cannot be bound. Causes: Outlook is **not installed** on the Robot host (the activity needs the desktop client, not just an account); a **bitness mismatch** between the Robot/process and the installed Outlook (a 64-bit process against a 32-bit Outlook, or vice versa); a **corrupted Office registry / type library** (common after a botched Office update); or an **orphaned `OUTLOOK.EXE`** from a prior run holding the COM server in a bad state.
2. **Activity times out or hangs.** The COM call is blocked waiting on something the Robot cannot satisfy. Causes: the Outlook **security prompt** ("A program is trying to send an email message on your behalf…", the Outlook Object Model Guard) is foregrounded but invisible/unanswered — fired when antivirus is out of date / not registered with Windows Security Center or programmatic-access policy is not set; Outlook is in **Work Offline** mode so the send never completes; or a slow first **profile load** exceeds the activity's `TimeoutMS` (default `30000` = 30 s).
3. **Uninitialized input.** A variable bound to `To`, `Subject`, or `Body` is `Nothing`/null (an upstream step that should have populated it was skipped or scoped wrong), or an attachment path in the `Attachments`/`Files` collection is empty/null. The activity dereferences it and throws `Object reference not set to an instance of an object`.

What to look for:

- **The exception class and message** — first signal. `Unable to cast COM object` / `Library not registered` → branch 1; a timeout / hang with no inner exception → branch 2; `NullReferenceException` at the activity → branch 3.
- **Outlook install + bitness on the Robot host** — whether the **desktop** Outlook is installed on the machine that ran the job (not the dev machine), and its bitness vs the Robot process (`File > Account > About Outlook` shows 32-/64-bit). Load-bearing for branch 1.
- **Session type (attended vs unattended) and Outlook state** — whether a security prompt or Work Offline state could be blocking the send, and whether the Robot's Windows user even has a configured Outlook profile. Load-bearing for branch 2.
- **The `To`/`Subject`/`Body` and attachment inputs** — literal vs expression-bound; trace each variable's producer and scope, and whether attachment paths resolve. Load-bearing for branch 3.
- **`TimeoutMS`** on the activity (milliseconds; default `30000`) — relevant to branch 2.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, and host.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and full message (including the inner exception). From workflow source (`.xaml`): the `Send Outlook Mail Message` node — literal vs expression-bound `To`/`Subject`/`Body`, the `Attachments` collection, the `Account`/profile, and `TimeoutMS`. From the job: the Robot **host** and whether the run was **attended or unattended**.

2. **Branch the diagnostic on the signature.**
   - `Unable to cast COM object` / `Library not registered` (`REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED`) → branch 1; go to step 3.
   - Timeout / hang with no clean inner exception → branch 2; go to step 4.
   - `NullReferenceException` at the activity → branch 3; go to step 5.

3. **Confirm branch 1 (COM cast / library not registered).** Confirm the desktop Outlook is installed on the **Robot host** (not only the developer machine) and note its **bitness** against the Robot process. A 64-bit process with a 32-bit-only Outlook (or a corrupted type library after an Office update) produces the cast / not-registered error. Check for a stray `OUTLOOK.EXE` left running with no window from a prior job.

4. **Confirm branch 2 (timeout / hang).** Determine whether the run is **unattended** (no interactive desktop). Check whether the Outlook **security prompt** could be firing (antivirus state / programmatic-access policy), whether Outlook is in **Work Offline** mode, and whether the Robot's Windows user has a configured profile. Read `TimeoutMS` and compare against a realistic profile-load + send time. A hang on an unattended Robot with no visible Outlook is the prototypical case.

5. **Confirm branch 3 (uninitialized input).** In the workflow source, trace the variables bound to `To`, `Subject`, `Body`, and each attachment path back to their producers. A variable left `Nothing` (upstream step skipped, or declared in an inner scope) or an empty attachment path confirms the branch. Reproduce by hardcoding literal values into the activity fields — if the error disappears, an input was null.

The root cause must name **which of the three surfaces** the failure maps to, with the specific evidence: the exception text, the Outlook install/bitness on the Robot host, the session type and Outlook state, and the input values. A generic "Outlook failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — COM cast / library not registered:**
  - Ensure the **desktop Outlook is installed** on every Robot host that runs the process (the activity cannot work against a webmail-only account).
  - Match **bitness** — the installed Outlook must match the Robot process architecture. Re-install the matching-bitness Office, or set the project compatibility so the process matches the installed Outlook.
  - Repair the Office installation: close **both** UiPath (Studio/Robot) and Outlook, run a **Quick Repair** of Microsoft Office (`Windows Settings > Installed apps > Microsoft Office > Modify > Quick Repair`), then restart the host.
  - Clear any orphaned `OUTLOOK.EXE` before the run (Task Manager / `Stop-Process -Name OUTLOOK -Force` as the Robot's Windows user) and fix whatever leaves it orphaned.

- **Branch 2 — Activity times out or hangs:**
  - Make sure Outlook is **running, signed in, and Online** (turn off `Send/Receive > Work Offline`) under the Robot's Windows user before the activity runs.
  - Resolve the **security prompt** at its source rather than waiting on it: keep antivirus up to date and registered with Windows Security Center (this is what normally suppresses the Object Model Guard prompt), or set the Outlook programmatic-access / Trust Center policy via Group Policy for the Robot's user. Do **not** rely on a human dismissing the prompt on an unattended Robot.
  - If the send is **legitimately** slow (first profile load), raise `TimeoutMS` above the worst observed duration (it is in **milliseconds**: `60000` = 60 s). Raising the timeout does **not** fix a blocking security prompt or Work Offline state — only branch-2 *slowness*.

- **Branch 3 — Uninitialized input:**
  - Initialize every variable bound to `To`, `Subject`, and `Body` before the activity, and guard against null/empty (a null `To` is the most common). Validate it by hardcoding literal values into the fields first.
  - Ensure each attachment path in the `Attachments`/`Files` collection is non-empty and resolves to an existing file at runtime; drop the attachment input entirely when there is nothing to attach rather than passing an empty string.

### Alternative — bypass Outlook with SMTP or modern Graph

If the COM/interop errors persist (or the process runs **unattended**), avoid the Outlook desktop dependency entirely:

- **Send SMTP Mail Message** (`UiPath.Mail.SMTP.Activities`) — sends straight to your mail server; no Outlook install or profile needed. Configure the SMTP host (e.g. `smtp.office365.com`), port (`587` with STARTTLS), and credentials.
- **Modern Graph** — the **o365-activities** (`UiPath.MicrosoftOffice365.Activities`) send mail via OAuth-authenticated Microsoft Graph, with no desktop client. Prefer these for server-side / unattended automation.

## Anti-patterns (what NOT to do)

- **"Just raise `TimeoutMS` until it works."** A larger timeout only helps a *legitimately slow* send (branch 2). For a blocking security prompt or Work Offline state it just makes the Robot hang longer before failing — fix the prompt/offline state instead.
- **"Wrap Send Outlook Mail in a Try Catch and continue."** Swallowing the exception turns a non-sent email into a silent success; downstream logic assumes the mail went out. Use Try-Catch only with a real recovery path (retry a transient COM state, fall back to SMTP, mark the item Failed, or re-throw).
- **"Disable the Outlook security prompt by lowering Programmatic Access to 'Never warn me'."** Doing this by hand on each host is brittle and a security regression; the supported fix is up-to-date antivirus registered with Windows Security Center, or a Group Policy for the Robot's user.
- **"Use Send Outlook Mail on an unattended server with no Outlook."** The activity requires the desktop client and a profile; on headless/unattended hosts use **Send SMTP Mail Message** or the modern Graph **o365-activities** instead.

## Prevention (cross-branch)

- For unattended / server-side mail, default to **Send SMTP Mail Message** or the modern Graph **o365-activities** — reserve the Outlook COM activities for attended desktop automations that genuinely need the user's Outlook.
- Provision every Robot host that uses the Outlook activities with a **matching-bitness desktop Outlook** and a configured profile for the Robot's Windows user; verify at provisioning, not at first failure.
- Keep antivirus current and registered with Windows Security Center (or set the programmatic-access Group Policy) so the Object Model Guard prompt never fires unattended.
- Initialize and validate `To`/`Subject`/`Body` and attachment paths before the activity; never pass an empty attachment path.

## Related

- [o365-activities overview](../../o365-activities/overview.md) — modern Microsoft Graph / OAuth mail (no desktop Outlook); the preferred path for unattended mail and the destination when migrating off the COM activities.
- [mail-activities overview](../overview.md) — the package's connection model (Outlook desktop COM vs SMTP/protocol) and how to choose between them.
