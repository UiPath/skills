# Final Resolution

Root Cause: Authoring-time selector typo in the **Click 'Simt ca am noroc'** activity — the workflow's selector targets an `aria-label` value that does not exist in the live page.

What went wrong: The job for process **ERN** in folder **Shared** (job key `d5fed611-e740-406c-a1b0-3c6de3371f17`) faulted because the **Click 'Simt ca am noroc'** activity in **Google.xaml** could not find the "I'm Feeling Lucky" button — its selector's `aria-label` has an extra trailing `cccccccccc` suffix that doesn't match the real element.

Why: The selector for the Click activity was authored with `aria-label='Simt ca am noroccccccccccc'`, but the live element on the page is `aria-label='Simt ca am noroc'`. Every other selector attribute (`css-selector`, `tag`, `type`) is identical to the live element, which proves the live UI did not change — the workflow simply ships with a typo. Healing Agent did run an analysis on the live page (`AutopilotForRobots.Enabled=true`, `HealingEnabled=true`, `AutoHealStatus=IssueDetected`) and identified a 94% match that corrects exactly that typo, but the run was in **recommendation-only mode** (`OrchestratorEnableHeal=false` — job logs: *"Healing agent analysis is enabled but recovery is disabled for current job"* and *"Healing agent could not recover the activity. Self-healing is disabled."*), so HA never retried at runtime and `RecoverySuccessful=false`. Orchestrator surfaced the result as a Faulted job with no automatic retry — Orchestrator does not auto-retry faulted jobs.

Evidence:

### UI Automation (Root Cause)
- Faulted activity: **Click 'Simt ca am noroc'** in **Google.xaml**, inside **Use Application/Browser 'Edge Google'** → **Sequence 'Do'**.
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at 2026-05-12T08:14:10Z.
- Strict selector failure log (08:13:32Z): `aria-label='Simt ca am noroccccccccccc'` did not match any element; HA reported closest live matches at 94%, 82%, 69%, 57%.
- Failed selector (verbatim): `<webctrl aria-label='Simt ca am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`
- Healing Agent's recovered partial selector (94% — `aria-label` corrected, every other attribute identical): `<webctrl aria-label='Simt ca am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit'/>`
- Selector diff: only `aria-label` changes — confirms an authoring typo, not UI drift.
- Healing Agent ran in recommendation-only mode (`OrchestratorEnableHeal=false`); the recovered selector was inferred from the post-failure UI tree but was never validated at runtime (`RecoverySuccessful=false`).

### Orchestrator (Propagation)
- Job for process **ERN** in folder **Shared**, key `d5fed611-e740-406c-a1b0-3c6de3371f17`, host **MOCK-HOST**.
- State: **Faulted**, started 2026-05-12T08:13:00Z, ended 2026-05-12T08:14:11Z.
- `AutopilotForRobots.Enabled=true`, `HealingEnabled=true`, `AutoHealStatus=IssueDetected` — Healing Agent observed the failure but Orchestrator had self-healing disabled for the run, so the fault propagated unchanged.
- Orchestrator does not auto-retry faulted jobs; the run terminated with the UI Automation exception bubbled up verbatim.

Immediate fix:

