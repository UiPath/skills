---
confidence: medium
---

# Send SMTP Mail Message Failures

## Context

A `UiPath.Mail.SMTP.Activities` `Send SMTP Mail Message` (`SmtpSendMail`) activity talks to a mail
server **directly over SMTP** — it does NOT drive a desktop Outlook client (that is
`send-outlook-mail-failures.md`) and does NOT call Microsoft Graph (that is the o365-activities
surface). It opens a socket to `Server:Port`, negotiates transport security (`SecureConnection` —
`None` / `StartTls` / `SSL` / `Auto`), authenticates with `Email` + password (Basic Auth) unless
configured otherwise, then hands the message to the server. Because it is protocol-level, its failures
come from the **server's SMTP response codes** and the **socket/TLS layer** — surfaced as
`System.Net.Mail.SmtpException` (often wrapping a `SocketException` or an `SmtpStatusCode`), not a COM
error.

The activity is the recommended path for **unattended** mail (no Outlook install / profile needed), so
these failures are common on server-side robots.

What it looks like — read the exception + the numeric SMTP status code first; it maps directly to a
branch:

- `SmtpException` / `The SMTP server requires a secure connection or the client was not authenticated.
  The server response was: 5.7.57 ...` or `535 5.7.3 Authentication unsuccessful` — **branch 1**.
- `535 5.7.139 Authentication unsuccessful, basic authentication is disabled` (Microsoft 365), or
  `534 5.7.9 Application-specific password required` (Gmail) — **branch 2** (auth mechanism disabled /
  app-password or OAuth required).
- `SmtpException: Failure sending mail` wrapping a `SocketException` (connection refused / timed out),
  or a TLS/handshake error / hang — **branch 3** (wrong `Port`/`SecureConnection` pairing, server
  unreachable, firewall).
- `550 5.7.1 Unable to relay` / `5.7.60 Client does not have permissions to send as this sender` /
  `553 sender address rejected` — **branch 4** (relay / sender not permitted).
- `550 mailbox unavailable` / `5.1.1 recipient rejected`, or `552 message size exceeds`, or an
  attachment `FileNotFoundException` before send — **branch 5** (recipient / attachment / size).
- `System.ArgumentException` / `System.NullReferenceException` at the activity with no server round-trip
  — **branch 6** (a required input `Server` / `From` / `To` is empty or null).

What can cause it (cause-branches — pick the right one from the exception + status code):

1. **Authentication failure (bad credentials).** The `Email` / password (or the credential asset they
   resolve from) is wrong, expired, or points at the wrong account. Server rejects with `535` /
   `5.7.3`. Distinct from branch 2 — here the mechanism is allowed but the secret is wrong.
2. **Auth mechanism disabled — Basic Auth / SMTP AUTH off (app-password or OAuth required).** The
   credentials are correct, but the server no longer accepts Basic Auth over SMTP. **Microsoft 365**
   disables SMTP AUTH per-mailbox / tenant-wide by default (`535 5.7.139 ... basic authentication is
   disabled`); **Gmail** requires an **app password** (or OAuth) when 2-Step Verification is on
   (`534 5.7.9`). The fix is not "fix the password" — it is enable SMTP AUTH on the mailbox, use an app
   password, or move to OAuth2 / the Graph o365-activities.
3. **Connection / port / transport-security mismatch.** `Server` unreachable (DNS, firewall, server
   down) → `SocketException`; or the `Port` and `SecureConnection` are mispaired: **587 = StartTls**,
   **465 = implicit SSL**, **25 = None/relay**. Using 465 with StartTls (or 587 with SSL) makes the TLS
   negotiation fail or hang. Symptom: `Failure sending mail` wrapping a socket/handshake error, or a
   timeout.
4. **Relay denied / sender not permitted.** Authentication succeeds, but the server refuses the message:
   the `From` address is not one the authenticated account may send as (`5.7.60` send-as), the
   recipient is external and the account/connector is not allowed to relay to it (`550 5.7.1 Unable to
   relay`), or an SPF/allowed-sender policy blocks the From domain.
5. **Recipient rejected / attachment / size.** A `To`/`Cc`/`Bcc` address is malformed or does not exist
   (`550 5.1.1`), an attachment path in `Attachments` does not resolve on the robot host
   (`FileNotFoundException` thrown before the send), or the message exceeds the server's size limit
   (`552`).
6. **Uninitialized / missing required input.** `Server`, `From`, or `To` is bound to a variable that is
   empty/null at runtime (an upstream step was skipped or an asset returned empty). The activity throws
   `ArgumentException` / `NullReferenceException` with no server round-trip.

What to look for:

- **The `SmtpException` message and the numeric SMTP status code** — the primary discriminator
  (`535`/`5.7.3` → 1; `5.7.139`/`5.7.9` → 2; `SocketException`/handshake → 3; `5.7.1`/`5.7.60` → 4;
  `5.1.1`/`552` → 5). A bare `Failure sending mail` always wraps an inner exception — read it.
- **`Server`, `Port`, `SecureConnection` on the activity** — from workflow source. The Port↔security
  pairing is load-bearing for branch 3. `smtp.office365.com` / `smtp.gmail.com` with Basic Auth points
  at branch 2.
- **How credentials are supplied** — literal, `Email`+password, or an Orchestrator credential asset.
  Branch 1 vs 2 hinges on whether the mechanism is allowed, not just the secret.
- **The `From` vs the authenticated `Email`** — a mismatch is branch 4 (send-as / relay).
- **`Attachments` paths and `To`/`From`/`Server` values** — literal vs expression; empty/null points at
  branch 6, bad attachment path at branch 5.

## Investigation

