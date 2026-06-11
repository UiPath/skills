**Root Cause:** The Forward Mail activity (`UiPath.MicrosoftOffice365.Activities.Mail.ForwardMail`, legacy non-Connections) dereferenced a null `Message` input — the bound variable `originalEmail` was never assigned anywhere in the executed workflow path, so it was null when the activity tried to read the original message's ID.

**What went wrong:** The last job in folder Shared — process **ERN_O365_LegacyMailNRE** (started 2026-06-10 17:58:41 UTC, machine MOCK-HOST) — faulted ~1 second in with `System.NullReferenceException: Object reference not set to an instance of an object.`

**Why:** In `O365_LegacyMailNRE.xaml`, the activity "Forward Mail with null Message (expect NullReferenceException)" runs inside the "Microsoft 365 Scope" with its `Message` property bound to the variable `originalEmail`. The execution trace shows no producer activity ever ran — no Get Mail / Get Newest Email span before the forward — so `originalEmail` held its default (null). Legacy Mail activities don't validate inputs; the activity dereferenced the null `Message` while building the forward request (faulting ~1.3 ms in, before any Microsoft Graph call) and threw the raw NRE. The raw NRE type itself indicates a legacy activity — the Connections path remaps it to "The object used in the activity does not exist."

**Key evidence:** Stack trace top frame `UiPath.MicrosoftOffice365.Activities.Mail.ForwardMail.ExecuteAsync`; trace span attributes `Message=originalEmail`, `To=new string[]{ "recipient@example.com" }` (non-null literal — rules out the null-recipient-element cause); exactly 3 spans (job root → Microsoft 365 Scope → Forward Mail) with no upstream mail-fetch.

**Immediate fix:** Ensure a producing activity assigns `originalEmail` before the forward (add/fix the Get Mail-style producer) and add an If/null-check on `originalEmail` to handle the no-message case explicitly. Source: `references/activity-packages/o365-activities/playbooks/legacy-mail-null-reference.md` § Resolution.

**Preventive fix:** Migrate the legacy Forward Mail to the modern Connections equivalent (Forward Email), which validates inputs and reports actionable messages instead of raw NREs.
