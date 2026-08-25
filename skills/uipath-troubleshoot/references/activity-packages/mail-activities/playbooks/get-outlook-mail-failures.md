---
confidence: medium
---

# Get Outlook Mail Messages Failures

## Context

A `UiPath.Mail.Outlook.Activities` `Get Outlook Mail Messages` (`GetOutlookMailMessages`) activity reads messages from a folder of the **locally installed Outlook desktop application** through COM interop — it does not call a mail API. It resolves the `MailFolder` (and optional `Account`) against the Outlook profile of the Windows user the Robot runs as, optionally narrows the result with a `Filter` (DASL/Jet) and `Top` / `OnlyUnreadMessages`, and returns the matching `MailMessage` list. Failures cluster around **folder resolution** (the `MailFolder` / `Account` string), **volume / timeout** (`TimeoutMS` vs folder size), the **COM session** (Outlook installed + running + same privilege level), the **`Filter` syntax**, and **Cached Exchange Mode** sync (items that exist in Outlook but are not in the local cache).

This activity shares the desktop-COM surface with `Send Outlook Mail Message` — Outlook-not-running / not-registered / bitness and privilege issues are diagnosed the same way (see [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 1). What is specific to `Get` is **folder resolution**, the **`Filter`** expression, and **Cached Exchange Mode** desync. For unattended / server-side mail with no desktop Outlook, prefer the modern Graph **o365-activities** (`Get Newest Email`, folder-scoped reads).

What this looks like — Get Outlook Mail faults surface as one of these signatures:

- `The specified folder does not exist` (the configured `MailFolder` could not be resolved) — branch 1.
- `The operation has timed out` after `TimeoutMS` while pulling the message list — branch 2.
- `The Outlook application is not running` / a COM cast failure, or the activity **freezes** with no exception — branch 3.
- The activity throws on an invalid `Filter`, or returns **zero results** while a `Filter` is set even though matching mail exists — branch 4.
- **No exception**, but the activity silently misses recent (or older) messages that are clearly visible in the Outlook desktop client — branch 5.

What can cause it (cause-branches — pick the right one from evidence):

1. **Folder not resolved (`MailFolder` / `Account`).** The `MailFolder` string does not map to a real Outlook folder. Common reasons: **nested-folder syntax** — a backslash path like `Inbox\Invoices` fails on some Mail-package versions (target the top-level `Inbox` first, or use the absolute form `\\your-email@domain.com\Inbox\Invoices`); **shared / generic mailbox** — reading from a shared box requires its primary address in the `Account` field (leaving `Account` blank uses only the default profile); **language discrepancy** — the folder name must match the Outlook UI language exactly (e.g. `Posteingang`, not `Inbox`, on a German client).
2. **Timeout on a large folder.** The folder holds thousands of messages (or messages with massive attachments), so enumerating them exceeds `TimeoutMS` (default `30000` = 30 s) and Outlook lags.
3. **Outlook not running / COM session broken.** The activity needs the desktop Outlook **installed and initialized** in the Robot's session. On a fully **unattended / RDP** session the foreground COM connection can intermittently drop, or there is no running Outlook instance; a **privilege mismatch** (UiPath running elevated/as Administrator while Outlook runs as a normal user, or vice versa) makes Windows block the two processes from talking — surfacing as "Outlook is not running" or a freeze. (Install / registration / bitness problems are the same surface as `Send Outlook Mail` branch 1.)
4. **Malformed `Filter` (DASL / Jet).** The `Filter` property expects valid DASL/Jet query syntax. An unescaped or unquoted value (`[Subject] = VarSubject`) is invalid and the activity errors or returns zero results; the value must be single-quoted (`[Subject] = 'Text'`).
5. **Cached Exchange Mode desync.** With **Cached Exchange Mode** on and the **Offline Settings** slider restricted (e.g. "Mail to keep offline: 3 months"), messages outside that window are not in the local `.ost` cache, so the activity cannot see mail the user can see in the full client — **no error**, just missing results.

What to look for:

- **The exception text (or its absence).** "specified folder does not exist" → branch 1; "operation has timed out" → branch 2; "Outlook is not running" / COM cast / a hang → branch 3; a `Filter`-related error or zero-results-with-a-filter → branch 4; **no error but missing recent/old mail** → branch 5.
- **`MailFolder` + `Account`** (literal values, from `Main.xaml`) — the folder string (nested? absolute? localized?) and whether `Account` is set for a shared mailbox.
- **Folder volume and `Top` / `OnlyUnreadMessages` / `TimeoutMS`** — the message count in the target folder vs the timeout and `Top`. Load-bearing for branch 2.
- **Session type and privilege** — attended vs unattended/RDP, whether a desktop Outlook is running for the Robot's user, and whether UiPath and Outlook run at the **same privilege level**. Load-bearing for branch 3.
- **The `Filter` string** — DASL/Jet validity and value quoting. Load-bearing for branch 4.
- **Cached Exchange Mode state** — whether the account uses Cached Exchange Mode and how the Offline Settings slider is set. Load-bearing for branch 5 (and only verifiable on the host).

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error (or confirm there is none), the activity config, and the host.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and message, or note that the job ended without one. From workflow source (`.xaml`): the `Get Outlook Mail Messages` node — `MailFolder`, `Account`, `Filter`, `Top`, `OnlyUnreadMessages`, `TimeoutMS`. From the job: the Robot **host** and whether the run was **attended or unattended**.

2. **Branch the diagnostic on the signature.**
   - `The specified folder does not exist` → branch 1; go to step 3.
   - `The operation has timed out` → branch 2; go to step 4.
   - `Outlook is not running` / COM cast / a hang → branch 3; go to step 5.
   - `Filter` error, or zero results with a `Filter` set → branch 4; go to step 6.
   - No error but mail visible in the client is missing from the output → branch 5; go to step 7.

3. **Confirm branch 1 (folder not resolved).** Compare the literal `MailFolder` against the real Outlook folder tree for the target account. Check for a backslash nested path (`Inbox\Invoices`), whether the source is a **shared mailbox** (then `Account` must carry its address), and whether the folder name matches the **Outlook UI language**. Any of these mismatches confirms the branch.

4. **Confirm branch 2 (timeout on volume).** Read `TimeoutMS` and estimate the target folder's message count / attachment size. A 30 s default against a folder with thousands of messages (or large attachments) confirms the branch — especially when `Top` is high or unset and `OnlyUnreadMessages` is off.

5. **Confirm branch 3 (Outlook session / privilege).** Confirm the run is unattended/RDP and whether a desktop Outlook is running for the Robot's user, and compare the **privilege level** of UiPath vs Outlook. "Outlook is not running" / a freeze on an unattended host, or an elevation mismatch, confirms the branch. (For an install/registration/bitness cast error, follow [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 1.)

6. **Confirm branch 4 (filter syntax).** Read the `Filter` string. An unquoted value (`[Subject] = VarSubject`) or otherwise non-DASL/Jet syntax confirms the branch. Reproduce by removing the filter — if results return, the filter was the problem.

7. **Confirm branch 5 (Cached Exchange Mode desync).** Only when there is **no error** but expected messages are absent. Check (on the host) whether the account uses Cached Exchange Mode and how the Offline Settings slider is set; mail outside the cached window being missing confirms the branch.

The root cause must name **which of the five surfaces** the failure maps to, with the specific evidence: the exception text (or its absence), the `MailFolder`/`Account`/`Filter`/`Top`/`TimeoutMS` values, the session type and privilege, and the Cached Exchange Mode state. A generic "couldn't read mail" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Folder not resolved:**
  - For a **nested** folder, target the top-level folder first, or use the **absolute path** form: `\\your-email@domain.com\Inbox\Invoices` (rather than `Inbox\Invoices`, which fails on some Mail-package versions).
  - For a **shared / generic mailbox**, set the shared box's primary address in the **`Account`** field. Leave `Account` blank only to use the default Outlook profile.
  - Match the folder name to the **exact Outlook UI language** (e.g. `Posteingang` on a German client, not `Inbox`).

- **Branch 2 — Timeout on a large folder:**
  - Raise `TimeoutMS` above the worst observed enumeration time (it is in **milliseconds**: `60000` = 60 s).
  - Reduce the batch: set `Top` to a small number (e.g. `10`–`20`) instead of a high/unset value, and turn on **`OnlyUnreadMessages`** when read mail does not need parsing.
  - For a chronically huge folder, narrow with a `Filter` (branch 4) or migrate the read to the modern Graph **o365-activities**, which paginate server-side.

- **Branch 3 — Outlook session / privilege:**
  - Ensure a desktop Outlook is **running and initialized** in the Robot's session before the activity — e.g. a `Start Process` on `outlook.exe` immediately before the mail activity to guarantee a valid foreground instance.
  - Run UiPath (Studio/Robot) and Outlook at the **same privilege level** — both elevated or both normal — so Windows does not block the cross-process COM call.
  - For install / registration / bitness errors, see [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) branch 1; for unattended reliability, prefer the modern Graph **o365-activities** (no desktop dependency).

- **Branch 4 — Malformed `Filter`:**
  - Use valid DASL/Jet syntax and **single-quote** the value. Incorrect: `[Subject] = VarSubject`. Correct: `[Subject] = 'Text to find'`. With a variable: `"[Subject] = '" + mySubjectVariable + "'"`.
  - Validate the filter against a small known-matching set before running at scale.

- **Branch 5 — Cached Exchange Mode desync:**
  - In Outlook: `File > Account Settings > Account Settings > (select account) > Change > Offline Settings`. Move the **"Mail to keep offline"** slider to **All**, or temporarily turn **off Cached Exchange Mode**, then re-run to confirm the missing messages now pass through.
  - If turning the cache off fixes it, either keep it off for the Robot's profile or widen the cached window to cover the mail the automation must read.

## Anti-patterns (what NOT to do)

- **"Just raise `TimeoutMS` until it works."** A bigger timeout helps a genuinely large folder (branch 2) but does nothing for a folder that does not resolve (branch 1), a broken COM session (branch 3), a bad filter (branch 4), or a cache desync (branch 5). Confirm the branch first.
- **"Wrap Get Outlook Mail in a Try Catch and continue on empty."** Swallowing the error (or an empty result) turns a folder-resolution / filter / cache problem into downstream logic processing **zero** messages as if the mailbox were empty — a silent wrong result that is harder to find than the original fault.
- **"Run UiPath as Administrator to fix the COM error."** Elevation does not fix COM interop and often **breaks** it by creating a privilege mismatch with a normally-launched Outlook (branch 3). Match privilege levels instead.
- **"Use Get Outlook Mail Messages on an unattended server with no Outlook."** The activity requires the desktop client and a profile; for headless / unattended reads use the modern Graph **o365-activities** instead.

## Prevention (cross-branch)

- Address folders with the absolute `\\account\Inbox\Sub` form (and set `Account` for shared mailboxes), and keep folder names in the Outlook UI language — verify at design time, not at first failure.
- Bound every read with a sensible `Top` / `OnlyUnreadMessages` / `Filter` so a folder-size spike cannot time the activity out.
- For unattended automation, default to the modern Graph **o365-activities**; reserve the Outlook COM read for attended desktop automations, and keep UiPath and Outlook at the same privilege level.
- Parameterize and single-quote every `Filter` value; never concatenate an unquoted variable into a DASL/Jet expression.
- Set the Robot profile's Cached Exchange Mode window to cover the mail the automation must read (or disable the cache for that profile).

## Related

- [send-outlook-mail-failures.md](./send-outlook-mail-failures.md) — the outbound Outlook COM activity; shares the COM-not-running / not-registered / bitness / privilege surface (branch 3 here) and the SMTP/Graph fallback guidance.
- [o365-activities overview](../../o365-activities/overview.md) — modern Microsoft Graph / OAuth mail reads (`Get Newest Email`, folder-scoped reads); the preferred path for unattended mail and the destination when migrating off the COM read activity.
- [mail-activities overview](../overview.md) — the package's connection model (Outlook desktop COM vs SMTP/protocol).
