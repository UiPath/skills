# UI Automation Portable API Reference

Reference for the `uiAutomation` service from the `UiPath.UIAutomationNext.Portable.API` package.

**Auto-imported namespaces:** `System`, `UiPath.UIAutomationNext.API.Contracts`, `UiPath.UIAutomationNext.Enums`, `UiPath.UIAutomationNext.API.Models`

**Service accessor:** `uiAutomation` (type `IUiAutomationAppService`)

---

## Overview

The Portable API is a .NET 6.0 portable subset of the full UI Automation API. It provides the same programmatic interface for coded workflows to interact with desktop applications, web browsers, and SAP. All files are linked from `UiPath.UIAutomationNext.API`, ensuring API surface parity.

### Workflow Pattern

1. **Open** or **Attach** to an application screen via `uiAutomation` — returns a `UiTargetApp` handle.
2. Use the `UiTargetApp` handle to perform element interactions (Click, TypeInto, GetText, etc.).
3. `UiTargetApp` implements `IDisposable` — always use `using` blocks or dispose manually.

```csharp
using var app = uiAutomation.Attach("MainScreen");
app.Click("submitButton");
string value = app.GetText("outputField");
```

### Target Resolution

Each method on `UiTargetApp` accepts targets in these forms:

- **`string target`** — a target name defined in the Object Repository screen.
- **`IElementDescriptor elementDescriptor`** — a strongly-typed Object Repository descriptor (e.g., `Descriptors.MyApp.Screen.Element`).
- **`TargetAnchorableModel target`** — accessed via the `UiTargetApp` indexer: `app["targetName"]` or `app[descriptor]`.
- **`RuntimeTarget target`** — a runtime reference returned by `GetChildren` or `GetRuntimeTarget`.

### Options Pattern

Most operations accept an optional `*Options` parameter. Use the `Options` static class for fluent builder creation:

```csharp
// Simple — uses defaults
app.Click("myButton");

// With options
app.Click("myButton", Options.Click(NClickType.Double, NMouseButton.Left)
    .With(keyModifiers: NKeyModifiers.Ctrl)
    .WithTimeouts(timeout: 10));
```

---

## Options Base Classes

All option classes follow this inheritance hierarchy:

```
ContinuableActivityOptions          → ContinueOnError, HealingAgentBehavior
  └─ ActivityWithVariablesOptions   → Variables dictionary
       └─ TargetOptions             → Timeout, DelayAfter, DelayBefore
            └─ [Specific Options]   → Action-specific properties
```

### ContinuableActivityOptions (abstract base)

| Property | Type | Default | Description |
|---|---|---|---|
| `ContinueOnError` | `bool` | `false` | Continue automation even when the activity throws an error |
| `HealingAgentBehavior` | `NChildHealingAgentBehavior` | — | Healing agent behavior for self-healing selectors |

### ActivityWithVariablesOptions (abstract, extends ContinuableActivityOptions)

| Property | Type | Default | Description |
|---|---|---|---|
| `Variables` | `Dictionary<string, string>` | empty | Variables for placeholder substitution in selectors |

### TargetOptions (abstract, extends ActivityWithVariablesOptions)

| Property | Type | Default | Description |
|---|---|---|---|
| `Timeout` | `double` | 30 | Maximum time (seconds) to find the element before throwing `SelectorNotFoundException` |
| `DelayAfter` | `double` | 0.3 | Delay (seconds) after executing the activity |
| `DelayBefore` | `double` | 0.2 | Delay (seconds) before the activity begins |

### Common Extension Methods on Options

```csharp
// Set timeouts on any option that implements IWithTimeouts
options.WithTimeouts(timeout: 10, delayAfter: 0.5, delayBefore: 0.1);

// Continue on error
options.WithContinueOnError(true);

// Add a variable for selector placeholder substitution
options.WithVariable("varName", "varValue");

// Verify execution (on options implementing IWithVerify: Click, TypeInto, Hover, KeyboardShortcut)
options.Until("verifyTargetName", until: NVerifyMode.Appears, retry: true, timeout: 2);
options.Until(targetAnchorableModel, until: NVerifyMode.Appears, retry: true, timeout: 2);

// Get the output UiElement after execution
options.GetUiElement(element => myUiElement = element);
```

---

## IUiAutomationAppService — Top-Level Service

Accessed via the `uiAutomation` service accessor. All methods have both sync and async variants.

### Attach — Attach to an Already Open Application

```csharp
// Using Object Repository screen name
UiTargetApp Attach(string screenName,
    string appName = "***",
    string appVersion = "***",
    NAppAttachMode appAttachMode = NAppAttachMode.ByInstance,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents);

// Using Object Repository screen name with options
UiTargetApp Attach(string screenName,
    TargetAppOptions targetAppOptions,
    string appName = "***",
    string appVersion = "***");

// Using screen descriptor (strongly-typed Object Repository)
UiTargetApp Attach(IScreenDescriptor screenDescriptor,
    NAppAttachMode appAttachMode = NAppAttachMode.ByInstance,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents);

// Using screen descriptor with options
UiTargetApp Attach(IScreenDescriptor screenDescriptor,
    TargetAppOptions targetAppOptions);

// Using a TargetAppModel (programmatic target)
UiTargetApp Attach(TargetAppModel targetApp,
    TargetAppOptions targetAppOptions = null);
```

**Async variants:** `AttachAsync(...)` — same signatures, returns `Task<UiTargetApp>`.

#### Examples

