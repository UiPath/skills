# Show Callout Activity Reference

Displays a form-based callout anchored to a UI element. The callout tracks the target's position and follows it in real time.

## Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| FormId | String | *(required)* | The callout form to display (selected in the designer) |
| InstanceName | String | `null` | Optional tag to distinguish multiple callout instances |
| Target | *(via Indicate Target)* | `null` | UI element to anchor to, captured using the Indicate Target button |
| UiElement | UiElement | `null` | Alternative: a UiElement variable from a previous UI Automation activity |
| ContinueOnError | Boolean | `true` | If true, exceptions are suppressed and the activity completes gracefully |
| AutomaticallyCloseAfter | TimeSpan? | `null` | Auto-close the callout after this duration |
| Arguments | Dictionary | `{}` | Field bindings (same as Show Form) |
| Width | Int32? | 300 | Width in pixels |
| Height | Int32? | 280 | Height in pixels |
| Title | String | `null` | Custom window title |
| ShowMargin | Boolean? | `false` | Window chrome (off by default) |
| ShowInTaskbar | Boolean? | `false` | Taskbar visibility (hidden by default) |

## Target Selection

**Either Target or UiElement must be provided.** A validation error is raised if both are empty.

- **Target** (recommended): Click the "Indicate Target" button in the designer to visually select the UI element the callout should point to. This captures a selector, just like other UI Automation activities.
- **UiElement**: Pass a `UiElement` variable obtained from a previous activity (e.g., Find Element). Useful when the target is already known at runtime.

When `UiElement` is set, the Indicate Target button is hidden (and vice versa).

## Behaviour

- The callout is always **async**: the activity completes immediately after the callout is shown, and the workflow continues while the callout remains visible.
- The callout displays a **visual pointer** (arrow) toward the target element.
- Position and Z-order are managed automatically - the callout follows the target if it moves and stays visually associated with the target's window.
- Properties like Left, Top, WindowState, and TopMost are auto-managed and hidden in the designer.

## Auto-Close

Set `AutomaticallyCloseAfter` to a `TimeSpan` value to have the callout close itself after a duration. Useful for transient guidance messages (e.g., "Click this button" that disappears after 10 seconds).

## Error Handling

With `ContinueOnError = true` (the default), if the target element cannot be found or the callout fails to display, the activity completes without throwing. Set to `false` if you need strict error handling.

Common error scenarios:
- Target element not found on screen
- UI Automation services not available
- Form not found (invalid FormId)