### UI Automation (Root Cause)
1. Apply Healing Agent's recovered selector to the **Click 'Simt ca am noroc'** activity in **Google.xaml**, replacing the typo'd `aria-label='Simt ca am noroccccccccccc'` with `aria-label='Simt ca am noroc'`.
  - Why: The failed and recovered selectors differ only by the `aria-label` value (failed has an extra trailing `cccccccccc`); every other attribute matches the live element. HA's 94% candidate is the same DOM position with the corrected label.
  - Where: `Google.xaml`, the `NClick` activity named *Click 'Simt ca am noroc'* inside `NApplicationCard 'Edge Google'` → `Sequence 'Do'`. Use the `uia-improve-selector` skill at `<PROJECT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-improve-selector/USAGE.md` if available, otherwise edit the XAML target directly with XML-encoded selector text.
  - Who: RPA developer.
  - Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-fix.md` → `interpretations/healing-agent-data.md` § "Applying `update-target` Fixes".
2. After editing, validate the workflow compiles cleanly.
  - Why: HA's selector was never tested at runtime (recommendation-only mode), so the only safety net before redeploying is a clean compile plus a manual rerun.
  - Where: `uip rpa get-errors --file-path "Google.xaml" --output json --use-studio`.
  - Who: RPA developer.
  - Source: `interpretations/healing-agent-data.md` § "Applying `update-target` Fixes" step 5.

### Orchestrator (Propagation)
1. Restart the faulted job from **Jobs → More Actions → Restart** once the selector fix is published, or trigger a fresh run of the **ERN** process in folder **Shared**.
  - Why: Orchestrator does not auto-retry faulted jobs — the existing job is terminal in the Faulted state and must be re-launched manually after the fix is in place.
  - Where: Orchestrator UI → Folder **Shared** → **Jobs** → job `d5fed611-e740-406c-a1b0-3c6de3371f17` → **More Actions → Restart**.
  - Who: admin or process owner.
  - Source: docsai — https://docs-staging.uipath.com/orchestrator/standalone/2020.10/user-guide/managing-jobs

Preventive fix:

1. UI Automation -- Enable self-healing (not just recommendation-only) for processes that rely on Healing Agent so the next selector defect is corrected at runtime instead of faulting the job.
  - Why: HA already correctly identified the fix on this run, but `OrchestratorEnableHeal=false` blocked the runtime retry (`RecoverySuccessful=false`), turning a recoverable failure into a Faulted job. With self-healing enabled HA would have retried with the 94% candidate and the job would have continued.
  - Where: Orchestrator → process / tenant **AutopilotForRobots** settings — enable self-healing (the runtime flag exposed as `OrchestratorEnableHeal`); confirm `AutopilotForRobots.HealingEnabled=true` at the tenant level.
  - Who: admin / platform team.
  - Source: `references/activity-packages/ui-automation/interpretations/healing-agent-data.md` § "Source Types and Recovery Status" + § "How to Check if HA is Enabled".
2. Orchestrator -- Build explicit retry/alerting around the **ERN** process so that future UI-automation faults are escalated or retried rather than left terminal.
  - Why: Orchestrator does not auto-retry Faulted jobs — without a dispatcher/queue-based retry loop or an alert rule, faults like this one stay terminal until a human notices.
  - Where: Parent/dispatcher workflow or queue triggering **ERN**, or Orchestrator alert rules on Faulted jobs in folder **Shared**.
  - Who: RPA developer + admin.
  - Source: docsai — https://docs-staging.uipath.com/orchestrator/automation-suite/2024.10/user-guide/job-states and https://docs-staging.uipath.com/orchestrator/standalone/2020.10/user-guide/managing-jobs

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Job faulted because the Click 'Simt ca am noroc' activity in Google.xaml has an authoring-time `aria-label` typo (`Simt ca am noroccccccccccc` vs the live `Simt ca am noroc`); Healing Agent produced a recommendation-only recovery for it. | high | confirmed | yes | Strict selector failure log at 08:13:32Z with `aria-label='Simt ca am noroccccccccccc'`; HA 94% match selector identical except for `aria-label='Simt ca am noroc'`; `OrchestratorEnableHeal=false` (logs: "recovery is disabled for current job"); `RecoverySuccessful=false`; ancestry matches triage (NClick inside NApplicationCard 'Edge Google' / Sequence 'Do' in Google.xaml). | Apply HA's recovered selector to the Click activity (interactive — see Post-presentation actions); enable self-healing at runtime; add Orchestrator-side retry/alerting. |

---

Now executing **Post-presentation Action 1 — Apply Healing Agent recovered selector**.

Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-fix.md` → `interpretations/healing-agent-data.md` § "Applying Fixes — MUST Ask the User".

```
Failed selector:
<webctrl aria-label='Simt ca am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />

Recovered Partial selector:
<webctrl aria-label='Simt ca am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit'/>

Recovered Fuzzy selector:
(not available — fuzzy variant lives in uia/*.json on host MOCK-HOST and is not exposed via Orchestrator OData)
```

**Warning:** Healing Agent was running in recommendation-only mode (OrchestratorEnableHeal=false) — the recovered selector was inferred from the UI tree after the failure but was not validated at runtime. There is no guarantee it will work.
