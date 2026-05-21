---
confidence: high
---

# Disabled Element — AlterIfDisabled Not Enabled

## Context

A UI Automation Next interaction activity located its target element, but the element's `disabled` property/attribute was set, and the activity's `AlterIfDisabled` property was not `True`. The driver aborts the operation rather than acting on a disabled element.

Applies to every UIAutomationNext interaction activity that exposes `AlterIfDisabled`:

- `NClick`
- `NTypeInto`
- `NSetText`
- `NCheck`
- `NSelectItem`
- `NSAPClickPictureOnScreen`

What this looks like:

- Exception class: `UiPath.UIAutomationNext.Exceptions.UiNodeDisabledElementException`
- Friendly message: `The target element is disabled. Operation canceled.`
- HRESULT: `0x8004027D` (`E_UINODE_CANNOT_ALTER_DISABLED_ELEM`)
- Stack origin: `UiInputService.<Click|Type|SetText|Check|Select>Async` → `DriverServiceCore.WrapComAsync` → `ExceptionExtensions.ThrowFriendly`
- Activity duration is short (sub-second to a few seconds) — the failure is NOT a timeout. The element was found, then rejected.
- Selector resolved successfully (no `NodeNotFoundException` / `SelectorNotFoundException` in the same trace).

This exception is specifically about the target element's own disabled property. A page overlay that *covers* the element produces a different error (click-intercepted / not-interactable / timeout), not this one. If the agent is tempted to infer "an overlay disabled the button," verify against the Healing Agent data — without HA popup evidence, that inference is unsupported.

What to look for:

- Confirm the exception class is `UiNodeDisabledElementException`. If the exception is `SelectorNotFoundException`, `UiElementNotFoundException`, `NodeNotFoundException`, or `TimeoutException` → use the matching `selector-failure-*.md` or `timeout-issue.md` playbook instead. The element being found is the entry condition for this playbook.
- Identify the faulting activity name and its parent container (`NApplicationCard`, `Use Browser`, `Attach Window`). The `AlterIfDisabled` setting lives on the leaf activity, not the container.
- Inspect the `InputMode` (or `Input Method`) of the leaf activity. If it is `HardwareEvents`, `AlterIfDisabled` is inert — see Resolution.
- Inspect any Healing Agent recovery data on the job for popup detections.

## Investigation

1. From the failed job, capture the exception class, friendly message, activity name, and workflow file (e.g., `ClickCase.xaml` → `NClick "Click 'Submit'"`).
2. Open the workflow source and locate the failing activity by its name or `IdRef`.
3. Read the activity's `AlterIfDisabled` property. Default is unset (`null`), which the driver treats as `false`.
4. Read the activity's `Input Mode` (Selector, Image, Hardware Events, Background, Native, Driver). Note whether it is `HardwareEvents`.
5. Check whether Healing Agent ran on this job, and in which mode (self-healing vs. recommendation-only). See [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md).
6. If HA ran, check whether it detected a popup or external interference covering the target:
   - Self-healing mode: look at `RecoveryInfo[].RecoveredExternally.Recoveries[]` and the run-level `RecoverySuccessful` / `ConsumedReason`.
   - Recommendation-only mode: look at `InferredRecoveryInfo` and `AnalysisResult[].AnalysisInformation` for popup detections.
7. Read the activity's `Target` selector and the parent scope's `TargetApp.Url` to record what page the activity ran against.

## Resolution

### Decision tree

Walk this tree from the top. Stop at the first branch that matches.

1. **Is the leaf activity's `Input Mode` (or inherited mode) `HardwareEvents`?**
   - YES → branch (A) below. `AlterIfDisabled` is inert in Hardware Events.
   - NO → continue.

2. **Did Healing Agent run on this job AND detect a popup / external interference that it could not clear?**
   - HA self-healing mode AND popup was detected AND HA's dismiss attempt failed (`RecoverySuccessful = false`, popup still blocked the click) → branch (B).
   - HA recommendation-only mode AND popup was detected in `InferredRecoveryInfo` / `AnalysisResult` (HA only inferred, did not attempt dismissal) → branch (C).
   - HA did not run, OR HA ran and found no popup, OR HA ran and successfully cleared the popup (in which case the job would not have faulted with this exception) → continue.

3. **Default (no HardwareEvents quirk, no HA-detected blocking popup) → branch (D):** Set `AlterIfDisabled = True` on the failing activity.

### Branches

- **(A) `Input Mode = HardwareEvents`:** `AlterIfDisabled` cannot help — the property does not apply to Hardware Events. Switch `Input Mode` to a driver-based mode that supports `AlterIfDisabled` (`Selector`, `Default`, `Driver`, `ChromiumAPI` where supported by the target tech), then apply branch (D). Do not leave the workflow as Hardware Events + disabled target — the click lands at the screen coordinate but the application ignores it, producing silent failures downstream rather than a typed exception.

- **(B) HA self-healing tried to dismiss a popup and failed:** The popup is the originating blocker. Do NOT set `AlterIfDisabled = True` — forcing the click would land on the popup, not the intended target. Fix the popup: inspect `RecoveryInfo[].RecoveredExternally.Recoveries[]` for the `ClickTarget` HA attempted and why it failed (popup not present in DOM, dismiss selector stale, popup re-appears after dismiss). Add a deterministic dismissal step to the workflow before the failing activity — typically a Click on the popup's actual close button, or apply the fix via Studio Desktop Recovery Panel.

- **(C) HA recommendation-only detected a popup:** HA inferred a popup over the target but did not attempt to dismiss it (recommendation-only mode). Do NOT set `AlterIfDisabled = True`. Surface the popup to the user (per [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md) presentation rules) and apply HA's `dismiss-popup` fix from `healing-fixes.json` via Studio Desktop Recovery Panel — or, if no fix entry exists, add a Click activity targeting the popup's dismiss button before the failing activity.

- **(D) Default — set `AlterIfDisabled = True` on the failing activity:** The element's `disabled` property is the abort cause and no popup is blocking the target. Add or update `AlterIfDisabled="True"` on the leaf activity's XAML element (or via Studio's Properties panel). Verify `Input Mode` is not `HardwareEvents` (branch A handles that). Acceptable input modes for this fix: `Selector`, `Default`, `Driver`, `ChromiumAPI`.

  This is the right fix for the broad case where the target's `disabled` attribute is set at click time — whether the disable is permanent (read-only field, advisory control), part of the normal UI lifecycle (button enables only on form-valid), or because an upstream step did not run. In all of those, `AlterIfDisabled = True` instructs the driver to act on the element as found, which is what the exception is asking for.

  Optional preventive add-ons (in addition to setting `AlterIfDisabled = True`):
  - If the disable is from a missing upstream step (e.g., the workflow forgot to type a query into a search box before clicking a dependent button), add that upstream step. `AlterIfDisabled = True` still belongs on the leaf as a defense-in-depth — it removes the abort even if the upstream step degrades.
  - If the workflow is sensitive to UI-version drift, keep Healing Agent enabled so future popup interferences get captured.
