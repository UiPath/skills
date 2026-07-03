**Root Cause:** The Send Mail activity's configured attachment file `C:\Temp\missing-attachment-repro.pdf` does not exist on the runtime machine, so the activity threw `System.IO.FileNotFoundException: File does not exist: C:\Temp\missing-attachment-repro.pdf` and faulted the job.

**What went wrong:** The last job in folder Shared — process **ERN_O365_SendMailRejected** (job key 74db8e32-8535-40b2-9b40-62540456adab, run 2026-06-10 18:15 UTC, unattended, machine MOCK-HOST) — faulted in the legacy **Send Mail** (`SendMail`) activity in `O365_SendMailRejected.xaml`.

**Why:** The legacy Send Mail activity's `Attachments` property is a collection of local file paths that must exist on the robot machine. While assembling attachments — before any Microsoft Graph send call — the package's `AttachmentsHelpers.EnsureFileExists` check found the path absent and threw `FileNotFoundException`. The Microsoft 365 Scope opened normally (auth OK), and no `ErrorInvalidRecipients` / `ErrorSendAsDenied` / `ErrorMessageSizeExceeded` codes appear anywhere — the other send-rejection causes are ruled out; the failure is purely the missing local file.

**Immediate fix:** Stage the file at the configured path on the runtime machine, or correct the `Attachments` entry on the Send Mail activity to a path that exists there, then re-run. Source: `references/activity-packages/o365-activities/playbooks/send-mail-rejected.md` § Resolution ("If attachment missing").

**Preventive fix:** Avoid user-profile-relative or machine-local temp paths for attachments in unattended runs; validate/log each dynamically-built path before the Send Mail step.
