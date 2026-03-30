---
name: uipath-servo
description: "Desktop and browser UI automation via CLI -- click, type, read, verify, screenshot, and extract UI elements. TRIGGER when: user mentions 'servo', any UI interaction or automation intent (desktop or browser), UI testing or verification tasks, taking screenshots of desktop/windows/elements. DO NOT TRIGGER when: pure API/backend work, writing UI code (WPF, WinForms, Java, Qt, HTML/CSS) without intent to test or verify it."
metadata:
  allowed-tools: Bash(servo:*), Bash(npx *@uipath/servo*), Read, Grep
---

# UI Automation with Servo

> **Servo is a standalone command-line tool.** It is NOT a subcommand of `uip` — you run it directly from your terminal.

**Windows only.** Run via npx or install globally:

```bash
# Run directly via npx (no install needed)
npx @uipath/servo --help

# Or install globally, then use the `servo` command
npm install -g @uipath/servo
servo --help
```

## Quick Start

```bash
# list top-level windows and browser tabs
servo targets
# snapshot a window to get its UI tree
servo snapshot w1
# interact using element refs from the snapshot
servo click e5
servo type e3 "hello"
servo select e8 "Option B"
# re-snapshot after UI changes -- refs may be stale
servo snapshot w1
# take a screenshot
servo screenshot w1
```

## Commands

All commands accept --help`, `--timeout` and `--visualize` (shows a visual indicator of the target element).

Commands that write output files accept `--filename <path>` to override the output file path.

### Discover

```bash
servo targets                           # List windows (w-refs) and browser tabs (b-refs)
servo targets --exclude Windows         # Browser tabs only
servo snapshot w1                       # Capture UI tree with element refs (e-refs)
servo snapshot b1                       # Snapshot a browser tab
servo snapshot w1 --framework UiaOnly   # Use specific UI framework
```

### Interact

```bash
servo click e5                                # Click (left, single)
servo click e5 --button Right                 # Right-click
servo click e5 --type Double                  # Double-click
servo click e5 -i ControlApi                  # Click via element API (background windows)
servo click e5 --offset "10,-5"               # Click with pixel offset from center (default origin)
servo click e5 --origin TopLeft --offset "5,-10"  # Origin: Center, TopLeft, TopRight, BottomLeft, BottomRight, TopCenter, BottomCenter, LeftCenter, RightCenter
servo click e5 --modifiers Ctrl               # Ctrl+click (e.g. multi-select in lists)
servo click e5 -m "Ctrl,Shift"                # Ctrl+Shift+click
servo hover e4                                # Hover over element
servo type e3 "some text"                     # Type into element
servo type e3 "text" --clear-before           # Clear field, then type (implies --click-before)
servo type e3 "text" --click-before           # Click field before typing (auto-enabled for HardwareEvents)
servo type e3 "text" -i ControlApi            # Use ControlApi (may auto-clear)
servo type e3 "text" -i WebBrowserDebugger    # Use browser debugger protocol (recommended for Chrome/Edge)
servo type e3 "[d(ctrl)]a[u(ctrl)]"           # Select all (Ctrl+A)
servo select e8 "Option B"                    # Select "Option" from dropdown/list
servo wheel e5 --direction Down -c 10         # Scroll down 10 clicks
servo focus e5                                # Bring element into view and focus
servo window w2 BringToForeground             # Bring window to front
servo window w1 Maximize                      # Maximize, Minimize, Restore, Close, Hide, Show
```

### Inspect

```bash
servo get e5 text                       # Read a single attribute
servo get-all e5                        # Read all attributes
servo get-attribute-names e5            # List available attribute names
servo screenshot                        # Full desktop screenshot
servo screenshot w1                     # Window screenshot
servo screenshot e5                     # Element screenshot
servo extract-table e5                  # Extract table data as markdown
servo highlight e5                      # Draw red border
servo highlight e5 --color Blue --duration 5
servo selector e5                       # Get UiPath selector string
```

### Manage

```bash
servo server --start                    # Start server manually
servo server --stop                     # Stop server
servo server --status                   # Check server status
servo server --start -s sess1           # Start server for specific session
servo server --stop -s sess1            # Stop server for specific session
servo server --kill-all                 # Kill all server processes (last resort)
servo clean                             # Delete output files
```

Commands that produce output (targets, snapshot, screenshot, etc.) print a summary to the console and write details to a file:

```bash
servo targets
### Top-level targets (11 windows, 2 browser tabs)
- [Targets](.servo/output/targets-2026-07-19T12-10-01-002.yml)
```

Read the linked `.servo/output/` file to see the full results.

## Snapshot Format

Snapshots show the UI accessibility tree. Each node has:

- **Role** -- Element type: `Button`, `InputBox`, `CheckBox`, `DropDown`, `List`, `TreeItem`, `TabPage`, `MenuItem`, etc.
- **"Name"** -- Accessible label in quotes (e.g., `Button "OK"`)
- **[ref=eN]** -- Element reference for interaction. Use this ref in commands.
- **[state]** -- State markers: `[selected]`, `[focused]`, `[disabled]`, `[read only]`
- **: text** -- Inline value (e.g., `InputBox [ref=e3]: pre-filled`)
- **/attr** -- Attributes as child lines (e.g., `/url: https://...`, `/placeholder: Type here`)
- **Children** -- Nested with indentation

