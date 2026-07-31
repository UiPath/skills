# Final Resolution

Root Cause: Healing Agent refused to recover a selector-drift fault on the Click 'Simt că am noroc' activity because the tenant has no Healing Agent entitlement (Allowed.AgentService=0, LicensedFeatures=[]).

What went wrong: The most recent job of process **ERN** in folder **Shared** faulted on a Click activity because the workflow's selector aria-label has trailing garbage characters and no longer matches the live element, and Healing Agent — which is designed to heal exactly this drift — refused to run for lack of a license consumable.

Why: The activity **Click 'Simt că am noroc'** in **Google.xaml** raised `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` because the workflow's selector targets `aria-label='Simt că am noroccccccccccc'` (extra trailing `cccccccccc`) while the live element is `aria-label='Simt că am noroc'` — a 94% match that Healing Agent is built to recover automatically. Healing Agent was enabled on the run (`AutopilotForRobots.Enabled=true`, `HealingEnabled=true`), but the tenant has zero Healing Agent entitlement on this `ENTERPRISE` plan (`Allowed.AgentService=0`, `LicensedFeatures=[]`). HA therefore emitted the canonical no-license error, produced no diagnostic data (22-byte empty healing-data archive), and let the underlying selector exception propagate to a job fault. RuntimeType `StudioPro` is in the Non-Test set, so the pool requested was regular **Heals**, not Test Heals. The `ENTERPRISE` plan label alone is not diagnostic — it could be Flex Enterprise without the HA Add-On, or Unified Enterprise where the bundled Heals were not provisioned to this tenant. The deterministic signal is `Allowed.AgentService=0` with empty `LicensedFeatures`.

Evidence:

### UI Automation (Root Cause)
- Failing activity: **Click 'Simt că am noroc'** (`NClick`) in **Google.xaml**, path: `Google` → `Sequence "Google"` → `NApplicationCard "Edge Google"` → `Sequence "Do"` → `Click 'Simt că am noroc'`.
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException`.
- Workflow selector (failed): `<webctrl aria-label='Simt că am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`.
- Live element closest match (94%): `<webctrl aria-label='Simt că am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />` — same DOM position, only the `aria-label` differs (trailing `cccccccccc` appended in the workflow).
- Healing Agent was enabled on the run (`AutopilotForRobots.Enabled=true`, `AutopilotForRobots.HealingEnabled=true`) but produced no diagnostic data — the `uip or jobs healing-data` archive is exactly 22 bytes (empty ZIP, end-of-central-directory record only, zero entries). HA refused to run.

### Orchestrator (Propagation / Signal Source)
- Job: process **ERN**, key `cedeff5a-ba9b-4ff5-80c2-b79b5662f59b`, folder **Shared**, host **MOCK-HOST**, Type `Attended`, RuntimeType `StudioPro`, EntryPointPath `Google.xaml`. CreationTime `2026-05-18T12:48:38.730Z`, EndTime `2026-05-18T12:49:13.423Z`, State `Faulted`, ErrorCode `Robot`, JobError `{}`.
- Robot Error log at `2026-05-18T12:49:12.651Z` (verbatim): `'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.` — the canonical English deterministic signal for missing HA entitlement.
- Tenant licensing (`uip or licenses info`): `SubscriptionPlan=ENTERPRISE`, `Allowed.AgentService=0`, `Used.AgentService=0`, `LicensedFeatures=[]`. `Allowed.AgentService=0` with empty `LicensedFeatures` is the deterministic missing-entitlement signal; the plan label is not diagnostic on its own.
- RuntimeType `StudioPro` is in the Non-Test set, so the requested consumable pool is **Heals** (regular), not **Test Heals**.

Immediate fix:

### UI Automation (Root Cause)
1. Correct the selector typo in **Google.xaml** on the **Click 'Simt că am noroc'** activity — change `aria-label='Simt că am noroccccccccccc'` to `aria-label='Simt că am noroc'`.
  - Why: The workflow's `aria-label` has an obvious authoring regression (trailing `cccccccccc`); the live element is `Simt că am noroc` at the identical DOM position (94% closest match). With no HA license, this manual correction is the only path to make the activity pass.
  - Where: `Google.xaml`, activity path `Google` → `Sequence "Google"` → `NApplicationCard "Edge Google"` → `Sequence "Do"` → `Click 'Simt că am noroc'`.
  - Who: RPA developer.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Resolution ("without the license, manual fix is to correct the selector aria-label in Google.xaml") and evidence file `evidence/H1-ha-no-license.json` (`failed_selector_xml` vs `closest_match_selector_xml`).

