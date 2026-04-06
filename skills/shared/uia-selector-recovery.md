# Runtime Selector Failure Recovery

"UI element not found", "UI element is invalid", element not on screen -- these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes.

When a workflow fails at runtime with a selector error:

1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Identify the failing element** -- read the error to find which descriptor/element failed.
3. **Read the window selector** -- from the Object Repository files, find the screen's selector that scopes the failing element.
4. **Run the `uia-improve-selector` skill in recover mode** by spawning a subagent with the Agent tool. The prompt must include: the `uia-improve-selector` SKILL.md path (find it under the UIA activity-docs skills folder), the project folder, `--mode recover`, `--window <windowSelector>`, and `--partial <failingPartialSelector>`. The subagent reads the skill, re-analyzes the live DOM in its current state, and returns a corrected selector.
5. **Update the OR element** with the recovered selector.
6. **Clean up and re-run** -- follow the [Running UI Automation Workflows](uia-debug-workflow.md) procedure (stop, diff, close leaked windows, re-run).

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.
