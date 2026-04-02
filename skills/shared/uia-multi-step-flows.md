# Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill through TARGET-8) — before using servo to advance to the next state. Servo interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use servo to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, servo is ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

> **WARNING: Servo refs and UIA snapshot refs are independent numbering systems.** Element `e42` from `uip rpa uia snapshot filter` is NOT the same as `e42` from `servo snapshot`. Always run `servo snapshot <window-ref>` to get servo-specific refs before using `servo click`/`servo type`. Never reuse refs from UIA snapshots in servo commands.

Use the `servo` CLI to interact with already-configured targets and advance the UI, then run `uia-configure-target` again for the newly visible elements:

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to TARGET-8 (OR registration) for each element. Do not stop after getting a raw selector.
2. **Advance the UI** using servo to move to the next state (e.g., click a button to open a form):
   ```bash
   # List targets to find the window/tab
   servo targets
   # Take a SERVO snapshot to get servo-specific element refs
   servo snapshot <window-or-tab-ref>
   # Click to advance UI state (use servo refs, NOT UIA refs)
   servo click <servo-element-ref>
   ```
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill through TARGET-8).
4. **Repeat** until all workflow targets are registered in the OR.

**Do NOT use `uip rpa run-file` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. Servo is stateless: it clicks/types and leaves the app in the resulting state.

After all targets are captured, build the full workflow in one pass using all the collected OR references.

See also: [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the `uia-configure-target` skill details and indication fallback commands.
