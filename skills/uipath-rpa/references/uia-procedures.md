# UI Automation Procedures

Runtime procedures for UI automation workflows: prerequisites, debug sessions, multi-step flows, and selector recovery.

## Prerequisites

**Required package:** `UiPath.UIAutomation.Activities`

The `uip rpa uia` subcommands (snapshot, selector-intelligence, object-repository) used by `uia-configure-target` require **`UiPath.UIAutomation.Activities` >= 26.3.1-beta.11555873**. Before configuring any target, check the installed version in `project.json` under `dependencies`.

If the installed version is below the minimum, ask the user whether to upgrade:

```bash
uip rpa get-versions --package-id UiPath.UIAutomation.Activities --project-dir "$PROJECT_DIR" --output json --use-studio

# If user approves the upgrade:
uip rpa install-or-update-packages --packages '[{"id": "UiPath.UIAutomation.Activities", "version": "26.3.1-beta.11555873"}]' --project-dir "$PROJECT_DIR" --output json --use-studio
```

If the user declines, warn that `uip rpa uia` commands will fail and fall back to the indication tools (see [uia-configure-target-guide.md](uia-configure-target-guide.md) for fallback commands).

---

## Running UI Automation Workflows (Debug Sessions)

**Always use `--command StartDebugging`** (not `StartExecution`) when running workflows with UI automation. A debug session pauses on error instead of tearing down the application, leaving the UI state available for inspection.

**Every debug run** must follow this procedure to prevent stale windows from accumulating or being reused in a dirty state:

1. **Record the window baseline:**
   ```bash
   servo targets
   ```
   Note which windows (w-refs and titles) are already present.
2. **Run the workflow:**
   ```bash
   uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command StartDebugging --output json --use-studio
   ```
3. **When done** (success or failure) — **stop the debug session:**
   ```bash
   uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command Stop --output json --use-studio
   ```
4. **List windows again:**
   ```bash
   servo targets
   ```
5. **Diff before vs after.** Any window present now that was NOT in the baseline was opened by the workflow. Close it:
   ```bash
   servo window <w-ref> Close
   ```

Skipping steps 4-5 causes the next run's open-if-not-open behavior to reuse a stale window in whatever state it was left in, or -- if the selector doesn't match -- to spawn a duplicate instance.

If a selector error occurs during the debug run, see [Runtime Selector Failure Recovery](#runtime-selector-failure-recovery) below.

---

## Multi-Step UI Flows

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

See also: [uia-configure-target-guide.md](uia-configure-target-guide.md) for the `uia-configure-target` skill details and indication fallback commands.

---

## Runtime Selector Failure Recovery

"UI element not found", "UI element is invalid", element not on screen -- these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes.

When a workflow fails at runtime with a selector error:

1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Identify the failing element** -- read the error to find which descriptor/element failed.
3. **Read the window selector** -- from the Object Repository files, find the screen's selector that scopes the failing element.
4. **Run the `uia-improve-selector` skill in recover mode** by spawning a subagent with the Agent tool. The prompt must include: the `uia-improve-selector` SKILL.md path (find it under the UIA activity-docs skills folder), the project folder, `--mode recover`, `--window <windowSelector>`, and `--partial <failingPartialSelector>`. The subagent reads the skill, re-analyzes the live DOM in its current state, and returns a corrected selector.
5. **Update the OR element** with the recovered selector.
6. **Clean up and re-run** -- follow the [Running UI Automation Workflows](#running-ui-automation-workflows-debug-sessions) procedure (stop, diff, close leaked windows, re-run).

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.
