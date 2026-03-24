# Target System

The target system defines how UI Automation activities locate application windows and UI elements at runtime. There are two main target types used across activities: **TargetAnchorable** (for locating UI elements within an application) and **TargetApp** (for locating the application window itself). Together, they form a hierarchical targeting model: TargetApp identifies the application, while TargetAnchorable identifies specific elements within it.

## TargetAnchorable

`TargetAnchorable` is used by most UI element activities (Click, Type Into, Get Text, etc.) to locate a specific element within an application window. It supports selectors, anchors, fuzzy matching, and offset configurations.

**Inherits from: `Target`**
**Latest version: V6**

### Own Properties

| Property | Display Name | Type | Description |
|----------|-------------|------|-------------|
| `PointOffset` | Click offset | `PointOffset` | The offset values used to perform the click. The default is the center of the target. |
| `RegionOffset` | Area | `RegionOffset` | The offset values for the area used to perform the action. |
| `ElementVisibilityArgument` | Visibility check | `InArgument<NElementVisibility>` | When enabled, the activity also checks whether the UI element is visible or not. |
| `IsResponsive` | Responsive websites | `bool` | Enable responsive websites layout. Default: `false`. |
| `ScopeSelectorArgument` | Window selector (Application instance) | `InArgument<string>` | **Required for reliable targeting.** The window selector that identifies the application window. Must be set on every `TargetAnchorable` — even when the activity is inside an `NApplicationCard` scope. Without it, the activity cannot locate the target element at runtime (`NodeNotFoundException`). Set it to the same selector used in the parent `NApplicationCard`'s `TargetApp.Selector`. |
| `WaitForReadyArgument` | Wait for page load | `InArgument<NWaitForReady>` | Before performing the action, wait for the application to become ready to accept input. The options are: None - does not wait for the target to be ready; Interactive - waits until only a part of the app is loaded; Complete - waits for the entire app to be loaded. **Project setting.** |
| `SemanticSelectorArgument` | Semantic selector | `InArgument<string>` | A semantic description that defines the target. |

### Inherited Properties (from Target)

| Property | Display Name | Type | Description |
|----------|-------------|------|-------------|
| `FullSelectorArgument` | Strict selector | `InArgument<string>` | The strict selector generated for the target UI element. |
| `FuzzySelectorArgument` | Fuzzy selector | `InArgument<string>` | The fuzzy selector parameters. |
| `SearchSteps` | Targeting methods | `TargetSearchSteps` | The selector types to use for identifying the element. It can be set to any combination of Strict selector, Fuzzy selector, or Image. Default: `TargetSearchSteps.None`. |
| `ImageAccuracyArgument` | Image accuracy | `InArgument<double>` | Indicates the accuracy level for image matching. Default value is 0.8. |
| `ImageOccurrenceArgument` | Image occurrence | `InArgument<int>` | Indicates a specific occurrence to be used, when multiple matches are found. A value greater than 0 indicates the nth occurrence (1-based index). Default value is 0, meaning no specific occurrence will be used. |
| `ImageFindModeArgument` | Image find mode | `InArgument<NImageFindMode>` | Indicates the algorithm used for image matching. Default value is Find enhanced all. |
| `NativeTextArgument` | Native text | `InArgument<string>` | The text to find to identify the UI element. |
| `NativeTextOccurrenceArgument` | Native text occurrence | `InArgument<int>` | Indicates a specific occurrence to be used, when multiple matches are found. Default value is 0, meaning no specific occurrence will be used. |
| `IsNativeTextCaseSensitive` | Native text case-sensitive | `bool` | Indicates whether text matching is case-sensitive. Default: `false`. |
| `SemanticElementType` | Semantic element type | `NSemanticElementType` | Indicates the semantic element type. Default: `NSemanticElementType.None`. |
| `SemanticTextArgument` | Semantic Text | `InArgument<string>` | Indicates the text identified using AI-based capabilities. |
| `CvType` | CV Control type | `UIVisionCategoryType` | Indicates the type of control identified using Computer Vision. Default: `UIVisionCategoryType.None`. |
| `CvTextArgument` | CV Text | `InArgument<string>` | Indicates the text identified using Computer Vision. |
| `CvTextOccurrenceArgument` | CV Text occurrence | `InArgument<int>` | Indicates a specific occurrence to be used, when multiple matches are found. Default value is 0, meaning no specific occurrence will be used. |
| `CvTextAccuracyArgument` | CV Text accuracy | `InArgument<double>` | Indicates the accuracy level for OCR text matching. Default value is 0.7. |

### Object Repository Properties