### Orchestrator (Root Cause — Entitlement)
1. Acquire the Healing Agent Add-On for this tenant, **or** move the tenant to a plan that bundles Heals (Flex Advanced or Unified Enterprise both bundle 5K Heals).
  - Why: `Allowed.AgentService=0` and `LicensedFeatures=[]` on the tenant — this is Cause #1 in the matched playbook ("No Healing Agent entitlement on the tenant"). Plan name alone is not diagnostic; the current `ENTERPRISE` label could be Flex Enterprise without the HA Add-On, or Unified Enterprise that has not yet been provisioned with Heals. Without the entitlement, every future selector-drift failure on this tenant will fault the same way.
  - Where: Automation Cloud admin portal → Admin → Licenses → Consumables. Confirm the Heals pool ends up in the **Enabled** state on this tenant, not merely present.
  - Who: UiPath tenant admin / platform team.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Resolution (first branch: `Operation code HealingAgent` + `Allowed.AgentService==0` + `LicensedFeatures: []`).
2. After the license is in place, re-run the failed job (`uip or jobs start-process` or via Orchestrator UI). If HA produces data on the retry, continue with `selector-failure-healing-fix.md`. If HA still produces no data, escalate to `no-recovery-data.md` (other causes: connectivity to Semantic Proxy / LLM Gateway, classic activity, image-only target).
  - Why: The playbook explicitly directs verification of the fix by retrying the same job; only a successful retry proves the entitlement change took effect.
  - Where: Orchestrator → folder `Shared` → process **ERN**.
  - Who: RPA developer / operator.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Resolution (final bullet, "In all branches").

Preventive fix:

1. UI Automation — Author selectors with strict-attribute targeting only on values that are stable. The current failure is a hand-edit typo (`Simt că am noroc` → `Simt că am noroccccccccccc`); a fuzzy or relaxed selector strategy on the `aria-label` would have masked it. Use the Studio Object Repository / Selector Editor's "Validate selector" against the live target before publishing.
  - Why: The selector regression survived publish because nothing validated the workflow selector against a live page. Evidence: `aria-label='Simt că am noroccccccccccc'` does not match any element on the page (best live match is 94%).
  - Where: `Google.xaml` and any other workflow that targets the Google search page; Studio Object Repository.
  - Who: RPA developer.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Context (HA exists precisely to absorb this class of selector drift; without it, authoring discipline is the only defense).
2. Orchestrator — Once the HA entitlement is provisioned, verify periodically that the Heals pool stays enabled and is not exhausted (`uip or licenses info` → `Data.Allowed.AgentService` and `Data.Used.AgentService`). The bundled 5K heals are consumed per unique recovered element per job; after exhaustion, Unified spends 3 Platform Units per heal and Flex spends 15 Agent Units per heal.
  - Why: `Allowed.AgentService=0` today means every HA-eligible failure on this tenant degrades to a hard fault; a depleted or disabled pool produces the same outcome later.
  - Where: Automation Cloud → Admin → Licenses → Consumables; `uip or licenses info --output json`.
  - Who: UiPath tenant admin / platform team.
  - Source: `references/activity-packages/ui-automation/playbooks/healing-agent-no-license.md` § Investigation step 5 and § Resolution (pool-exhausted branch).

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Job `ERN` faulted on the Click 'Simt că am noroc' activity with `NodeNotFoundException` (workflow selector `aria-label='Simt că am noroccccccccccc'` vs live `'Simt că am noroc'`, 94% match); Healing Agent was enabled but refused to run because the tenant has no HA entitlement (`Allowed.AgentService=0`, `LicensedFeatures=[]`), so the underlying selector mismatch propagated to a job fault. | high | confirmed | yes | Robot Error log line `'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.` at `2026-05-18T12:49:12.651Z`; `AutopilotForRobots.Enabled=true` and `HealingEnabled=true`; healing-data archive 22 bytes (empty ZIP); `Allowed.AgentService=0`, `LicensedFeatures=[]`; RuntimeType `StudioPro` (Non-Test → regular Heals pool). | (a) Correct the selector `aria-label` in **Google.xaml** from `Simt că am noroccccccccccc` to `Simt că am noroc`; (b) acquire the HA Add-On for the tenant, or move to a plan that bundles Heals (Flex Advanced or Unified Enterprise); (c) retry the job and continue with `selector-failure-healing-fix.md` only if HA produces data on retry.  |
