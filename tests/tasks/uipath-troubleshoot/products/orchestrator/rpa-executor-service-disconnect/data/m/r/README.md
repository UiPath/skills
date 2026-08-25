# Scenario: rpa-executor-service-disconnect

Synthetic Orchestrator control-plane scenario. Job `d4a40001-4444-4444-8444-444444444444`
(`NightlyPost`, folder Batch Ops) ran ~68s on BATCH-BOT-02 then faulted with
`Job faulted due to service shutdown or disconnect.` Maps to
`products/orchestrator/playbooks/executor-start-transient-rerun.md` (rerun-class).

The discriminating evidence: the message names a **service shutdown/disconnect**
(not a logon code, session-timeout, slot/console, or quota), history is
Pending → Running → Faulted, and `jobs list` shows the **previous nights'
NightlyPost runs on the same host succeeded** — an intermittent transient. The
fix is to **rerun** (escalating to host/robot stability + Robot update only if
it recurs) — NOT a credential, slot, license, or code change.

Control-plane failure, so there is no `process/` source; the agent diagnoses
from `uip or jobs`/`machines` evidence. Grading: `skill_triggered` +
`llm_judge` vs `RESOLUTION.md`.
