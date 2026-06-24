# Final Resolution

---

**Root Cause:** The `FetchInboxMessages` process faults in its **Get IMAP Mail
Messages** activity (`UiPath.Mail.IMAP.Activities.GetIMAPMailMessages`, package
`UiPath.Mail.Activities`) with a **raw `System.TimeoutException: The operation
has timed out.`** thrown by the activity's own `TimeoutMS` guard
(`UiPath.Mail.Activities.Extensions.TaskExtensions.TimeoutAfter` →
`GetMailActivity.ExecuteAsync`). The connect never completes within the
configured timeout, so the guard fires.

The controllable cause is a **`SecureConnection` / `Port` mismatch** in the
activity configuration: `Server=imap.gmail.com`, **`Port=143`**, but
**`SecureConnection=SslOnConnect`** with **`TimeoutMS=15000`**. `SslOnConnect`
forces an immediate TLS handshake on connect, but port `143` is the **plaintext
IMAP** port (it expects a cleartext greeting, or STARTTLS upgrade) — so the
handshake never gets a TLS response and **hangs until the 15-second `TimeoutMS`
elapses**, surfacing as the timeout rather than a fast `SslHandshakeException`.

This maps to the **Get IMAP Mail Messages failures** playbook,
**branch 2 (timeout)** —
`references/activity-packages/mail-activities/playbooks/get-imap-mail-messages-failures.md`.

> The `TimeoutException` is raised **raw** by the activity's `TimeoutMS` guard —
> it is NOT wrapped in the `Cannot connect to the (IMAP) Mail Service…`
> `MailException` that the MailKit TLS/auth/protocol faults carry.

**What went wrong:** The `FetchInboxMessages` job (started
2026-06-24T08:24:28Z) dispatched and ran cleanly (`Pending → Running →
Faulted`), then faulted ~23.5 seconds later when `Get IMAP Mail Messages`
exceeded its 15-second `TimeoutMS` waiting on a TLS handshake that the plaintext
port could not satisfy.

**Why:** A file-/network-level connection to `imap.gmail.com:143` with
`SslOnConnect` attempts TLS immediately against a port that speaks plaintext
IMAP. With no TLS peer, the handshake stalls; the activity's `TimeoutMS` guard
trips and throws `System.TimeoutException` directly. The robot, license, and
host were all fine — the failure is entirely inside the mail activity's connect.

This is **NOT** an authentication failure (the connect never reached the auth
step — there is no `AuthenticationException` / "Authentication failed"), **NOT**
a folder problem (`Mail Folder does not exist…` did not occur), **NOT** an
infrastructure / licensing / dispatch problem (the job reached `Running` and
executed), and **NOT** a generic "mail server is down" with no controllable fix
— the `SecureConnection`/`Port` pairing in the workflow is the lever.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `FetchInboxMessages` — Faulted at 2026-06-24T08:24:52Z (ran ~23.5 s — a timeout window elapsing, not an instant crash)
- Folder: Shared (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`)
- Host: `MOCK-HOST`; identity `newrobot` (Unattended)
- `or jobs get` `Info`: `System.TimeoutException: The operation has timed out.` at `GetIMAPMailMessages "GetIMAPMailMessages"`, frames into `TaskExtensions.TimeoutAfter` → `GetMailActivity.ExecuteAsync`
- `or jobs logs --level Error`: same `System.TimeoutException` pinned to the `GetIMAPMailMessages` step
- `or jobs history`: `Pending → Running → Faulted` (clean dispatch; failure is in execution)

### Mail Activities (Surface / Root Cause)
- Activity (from `Main.xaml`): `GetIMAPMailMessages` (`UiPath.Mail.IMAP.Activities`)
- Config (from `Main.xaml`): `Server="imap.gmail.com"`, `Port="143"`,
  `SecureConnection="SslOnConnect"`, `TimeoutMS="15000"`, `MailFolder="Inbox"`
- The `SslOnConnect` + `143` pairing forces a TLS handshake on the plaintext
  IMAP port → handshake hangs → `TimeoutMS` guard throws raw
  `System.TimeoutException`.

---

**Immediate fix (align `SecureConnection` with the port):**

1. **Use the matching SSL/port pairing for IMAP.**
   - For implicit TLS: `Port=993` with `SecureConnection=SslOnConnect` (or `Auto`).
   - For STARTTLS on the plaintext port: `Port=143` with `SecureConnection=StartTls`.
   - **Where:** the `Get IMAP Mail Messages` activity in `Main.xaml`.
   - **Who:** RPA developer.
2. **Verify reachability from the Robot host.** Confirm `MOCK-HOST` can reach
   the chosen `Server:Port` (firewall/proxy) so the handshake can complete.
3. **Only raise `TimeoutMS` if the server is legitimately slow** — it does not
   fix a `SecureConnection`/port mismatch; a larger value just makes the job
   hang longer before the same timeout.

**Do NOT** treat this as an auth/credential problem, a missing folder, or an
infrastructure outage — none of those occurred; the connect timed out on a
TLS/port mismatch.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Get IMAP Mail Messages` connect times out because `SecureConnection=SslOnConnect` is set against plaintext IMAP port `143`, so the TLS handshake hangs until `TimeoutMS` (15 s) elapses | High | Confirmed | Yes | Raw `System.TimeoutException` at `TaskExtensions.TimeoutAfter`/`GetMailActivity` (`or jobs get`/`logs`) + `Port=143`/`SecureConnection=SslOnConnect` in `Main.xaml` | Align port/SSL pairing (993+SslOnConnect or 143+StartTls); verify host reachability |
| H2 | Authentication failure (bad creds / app-password) | Low | Rejected | No | No `AuthenticationException` / "Authentication failed"; the connect never reached auth | n/a |
| H3 | Mail folder not found | Low | Rejected | No | No `Mail Folder does not exist for specified client.`; `MailFolder=Inbox` | n/a |
| H4 | Infrastructure / licensing / dispatch failure | Low | Rejected | No | Job reached `Running` and executed; `ErrorCode=Robot`, fault inside the activity | n/a |

---

Would you like help applying the fix — the exact `Port`/`SecureConnection`
change on the `Get IMAP Mail Messages` activity? I can also clean up the
`.local/investigations/` folder if you no longer need it.
