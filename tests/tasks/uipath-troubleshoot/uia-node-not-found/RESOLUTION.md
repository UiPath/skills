# Final Resolution

Root Cause: Wrong-page-scope authoring defect in TO.xaml — NApplicationCard "Edge Google" attaches to a pre-existing Google homepage tab (AttachMode=ByInstance) and never navigates to doodles.google, so the Click "Creating a Doodle" runs against the wrong page where the target element does not exist.

What went wrong: The Click "Creating a Doodle" activity tried to find a link inside the Google Doodles archive drawer, but the browser was on the Google.ro homepage and never reached doodles.google.

Why: TO.xaml's NApplicationCard "Edge Google" is configured with `TargetApp.Url='https://www.google.com/'`, `TargetApp.Selector` title `'Google'`, and `AttachMode='ByInstance'`. At runtime on host MOCK-HOST, an existing Edge window with title "Google" (the Google.ro homepage in Romanian locale) was already open, so the card latched onto it instead of opening or navigating anywhere. The card's body contains exactly one child — the failing Click — and the entire project (Main.xaml, TO.xaml, ERN.xaml, Google.xaml, Transaction.xaml) contains zero navigation activities (NGoToUrl / NavigateBrowser / OpenBrowser) inside any NApplicationCard. The Click's selector (`<webctrl aaname=' Creating a Doodle ' class='glue-header__link' parentid='glue-drawer-2465973' tag='A' />`) targets the doodles.google archive drawer, but the live DOM was the Google.ro homepage, so UI Automation raised NodeNotFoundException after the 5 s timeout. Healing Agent was enabled and ran, but because the live page is an entirely different page family from the target, all 13 alternative-target analyzers returned zero detections; there was no correct target to recover toward, so `RecoverySuccessful=false`, `ConsumedReason='RecoveryFailed'`, and no `healing-fixes.json` was produced. Orchestrator then surfaced the activity-level failure as a Faulted job — Orchestrator is the propagation layer here, not the originating fault.

Evidence:

### UI Automation (Root Cause)
- Failing activity: Click "Creating a Doodle" (NClick_1) in `TO.xaml`, inside NApplicationCard "Edge Google", inside Sequence "TO".
- Exception: `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at 2026-05-19T10:03:29.9767309Z (8.4 s after job start).
- Failed selector (verbatim from `raw/healing-data/uia/639147818412857258.json`, `FailedResolvedTarget.PartialSelector`):
  `<webctrl aaname='                   Creating a Doodle                 ' class='glue-header__link' parentid='glue-drawer-2465973' tag='A' />`
- Parent NApplicationCard "Edge Google" configuration (TO.xaml lines 94, 113–122):
  - `TargetApp.Url = 'https://www.google.com/'` (generic Google homepage, NOT doodles.google)
  - `TargetApp.Selector = <html app='msedge.exe' title='Google' />` (permissive homepage title; does NOT match the Doodles archive title)
  - `AttachMode = 'ByInstance'` (attach-only — does not launch or navigate)
  - Body Sequence "Do" contains exactly one child: the failing Click. Zero navigation activities anywhere in the card.
- Repo-wide search for `NGoToUrl | NavigateBrowser | OpenBrowser | NGoToUrlX` across all project .xaml files: zero matches inside any NApplicationCard scope.
- Wrong-page-scope four-criteria gate (selector-failure-healing-disabled.md step 6): all four PASS.
  - (a) parent `TargetApp.Url='https://www.google.com/'` ≠ child `Target.BrowserURL='doodles.google'`.
  - (b) `AttachMode='ByInstance'` (canonical attach-only mode named in the playbook).
  - (c) Navigation-activity count inside the card before the failing Click = 0.
  - (d) Closest-match list in `OriginalException` is 10/10 Google.ro homepage chrome (classes `gb_4`/`gb_C` under parentid `gb`/`gbwa`, `pHiOh` footer family, `w5hRs` Google Store), all in Romanian — zero `glue-*` or drawer parentid candidates.
- Healing Agent telemetry (`HealingAgentContext.OrchestratorEnableHeal=true`, `GovernanceEnableHeal=true`): all 13 alternative-target analyzers ran with `DetectionsCount=0`; `RecoveryInfo=null`, `InferredRecoveryInfo=null`, `RecoverySuccessful=false`, `ConsumedReason='RecoveryFailed'`; no `healing-fixes.json` written. Per the playbook: enabling HA does not fix wrong-page-scope defects.

### Orchestrator (Propagation)
- Process ERN v1.0.8, release "ERN", entry point TO.xaml.
- Job 899a0c10-d81b-44ea-9d29-cecc00fd8976 in folder "Shared", host machine MOCK-HOST, runtime StudioPro.
- Job state: Faulted. Start 2026-05-19T10:03:21.587Z, end 2026-05-19T10:04:04.930Z, fault at 10:03:29.977Z.
- Orchestrator surfaced the activity-level NodeNotFoundException as a faulted job; there is no Orchestrator-side misconfiguration — it correctly reported what the activity raised.

Immediate fix:

### UI Automation (Root Cause)
Pick one of the three branches below (in order of preference). All three address the same defect; only one needs to be applied.

1. Insert a navigation activity inside NApplicationCard "Edge Google" before the failing Click.
   - Why: The card never navigates to doodles.google, so the live page is whatever the pre-existing Edge "Google" tab happened to be (Google.ro homepage in this run). A "Go To URL" activity forces the attached tab onto the expected page.
   - Where: ``, inside the NApplicationCard "Edge Google" Body / Sequence "Do", before the Click "Creating a Doodle". Add a "Go To URL" (NGoToUrl) targeting the Doodles archive URL the Click was recorded against (e.g., `https://doodles.google/` or the specific archive page that hosts the drawer with id `glue-drawer-2465973`).
   - Who: RPA developer.
   - Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md` § Resolution → "If wrong-page scope (authoring defect)".

2. Repoint the card's TargetApp.Url to the Doodles archive and tighten the title selector.
   - Why: With AttachMode=ByInstance, the card needs a selector that uniquely identifies the Doodles archive tab; otherwise it will keep latching onto any "Google"-titled tab.
   - Where: ``, NApplicationCard "Edge Google": change `TargetApp.Url` from `https://www.google.com/` to the Doodles archive URL, and change `TargetApp.Selector` title from the permissive `'Google'` to the actual Doodles archive page title (e.g., the title the failing Click's design-time recording captured in its `ScopeSelectorArgument`).
   - Who: RPA developer.
   - Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md` § Resolution → "If wrong-page scope (authoring defect)".

3. Change AttachMode away from ByInstance so the card opens/navigates rather than only attaching.
   - Why: ByInstance silently fails-open onto any pre-existing tab matching the (permissive) title. A launch/navigate mode forces the card to land on the intended page.
   - Where: ``, NApplicationCard "Edge Google": change `AttachMode='ByInstance'` to a mode that opens/navigates (e.g., `OpenIfNotRunning` plus the corrected `TargetApp.Url`).
   - Who: RPA developer.
   - Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md` § Resolution → "If wrong-page scope (authoring defect)".

