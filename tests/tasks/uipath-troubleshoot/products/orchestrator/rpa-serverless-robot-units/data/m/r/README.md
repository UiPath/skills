# Scenario: rpa-serverless-robot-units

Synthetic Orchestrator control-plane scenario. Serverless job `c3930001-3333-4333-8333-333333333333`
(`InvoiceParse`, folder Cloud Robots) goes straight to Faulted with
`Automation cannot be started. Your tenant's assigned Robot Units have been exceeded.`
Maps to `products/orchestrator/playbooks/serverless-license-quota.md`.

The discriminating evidence: `jobs get` shows `RuntimeType` Serverless, history
is Pending → Faulted (never Running), and the message names a **tenant-scope
Robot Units** limit. `machines list` is empty (serverless jobs bind no listed
machine template — expected, not a no-host fault). The fix is to allocate more
Robot Units to the tenant (or reduce serverless concurrency) — NOT an
executor/session, credential, robot-version, or rerun fix.

Control-plane failure (pre-workflow), so there is no `process/` source; the
agent diagnoses from `uip or jobs`/`machines` evidence. Grading:
`skill_triggered` + `llm_judge` vs `RESOLUTION.md`.
