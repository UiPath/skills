# Final Resolution

Root Cause: `AlterIfDisabled` not set to `True` on `NClick "Click 'Simt că am noroc(1)'"` in `ClickCase.xaml`. The driver located the target element, the element's own `disabled` property/attribute was set, and with `AlterIfDisabled` absent (driver treats as `false`) the driver aborted with `UiNodeDisabledElementException`. Healing Agent was disabled on this job (`Enabled=false`, `HealingEnabled=false`), so no popup detection was available to override the default fix. Per the disabled-element playbook decision tree, this is branch (D) — the default — and the correct fix is to set `AlterIfDisabled = True`.

What went wrong: The UI Automation Next driver resolved the selector for the "Simt că am noroc" ("I'm Feeling Lucky") button on Google Search, confirmed the leaf element's `disabled` property was set, and aborted the click rather than acting on a disabled element. The failure is property-level on the target itself, not a selector miss, not a timeout, and not an overlay covering the element (an overlay would have produced a click-intercepted / not-interactable error, not `UiNodeDisabledElementException`).

Why: `ClickCase.xaml`'s leaf `NClick` has no `AlterIfDisabled` attribute (defaults to `false`). The parent `NApplicationCard "Edge Google"` uses `InteractionMode = DebuggerApi` and the `NClick` inherits via `SameAsCard` — so the input mode honors `AlterIfDisabled` (branch A — HardwareEvents — is eliminated). Healing Agent was disabled on the job, so there is no HA popup detection that would shift this to branch (B) or branch (C). Default rule applies: set `AlterIfDisabled = True`. Cross-run consistency (all 6 faulted ERN jobs fault at the same activity) is consistent with a deterministic property-level abort, not a transient race.

Branch discrimination per `references/activity-packages/ui-automation/playbooks/disabled-element.md`:
- (A) `Input Mode = HardwareEvents` — ELIMINATED. Card uses `DebuggerApi`, which honors `AlterIfDisabled`.
- (B) HA self-healing detected popup and failed to dismiss — ELIMINATED. HA was disabled on this job.
- (C) HA recommendation-only inferred popup — ELIMINATED. HA was disabled on this job.
- (D) Default — set `AlterIfDisabled = True` — APPLIES.

Evidence:

### UI Automation (Root Cause)
- Failing activity: `NClick "Click 'Simt că am noroc(1)'"` (`IdRef=NClick_1`) in `ClickCase.xaml`, inside `NApplicationCard "Edge Google"`, inside Sequence "ClickCase".
- Exception: `UiPath.UIAutomationNext.Exceptions.UiNodeDisabledElementException`, friendly message "The target element is disabled. Operation canceled.", HRESULT `0x8004027D` (`E_UINODE_CANNOT_ALTER_DISABLED_ELEM`).
- Stack origin: `UiInputService.ClickAsync` → `DriverServiceCore.WrapComAsync` → `ExceptionExtensions.ThrowFriendly`.
- Failed activity properties (verbatim from `ClickCase.xaml`):
  - `AlterIfDisabled` attribute absent on the `NClick` element — defaults to `false`.
  - `InteractionMode="SameAsCard"` on the `NClick`, inheriting from parent `NApplicationCard InteractionMode="DebuggerApi"`. Not `HardwareEvents`, so `AlterIfDisabled` would be effective if set.
  - Target selector: `<webctrl aria-label='Simt că am noroc' css-selector='body>div>div>form>div>div>div>center>input' tag='INPUT' type='submit' />`.
  - Activity `Timeout = 3` seconds, `Version = V5`, `VerifyOptions.Mode = Appears`.
- Parent `NApplicationCard "Edge Google"` configuration: `AttachMode = ByInstance`, `InteractionMode = DebuggerApi`, `TargetApp.Url = https://www.google.com/`, `BrowserType = Edge`.
- Job duration ≈ 4.7 s (start 2026-05-21T09:24:58.130Z, end 2026-05-21T09:25:02.813Z) — element was found and then rejected on its `disabled` property, not a timeout.
- Selector resolved successfully (no `NodeNotFoundException` / `SelectorNotFoundException` in trace).
- Healing Agent telemetry: `Enabled=false`, `HealingEnabled=false`. No `RecoveryInfo`, no `InferredRecoveryInfo`, no `healing-fixes.json`, no popup detection. Branches (B) and (C) of the playbook do not apply.
- Cross-run consistency: 6 faulted ERN jobs in folder `Shared` share the same failure signature at the same `NClick` — deterministic property-level abort.

### Orchestrator (Propagation)
- Process `ERN`, release version 20324882, entry point `ClickCase.xaml`.
- Job `49655b57-ad0a-410c-8256-38c215f9246d` in folder `Shared` (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`, Type=Standard), host machine `MOCK-HOST`, runtime StudioPro, Source=Agent, Type=Attended.
- Job state: Faulted; Orchestrator surfaced the activity-level `UiNodeDisabledElementException` as a faulted job. No Orchestrator-side misconfiguration.

Immediate fix:

### UI Automation (Root Cause)
1. Set `AlterIfDisabled = True` on `NClick "Click 'Simt că am noroc(1)'"` in `ClickCase.xaml`.
   - Why: The leaf element's `disabled` property is the abort cause. `InputMode` honors `AlterIfDisabled` (`DebuggerApi`, not `HardwareEvents`). Healing Agent was disabled, so there is no popup detection that would override the default. The playbook's branch (D) directly prescribes this.
   - Where: `ClickCase.xaml` — `NClick` element `IdRef=NClick_1`; add `AlterIfDisabled="True"` as an XAML attribute, or set via Studio's Properties panel.
   - Who: RPA developer.
   - Source: `references/activity-packages/ui-automation/playbooks/disabled-element.md` § Resolution → branch (D).

After applying the fix, validate the workflow: `uip rpa get-errors --file-path "ClickCase.xaml" --output json`.

### Orchestrator (Propagation)
1. Restart the job from Orchestrator after the `ClickCase.xaml` fix is published.
   - Why: Faulted jobs must be restarted manually — Orchestrator does not auto-retry process-level faults.
   - Where: Orchestrator → Jobs → locate process `ERN` job (key `49655b57-ad0a-410c-8256-38c215f9246d`) → More Actions → Restart. Or republish `ERN` to a new version and trigger a fresh run.
   - Who: Process owner / RPA developer.

Preventive fix:

1. UI Automation — enable Healing Agent on the ERN process so future failures capture popup detections and UI tree snapshots.
   - Why: HA was disabled on this run, which is why branches (B) and (C) of the playbook could not be evaluated. With HA enabled, any future failure caused by a covering popup would be surfaced explicitly rather than defaulting to branch (D).
   - Where: Orchestrator → Tenant / Folder → Process ERN → Autopilot / Healing settings.
   - Who: Admin / process owner.
   - Source: `references/activity-packages/ui-automation/playbooks/disabled-element.md` § Investigation step 5–6.

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `NClick "Click 'Simt că am noroc(1)'"` faulted with `UiNodeDisabledElementException` because the target element's `disabled` property was set and `AlterIfDisabled` was not `True`. Branch discriminated by checking `InputMode` and Healing Agent popup detection. | high | confirmed | yes | Exact signature match for the playbook (exception class, friendly message, stack, sub-5s duration, selector resolved). `AlterIfDisabled` attribute absent on the `NClick`; `InteractionMode=DebuggerApi` (not HardwareEvents → branch A eliminated); Healing Agent disabled, no popup detection (branches B/C eliminated). | Branch (D) — set `AlterIfDisabled = True` on `NClick_1` in `ClickCase.xaml`. |
