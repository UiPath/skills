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
- **Space key:** Use a literal space character ` `, NOT `[k(space)]`. Example: Ctrl+Space = `[d(ctrl)] [u(ctrl)]`.
- All key names must be **lowercase**: `ctrl`, `shift`, `enter` -- not `Ctrl`, `SHIFT`, `Enter`.

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

## Modifier Combinations

| Pattern | Syntax | Example |
|---------|--------|---------|
| Single modifier | `[d(mod)]key[u(mod)]` | `[d(ctrl)]c[u(ctrl)]` = Ctrl+C (copy) |
| Multiple modifiers | `[d(m1)][d(m2)]key[u(m2)][u(m1)]` | `[d(ctrl)][d(shift)]a[u(shift)][u(ctrl)]` = Ctrl+Shift+A |
| Modifier + special key | `[d(mod)][k(key)][u(mod)]` | `[d(alt)][k(f4)][u(alt)]` = Alt+F4 |
| Key sequence | Chain in one string | `[d(ctrl)]a[u(ctrl)][k(del)]` = Select all + delete |

## Common Workflow Patterns

Keyboard shortcuts are often faster and more reliable than clicking through menus. Prefer shortcuts when confident they work in the target app.

### Text Editing

```bash
# Select all and delete (clear a field)
servo type e3 "[d(ctrl)]a[u(ctrl)][k(del)]"

# Replace field text: select all, delete, type new value
servo type e3 "[d(ctrl)]a[u(ctrl)][k(del)]new text here"

# Undo / Redo
servo type e3 "[d(ctrl)]z[u(ctrl)]"             # Undo
servo type e3 "[d(ctrl)]y[u(ctrl)]"             # Redo

# Copy / Paste
servo type e3 "[d(ctrl)]c[u(ctrl)]"             # Copy
servo type e3 "[d(ctrl)]v[u(ctrl)]"             # Paste

# Find on page (works in browsers, editors, most apps)
servo type e3 "[d(ctrl)]f[u(ctrl)]"
servo type e5 "search term[k(enter)]"

# Find and Replace
servo type e3 "[d(ctrl)]h[u(ctrl)]"
```

### Navigation

```bash
# Tab between form fields
servo type e3 "value1[k(tab)]value2[k(tab)]value3"

# Shift+Tab to go back a field
servo type e3 "[d(shift)][k(tab)][u(shift)]"

# Page up/down for fast scrolling
servo type e3 "[k(pgdn)]"
servo type e3 "[k(pgup)]"

# Home/End to jump to start/end of line
servo type e3 "[k(home)]"
servo type e3 "[k(end)]"

# Ctrl+Home/End to jump to start/end of document
servo type e3 "[d(ctrl)][k(home)][u(ctrl)]"
servo type e3 "[d(ctrl)][k(end)][u(ctrl)]"
```

### Browser Shortcuts

```bash
# New tab
servo type e3 "[d(ctrl)]t[u(ctrl)]"

# Close tab
servo type e3 "[d(ctrl)]w[u(ctrl)]"

# Address bar focus (then type URL + Enter)
servo type e3 "[d(ctrl)]l[u(ctrl)]"

# Refresh page
servo type e3 "[k(f5)]"
```

### Modifier + Click (via servo click --modifiers)

```bash
# Ctrl+click for multi-select in lists/tables
servo click e5 --modifiers Ctrl

# Shift+click for range-select
servo click e5 --modifiers Shift

# Ctrl+Shift+click
servo click e5 -m "Ctrl,Shift"
```

## Type Into Pitfalls

When using `servo type` with regular text (not just special keys), be aware of these interactions:

### Newlines trigger Enter

Typing a newline character in `servo type` sends an Enter key press. In messaging apps (Slack, Teams, etc.), this **sends the message** instead of creating a new line.

```bash
# WRONG -- sends "Line 1" as a message, then types "Line 2" into a new message
servo type e3 "Line 1\nLine 2"

# CORRECT -- use Shift+Enter for a newline within the message
servo type e3 "Line 1[d(shift)][k(enter)][u(shift)]Line 2"
```

**Newline key by app context:**
- **Slack, Teams, chat apps:** Shift+Enter = newline, Enter = send
- **Excel, Google Sheets:** Alt+Enter = newline within cell, Enter = move to next cell
- **Word, Notepad, most editors:** Enter = newline (no workaround needed)

### Auto-bulleted lists

Apps like Slack, Teams, PowerPoint, and Word auto-add bullets when pressing Enter in a list context. If you also type a bullet character, you get doubled bullets (`- - Item`).

```bash
# WRONG in Slack/Teams -- double bullets
servo type e3 "- Item 1[d(shift)][k(enter)][u(shift)]- Item 2"

# CORRECT -- only add bullet for first item, app adds rest
servo type e3 "- Item 1[d(shift)][k(enter)][u(shift)]Item 2"
```

## Examples

```
servo type e3 "[k(enter)]"                       # press Enter
servo type e3 "[d(ctrl)]a[u(ctrl)]"              # Ctrl+A (select all)
servo type e3 "[d(alt)][k(f4)][u(alt)]"          # Alt+F4 (close window)
servo type e3 "[d(shift)][k(left)][k(left)][u(shift)]" # Shift+Left x2 (select 2 chars)
servo type e3 "Hello[k(enter)]World"             # type Hello, press Enter, type World
servo type e3 "[[k(enter)]"                      # types literal "[k(enter)]"
```
