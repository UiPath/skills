# Final Resolution

Root Cause: Healing Agent refused to run on this job because the tenant's Healing Agent consumable pool is **exhausted** — the tenant IS entitled (`Allowed.AgentService=5000`, `LicensedFeatures` includes `HealingAgent`) but has already consumed its full allocation for the billing period (`Used.AgentService=5000`, i.e. `Used >= Allowed`). With no remaining Heals to spend, Healing Agent emitted "No available license / Agentic units to perform healing analysis and recovery" and produced an empty (22-byte) healing-data archive, leaving the underlying selector exception as the terminal fault. The `NodeNotFoundException` on the "Click 'Simt că am noroc'" activity is an authoring-time selector typo that HA would normally have recovered — had a Heal been available.

What went wrong: The "Click 'Simt că am noroc'" activity in `Google.xaml` failed with `NodeNotFoundException`, and Healing Agent — which was enabled on the run and would normally have recovered the selector — refused to execute because the tenant's Heals allocation is fully consumed for this period.

Why: The activity's authoring-time selector targets `aria-label='Simt că am noroccccccccccc'` (with nine extra trailing `c` characters); the live element is `aria-label='Simt că am noroc'` (94% closest match). Strict selector matching threw `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at 2026-05-15T17:10:18.631Z. The job had `AutopilotForRobots.Enabled=true` and `AutopilotForRobots.HealingEnabled=true`, so Healing Agent was invoked for this activity — but 413 ms earlier, at 17:10:18.218Z, Healing Agent logged at Error level: `'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.` The tenant's `uip or licenses info` returns `Data.Allowed.AgentService=5000` with `Data.Used.AgentService=5000` and `Data.LicensedFeatures` containing `HealingAgent` — the deterministic signature of an **exhausted pool** (`Used >= Allowed` while `Allowed > 0`), NOT a missing entitlement. The job's release `ProcessType` is `Process` (not `TestAutomationProcess`), so the requested pool is regular Heals (operation code `HealingAgent`), not Test Heals. With the Heals pool drained, Healing Agent could not consume a Heal, refused to run, and the selector exception propagated up to Orchestrator as a `Faulted` job with `ErrorCode=Robot`.

Evidence:

### UI Automation (Root Cause)
- Faulted activity: **Click 'Simt că am noroc'** (NClick) in `Google.xaml`, inside `NApplicationCard "Edge Google"` → `Sequence "Do"`.
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at `UiPath.UIAutomationNext.Activities.TargetCommonLogic.GetSearchResultAsync`.
- Failed target selector (authoring): `<webctrl aria-label='Simt că am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`.
- Closest live match (94%): `<webctrl aria-label='Simt că am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit'/>` — nine extra trailing `c` characters on the authoring side.
- Healing Agent refusal log line (verbatim, Level=Error, 2026-05-15T17:10:18.218Z): `'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.`
- Healing Agent diagnostic archive (`uip or jobs healing-data`): **22 bytes** — empty ZIP, zero entries.
- Tenant license (the discriminator): `Data.Allowed.AgentService=5000`, `Data.Used.AgentService=5000` (`Used >= Allowed` → **pool exhausted**), `Data.LicensedFeatures=["HealingAgent"]` (HA IS entitled), `Data.SubscriptionPlan='ENTERPRISE'`, `Data.IsExpired=false`.
- Operation code (regular Heals): release `ProcessType='Process'` (not `TestAutomationProcess`) → pool requested is `HealingAgent`, not `HealingAgent.Test`.

### Orchestrator (Propagation)
- Job state: **Faulted** (process **ERN**, entry point `Google.xaml`).
- Folder: **Shared**.
- Host machine: **MOCK-HOST**.
- Job key (for commands): `d2c90d73-bcee-4f9d-b9fc-d37146b7f6ff`. Trace ID: `d2c90d73bcee4f9db9fcd37146b7f6ff`.
- StartTime 2026-05-15T17:09:44.470Z; EndTime 2026-05-15T17:10:18.527Z (~34 s).
- `ErrorCode='Robot'`, `JobError={}` — actionable detail is in the robot log, not on the job record.
- `AutopilotForRobots.Enabled=true`, `AutopilotForRobots.HealingEnabled=true` on the job.

Immediate fix:

