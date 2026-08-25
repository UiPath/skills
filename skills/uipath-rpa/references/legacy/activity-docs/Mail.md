# UiPath Mail Activities - Legacy Reference

## Overview
Email automation supporting 6 protocols: SMTP, IMAP, POP3, Exchange/O365, Outlook (COM), Lotus Notes (COM). Package: `UiPath.Mail.Activities`.

---

## Protocol Support Matrix

| Protocol | Send | Receive | Delete | Move | Mark Read | Drafts | Shared Mailbox | Trigger | COM |
|----------|------|---------|--------|------|-----------|--------|----------------|---------|-----|
| SMTP | Y | - | - | - | - | - | - | - | - |
| IMAP | - | Y | Y | Y | Y | - | - | Y | - |
| POP3 | - | Y | Y* | - | - | - | - | - | - |
| Exchange | Y | Y | Y | Y | Y | Y | Y | - | - |
| Outlook | Y | Y | Y | Y | Y | Y | - | Y | Y |
| Lotus Notes | Y | Y | Y | Y | - | - | - | - | Y |

*POP3: delete only via `DeleteMessages` flag on retrieval

---

## Key Activities & Arguments

### SMTP - SendMail
- **Inputs**: Email, Password/SecurePassword, Server, Port, SecureConnection, To/Cc/Bcc (semicolon-separated), Subject, Body, Files, IsBodyHtml
- **Output**: StatusCode (string, e.g. "250")
- **SecureConnection**: None, Auto, SslOnConnect, StartTls, StartTlsWhenAvailable

### IMAP - GetIMAPMailMessages
- **Inputs**: Email, Password, Server, Port, MailFolder (default "Inbox"), FilterExpression, OnlyUnreadMessages (default true), Top (default 30)
- **Output**: Messages (List\<MailMessage\>)
- **FilterExpressionCharacterSet**: default US-ASCII (use UTF-8 for non-ASCII)

### POP3 - GetPOP3MailMessages
- **Inputs**: Email, Password, Server, Port, DeleteMessages (default false), Top (default 30)
- **Output**: Messages (List\<MailMessage\>)

### Exchange
- **SendExchangeMail**: Server, ExchangeVersion (2007-2021), AuthenticationType (Basic/OAuth2/Interactive), ApplicationId, DirectoryId
- **GetExchangeMailMessages**: CustomFolder (default "Inbox"), SharedMailbox, FilterExpression (requires Exchange2010+)
- **AuthTypes**: Basic, OAuth2, Interactive (requires ApplicationId)

### Outlook (COM Interop)
- **SendOutlookMail**: Account, SentOnBehalfOfName, Importance, Sensitivity, IsDraft
- **GetOutlookMailMessages**: Account, Folder, OnlyUnreadMessages, Top
- **SaveAttachementsOutlook**: Note typo in class name (historical)

### Modern X-Activities (Connection Service)
- **SendMailX**: Account (IMailQuickHandle), IsDraft (default true - doesn't send!)
- **ForEachEmailX**: NumberOfEmailsLimit (default 100, 0=all), RetrieveAttachments (default true)
- **SaveMailAttachmentsX**: Filter (regex), ExcludeInlineAttachments, OverwriteExisting

---

## Critical Gotchas

### Authentication
1. **OAuth works on direct activity properties but NOT via Integration Service connections** - UseOAuth parameter IS functional when set directly on SMTP/IMAP/POP3 activities (enables SASL XOAUTH2). However, it's **hardcoded false** in the Connection Service path (TODO PRODACTV-4005). Pass OAuth token as Password and set UseOAuth=true directly.
2. **SecurePassword takes precedence** over Password if length > 0. Note: SMTP's SendMail lacks `[OverloadGroup]` on Password/SecurePassword, so both can be set simultaneously (unlike IMAP/POP3).
3. **Addresses are semicolon-separated** (`;`) - NOT comma-separated. **Exception: Lotus Notes uses commas** (`SplitCommaSeparatedEntries`)
4. **Interactive auth requires ApplicationId** - validation error if missing

### SMTP Specific
5. **Attachments CLEARED when replying** - `if(action != MailAction.Forward) mailMessage.Attachments.Clear()`
6. **ContinueOnError** only skips RuleViolationException, NOT SmtpCommandException

### POP3 Specific
7. **No folder support** - POP3 is stateless, only downloads from inbox
8. **DeleteMessages permanent** - Once deleted on retrieval, cannot be recovered

### Exchange Specific
9. **ExchangeVersion 2007 doesn't support FilterExpression** - validation error
10. **FilterByMessageIds** is Exchange-specific format, not standard message IDs

### Outlook COM Specific
11. **PiP (Process in Process) used for session isolation** - When Robot runs in PiP mode (separate session), MainSessionServer.exe proxies COM calls to the main user session. Not specifically about 64-bit, but about session access to Outlook.
12. **Converts relative attachment paths to absolute** automatically
13. **Orphaned processes** possible if parent crashes (PiP process relies on timeout)

### Lotus Notes Specific
14. **Folder syntax is Lotus-specific**: `($Inbox)`, `(Drafts)` - NOT standard paths
15. **32-bit execution required** or PiP COM proxy

### Governance
16. **Email blocklist validation** - SendMail validates To/Cc/Bcc against organization blocklists
17. **RuleViolationException is NOT continuable** (IsContinuableException returns false)
18. **Skipped for drafts** (IsDraft=true)

### Attachment Handling
19. **Inline attachments in AlternateViews** - SaveMailAttachments includes LinkedResources unless ExcludeInlineAttachments=true
20. **Double-counting possible** - AlternateViews + Attachments may have duplicates

### Additional Discovered Gotchas
23. **OAuth2 silently falls back to password auth** - If OAuth2 authentication fails, code catches AuthenticationException and falls back to username/password. This can mask OAuth misconfiguration.
24. **Outlook session conflict** - `CanExecuteForCurrentUserInCurrentSession()` returns false if Outlook is open in another session. Activity will fail silently.
25. **NTLM auth requires explicit handling** - MailKit dropped implicit NTLM; code explicitly checks for NTLM mechanism with fallback.

### Certificate Handling
21. **IgnoreCRL** disables certificate revocation list checking (security risk)
22. **StartTlsWhenAvailable** falls back to plaintext if server doesn't support (dangerous)