Example:

```
- DropDown [ref=e73]: Second
  - Option "-- Choose --"
  - Option "First"
  - Option "Second" [selected]
  - Option "Third (disabled)"
- InputBox "Username" [ref=e5]: john_doe
  - /placeholder: Enter username
- CheckBox "Remember me" [ref=e6] [selected]
- Button "Submit" [ref=e7]
- Button "Cancel" [ref=e8] [disabled]
```

**Key rules:**

- Only elements with `[ref=eN]` are interactable. Elements without refs are shown for context only.
- `[disabled]` elements cannot be interacted with -- skip them.
- `[selected]` on CheckBox/RadioButton means checked; on TabPage/ListItem means active.
- Snapshots may not show all text or attribute values. Use `servo get <e> text` or `servo get-all <e>` to read values, or `servo extract-table <e>` for table data.

## Ref Lifecycle

**Window refs (w1, w2) and browser refs (b1, b2)** are assigned by `servo targets`. They reset on each `servo targets` call.

**Element refs (e1, e2, e3...)** are assigned by `servo snapshot`. They reset on each `servo snapshot` call.

b-refs target browser tabs; w-refs target windows. See Application Guides > Browsers for details.

**Always re-snapshot after actions that change UI state.** Clicking a button, selecting a tab, or typing may alter the UI tree, making previous e-refs invalid.

```bash
servo snapshot w1        # Get refs
servo click e7           # Perform action
servo snapshot w1        # Get fresh refs -- old ones are stale
servo type e5 "hello"    # Use new refs
```

## Frameworks

Use `--framework` with `servo snapshot` to control how the UI tree is scanned.

Default framework works for most apps. Exceptions — use `--framework UiaOnly` for:
- WinUI3 apps — modern Windows apps like Windows Terminal, and the redesigned Notepad, Paint, Calculator, Media Player
- WPF apps — .NET desktop apps with rich UI like Visual Studio, Blend, or any app built with XAML
- SAP Logon (only the connection picker)

If a snapshot looks empty or incomplete, try a different framework.

## Input Methods

Use `--input-method` (`-i`) with `click`, `type`, and `hover`:

