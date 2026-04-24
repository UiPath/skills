# Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill through TARGET-8) — before using servo to advance to the next state. Servo interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use servo to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, servo is ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

## Advancing UI State — Two Options

After registering an element in the Object Repository, you often need to interact with it to reveal the next screen's elements. Two CLIs can drive the interaction; prefer `uia interact` whenever possible.

### Preferred: `uia interact` (for configured OR targets)

Once an element is registered in the OR (TARGET-8 complete), use `uia interact click` or `uia interact type` with the OR reference ID. This reuses the exact selector that was validated during target configuration — no separate snapshot, no second ref system, no selector guessing.

```bash
# Click a configured target by OR reference ID
uip rpa uia interact click --reference-id "<OR_REFERENCE_ID>"

# Type into a configured target by OR reference ID
uip rpa uia interact type --reference-id "<OR_REFERENCE_ID>" --text "hello"
```

Alternate input forms (same result):

```bash
# Use the definition file directly (before OR registration)
uip rpa uia interact click --definition-file-path "<WORK_FOLDER>/Target_1_Definition.json"
uip rpa uia interact type --definition-file-path "<WORK_FOLDER>/Target_1_Definition.json" --text "hello"

# Use raw selectors (ad-hoc, no OR entry required)
uip rpa uia interact click --window-selector "<html ... />" --partial-selector "<webctrl ... />"
uip rpa uia interact type --window-selector "<html ... />" --partial-selector "<webctrl ... />" --text "hello"
```

### Fallback: `servo` (for elements not in OR)

Use servo only when the element is NOT in the Object Repository and doesn't need to be (for example, a transient element you just want to click once to advance state, with no intention of using it in the final workflow).

> **WARNING: Servo refs and UIA snapshot refs are independent numbering systems.** Element `e42` from `uip rpa uia snapshot filter` is NOT the same as `e42` from `servo snapshot`. Always run `servo snapshot <window-ref>` to get servo-specific refs before using `servo click`/`servo type`. Never reuse refs from UIA snapshots in servo commands.

```bash
servo targets
servo snapshot <window-or-tab-ref>
servo click <servo-element-ref>
```

## Multi-Step Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to TARGET-8 (OR registration) for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state — prefer `uia interact click/type --reference-id "<OR_REF>"` on an element you just registered; fall back to servo only for elements not in OR.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill through TARGET-8).
4. **Repeat** until all workflow targets are registered in the OR.

**Do NOT use `uip rpa run-file` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. Both `uia interact` and `servo` are stateless: they perform one action and leave the app in the resulting state.

## Spawning XAML Write Agents

After completing all `uia-configure-target` calls for a screen (through TARGET-8 for all elements), spawn a write agent to add that screen's activities to the workflow file. The orchestrator hands off only OR reference IDs — the agent inserts plain activities with unique `sap2010:WorkflowViewState.IdRef` attributes and attaches targets itself via `link-element`. Each write agent depends on the previous one completing — they form a strict chain.

The screen boundary for write agents aligns with the Complete-then-advance rule above: everything configured before the next servo advance belongs to one write agent's scope.

See [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md) for the full pipeline, prompt templates, and chained dependency model.

After all targets are captured, build the full workflow in one pass using all the collected OR references — unless the workflow spans multiple screens, in which case use the parallel authoring pipeline to chain write agents per screen (see [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md)).

See also: [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for the `uia-configure-target` skill details and indication fallback commands.
