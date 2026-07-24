# Mail Activities (classic)

Activities from the classic mail packages that talk to a mail system directly from the Robot — distinct from the modern Graph/OAuth activities in **o365-activities** (`UiPath.MicrosoftOffice365.Activities`) and the Gmail activities in **gsuite-activities**. The classic mail packages are:

- **Outlook (desktop COM)** — `UiPath.Mail.Outlook.Activities`. Drives the locally installed **Outlook desktop application** through COM interop: `Send Outlook Mail Message` (`SendOutlookMail`), `Get Outlook Mail Messages` (`GetOutlookMailMessages`), `Move Outlook Mail Message`, `Reply To Outlook Mail Message`, `Mark Outlook As Read`. Requires Outlook installed **and** a configured mail profile in the session the Robot runs as.
- **SMTP / IMAP / POP3 / Exchange** — `UiPath.Mail.SMTP.Activities` (`Send SMTP Mail Message`), `UiPath.Mail.IMAP.Activities`, `UiPath.Mail.POP3.Activities`, `UiPath.Mail.EWS.Activities`. Protocol-level mail that talks to a mail server directly, with no desktop client dependency.

## How Outlook (desktop COM) activities run

`Send Outlook Mail Message` does **not** call a mail API. It:

1. Attaches to (or launches) the local **OUTLOOK.EXE** via COM interop, under the Windows user the Robot runs as.
2. Uses that user's default (or a named) **Outlook profile / account** to compose and send the message through the Outlook Object Model.
3. Returns when Outlook accepts the item into the Outbox / Sent Items.

Because the call goes through the desktop application, failures cluster around the **COM layer** (Outlook installed/registered, process bitness, orphaned `OUTLOOK.EXE`), the **session/UI** (a security prompt or Work Offline state blocking the call), and the **inputs** (uninitialized `To`/`Subject`/`Body` or a bad attachment path). This makes the Outlook COM activities fragile on unattended Robots, where there is no interactive desktop to dismiss a prompt.

> For unattended or server-side mail with no Outlook install, prefer **Send SMTP Mail Message** (`UiPath.Mail.SMTP.Activities`) or the modern Graph **o365-activities** — both avoid the desktop COM dependency entirely.

## Common Failure Families

- **COM cast / library not registered** — `Unable to cast COM object …` / `Library not registered` (`REGDB_E_CLASSNOTREG`, `TYPE_E_LIBNOTREGISTERED`). Outlook not installed/registered, a process-vs-Outlook **bitness** mismatch, corrupted Office registry/type-library, or an orphaned `OUTLOOK.EXE` from a prior run.
- **Timeout / hang** — the activity blocks until `TimeoutMS` elapses. A hidden security prompt ("A program is trying to send an email message on your behalf"), Outlook in **Work Offline** mode, or a slow first-launch of the profile.
- **Uninitialized input** — `Object reference not set to an instance of an object` from a null `To`/`Subject`/`Body` variable or an empty/null attachment path.
- **SMTP protocol failures (`Send SMTP Mail Message`)** — server-side, not COM: `System.Net.Mail.SmtpException` carrying an SMTP status code. `535 5.7.3` (bad credentials); `535 5.7.139` / `534 5.7.9` (Basic Auth / SMTP AUTH disabled — M365/Gmail need SMTP AUTH enabled, an app password, or OAuth2/Graph, NOT a password fix); `Failure sending mail` wrapping a `SocketException` / TLS handshake (wrong `Port`↔`SecureConnection` pairing — 587/StartTls, 465/SSL, 25/None — or unreachable server); `550 5.7.1 Unable to relay` / `5.7.60` (relay / send-as not permitted); `550 5.1.1` / `552` / attachment `FileNotFoundException` (recipient/attachment/size); and `ArgumentException`/`NullReferenceException` from an empty `Server`/`From`/`To`. See [send-smtp-mail-failures.md](./playbooks/send-smtp-mail-failures.md).

## Package

NuGet: `UiPath.Mail.Outlook.Activities` (desktop COM), `UiPath.Mail.SMTP.Activities` (SMTP), `UiPath.Mail.IMAP.Activities` / `UiPath.Mail.POP3.Activities` / `UiPath.Mail.EWS.Activities` (protocol). The Outlook COM activities require Outlook installed and a profile on the Robot host; protocol activities require only network access to the mail server.
