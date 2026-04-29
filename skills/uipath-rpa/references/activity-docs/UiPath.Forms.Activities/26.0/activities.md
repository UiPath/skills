# Forms Activities Reference

## Show Form

Displays a form designed in UiPath Studio.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| FormId | String | *(required)* | The form to display (selected in the designer) |
| InstanceName | String | `null` | Optional tag to distinguish multiple instances of the same form |
| IsAsync | Boolean | `true` | If true, the activity completes immediately; if false, blocks until the form is closed |
| Arguments | Dictionary | `{}` | Bindings between form field IDs and workflow variables |
| Width | Int32? | `null` | Window width in pixels |
| Height | Int32? | `null` | Window height in pixels |
| Left | Int32? | `null` | Window X position in pixels |
| Top | Int32? | `null` | Window Y position in pixels |
| Title | String | `null` | Custom window title |
| ShowMargin | Boolean? | `null` | Whether the window has standard chrome (title bar, borders) |
| ShowInTaskbar | Boolean? | `null` | Whether the form appears in the taskbar |
| TopMost | Boolean? | `null` | Whether the form stays on top of other windows |
| WindowState | WindowState? | `null` | Initial window state (Normal, Minimized, Maximized) |

### Usage Notes

- If a form with the same FormId and InstanceName is already open, the existing window is reused rather than opening a duplicate.
- In **sync mode**, Out and InOut arguments are updated when the form closes.
- In **async mode**, Out and InOut arguments bound to Global Variables update in real time as the user interacts with the form.

---

## Close Form

Programmatically closes a running form.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The form to close |
| InstanceName | String | The instance tag (if multiple instances exist) |

---

## Get Form Fields

Reads field values from a running form.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The form to read from |
| InstanceName | String | The instance tag |
| Arguments | Dictionary&lt;String, OutArgument&gt; | Map of form field IDs to output variables |

### Usage Notes

- Each key in `Arguments` is a form field ID; the corresponding variable receives the field's value.
- Values are automatically converted to match the variable's type.
- Throws if no form matches, or if multiple forms match the selector (use InstanceName to disambiguate).

---

## Set Form Fields

Sets field values on a running form.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The form to update |
| InstanceName | String | The instance tag |
| Arguments | Dictionary&lt;String, InArgument&gt; | Map of form field IDs to input values |

### Usage Notes

- Each key in `Arguments` is a form field ID; the corresponding value is pushed to the form.
- Throws if no form matches the selector.

---

## Change Form Properties

Modifies the window properties of a running form. Only properties that are set (non-null) are applied; others remain unchanged.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The form to modify |
| InstanceName | String | The instance tag |
| Width | Int32? | Window width in pixels |
| Height | Int32? | Window height in pixels |
| Left | Int32? | Window X position |
| Top | Int32? | Window Y position |
| Title | String | Window title |
| ShowMargin | Boolean? | Window chrome visibility |
| TopMost | Boolean? | Always-on-top state |
| WindowState | WindowState? | Window state (Normal, Minimized, Maximized) |

---

## Hide Form

Hides a running form window without closing it. The form remains active in the background.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The form to hide |
| InstanceName | String | The instance tag |

---

## Bring Form To Front

Brings a previously hidden form back to the foreground.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The form to restore |
| InstanceName | String | The instance tag |

---

## Execute Script

Executes JavaScript code within the context of a running form.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| FormId | String | The target form |
| InstanceName | String | The instance tag |
| Source | String | JavaScript source code to execute |

### Usage Notes

- If `Source` is empty, the activity completes without error and returns an empty result.
- The script runs inside the form's browser context and can interact with the form's DOM and Form.io API.