1. **Capture the exact error, status code, activity, and config.** From `uip or jobs get <job-key>
   --output json` → `Info` (and `uip or jobs logs <key> --level Error --output json`): the
   `SmtpException` message **and the numeric SMTP status code**, plus any inner `SocketException`. From
   workflow source (`.xaml`): the `Send SMTP Mail Message` node — `Server`, `Port`, `SecureConnection`,
   `From`, `To`, `Attachments`, and how `Email`/password resolve.
2. **Branch on the status code / exception:**
   - `535` / `5.7.3` (mechanism allowed, secret rejected) → branch 1.
   - `5.7.139` (M365 basic auth disabled) / `5.7.9` (Gmail app password) → branch 2.
   - `SocketException` / connection refused / timeout / TLS handshake → branch 3; cross-check the
     `Port` ↔ `SecureConnection` pairing.
   - `5.7.1` / `5.7.60` / `553` → branch 4; compare `From` against the authenticated account.
   - `5.1.1` / `552` / attachment `FileNotFoundException` → branch 5.
   - `ArgumentException` / `NullReferenceException`, no server response → branch 6; trace the empty
     input's producer.
3. **Confirm the branch with the config.** For branch 2, note the host (`smtp.office365.com` /
   `smtp.gmail.com`) and that credentials are Basic Auth — the `5.7.139` / `5.7.9` code is decisive. For
   branch 3, confirm the Port↔security mismatch (587/StartTls, 465/SSL, 25/None). For branch 4, confirm
   `From` ≠ authenticated `Email`.

The root cause is **which SMTP-layer condition the server (or socket) reported** — a rejected secret vs
a disabled mechanism vs a transport mispairing vs a relay/sender policy — not "email failed"
generically. A confirmed finding names the status code, the relevant config value, and the branch.

## Resolution

- **Branch 1 — Bad credentials:** correct the `Email`/password (or fix the Orchestrator credential asset
  they resolve from); confirm the account is not locked/expired. Re-run.
- **Branch 2 — Auth mechanism disabled (Basic Auth / SMTP AUTH off):**
  - **Microsoft 365:** either enable SMTP AUTH on the specific mailbox (`Set-CASMailbox -SmtpClientAuthenticationDisabled $false`, and ensure the tenant-wide switch permits it) — or, preferred, stop using Basic-Auth SMTP and move to **OAuth2** or the Graph **o365-activities** (`UiPath.MicrosoftOffice365.Activities`), which Microsoft supports going forward.
  - **Gmail / Google Workspace:** generate an **app password** (requires 2-Step Verification) and use it in place of the account password, or switch to OAuth2.
  - Do NOT keep retrying the real password — the mechanism, not the secret, is being refused.
- **Branch 3 — Connection / port / transport mismatch:** pair `Port` with `SecureConnection` correctly —
  **587 + StartTls**, **465 + SSL**, **25 + None** (relay). Verify the robot host can reach the server
  (`Test-NetConnection <server> -Port <port>`); open the firewall / allowlist the SMTP egress if not.
  For transient issues add a Retry Scope around the send.
- **Branch 4 — Relay / sender not permitted:** set `From` to an address the authenticated account is
  allowed to send as (or grant Send-As), or route through a relay/connector permitted to send to the
  external recipient. For M365, use an authenticated submission (the mailbox's own address) rather than
  an unauthenticated relay, or configure a Direct Send / SMTP relay connector.
- **Branch 5 — Recipient / attachment / size:** fix the malformed/nonexistent recipient address; confirm
  every `Attachments` path resolves on the **robot host** at runtime (not the dev machine); split or
  compress messages that exceed the server size limit.
- **Branch 6 — Uninitialized input:** trace the empty `Server`/`From`/`To` variable to its producer
  (skipped step, empty asset, bad concatenation) and populate it; add a guard that fails fast with a
  clear message when a required field is empty, rather than letting the framework exception surface.

> Approval gate (SKILL.md §1.10): fixes that edit the user's workflow (Port/SecureConnection/From) or
> change credentials/mailbox settings are changes to their system — present the concrete change and get
> approval before editing.

## Anti-patterns (what NOT to do)

- **Do NOT "fix the password" for a `5.7.139` / `5.7.9` error.** The credentials are fine — the server
  disabled the auth *mechanism*. Chasing the password wastes time; enable SMTP AUTH / use an app
  password / move to OAuth2.
- **Do NOT blindly flip `SecureConnection` to `None`** to get past a TLS handshake error. That sends
  credentials and mail in clear text (and most servers reject it anyway). Fix the Port↔security pairing
  instead.
- **Do NOT swap to `Send Outlook Mail Message` to "avoid the SMTP problem."** That introduces the
  desktop-Outlook COM dependency (profile, Object Model Guard, Work Offline — see
  `send-outlook-mail-failures.md`) and is the wrong direction for a server-side robot. The right
  modernization is OAuth2 SMTP or the Graph o365-activities.

## Prevention (cross-branch)

- Store SMTP credentials in an Orchestrator credential asset, not literals; rotate before expiry.
- Pin the correct Port↔`SecureConnection` pairing per server and document it (587/StartTls for most
  submission endpoints).
- For Microsoft 365 / Gmail, plan for Basic-Auth deprecation up front: use OAuth2 SMTP or the Graph
  o365-activities for new unattended workflows rather than Basic-Auth SMTP.
- Validate `Server`/`From`/`To` and every attachment path at job start; fail fast with a clear message.

## Related

- Desktop Outlook COM send failures (profile, security prompt, Work Offline) →
  [send-outlook-mail-failures.md](./send-outlook-mail-failures.md).
- Modern Graph-based mail (no SMTP, no desktop client; OAuth) → the o365-activities surface
  ([o365-activities/overview.md](../../o365-activities/overview.md)).