After applying any of the three options, validate the workflow: `uip rpa get-errors --file-path "" --output json`.

### Orchestrator (Propagation)
1. Restart the job from Orchestrator after the TO.xaml fix is published.
   - Why: Faulted jobs must be restarted manually — Orchestrator does not auto-retry process-level faults.
   - Where: Orchestrator → Jobs → locate process ERN job (key `899a0c10-d81b-44ea-9d29-cecc00fd8976`) → More Actions → Restart. Or republish ERN to a new version and trigger a fresh run.
   - Who: Process owner / RPA developer.
   - Source: docsai → https://docs-staging.uipath.com/orchestrator/automation-suite/2.2510/user-guide/job-states and https://docs-staging.uipath.com/orchestrator/standalone/2020.10/user-guide/managing-jobs.

Preventive fix:

1. UI Automation — keep Healing Agent enabled on the ERN process for future selector drift, but do not rely on it as a substitute for correct scoping.
   - Why: Healing Agent is currently enabled (`OrchestratorEnableHeal=true`) and ran for this fault, but produced no recovered selector because the live page is the wrong page entirely — HA can only recover against the page actually rendered. Keeping HA on remains useful for future genuine selector drift, but the wrong-page-scope authoring defect is invisible to it.
   - Where: Orchestrator → Tenant / Folder → Process ERN → Autopilot / Healing settings (already on; verify it stays on after the fix is published).
   - Who: Admin / process owner.
   - Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md` § Resolution → "Always" + the playbook's explicit caveat that HA does not fix wrong-page-scope defects.

2. UI Automation — author every NApplicationCard / Attach Browser scope so its `TargetApp.Url` (or `TargetApp.Selector` title) matches the page its child activities target, and avoid `AttachMode=ByInstance` unless a navigation activity inside the scope explicitly drives the browser to the expected page.
   - Why: All four wrong-page-scope criteria from the playbook gate were met in TO.xaml; the same authoring pattern (generic homepage URL + permissive title + ByInstance + zero navigation children) can recur in any future workflow.
   - Where: Code-review checklist for any new UI workflow; apply to every browser-scoped activity in the ERN project today.
   - Who: RPA developer / code-review reviewer.
   - Source: `references/activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md` § Causes → "Wrong-page scope (authoring defect)" and § Resolution.

3. Orchestrator — turn on job recording for the ERN process so future faults capture the live page state.
   - Why: There is no Orchestrator playbook for this propagation pattern (a child activity fault surfacing as a faulted job); recordings give the next investigation direct visual evidence of the live page at fault time instead of having to infer it from Healing Agent close-matches.
   - Where: Orchestrator → Tenant Settings → Processes / Process ERN → Enable Recording. Then on faulted runs use More Options → Download Recording.
   - Who: Admin / process owner.
   - Source: docsai → https://docs-staging.uipath.com/orchestrator/standalone/2020.10/user-guide/about-jobs (Recording section) and https://docs-staging.uipath.com/orchestrator/automation-suite/2.2510/user-guide/job-states.

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Selector mismatch on Click "Creating a Doodle"; Healing Agent active and produced recovery data — apply the playbook's apply-fix flow | high | inconclusive | no | FailedResolvedTarget matches job-reported selector verbatim; but `RecoveryInfo=null`, `InferredRecoveryInfo=null`, `RecoverySuccessful=false`, `ConsumedReason='RecoveryFailed'`, no `healing-fixes.json`; all 13 alternative-target analyzers returned 0 detections | Playbook's interactive apply-fix path cannot run — no recovered selector exists; investigation continued to find why HA had nothing to recover toward |
| H2 | Locale/geo redirect at the doodles.google host served Google.ro homepage instead of the Doodles archive | medium | eliminated | no | TO.xaml shows `TargetApp.Url='https://www.google.com/'` and zero navigation activities in the project — the workflow never asks the browser to visit doodles.google, so a redirect at that host cannot be the cause | n/a |
| H3 | Drawer was collapsed; workflow lacks a preceding activity to open it | medium | pending | no | Not pursued — H5's verified evidence shows the live page is not the Doodles archive at all, so a collapsed drawer on the archive page is moot | n/a |
| H4 | Page had not finished rendering the drawer by fault time | low | pending | no | Not pursued — same reason as H3; live page is the wrong page, not a mid-load correct page | n/a |
| H5 | NApplicationCard "Edge Google" attached to a pre-existing Google homepage tab via `AttachMode=ByInstance`; no navigation to doodles.google ever performed | medium | confirmed | yes | All four wrong-page-scope criteria pass: `TargetApp.Url='https://www.google.com/'` ≠ `Target.BrowserURL='doodles.google'`, `AttachMode='ByInstance'`, zero navigation activities in any NApplicationCard project-wide, closest matches 10/10 Google.ro homepage chrome (Romanian, classes `gb_*`/`pHiOh`/`w5hRs`) with zero `glue-*` candidates; depth-check verified | Apply one of three branches above (insert navigation activity / repoint TargetApp.Url + tighten title / change AttachMode), then restart job |

---

**Post-presentation actions**

**Action 1 — Apply Healing Agent recovered selector — BLOCKED.** Healing Agent ran but produced no recovered selector (`RecoverySuccessful=false`, `ConsumedReason='RecoveryFailed'`, no `healing-fixes.json`). There is nothing to apply because the live page never contained the target element. This is a property of the run, not a tester gap — the underlying defect is wrong-page-scope, not selector drift. Surfacing per presenter instruction; proceeding to Action 2.

**Action 2 — Apply wrong-page-scope fix to TO.xaml.** Plain-text context:

```
Defect: NApplicationCard "Edge Google" in TO.xaml attaches to a pre-existing "Google"-titled Edge tab via AttachMode=ByInstance and never navigates to doodles.google. The failing Click runs against whatever page that tab happens to show (in this run: the Google.ro homepage), where the glue-drawer-2465973 / "Creating a Doodle" link does not exist.

