# Send SMTP Mail Message — Port / Transport-Security Mismatch (Branch 3)

Runtime troubleshooting scenario for `UiPath.Mail.SMTP.Activities` `Send SMTP Mail Message`
(`SmtpSendMail`), covering the **connection / port-vs-`SecureConnection` mismatch** of
`send-smtp-mail-failures.md` **Branch 3**.

## What this scenario exercises

An unattended job hangs ~35 s then faults with `System.Net.Mail.SmtpException: Failure sending mail`
wrapping an `IOException` → `SocketException` ("An existing connection was forcibly closed"). The
activity pairs `Port=465` with `SecureConnection=StartTls`, but 465 expects **implicit** SSL — so the
STARTTLS negotiation fails and the server drops the socket. The agent must attribute the failure to the
Port↔`SecureConnection` mismatch (not auth, not relay, not a server outage) and prescribe the correct
pairing: **587 + StartTls** or **465 + SSL**.

## Discriminator

- The socket **connected** (`TCP connected`) and the failure is at the **TLS negotiation** — so it is
  not a server-unreachable outage.
- There is **no `535`/`5.7.x` auth code** and **no `550`/`5.7.1` relay code** — so it is not Branch 1/2
  (auth) or Branch 4/5 (relay/recipient). The error is a `SocketException` at transport setup.
- Source shows the decisive mispairing: `Port="465"` + `SecureConnection="StartTls"`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `SmtpSendMail` with `Server="smtp.office365.com"`, `Port="465"`, `SecureConnection="StartTls"` |
| `data/m/r/` | synthetic canned `uip` responses; the smoking gun is `job-logs.json` (connect 465 StartTls → STARTTLS gets no response on an implicit-TLS port → connection dropped → `SmtpException`/`SocketException`); `docsai ask` passthrough |

Diagnosis is not leaked in any agent-visible name (project `WeeklyReportDispatcher`, activity "Send SMTP
Mail Message"); the prompt states only the observed symptom (job hangs then faults with the pasted
`Failure sending mail` / socket error).

## Success criteria

`skill_triggered` + `llm_judge` against `RESOLUTION.md`:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the Port↔`SecureConnection` mismatch (465 + StartTls) as the cause and prescribed the
  correct pairing (587 + StartTls, or 465 + SSL) — not an auth, relay, or server-outage misdiagnosis,
  and not disabling `SecureConnection`.

Playbook: `references/activity-packages/mail-activities/playbooks/send-smtp-mail-failures.md` (Branch 3).
