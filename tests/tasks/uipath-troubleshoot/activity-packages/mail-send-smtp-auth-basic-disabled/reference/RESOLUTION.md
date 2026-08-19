# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Microsoft 365 rejected the `Send SMTP Mail Message` login because Basic Authentication
(SMTP AUTH) is disabled for the account — `535 5.7.139 Authentication unsuccessful ... basic
authentication is disabled`.** The credentials are correct; the auth **mechanism** is off. This is the
Basic-Auth / SMTP-AUTH-disabled sub-case of `send-smtp-mail-failures.md` **Branch 2**, NOT a wrong
password (Branch 1), a connection/TLS problem (Branch 3), or a relay/recipient issue.

The activity connected to `smtp.office365.com:587`, negotiated STARTTLS, and attempted `AUTH LOGIN` with
`svc-billing@contoso-test.com`; Microsoft 365 refused the Basic-Auth submission with the `5.7.139`
code. Retrying the password will never succeed — Microsoft has deprecated Basic-Auth SMTP.

**What went wrong:** The `AutomatedBillingNotifier` job faulted ~3 s after launch. Job logs show
`Connecting to smtp.office365.com:587 (SecureConnection=StartTls)` → `STARTTLS negotiated; authenticating
as svc-billing@contoso-test.com (Basic Auth / AUTH LOGIN)` → `Server rejected authentication: 535
5.7.139 ... [basic authentication is disabled]`. The transport (587/StartTls) is correct and the TLS
handshake succeeded — only the Basic-Auth login was refused.

**Why — and why it is NOT another branch:**
- **NOT Branch 1 (bad credentials).** The server code is `5.7.139` (mechanism disabled), not `5.7.3`
  (secret rejected). Fixing/rotating the password does not help.
- **NOT Branch 3 (connection / port / TLS).** The socket connected and STARTTLS negotiated on 587; there
  is no `SocketException` or handshake error. The Port↔SecureConnection pairing (587 + StartTls) is
  correct.
- **NOT Branch 4/5 (relay / recipient).** Authentication never succeeded, so the server never evaluated
  the sender/recipient; there is no `5.7.1`/`5.7.60`/`5.1.1`.

**Evidence:**
- Job `a4b5c6d7-8293-4c04-9d5e-6f7081920415` (folder RPA Production, `MOCK-HOST`, `UIPATH\ROBOTUSER1`)
  `State = Faulted`; `Info`/Error: `SmtpException ... 535 5.7.139 ... [basic authentication is disabled]`.
- Logs: connected `smtp.office365.com:587` StartTls, STARTTLS negotiated, `AUTH LOGIN` for
  `svc-billing@contoso-test.com` rejected with `5.7.139`.
- Source: `SmtpSendMail` `Server="smtp.office365.com"`, `Port="587"`, `SecureConnection="StartTls"`,
  Basic-Auth `Email="svc-billing@contoso-test.com"`.

**Immediate fix:**
1. **Preferred — stop using Basic-Auth SMTP.** Move the send to **OAuth2** SMTP, or replace the activity
   with the Graph **o365-activities** (`UiPath.MicrosoftOffice365.Activities`, app registration + OAuth),
   which Microsoft supports going forward. This is the durable fix; Basic-Auth SMTP is deprecated.
2. **Or enable SMTP AUTH for this mailbox** (if policy allows): `Set-CASMailbox
   svc-billing@contoso-test.com -SmtpClientAuthenticationDisabled $false`, and confirm the tenant-wide
   SMTP AUTH switch permits it (Microsoft 365 admin center → Roles / Org settings). Then re-run.

**Do NOT** rotate or "fix" the password, and do NOT weaken `SecureConnection` — the credentials and
transport are fine; the mechanism is disabled. Do NOT swap to `Send Outlook Mail Message` (that adds a
desktop-Outlook COM dependency).

**Preventive fix:**
- For Microsoft 365 / Gmail, use OAuth2 SMTP or the Graph o365-activities for new unattended workflows;
  do not build on Basic-Auth SMTP, which is being retired.
- Track mailbox auth-policy changes — a tenant flipping SMTP AUTH off will break every Basic-Auth SMTP
  job at once.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | M365 disabled Basic Auth / SMTP AUTH for the account; the correct credentials are refused with 535 5.7.139. | High | Confirmed | Yes | `535 5.7.139 ... basic authentication is disabled`; STARTTLS on 587 succeeded, only AUTH LOGIN refused. | Move to OAuth2 SMTP / Graph o365, or enable SMTP AUTH on the mailbox. |
| H2 | Wrong/expired password (Branch 1). | Low | Eliminated | No | Server code is `5.7.139` (mechanism), not `5.7.3` (secret). | N/A |
| H3 | Connection / port / TLS mismatch (Branch 3). | Low | Eliminated | No | Socket connected, STARTTLS negotiated on 587; no `SocketException`/handshake error. | N/A |
