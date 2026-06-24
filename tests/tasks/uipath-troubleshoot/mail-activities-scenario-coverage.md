# Mail Activities — Replay Scenario Coverage

Live-repro coverage for the `UiPath.Mail` Diagnose-Agent playbooks. Decision:
**live-repro only** — ship a faithful-replay scenario only for faults
reproducible on the available environment (a staging tenant with a connected
unattended robot serving folder Shared, .NET 8 runtime, **no**
Gmail/Graph/Exchange Integration Service connection, **no** Outlook desktop).
Everything else is an explicit, reasoned skip below.

All mail **playbooks** are authored and committed regardless; this table is about
the accompanying coder-eval **scenarios**.

> **Environment finding:** all SMTP/IMAP/Exchange activities ship in the single
> `UiPath.Mail.Activities` NuGet package (the `UiPath.Mail.{SMTP,IMAP,Exchange}.Activities`
> names are namespaces). The repro project pins only `UiPath.Mail.Activities`.

| Activity | Exceptions | Live scenario | Why |
|----------|-----------|---------------|-----|
| GetIMAPMailMessages | `SslHandshakeException`, **`TimeoutException`**, `ImapProtocolException`, `AuthenticationException` | ✅ `mail-imap-timeout` | Reproduced on the robot: `imap.gmail.com:143` + `SecureConnection=SslOnConnect` → raw `System.TimeoutException` from the `TimeoutMS` guard. Public endpoint, no auth/consent needed. |
| SendMail (SMTP) | `ArgumentException`, `Null/ArgumentNull/NullReference`, `SslHandshakeException`, `SmtpCommandException`, `KeyNotFoundException`, **`FormatException`** | ✅ `mail-smtp-malformed-recipient` | Reproduced via the **`FormatException`** branch: `To="finance team distribution list"` (a description, not an address) → `MailAddressParser` rejects it at message build, before any connect. Pure input fault, no network. **SSL-handshake branch NOT reproducible here** (see note below). |
| SaveMail | `ArgumentException` | ❌ skip | On .NET 8 an illegal-char `FilePath` does **not** throw `ArgumentException` (Windows treats `name:x` as an NTFS alternate-data-stream; the write succeeds). The `ArgumentException` is a .NET Framework / older-runtime signature not reproducible on the modern (`targetFramework: Windows` = .NET 8) robot. |
| Business.CreateHtmlContent | `ArgumentException` | ❌ skip | Not a standalone top-level activity — it is the HTML-body sub-editor (`HtmlContentArgument`) inside `Send Mail`. Cannot be packaged/run as a standalone entry point to fault in isolation. |
| Business.OutlookApplicationCard | `SystemException`, `COMException` | ❌ skip | Requires the **Outlook desktop** client + a configured profile on the robot host; the unattended robot has no Outlook install / interactive session. Un-stageable. |
| Business.ForEachEmailX | `TimeoutException`, `SystemException` | ❌ skip | Requires a live provider connection (Outlook/Graph/Gmail/Exchange) supplying an email collection to iterate. No mail-provider connection available. |
| SaveMailAttachments | `IOException` | ❌ skip | Requires a `MailMessage` **with attachments** sourced from a provider, then a disk condition (lock / path-too-long). The provider half is un-stageable without a connection. |
| Business.SendMailX | `ObjectDisposedException`, `Microsoft.Graph.ServiceException`, `Google.GoogleApiException` | ❌ skip | Provider-specific: needs a Graph (o365) or Gmail connection. None provisioned; Graph send also needs consent. Un-stageable. |
| GetExchangeMailMessages | `ServiceVersionException`, `AggregateException`, `ServiceResponseException`, `ExchangeException` | ❌ skip | Requires a reachable Exchange/EWS endpoint + Basic/OAuth credentials. No Exchange environment. |
| SendExchangeMail | `UriFormatException`, `MsalClientException`, `ServiceRequestException`, `Null/ArgumentNull/Argument`, `KeyNotFoundException`, `FileNotFoundException`, `ExchangeException` | ❌ skip | Same EWS/MSAL dependency; OAuth/autodiscover/endpoint not available. |
| MoveIMAPMailMessageToFolder | `ImapCommandException`, `IOException` | ❌ skip | Requires an **authenticated** IMAP session (valid app-password mailbox) holding a real message to move; the `ImapCommandException` path is only reachable after a successful connect+auth. No app-password mailbox provisioned. |

## How to lift the skips later

- **SendMailX / GetExchangeMailMessages / SendExchangeMail / ForEachEmailX** —
  provision an Integration Service connection (Gmail app-password, Graph/o365
  OAuth, or an Exchange/EWS endpoint) on the tenant, then run the pipeline in
  `tests/tasks/uipath-troubleshoot/PLAYBOOK-VALIDATION-PIPELINE.md`.
- **SaveMail / SaveMailAttachments** — repro on a **Windows-Legacy (.NET
  Framework 4.6.1)** robot where the file-path `ArgumentException` / `IOException`
  signatures match the field-observed failures.
- **OutlookApplicationCard** — a robot host with Classic Outlook desktop installed.
- **MoveIMAPMailMessageToFolder** — a Gmail/IMAP app-password mailbox for
  authenticated IMAP moves.

## SSL-handshake branch finding (IMAP/SMTP TLS)

The `SslHandshakeException` branch of the IMAP/SMTP playbooks is **not
reproducible on this .NET 8 runtime**. Two deterministic attempts —
`SslOnConnect` against a plaintext port (`imap.gmail.com:143`), and against an
expired-cert TLS host (`expired.badssl.com:443`) — **both surfaced as
`System.TimeoutException`** (the activity's `TimeoutMS` guard firing), not a fast
`SslHandshakeException`. The UiPath Mail activities appear to use a lenient
certificate path and then hang on the post-handshake protocol read until the
guard trips. A genuine `SslHandshakeException` repro would need a TLS endpoint
that fails the handshake *itself* fast (protocol/cipher/version rejection) — not
covered here. The `get-imap-mail-messages-failures` / `send-smtp-mail-failures`
playbooks document `SslHandshakeException` from source; it is just not
live-reproducible on this environment.
