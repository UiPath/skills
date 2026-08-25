# Send SMTP Mail Message — Basic Auth / SMTP AUTH Disabled (Branch 2)

Runtime troubleshooting scenario for `UiPath.Mail.SMTP.Activities` `Send SMTP Mail Message`
(`SmtpSendMail`), covering the **Basic-Auth / SMTP-AUTH-disabled** sub-case of
`send-smtp-mail-failures.md` **Branch 2**.

## What this scenario exercises

An unattended job faults with `System.Net.Mail.SmtpException ... 535 5.7.139 Authentication
unsuccessful ... [basic authentication is disabled]`. The activity connected to `smtp.office365.com:587`
and negotiated STARTTLS fine — Microsoft 365 refused the **Basic-Auth** login because SMTP AUTH is
disabled for the account. The agent must recognize the `5.7.139` code as a **disabled auth mechanism**
(not a wrong password, not a transport problem) and prescribe moving to OAuth2 / Graph o365 (preferred)
or enabling SMTP AUTH on the mailbox — NOT rotating the password.

## Discriminator vs the other auth/connection branches

- `5.7.139` (mechanism disabled) — **this scenario**; the fix is auth-policy / OAuth, not the secret.
- `535 5.7.3` (secret rejected) — Branch 1, a real credential problem.
- `SocketException` / TLS handshake — Branch 3, a Port↔`SecureConnection` mispairing. Here STARTTLS on
  587 succeeded, so it is not Branch 3.

The logs make the discriminator explicit: STARTTLS negotiated and `AUTH LOGIN` was attempted, then the
server returned `5.7.139 ... basic authentication is disabled` — transport OK, mechanism refused.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `SmtpSendMail` targeting `smtp.office365.com:587` StartTls with Basic-Auth `Email` |
| `data/m/r/` | synthetic canned `uip` responses; the smoking gun is `job-logs.json` (connect → STARTTLS → AUTH LOGIN → `535 5.7.139 basic authentication is disabled`); `docsai ask` passthrough |

Diagnosis is not leaked in any agent-visible name (project `AutomatedBillingNotifier`, activity "Send
SMTP Mail Message"); the prompt states only the observed symptom (job faults with the pasted `535`
error).

## Success criteria

`skill_triggered` + `llm_judge` against `RESOLUTION.md`:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the disabled Basic-Auth / SMTP-AUTH mechanism (`5.7.139`) as the cause and prescribed
  OAuth2 / Graph o365 or enabling SMTP AUTH — not a password rotation, transport change, or Outlook swap.

Playbook: `references/activity-packages/mail-activities/playbooks/send-smtp-mail-failures.md` (Branch 2).
