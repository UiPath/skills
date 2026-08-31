# Final Resolution

---

**Root Cause:** The `Delete Outlook Mail Message` activity in `Main.xaml`
targets a message in the shared mailbox `ap-shared@contoso.com` (its address
is correctly set in the `Account` property). The shared mailbox opens, the
target message is found, but the delete is **denied** because the Robot
account `UIPATH\ROBOTUSER1` has **Send-As** but **not Full Access (delete)**
rights on that shared mailbox. The COM layer surfaces the denial as
`You do not have sufficient permission to perform this operation on this
object.` ->
`System.Runtime.InteropServices.COMException: Access is denied. (Exception
from HRESULT: 0x80070005 (E_ACCESSDENIED))`.

This maps to:
`references/activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md`
Branch 5 (Mailbox permission / access denied).

**What went wrong:** The `SharedInboxArchiver` job (started
2026-06-04T15:15:00Z) faulted ~3 seconds after launch when its
`Delete Outlook Mail Message` activity tried to delete a processed message
from the shared mailbox. `Get Outlook Mail Messages` succeeded — the read
path needs only the access the account already has — so the failure looks
like it appears only at the delete step.

**Why:** Send-As lets the account send mail as the shared mailbox; it does
**not** grant the read/write/**delete** rights that Full Access provides.
The delete is the first operation that exercises delete rights, so the
missing permission only surfaces there.

---

**This is NOT the other branches:**

- **NOT Branch 1 (stale message reference).** The job log shows the target
  message **WAS resolved/found** in `ap-shared@contoso.com\Inbox`
  immediately before the delete — there is no `An object could not be found`
  error and no fetch-to-delete gap. The object exists; the account simply
  cannot delete it.
- **NOT Branch 2 (collection modified inside a loop).** `Main.xaml` deletes a
  single message after `Get Outlook Mail Messages`; there is no `For Each`
  mutating the live collection, and no `Collection was modified` error.
- **NOT Branch 3 (New Outlook).** There is no post-update break and no
  COM-bind failure — the COM call reaches Outlook, opens the shared mailbox,
  and is rejected with an access error.
- **NOT Branch 4 (COM session blocked / privilege / hang).** There is no
  timeout or freeze; the job faults fast with a clean access-denied
  exception, not `The operation has timed out`.
- **NOT a folder-path typo.** The Orchestrator folder `RPA Production`
  resolved (folder key `f7a8b9c0-1234-4e5f-8a6b-7c8d9e0f1021`) and the
  shared mailbox + message resolved at runtime.
- **NOT a credential / password problem.** The Robot authenticated and ran;
  the read worked. This is a mailbox-rights gap, not a sign-in failure.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: SharedInboxArchiver -- Faulted at 2026-06-04T15:15:03.140Z (ran ~3.0 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Robot identity: `UIPATH\ROBOTUSER1` (`RobotUser1`)
- Folder: RPA Production (key `f7a8b9c0-1234-4e5f-8a6b-7c8d9e0f1021`)
- Final error: `Delete Outlook Mail Message: You do not have sufficient permission to perform this operation on this object.` -> `Main.xaml` -> `DeleteOutlookMailMessage "Delete Outlook Mail Message"` -> `Sequence "Main Sequence"` -> `Main "Main"`, with `System.Runtime.InteropServices.COMException: Access is denied. (Exception from HRESULT: 0x80070005 (E_ACCESSDENIED))`

### Mail Activities (Root Cause)
- `Main.xaml`: a `Sequence` running `Get Outlook Mail Messages` then
  `Delete Outlook Mail Message` (`DeleteOutlookMailMessage`), both with
  `Account="ap-shared@contoso.com"` — the shared mailbox address is already
  set correctly.
- Job log trail (smoking gun):
  - `[Get Outlook Mail Messages] Opened shared mailbox 'ap-shared@contoso.com' (Inbox)` — the shared mailbox **opened**.
  - `[Get Outlook Mail Messages] Retrieved 7 message(s)` — read succeeded.
  - `[Delete Outlook Mail Message] Target message resolved in 'ap-shared@contoso.com\Inbox' ...; attempting delete` — the message was **found**.
  - `[Delete Outlook Mail Message] delete denied on shared mailbox 'ap-shared@contoso.com'; the account can send-as but lacks Full Access (delete) rights` — the **denial reason**.
  - `[Delete Outlook Mail Message] You do not have sufficient permission to perform this operation on this object.` + `Access is denied (0x80070005 E_ACCESSDENIED)`.
- The read working while the delete is denied is the signature of **Send-As
  without Full Access** on a shared mailbox.

---

**Immediate fix:**

The agent cannot grant mailbox rights from Orchestrator and the user is
neither on MOCK-HOST nor an Exchange administrator. Hand the user this
IT / host check list to request.

### IT / host check list (RPA Production / MOCK-HOST / ap-shared@contoso.com)

1. **Confirm `Account` is set to the shared mailbox address.**
   - **What:** In `Main.xaml`, both `Get Outlook Mail Messages` and
     `Delete Outlook Mail Message` already set
     `Account="ap-shared@contoso.com"`. Keep it — do not remove it. This is
     correct and is not the cause; it is listed so IT knows the target.
   - **Why:** The `Account` routes the activity to the shared mailbox; the
     remaining gap is the **rights** on that mailbox, not the address.

2. **Ask the Exchange administrator to grant Full Access.**
   - **What:** Request that the Exchange admin grant the Robot's Active
     Directory account `UIPATH\ROBOTUSER1` **Full Access** permission (not
     just Send-As) on the shared mailbox `ap-shared@contoso.com`. In
     Exchange this is `Add-MailboxPermission -Identity ap-shared@contoso.com
     -User ROBOTUSER1 -AccessRights FullAccess -InheritanceType All`, run by
     the admin.
   - **Why:** Send-As lets the account send as the mailbox but does not grant
     read/write/**delete** rights. Full Access provides the delete right the
     activity needs.

3. **Confirm the grant propagated, then re-run.**
   - **What:** After the admin applies Full Access, allow for replication
     (can take time in hybrid/cached environments), then re-run
     `SharedInboxArchiver` from Orchestrator and confirm the delete succeeds.
   - **Why:** Verifies the permission gap was the only blocker.

Come back with whether the Exchange admin granted Full Access and the result
of the re-run. That confirms Branch 5 and closes the case.

---

**Preventive fix:**

1. **Provision Full Access at onboarding.** Whenever a Robot must delete from
   (or otherwise modify) a shared mailbox, request **Full Access** for the
   Robot's AD account on that mailbox up front — not just Send-As.
   - **Why:** Send-As-only is the most common reason a shared-mailbox delete
     is denied while the read works.
   - **Who:** Exchange administrator / platform team.

2. **Set `Account` to the shared address at design time.** Keep the shared
   mailbox address in the `Account` property of every mail activity that
   targets it, so the activities never fall back to the Robot's own mailbox.
   - **Why:** Removes mailbox-routing ambiguity from the failure funnel.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Robot account has Send-As but not Full Access (delete) rights on the shared mailbox `ap-shared@contoso.com`, so the delete is denied (Branch 5) | High | Confirmed (matches playbook signature; needs Exchange admin to apply the grant) | Yes | `Access is denied (0x80070005 E_ACCESSDENIED)` / "insufficient permission" on delete; job log "send-as but lacks Full Access"; mailbox opened + message found; `Account="ap-shared@contoso.com"` in `Main.xaml` | Keep `Account` as the shared address; have the Exchange admin grant `ROBOTUSER1` Full Access on `ap-shared@contoso.com` |
| H2 | Stale message reference / object not found (Branch 1) | Low | Eliminated | No | Job log shows the target message WAS resolved before the delete | n/a |

---

Would you like me to draft the IT / Exchange request as a single note you can
hand off, or clean up the `.local/investigations/` folder?
