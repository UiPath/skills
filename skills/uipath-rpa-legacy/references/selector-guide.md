# Selector Guide

Selector anatomy, strategy, and best practices for building reliable UI automation in legacy UiPath workflows.

For UI automation activities (Click, TypeInto, etc.), see [activity-docs/UIAutomation.md](./activity-docs/UIAutomation.md).
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
