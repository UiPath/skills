# Final Resolution — No Healing Agent Recovery Data

**Root cause:** Authoring-time selector typo in the NClick activity `Click 'Simt că am noroc'` in `Google.xaml`. The `aria-label` contains 10 spurious trailing `c` characters (`Simt că am noroccccccccccc`), so the strict selector matched no element on the live page. Healing Agent did not auto-recover because the run is an **Attended StudioPro** execution, which is **not HA-eligible** per UiPath documentation — HA runs only for Orchestrator-scheduled jobs.

## What went wrong

Job `bad89b79-48c4-49ef-9de3-513df72ab69f` (id `4014101`, process `ERN`, folder `Shared`) faulted with `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException`. The NClick selector searched for aria-label `Simt că am noroccccccccccc` while the live button exposes aria-label `Simt că am noroc` (94% match, identical `css-selector`, `tag`, `type`).

`AutopilotForRobots.HealingEnabled=true` is set at the process level, but the runtime eligibility gate (run type) filtered this execution out. HA produced no artifacts; `uip or jobs healing-data <jobKey>` returned a 22-byte empty ZIP on two consecutive invocations.

## Evidence

- **Activity:** NClick `Click 'Simt că am noroc'` in `Google.xaml` (inside NApplicationCard `Edge Google`).
- **Failed selector:** `<webctrl aria-label='Simt că am noroccccccccccc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`.
- **Closest live match (94%):** `<webctrl aria-label='Simt că am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit'/>`.
- **Run type:** `Type=Attended, RuntimeType=StudioPro, Source=Agent`. Machine `MOCK-HOST`.
- **HA export:** empty 22-byte ZIP, 0 files — no `healing-fixes.json`, no `uia/*.json`, no `recovery-data-summary.json`.
- **UiPath docs (`uip docsai`):** "Healing Agent is currently only available for processes executed as jobs. Healing Agent is not available for other types of jobs, such as triggers or test cases." Attended StudioPro runs are not Orchestrator jobs, so HA does not execute.

## Matched playbooks

- `references/activity-packages/ui-automation/playbooks/selector-failure-manual.md` (confirmed root cause — manual remediation path)
- `references/activity-packages/ui-automation/playbooks/no-recovery-data.md` (confirms HA-ineligibility explanation)

## Immediate fix

1. Correct the NClick target aria-label in `Google.xaml`: replace `Simt că am noroccccccccccc` with `Simt că am noroc`.

## Preventive fix

1. Replace the brittle long-aria-label match with a stabler attribute (`automationid`/`role`/`name`) or wildcard tolerance — the current selector is fragile to typos and localization changes.
2. No Orchestrator-side change can enable HA for attended StudioPro runs; HA exclusion of attended runs is by design. Future unattended Orchestrator-scheduled executions of the same process will produce HA artifacts because `AutopilotForRobots.HealingEnabled=true` is already correct.
