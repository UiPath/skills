# Send Outlook Mail Message Timeout — Work Offline (Branch 2)

Runtime troubleshooting scenario for `UiPath.Mail.Outlook.Activities` `Send Outlook Mail Message`
(`SendOutlookMail`), covering the **Work Offline** sub-cause of
`send-outlook-mail-failures.md` **Branch 2 ("Activity times out or hangs")**.

## What this scenario exercises

An unattended job faults with `System.TimeoutException` after `TimeoutMS` (30000 ms). Outlook launched
and the profile loaded, the message was composed and **placed in the Outbox**, but it was never
transmitted because Outlook is **offline (Work Offline)** — so the COM send blocks until the timeout.
The agent must match Branch 2 and attribute the hang specifically to **Work Offline / an offline
mailbox**, and hand a host-side check list (turn off `Send/Receive > Work Offline`, confirm the profile
connects Online, flush the Outbox; switch to SMTP/Graph for unattended). It must NOT diagnose the
security-prompt sibling, a COM-cast (Branch 1), or a null input (Branch 3), and must NOT merely raise
`TimeoutMS`.

## The discriminator vs the security-prompt sibling

Branch 2 has two sub-causes with the **same Orchestrator signature** (timeout at `TimeoutMS`, no COM
error, no null): a hidden Object Model Guard **security prompt** and **Work Offline**. This scenario is
distinguished from `mail-send-outlook-mail-timeout-security-prompt` by evidence that rules the prompt
out and rules Work Offline in:

- Job log: `item placed in the Outbox for sending` → `still in the Outbox and has not been transmitted;
  Outlook connectivity state reports Disconnected ... (no dialog or prompt was raised)`.
- User's attended re-run on the host: **no popup/dialog appeared**, and the email was left **unsent in
  the Outbox**.

A "hidden security prompt" answer should score lower here because the evidence explicitly shows no
prompt and a queued Outbox item — the offline fingerprint.

## Sibling-branch comparison (same playbook)

| Branch / sub-cause | Signature | This scenario? |
|---|---|---|
| Branch 1 — COM cast / library not registered | `InvalidCastException` / `COMException` `REGDB_E_CLASSNOTREG` | No — Outlook launched + profile loaded; clean timeout |
| Branch 2 — **security prompt** (Object Model Guard) | timeout / hang; a modal awaiting input | No — sibling scenario; here no prompt was raised |
| **Branch 2 — Work Offline** | **timeout / hang; item queued in the Outbox, Outlook offline, no prompt** | **Yes** |
| Branch 3 — Uninitialized input | `NullReferenceException` at the activity | No — `To`/`Subject`/`Body` are literals |

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `SendOutlookMail` with literal `To`/`Subject`/`Body` and `TimeoutMS="30000"` on an unattended process |
| `data/m/r/` | synthetic canned `uip` responses; the smoking gun is in `job-logs.json` (item placed in Outbox → still in Outbox / Disconnected / no prompt → timeout at `TimeoutMS`); `docsai ask` passthrough |

The user is framed as **off-host** (Orchestrator only), so the correct behavior is to hand a host-side
check list and stop, not to run host commands. Diagnosis is not leaked in any agent-visible name
(project `NightlyStatementMailer`, activity "Send Outlook Mail Message"); the prompt states only
observed symptoms (timeout on every run; no popup in an attended test; email left in the Outbox).

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched Branch 2 and attributed the hang to **Work Offline / an offline mailbox** (item queued
  in the Outbox, no prompt) — not the security prompt, COM cast, or null input.
- Agent handed a host-side check list (turn off Work Offline, confirm the profile connects Online, flush
  the Outbox; SMTP/Graph for unattended) and did NOT recommend merely raising `TimeoutMS`.

Playbook: `references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
(Branch 2 — Work Offline sub-cause).
