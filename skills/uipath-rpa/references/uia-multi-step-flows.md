# Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill through TARGET-8) — before advancing to the next state. Interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use `uia interact` or `servo` to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, these commands are ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

## Advancing UI State — Two Options

After registering an element in the Object Repository, you often need to interact with it to reveal the next screen's elements. Two CLIs can drive the interaction; prefer `uia interact` when you are already in a UIA capture loop.

### Preferred: `uia interact` (UIA-native, reuses the UIA snapshot)

`uia interact click` and `uia interact type` take an element ref from the UIA snapshot (the same `eN` refs surfaced by `uip rpa uia snapshot filter`). Staying in the UIA ref system avoids the cross-snapshot ref confusion that servo introduces.

```bash
uip rpa uia interact click <uia-element-ref>
uip rpa uia interact type <uia-element-ref> "hello"
```

Use this when the UIA snapshot is already loaded (for example, immediately after a `uia-configure-target` capture of the current screen), so the `eN` refs are still valid.

### Fallback: `servo`

Use `servo` when you don't have a current UIA snapshot, or when interacting with elements outside the UIA tree (native Windows chrome, OS dialogs, etc.).

> **WARNING: Servo refs and UIA snapshot refs are independent numbering systems.** Element `e42` from `uip rpa uia snapshot filter` is NOT the same as `e42` from `servo snapshot`. Always run `servo snapshot <window-ref>` to get servo-specific refs before using `servo click`/`servo type`. Never reuse refs from UIA snapshots in servo commands (or vice versa).

```bash
servo targets
servo snapshot <window-or-tab-ref>
servo click <servo-element-ref>
servo type <servo-element-ref> "hello"
```

## Multi-Step Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to TARGET-8 (OR registration) for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state — prefer `uip rpa uia interact click/type eN` using the `eN` ref from the UIA snapshot that was just captured; fall back to `servo click`/`servo type` (with its own `servo snapshot`-specific refs) when the UIA snapshot isn't current or the element sits outside the UIA tree.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill through TARGET-8).
4. **Repeat** until all workflow targets are registered in the OR.

**Do NOT use `uip rpa run-file` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. Both `uia interact` and `servo` are stateless: they perform one action and leave the app in the resulting state.

## Multi-Screen Workflows

For XAML workflows that span multiple screens, use the parallel authoring pipeline: one write agent per screen, chained in order. The screen boundary for each write agent aligns with the Complete-then-advance rule above — everything configured before the next `uia interact` / `servo` advance belongs to one write agent's scope.

Single-screen workflows skip the pipeline: build the full workflow in one pass using all the collected OR references.

See [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md) for the full pipeline (scaffolding agent, chained screen agents, OR reference handoff, task structure, and prompt templates).

See also: [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the `uia-configure-target` skill details and indication fallback commands.
