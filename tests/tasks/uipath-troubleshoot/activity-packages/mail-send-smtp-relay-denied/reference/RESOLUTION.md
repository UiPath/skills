# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **The `Send SMTP Mail Message` activity authenticates as
`svc-billing@contoso-test.com` but sets `From = noreply@marketing-partner.com` — an address the
authenticated account is not permitted to send as — so the server rejects the message with `550 5.7.60
Client does not have permissions to send as this sender`.** This is the relay / sender-not-permitted
sub-case of `send-smtp-mail-failures.md` **Branch 4** — NOT an authentication failure (auth succeeded)
and NOT a connection/TLS problem.

Connection, TLS, and login all succeeded; the server refused the message at the envelope step because
the `MAIL FROM` sender does not match (or is not an allowed send-as alias of) the authenticated mailbox.

**What went wrong:** The `CustomerAlertSender` job faulted ~4 s after launch. Job logs show `Connecting
to smtp.office365.com:587 (StartTls)` → `STARTTLS negotiated; authenticated as
svc-billing@contoso-test.com` → `MAIL FROM:<noreply@marketing-partner.com>; RCPT
TO:<customer-updates@contoso-test.com>` → `Server rejected the message: 550 5.7.60 ... does not have
permissions to send as this sender (authenticated as svc-billing@contoso-test.com, From
noreply@marketing-partner.com)`. The `From` domain (`marketing-partner.com`) is not owned by the
authenticated Contoso account.

**Why — and why it is NOT another branch:**
- **NOT Branch 1/2 (authentication).** The logs show `authenticated as svc-billing@contoso-test.com`
  succeeded; there is no `535`/`5.7.3`/`5.7.139`. The failure is `550 5.7.60`, a send-as/relay policy
  rejection AFTER a successful login.
- **NOT Branch 3 (connection / TLS).** STARTTLS negotiated on 587 and the session reached the envelope
  commands; no `SocketException`/handshake error.
- **NOT Branch 5 (recipient / attachment).** The rejection code is `5.7.60` (sender permissions), not
  `5.1.1` (bad recipient) or `552` (size); the recipient was accepted.

**Evidence:**
- Job `c7d8e9f0-1526-4f37-8081-92a3b4c5d6e8` (folder RPA Production, `MOCK-HOST`, `UIPATH\ROBOTUSER1`)
  `State = Faulted`; `Info`/Error: `SmtpException: Mailbox unavailable. The server response was: 550
  5.7.60 ... Client does not have permissions to send as this sender.`
- Logs: authenticated as `svc-billing@contoso-test.com`, then `MAIL FROM:<noreply@marketing-partner.com>`
  rejected with `5.7.60`.
- Source: `SmtpSendMail` `Email="svc-billing@contoso-test.com"` (auth) but
  `From="noreply@marketing-partner.com"` — a mismatch the account may not send as.

**Immediate fix:**
1. Set `From` to an address the authenticated account is allowed to send as — the simplest is the
   account's own address (`From = "svc-billing@contoso-test.com"`), or a shared mailbox / alias that
   `svc-billing` has **Send As** / **Send on Behalf** rights to (grant those rights in Exchange if the
   `noreply@...` identity is required).
2. If mail genuinely must originate from `noreply@marketing-partner.com` (a different org/domain), route
   it through a mail server/connector that is authorized to relay for that domain, or authenticate as a
   mailbox in that domain — do not spoof it from the Contoso account.
3. Re-run once `From` matches the authenticated sender's permitted identities.

**Do NOT** treat this as an auth or connectivity issue (login and TLS succeeded), and do NOT weaken
transport security. The envelope sender, not the credentials, is being refused.

**Preventive fix:**
- Keep `From` aligned with the authenticated `Email` (or an explicitly granted Send-As alias); review
  `From` whenever the sending account changes.
- For cross-domain "no-reply" sending, use an authorized relay/connector or a mailbox in that domain,
  configured with the proper send-as permissions.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Auth succeeds as svc-billing, but From (noreply@marketing-partner.com) is not a permitted send-as identity, so the server rejects with 550 5.7.60. | High | Confirmed | Yes | Logs: authenticated as svc-billing@contoso-test.com → `MAIL FROM:<noreply@marketing-partner.com>` rejected `550 5.7.60 send as this sender`; source `Email`≠`From`. | Set `From` to the authenticated account / a granted Send-As alias, or relay via an authorized connector. |
| H2 | Authentication failure (Branch 1/2). | Low | Eliminated | No | Login succeeded (`authenticated as ...`); no `535`/`5.7.x` auth code. | N/A |
| H3 | Connection / TLS (Branch 3) or bad recipient (Branch 5). | Low | Eliminated | No | STARTTLS negotiated, recipient accepted; rejection is `5.7.60` (sender), not socket/`5.1.1`/`552`. | N/A |