- **HardwareEvents** (default) -- Simulates real mouse/keyboard. Auto-activates the window (foreground required). Typing appends to existing text, use `--clear-before` to clear first.
- **ControlApi** -- Uses the element's native API directly. Works on background windows. Usually auto-clears the field before typing, so do not use `--clear-before` by default. Verify the result with `servo get`, `servo get-all`, or re-snapshot -- only retry with `--clear-before` if the field contains unexpected text. Recommended for Firefox (only in b-ref mode), Java Swing/AWT apps, and SAP WinGUI session windows.
- **WebBrowserDebugger** -- Dispatches via Chromium Debugger. Recommended for Chrome/Edge. Does not require foreground.

Switch input methods when the default has no visible effect on the target element.

Special keys in `servo type` and `--modifiers` in `servo click` are fully supported with HardwareEvents and WebBrowserDebugger. ControlApi may support special keys for some applications (e.g.: Browsers (b-refs) and SAP session windows), but this is not guaranteed -- other input methods may silently ignore them.

## Special Keys

`servo type` supports special key syntax:

- `[k(key)]` -- Press and release (e.g., `[k(enter)]`, `[k(tab)]`)
- `[d(key)]` -- Hold down (e.g., `[d(ctrl)]`, `[d(shift)]`)
- `[u(key)]` -- Release (e.g., `[u(ctrl)]`, `[u(shift)]`)

```bash
servo type e5 "[d(ctrl)]a[u(ctrl)]"         # Select all
servo type e5 "[d(ctrl)]c[u(ctrl)]"         # Copy
servo type e5 "[k(enter)]"                  # Press Enter
servo type e5 "Line 1[k(enter)]Line 2"      # Type multiline
servo type e5 "[[k(enter)]"                 # Type literal "[k(enter)]"
```

Full key reference: [references/special-keys.md](references/special-keys.md)

## UiPath Selectors

`servo selector` generates UiPath selector strings compatible with UiPath UIAutomation:

```bash
servo selector e10
<wnd app='notepad.exe' title='Untitled - Notepad' /><ctrl name='Text Editor' role='document' />
```

## Common Patterns

### Select from dropdown/list

DropDown and List elements show options as children. Use the **parent's ref** and the option's text:

```bash
servo select e73 "First"              # Select "First" using the DropDown's ref
```

The current selection is shown as inline text after `:` or as a child marked `[selected]`. Re-snapshot to confirm.

If options are missing, click the element to expand it and re-snapshot -- some load children only when opened.

### Toggle a checkbox

```bash
servo click e6                # Click to toggle; re-snapshot to verify
servo snapshot w1             # [selected] = checked, no [selected] = unchecked
```

### Navigate a menu

```bash
servo click e13               # Click "File" menu item
servo snapshot w1             # Snapshot to see submenu items
servo click e42               # Click the desired submenu item
```

### Expand a tree node

```bash
servo click e108 --type Double  # Double-click to expand tree item
servo snapshot w1               # Snapshot to see children
```

### Switch tabs

```bash
servo click e115              # Click the tab you want
servo snapshot w1             # Verify tab is now [selected] and content changed
```

### Fill a form

```bash
servo targets                 # Find the window
servo snapshot w1
servo type e5 "John Doe" --clear-before
servo type e6 "john@example.com" --clear-before
servo select e8 "USA"
servo click e10               # Submit button
servo snapshot w1             # Verify result
```

## Error Recovery

**Possible misconfiguration:** If you suspect an app is not properly configured for automation (e.g., missing extension, scripting disabled), tell the user and point them to the relevant Application Guide.

**Empty/partial snapshot** -- Wrong framework or window not ready:

```bash
servo window w1 BringToForeground      # Ensure window is visible
servo window w1 Maximize               # Maximize to see all elements
servo snapshot w1 --framework UiaOnly  # Try different framework
```

**Dropdown/list options not visible** -- Click to expand, then re-snapshot:

```bash
servo click e10                        # Click the DropDown to expand it
servo snapshot w1                      # Re-snapshot to see the options
```

**Interaction has no visible effect:**