```csharp
// Attach via Object Repository
using var app = uiAutomation.Attach("LoginScreen");

// Attach with options
using var app = uiAutomation.Attach("LoginScreen",
    Options.AppAttach(NAppAttachMode.ByInstance, timeout: 60));

// Attach using typed descriptor
using var app = uiAutomation.Attach(Descriptors.MyApp.LoginScreen);

// Attach to a web app using TargetAppModel
var target = AppTarget.FromUrl("https://example.com", "<html .../>", NBrowserType.Chrome);
using var app = uiAutomation.Attach(target);
```

### Open — Open an Application

```csharp
UiTargetApp Open(string screenName,
    string appName = "***",
    string appVersion = "***",
    NAppOpenMode openMode = NAppOpenMode.IfNotOpen,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents);

UiTargetApp Open(string screenName,
    TargetAppOptions targetAppOptions,
    string appName = "***",
    string appVersion = "***");

UiTargetApp Open(IScreenDescriptor screenDescriptor,
    NAppOpenMode openMode = NAppOpenMode.IfNotOpen,
    NWindowResize windowResize = NWindowResize.None,
    NInteractionMode interactionMode = NInteractionMode.HardwareEvents);

UiTargetApp Open(IScreenDescriptor screenDescriptor,
    TargetAppOptions targetAppOptions);

UiTargetApp Open(TargetAppModel targetApp,
    TargetAppOptions targetAppOptions = null);
```

**Async variants:** `OpenAsync(...)` — same signatures, returns `Task<UiTargetApp>`.

#### Examples

```csharp
// Open via Object Repository
using var app = uiAutomation.Open("MainScreen");

// Open with specific mode
using var app = uiAutomation.Open("MainScreen",
    Options.AppOpen(openMode: NAppOpenMode.Always, windowResize: NWindowResize.Maximize));

// Open from file path
var target = AppTarget.FromPath(@"C:\Program Files\MyApp\app.exe");
using var app = uiAutomation.Open(target, Options.AppOpen());
```

### Global Operations (not tied to a UiTargetApp)

```csharp
// Send keyboard shortcuts (not element-specific)
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions);
Task KeyboardShortcutAsync(KeyboardShortcutOptions keyboardShortcutOptions);

// Take a screenshot of the entire screen
void TakeScreenshot(TakeScreenshotOptions takeScreenshotOptions);
Task TakeScreenshotAsync(TakeScreenshotOptions takeScreenshotOptions);

// Direct Click/TypeInto/Hover/GetText/Highlight/SelectItem on a UiElement
void Click(UiElement uiElement, ClickOptions clickOptions = null);
Task ClickAsync(UiElement uiElement, ClickOptions clickOptions = null);
void TypeInto(UiElement uiElement, TypeIntoOptions typeIntoOptions);
Task TypeIntoAsync(UiElement uiElement, TypeIntoOptions typeIntoOptions);
void Hover(UiElement uiElement, HoverOptions hoverOptions = null);
Task HoverAsync(UiElement uiElement, HoverOptions hoverOptions = null);
string GetText(UiElement uiElement, GetTextOptions options = null);
Task<string> GetTextAsync(UiElement uiElement, GetTextOptions options = null);
void Highlight(UiElement uiElement, HighlightOptions highlightOptions = null);
Task HighlightAsync(UiElement uiElement, HighlightOptions highlightOptions = null);
void SelectItem(UiElement uiElement, SelectItemOptions options);
Task SelectItemAsync(UiElement uiElement, SelectItemOptions options);

// Get a UiElement from a RuntimeTarget
UiElement GetUiElement(RuntimeTarget target);
Task<UiElement> GetUiElementAsync(RuntimeTarget target);

// Set runtime browser
void SetDefaultRuntimeBrowser();
Task SetDefaultRuntimeBrowserAsync();
void SetRuntimeBrowser(NBrowserType browserType);
Task SetRuntimeBrowserAsync(NBrowserType browserType);
void SetRuntimeBrowser(SetRuntimeBrowserOptions setRuntimeBrowserOptions);
Task SetRuntimeBrowserAsync(SetRuntimeBrowserOptions setRuntimeBrowserOptions);

// Clipboard
string GetClipboard(GetClipboardOptions options);
Task<string> GetClipboardAsync(GetClipboardOptions options);
void SetClipboard(SetClipboardOptions setClipboardOptions);
Task SetClipboardAsync(SetClipboardOptions setClipboardOptions);

// Wait for element state (uses IElementDescriptor from Object Repository)
bool WaitState(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
Task<bool> WaitStateAsync(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
```

---

## UiTargetApp — Application Handle Methods

`UiTargetApp` is the synchronous wrapper returned by `Attach`/`Open`. It wraps `RuntimeTargetApp` and provides both sync and async methods. All methods on `UiTargetApp` accept targets as `string` (Object Repository name), `IElementDescriptor`, `TargetAnchorableModel`, or `RuntimeTarget`.

### Indexer

```csharp
// Get a TargetAnchorableModel by name
TargetAnchorableModel target = app["targetName"];

// Get a TargetAnchorableModel by descriptor
TargetAnchorableModel target = app[Descriptors.MyApp.Screen.Element];
```

### Click

```csharp
void Click(string target, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left);
void Click(string target, ClickOptions clickOptions);
void Click(IElementDescriptor elementDescriptor, NClickType clickType = NClickType.Single, NMouseButton mouseButton = NMouseButton.Left);
void Click(IElementDescriptor elementDescriptor, ClickOptions clickOptions);
// Async: ClickAsync(...)
```

#### ClickOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `ClickType` | `NClickType` | `Single` | Single, Double, Down, or Up |
| `MouseButton` | `NMouseButton` | `Left` | Left, Right, or Middle |
| `KeyModifiers` | `NKeyModifiers` | `None` | None, Alt, Ctrl, Shift, Win |
| `CursorMotionType` | `CursorMotionType` | `Instant` | Instant or Smooth |
| `AlterIfDisabled` | `bool` | `false` | Execute action even if element is disabled |
| `ActivateBefore` | `bool` | `true` | Bring element to foreground before clicking |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | SameAsCard, HardwareEvents, SimulateEvents |
| `UnblockInput` | `bool` | `false` | Unblock input when Click triggers a modal dialog. Only works with Simulate Click |
| `VerifyOptions` | `VerifyOptions` | `null` | Verify execution after action |

**Builder:** `Options.Click(NClickType clickType = Single, NMouseButton mouseButton = Left)`

```csharp
app.Click("button");
app.Click("button", Options.Click(NClickType.Double).With(keyModifiers: NKeyModifiers.Ctrl));
```

### TypeInto

```csharp
void TypeInto(string target, string text);
void TypeInto(string target, SecureString secureText);
void TypeInto(string target, TypeIntoOptions typeIntoOptions);
void TypeInto(IElementDescriptor elementDescriptor, string text);
void TypeInto(IElementDescriptor elementDescriptor, TypeIntoOptions typeIntoOptions);
// Async: TypeIntoAsync(...)
```

#### TypeIntoOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Text` | `string` | — | The text to enter |
| `SecureText` | `SecureString` | — | The secure text to enter |
| `DelayBetweenKeys` | `double` | project setting | Delay (seconds) between keystrokes (max 1s) |
| `ActivateBefore` | `bool` | `true` | Bring element to foreground before typing |
| `ClickBeforeMode` | `NClickMode` | project setting | Click the field before typing: None, Single, Double |
| `EmptyFieldMode` | `NEmptyFieldMode` | project setting | Clear the field before typing |
| `ClipboardMode` | `NTypeByClipboardMode` | project setting | Whether to use clipboard for typing |
| `DeselectAfter` | `bool` | `false` | Add a Complete event after text entry |
| `AlterIfDisabled` | `bool` | `false` | Execute action even if element is disabled |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction method |
| `VerifyOptions` | `VerifyOptions` | `null` | Verify execution after action |

**Builder:** `Options.TypeInto(string text)` or `Options.TypeInto(SecureString secureText)`

```csharp
app.TypeInto("emailField", "user@example.com");
app.TypeInto("emailField", Options.TypeInto("user@example.com")
    .With(emptyFieldMode: NEmptyFieldMode.SingleLine, delayBetweenKeys: 0.05));

// Verify typing was correct
app.TypeInto("emailField", Options.TypeInto("user@example.com")
    .UntilText(expectedText: "user@example.com", retry: true, timeout: 5));
```

### GetText

```csharp
string GetText(string target);
string GetText(string target, GetTextOptions getTextOptions);
string GetText(IElementDescriptor elementDescriptor);
string GetText(IElementDescriptor elementDescriptor, GetTextOptions getTextOptions);
// Async: GetTextAsync(...)
```

#### GetTextOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `ScrapingOptions` | `NScrapingOptions` | `None` | None, AllowFormatting, IgnoreHiddenText, GetWordsCoordinates |
| `ScrapingMethod` | `NScrapingMethod` | `Default` | Default, TextAttribute, Fulltext, Native |

**Builder:** `Options.GetText(NScrapingOptions scrapingOptions = None, NScrapingMethod scrapingMethod = Default)`

```csharp
string text = app.GetText("outputField");
string text = app.GetText("outputField", Options.GetText(NScrapingMethod.Native));
```

### Hover

```csharp
void Hover(string target, double hoverTime, CursorMotionType cursorMotionType);
void Hover(string target, HoverOptions hoverOptions);
void Hover(IElementDescriptor elementDescriptor, HoverOptions hoverOptions);
// Async: HoverAsync(...)
```

#### HoverOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `HoverTime` | `double` | 0 | Seconds to hover the element |
| `CursorMotionType` | `CursorMotionType` | `Instant` | Instant or Smooth |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction method |
| `VerifyOptions` | `VerifyOptions` | `null` | Verify execution after action |

**Builder:** `Options.Hover(double? hoverTime = null, CursorMotionType cursorMotionType = Instant, NChildInteractionMode interactionMode = SameAsCard)`

### SelectItem

```csharp
void SelectItem(string target, string item);
void SelectItem(string target, SelectItemOptions selectItemOptions);
void SelectItem(IElementDescriptor elementDescriptor, string item);
void SelectItem(IElementDescriptor elementDescriptor, SelectItemOptions selectItemOptions);
// Async: SelectItemAsync(...)
```

#### SelectItemOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Item` | `string` | — | The name of the item to select |
| `AlterIfDisabled` | `bool` | `false` | Execute even if element is disabled |

**Builder:** `Options.SelectItem(string item)`

```csharp
app.SelectItem("countryDropdown", "United States");
```

### Check

```csharp
void Check(string target, NCheckType checkType = NCheckType.Check);
void Check(string target, CheckOptions checkOptions);
void Check(IElementDescriptor elementDescriptor, NCheckType checkType = NCheckType.Check);
// Async: CheckAsync(...)
```

#### CheckOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `CheckType` | `NCheckType` | `Check` | Check, Uncheck, or Toggle |
| `AlterIfDisabled` | `bool` | `false` | Execute even if element is disabled |

**Builder:** `Options.Check(NCheckType checkType = Check)`

### Highlight

