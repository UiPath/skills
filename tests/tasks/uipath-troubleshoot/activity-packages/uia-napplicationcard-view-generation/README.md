# UIAutomationNext NApplicationCard — Could Not Generate View (Design-Time)

Design-time (Studio) troubleshooting scenario for
`UiPath.UIAutomationNext.Activities.NApplicationCard` (the modern Use Application/Browser container).

## What this scenario exercises

Studio cannot render the `Use Application/Browser` card on the design surface — the Output panel shows
`Could not generate view for NApplicationCard` + `Object reference not set to an instance of an object`.
The agent must recognize this as a **Studio ↔ activity-package version skew + corrupted/stale cache**
problem (a design-time rendering fault, not a robot job fault, and not corrupt XAML), and prescribe
aligning the package version and clearing caches.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` with a `Use Browser` `NApplicationCard`; `project.json` pins `UiPath.UIAutomation.Activities [24.10.12]` against an older `studioVersion 23.10.4.0`; a stale `obj/project.assets.json` restored against yet-older `22.10.7` — cache drift |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` — no job/trace exists for a design-time error |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the Studio/package version skew + stale cache and the fix (align
  `UiPath.UIAutomation.Activities` to the Studio/runtime version, clear `%LOCALAPPDATA%\UiPath\.cache`
  and the project `.local`/`bin`/`obj`, reopen — do NOT hand-edit the `.xaml`).

Playbook: `references/activity-packages/ui-automation/playbooks/napplicationcard-view-generation-failed.md`.
