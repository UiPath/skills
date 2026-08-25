---
confidence: medium
---

# Serverless Run Cancelled — 15-Minute Execution Time Limit

## Context

A **serverless** (Automation Cloud Robot – Serverless, `RuntimeType` Serverless / `runtimetype = 9`) job **starts, runs, and is then terminated mid-execution** on reaching the serverless per-job time limit. Per UiPath docs, **each serverless job is limited to 15 minutes; jobs that take longer are terminated when they reach 15 minutes of execution time.** This is an **execution ceiling**, not a start-time block.

> **Distinct from [serverless-license-quota.md](./serverless-license-quota.md).** That playbook is for a serverless job that **never starts** (rejected at allocation time with a Robot-Units / Personal-Automation-quota message, near-zero runtime). This one is for a job that **ran ~15 minutes and was cut off** at the ceiling. Run duration is the discriminator.

What this looks like:
- `RuntimeType` Serverless / `runtimetype = 9`, and the job reached **Running** (it was not rejected at start).
- Run duration ≈ **15 minutes** (`EndTime − StartTime`), then the job stops (Faulted / Stopped / Cancelled).
- The status/`Info` indicates the run was cancelled on reaching the time limit (wording such as "reached the time limit" / "cancelled" — the exact user-facing string is not documented and may vary by surface, so key off the ~15-minute duration, not a verbatim message).
- No quota / Robot-Units message, no `Could not start executor`, and no in-workflow exception that explains the stop on its own.

What causes it:
- The workflow legitimately needs **more than 15 minutes** on a serverless robot — long loops, large data volumes, slow external systems, or waits — and hits the hard serverless ceiling.

## Investigation

1. **Get the job:** `uip or jobs get <job-key> --output json` → confirm `RuntimeType` Serverless / `runtimetype = 9`, that the job reached **Running**, and compute `EndTime − StartTime` ≈ 15 min.
2. **Rule out the license/quota case:** confirm there is **no** `Automation cannot be started … Robot Units` / `Personal Automation quota` message and that runtime is ~15 min (not near-zero). A job that never ran → [serverless-license-quota.md](./serverless-license-quota.md) instead.
3. **Rule out an in-workflow fault:** `uip or jobs logs <job-key> --level Error --output json` — if the stop is explained by a workflow exception rather than the time ceiling, diagnose that exception instead.

## Resolution

- **Bring the run under 15 minutes** — optimize the workflow (batch or cap the data processed per run, remove avoidable waits, parallelize independent work), or **split it into multiple shorter jobs** chained via a trigger/orchestration so each run stays under the serverless ceiling.
- **Move long-running workloads off serverless** — run them on an **unattended (VM / machine-template) robot**, which is not subject to the 15-minute serverless per-job limit.
- Rerunning as-is does **not** help — a workflow that needs more than 15 minutes hits the ceiling every time until it is shortened or moved.

Source: UiPath docs — *Executing unattended automations with Serverless robots* ("Each job is limited to 15 minutes. Jobs that take longer are terminated when they reach 15 minutes of execution time.").
