### NKeyboardShortcuts — send keyboard shortcuts

#### CRITICAL: `Shortcuts` property and VB bracket parsing

The `Shortcuts` property uses a bracket-based hotkey encoding (`[d(hk)]...[u(hk)]`) that looks like VB expression syntax but is **not** — it is a literal string. This works because the activity exposes **two separate properties**:

| XAML attribute | C# type | Bracket behavior | When to use |
|----------------|---------|------------------|-------------|
| `Shortcuts` | `string` (plain property) | **Literal text** — brackets are part of the hotkey encoding, NOT VB expressions | **Always use this one** for hardcoded shortcuts |
| `ShortcutsArgument` | `InArgument<string>` | **VB expression** — `[...]` would be parsed as a VB expression and FAIL | Only for dynamic/variable-driven shortcuts (rare) |

**NEVER set `ShortcutsArgument` with the hotkey encoding directly** — the VB parser will try to evaluate `d(hk)` as a function call and throw. Always use the plain `Shortcuts` attribute for hotkey strings.

#### Hotkey encoding format

Every shortcut sequence is wrapped in `[d(hk)]...[u(hk)]` delimiters (shortcut-start / shortcut-end). Inside:

| Token | Meaning | Example |
|-------|---------|---------|
| `[d(hk)]` | Start of shortcut sequence | Required at the beginning |
| `[u(hk)]` | End of shortcut sequence | Required at the end |
| `[d(ctrl)]` | Hold Ctrl modifier | `[d(ctrl)]a[u(ctrl)]` = press A while holding Ctrl |
| `[u(ctrl)]` | Release Ctrl modifier | Always pair with `[d(ctrl)]` |
| `[d(shift)]` | Hold Shift modifier | |
| `[u(shift)]` | Release Shift modifier | |
| `[d(alt)]` | Hold Alt modifier | |
| `[u(alt)]` | Release Alt modifier | |
| `[d(lwin)]` | Hold Windows key | |
| `[u(lwin)]` | Release Windows key | |
| `[k(tab)]` | Press special key (Tab) | Use `[k(...)]` for non-printable keys |
| `[k(enter)]` | Press Enter | |
| `[k(back)]` | Press Backspace | |
| `[k(del)]` | Press Delete | |
| `[k(f1)]`–`[k(f12)]` | Press function key | |
| `a`, `w`, etc. | Press printable character | Plain characters (no brackets) |

**Common examples:**

| Shortcut | Encoding |
|----------|----------|
| Ctrl+A | `[d(hk)][d(ctrl)]a[u(ctrl)][u(hk)]` |
| Ctrl+W | `[d(hk)][d(ctrl)]w[u(ctrl)][u(hk)]` |
| Ctrl+Shift+J | `[d(hk)][d(ctrl)d(shift)]j[u(shift)u(ctrl)][u(hk)]` |
| Alt+F4 | `[d(hk)][d(alt)][k(f4)][u(alt)][u(hk)]` |
| Shift+Tab | `[d(hk)][d(shift)][k(tab)][u(shift)][u(hk)]` |
| Tab (10x) then Space | `[d(hk)][k(tab)][u(hk)][d(hk)][k(tab)][u(hk)]...[d(hk)] [u(hk)]` |
| Enter | `[d(hk)][k(enter)][u(hk)]` |
| Space | `[d(hk)] [u(hk)]` |
| Type "ab" | `[d(hk)]ab[u(hk)]` |

**Multiple modifiers** are combined in a single `[d(...)]` block with modifiers listed alphabetically on press and reversed on release: `[d(alt)d(ctrl)]...[u(ctrl)u(alt)]`.

**Multiple shortcut sequences** are concatenated: `[d(hk)]...[u(hk)][d(hk)]...[u(hk)]`.

#### XAML template

```xml
<!-- Sends keyboard shortcuts/hotkeys to the active application.
     InteractionMode: HardwareEvents is most reliable for shortcuts.
     IMPORTANT: Use the plain "Shortcuts" attribute (string), NOT "ShortcutsArgument" (InArgument).
     The [d(hk)]...[u(hk)] encoding is literal text, not a VB expression. -->
<uix:NKeyboardShortcuts
    ActivateBefore="True"
    ClickBeforeMode="None"
    DisplayName="Keyboard Shortcut — Ctrl+A (Select All)"
    HealingAgentBehavior="SameAsCard"
    InteractionMode="HardwareEvents"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Shortcuts="[d(hk)][d(ctrl)]a[u(ctrl)][u(hk)]"
    Version="V5">

  <!-- Optional: verify a target appears after the shortcut -->
  <uix:NKeyboardShortcuts.VerifyOptions>
    <uix:VerifyExecutionOptions DisplayName="Verification target" Mode="Appears">
      <uix:VerifyExecutionOptions.Retry>
        <InArgument x:TypeArguments="x:Boolean" />
      </uix:VerifyExecutionOptions.Retry>
      <uix:VerifyExecutionOptions.Target>
        <uix:TargetAnchorable
            DesignTimeRectangle="0, 0, 0, 0"
            Guid="b4c5d6e7-f8a9-0123-bcde-234567890123"
            Reference="<element-that-appears-after-shortcut>" />
      </uix:VerifyExecutionOptions.Target>
      <uix:VerifyExecutionOptions.Timeout>
        <InArgument x:TypeArguments="x:Double" />
      </uix:VerifyExecutionOptions.Timeout>
    </uix:VerifyExecutionOptions>
  </uix:NKeyboardShortcuts.VerifyOptions>
</uix:NKeyboardShortcuts>
```
