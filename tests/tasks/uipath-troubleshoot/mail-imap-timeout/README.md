# Mail IMAP Get — Connect Timeout from SecureConnection/Port Mismatch

Replays staging job `80b4bf8e-9437-4ef9-884c-41d1d2cd429c` (`FetchInboxMessages`,
folder Shared). Fault: `System.TimeoutException: The operation has timed out.`
raised raw by the **Get IMAP Mail Messages** activity
(`UiPath.Mail.IMAP.Activities.GetIMAPMailMessages`) from its `TimeoutMS` guard.
Maps to `mail-activities/playbooks/get-imap-mail-messages-failures.md` — **branch
2 (timeout)**.

## What this scenario uncovers

**Root Cause:** The `Get IMAP Mail Messages` activity is configured with
`Server=imap.gmail.com`, **`Port=143`**, **`SecureConnection=SslOnConnect`**,
`TimeoutMS=15000`. `SslOnConnect` forces an immediate TLS handshake, but port
`143` is the **plaintext** IMAP port — the handshake never gets a TLS peer and
hangs until the 15-second `TimeoutMS` elapses, surfacing as a raw
`System.TimeoutException` from the activity's guard (NOT wrapped in the
`Cannot connect to the (IMAP) Mail Service…` MailException). The fix is to align
the SSL/port pairing: `993` + `SslOnConnect`/`Auto`, or `143` + `StartTls`.

This is **not** an auth failure (the connect never reached auth), **not** a
missing folder, and **not** an infrastructure/licensing/dispatch problem (the
job reached `Running` and executed).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | snapshot of the failing `MailRepro` project — `Get IMAP Mail Messages` with `Port=143` + `SecureConnection=SslOnConnect`, project type Windows |
| `fixtures/mocks/responses/*.json` | **real** `uip` captures from `.local/investigations/raw`, scrubbed |
| `fixtures/mocks/responses/manifest.json` | dispatch table (first-match) |

The decisive evidence:

1. `or jobs get` / `or jobs logs --level Error` → `System.TimeoutException: The
   operation has timed out.` pinned to `GetIMAPMailMessages`, frames into
   `UiPath.Mail.Activities.Extensions.TaskExtensions.TimeoutAfter` →
   `GetMailActivity.ExecuteAsync`.
2. `or jobs history` → `Pending → Running → Faulted` (clean dispatch; the fault
   is in execution, ~23.5 s in — a timeout window, not an instant crash).
3. `process/Main.xaml` → `Port=143` + `SecureConnection=SslOnConnect` — the
   controllable mismatch.

## Provenance / scrub

Captured from a real staging fault. Scrubbed: host → `MOCK-HOST`, account →
`UIPATH\REPLACEMENT_USER`, personal-workspace email → `original_email@test.com`.
Error texts, job key (`80b4bf8e-…`), and folder key (`defb8e05-…`) kept verbatim.

## Success criteria

Scores the conclusion, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `get-imap-mail-messages-failures` **branch 2 (timeout)** and
  reached the same root cause as `RESOLUTION.md`: the `SecureConnection`/`Port`
  mismatch (`SslOnConnect` on plaintext `143`) makes the handshake hang to the
  `TimeoutMS` guard.
- Conclusion recommends aligning the SSL/port pairing (`993`+`SslOnConnect` or
  `143`+`StartTls`) and must NOT land on an auth/credential failure, a missing
  folder, or an infrastructure/licensing/dispatch failure.