```csharp
void Highlight(string target, KnownColor color = KnownColor.Yellow, double duration = 3);
void Highlight(string target, HighlightOptions highlightOptions);
void Highlight(IElementDescriptor elementDescriptor, HighlightOptions highlightOptions);
// Async: HighlightAsync(...)
```

#### HighlightOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `HighlightTime` | `double` | 2 | Duration (seconds) to highlight |
| `Color` | `KnownColor` | `Yellow` | Color of the highlight box |

**Builder:** `Options.Highlight(KnownColor color = Yellow, double? duration = null)`

### GetAttribute

```csharp
string GetAttribute(string target, string attribute);
string GetAttribute(string target, GetAttributeOptions getAttributeOptions);
// Async: GetAttributeAsync(...)
```

#### GetAttributeOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Attribute` | `string` | — | The name of the attribute to retrieve |

**Builder:** `Options.GetAttribute(string attribute)`

### IsEnabled

```csharp
bool IsEnabled(string target);
bool IsEnabled(string target, IsEnabledOptions isEnabledOptions);
// Async: IsEnabledAsync(...)
```

Returns `true` if the target element is enabled.

### KeyboardShortcut

```csharp
// On UiTargetApp (element-scoped)
void KeyboardShortcut(string target, string shortcuts, double delayBetweenShortcuts = 0.5);
void KeyboardShortcut(string target, KeyboardShortcutOptions keyboardShortcutOptions);
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions); // no target, global

// On uiAutomation service (global)
void KeyboardShortcut(KeyboardShortcutOptions keyboardShortcutOptions);
```

#### KeyboardShortcutOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Shortcuts` | `string` | — | The keyboard shortcut string (see format below) |
| `ActivateBefore` | `bool` | `true` | Bring element to foreground first |
| `DelayBetweenShortcuts` | `double` | project setting | Delay (seconds) between consecutive shortcuts |
| `DelayBetweenKeys` | `double` | project setting | Delay (seconds) between consecutive keys |
| `ClickBeforeMode` | `NClickMode` | `None` | Click element before sending shortcuts |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction method |
| `VerifyOptions` | `VerifyOptions` | `null` | Verify execution after action |

**Shortcut string format:** `[d(hk)][d(ctrl)]c[u(ctrl)][u(hk)]` for Ctrl+C.

**Builder helpers:**

```csharp
Options.KeyboardShortcut(string shortcuts)     // raw shortcut string
Options.KeyboardShortcutEsc()                   // Escape key
Options.KeyboardShortcutTab()                   // Tab key
Options.KeyboardShortcutCtrl(string key)        // Ctrl+key
Options.KeyboardShortcutCtrlA()                 // Ctrl+A
Options.KeyboardShortcutCtrlC()                 // Ctrl+C
Options.KeyboardShortcutCtrlV()                 // Ctrl+V
Options.KeyboardShortcutWin(string key)         // Win+key
Options.KeyboardShortcutWinM()                  // Win+M (minimize all)
```

### MouseScroll

```csharp
void MouseScroll(string target, NScrollDirection direction = Down, int movementUnits = 10);
void MouseScroll(string target, string searchedTarget, NScrollDirection direction = Down, int movementUnits = 100);
void MouseScroll(string target, MouseScrollOptions mouseScrollOptions);
// Async: MouseScrollAsync(...)
```

#### MouseScrollOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Direction` | `NScrollDirection` | `Down` | Up, Down, Left, Right |
| `MovementUnits` | `int` | 10 | Number of wheel detents to scroll |
| `KeyModifiers` | `NKeyModifiers` | `None` | Key modifier during scroll |
| `CursorMotionType` | `CursorMotionType` | `Instant` | Mouse cursor motion type |
| `InteractionMode` | `NChildInteractionMode` | `HardwareEvents` | Interaction method |
| `SearchedElement` | `SearchedElementOptions` | `null` | Element to scroll to (if set, scrolls until element is found) |

**Builder:**

```csharp
Options.MouseScroll(NScrollDirection direction = Down, int movementUnits = 10)
Options.MouseScrollToElement(TargetAnchorableModel searchedTarget, NScrollDirection direction = Down, int movementUnits = 100)
```

### DragAndDrop

```csharp
void DragAndDrop(string target, TargetAnchorableModel destinationTarget = null, ...);
void DragAndDrop(string target, DragAndDropOptions dragAndDropOptions);
// Async: DragAndDropAsync(...)
```

#### DragAndDropOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `DestinationTarget` | `TargetAnchorableModel` | `null` | The destination element to drop onto |
| `KeyModifiers` | `NKeyModifiers` | `None` | Key modifier during drag |
| `MouseButton` | `NMouseButton` | `Left` | Mouse button to use |
| `CursorMotionType` | `CursorMotionType` | `Instant` | Mouse cursor motion type |
| `UseSourceHover` | `bool` | `false` | Hover over source before dragging |
| `DelayBetweenActions` | `double` | 0 | Delay between drag and drop actions |

**Builder:** `Options.DragAndDrop(TargetAnchorableModel destinationTarget, ...)`

### GoToUrl

```csharp
void GoToUrl(string url);
void GoToUrl(GoToUrlOptions urlOptions);
// Async: GoToUrlAsync(...)
```

**Builder:** `Options.GoToUrl(string url)`

### GetUrl

```csharp
string GetUrl(GetUrlOptions getUrlOptions = null);
// Async: GetUrlAsync(...)
```

Returns the current URL of the attached browser.

### WaitState

```csharp
// On UiTargetApp (uses target name)
bool WaitState(string target, NCheckStateMode checkStateMode, double timeout);
bool WaitState(string target, CheckStateOptions checkStateOptions);

// On uiAutomation service (uses IElementDescriptor)
bool WaitState(IElementDescriptor elementDescriptor, CheckStateOptions checkStateOptions);
```

#### CheckStateOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Mode` | `NCheckStateMode` | — | `WaitAppear` or `WaitDisappear` |
| `CheckVisibility` | `bool` | `false` | Also check element visibility (not just existence) |

**Builder:**

```csharp
Options.WaitAppear(bool checkVisibility = false, double? timeout = null)
Options.WaitDisappear(bool checkVisibility = false, double? timeout = null)
Options.CheckState(NCheckStateMode mode, bool checkVisibility = false, double? timeout = null)
```

```csharp
bool appeared = app.WaitState("loadingSpinner", NCheckStateMode.WaitDisappear, timeout: 30);
```

### TakeScreenshot

```csharp
// On UiTargetApp (element-scoped)
void TakeScreenshot(string target, string fileName);
void TakeScreenshot(string target, TakeScreenshotOptions takeScreenshotOptions);

// On uiAutomation service (full screen)
void TakeScreenshot(TakeScreenshotOptions takeScreenshotOptions);
```

#### TakeScreenshotOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `FileName` | `string` | — | File path to save the screenshot |

**Builder:** `Options.TakeScreenshotToFile(string fileName)`

### GetChildren

```csharp
IEnumerable<RuntimeTarget> GetChildren(string target, string selectorFilter, bool checkRootVisibility = false, bool recursive = false, double timeout = 30);
IEnumerable<RuntimeTarget> GetChildren(string target, GetChildrenOptions getChildrenOptions);
// Async: GetChildrenAsync(...)
```

#### GetChildrenOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `SelectorFilter` | `string` | — | Selector filter to match child elements |
| `Timeout` | `double` | 30 | Timeout in seconds |
| `Recursive` | `bool` | `false` | Recursively search all descendants |
| `CheckRootVisibility` | `bool` | `false` | Check if root element is visible |

**Builder:** `Options.GetChildren(string selectorFilter, bool checkRootVisibility = false, bool recursive = false, double? timeout = null)`

### ExtractData

```csharp
DataTable ExtractData(string target, string extractMetadata, string tableSettings = "", NChildInteractionMode interactionMode = SameAsCard, LimitType limitExtractionTo = Rows, int? numberOfItems = null);
DataTable ExtractData(string target, string nextPageTarget, string extractMetadata, string tableSettings = "", double delayBetweenPages = 0.3, ...);
DataTable ExtractData(string target, ExtractDataOptions extractDataOptions);
// Async: ExtractDataAsync(...)
```

#### ExtractDataOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `ExtractMetadata` | `string` | — | Metadata defining columns and extraction rules |
| `TableSettings` | `string` | `""` | Table extraction settings |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction method |
| `LimitExtractionTo` | `LimitType` | `Rows` | Limit by Rows or Items |
| `NumberOfItems` | `int?` | `null` | Max items to extract (null = unlimited) |
| `NextPage` | `NextPageOptions` | `null` | Pagination settings |

#### ExtractTableDataOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction method |
| `LimitExtractionTo` | `LimitType` | `Rows` | Limit by Rows or Items |
| `NumberOfItems` | `int?` | `null` | Max items to extract |
| `DelayBetweenPages` | `double` | project setting | Delay between pages |

### SetValue

```csharp
void SetValue(string target, SetValueOptions setValueOptions);
// Async: SetValueAsync(...)
```

#### SetValueOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Value` | `string` | — | Value to set on the element |
| `EnableValidation` | `bool` | `false` | Validate the value was set correctly |

**Builder:** `Options.SetValue(string value)`

### FillForm

```csharp
void FillForm(object dataSource);
void FillForm(FillFormOptions fillFormOptions);
// Async: FillFormAsync(...)
```

#### FillFormOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `DataSource` | `object` | `null` | Data to fill the form with |
| `EnableValidation` | `bool` | `false` | Validate values were set correctly |

**Builder:** `Options.FillForm(object dataSource = null)`

### ClosePopup

```csharp
void ClosePopup(ClosePopupOptions closePopupOptions);
// Async: ClosePopupAsync(...)
```

#### ClosePopupOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `PreferredButtons` | `string[]` | `["Close", "Cancel"]` | Preferred button search order |
| `PopupAppearTimeout` | `double` | project setting | Timeout (seconds) waiting for popup |
| `EnableAI` | `bool` | `false` | Use AI to close the popup |

**Builder:** `Options.ClosePopup(string[] preferredButtons = null, double? popupAppearTimeout = null)`

### GetAccessibilityCheck

```csharp
string GetAccessibilityCheck(GetAccessibilityCheckOptions options = null);
// Async: GetAccessibilityCheckAsync(...)
```

Returns accessibility check results as a string.

### GetRuntimeTarget

```csharp
RuntimeTarget GetRuntimeTarget(string target, GetRuntimeTargetOptions options = null);
RuntimeTarget GetRuntimeTarget(TargetAnchorableModel targetAnchorableModel, GetRuntimeTargetOptions options = null);
// Async: GetRuntimeTargetAsync(...)
```

Resolves a target into a `RuntimeTarget` for reuse across multiple operations.

### GetUiElement

```csharp
UiElement GetUiElement(RuntimeTarget target);    // from RuntimeTarget
UiElement GetUiElement();                         // from the app itself
// Async: GetUiElementAsync(...)
```

Gets the underlying `UiElement` from a runtime reference. Available only in coded workflows.

### InjectJsScript

```csharp
string InjectJsScript(string target, InjectJsScriptOptions injectJsScriptOptions);
// Async: InjectJsScriptAsync(...)
```

#### InjectJsScriptOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `ScriptCodePath` | `string` | — | JavaScript code as string or full path to a .js file |
| `InputParameter` | `string` | `""` | Input data for the script |
| `ExecutionWorld` | `NExecutionWorld` | `Isolated` | Execution context for the script |

**Builder:** `Options.InjectJsScript(string scriptCodePath, string inputParameter = null)`

### UITask (AI Agent)

```csharp
UITaskResult UITask(UITaskOptions options = null);
// Async: UITaskAsync(...)
```

#### UITaskOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `Task` | `string` | — | Natural language description of the task to execute |
| `AgentType` | `NUITaskAgentType` | project setting | Type of AI agent |
| `InteractionMode` | `NChildInteractionMode` | `SameAsCard` | Interaction method |
| `MaxIterations` | `int` | project setting | Max iterations (0 = no limit) |
| `ClipboardMode` | `NTypeByClipboardMode` | project setting | Whether agent can use clipboard |
| `IsDOMEnabled` | `bool` | project setting | Whether agent can use native DOM |
| `IsVariableSecurityEnabled` | `bool` | `true` | Block prompt injection via variables |
| `TraceAttachMode` | `NTraceAttachMode` | project setting | Trace attach mode |

#### UITaskResult

| Property | Type | Description |
|---|---|---|
| `Status` | `string` | Task execution status |
| `Result` | `string` | Result string |
| `ErrorMessage` | `string` | Error message if failed |
| `HttpErrorStatusCode` | `string` | HTTP error status if applicable |
| `TraceFiles` | `string[]` | Trace file paths |

**Builder:** `Options.UITask(string task)`

```csharp
var result = app.UITask(Options.UITask("Click the Submit button and wait for confirmation"));
```

### SetRuntimeBrowser

```csharp
// On uiAutomation service
void SetDefaultRuntimeBrowser();
void SetRuntimeBrowser(NBrowserType browserType);
void SetRuntimeBrowser(SetRuntimeBrowserOptions setRuntimeBrowserOptions);
```

#### SetRuntimeBrowserOptions

| Property | Type | Default | Description |
|---|---|---|---|
| `BrowserType` | `NBrowserType` | — | Chrome, Edge, Firefox, Safari, IE, WebDriver |

**Builder:** `Options.SetRuntimeBrowser(NBrowserType browserType)`

### Clipboard Operations

```csharp
// On uiAutomation service
string GetClipboard(GetClipboardOptions options);
void SetClipboard(SetClipboardOptions setClipboardOptions);
```

#### SetClipboardOptions

| Property | Type | Description |
|---|---|---|
| `Text` | `string` | Text to set on the clipboard |

---

## SAP-Specific Operations

All SAP operations are available on `UiTargetApp` after attaching to a SAP window.

### SAPSelectMenuItem

```csharp
void SAPSelectMenuItem(string item);
void SAPSelectMenuItem(SelectItemOptions selectItemOptions);
```

### SAPClickToolbarButton

```csharp
void SAPClickToolbarButton(string target, string item);
void SAPClickToolbarButton(string target, SelectItemOptions selectItemOptions);
```

### SAPReadStatusbar

```csharp
SAPReadStatusbarResult SAPReadStatusbar();
SAPReadStatusbarResult SAPReadStatusbar(SAPReadStatusbarOptions readStatusbarOptions);
```

### SAPSelectDatesInCalendar

```csharp
void SAPSelectDatesInCalendar(string target, DateTime date);                     // single date
void SAPSelectDatesInCalendar(string target, DateTime startDate, DateTime endDate); // date range
void SAPSelectDatesInCalendar(string target, int year, int week);                // week
void SAPSelectDatesInCalendar(string target, SAPSelectDatesInCalendarOptions options);
```

**Builder:**

```csharp
Options.SAPSelectDatesInCalendar(DateTime date)
Options.SAPSelectDatesInCalendar(DateTime startDate, DateTime endDate)
Options.SAPSelectDatesInCalendar(int year, int week)
```

### SAPCallTransaction

```csharp
void SAPCallTransaction(string transaction);
void SAPCallTransaction(string transaction, string prefix);
void SAPCallTransaction(SAPCallTransactionOptions options);
```

#### SAPCallTransactionOptions

| Property | Type | Description |
|---|---|---|
| `Transaction` | `string` | Transaction code |
| `Prefix` | `string` | Transaction prefix |

### SAPExpandTree / SAPExpandALVTree

```csharp
void SAPExpandTree(string target, string path);
void SAPExpandTree(string target, SAPExpandTreeOptions options);
void SAPExpandALVTree(string target, string path);
void SAPExpandALVTree(string target, SAPExpandALVTreeOptions options);
```

---

## Target Builders

### Target — Build TargetAnchorableModel Programmatically

```csharp
// Factory methods
Target.FromSelector(string selector)                     // from UI selector
Target.FromFuzzySelector(string selector)                // from fuzzy selector
Target.FromImage(string imagePath, double accuracy = 0.8) // from image file
Target.FromComputerVision(string imagePath, UIVisionCategoryType cvType, string cvText, AreaModel cvElementArea = null, AreaModel cvTextArea = null)
Target.FromSemanticSelector(string semanticSelector)     // AI-based targeting

// Extension methods for chaining
target.WithSelector(string selector)
target.WithFuzzySelector(string selector, double fuzzyAccuracy = 0.7, int fuzzyMatches = 1)
target.WithScopeSelector(string selector)       // set window scope
target.WithPointOffset(NPosition position = Center, int x = 0, int y = 0)
target.WithImage(string imagePath, double accuracy = 0.8)
target.WithComputerVision(string imagePath, UIVisionCategoryType cvType, string cvText, AreaModel cvElementArea = null, AreaModel cvTextArea = null, double ocrAccuracy = 0.9)
target.WithSemanticSelector(string semanticSelector)
```

