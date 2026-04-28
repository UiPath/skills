# Runtime Selector Failure Recovery

"UI element not found", "UI element is invalid", element not on screen -- these surface at runtime, not during static validation. They occur when a selector was captured against one app state but the DOM changed by the time the activity executes.

When a workflow fails at runtime with a selector error:

1. **The app is already in the right state.** The debug session paused at the failing activity, so the app's current DOM reflects the state that activity needs to target.
2. **Identify the failing element** -- read the error to find which descriptor/element failed.
3. **Read the window selector** -- from the Object Repository files, find the screen's selector that scopes the failing element.
4. **Stage selector recovery.** Read `<PROJECT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-improve-selector/USAGE.md`, choose the recover-mode invocation form for this context, and run its staging CLI command exactly as documented.
5. **Improve the staged selector.** Run the `uia-improve-selector` recover-mode instructions against the staged folder. If the current coding environment supports delegated worker sessions, you may delegate only this staged-folder improvement step; otherwise execute the same recover-mode instructions inline in the current session.
6. **Write back the recovered selector.** Run the write-back CLI command from the same invocation form to persist the recovered selector into the Object Repository.
7. **Clean up and re-run** -- follow the [Running UI Automation Workflows](uia-debug-workflow.md) procedure (stop, diff, close leaked windows, re-run).

The required contract is **stage from the paused debug state -> improve the staged selector -> write back through the documented CLI**. Do not hand-edit selector strings or Object Repository files directly.

Repeat until the workflow completes successfully. Each failure advances the app to the next problematic state, making recovery self-correcting.
