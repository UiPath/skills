# UiPath UIAutomation Activities - Legacy Reference

## Overview
Legacy desktop UI automation for Windows. Click, type, find elements, manage windows/browsers. Package: `UiPath.UIAutomation.Activities`.

---

## Input Methods

| Method | Constant | Speed | Reliability | Special Keys | Notes |
|--------|----------|-------|-------------|--------------|-------|
| Hardware Events (default) | SYNTHESIZE_INPUT | Slow | Most reliable | YES | Acquires input lock, blocks user input |
| Window Messages | WINDOW_MESSAGES | Fast | Least reliable | YES | Best for classic Win32 apps |
| UI Automation API | API | Medium | Very reliable | **NO** | SimulateClick/SimulateType; bypasses input |

**CRITICAL: Cannot use SimulateClick AND SendWindowMessages simultaneously**
**SimulateType + special keys produces design-time WARNING** (not hard error)

---

## Key Activities

### Mouse
| Activity | Key Arguments | Defaults |
|----------|---------------|----------|
| `Click` | ClickType (Single/Double/Down/Up), MouseButton (Left/Right/Middle), KeyModifiers, CursorPosition, SimulateClick, SendWindowMessages | AlterIfDisabled=true |
| `Hover` | CursorPosition, SimulateHover, SendWindowMessages | Hover duration ~1000ms |

### Keyboard
| Activity | Key Arguments | Defaults |
|----------|---------------|----------|
| `TypeInto` | Text, SimulateType, SendWindowMessages, Activate, ClickBeforeTyping, EmptyField, DelayBetweenKeys | Activate=true, AlterIfDisabled=true |
| `TypeSecureText` | SecureText (SecureString) | Special keys escaped in non-Simulate mode |
| `SendHotkey` | Key, SpecialKey, KeyModifiers | Activate=true |

### Element Search
| Activity | Key Arguments | Key Gotcha |
|----------|---------------|------------|
| `Element Exists` | Target | **Returns false instead of throwing on timeout** |
| `Find Children` | Target, Filter, Scope | Returns lazy IEnumerable |
| `Find Relative` | Target, CursorPosition (offset) | Returns first element at coordinates |
| `Get Ancestor` | Target, UpLevels | Returns null at root |
| `Wait Element Appear` | Target, WaitVisible, WaitActive | Adaptive polling: 50ms -> 200ms -> 1000ms |
| `Wait Element Vanish` | Target, WaitNotVisible | Returns silently on timeout |

### Element Attributes
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `Get Text` / `Get Value` | Target | Wraps GetAttribute("text") |
| `Get Attribute` | Target, Attribute | Returns null if attribute doesn't exist |
| `Set Value` | Target, Text | Uses SetAttribute("text") |
| `Select Item` | Target, Item | Exact match usually required |
| `Select Multiple Items` | Target, MultipleItems, AddToSelection | |
| `Check` | Target, Action (Check/Uncheck/Toggle) | Toggle reads current state first |
| `Wait Attribute` | Attribute, AttributeValue | Supports wildcards (* and ?); polls every 100ms |
| `Get Position` | Target | Returns Rectangle (screen coordinates) |

### Actions
| Activity | Purpose |
|----------|---------|
| `Activate` | Bring window to foreground |
| `Set Focus` | Set keyboard focus (doesn't foreground) |
| `Highlight` | Debug visualization (blocking for duration) |
| `Take Screenshot` | Capture element as Image |

### Scopes
| Activity | Key Arguments |
|----------|---------------|
| `Open Browser` | Url, BrowserType (IE/Chrome/Firefox/Edge), Private, NewSession, Hidden, CommunicationMethod |
| `Open Application` | Selector, FileName, Arguments, WorkingDirectory |
| `Window Scope` | Selector OR Window (mutually exclusive) |
| `Browser Scope` | Selector OR Browser (mutually exclusive) |

---

## Special Key Syntax (TypeInto)
```
[k(end)]        - End key
[k(home)]       - Home key
[k(del)]        - Delete key
[k(backspace)]  - Backspace
[k(enter)]      - Enter
[k(tab)]        - Tab
[k(escape)]     - Escape
[k(ctrl+a)]     - Ctrl+A (press+release)
[d(ctrl)]       - Ctrl down
[u(ctrl)]       - Ctrl up
[k(F1)]         - Function key F1-F12
```

---

## Critical Gotchas

### AlterIfDisabled Default
1. **AlterIfDisabled=true by default** on Click, TypeInto, SetValue, SelectItem, Check - can interact with disabled/grayed controls unexpectedly

### TypeInto Specifics
2. **SimulateType CANNOT handle special keys** - fails validation if `[k(...)]` syntax detected
3. **EmptyField uses hardcoded sequence**: `[k(end)d(shift)k(home)u(shift)k(del)]` - may fail for multi-line. **CRITICAL: EmptyField is silently ignored when SimulateType=true** - only works with hardware events and SendWindowMessages
4. **DelayBetweenKeys max 1000ms** - validation error if exceeded
5. **Activate=true by default** - may cause unwanted window switches

### Selector Issues
6. **Selector matching is fragile** - UI changes invalidate selectors
7. **Placeholders** `{varName}` resolved at runtime - null variables cause failures
8. **Closest matches** can return wrong element if multiple similar elements exist
9. **Closest matches disabled in Exists** activity (returns false cleanly)

### Click Specifics
10. **SimulateClick cannot CLICK_DOUBLE with BTN_RIGHT or BTN_MIDDLE**
11. **SimulateClick doesn't acquire input lock** - others do
12. **CursorMotionType** affects how cursor moves (straight line, smooth, etc.)

### Timing
13. **Default timeout ~30,000ms** (30 seconds) across most activities
14. **DelayBefore/DelayAfter are sequential** (Thread.Sleep internally)
15. **WaitUiElementAppear adaptive polling**: 50ms -> 200ms -> 1000ms
16. **Exists returns false instead of throwing** on timeout

### Browser Scope
17. **NewSession=true (default)** creates new browser process (slower but isolated)
18. **NewSession=false** reuses existing browser (faster, shared state/cookies)
19. **Private mode** may disable extensions/drivers
20. **CommunicationMethod**: Native (UiPath driver) vs WebDriver (Selenium-based)

### Window/Browser Scope Validation
21. **Must set either Selector OR Window/Browser** - not both, not neither
22. **If Window/Browser set, SearchScope cannot be set**

### Image-Based Activities
23. **Template matching** (not AI) - sensitive to resolution, brightness, minor UI changes
24. **Slower than selector-based** - use only for unstable selectors

### Error Handling
25. **ContinueOnError=false by default** - exceptions thrown
26. **Governance exceptions never suppressed** even with ContinueOnError=true

### Additional Validated Gotchas
27. **OpenBrowser defaults to IE** - BrowserType default is `BrowserType.IE`
28. **Hover has fixed 1000ms duration** - hardcoded, not configurable
29. **Default timeouts**: Timeout=30,000ms, DelayAfter=300ms, DelayBefore=200ms, OpenBrowser=60s
30. **AlterIfDisabled NOT passed to node in hardware events mode for TypeInto** (but IS passed for Click) - inconsistent behavior
31. **CursorMotionType.Smooth only works with hardware events** - has no effect with SimulateClick or SendWindowMessages
32. **Data Scraping hardcodes ContinueOnError=true** - extraction failures produce empty DataTable, no error
33. **SimulateClick MV3 workaround** - hidden project setting `EnableWorkaroundForSimulateClickMV3` (default false) needed for Chrome Manifest V3 extensions
34. **Image OCR uses hardcoded 5-pixel offset** - can cause incorrect crops on small images
