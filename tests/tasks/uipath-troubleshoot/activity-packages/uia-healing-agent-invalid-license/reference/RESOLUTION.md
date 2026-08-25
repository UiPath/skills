# Final Resolution

Root Cause: Healing Agent refused to run on this job because the tenant has no Healing Agent entitlement (regular Heals pool). The underlying NodeNotFoundException on the "Click 'Simt că am noroc'" activity is an authoring-time selector typo that Healing Agent would normally have recovered — but with `Allowed.AgentService=0` and `LicensedFeatures=[]`, Healing Agent emitted "No available license / Agentic units to perform healing analysis and recovery" and produced an empty (22-byte) healing-data archive, leaving the selector exception as the terminal fault.

What went wrong: The "Click 'Simt că am noroc'" activity in `Google.xaml` failed with `NodeNotFoundException`, and Healing Agent — which was enabled on the run and would normally have recovered the selector — refused to execute because the tenant is not entitled to Healing Agent consumables.

Why: The activity's authoring-time selector targets `aria-label='Simt că am noroccccccccccc'` (with nine extra trailing `c` characters); the live element is `aria-label='Simt că am noroc'` (94% closest match). Strict selector matching threw `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at 2026-05-15T17:10:18.631Z. The job had `AutopilotForRobots.Enabled=true` and `AutopilotForRobots.HealingEnabled=true`, so Healing Agent was invoked for this activity — but 413 ms earlier, at 17:10:18.218Z, Healing Agent logged at Error level: `'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.` The tenant's `uip or licenses info` returns `Data.Allowed.AgentService=0` and `Data.LicensedFeatures=[]`, despite `SubscriptionPlan='ENTERPRISE'` — per the matched playbook, the ENTERPRISE plan label does not imply HA bundling (only Flex Advanced and Unified Enterprise bundle Heals, and the HA Add-On must be provisioned). With no entitlement, Healing Agent could not consume a Heal, refused to run, and the selector exception propagated up to Orchestrator as a `Faulted` job with `ErrorCode=Robot`. The job's RuntimeType (`StudioPro`) is in the Non-Test set, so the pool that should have been charged is regular Heals (operation code `HealingAgent`), not Test Heals.

Evidence:

### UI Automation (Root Cause)
- Faulted activity: **Click 'Simt că am noroc'** (NClick) in `Google.xaml`, inside `NApplicationCard "Edge Google"` → `Sequence "Do"`.
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at `UiPath.UIAutomationNext.Activities.TargetCommonLogic.GetSearchResultAsync`.
- Failed target selector (authoring): `<webctrl aria-label='Simt că am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`.
- Closest live match (94%): `<webctrl aria-label='Simt că am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit'/>` — nine extra trailing `c` characters on the authoring side.
- Healing Agent refusal log line (verbatim, Level=Error, 2026-05-15T17:10:18.218Z): `'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.`
- Healing Agent diagnostic archive (`uip or jobs healing-data`): **22 bytes** — empty ZIP, zero entries.
- Tenant license: `Data.Allowed.AgentService=0`, `Data.Used.AgentService=0`, `Data.LicensedFeatures=[]`, `Data.SubscriptionPlan='ENTERPRISE'`, `Data.IsExpired=false`.
- Operation code (inferred from `RuntimeType='StudioPro'`, Non-Test set): `HealingAgent` → regular Heals pool requested.

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
1. Acquire the Healing Agent Add-On for this tenant, or move the tenant to a plan that bundles Heals (Flex Advanced or Unified Enterprise).
  - Why: `uip or licenses info` returns `Data.Allowed.AgentService=0` and `Data.LicensedFeatures=[]`. Per the matched playbook, this is the deterministic signature for "No Healing Agent entitlement on the tenant" — the plan tier label (`ENTERPRISE`) alone does not encode whether HA is bundled (Flex vs Unified is not exposed in `licenses info`).
  - Where: Automation Cloud admin portal → **Admin** → **Licenses** → **Consumables**. Provision the Healing Agent Add-On against this tenant, or change the subscription to Flex Advanced / Unified Enterprise (both bundle 5,000 Heals).
  - Who: Tenant admin / platform team.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Resolution, first bullet (operation code `HealingAgent` + `Allowed.AgentService==0` + `LicensedFeatures:[]`).

