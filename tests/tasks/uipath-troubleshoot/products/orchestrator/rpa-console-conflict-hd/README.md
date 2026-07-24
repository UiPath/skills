# Scenario: rpa-console-conflict-hd

Synthetic Orchestrator control-plane scenario. Job `b2820001-2222-4222-8222-222222222222`
(`ClaimsIntake`, folder HD Automations) faults at executor start with
`Another interactive job is using the machine's console. Only one interactive job can use the console at a time.`
Maps to `products/orchestrator/playbooks/console-conflict-login-to-console.md`.

The discriminating evidence: `machines list --all-fields` shows HD-BOT-POOL is a
high-density host (5 unattended slots, 4 robot users), and `jobs list` shows a
concurrent ClaimsIntake job Running on the same host. On an HD host, the console
message means the robots use **Login to Console = True** — all jobs attach to
the single physical console session, so only one interactive job runs at a time.
The fix is to disable Login to Console for the HD robots so each job gets its own
session — NOT a credential fix, a slot change, or a rerun.

Control-plane failure (pre-workflow), so there is no `process/` source; the
agent diagnoses from `uip or jobs`/`machines` evidence. Grading:
`skill_triggered` + `llm_judge` vs `RESOLUTION.md`.
