# Resolution — Healing Agent was NOT engaged; the log line is informational; zero consumption

## User's question

For the **last job in Orchestrator folder `Shared`**: did the Healing Agent (HA) actually run, did it consume any AI units / credits / AI Trust Layer, and what does the `healing-agent` log line mean?

## Verified answer

The most-recent job in folder `Shared` is **`27cecb5c-74c6-4abb-b488-714123d9efc2`** (process `BlankProcess2`, Attended, RuntimeType `StudioPro`), **State = Faulted**. It faulted on a UIAutomationNext **`NodeNotFoundException`** — `NClick "Click 'I'm Feeling Lucky'"` inside `NApplicationCard "Edge Google"` in `Main.xaml` — a plain selector / target-not-found failure.

**Healing Agent did NOT run for this job:**

1. The authoritative job field **`AutopilotForRobots`** reports `Enabled = false` AND `HealingEnabled = false` — HA was off for this run.
2. The robot log contains exactly one HA line, at **Level Info**: **`"Healing agent is disabled for the current job."`** This is a **benign informational config-read** — the robot records the HA state it ran with at startup. It appears regardless of HA state, is **non-blocking**, and does **not** mean HA engaged. (This is Surface 2 of the `healing-agent-orch-issues` playbook — the robot config-read log line — in its "disabled" variant.)
3. The HA diagnostic archive (`uip or jobs healing-data`) is a **22-byte empty ZIP** (zero entries) — HA produced no detection or recommendation data.

**Consumption: ZERO.** No AI units, no credits, no AI Trust Layer / LLM calls were consumed. Units are charged only on a **successful heal or recommendation**; with HA disabled, nothing was produced. (Independently, `uip or licenses info` shows `Allowed.AgentService = 0`, `Used.AgentService = 0`, `LicensedFeatures = []` — the tenant has no HA entitlement at all, so HA could not have consumed even if it had been enabled.)

## What the log line means (the user's third question)

`"Healing agent is disabled for the current job."` is purely informational. The robot reads the HA configuration at job start and logs the resulting state. It is **not** evidence that HA ran, and it carries **no execution-time or consumption cost**.

## Correct answer to give the user

- Reassure: HA did **not** run and consumed **nothing** for this job; the log line is informational only.
- The job itself failed for an unrelated reason — a UI Automation selector / target-not-found (`NodeNotFoundException`) on the `I'm Feeling Lucky` click. That is a normal selector failure to fix in the workflow (re-indicate the element, add a Check App State / wait, validate the target). HA being disabled simply means no automated recovery was attempted.
- If the user *wants* HA to attempt recovery on future runs, HA must be enabled on the process/job **and** the tenant must be provisioned with the Healing Agent add-on + Heals (currently `Allowed.AgentService = 0`).

## Must NOT conclude

- ❌ That HA ran or consumed any units / credits for this job (it was disabled; the archive is empty).
- ❌ That the `"Healing agent is disabled for the current job."` log line indicates HA activity or a cost.
- ❌ Treat this as the `"No available license / Agentic units to perform healing analysis and recovery"` notice — that line is **not** present here; this is the disabled-config-read line, a different signal.
- ❌ Recommend stripping `VerifyOptions` / Verify Execution from the activity as a fix.