| Property | Display Name | Type | Description |
|----------|-------------|------|-------------|
| `Reference` | OR Reference | `string` | Object Repository reference ID linking this target to an element registered in `.objects/`. Format: `<library>/<selection>/<version>/<screen>/<element>`. When set, Studio syncs selector changes from the OR entry. The selectors (`FullSelectorArgument`, `ScopeSelectorArgument`) are still used at runtime — `Reference` is the OR linkage, not a replacement for selectors. |
| `ContentHash` | Content hash | `string` | Hash of the OR entry content. Used by Studio to detect when the OR entry has changed. |
| `Guid` | GUID | `string` | Unique identifier for this target instance in the workflow. |
| `ElementType` | Element type | `string` | UI element type (e.g., `Button`, `Text`, `CheckBox`). Design-time metadata from the OR. |
| `DesignTimeRectangle` | Design-time rectangle | `string` | Bounding box of the element at design time (`x, y, width, height`). Design-time metadata. |
| `DesignTimeScaleFactor` | Design-time scale | `string` | DPI scale factor at design time. Design-time metadata. |

### XAML Syntax

Use plain XML-escaped attribute strings for selector properties. Do NOT wrap selectors in `CSharpValue` or `[bracket]` expressions — they are literal strings, not expressions.

```xml
<!-- Without OR reference (inline selectors only) -->
<uix:TargetAnchorable
    FullSelectorArgument="&lt;uia automationid='submitBtn' name='Submit' /&gt;"
    ScopeSelectorArgument="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    SearchSteps="Selector"
    Version="V6" />

<!-- With OR reference (selectors + link to Object Repository element) -->
<uix:TargetAnchorable
    FullSelectorArgument="&lt;uia automationid='submitBtn' name='Submit' /&gt;"
    Reference="ulW7.../cmDZJ049506fyLJLXd7dIA"
    ScopeSelectorArgument="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    SearchSteps="Selector"
    Version="V6" />
```

Expanded syntax (only needed for non-literal, expression-driven values):

```xml
<uix:TargetAnchorable Version="V6">
  <uix:TargetAnchorable.PointOffset>
    <uix:PointOffset />
  </uix:TargetAnchorable.PointOffset>
  <uix:TargetAnchorable.RegionOffset>
    <uix:RegionOffset />
  </uix:TargetAnchorable.RegionOffset>
  <uix:TargetAnchorable.ElementVisibilityArgument>
    <InArgument x:TypeArguments="uia:NElementVisibility" />
  </uix:TargetAnchorable.ElementVisibilityArgument>
  <uix:TargetAnchorable.WaitForReadyArgument>
    <InArgument x:TypeArguments="uia:NWaitForReady" />
  </uix:TargetAnchorable.WaitForReadyArgument>
  <uix:TargetAnchorable.SemanticSelectorArgument>
    <InArgument x:TypeArguments="x:String" />
  </uix:TargetAnchorable.SemanticSelectorArgument>
  <uix:TargetAnchorable.FullSelectorArgument>
    <InArgument x:TypeArguments="x:String">[selector]</InArgument>
  </uix:TargetAnchorable.FullSelectorArgument>
  <uix:TargetAnchorable.FuzzySelectorArgument>
    <InArgument x:TypeArguments="x:String">[fuzzySelector]</InArgument>
  </uix:TargetAnchorable.FuzzySelectorArgument>
  <uix:TargetAnchorable.ImageAccuracyArgument>
    <InArgument x:TypeArguments="x:Double">0.8</InArgument>
  </uix:TargetAnchorable.ImageAccuracyArgument>
  <uix:TargetAnchorable.NativeTextArgument>
    <InArgument x:TypeArguments="x:String">[text]</InArgument>
  </uix:TargetAnchorable.NativeTextArgument>
</uix:TargetAnchorable>
```

## TargetApp

`TargetApp` is used by the **Use Application/Browser** activity to identify and connect to the target application window or browser tab.

**Latest version: V2**

| Property | Display Name | Type | Description |
|----------|-------------|------|-------------|
| `Selector` | Selector | `InArgument<string>` | List of attributes used to find a particular application window. |
| `FilePath` | File path | `InArgument<string>` | The full path to the executable file that starts the application. Used only when opening a new application instance. |
| `Arguments` | Arguments | `InArgument<string>` | Parameters to pass to the target application at startup. Used only when opening a new application or browser instance. |
| `Url` | URL | `InArgument<string>` | The URL of the web page to open. |
| `WorkingDirectory` | Working directory | `InArgument<string>` | Path of the current working directory. |
| `Reference` | OR Reference | `string` | Object Repository reference ID linking this target to a screen registered in `.objects/`. Format: `<library>/<selection>/<version>/<screen>`. When set, Studio syncs selector changes from the OR entry. The `Selector` property is still used at runtime. |
| `ContentHash` | Content hash | `string` | Hash of the OR entry content. Design-time metadata managed by Studio. |
| `Area` | Area | `string` | Window position and size at design time (`x, y, width, height`). Design-time metadata. |
| `InformativeScreenshot` | Screenshot | `string` | Filename of the screen screenshot stored in `.screenshots/`. Design-time metadata. |

### XAML Syntax

Use plain XML-escaped attribute strings for selector properties:

