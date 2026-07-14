# Final Resolution

---

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml`
reads the `Archive` Outlook folder with `Top="5000"` and
`OnlyUnreadMessages="False"`, leaving `TimeoutMS="30000"` (the default
30s). The `Archive` folder holds roughly 18,420 messages, so enumerating
that volume cannot complete inside the 30-second window. The activity
exceeds `TimeoutMS` and faults with
`System.TimeoutException: The operation has timed out.` This is a
**volume vs timeout** failure, not a folder, account, or COM problem.

**NOT the other branches.** This is explicitly NOT:

- **Branch 1 (folder not resolved).** The error is "operation has timed
  out", not "the specified folder does not exist". `MailFolder="Archive"`
  resolves fine - the job logs show the activity successfully *started*
  enumerating the folder (it reported the item count and pulled 4,100
  items) before the timeout. The `Account` is blank but valid for the
  default profile.
- **Branch 3 (Outlook not running / COM session / privilege).** There is
  no "Outlook is not running" message, no COM cast failure, and no freeze
  with no exception - Outlook answered and began returning items. The
  cause is the size of the result set, not a broken or privilege-mismatched
  COM session.
- **Branch 4 (malformed Filter).** No `Filter` is set on the activity, so
  there is no DASL/Jet syntax to be wrong and no zero-results-with-a-filter
  symptom.
- **Branch 5 (Cached Exchange Mode desync).** That branch has **no
  exception** - mail is silently missing. Here the job hard-faults with a
  timeout, so it is not a cache-window issue.

This maps to:
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
(Branch 2 - Timeout on a large folder).

**What went wrong:** The `ArchiveMailScanner` job (started
2026-06-03T02:00:00Z) faulted ~30 seconds later, at the full
`TimeoutMS=30000` boundary, when `Get Outlook Mail Messages` could not
finish enumerating the `Archive` folder. The activity asked for up to
5,000 messages from a folder of ~18,420 items with no unread-only filter,
which is far more than a 30-second COM enumeration can return.

**Why:** `TimeoutMS` bounds how long the activity will wait for Outlook to
return the requested messages. With `Top` high (5000) and
`OnlyUnreadMessages` off, the activity tries to pull the maximum from a
huge folder; the per-item COM round-trips through the desktop Outlook add
up past 30 seconds, so the wait elapses and the activity raises the
timeout. Lowering the requested volume (or widening the window) lets the
read complete.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ArchiveMailScanner -- Faulted at 2026-06-03T02:00:30.620Z (ran for ~30.4 seconds, i.e. the full TimeoutMS window)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST, robot account `UIPATH\ROBOTUSER1`
- Folder: RPA Production (key `a9b0c1d2-3e4f-4a5b-8c6d-7e8f90123456`)
- Final error: `System.TimeoutException: The operation has timed out.` -> `Main.xaml` -> `GetOutlookMailMessages "Get Outlook Mail Messages"` -> `Sequence "Main Sequence"` -> `Main "Main"`

### Mail Activities (Root Cause)
- Activity: `GetOutlookMailMessages` (DisplayName: "Get Outlook Mail Messages"), package `UiPath.Mail.Activities`
- From `Main.xaml`: `MailFolder="Archive"`, `Account=""`, `Top="5000"`, `OnlyUnreadMessages="False"`, `TimeoutMS="30000"`
- Job log (smoking gun): `[Get Outlook Mail Messages] enumerating folder 'Archive' (approx. 18,420 items); Top=5000, OnlyUnreadMessages=False`, followed by a Warn at +25s that enumeration was still running and the 30s timeout was about to be reached, then the timeout Error at +30s.
- The folder resolved and Outlook responded (4,100 of 5,000 items retrieved before the timeout) - confirming the fault is volume vs the `TimeoutMS` window, not folder resolution or a broken COM session.

---

**Immediate fix:**

1. **Raise `TimeoutMS`** on the `Get Outlook Mail Messages` activity above
   the worst observed enumeration time. It is in **milliseconds**: set it
   to `60000` (60s) or higher for this folder size.
2. **Reduce the batch** so the read fits the window:
   - Set `Top` to a small number (e.g. `10`-`20`) instead of `5000`.
   - Turn on `OnlyUnreadMessages` if only unread mail needs processing.
3. For a chronically huge folder like `Archive`, **narrow with a `Filter`**
   (e.g. a date-bounded DASL/Jet expression - single-quote the value) so
   the activity never enumerates the whole folder, or **migrate the read
   to the modern Graph o365-activities** (`Get Newest Email`,
   folder-scoped reads), which paginate server-side and have no desktop
   Outlook dependency.

Combining a higher `TimeoutMS` with a smaller `Top` / `OnlyUnreadMessages`
is the durable fix - raising the timeout alone leaves the activity
enumerating ~18k items on every run, which will keep getting slower as the
folder grows.

---

**Preventive fix:**

1. **Studio** -- bound every `Get Outlook Mail Messages` read with a
   sensible `Top` / `OnlyUnreadMessages` / `Filter` so a folder-size spike
   cannot time the activity out. Never leave `Top` high/unset against a
   folder that grows unbounded.
   - **Why:** Volume-vs-timeout is the most common Get Outlook Mail fault
     on large mailboxes.
   - **Who:** RPA developer

2. **Architecture** -- for unattended automation default to the modern
   Graph **o365-activities**, which paginate server-side and avoid the
   desktop COM enumeration cost entirely.
   - **Why:** Removes the timeout class for large folders and the desktop
     Outlook dependency.
   - **Who:** RPA developer / solution architect

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Get Outlook Mail Messages` timed out enumerating the large `Archive` folder (~18,420 items) because `Top=5000` and `OnlyUnreadMessages=False` against the default `TimeoutMS=30000` | High | Confirmed | Yes | `System.TimeoutException: The operation has timed out.` after the full 30s window + job-log volume line (`approx. 18,420 items; Top=5000`) + `Main.xaml` `Top="5000"` / `TimeoutMS="30000"` | Raise `TimeoutMS` (>= 60000) AND reduce the batch (`Top` ~10-20, enable `OnlyUnreadMessages`, or add a `Filter`) |
| H2 | Folder `Archive` did not resolve (Branch 1) | Low | Eliminated | No | Error is a timeout, not "specified folder does not exist"; logs show the folder enumerated and 4,100 items returned | n/a |
| H3 | Outlook not running / COM session broken (Branch 3) | Low | Eliminated | No | No "Outlook is not running" / COM cast / freeze; Outlook responded and returned items before the timeout | n/a |

---

Would you like me to draft the `Main.xaml` edit (raise `TimeoutMS`, lower
`Top`, enable `OnlyUnreadMessages`) as a diff you can apply, or clean up the
`.local/investigations/` folder?