### UI Automation (Root Cause)
1. Replenish the Healing Agent consumable pool for this tenant, or wait for the billing period to reset.
  - Why: `uip or licenses info` shows `Data.Allowed.AgentService=5000` with `Data.Used.AgentService=5000` (`Used >= Allowed`) — the tenant IS entitled to Healing Agent but has consumed its entire Heals allocation for the period. This is the deterministic signature for a **pool-exhausted** condition (playbook cause #7), NOT a missing entitlement (`Allowed > 0`, `LicensedFeatures` includes `HealingAgent`). Acquiring another Add-On would not help — the entitlement already exists; the units are spent.
  - Where: Automation Cloud admin portal → **Admin** → **Licenses** → **Consumables**. Allocate additional Heals to this tenant, or wait for the monthly billing reset. After the bundled 5K Heals are consumed, overflow is charged at **3 Platform Units per heal (Unified)** or **15 Agent Units per heal (Flex)** — verify the overflow unit pool has capacity.
  - Who: Tenant admin / platform team.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Resolution, bullet (operation code `HealingAgent` + `Allowed.AgentService > 0` + `Used.AgentService >= Allowed.AgentService`).

2. After the pool has capacity again, restart the same job (or trigger a new run from the **ERN** process).
  - Why: Cause #7 is a consumable-capacity block; Healing Agent will be invoked again on the next run and is expected to recover the selector typo automatically (the live match at 94% is well within HA's recovery range). If HA still produces no data after the pool is replenished, the investigation escalates to `no-recovery-data.md` (other causes: Semantic Proxy connectivity, classic activity, image-only target).
  - Where: Orchestrator → **Jobs** → **Start Job** on process **ERN** in folder **Shared**.
  - Who: RPA developer or process owner.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Resolution, last bullet ("In all branches: after the licensing issue is resolved, restart the same job").

### Orchestrator (Propagation)
1. Enable Orchestrator alert emails for faulted jobs so future occurrences surface proactively instead of being discovered post-hoc.
  - Why: The faulted job for process **ERN** had `JobError={}` on the job record — actionable detail lived only in the robot log. Orchestrator's standard propagation surface for faulted jobs is its alert-email pipeline; without it, faulted jobs require manual restart from the **Jobs** screen (jobs in `Faulted` cannot be auto-retried at the job level — only queue items can).
  - Where: Orchestrator → **Settings** → **General** → enable **Enable Alerts Email** and configure SMTP settings. Confirm each recipient has a valid email and **View** permission on **Alerts**. Orchestrator will then send aggregated Fatal/Error alerts every 10 minutes and a daily Alerts Dashboard email that includes the **Faulted Jobs** count.
  - Who: Orchestrator admin.
  - Source: https://docs-staging.uipath.com/orchestrator/standalone/2022.4/user-guide/setting-up-alert-emails

Preventive fix:

1. **UI Automation** — Correct the authoring-time selector typo in `Google.xaml` so the activity does not depend on Healing Agent for normal operation.
  - Why: The failed selector's `aria-label` is `Simt că am noroccccccccccc` (nine extra trailing `c` characters); the live element's `aria-label` is `Simt că am noroc` at 94% match. Every run of this activity burns one Heal to recover the same authoring defect — which is precisely what drained the pool. Fixing the selector eliminates the recurring Heal consumption and removes the dependency on the pool having capacity for this workflow to succeed.
  - Where: `Google.xaml`, activity `NClick "Click 'Simt că am noroc'"` (under `NApplicationCard "Edge Google"` → `Sequence "Do"`). Update the target selector's `aria-label` from `Simt că am noroccccccccccc` to `Simt că am noroc`.
  - Who: RPA developer.
  - Source: `evidence/triage-initial.json` and `raw/triage-jobs-logs-error.json` (closest selector matches found, 94% on `aria-label='Simt că am noroc'`).

2. **UI Automation** — Monitor Heals consumption and budget the pool against the portfolio's healing rate.
  - Why: With Healing Agent enabled, every unrecovered selector on each job consumes one Heal (3 Platform Units per heal on Unified, 15 Agent Units on Flex after the bundled 5K is exhausted). A recurring authoring defect like this one silently drains the pool; tracking consumption prevents a mid-period exhaustion that faults otherwise-recoverable jobs.
  - Where: Automation Cloud → **Admin** → **Licenses** → **Consumables** (Heals usage), and process settings for **ERN** (Autopilot for Robots → Healing Enabled toggle).
  - Who: RPA developer or process owner.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Licensing model.

3. **Orchestrator** — Where workflows are queue-driven, enable queue-level auto-retry so transient failures do not require manual restart even when Healing Agent is unavailable.
  - Why: Job-level retry does not exist in Orchestrator — `Faulted` jobs must be restarted manually unless they consume from a queue with **Auto Retry** enabled. For processes like **ERN** that target external UIs (Google), a queue front-end is the documented resilience pattern.
  - Where: Orchestrator → **Queues** → **Add** → set **Auto Retry = Yes** and **Max # of retries** = desired retry count.
  - Who: RPA developer / Orchestrator admin.
  - Source: https://docs-staging.uipath.com/orchestrator/automation-suite/2021.10/user-guide/managing-queues-in-orchestrator

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|---|---|---|---|---|---|
| H1 | Healing Agent refused to run on job `d2c90d73-bcee-4f9d-b9fc-d37146b7f6ff` because the tenant's Heals pool is exhausted (`Allowed.AgentService=5000`, `Used.AgentService=5000` → `Used >= Allowed`), NOT because HA is unlicensed; the underlying NClick `NodeNotFoundException` on "Click 'Simt că am noroc'" (authoring selector typo) would normally have been recovered by HA. | high | confirmed | yes | Robot Error log 17:10:18.218Z (HA "No available license"); 22-byte empty HA archive; `licenses info` Allowed.AgentService=5000 with Used.AgentService=5000 and LicensedFeatures=["HealingAgent"]; Autopilot+Healing enabled on job; release ProcessType=Process (regular Heals pool); HA refusal precedes terminal exception by 413 ms on same activity. | Replenish the Heals pool (or wait for the billing reset), restart the **ERN** job; independently correct the `aria-label` typo in `Google.xaml` to stop draining Heals. |
