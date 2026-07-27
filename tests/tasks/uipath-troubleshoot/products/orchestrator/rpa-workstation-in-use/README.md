# Scenario: rpa-workstation-in-use

Synthetic Orchestrator control-plane scenario. Job `a1710001-1111-4111-8111-111111111111`
(`DailyExtract`, folder Unattended Ops) faults at executor start with
`Could not start executor. The workstation is in use by another user.` Maps to
`products/orchestrator/playbooks/workstation-in-use-machine-slots.md`.

The discriminating evidence is in `machines list --all-fields` + `jobs list`:
WS-CLIENT-07 is a Windows 11 client (single interactive session) whose template
grants `unattendedSlots: 3`, and a concurrent job (`HourlySync`) was Running on
the same host when `DailyExtract` was dispatched — so Windows had no second
session to seat it. Non-overlapping runs succeed. The fix is to align the slot
count with the host's capacity (reduce to 1, or use a multi-session host) — NOT
a credential fix, a rerun, or a licensing change.

Control-plane failure (pre-workflow), so there is no `process/` source; the
agent diagnoses from `uip or jobs`/`machines` evidence. Grading:
`skill_triggered` + `llm_judge` vs `RESOLUTION.md`.
