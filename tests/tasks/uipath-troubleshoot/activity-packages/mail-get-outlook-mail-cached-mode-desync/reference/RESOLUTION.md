# Final Resolution

---

**Root Cause:** The `ComplianceMailExport` job ends **Successful with no
error**, but the `Get Outlook Mail Messages` activity returns only the
**locally cached subset** of the Inbox. The Robot's Outlook account runs
in **Cached Exchange Mode** with a **restricted Offline Settings window**
("Mail to keep offline" set to a few months), so mail outside that window
is never synced into the local `.ost` cache. The activity reads from
Outlook's local store through COM, so it can only see what the cache
holds - it cannot see mail the user sees in the full online client. This
is **Branch 5 (Cached Exchange Mode desync)** of the
`get-outlook-mail-failures` playbook.

**What went wrong:** The job (started 2026-06-03T05:30:00Z) completed
cleanly in ~6 seconds and reported `Messages retrieved: 142.`. There is
no fault, no warning, no error log. But the user sees far more mail in
the Outlook desktop client, including recent items, none of which appear
in the export. The job-log line
`[Get Outlook Mail Messages] retrieved 142 messages from 'Inbox'
(Top=500, no filter); oldest item dated 2026-03-03` is the tell: the
oldest returned item sits ~3 months back, which is the edge of a
restricted offline-sync window, and the count is far below the real Inbox
size.

**Why it is NOT the other branches (ruled out):**

- **NOT Branch 1 (folder not resolved).** The job log shows
  `resolved folder 'Inbox' on the default account`. The folder is the
  correct top-level `Inbox`, not a nested/localized/shared-mailbox path.
- **NOT Branch 2 (timeout).** The job ended **Successful**, not faulted,
  and ran only ~6 seconds. Nothing timed out.
- **NOT Branch 3 (Outlook not running / COM session broken).** Outlook
  attached and the read completed without a COM error or hang.
- **NOT Branch 4 (malformed `Filter`).** `Main.xaml` sets **no `Filter`**
  at all, so there is no DASL/Jet expression to be wrong, and the result
  is not zero - it is a partial result.
- **NOT a "`Top` too low" problem.** `Top="500"` is high; only 142
  messages came back, so `Top` is not the limiter.
- **NOT "add/fix a `Filter`."** There is no filter and none is needed -
  adding one would only narrow the result further.
- **NOT "the mailbox is small / those emails do not exist."** The user
  confirms the missing mail is visible in the Outlook desktop client; the
  mail exists, it is simply not in the local cache.

This is **not a workflow fix** - the workflow is correct. The fix is on
the **host**, in the Robot's Outlook account configuration, and can only
be confirmed there.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ComplianceMailExport -- **Successful** at 2026-06-03T05:30:06.420Z
  (ran ~6.3 seconds)
- Job type: Unattended, scheduled, on machine MOCK-HOST, robot identity
  `UIPATH\ROBOTUSER1` / `RobotUser1`
- Folder: RPA Production (key `a5b6c7d8-9e0f-4a1b-8c2d-3e4f5a6b7c8d`)
- `Info`: `ComplianceMailExport completed. Messages retrieved: 142.`
  (benign success message)
- Error-level job logs: **empty** -- there is no error to find.
- No Faulted job exists for this folder (the Faulted job list is empty);
  the run under investigation is a Successful one.

### Mail Activities (Root Cause)
- Activity: `GetOutlookMailMessages` (DisplayName: "Get Outlook Mail
  Messages") in `Main.xaml`
- `MailFolder="Inbox"` (correct, resolved per the job log)
- `Account=""` (default profile)
- `Top="500"` (high -- not the limiter)
- **No `Filter`** property set
- `OnlyUnreadMessages="False"`
- Signal in the full job logs:
  `[Get Outlook Mail Messages] retrieved 142 messages from 'Inbox'
  (Top=500, no filter); oldest item dated 2026-03-03` -- far fewer than
  the Inbox holds, with the oldest item right at a ~3-month cache cutoff.

---

**Immediate fix:**

The agent cannot read the Robot's Outlook account configuration from
Orchestrator alone. Hand the user this host-side check to run the next
time they are in front of MOCK-HOST under the robot's Windows user.

### Host-side check list (RPA Production / MOCK-HOST, robot's Windows user)

1. **Inspect Cached Exchange Mode and the Offline Settings window.**
   - **What:** In Outlook, go to
     `File > Account Settings > Account Settings > (select the account) >
     Change > Offline Settings`. Note whether **Cached Exchange Mode** is
     on and where the **"Mail to keep offline"** slider sits (e.g.
     `3 months`).
   - **Why:** With the slider restricted, mail older than that window is
     not in the local `.ost`, so the activity cannot see it even though
     the full online client can.

2. **Widen the cache (or turn it off) and re-run.**
   - **What:** Move the **"Mail to keep offline"** slider to **All**, or
     temporarily **uncheck Cached Exchange Mode**. Let Outlook finish
     syncing, then re-run the process from Orchestrator and compare the
     retrieved count to the real Inbox size.
   - **Why:** If the missing mail now appears in the export, Branch 5
     (cache desync) is confirmed. If turning the cache off fixes it, keep
     it off for the robot's profile or widen the window to cover the mail
     the automation must read.

3. **(Optional, longer-term) Move the read to Microsoft Graph.**
   - **What:** Replace the desktop-COM `Get Outlook Mail Messages` with
     the modern Graph **o365-activities** (`Get Newest Email`,
     folder-scoped reads).
   - **Why:** Graph reads are **server-side** and not bound to the local
     cache window, so they return the full mailbox regardless of Cached
     Exchange Mode - the robust path for unattended mail export.

Come back with what step 1 showed (Cached Exchange Mode state + slider
position) and whether step 2 restored the missing mail. That confirms the
branch and produces the final fix.

> The agent did not change any host setting - it cannot, from
> Orchestrator. The above is a check list for the user to run on the host.

---

**Preventive fix:**

1. **Robot profile provisioning** -- on the robot's Outlook profile, set
   the Cached Exchange Mode "Mail to keep offline" window to **All** (or
   disable Cached Exchange Mode for that profile), so no mail the
   automation must read ever falls outside the local cache.
   - **Why:** Removes the silent-shortfall failure mode entirely.
   - **Who:** Platform / robot host team.

2. **Studio / architecture** -- for unattended mail export, default to
   the Microsoft Graph **o365-activities** rather than the desktop-COM
   read activity, so the read is server-side and cache-independent.
   - **Why:** Eliminates the desktop dependency and the cache window as a
     correctness factor.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Cached Exchange Mode with a restricted Offline Settings window means out-of-window Inbox mail is not in the local `.ost`, so the activity silently returns only the cached subset (Branch 5) | High | Confirmed (matches playbook signature; pending host-side verification of the Offline Settings slider) | Yes | Successful job + empty error logs + `retrieved 142 messages ... oldest item dated 2026-03-03` against `Top=500`/no Filter/folder resolved in `Main.xaml` | Widen the Offline Settings slider to All / disable Cached Exchange Mode and re-run; or move to Graph o365 reads |
| H2 | Workflow-side limiter (`Top` too low, a `Filter`, wrong/nested folder) | High | Eliminated | No | `Top="500"` (high), **no `Filter`**, `MailFolder="Inbox"` resolved per the job log | n/a -- workflow is correct |

---

Would you like me to draft the host-check note as a single document you
can hand off, or clean up the `.local/investigations/` folder?
