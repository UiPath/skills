# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **The `Send SMTP Mail Message` activity pairs `Port=465` with
`SecureConnection=StartTls`, but port 465 expects *implicit* SSL/TLS from the first byte — so the
STARTTLS negotiation fails and the server forcibly closes the socket.** The fault surfaces as
`System.Net.Mail.SmtpException: Failure sending mail` wrapping an `IOException` → `SocketException` ("An
existing connection was forcibly closed by the remote host"). This is the connection / port-vs-transport
mismatch of `send-smtp-mail-failures.md` **Branch 3** — NOT an authentication failure and NOT a
relay/recipient problem.

Correct pairings: **587 = StartTls**, **465 = SSL (implicit)**, **25 = None**. The workflow mixed the
465 port with the 587-style StartTls setting.

**What went wrong:** The `WeeklyReportDispatcher` job hung ~35 s then faulted. Job logs show `Opening
connection to smtp.office365.com:465 (SecureConnection=StartTls)` → `TCP connected; sending EHLO then
STARTTLS command on port 465` → `No SMTP greeting/response to STARTTLS on port 465; the server appears to
expect implicit TLS on this port` → `Transport connection dropped during TLS negotiation`. The socket
connected, but sending a plaintext STARTTLS handshake to an implicit-TLS port made the server drop the
connection.

**Why — and why it is NOT another branch:**
- **NOT Branch 1/2 (authentication).** No `535`/`5.7.x` auth code — the failure is at the transport/TLS
  layer, before any AUTH exchange completed. The error is a `SocketException`, not an auth rejection.
- **NOT Branch 4/5 (relay / recipient).** No `550`/`5.7.1`/`5.1.1` — the server never accepted the
  session far enough to evaluate sender or recipient.
- **NOT a server outage.** The TCP connect succeeded (`TCP connected`); only the TLS negotiation failed,
  which points at the port/security pairing, not reachability.

**Evidence:**
- Job `b6c7d8e9-0415-4d26-8f70-8192a3b4c5d6` (folder RPA Production, `MOCK-HOST`, `UIPATH\ROBOTUSER1`)
  `State = Faulted`; `Info`/Error: `SmtpException: Failure sending mail ---> IOException ---> SocketException:
  An existing connection was forcibly closed`.
- Logs: connect `smtp.office365.com:465` StartTls → STARTTLS on 465 gets no proper response → connection
  dropped during TLS negotiation.
- Source: `SmtpSendMail` `Server="smtp.office365.com"`, `Port="465"`, `SecureConnection="StartTls"` — the
  mispaired combination.

**Immediate fix:**
1. Pair the port with the right transport security. For `smtp.office365.com`, use **`Port=587` with
   `SecureConnection=StartTls`** (the standard submission endpoint), OR **`Port=465` with
   `SecureConnection=SSL`** (implicit TLS). Do NOT keep `465` + `StartTls`.
2. Re-run — with a matched pairing the TLS handshake completes and the send proceeds.
3. Verify the robot host can reach the endpoint (`Test-NetConnection smtp.office365.com -Port 587`) if it
   still fails after the pairing fix.

**Do NOT** set `SecureConnection=None` to "get past" the handshake (that sends credentials/mail in clear
text and the server will reject it). Do NOT chase credentials — no auth error occurred.

**Preventive fix:**
- Standardize the Port↔`SecureConnection` pairing per server and document it (587/StartTls for most
  submission endpoints); review it whenever the SMTP host or port changes.
- Add a Retry Scope for genuinely transient transport blips, but only after the pairing is correct.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Port 465 paired with StartTls; 465 is implicit SSL, so STARTTLS fails and the server drops the socket. | High | Confirmed | Yes | `Port="465"` + `SecureConnection="StartTls"` in source; logs STARTTLS-on-465 no response → connection dropped; `SmtpException ... SocketException forcibly closed`. | Use 587+StartTls or 465+SSL. |
| H2 | Authentication failure (Branch 1/2). | Low | Eliminated | No | No `535`/`5.7.x`; failure is at TLS/transport before AUTH. | N/A |
| H3 | Server unreachable / outage. | Low | Eliminated | No | TCP connected; only TLS negotiation failed — points at the pairing, not reachability. | N/A |