#### Example

```csharp
var target = Target.FromSelector("<webctrl tag='input' id='email' />")
    .WithPointOffset(NPosition.Center, x: 0, y: 0);
app.Click(target, Options.Click());
```

### AppTarget — Build TargetAppModel Programmatically

```csharp
// Factory methods
AppTarget.FromPath(string path)                                           // desktop app from exe path
AppTarget.FromUrl(string url, string selector, NBrowserType browserType)  // web app

// Extension methods
app.WithPath(string path)
app.WithSelector(string selector)
app.WithTitle(string title, bool isExactTitleEnabled = false)
app.WithUrl(string url, string selector, NBrowserType browserType)

// Get targets from app model
app.GetWindowTarget()                            // get the window-level target
app.GetTarget(string targetName)                 // get a named element target
app.GetTarget(IElementDescriptor elementDescriptor)  // get target from descriptor
```

#### Example

```csharp
// Open a web application programmatically
var webApp = AppTarget.FromUrl("https://myapp.com", "<html />", NBrowserType.Chrome);
using var app = uiAutomation.Open(webApp, Options.AppOpen(windowResize: NWindowResize.Maximize));
app.GoToUrl("https://myapp.com/login");
```

---

## TargetAppOptions

Configuration for `Attach` and `Open` operations.

| Property | Type | Default | Description |
|---|---|---|---|
| `Timeout` | `double` | 30 | Timeout (seconds) for attaching/opening |
| `InteractionMode` | `NInteractionMode` | `HardwareEvents` | HardwareEvents or SimulateEvents |
| `AttachMode` | `NAppAttachMode` | `ByInstance` | ByInstance or ByTitle |
| `OpenMode` | `NAppOpenMode` | project setting | Never, Always, or IfNotOpen |
| `CloseMode` | `NAppCloseMode` | `Always` | Whether to close app on scope exit |
| `WindowResize` | `NWindowResize` | project setting | None, Maximize, or Minimize |
| `UserDataFolderMode` | `BrowserUserDataFolderMode` | project setting | Browser profile handling |
| `UserDataFolderPath` | `string` | project setting | Path to browser user data folder |
| `IsIncognito` | `bool` | `false` | Open browser in incognito mode |
| `WebDriverMode` | `NWebDriverMode` | project setting | WebDriver configuration |
| `WorkingDirectory` | `string` | — | Working directory for the app |
| `DialogHandlingOptions` | `DialogHandlingOptions` | `null` | Dialog handling configuration |

**Builders:**

```csharp
Options.AppAttach(NAppAttachMode attachMode = ByInstance, NAppOpenMode openMode = Never, double? timeout = null, NWindowResize? windowResize = null, NInteractionMode? interactionMode = null)

Options.AppOpen(NAppAttachMode attachMode = ByInstance, NAppOpenMode openMode = Always, double? timeout = null, NWindowResize? windowResize = null, NInteractionMode? interactionMode = null)

// Chain browser-specific settings
appOptions.WithBrowserOptions(string userDataFolderPath = null, BrowserUserDataFolderMode? userDataFolderMode = null, bool isIncognito = false, NWebDriverMode? webDriverMode = null)
```

---

## VerifyOptions — Action Verification

Used with `IWithVerify` options (Click, TypeInto, Hover, KeyboardShortcut) to verify an action was successful.

| Property | Type | Default | Description |
|---|---|---|---|
| `Target` | `TargetAnchorableModel` | — | Element to verify |
| `Mode` | `NVerifyMode` | — | `Appears` or `Disappears` |
| `Retry` | `bool` | project setting | Retry action if verification fails |
| `Timeout` | `double` | project setting | Verification timeout (seconds) |
| `DelayBefore` | `double` | 0 | Delay before verification |
| `IsLoose` | `bool` | `false` | Target not tied to an application card |
| `ExpectedText` | `string` | — | Expected text for TypeInto verification |

**Builder (extension method on any IWithVerify option):**

```csharp
// Verify by target name
options.Until("successMessage", until: NVerifyMode.Appears, retry: true, timeout: 2)

// Verify by target model
options.Until(targetModel, until: NVerifyMode.Appears, retry: true, timeout: 2)

// Verify TypeInto expected text
typeIntoOptions.UntilText(expectedText: "hello", retry: true, timeout: 5)
```

---

## TargetAppModel

Defines an application target programmatically.

| Property | Type | Default | Description |
|---|---|---|---|
| `Selector` | `string` | — | Window/app selector |
| `FilePath` | `string` | — | Application executable path |
| `Reference` | `string` | — | Reference ID |
| `Arguments` | `string` | — | Launch arguments |
| `Url` | `string` | — | Web URL |
| `BrowserType` | `NBrowserType` | `None` | Browser type for web apps |
| `IsExactTitleEnabled` | `bool` | `false` | Exact title matching |
| `Title` | `string` | — | Window title |
| `Area` | `AreaModel` | — | Screen area |
| `Elements` | `IDictionary<string, TargetAnchorableModel>` | — | Named element targets |

---

## TargetAnchorableModel

Comprehensive model for identifying a UI element. Created via `Target` builder or retrieved from Object Repository.