```xml
<!-- Without OR reference -->
<uix:TargetApp
    Selector="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    Version="V2" />

<!-- With OR reference (selector + link to Object Repository screen) -->
<uix:TargetApp
    Reference="ulW7.../B_nfvc4lj0aNIoz-5nodeg"
    Selector="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    Version="V2" />
```

Expanded syntax (only needed for non-literal, expression-driven values):

```xml
<uix:TargetApp Version="V2">
  <uix:TargetApp.Selector>
    <InArgument x:TypeArguments="x:String">[selector]</InArgument>
  </uix:TargetApp.Selector>
  <uix:TargetApp.FilePath>
    <InArgument x:TypeArguments="x:String">[filePath]</InArgument>
  </uix:TargetApp.FilePath>
  <uix:TargetApp.Arguments>
    <InArgument x:TypeArguments="x:String">[arguments]</InArgument>
  </uix:TargetApp.Arguments>
  <uix:TargetApp.Url>
    <InArgument x:TypeArguments="x:String">[url]</InArgument>
  </uix:TargetApp.Url>
  <uix:TargetApp.WorkingDirectory>
    <InArgument x:TypeArguments="x:String">[workingDirectory]</InArgument>
  </uix:TargetApp.WorkingDirectory>
</uix:TargetApp>
```

## Configure a TargetAnchorable

To configure a TargetAnchorable for an activity, spawn a general-purpose subagent with the following prompt (replace `$VARIABLES` with actual values):

> Read the skill file at `uia-configure-target/SKILL.md` (resolve relative to this file's directory: `../../skills/uia-configure-target/SKILL.md`) and execute it with these arguments: `--window $WINDOW --elements $ELEMENTS`

To configure multiple elements on the same screen in a single invocation, separate them with `|`. This captures the window once and reuses it for all elements:

> `--window $WINDOW --elements "element one | element two | element three"`

## Configure a TargetApp

To configure a TargetApp (window only, no elements), spawn a general-purpose subagent with the following prompt:

> Read the skill file at `uia-configure-target/SKILL.md` (resolve relative to this file's directory: `../../skills/uia-configure-target/SKILL.md`) and execute it with these arguments: `--window $WINDOW`


## Using Object Repository References in XAML

After `uia-configure-target` returns screen and element reference IDs, apply them to the XAML as follows:

**1. On `TargetApp`** — set `Reference` to the **screen** reference ID:
```xml
<uix:TargetApp
    Reference="ulW7KVQc9ECQrwRUerqlGA/.../B_nfvc4lj0aNIoz-5nodeg"
    Selector="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    Version="V2" />
```

**2. On `TargetAnchorable`** — set `Reference` to the **element** reference ID:
```xml
<uix:TargetAnchorable
    FullSelectorArgument="&lt;uia automationid='submitBtn' name='Submit' /&gt;"
    Reference="ulW7KVQc9ECQrwRUerqlGA/.../cmDZJ049506fyLJLXd7dIA"
    ScopeSelectorArgument="&lt;wnd app='myapp.exe' title='My App' /&gt;"
    SearchSteps="Selector"
    Version="V6" />
```

**Key points:**
- `Reference` links the XAML target to an OR entry — it does **not** replace the selectors. Both `FullSelectorArgument`/`ScopeSelectorArgument` (on TargetAnchorable) and `Selector` (on TargetApp) must still be set. The selectors are the runtime mechanism; `Reference` is the design-time linkage that allows Studio to sync selector changes from the OR.
- When an element is reused across multiple activities (e.g., clicking the same button twice), use the **same** `Reference` value on each `TargetAnchorable`.
- Design-time metadata (`ContentHash`, `DesignTimeRectangle`, `Guid`, `Area`, `IconBase64`, `InformativeScreenshot`) is managed by Studio when it opens the file. You do not need to set these — Studio will populate them from the OR entry.
- If OR references are not needed (e.g., quick one-off automations), inline selectors without `Reference` work fine.

## Notes

- **Version attributes**: Always specify the latest version in XAML. `TargetAnchorable` uses `Version="V6"` and `TargetApp` uses `Version="V2"`. Omitting the version or using an older version may result in legacy behavior or missing features.
- **TargetAnchorable** is embedded as a sub-object (named `Target`) in activities that interact with UI elements. It is not set directly as an activity property in the Properties panel; instead, its sub-properties appear under the Target category.
- **TargetApp** is embedded as a sub-object (named `TargetApp`) in the Use Application/Browser activity. It configures the application window identification.
- **Anchors**: `TargetAnchorable` supports up to three anchors for improved element identification accuracy. Anchors are sibling sub-objects alongside the target and are used to disambiguate elements that share similar selectors.
- **Semantic selectors** (in `TargetAnchorable`) enable AI-powered element identification using natural language descriptions, providing resilience against UI layout changes.
- **Project settings**: Properties marked with `isProjectSetting: true` (such as `WaitForReadyArgument`) can have their defaults configured at the project level.
