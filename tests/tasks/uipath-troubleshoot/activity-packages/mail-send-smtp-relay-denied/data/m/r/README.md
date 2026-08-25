# Send SMTP Mail Message — Relay / Sender Not Permitted (Branch 4)

Runtime troubleshooting scenario for `UiPath.Mail.SMTP.Activities` `Send SMTP Mail Message`
(`SmtpSendMail`), covering the **relay / sender-not-permitted** sub-case of
`send-smtp-mail-failures.md` **Branch 4**.

## What this scenario exercises

An unattended job faults with `System.Net.Mail.SmtpException: Mailbox unavailable. The server response
was: 550 5.7.60 ... Client does not have permissions to send as this sender.` Connection, STARTTLS, and
authentication all succeed as `svc-billing@contoso-test.com`, but the activity's `From` is
`noreply@marketing-partner.com` — an address the authenticated account may not send as — so the server
rejects the message at the envelope step. The agent must attribute the failure to the send-as / relay
policy (authenticated identity ≠ `From`) and prescribe aligning `From` with the authenticated account /
a granted Send-As alias (or relaying via an authorized connector) — NOT an auth or transport fix.

## Discriminator

- Login **succeeded** (`authenticated as svc-billing@contoso-test.com`) — so it is not Branch 1/2
  (auth); there is no `535`/`5.7.3`/`5.7.139`.
- STARTTLS negotiated on 587 and the session reached `MAIL FROM`/`RCPT TO` — so it is not Branch 3
  (connection/TLS).
- The rejection code is `5.7.60` (sender permissions), not `5.1.1` (bad recipient) or `552` (size) — so
  it is not Branch 5.
- Source shows the decisive mismatch: `Email="svc-billing@contoso-test.com"` (auth) vs
  `From="noreply@marketing-partner.com"`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `SmtpSendMail` authenticating as `svc-billing@contoso-test.com` with `From="noreply@marketing-partner.com"` |
| `data/m/r/` | synthetic canned `uip` responses; the smoking gun is `job-logs.json` (auth OK → `MAIL FROM:<noreply@marketing-partner.com>` → `550 5.7.60 ... send as this sender`); `docsai ask` passthrough |

Diagnosis is not leaked in any agent-visible name (project `CustomerAlertSender`, activity "Send SMTP
Mail Message"); the prompt states only the observed symptom (job faults with the pasted `550 5.7.60`
error).

## Success criteria

`skill_triggered` + `llm_judge` against `RESOLUTION.md`:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the send-as / relay rejection (authenticated identity ≠ `From`) as the cause and
  prescribed aligning `From` with the authenticated account / a granted Send-As alias (or an authorized
  relay) — not an auth-credential, transport, or recipient misdiagnosis.

Playbook: `references/activity-packages/mail-activities/playbooks/send-smtp-mail-failures.md` (Branch 4).
