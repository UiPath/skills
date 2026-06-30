**Root Cause:** The Get Mail (`GetMail`, legacy) activity in `O365_MailMessageNotFound.xaml` dereferenced a stale message ID — the email no longer exists in the mailbox store, so Microsoft Graph returned `ErrorItemNotFound` (HTTP 404) and the job faulted.

**What went wrong:** The last job in folder Shared — process **ERN_O365_MailMessageNotFound** (job cbbaaaf6-b416-4025-9a98-c8ee50990f76, ran 2026-06-10 19:45 UTC, unattended, machine MOCK-HOST) — faulted at the "Get Mail by corrupted ID ..." activity inside the Microsoft 365 Scope with raw `Microsoft.Graph.ServiceException` — `Code: ErrorItemNotFound`, `Message: The specified object was not found in the store., The process failed to get the correct properties.`, `Status Code: NotFound`.

**Why:** The activity's `EmailId` was bound to variable `staleId` holding an ID that passes Outlook's integrity check (so not `ErrorInvalidIdMalformed`) but resolves to no message in the store — the signature of a deleted/stale message ID. The immediately preceding "Get newest email (source of a real ID)" activity succeeded against the same Inbox/connection — eliminating mailbox-mismatch (`ErrorInvalidMailboxItemId` absent), authentication, and missing-scope-as-404 branches.

**Immediate fix:** Confirm the referenced message still exists (check the mailbox incl. Deleted Items); don't persist message IDs across runs — re-fetch by filter at consumption time instead of consuming a stored/constructed ID. Source: `references/activity-packages/o365-activities/playbooks/mail-message-not-found.md` § Resolution steps 1 and 3.

**Preventive fix:** Wrap by-ID mail operations in Try/Catch with a business-exception path when the message can legitimately be gone by run time.
