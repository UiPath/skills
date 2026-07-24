# Selector Guide

Selector anatomy, strategy, and best practices for building reliable UI automation in legacy UiPath workflows.

UI automation activities (Click, TypeInto, etc.): [§ UIAutomation Activities Reference](#uiautomation-activities-reference) below.
For input method gotchas (SimulateType, EmptyField), see [activity-docs/_COMMON-PITFALLS.md](./activity-docs/_COMMON-PITFALLS.md).

---

## 1. Selector XML Anatomy

A selector is an XML string that identifies a UI element by its position in the application's control hierarchy. Each XML tag represents one level in the hierarchy.

### Tag Types

| Tag | Represents | Found In |
|---|---|---|
| `<wnd>` | Window (Win32/WPF/Java) | Desktop applications |
| `<ctrl>` | Control inside a window | Desktop applications |
| `<html>` | Browser window/document | Web applications |
| `<webctrl>` | HTML element | Web applications |
| `<java>` | Java component | Java applications |

### Common Attributes

| Attribute | Description | Stability |
|---|---|---|
| `automationid` | Developer-assigned unique ID (WPF/UWP) | **HIGH** — rarely changes |
| `id` | HTML element ID | **HIGH** — if developer-assigned (not auto-generated) |
| `name` | Control name | **MEDIUM** — stable for named controls |
| `role` | ARIA role or control type (button, edit, combobox) | **MEDIUM** — describes function, not instance |
| `aaname` | Accessible name (screen reader text) | **MEDIUM** — may change with UI text changes |
| `cls` | Window class name | **MEDIUM** — stable within app version |
| `tag` | HTML tag (input, div, span, a) | **LOW** — too generic for identification |
| `parentid` | Parent element's ID | **MEDIUM** — depends on parent stability |
| `idx` | Positional index among siblings | **VERY LOW** — breaks when UI order changes |
| `title` | Window title | **LOW** — often contains dynamic data |

### Selector Example (Web)

```xml
<html app='chrome.exe' title='Invoice Portal*' />
<webctrl id='txtInvoiceNumber' tag='INPUT' />
```

### Selector Example (Desktop)

```xml
<wnd app='notepad.exe' cls='Notepad' title='Untitled*' />
<ctrl name='Text Editor' role='edit' />
```

---

## 2. Attribute Stability Ranking

When multiple attributes are available, prefer the most stable ones:

1. **automationid** — best for WPF/UWP apps; developer-assigned, rarely changes
2. **id** — best for web apps with stable IDs (not auto-generated like `id='ember-1234'`)
3. **name** — good for named controls in desktop apps
4. **role** — good as supporting attribute (not unique alone)
5. **aaname** — acceptable when other stable attributes unavailable
6. **cls** — use for window-level identification
7. **tag** — too generic alone; use only with other attributes
8. **idx** — **AVOID** — breaks when siblings are added/removed/reordered

### Rules

1. **NEVER rely solely on `idx`** — positional indices break when the UI changes. If `idx` is the only distinguishing attribute, use Anchor Base instead.
2. **Avoid auto-generated IDs** — IDs like `ember-1234`, `react-abc123`, or `__ID0` change between sessions
3. **Prefer `automationid` over `name`** — both identify the control, but `automationid` is more stable across UI updates
4. **Combine 2-3 attributes** for robust identification — e.g., `role='button' aaname='Submit'` is stronger than either alone

---

## 3. Full vs Partial Selectors

### Full Selector

Includes the top-level window tag. Used when the activity is NOT inside a container scope.

```xml
<wnd app='notepad.exe' cls='Notepad' title='*' />
<ctrl name='Text Editor' role='edit' />
```

### Partial Selector

Omits the top-level window tag. Used ONLY inside a container scope (Attach Window, Attach Browser, Open Browser, Open Application).

```xml
<!-- Inside Attach Browser for chrome.exe -->
<webctrl id='txtInvoiceNumber' tag='INPUT' />
```

### When to Use Each

| Context | Selector Type | Why |
|---|---|---|
| Activity is standalone (no container) | Full selector | Must identify the window + element |
| Activity is inside Attach Browser | Partial selector | Container already identifies the browser window |
| Activity is inside Attach Window | Partial selector | Container already identifies the app window |
| Activity is inside Open Application | Partial selector | Container already identifies the app window |

### Rule

**ALWAYS use container scopes (Attach Browser/Window) with partial selectors inside** — this is more reliable than full selectors on every activity because:
1. The window identification is done once (in the container)
2. If the window title changes, you fix it in one place
3. Partial selectors are shorter and less fragile

---

## 4. Dynamic Selector Strategies

### Wildcards

Use `*` to match any text in a dynamic attribute portion:

```xml
<!-- Window title changes with document name -->
<wnd app='excel.exe' title='* - Excel' />

<!-- Button text includes dynamic count -->
<webctrl aaname='Show Results (*)' tag='BUTTON' />
```

### Variables in Selectors

Inject VB.NET variables into selectors using `{{variableName}}` syntax:

```xml
<!-- Select a specific row by customer name -->
<webctrl aaname='{{customerName}}' tag='TD' />

<!-- Dynamic window title -->
<wnd app='sap.exe' title='{{sapTransactionCode}} *' />
```

In XAML, this looks like:
```xml
<ui:Click Selector="&lt;html app='chrome.exe' /&gt;&lt;webctrl aaname='{{customerName}}' tag='TD' /&gt;" />
```

### Rules

1. **Use wildcards for known-dynamic portions** — window titles with filenames, buttons with counts, timestamps
2. **Use variables for data-driven selection** — customer names, invoice numbers, row identifiers
3. **Don't wildcard everything** — `<webctrl aaname='*' tag='*' />` matches every element; keep enough specificity

---

## 5. Anchor Base Pattern

When a target element has no stable selector, use a nearby stable element (the anchor) as reference.

### Structure

```
Anchor Base
  ├── Anchor: Find Element (stable label/header near the target)
  │   └── Selector: <webctrl aaname='Invoice Amount' tag='LABEL' />
  └── Action: Get Text / TypeInto / Click (target element)
      └── Selector: <webctrl tag='INPUT' />
```

### When to Use

1. Target element has only `idx` or auto-generated ID
2. Multiple identical elements on the page (e.g., multiple "Edit" buttons)
3. Element position changes relative to page but stays fixed relative to its label
4. Data-driven forms where the field structure is consistent but selectors are not

### Rules

1. **The anchor must be unique and stable** — labels, headers, static text
2. **Anchor and target must be visually close** — the Anchor Base finds the nearest matching target relative to the anchor
3. **Set AnchorPosition** if needed — Top, Bottom, Left, Right, Auto (Auto works for most cases)

---

## 6. Container Scope Strategy

Structure UI automation workflows with container scopes to reduce selector fragility and improve readability.

### Recommended Pattern

```
Sequence "Process Invoice in Web Portal"
  ├── Attach Browser (selector: <html app='chrome.exe' title='Invoice Portal*' />)
  │   ├── TypeInto "Invoice Number" (partial: <webctrl id='txtInvoice' />)
  │   ├── TypeInto "Amount" (partial: <webctrl id='txtAmount' />)
  │   ├── Click "Submit" (partial: <webctrl id='btnSubmit' />)
  │   └── Element Exists "Success" (partial: <webctrl id='lblSuccess' />)
```

### Rules

1. **One container per application window** — don't nest Attach Browser inside Attach Browser
2. **Use partial selectors inside containers** — shorter, less fragile, window identification handled by container
3. **Check App State or Element Exists before acting** — verify the app is ready before clicking

---

## 7. Selector Validation Checklist

When generating XAML with selectors, verify:

1. [ ] No reliance on `idx` attribute alone — use stable attributes or Anchor Base
2. [ ] Window title uses wildcard for dynamic portions — `title='Invoice*'` not `title='Invoice #12345'`
3. [ ] No auto-generated IDs — avoid `id='ember-1234'`, `id='__ID0'`
4. [ ] Container scope used for multiple actions on same window — Attach Browser/Window with partial selectors
5. [ ] Variables used for data-driven selectors — `{{variableName}}` syntax
6. [ ] Special characters escaped in XAML — `&lt;` for `<`, `&gt;` for `>`, `&amp;` for `&`, `&quot;` for `"`
7. [ ] Web selectors start with `<html>` tag (full) or `<webctrl>` tag (partial)
8. [ ] Desktop selectors start with `<wnd>` tag (full) or `<ctrl>` tag (partial)

---

## 8. Frames and iFrames

Web pages with frames or iFrames have nested document contexts. Selectors must include the frame boundary.

### Identifying Frame Selectors

```xml
<!-- Main page element -->
<html app='chrome.exe' title='Portal' />
<webctrl id='mainContent' tag='DIV' />

<!-- Element INSIDE an iFrame -->
<html app='chrome.exe' title='Portal' />
<webctrl tag='IFRAME' id='contentFrame' />        <!-- frame boundary -->
<webctrl id='txtField' tag='INPUT' />              <!-- element inside frame -->
```

### Rules

1. **Each iFrame adds a `<webctrl>` tag level** in the selector pointing to the IFRAME element
2. **Nested iFrames add multiple levels** — each frame boundary is a separate `<webctrl>` tag
3. **Frame IDs may be dynamic** — use `name` attribute or wildcard if `id` changes

---

## 9. Common Selector Patterns by Platform

### Desktop Application (Win32)

```xml
<wnd app='notepad.exe' cls='Notepad' title='*' />
<ctrl name='Text Editor' role='edit' />
```

### Web — Chrome

```xml
<html app='chrome.exe' title='My Application*' />
<webctrl id='submitBtn' tag='BUTTON' />
```

### Web — Edge

```xml
<html app='msedge.exe' title='My Application*' />
<webctrl id='submitBtn' tag='BUTTON' />
```

### Java Application

```xml
<wnd app='java.exe' cls='SunAwtFrame' title='*' />
<ctrl role='push button' name='OK' />
```

### SAP GUI

```xml
<wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' title='SAP*' />
<ctrl automationid='usr/txtRSYST-MESSION' />
```

### Citrix/RDP (Virtual Desktop)

Standard selectors do NOT work inside Citrix/RDP sessions. Use:
1. **Image-based automation** — Click Image, Find Image
2. **OCR-based automation** — Get OCR Text, Click OCR Text
3. **Citrix extension** (if available) — provides native selectors inside the virtual session

---

## 10. Object Repository Concepts

For teams managing many UI automations against the same applications, the Object Repository centralizes selector management.

### Hierarchy

```
Application (e.g., "InvoicePortal")
  └── Screen (e.g., "LoginPage", "InvoiceListing")
      └── UI Element (e.g., "UsernameField", "SubmitButton")
          └── UI Descriptor (selector + fuzzy selector + image + anchor)
```

### Naming Convention

`[ApplicationName].[ScreenName].[ElementName]` — e.g., `InvoicePortal.LoginPage.UsernameField`

### UI Libraries

Object Repository descriptors can be published as **UI Libraries** — NuGet packages that other projects consume. When a selector changes, update the UI Library once and all consuming projects get the fix.

### Multiple Targeting Strategies

A UI Descriptor can include multiple targeting methods for resilience:
1. **Strict selector** — exact match (primary)
2. **Fuzzy selector** — attribute-flexible match (fallback)
3. **Image** — visual match (fallback when selectors fail)
4. **Anchor** — relative to nearby stable element

### When to Use Object Repository

- Team maintains 5+ automations against the same application
- Application undergoes frequent UI changes
- Multiple developers work on automations for the same application
- Organization wants centralized selector management

---

## UIAutomation Activities Reference

### Overview
Legacy desktop UI automation for Windows. Click, type, find elements, manage windows/browsers. Package: `UiPath.UIAutomation.Activities`.

---

### Input Methods

| Method | Constant | Speed | Reliability | Special Keys | Notes |
|--------|----------|-------|-------------|--------------|-------|
| Hardware Events (default) | SYNTHESIZE_INPUT | Slow | Most reliable | YES | Acquires input lock, blocks user input |
| Window Messages | WINDOW_MESSAGES | Fast | Least reliable | YES | Best for classic Win32 apps |
| UI Automation API | API | Medium | Very reliable | **NO** | SimulateClick/SimulateType; bypasses input |

**CRITICAL: Cannot use SimulateClick AND SendWindowMessages simultaneously**
**SimulateType + special keys produces design-time WARNING** (not hard error)

---

### Key Activities

#### Mouse
| Activity | Key Arguments | Defaults |
|----------|---------------|----------|
| `Click` | ClickType (Single/Double/Down/Up), MouseButton (Left/Right/Middle), KeyModifiers, CursorPosition, SimulateClick, SendWindowMessages | AlterIfDisabled=true |
| `Hover` | CursorPosition, SimulateHover, SendWindowMessages | Hover duration ~1000ms |

#### Keyboard
| Activity | Key Arguments | Defaults |
|----------|---------------|----------|
| `TypeInto` | Text, SimulateType, SendWindowMessages, Activate, ClickBeforeTyping, EmptyField, DelayBetweenKeys | Activate=true, AlterIfDisabled=true |
| `TypeSecureText` | SecureText (SecureString) | Special keys escaped in non-Simulate mode |
| `SendHotkey` | Key, SpecialKey, KeyModifiers | Activate=true |

#### Element Search
| Activity | Key Arguments | Key Gotcha |
|----------|---------------|------------|
| `Element Exists` | Target | **Returns false instead of throwing on timeout** |
| `Find Children` | Target, Filter, Scope | Returns lazy IEnumerable |
| `Find Relative` | Target, CursorPosition (offset) | Returns first element at coordinates |
| `Get Ancestor` | Target, UpLevels | Returns null at root |
| `Wait Element Appear` | Target, WaitVisible, WaitActive | Adaptive polling: 50ms -> 200ms -> 1000ms |
| `Wait Element Vanish` | Target, WaitNotVisible | Returns silently on timeout |

#### Element Attributes
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

#### Actions
| Activity | Purpose |
|----------|---------|
| `Activate` | Bring window to foreground |
| `Set Focus` | Set keyboard focus (doesn't foreground) |
| `Highlight` | Debug visualization (blocking for duration) |
| `Take Screenshot` | Capture element as Image |

#### Scopes
| Activity | Key Arguments |
|----------|---------------|
| `Open Browser` | Url, BrowserType (IE/Chrome/Firefox/Edge), Private, NewSession, Hidden, CommunicationMethod |
| `Open Application` | Selector, FileName, Arguments, WorkingDirectory |
| `Window Scope` | Selector OR Window (mutually exclusive) |
| `Browser Scope` | Selector OR Browser (mutually exclusive) |

---

### Special Key Syntax (TypeInto)
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

**Authoring rule:** when any of these tokens appears in `Text`, write the value with child element syntax — not attribute form. The attribute form `Text="[&quot;13700132[k(enter)]&quot;]"` runs correctly but the value will not render in Studio because the literal `[` / `]` inside the string collide with the outer VB expression markers. Use:

```xml
<uix:NTypeInto ...>
  <uix:NTypeInto.Text>
    <InArgument x:TypeArguments="x:String">["13700132[k(enter)]"]</InArgument>
  </uix:NTypeInto.Text>
</uix:NTypeInto>
```

See [../ui-automation-guide.md § XAML-Specific Pitfalls](../ui-automation-guide.md) — "NTypeInto `Text` with literal `[k(...)]` special-key tokens" — for alternatives (`Chr(91)`/`Chr(93)` construction, split-activity).

---

### Critical Gotchas

#### AlterIfDisabled Default
1. **AlterIfDisabled=true by default** on Click, TypeInto, SetValue, SelectItem, Check - can interact with disabled/grayed controls unexpectedly

#### TypeInto Specifics
2. **SimulateType CANNOT handle special keys** - fails validation if `[k(...)]` syntax detected
3. **EmptyField uses hardcoded sequence**: `[k(end)d(shift)k(home)u(shift)k(del)]` - may fail for multi-line. **CRITICAL: EmptyField is silently ignored when SimulateType=true** - only works with hardware events and SendWindowMessages
4. **DelayBetweenKeys max 1000ms** - validation error if exceeded
5. **Activate=true by default** - may cause unwanted window switches

#### Selector Issues
6. **Selector matching is fragile** - UI changes invalidate selectors
7. **Placeholders** `{varName}` resolved at runtime - null variables cause failures
8. **Closest matches** can return wrong element if multiple similar elements exist
9. **Closest matches disabled in Exists** activity (returns false cleanly)

#### Click Specifics
10. **SimulateClick cannot CLICK_DOUBLE with BTN_RIGHT or BTN_MIDDLE**
11. **SimulateClick doesn't acquire input lock** - others do
12. **CursorMotionType** affects how cursor moves (straight line, smooth, etc.)

#### Timing
13. **Default timeout ~30,000ms** (30 seconds) across most activities
14. **DelayBefore/DelayAfter are sequential** (Thread.Sleep internally)
15. **WaitUiElementAppear adaptive polling**: 50ms -> 200ms -> 1000ms
16. **Exists returns false instead of throwing** on timeout

#### Browser Scope
17. **NewSession=true (default)** creates new browser process (slower but isolated)
18. **NewSession=false** reuses existing browser (faster, shared state/cookies)
19. **Private mode** may disable extensions/drivers
20. **CommunicationMethod**: Native (UiPath driver) vs WebDriver (Selenium-based)

#### Window/Browser Scope Validation
21. **Must set either Selector OR Window/Browser** - not both, not neither
22. **If Window/Browser set, SearchScope cannot be set**

#### Image-Based Activities
23. **Template matching** (not AI) - sensitive to resolution, brightness, minor UI changes
24. **Slower than selector-based** - use only for unstable selectors

#### Error Handling
25. **ContinueOnError=false by default** - exceptions thrown
26. **Governance exceptions never suppressed** even with ContinueOnError=true

#### Additional Validated Gotchas
27. **OpenBrowser defaults to IE** - BrowserType default is `BrowserType.IE`
28. **Hover has fixed 1000ms duration** - hardcoded, not configurable
29. **Default timeouts**: Timeout=30,000ms, DelayAfter=300ms, DelayBefore=200ms, OpenBrowser=60s
30. **AlterIfDisabled NOT passed to node in hardware events mode for TypeInto** (but IS passed for Click) - inconsistent behavior
31. **CursorMotionType.Smooth only works with hardware events** - has no effect with SimulateClick or SendWindowMessages
32. **Data Scraping hardcodes ContinueOnError=true** - extraction failures produce empty DataTable, no error
33. **SimulateClick MV3 workaround** - hidden project setting `EnableWorkaroundForSimulateClickMV3` (default false) needed for Chrome Manifest V3 extensions
34. **Image OCR uses hardcoded 5-pixel offset** - can cause incorrect crops on small images