2. After the entitlement is in place, restart the same job (or trigger a new run from the **ERN** process).
  - Why: Cause #1 is a licensing block; Healing Agent will be invoked again on the next run and is expected to recover the selector typo automatically (the live match at 94% is well within HA's recovery range). If HA still produces no data after the license fix, the investigation escalates to `no-recovery-data.md` (other causes: Semantic Proxy connectivity, classic activity, image-only target).
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
  - Why: The failed selector's `aria-label` is `Simt că am noroccccccccccc` (nine extra trailing `c` characters); the live element's `aria-label` is `Simt că am noroc` at 94% match. Even with Healing Agent licensed, every run of this activity would burn one Heal to recover the same authoring defect. Fixing the selector eliminates the recurring HA charge and removes the dependency on HA being licensed for this workflow to succeed.
  - Where: `Google.xaml`, activity `NClick "Click 'Simt că am noroc'"` (under `NApplicationCard "Edge Google"` → `Sequence "Do"`). Update the target selector's `aria-label` from `Simt că am noroccccccccccc` to `Simt că am noroc`.
  - Who: RPA developer.
  - Source: `evidence/triage-initial.json` and `raw/triage-jobs-logs-error.json` (closest selector matches found, 94% on `aria-label='Simt că am noroc'`).

2. **UI Automation** — After the tenant is entitled, decide whether to keep Healing Agent enabled on this process and budget for Heal consumption.
  - Why: With Healing Agent enabled, every unrecovered selector on each job consumes one Heal (3 Platform Units per heal on Unified, 15 Agent Units on Flex after the bundled 5K is exhausted). For workflows whose selectors are stable post-fix, the runtime cost may not be justified; for workflows targeting volatile UIs, HA is the cheaper option.
  - Where: Process settings for **ERN** in Orchestrator (Autopilot for Robots → Healing Enabled toggle).
  - Who: RPA developer or process owner.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Licensing model.

3. **Orchestrator** — Where workflows are queue-driven, enable queue-level auto-retry so transient failures do not require manual restart even when Healing Agent is unavailable.
  - Why: Job-level retry does not exist in Orchestrator — `Faulted` jobs must be restarted manually unless they consume from a queue with **Auto Retry** enabled. For processes like **ERN** that target external UIs (Google), a queue front-end is the documented resilience pattern.
  - Where: Orchestrator → **Queues** → **Add** → set **Auto Retry = Yes** and **Max # of retries** = desired retry count.
  - Who: RPA developer / Orchestrator admin.
  - Source: https://docs-staging.uipath.com/orchestrator/automation-suite/2021.10/user-guide/managing-queues-in-orchestrator

**Note on confidence:** The depth-verifier flagged a textual gap — `H1.resolution` was `null` in `hypotheses.json` even though the named cause (`## Causes #1` — missing tenant entitlement) and matching `## Resolution` branch were both unambiguously identified by the tester. The resolution above is assembled directly from the matched playbook's first `## Resolution` bullet. H1 is presented at **medium** confidence in the summary below to reflect the textual gap, even though the underlying cause-evidence alignment is deterministic.

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|---|---|---|---|---|---|
| H1 | Healing Agent refused to run on job `d2c90d73-bcee-4f9d-b9fc-d37146b7f6ff` because the tenant has no Healing Agent entitlement (`Allowed.AgentService=0`, `LicensedFeatures=[]`); the underlying NClick `NodeNotFoundException` on "Click 'Simt că am noroc'" (authoring selector typo) would normally have been recovered by HA. | medium | confirmed | yes | Robot Error log 17:10:18.218Z (HA "No available license"); 22-byte empty HA archive; `licenses info` Allowed.AgentService=0 + LicensedFeatures=[]; Autopilot+Healing enabled on job; RuntimeType=StudioPro (regular Heals pool); HA refusal precedes terminal exception by 413 ms on same activity. | Acquire HA Add-On (or move to Flex Advanced / Unified Enterprise), restart the **ERN** job; independently correct the `aria-label` typo in `Google.xaml`. |

---

Want me to help implement any of these (e.g., open `Google.xaml` and apply the selector fix), or clean up `.local/investigations/`?