```bash
servo get-all e5                       # Check element attributes for clues
servo click e5 -i ControlApi           # Try a different input method
```

**Click lands on wrong spot** -- The click feedback shows screen coordinates. Take a screenshot and check whether those coordinates are visually inside the intended element. If not:

```bash
servo highlight e5                               # Highlight the element to see its bounds
servo screenshot e5                              # Screenshot the whole desktop
servo get e5 position                            # Get the reported position of the element

# Try
servo click e5 --origin TopLeft --offset "5,5"   # Use a different origin point instead of center
servo click e5 -i ControlApi                     # Might ignore the coordinates
servo snapshot w1 --framework UiaOnly            # Re-snapshot with different framework (bounds may differ)
servo click e10                                  # Click a child element that may be more reliably located
```

**Connection error** -- Server in a bad state:

```bash
servo server --kill-all                # Kill all servers, then retry
servo targets                          # Reconnects automatically
```

## Sessions

Use `--session` (`-s`) to run isolated servo instances:

```bash
servo targets -s sess1
servo snapshot w1 -s sess1
servo click e5 -s sess1
```

Each session has its own server, refs, and state.

**Cleanup:** When automation is done, stop all servers -- both named and default sessions:

```bash
servo server --stop                    # Stop default session
servo server --stop -s sess1           # Stop named session
```

## Application Guides

### Browsers

**Prerequisites:** UiPath browser extensions must be installed for b-refs to appear in `servo targets`. Install: https://docs.uipath.com/studio/standalone/latest/user-guide/about-extensions

**Targeting:** Use b-refs (not w-refs) for web content -- b-refs provide the DOM tree.

```bash
servo targets
# - Window "My Page - Google Chrome" [ref=w1]
# - Browser "My Page" [ref=b1]

servo snapshot b1                       # Preferred: snapshot the browser tab
```

**IMPORTANT: Internal browser pages (new tab, settings, bookmarks, downloads etc.) are NOT available as b-refs.** The browser extension cannot access these pages, so they will only appear as w-refs in `servo targets`.

- Discarded tabs show `[discarded]` state -- servo attempts to activate them automatically before interaction
- After page navigation, re-snapshot to get fresh refs

**Input methods:**
- Chromium (Chrome, Edge): Use `-i WebBrowserDebugger`. Fallback: ControlApi, then HardwareEvents.
- Firefox: Use `-i ControlApi` -- WebBrowserDebugger is not supported. Fallback: HardwareEvents.


### SAP WinGUI

**Prerequisites:** SAP GUI Scripting should be enabled (server and client). Setup guide: https://docs.uipath.com/activities/other/latest/ui-automation/sap-wingui-configuration-steps

**Framework selection:**
- SAP Logon (connection picker) → `--framework UiaOnly`
- All other SAP GUI windows (after connecting) → `--framework Default` (or omit)

```bash
servo snapshot w1 --framework UiaOnly    # SAP Logon window
servo snapshot w1                        # SAP session window (Default)
```

**Transaction code navigation:**

```bash
servo snapshot w1                              # Get ref for the command field
servo type e1 -i ControlApi "/nVA01[k(enter)]" # Navigate to transaction VA01
servo snapshot w1                              # New transaction screen loaded with new refs
```

**Reading table data:** Snapshots only show rows currently in view. Maximize first for more rows in snapshot:

```bash
servo extract-table e15 --timeout 120    # Extracts entire table, not just visible rows
```

To interact with specific rows not in view, scroll and re-snapshot:

```bash
servo wheel e15 --direction Down -c 5    # Scroll down
servo snapshot w1                        # Fresh refs for newly visible rows
```

**Status bar:** SAP confirms operations via the status bar. After an action:

```bash
servo get e99 text                       # Read status bar
```

**Tips:**
- Use longer timeouts for SAP operations
- Check status bar messages to confirm operations
- SAP tables only expose visible rows in snapshots -- use `extract-table` for full data
