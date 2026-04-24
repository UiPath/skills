# Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill flow) — before advancing to the next state. Interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use the `uia interact` CLI to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, these commands are ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

## Advancing UI State

After registering an element in the Object Repository, interact with it (or a sibling element) to reveal the next screen via the `uia interact` CLI. See the skill at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md`.

**Reuse refs from the current `uia-configure-target` capture — do not re-inspect.** `uia interact` resolves element refs against the most recent snapshot in memory regardless of which CLI wrote it (the two write to different folders, but the snapshot is shared). Pass the same e-refs (`e28`, `e35`, etc.) directly to `uia interact click`/`type`/`select`. Running `snapshot inspect` just to re-mint refs for an unchanged UI is wasted work — the refs you have are still live.

Re-inspect (or re-run `snapshot capture`) only when the UI has actually advanced since the last capture; refs from a pre-advance snapshot will not resolve against the new state.

## Multi-Step Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to OR registration for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state via the `uia interact` CLI.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill flow).
4. **Repeat** until all workflow targets are registered in the OR.

**Do NOT use `uip rpa run-file` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. The `uia interact` CLI is stateless: it performs one action and leaves the app in the resulting state.

## Multi-Screen Workflows

For XAML workflows that span multiple capture screens, add each screen's activities to the workflow as its targets are registered. Each batch aligns with the Complete-then-advance rule above: everything configured before the next `uia interact` CLI advance belongs to one batch. Validate with `get-errors` after each batch to catch issues early.

See also: [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the `uia-configure-target` skill policy and indication fallback routing.
