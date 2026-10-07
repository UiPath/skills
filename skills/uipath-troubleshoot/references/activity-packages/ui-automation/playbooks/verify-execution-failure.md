---
confidence: high
---

# Verify Execution Failure — Post-Action Assertion Did Not Hold

## Context

A UI Automation Next interaction activity completed its primary action successfully, but its `VerifyOptions` post-condition check did not hold within the verify `Timeout`. The driver throws `VerifyActivityExecutionException`. The action's side effects are NOT rolled back — the click already clicked, the hover already hovered, the keystrokes were already sent — and with `Retry` on (the default) each failed check ran the action again, so they may have happened several times.

Applies to every UIAutomationNext activity that exposes `VerifyOptions`:

- `NClick`
- `NHover`
- `NKeyboardShortcuts`
- `NTypeInto`

This playbook covers the general assertion failure cases (wrong verify target, wrong mode, timeout too short, post-recovery verify failure, action had no visible effect). It does NOT cover `NTypeInto`-specific text-mismatch sub-cases (password fields, special-keys delivery, expected-vs-actual text mismatch, input-disappeared-mid-type) — those have their own friendly-message keys and a separate playbook.

What this looks like:

- Exception class: `UiPath.UIAutomationNext.Exceptions.VerifyActivityExecutionException`
- Friendly message (generic, this playbook's target): `The element was found but the verification failed because the action did not have the expected outcome.` (resource key `ExceptionCheckActivity`)
- Other friendly messages this playbook handles:
  - `The verification failed because the verification target is invalid or not found.` (`ExceptionVerificationTargetNotFoundOrInvalid`)
  - `The verification failed because the verification target image could not be retrieved.` (`ExceptionVerificationImageCouldNotBeRetrieved`)
  - `The verification failed because the verification target does not support text attribute.` (`ExceptionVerificationTextNotSupported`)
  - `The activity execution was recovered by Autopilot, but the verification configured on the activity failed.` (`ExceptionRecoveredButValidationFailed`)
- Stack origin: `VerifyExecutionService.ExecuteWithVerifyInternalAsync` → `ExecuteWithVerifyAsync` → `<Activity>.ExecuteAsync`
- Fault duration follows `Retry`. Each check waits up to the verify `Timeout` (default 10s). With `Retry` off, or once the acted-on element is gone, the first failed check throws: about one verify `Timeout`. With `Retry` on (default), `VerifyExecutionService` re-runs the whole activity — action and check — until the activity's own `Timeout` (default 30s) has elapsed: about the activity `Timeout`, up to one verify `Timeout` more.
- The action itself succeeded — there is NO `NodeNotFoundException` / `SelectorNotFoundException` / `UiNodeDisabledElementException` in the same trace for the failing activity.

What can cause it:

- Verify target selector points at the wrong element, an over-specific element, or an element that only sometimes appears
- Verify mode (`Appears` / `Disappears` / `TextChanges` / `AspectChanges`) is wrong for the outcome the action actually produces
- Verify timeout is shorter than how long the asserted state takes to settle (slow page, animation, async navigation)
- The action's effect is non-deterministic (e.g., a "random result" / "surprise me" style action whose destination varies by run), and the verify target presumes a deterministic outcome
- Autopilot recovery healed the action via an alternate path, and the asserted post-condition is no longer reachable from the recovered state
- The action landed but had no UI effect (overlay swallowed the click, focus lost between activities, element re-rendered)

What to look for:

- Confirm the exception class is `VerifyActivityExecutionException`. If it is anything else, this playbook does not apply.
- Confirm the friendly message is one of the keys listed above. If it is `ExceptionCheckActivityPassword`, `ExceptionCheckActivityTypeInto`, `ExceptionCheckActivityTypeIntoWithSpecialKeys`, or `ExceptionCheckActivityTypeIntoInputDisappeared`, use the (planned) `verify-execution-typeinto.md` playbook instead — those are NTypeInto text-match failures with different fixes.
- Identify the faulting activity name and its workflow file (e.g., `ClickCase.xaml` → `NClick "Click 'Submit'"`).
- The `VerifyOptions` configuration (Target selector, Mode, Timeout, Retry) is **NOT in job logs or traces** — only in the workflow source. This investigation is **source-required**.

## Investigation

1. From the failed job, capture the exception class, friendly message, faulting activity, and workflow file.
2. Open the workflow source. Locate the failing activity by name or `IdRef`. Read its full `VerifyOptions` block:
   - `Mode` (`Appears` / `Disappears` / `TextChanges` / `AspectChanges`)
   - `Target` — the full selector and any anchors / scope (note the `BrowserURL`, `ScopeSelectorArgument`, `aaname`, `tag`)
   - `Timeout` — explicit value, or empty `<InArgument x:TypeArguments="x:Double" />` meaning the default (10s)
   - `Retry` — `true` / `false` / unset (default `true`)
3. Read the activity's own `Target` selector and its `InteractionMode` (separate concern, but useful context).
4. Compare the verify `Target.BrowserURL` / scope to where the action actually lands. If they differ, the action navigates somewhere — verify whether the verify target is realistically reachable from the action's landing page.
5. Check whether the asserted outcome is deterministic. If the action can produce different end states across runs (search result page, dynamic content, A/B variants), an `Appears` assertion on a specific element is fragile.
6. Compute the fault duration and read it against `Retry`. About one verify `Timeout` (`Retry` off, or the acted-on element gone after the first run): the action ran once and the check never held. About the activity `Timeout` with `Retry` on: the action ran several times and no check held — check the application for repeated effects (a second submission, text typed twice). Much shorter than one verify `Timeout`: an inner failure short-circuited (e.g., verify target selector invalid at parse time).
7. If Healing Agent ran on this job, check whether the action was *recovered* (the original target was healed) — the recovered action can resolve to a different landing page than the workflow author expected, which can make the verify target unreachable. See [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md).

## Resolution

### Decision tree

Walk this tree from the top. Stop at the first branch that matches.

1. **Is the friendly message `ExceptionVerificationTargetNotFoundOrInvalid`?**
   - YES → branch **(A)**. The verify selector itself is bad — fix the selector before doing anything else.
   - NO → continue.

2. **Is the friendly message `ExceptionVerificationTextNotSupported` or `ExceptionVerificationImageCouldNotBeRetrieved`?**
   - YES → branch **(B)**. The verify `Mode` is incompatible with the verify target's element type.
   - NO → continue.

3. **Is the friendly message `ExceptionRecoveredButValidationFailed`?**
   - YES → branch **(C)**. Autopilot healed the action; the healed path landed somewhere the verify target cannot reach.
   - NO → continue.

4. **Is the action's outcome non-deterministic** (different runs land on different pages / different DOM)?
   - YES → branch **(D)**. The verify target presumes a specific outcome that the action does not guarantee.
   - NO → continue.

5. **Did the checks run their full verify `Timeout` (fault duration, Investigation step 6) AND is the asserted state reachable but slow** (animations, async load, navigation)?
   - YES → branch **(E)**. Verify timeout is too short for the real settle time.
   - NO → continue.

6. **Default — the action ran but produced no UI effect** → branch **(F)**. Diagnose why the action did not have its intended consequence (overlay, focus, wrong target).

### Branches

- **(A) `ExceptionVerificationTargetNotFoundOrInvalid` — bad verify selector.** The `VerifyOptions.Target` failed to parse or returned no nodes. Open the verify target in Studio's Object Repository / selector editor. Fix the selector to point at a real, stable element on the post-action page. Common authoring mistakes: pointing verify at the same element as the action (which often disappears after the action); copying a stale design-time selector from a now-changed page; using a selector with a dynamic `idx=` that shifts between sessions. Do NOT remove `VerifyOptions` entirely — re-targeting is the right fix.

- **(B) `ExceptionVerificationTextNotSupported` / `ExceptionVerificationImageCouldNotBeRetrieved` — wrong `Mode` for the element type.** `TextChanges` on an element that does not expose a text attribute (image, canvas, custom non-text control) throws `TextNotSupported`. `AspectChanges` on an element whose bounding rect cannot be captured (offscreen, zero-size, hidden) throws `ImageCouldNotBeRetrieved`. Switch `Mode`:
  - For text-bearing elements: `TextChanges` or `Appears` (with a target whose text changes drive its presence)
  - For visual / image elements: `AspectChanges` with a verify target that is on-screen and has non-zero size
  - For elements that should appear or disappear post-action: `Appears` or `Disappears`
  If no mode fits the element type, re-target the verify at a different element that does support the desired mode.

- **(C) `ExceptionRecoveredButValidationFailed` — Autopilot recovered the action but verify still fails.** The recovered action landed on a path the verify target cannot reach. Two sub-options:
  - If the recovery is correct and the verify target is wrong-for-the-recovered-path: update the verify target to match where the recovered action actually lands. The original verify target was specific to the unhealed path.
  - If the recovery is wrong (healed to a different button than the intended one): treat this as a selector-failure case. Apply the Healing Agent fix from `healing-fixes.json` via Studio Desktop Recovery Panel, or update the action's primary selector so recovery is not invoked. See `selector-failure-healing-fix.md`.

- **(D) Non-deterministic action outcome — verify target is over-specific.** The action can land on different pages / DOMs across runs (search results, a randomized-destination button, dynamic feeds, A/B-tested layouts). An `Appears` assertion on a single specific element will fail whenever the action lands elsewhere. Fix one of:
  - **Loosen the verify target** to an element that is present on every reachable post-action page (a navigation bar, footer, page chrome, a meta element). Sacrifices specificity for reliability.
  - **Switch `Mode` to `AspectChanges`** on a region that is guaranteed to change after the action — verifies *something happened* without asserting *what* happened.
  - Do NOT extend the timeout — the issue is not slowness, it is non-existence on this run.
  - **Do NOT remove `VerifyOptions`** to make the exception go away. Stripping the assertion turns a noisy failure into a silent one and weakens the workflow. If no stable verify target exists across all reachable outcomes AND no region is suitable for `AspectChanges`, surface that to the workflow author as a design issue — the action's outcome cannot be asserted and the workflow needs rethinking — instead of deleting the verify block.

- **(E) Verify timeout too short for the real settle time.** The asserted state is reachable but takes longer than the verify timeout to appear/change. Increase `VerifyOptions.Timeout` above the 10s default to a value that comfortably covers worst-case settle (e.g., 15–20s for slow web navigation, 20–30s for app launches or remote workflows). Do NOT extend blindly — first confirm that the verify target *does* eventually appear when the activity is rerun with a longer timeout. If the target never appears regardless of wait, the cause is branch (D) or (F), not timeout. With `Retry` on, every check that ran out re-ran the action: check the application for repeated effects, and set `Retry` to `False` on an action whose second run changes state (submit, save, send, typing into a field that was not emptied).

- **(F) Action had no UI effect — diagnose why.** The action dispatched but the application did not respond. Common causes (investigate in this order):
  - **Click intercepted by an overlay / popup.** Inspect Healing Agent data for popup detections; add a deterministic dismiss step before the action. See [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md).
  - **Wrong element targeted.** The action's selector matched a duplicate or shadow element (off-screen iframe, hidden carousel, ARIA-hidden duplicate). Tighten the action's selector — not the verify target.
  - **`InputMode` mismatch with target tech.** `Simulate` on a non-HTML host, `HardwareEvents` on a screen region that has moved, `ChromiumAPI` on a non-Chromium frame. The action lands at the OS layer but the application's event handler never fires. Switch `InputMode` to match the target tech.
  - **Focus lost between activities.** A prior activity left focus on a different app/tab. Add a Use Application / Activate step before the action.
  - **Timing — DOM not ready.** The action runs against a stale DOM (page was re-rendered between action and verify). Set `WaitForReady` = `Complete` on the action's target, or a `DelayBefore` on the action when the page re-renders after the target first appears. A Check App State before the action adds nothing: it waits for the element to appear, which the action already does.

  Once the action's actual effect is restored, the verify assertion will hold without changes.

**Applying these fixes.** Re-targeting the verify selector, changing `Mode`, raising `Timeout`, turning `Retry` off, or adding a dismiss / focus step all change the workflow `.xaml` — interactive: the troubleshooter never edits the workflow itself; on the user's approval it delegates the apply, otherwise it recommends only. Never strip `VerifyOptions` to silence the exception (see branches A and D); configure or re-target it. Any Studio Desktop Recovery Panel fix or re-publish is a user action — recommend it, do not execute.
