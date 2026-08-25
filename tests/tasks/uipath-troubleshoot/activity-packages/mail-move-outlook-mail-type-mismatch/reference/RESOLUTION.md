# Final Resolution

---

**Root Cause:** After the team updated the mail packages, the
`InboxAutoFiler` workflow mixed the classic and modern mail activity
families. `Main.xaml` now uses the **modern Move Email** activity
(`MoveEmailConnections`, from `UiPath.MicrosoftOffice365.Activities`),
whose message input expects an **`Office365Message` / `IResource`**
object reference. But the workflow wires a **`String`** variable
(`messageId`, holding a text message-ID) into that input -- the
binding left over from the classic design. At runtime the activity
cannot convert the String to the resource type and throws:

`Cannot convert type 'System.String' to
'UiPath.MicrosoftOffice365.Models.Office365Message'.`
(`System.InvalidCastException`)

This is a **type mismatch**, not a bad value. The message-ID string is
well-formed; the problem is that a modern resource-typed property was
fed a plain `String`.

This maps to:
`references/activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md`
-- **Branch 3 (modern-vs-classic type mismatch)**.

**What this is NOT:**

- **Not Branch 1 (COM session loss / Outlook not running).** There is
  no "operation failed" / "folder does not exist" COM error and no
  intermittency -- it fails deterministically, every run, with a
  `convert/cast` error, not a session error.
- **Not Branch 2 (folder path / `Account` typo).** The destination
  `DestinationMailFolder` (`Inbox\Processed`) resolves fine; the fault
  is on the **message** input, and it is a type-conversion error, not a
  "folder does not exist" error.
- **Not Branch 4 (New Outlook removed the desktop COM API).** There is
  no COM-bind / "Outlook is not running" failure and no post-OS-update
  break; the trigger was a **package** update, and the modern Graph
  activity does not use desktop COM at all.
- **Not a wrong or empty message ID.** The value
  (`AAMkAGI2...`) is a valid message-ID string. The **type** is wrong,
  not the value -- a different message ID would fail identically.
- **Not an authentication, permission, or connectivity issue.** The
  exception is `InvalidCastException` raised before any Graph call, not
  an auth/permission/network error.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `InboxAutoFiler` -- Faulted at 2026-06-04T09:10:02.260Z (ran
  ~2.1 seconds after start at 09:10:00.140Z).
- Job type: Unattended, triggered by a scheduled trigger on machine
  `MOCK-HOST`; account `UIPATH\ROBOTUSER1` / `RobotUser1`.
- Folder: `RPA Production` (key
  `f1a2b3c4-5d6e-4f7a-8b9c-9d0e1f2a3b4c`).
- Final error: `Move Email: Cannot convert type 'System.String' to
  'UiPath.MicrosoftOffice365.Models.Office365Message'.` ->
  `MoveEmailConnections "Move Email"` -> `Sequence "Main Sequence"` ->
  `Main "Main"`, wrapping `System.InvalidCastException`.

### Mail Activities (Root Cause)
- Activity: `MoveEmailConnections` (DisplayName: "Move Email") -- the
  **modern** Move Email from `UiPath.MicrosoftOffice365.Activities`.
- Its `Message` property is bound to `[messageId]`, a **`String`**
  variable -- not the `Office365Message` output of a read activity.
- `project.json` carries **both** mail families:
  `UiPath.Mail.Activities` `[1.18.3]` (classic) and
  `UiPath.MicrosoftOffice365.Activities` `[2.3.6]` (modern) -- the
  classic-vs-modern mix that produced the binding left over after the
  update.
- Job logs echo the binding directly:
  `[Move Email] message input bound to String 'AAMkAGI2...' but the
  activity expects an Office365Message resource` -- the
  String-where-a-resource-is-expected is visible in the run.

---

**Immediate fix:**

Make the modern Move Email's message input resolve to the object type
it expects, OR move back to the classic activity that accepts strings.

1. **Map the resource with the `+` (plus) picker.**
   - In the **Move Email** activity, do not bind a `String` to the
     `Message` (and folder) property. Click the **`+` (plus)** button
     next to the property and pick the message via the resource /
     directory picker so the binding resolves to the expected
     `Office365Message` / `IResource` object. Typically the message
     comes from a preceding modern read activity that outputs an
     `Office365Message`; wire that output in.

2. **Or switch to the classic `Move Outlook Mail Message`.**
   - If your variables are explicit `String` / `MailMessage` types,
     replace the modern Move Email with the **classic**
     `Move Outlook Mail Message` (`MoveOutlookMessage`,
     `UiPath.Mail.Outlook.Activities`), which accepts a `MailMessage`
     (and string folder path) directly. Do not mix classic string
     inputs into modern resource-typed properties.

Either path makes the activity's input type match its binding and
clears the `InvalidCastException`.

---

**Preventive fix:**

1. **Studio** -- keep classic and modern mail activities separate. Match
   input types to the activity family: `String` / `MailMessage` for the
   classic `Move Outlook Mail Message`; `Office365Message` / `IResource`
   (mapped via the `+` picker) for the modern Move Email. Do not carry a
   classic string binding into a modern resource-typed property.
   - **Who:** RPA developer.

2. **After any mail-package upgrade** -- re-validate every Move / Get /
   Send activity's bindings before publishing. A dependency update that
   swaps a classic activity for its modern equivalent silently leaves
   string bindings on properties that now expect resource objects;
   re-validation catches the type mismatch at design time instead of in
   a faulted Production job.
   - **Who:** RPA developer / release reviewer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The modern Move Email activity received a `String` on its message input, which expects an `Office365Message` / `IResource` object (classic/modern mix after the package update), throwing the convert/cast error | High | Confirmed | Yes | `InvalidCastException` "Cannot convert type 'System.String' to '...Office365Message'" + `[messageId]` String wired into `MoveEmailConnections` in `Main.xaml` + both mail packages in `project.json` + the job-log binding line | Map the message/folder via the `+` resource picker, or switch to the classic `Move Outlook Mail Message` with string/`MailMessage` inputs |
| H2 | The message-ID value is wrong or empty | Low | Eliminated | No | The String value is well-formed; the error is a TYPE conversion, not a missing/invalid value -- a different ID fails identically | n/a |

---

Would you like me to draft the binding-fix note as a single hand-off
document, or clean up the `.local/investigations/` folder?
