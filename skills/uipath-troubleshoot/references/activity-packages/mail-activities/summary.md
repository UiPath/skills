# Mail Activities Playbooks

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Send Outlook Mail Message Failures | Medium | `Send Outlook Mail Message` (`SendOutlookMail`, `UiPath.Mail.Outlook.Activities`) fails across three surfaces: COM cast / library-not-registered (`Unable to cast COM object` / `Library not registered` — Outlook not installed/registered, process-vs-Outlook bitness mismatch, corrupted Office registry, or orphaned `OUTLOOK.EXE`); activity times out or hangs (hidden "a program is trying to send an email" security prompt, Work Offline mode, or slow profile load); and `Object reference not set to an instance of an object` from an uninitialized `To`/`Subject`/`Body` or empty attachment path. Includes the `Send SMTP Mail Message` / modern Graph fallback for unattended runs. | [send-outlook-mail-failures.md](./playbooks/send-outlook-mail-failures.md) |
