---
confidence: high
---

# Activity Configuration Error — Invalid Property Value

## Context

A UI Automation activity faulted on its own property validation, before (or independent of) finding the target: a required input was empty or a value was out of range. The exception names the property, so the cause is the configuration of that activity.

What this looks like — one of these messages, by activity:
- **Mouse Scroll** (`NMouseScroll`):
  - `Value for property [Movement units] can not be lower than 1.` — `Movement units` was 0 or negative.
  - `Searched element Target or Input UI Element must be set when Scroll type is set to Until element is found.` — "scroll until found" was selected with no searched-element target/input.
  - `Unable to find the searched element.` — scrolling completed without ever finding the configured searched element.
- **Keyboard Shortcuts** (`NKeyboardShortcuts`): `Invalid or empty shortcut sequence.` — no keys, or an unparseable key combination.
- **Take Screenshot** (`NTakeScreenshot`):
  - `'File name' can not be null, empty or whitespace.` — saving to file with no `File name`.
  - `Required argument 'Saved image' was not provided.` — saving to an image output with no `Saved image` argument bound.

What can cause it:
- A property left at an invalid value (Movement units < 1, empty shortcut, empty file name).
- A property fed by a variable/expression that evaluates to empty/zero at runtime because an upstream step did not populate it.
- A mode/option chosen without its dependent input (scroll-until-found without a searched element; save-to-file without a file name; save-to-image without an output argument).

What to look for:
- The message names the property and the activity — read that property's configured value in the workflow.
- If the value comes from a variable/expression, check what produced it.

## Investigation

1. From the failed job, capture the exact message (it names the property), the activity, and the workflow.
2. Open the activity and read the named property's value.
3. If the property is bound to a variable/expression, trace the upstream step that should set it; an empty/zero value usually means that step did not run or returned nothing.
4. For mode-dependent inputs (Mouse Scroll "until element is found", Take Screenshot save mode), confirm the dependent input is provided for the selected mode.

## Resolution

- **Out-of-range/empty literal:** set a valid value on the activity (Movement units ≥ 1, a non-empty shortcut sequence, a file name / output argument).
- **Empty from upstream:** fix the upstream step/variable that should populate the property — do not hard-code a literal to mask a missing producer unless the value is genuinely static.
- **Mode missing its input:** provide the dependent input for the chosen mode (a searched-element target for scroll-until-found; a file name for save-to-file; a `Saved image` output for save-to-image).
- **Mouse Scroll "Unable to find the searched element":** the searched element never appeared while scrolling — confirm the element exists on that view and is reachable by scrolling; if it should appear only after an earlier step, fix that step. Increase the searched-element timeout only if the element genuinely appears late.