Project: 
Workflow file: TO.xaml
Parent scope: NApplicationCard "Edge Google"
Failing activity: Click "Creating a Doodle" (NClick_1)

Current parent-scope configuration:
  TargetApp.Url       = 'https://www.google.com/'
  TargetApp.Selector  = <html app='msedge.exe' title='Google' />
  AttachMode          = 'ByInstance'
  Navigation activities inside the card before the Click: 0

Failing selector (correct against the Doodles archive, wrong page at runtime):
  <webctrl aaname='                   Creating a Doodle                 '
           class='glue-header__link'
           parentid='glue-drawer-2465973'
           tag='A' />

Three available remediation branches (apply ONE):
  A) Insert a "Go To URL" activity inside NApplicationCard "Edge Google" before the failing Click, targeting the Doodles archive URL (e.g., https://doodles.google/ or the specific archive page that hosts glue-drawer-2465973).
  B) Repoint TargetApp.Url to the Doodles archive URL AND tighten TargetApp.Selector title to match the Doodles archive page title (not the generic 'Google').
  C) Change AttachMode from 'ByInstance' to a mode that opens/navigates (e.g., 'OpenIfNotRunning') AND set TargetApp.Url to the Doodles archive URL.

After the change, validate with:
  uip rpa get-errors --file-path "" --output json
```

**Warning:** Healing Agent was enabled on this run but could not produce a recovered selector — the live page never contained the target element, so there is no HA suggestion to apply. The fix must be made at the parent scope (NApplicationCard "Edge Google") in TO.xaml, not on the Click's selector. Enabling Healing Agent does not fix wrong-page-scope defects.
