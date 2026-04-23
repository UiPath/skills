# Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill flow) — before advancing to the next state. Interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use `uia interact` or `servo` to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, these commands are ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

## Advancing UI State — Two Options

After registering an element in the Object Repository, you often need to interact with it to reveal the next screen's elements. Two CLIs can drive the interaction; prefer `uia interact` when you are already in a UIA capture loop.

### Preferred: `uia interact` (UIA-native, reuses the UIA snapshot)

`uia interact` commands take element refs from the UIA snapshot (the same `eN` refs produced by the UIA snapshot-filter CLI). Staying in the UIA ref system avoids the cross-snapshot ref confusion that servo introduces.

Use `uia interact` when the UIA snapshot is already loaded (for example, immediately after a `uia-configure-target` capture of the current screen), so the `eN` refs are still valid.

Command syntax and caveats: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md` § Interact.

### Fallback: `servo`

Use `servo` when you don't have a current UIA snapshot, or when interacting with elements outside the UIA tree (native Windows chrome, OS dialogs, etc.).

> **WARNING: Servo refs and UIA snapshot refs are independent numbering systems.** Element `e42` from a UIA snapshot is NOT the same as `e42` from a servo snapshot. Always refresh servo's own ref map (`servo snapshot <window-ref>`) before using any servo interaction command. Never reuse refs from UIA snapshots in servo commands (or vice versa).

Command syntax: see the `servo` skill.

## Multi-Step Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to OR registration for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state — prefer `uia interact` using the `eN` ref from the UIA snapshot that was just captured; fall back to `servo` (with its own `servo snapshot`-specific refs) when the UIA snapshot isn't current or the element sits outside the UIA tree.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill flow).
4. **Repeat** until all workflow targets are registered in the OR.

**Do NOT use `uip rpa run-file` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. Both `uia interact` and `servo` are stateless: they perform one action and leave the app in the resulting state.

## Multi-Screen Workflows

For XAML workflows that span multiple screens, use the parallel authoring pipeline: one write agent per screen, chained in order. The screen boundary for each write agent aligns with the Complete-then-advance rule above — everything configured before the next `uia interact` / `servo` advance belongs to one write agent's scope.

Single-screen workflows skip the pipeline: build the full workflow in one pass using all the collected OR references.

See [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md) for the full pipeline (scaffolding agent, chained screen agents, OR reference handoff, task structure, and prompt templates).

See also: [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the `uia-configure-target` skill policy and indication fallback routing.
