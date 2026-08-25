# UiPath Forms Activities - Legacy Reference

## Overview
HTML/FormIo-based forms for user interaction. Supports async/modal display, field binding, events, and triggers. Package: `UiPath.Forms.Activities`.

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `ShowFormActivity` | Display form (async or modal) | FormId, InstanceName, Arguments (Dict), Width, Height, Left, Top, Title, IsAsync (default true) |
| `CloseFormActivity` | Close open form | FormId, InstanceName |
| `HideFormActivity` | Minimize/hide form | FormId, InstanceName |
| `BringFormToFrontActivity` | Restore hidden form | FormId, InstanceName |
| `GetFormFieldsActivity` | Read current field values | FormId, InstanceName, Arguments (Dict\<string, OutArgument\>) |
| `SetFormFieldsActivity` | Set field values | FormId, InstanceName, Arguments (Dict\<string, InArgument\>) |
| `ChangeFormPropertiesActivity` | Modify form at runtime | FormId, InstanceName, Height, Width, Title, WindowState, TopMost |
| `ExecuteScriptActivity` | Run JavaScript in form | FormId, InstanceName, Source (JS code) |
| `FormTriggerActivity<T>` | Listen for form events | FormId, InstanceName, Event (e.g., "button1.click"), MessageId |
| `ShowCalloutActivity` | Popup near UI element | Target/UiElement, AutomaticallyCloseAfter, all ShowForm args |

---

## FormIo Type Mapping

| FormIo Component | C# Type |
|-----------------|---------|
| Checkbox | bool |
| Number / Currency | double |
| Password | SecureString |
| DataGrid / EditGrid | DataTable |
| DateTime | DateTime |
| Date | DateOnly |
| Time | TimeOnly |
| Survey / DataMap | Dictionary\<string, string\> |
| Select (multiple) | IEnumerable\<string\> |
| Select (single) | string |
| Default | string |

---

## Critical Gotchas

### Form Display
1. **IsAsync=true (default)** - returns immediately; form runs in background
2. **IsAsync=false** - blocks workflow until form closes
3. **DuplicateBehavior=ReuseExisting** by default - same FormId+InstanceName reuses form
4. **FormSelectorNotUnique exception** if FormId+InstanceName conflict exists

### Arguments Binding
5. **Arguments dictionary maps field IDs to workflow variables** (In/Out/InOut)
6. **Global variables** bound via `GlobalVariables.PropertyName` regex pattern
7. **Type coercion** uses `Convert.ChangeType()` - arrays parsed via string splitting
8. **Complex types/objects fail** with FormsRuntimeException(InvalidArgument)

### Platform Limitations
9. **ExternalHost (Assistant/Robot)**: HTML forms only - FormIo/native forms throw NotSupportedException
10. **Desktop**: Requires WebView2 runtime installed
11. **WebSocket URI hardcoded** to `ws://127.0.0.1:29831` (not localhost, to avoid IPv6 2-second timeout)

### Async Patterns
12. **async void methods with #pragma warning disable** - unhandled exceptions are catastrophic
13. **Try/catch wraps to TaskCompletionSource.SetException()** for safety

### Timeouts
14. **FormLoadTimeout = 10 seconds** - configurable but soft-enforced
15. **GetValueTimeout / InitializeTimeout = 10 seconds**

### Form Selection
16. **Wildcard-based matching** - missing selector fields match any value
17. **Multiple matches throw exception** (not silent failure)

### Form Files
18. **Extension**: `.uiform` (native FormIo) or `.html` (raw HTML)
19. **Form ID resolution** via Constants.IdMapFileName probed relative to assembly

### Callout Activity
20. **ShowCalloutActivity integrates with UIAutomationNext** for target tracking
21. **Defaults**: Width=300, Height=280, ShowMargin=false, ShowInTaskbar=false
22. **ContinueOnError=true by default** (unlike ShowFormActivity)