| Property | Type | Description |
|---|---|---|
| `PartialSelector` | `string` | Element selector |
| `ScopeSelector` | `string` | Window scope selector |
| `FuzzyPartialSelector` | `string` | Fuzzy selector string |
| `FuzzyAccuracy` | `double` | Fuzzy matching accuracy threshold |
| `FuzzyMatches` | `int` | Max fuzzy matches |
| `SemanticSelector` | `string` | AI-based semantic selector |
| `ImageBase64` | `string` | Base64-encoded image for image matching |
| `Accuracy` | `double` | Image matching accuracy |
| `ImageOccurrence` | `int` | Which occurrence of the image to use |
| `ImageFindMode` | `NImageFindMode` | Exact, Fuzzy, or Auto |
| `Text` | `string` | Text identification |
| `NativeText` | `string` | Native text identification |
| `NativeTextOccurrence` | `int` | Which text occurrence |
| `CvType` | `UIVisionCategoryType` | Computer Vision element type |
| `CvText` | `string` | Computer Vision text |
| `CvTextAccuracy` | `double` | CV text accuracy |
| `PointOffset` | `PointOffsetModel` | Click position offset |
| `RegionOffset` | `RegionOffsetModel` | Clipping region |
| `Visibility` | `NElementVisibility` | Visibility requirement |
| `WaitForReady` | `NWaitForReady` | Wait for ready state |
| `SearchSteps` | `TargetSearchSteps` | Flags for which search methods to use |
| `Elements` | `IDictionary<string, TargetAnchorableModel>` | Nested child elements |

---

## Supporting Models

### RuntimeTarget

A resolved runtime reference to a UI element, returned by `GetChildren` and `GetRuntimeTarget`.

| Property | Type | Description |
|---|---|---|
| `Reference` | `Guid` | Unique cache reference |
| `Element` | `UiElement` | Cached UiElement |

### AreaModel

| Property | Type | Description |
|---|---|---|
| `X` | `int` | X coordinate |
| `Y` | `int` | Y coordinate |
| `Width` | `int` | Width |
| `Height` | `int` | Height |

### PointOffsetModel

| Property | Type | Description |
|---|---|---|
| `Position` | `NPosition` | Position anchor (Center, TopLeft, etc.) |
| `X` | `int` | X offset |
| `Y` | `int` | Y offset |

### SearchedElementOptions

| Property | Type | Description |
|---|---|---|
| `Target` | `TargetAnchorableModel` | Element to scroll to |
| `Timeout` | `double` | Timeout for finding the element |

### NextPageOptions

| Property | Type | Description |
|---|---|---|
| `Target` | `TargetAnchorableModel` | Next page button/link target |
| `DelayBetweenPages` | `double` | Delay between page navigations |

---

## Enum Reference

| Enum | Values | Description |
|---|---|---|
| `NClickType` | `Single`, `Double`, `Down`, `Up` | Type of mouse click |
| `NMouseButton` | `Left`, `Right`, `Middle` | Mouse button |
| `NKeyModifiers` | `None`, `Alt`, `Ctrl`, `Shift`, `Win` | Keyboard modifiers |
| `NCheckType` | `Check`, `Uncheck`, `Toggle` | Checkbox action |
| `NCheckStateMode` | `WaitAppear`, `WaitDisappear` | Element state check mode |
| `NScrollDirection` | `Up`, `Down`, `Left`, `Right` | Scroll direction |
| `NAppAttachMode` | `ByInstance`, `ByTitle` | How to find the app |
| `NAppOpenMode` | `Never`, `Always`, `IfNotOpen` | When to open the app |
| `NAppCloseMode` | `Never`, `Always` | When to close the app on scope exit |
| `NWindowResize` | `None`, `Maximize`, `Minimize` | Window resize on attach/open |
| `NInteractionMode` | `HardwareEvents`, `SimulateEvents` | Top-level interaction mode |
| `NChildInteractionMode` | `SameAsCard`, `HardwareEvents`, `SimulateEvents` | Per-action interaction mode |
| `NVerifyMode` | `Appears`, `Disappears` | Verification check |
| `NClickMode` | `None`, `Single`, `Double` | Click before typing mode |
| `NEmptyFieldMode` | Various modes | How to clear field before typing |
| `NScrapingOptions` | `None`, `AllowFormatting`, `IgnoreHiddenText`, `GetWordsCoordinates` | Text scraping options |
| `NScrapingMethod` | `Default`, `TextAttribute`, `Fulltext`, `Native` | Text scraping method |
| `NBrowserType` | `None`, `Chrome`, `Edge`, `Firefox`, `Safari`, `IE`, `WebDriver` | Browser type |
| `NImageFindMode` | `Exact`, `Fuzzy`, `Auto` | Image search mode |
| `NElementVisibility` | `Visible`, `Hidden`, `Any` | Element visibility filter |
| `NWaitForReady` | `None`, `Complete`, `Interactive` | Page/element readiness |
| `CursorMotionType` | `Instant`, `Smooth` | Mouse cursor movement style |
| `NPosition` | `Center`, `TopLeft`, etc. | Anchor position for offsets |
| `NDateSelectionType` | `Date`, `Range`, `Week` | SAP calendar date selection |
| `NExecutionWorld` | `Isolated`, etc. | JS script execution context |
| `NUITaskAgentType` | Various agent types | AI task agent type |
| `NTypeByClipboardMode` | Various modes | Clipboard usage for typing |
| `NTraceAttachMode` | Various modes | Trace attachment |
| `LimitType` | `Rows`, `Items` | Data extraction limit type |
| `BrowserUserDataFolderMode` | Various modes | Browser user data folder handling |
| `NWebDriverMode` | Various modes | WebDriver mode |
| `NChildHealingAgentBehavior` | Various modes | Self-healing selector behavior |
