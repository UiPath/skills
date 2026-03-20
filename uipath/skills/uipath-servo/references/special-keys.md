# Special Keys

Special key syntax for `servo type` -- key names, modifiers, and combination patterns.

## Syntax

| Syntax | Meaning |
|--------|---------|
| `[k(key)]` | Press and release |
| `[d(key)]` | Hold down |
| `[u(key)]` | Release |

- Supported with **HardwareEvents** (default) and **WebBrowserDebugger**. Other input methods: support varies by target application.
- Escape a literal `[` by writing `[[`.
- Mix text and special keys: `"Hello[k(enter)]World"` types "Hello", presses Enter, types "World".

## Key Reference

| Category | Keys |
|----------|------|
| **Modifiers** | `ctrl`, `alt`, `shift` |
| **Navigation** | `left`, `right`, `up`, `down`, `home`, `end`, `pgup`, `pgdn`, `tab` |
| **Editing** | `enter`, `back` (Backspace), `del`, `ins`, `esc` |
| **Function** | `f1` through `f12` |
| **Toggle** | `caps`, `num` |
| **Windows** | `lwin`, `rwin` |

Left/right modifier variants exist (`lctrl`, `rctrl`, `lalt`, `ralt`, `lshift`, `rshift`) but `ctrl`/`alt`/`shift` are sufficient for most automation.

## Common Names

Use UiPath key names, not full names:

| Key | Name | NOT |
|-----|------|-----|
| Backspace | `back` | `backspace` |
| Delete | `del` | `delete` |
| Escape | `esc` | `escape` |
| Page Up | `pgup` | `pageup` |
| Page Down | `pgdn` | `pagedown` |
| Insert | `ins` | `insert` |

## Examples

```
servo type e3 "[k(enter)]"                       # press Enter
servo type e3 "[d(ctrl)]a[u(ctrl)]"              # Ctrl+A (select all)
servo type e3 "[d(alt)k(f4)u(alt)]"              # Alt+F4 (close window)
servo type e3 "[d(shift)k(left)k(left)u(shift)]" # Shift+Left x2 (select 2 chars)
servo type e3 "Hello[k(enter)]World"             # type Hello, press Enter, type World
servo type e3 "[[k(enter)]"                      # types literal "[k(enter)]"
```
